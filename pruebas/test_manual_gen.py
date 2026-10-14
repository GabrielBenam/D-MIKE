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
    return subprocess.run([sys.executable, str(MANUAL / "gen.py"), "--permitir-faltantes", "--salida", str(salida)], cwd=cwd, capture_output=True, text=True, timeout=600)


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
    assert "Sección no generada" in textos[0][1]                     # el PDF parcial declara lo que le falta


def test_manual_sin_entradas_se_detiene_con_mensaje(tmp_path):
    r = subprocess.run([sys.executable, str(MANUAL / "gen.py"), "--entradas", str(tmp_path), "--salida", str(tmp_path / "s")], capture_output=True, text=True, timeout=120)
    if "No module named" in r.stderr: pytest.skip("faltan dependencias del generador")
    assert r.returncode != 0 and "Faltan entradas" in r.stderr and "svgs.json" in r.stderr and "paso_a_paso.md" in r.stderr and "--permitir-faltantes" in r.stderr
