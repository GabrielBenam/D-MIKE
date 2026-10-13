import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "herramientas"))
import exportar_catalogo as ec


def test_catalogo_cubre_todos_los_modulos_registrados(tmp_path):
    from app.modulos import cargar
    from app.modulos.formatos import FORMATOS
    from app.api import VERSION
    ruta = ec.main(["--salida", str(tmp_path)])
    assert ruta.name == f"catalogo_dmike_{VERSION}.json"
    cat = json.loads(ruta.read_text(encoding="utf-8"))
    ids = [m["id"] for m in cat["modulos"]]
    assert sorted(ids) == sorted(cargar()) and len(ids) == len(set(ids)) == cat["total_modulos"]
    for m in cat["modulos"]:
        assert m["titulo"] and m["ruta"], m["id"]
        if m["id"] in FORMATOS: assert m["tipo"] == "formato" and (m["cabecera"] or m["tablas"]), m["id"]   # A3 solo tiene cabecera
        else: assert m["tipo"] == "analisis" and "parametros" in m, m["id"]


def test_catalogo_incluye_opciones_de_parametros_y_formatos(tmp_path):
    cat = json.loads(ec.main(["--salida", str(tmp_path)]).read_text(encoding="utf-8"))
    por_id = {m["id"]: m for m in cat["modulos"]}
    tipo = next(c for c in por_id["AMEF"]["cabecera"] if c["campo"] == "tipo")
    assert {o["valor"] for o in tipo["opciones"]} == {"proceso", "diseno"}
    assert any(c.get("opciones") for m in cat["modulos"] if m["tipo"] == "analisis" for c in m["parametros"])
