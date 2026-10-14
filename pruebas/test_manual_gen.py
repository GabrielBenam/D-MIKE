"""Generador del manual (herramientas/manual): sin rutas absolutas ajenas al repositorio y mismo PDF desde cualquier directorio."""
import re, shutil, subprocess, sys
from pathlib import Path
import pytest

RAIZ = Path(__file__).resolve().parent.parent
MANUAL = RAIZ / "herramientas" / "manual"
ENTORNO_AJENO = "/home/" + "claude"            # partido para que esta prueba no se encuentre a sí misma
ABS = re.compile(re.escape(ENTORNO_AJENO) + r"|/mnt/(?:user-data|project)|(?<![\w:.])/tmp/|[A-Za-z]:\\\\")


def test_manual_sin_rutas_absolutas():
    archivos = [f for f in MANUAL.rglob("*") if f.is_file() and f.suffix in (".py", ".json", ".md", ".txt", ".html") and "salida" not in f.parts]
    assert {f.name for f in archivos} >= {"gen.py", "textos.json", "README.md"}
    malos = [f"{f.relative_to(RAIZ)}:{n}: {l.strip()[:90]}" for f in archivos for n, l in enumerate(f.read_text(encoding="utf-8").splitlines(), 1) if ABS.search(l)]
    assert malos == []
    assert subprocess.run(["git", "grep", "-l", ENTORNO_AJENO], cwd=RAIZ, capture_output=True, text=True).stdout == ""      # en todo el repositorio


def _generar(cwd, salida):
    return subprocess.run([sys.executable, str(MANUAL / "gen.py"), "--salida", str(salida)], cwd=cwd, capture_output=True, text=True, timeout=600)


@pytest.mark.interfaz
def test_manual_mismo_pdf_desde_distintos_directorios(tmp_path):
    pytest.importorskip("markdown", reason="falta el paquete markdown (requirements-dev.txt)")
    if not (shutil.which("pdfinfo") and shutil.which("pdftotext")): pytest.skip("falta poppler-utils (pdfinfo, pdftotext)")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p: p.chromium.launch().close()
    except Exception as e: pytest.skip(f"sin navegador de Playwright ({str(e).splitlines()[0][:60]})")
    textos = []
    for nombre, cwd in (("a", RAIZ), ("b", MANUAL)):
        r = _generar(cwd, tmp_path / nombre)
        assert r.returncode == 0, r.stderr[-600:]
        pdf = next((tmp_path / nombre).glob("D-MIKE_Manual_de_uso_v*.pdf"))
        assert pdf.stat().st_size > 100_000 and not (tmp_path / nombre / "_pasada1.pdf").exists()
        n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
        textos.append((n, subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout))
    assert textos[0] == textos[1] and textos[0][0] > 50
    assert "Sección no generada" not in textos[0][1] and textos[0][0] > 120      # manual completo, no parcial


def test_manual_sin_entradas_se_detiene_con_mensaje(tmp_path):
    r = subprocess.run([sys.executable, str(MANUAL / "gen.py"), "--entradas", str(tmp_path), "--salida", str(tmp_path / "s")], capture_output=True, text=True, timeout=120)
    if "No module named" in r.stderr: pytest.skip("faltan dependencias del generador")
    assert r.returncode != 0 and "Faltan entradas" in r.stderr and "paso_a_paso.md" in r.stderr and "--permitir-faltantes" in r.stderr


def test_generar_svgs_produce_las_figuras_que_usa_el_manual(tmp_path):
    """svgs.json trae las 10 figuras que gen.py inserta en la sección 6 (módulo, k-ésimo resultado, j-ésima gráfica) y es reproducible."""
    import json
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    for destino in (a, b):
        r = subprocess.run([sys.executable, str(MANUAL / "generar_svgs.py"), "--salida", str(destino)], capture_output=True, text=True, timeout=300)
        if "No module named" in r.stderr: pytest.skip("faltan dependencias del programa")
        assert r.returncode == 0, r.stderr[-500:]
    assert a.read_bytes() == b.read_bytes()
    sv = json.loads(a.read_text(encoding="utf-8"))
    usadas = [("MSA-VAR", 0, 0), ("SPC", 0, 0), ("CAPACIDAD", 0, 0), ("PARETO", 0, 0), ("ANOVA", 0, 0), ("FACTORIAL", 0, 0), ("RSM", 0, 1), ("RSM", 1, 1), ("OPTIMIZADOR", 0, 0), ("CAPACIDAD", 1, 0)]
    for mod, k, j in usadas:
        assert sv[mod][k]["svg"][j].lstrip().startswith("<svg") and len(sv[mod][k]["huella"]) == 64, (mod, k, j)
    assert "dc:date" not in a.read_text(encoding="utf-8")


@pytest.mark.interfaz
def test_manual_completo_sin_permitir_faltantes(tmp_path):
    pytest.importorskip("markdown", reason="falta el paquete markdown (requirements-dev.txt)")
    if not (shutil.which("pdfinfo") and shutil.which("pdftotext")): pytest.skip("falta poppler-utils")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p: p.chromium.launch().close()
    except Exception as e: pytest.skip(f"sin navegador de Playwright ({str(e).splitlines()[0][:60]})")
    ent = tmp_path / "entradas"; ent.mkdir()
    shutil.copy(MANUAL / "entradas" / "D-MIKE_caso_integral_paso_a_paso.md", ent)           # el glosario sale de la raíz y svgs.json se genera solo
    r = subprocess.run([sys.executable, str(MANUAL / "gen.py"), "--entradas", str(ent), "--salida", str(tmp_path / "s")], capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-600:]
    assert "ADVERTENCIA" not in r.stdout and (ent / "svgs.json").is_file()
    pdf = next((tmp_path / "s").glob("*.pdf"))
    texto = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    assert "Sección no generada" not in texto and "6.10 Notas de rigor" in texto and "A3: formato de una hoja" in texto
    assert (tmp_path / "s" / "manual.html").read_text(encoding="utf-8").count("<figure>") == 10
