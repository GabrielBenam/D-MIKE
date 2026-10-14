"""Detecta en local lo que el paso «Revisar que estén todos los archivos» de GitHub Actions detectaría en la nube."""
import re, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "herramientas"))


def _codigo_del_paso():
    """Extrae el código Python del paso del flujo, tal cual está escrito."""
    flujo = (RAIZ / ".github" / "workflows" / "main.yml").read_text(encoding="utf-8")
    m = re.search(r"- name: Revisar que estén todos los archivos\n\s+shell: python\n\s+run: \|\n((?:\s{10}.*\n|\n)+)", flujo)
    assert m, "no encuentro el paso de verificación en main.yml"
    return "\n".join(l[10:] for l in m[1].splitlines())


def test_paso_de_verificacion_del_flujo_no_reporta_faltantes():
    r = subprocess.run([sys.executable, "-c", _codigo_del_paso()], cwd=RAIZ, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_manifiesto_coincide_con_el_repositorio():
    import generar_manifiesto as gm
    esperado = [f for f in gm.archivos()]
    real = [l.strip() for l in (RAIZ / "MANIFIESTO.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    assert real == esperado, "MANIFIESTO.txt desactualizado: corre python herramientas/generar_manifiesto.py"


def test_catalogo_de_la_version_vigente_existe():
    from app.api import VERSION
    assert (RAIZ / "proyecto" / "catalogo" / f"catalogo_dmike_{VERSION}.json").exists()
