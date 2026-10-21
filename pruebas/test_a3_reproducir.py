"""A3: reproducir contra recalcular. «Repetir con datos actuales» recalcula; «Reproducir versión guardada» rehace el resultado original
con la copia congelada de sus entradas (celdas, tipo de columna y filtro de filas), la versión del motor y su huella SHA-256.
Un resultado con datos cambiados queda «desactualizado» pero sigue consultable. Datos SINTÉTICOS."""
import copy
from app.api import Api, VERSION

DATOS = "y\tg\tfiltro\n" + "\n".join(f"{10 + (i % 3) * 2 + (i % 5) * .37123}\t{'ABC'[i % 3]}\t{'si' if i < 20 else 'no'}" for i in range(30))
tablas = lambda r: [b.get("filas") for b in r["bloques"] if b["tipo"] == "tabla"]


def con_resultado():
    a = Api(); a.pegar(-1, 0, DATOS)
    return a, a.ejecutar_modulo("ESTADISTICOS", {"y": 0})["resultado"]


def test_copia_congelada_trae_version_huella_y_entradas():
    a, r = con_resultado()
    cg = r["definicion"]["congelado"]
    assert cg["version"] == VERSION and len(cg["huella"]) == 64 and cg["filtro"] == []
    assert cg["columnas"]["0"]["nombre"] == "y" and len(cg["columnas"]["0"]["celdas"]) == 30
    assert a.estado_resultado(r["uid"])["estado"] == "vigente"


def test_datos_cambiados_desactualizado_consultable_y_reproducible():
    a, r = con_resultado()
    a.hoja.editar(0, 0, "999")
    assert a.estado_resultado(r["uid"])["estado"] == "desactualizado"
    assert a.resultado(r["uid"]) is not None                                    # sigue consultable
    rep = a.reproducir_resultado(r["uid"])
    assert rep["error"] is None and tablas(rep["resultado"]) == tablas(r)       # mismos números que el original
    assert tablas(a.repetir_resultado(r["uid"])["resultado"]) != tablas(r)      # recalcular usa los datos nuevos


def test_reproduce_con_el_filtro_activo_al_correr():
    a = Api(); a.pegar(-1, 0, DATOS)
    a.hoja.aplicar_filtro([{"col": 2, "op": "=", "valor": "si"}])
    r = a.ejecutar_modulo("ESTADISTICOS", {"y": 0})["resultado"]
    assert r["definicion"]["congelado"]["filtro"] and "2" in r["definicion"]["congelado"]["columnas"]      # la columna del filtro también se congela
    a.hoja.aplicar_filtro([])                                                    # el usuario quita el filtro
    assert a.estado_resultado(r["uid"])["estado"] == "desactualizado"
    rep = a.reproducir_resultado(r["uid"])
    assert rep["error"] is None and tablas(rep["resultado"]) == tablas(r)
    assert tablas(a.repetir_resultado(r["uid"])["resultado"]) != tablas(r)


def test_huella_alterada_no_se_reproduce():
    a, r = con_resultado()
    a.proyecto.resultados[-1]["definicion"]["congelado"]["columnas"]["0"]["celdas"][0] = "1"
    assert a.reproducir_resultado(r["uid"])["error"] == "huella"


def test_copia_formato_1_sigue_reproduciendo():
    # migración: un resultado de v0.25 a v0.27 (sin «filtro», huella solo de columnas) se sigue reproduciendo y marcando
    a, r = con_resultado()
    cg = a.proyecto.resultados[-1]["definicion"]["congelado"]
    del cg["filtro"]; cg["huella"] = a._huella(cg["columnas"])
    assert a.estado_resultado(r["uid"])["estado"] == "vigente"
    assert a.reproducir_resultado(r["uid"])["error"] is None


def test_sin_filtro_la_huella_es_la_de_siempre():
    # compatibilidad: sin filtro de filas la huella cubre solo las columnas, igual que en v0.25 a v0.27 (las huellas guardadas siguen valiendo)
    a, r = con_resultado()
    cg = r["definicion"]["congelado"]
    assert cg["huella"] == a._huella(cg["columnas"]) and a._huella(cg["columnas"]) == a._huella(cg["columnas"], [])
