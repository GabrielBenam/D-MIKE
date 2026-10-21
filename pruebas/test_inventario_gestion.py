"""A5: ninguna entrada del grupo «Gestión» de la cinta puede ser solo una entrada de menú, y el inventario escrito está al día."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("inventario_gestion", RAIZ / "herramientas" / "inventario_gestion.py")
INV = importlib.util.module_from_spec(spec); spec.loader.exec_module(INV)


def test_toda_entrada_de_gestion_tiene_modulo_construido():
    filas = INV.inventario()
    assert len(filas) >= 17
    sin = [f["entrada"] for f in filas if f["estado"].startswith("Solo entrada")]
    assert sin == [], f"entradas de menú sin módulo: {sin}"
    assert all("no figura en el catálogo" not in f["estado"] for f in filas)
    assert all(f["tipo"] != "sin clasificar" for f in filas), "una entrada nueva necesita su fila en TIPO"


def sin_pruebas(md):
    """La columna de pruebas cambia cada vez que se agrega una prueba que nombra un formato; no cuenta para la sincronía."""
    return ["|".join(c for i, c in enumerate(l.split("|")) if i != 7) if l.startswith("|") else l for l in md.splitlines()]


def test_inventario_escrito_coincide_con_el_codigo():
    esperado = INV.como_markdown(INV.inventario())
    escrito = (RAIZ / "proyecto" / "INVENTARIO_GESTION.md").read_text(encoding="utf-8")
    assert sin_pruebas(escrito) == sin_pruebas(esperado), "regenera: python herramientas/inventario_gestion.py --escribir"
