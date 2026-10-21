"""E3-4 (parte 2): el paquete de avance lleva el design_id formal y la versión de cada diseño (ESPEC_receta_v2 sección 13: «el design_id formal llega con la
Entrega 3»). Son claves nuevas y opcionales: avance_version sigue en 1. Datos SINTÉTICOS."""
import json
from pathlib import Path
from app.api import Api
from app.nucleo import receta as RC

DISENO = {"tipo": "fact", "nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "centros": "2", "replicas": "1",
          "respuesta": "Resistencia", "aleatorio": True, "semilla": "7"}


def receta(tmp, modo="real", disenos=1):
    rc = {"tipo": "dmike-receta", "receta_version": 2, "dmike_minimo": "0.26", "modo_proyecto": modo, "id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c13",
          "datos_fijos": {}, "hojas": [{"hoja": "Corridas", "origen_datos": "vacia", "columnas": []}],
          "disenos": [{"id": "d1", "modulo": "DISENO-RSM", "hoja": "Corridas", "respuestas": ["Resistencia"], "parametros": dict(DISENO)}]}
    if disenos == 2:
        rc["disenos"].append({"id": "d2", "modulo": "DISENO-RSM", "hoja": "Corridas", "respuestas": ["Resistencia"], "parametros": {**DISENO, "nombres": "P, Q"}})
    rc["huella"] = RC.huella_receta({k: v for k, v in rc.items() if k != "huella"})
    ruta = tmp / "r.json"; ruta.write_text(json.dumps(rc), encoding="utf-8"); return str(ruta)


def avance(a, tmp, nombre="av.json"):
    ruta = tmp / nombre; r = a.exportar_avance(str(ruta)); assert r["error"] is None, r["sesion"][-1]["texto"]
    return json.loads(ruta.read_text(encoding="utf-8"))


def test_el_paquete_trae_design_id_y_version_de_cada_diseno(tmp_path):
    a = Api(); assert a.ejecutar_receta(receta(tmp_path, disenos=2))["error"] is None
    pkg = avance(a, tmp_path)
    assert pkg["avance_version"] == 1
    d = {x["id"]: x for x in pkg["disenos"]}
    assert d["d1"]["design_id"] == "DIS-Resistencia" and d["d1"]["version_diseno"] == 1
    assert d["d2"]["design_id"] == "DIS-Resistencia_2" and d["d2"]["version_diseno"] == 1          # dos diseños con la misma respuesta: ids distintos
    assert {x["design_id"] for x in a.disenos()} == {d["d1"]["design_id"], d["d2"]["design_id"]}


def test_el_paquete_refleja_la_version_registrada_y_sigue_siendo_solo_estado(tmp_path):
    a = Api(); a.ejecutar_receta(receta(tmp_path))
    col = a.hoja.indice("Temp"); nuevo = {"100": "100", "120": "140", "110": "120"}
    for i, t in enumerate(a.hoja.columnas[col].celdas[:a.hoja.n]): a.editar(i, col, nuevo[t])
    assert a.registrar_version_diseno("DIS-Resistencia", "cambio")["estado"] == "nueva"
    pkg = avance(a, tmp_path, "av2.json"); d = pkg["disenos"][0]
    assert d["design_id"] == "DIS-Resistencia" and d["version_diseno"] == 2 and "huella_diseno" not in d and "historial_versiones" not in d
    assert set(d) == {"id", "estado", "corridas", "respuestas_capturadas", "design_id", "version_diseno"}         # solo estado: ni niveles ni huellas ni respuestas
    texto = json.dumps(pkg, ensure_ascii=False)
    assert "RunId" not in texto and "140" not in texto                                                           # ni identificadores de corrida ni niveles


def test_demostracion_tambien_lo_trae_y_la_huella_del_paquete_se_comprueba(tmp_path):
    a = Api(); a.ejecutar_receta(receta(tmp_path, modo="demostracion"))
    pkg = avance(a, tmp_path); assert pkg["modo_proyecto"] == "demostracion" and pkg["disenos"][0]["design_id"] == "DIS-Resistencia"
    sin = {k: v for k, v in pkg.items() if k != "huella"}
    assert pkg["huella"] == RC.huella_receta(sin)                                                                   # la huella cubre las claves nuevas
