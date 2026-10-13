"""Incrementos 3 y 4: carga, validación y fusión del perfil. Datos sintéticos."""
import json, copy
from pathlib import Path
import pytest
from app.api import Api
from app.nucleo.catalogo import Catalogo
from app.nucleo.perfil import validar, PerfilInvalido

SINT = Path(__file__).parent / "sinteticos"
BASE = json.loads((SINT / "perfil_prueba_sintetico.json").read_text(encoding="utf-8"))
CAT = Catalogo()


def escribir(tmp_path, datos, nombre="p.json"):
    r = tmp_path / nombre
    r.write_text(datos if isinstance(datos, str) else json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return str(r)


def test_perfil_sintetico_valido():
    p, avisos = validar(json.dumps(BASE), CAT)
    assert p["version"] == 1 and len(p["modulos"]) == 12 and len(p["columnas"]) == 12
    assert [c["tipo"] for c in p["columnas"][:3]] == ["fecha", "texto", "texto"] and avisos == []


@pytest.mark.parametrize("n", range(1, 6))
def test_cinco_casos_del_simulador(n, tmp_path):
    api = Api(); texto = (SINT / "casos" / f"caso{n}.json").read_text(encoding="utf-8")
    r = api.abrir_perfil(escribir(tmp_path, texto))
    assert r["error"] is None and r["proyecto"]["version"] == 1
    esperado = json.loads(texto)
    activos = sum(len(v) for v in r["proyecto"]["activos"].values())
    assert activos == sum(1 for m in esperado["modulos"] if m["estado"] == "activo")
    nombres = [c["nombre"] for c in r["hoja"]["columnas"]]
    assert nombres == [c["nombre"] for c in esperado["hoja_datos_sugerida"]]
    assert r["proyecto"]["fase_actual"] == esperado["diagnostico"]["fase_actual"]


DANADOS = {
    "json_roto": ("{ esto no es json", "JSON legible"),
    "lista": ("[1, 2]", "se esperaba un objeto"),
    "sin_version": (lambda p: p.pop("version_perfil"), "version_perfil"),
    "version_texto": (lambda p: p.update(version_perfil="1"), "version_perfil"),
    "sin_modulos": (lambda p: p.pop("modulos"), "falta el campo modulos"),
    "fase_mala": (lambda p: p["modulos"][1].update(fase_asignada="X"), "fase no válida"),
    "tipo_col_malo": (lambda p: p["hoja_datos_sugerida"][0].update(tipo="decimal"), "tipo no válido"),
    "fijo_no_texto": (lambda p: p["datos_fijos"].update(responsable=5), "datos_fijos.responsable"),
}


@pytest.mark.parametrize("caso", DANADOS)
def test_perfiles_danados_no_tocan_nada(caso, tmp_path):
    cambio, msg = DANADOS[caso]
    if isinstance(cambio, str): datos = cambio
    else: datos = copy.deepcopy(BASE); cambio(datos)
    api = Api(); api.hoja.editar(0, 0, "7")
    antes = api.hoja.estado()
    r = api.abrir_perfil(escribir(tmp_path, datos))
    assert r["error"] == "perfil" and msg in r["sesion"][0]["texto"] and "No se cambió nada" in r["sesion"][0]["texto"]
    assert api.hoja.estado() == antes and api.proyecto.version == 0


def test_modulo_inexistente_se_ignora_con_aviso(tmp_path):
    d = copy.deepcopy(BASE); d["modulos"].append({"id": "NO-EXISTE", "fase_asignada": "M", "estado": "activo"})
    d["arbol_version"] = "1.2"
    r = Api().abrir_perfil(escribir(tmp_path, d))
    textos = " ".join(e["texto"] for e in r["sesion"])
    assert r["error"] is None and "NO-EXISTE no existe" in textos and "árbol v1.2" in textos


def test_columnas_existentes_no_se_duplican_ni_cambian(tmp_path):
    api = Api(); api.hoja.renombrar(0, "Tiempo"); api.hoja.editar(0, 0, "abc")
    r = api.abrir_perfil(escribir(tmp_path, BASE))
    nombres = [c["nombre"].lower() for c in r["hoja"]["columnas"]]
    assert nombres.count("tiempo") == 1 and len(nombres) == 12
    assert r["hoja"]["columnas"][0]["tipo"] == "texto" and r["hoja"]["columnas"][0]["texto"][0] == "abc"


def test_archivo_inexistente(tmp_path):
    r = Api().abrir_perfil(str(tmp_path / "no.json"))
    assert r["error"] == "lectura"


def test_cancelar_dialogo():
    api = Api(); api._elegir = lambda *a, **k: None
    assert "cancelada" in api.abrir_perfil()["sesion"][0]["texto"]


# ---------- incremento 4: fusión ----------
def v2(cambios=None):
    d = copy.deepcopy(BASE); d["version_perfil"] = 2
    if cambios: cambios(d)
    return d


def test_fusion_conserva_datos_avance_y_fijos(tmp_path):
    api = Api(); api.abrir_perfil(escribir(tmp_path, BASE, "v1.json"))
    j = api.hoja.indice("tiempo"); api.hoja.editar(0, j, "16.2"); api.hoja.editar(1, j, "2.7")
    api.fijar_datos({"responsable": "Otra persona (sintética)"})
    api.marcar_avance("CORRIDA", "hecho")
    api.proyecto.resultados.append({"modulo": "TIEMPOS", "id": "r1"})

    def cambios(d):
        d["datos_fijos"]["responsable"] = "Nombre del perfil v2"; d["datos_fijos"]["cliente_area"] = None
        d["modulos"] = [m for m in d["modulos"] if m["id"] not in ("CORRIDA", "TIEMPOS", "CORREL")]
        d["modulos"].append({"id": "PARETO", "fase_asignada": "A", "estado": "activo", "prioridad": "N"})
        d["hoja_datos_sugerida"] = d["hoja_datos_sugerida"][:3] + [{"nombre": "defecto", "tipo": "cat", "rol": "factor"}]
    r = api.abrir_perfil(escribir(tmp_path, v2(cambios), "v2.json"))
    assert r["error"] is None and r["proyecto"]["version"] == 2
    col = r["hoja"]["columnas"][j]
    assert col["nombre"] == "tiempo" and col["texto"][:2] == ["16.2", "2.7"]          # capturas intactas
    assert [c["nombre"] for c in r["hoja"]["columnas"]][-1] == "defecto"             # columna nueva al final
    assert len(r["hoja"]["columnas"]) == 13                                           # ninguna borrada
    fijos = {x["campo"]: x["valor"] for x in r["proyecto"]["fijos"]}
    assert fijos["responsable"] == "Otra persona (sintética)" and fijos["cliente_area"] == "Cliente ficticio"
    ids = {m["id"]: m for f in r["proyecto"]["activos"].values() for m in f}
    assert ids["CORRIDA"]["avance"] == "hecho" and ids["CORRIDA"]["conservado"]      # avance conservado
    assert ids["TIEMPOS"]["conservado"] and "CORREL" not in ids                       # capturas conservadas
    textos = " ".join(e["texto"] for e in r["sesion"])
    assert "fusionado" in textos and "no se borró" in textos


def test_fusion_misma_version_rechazada(tmp_path):
    api = Api(); api.abrir_perfil(escribir(tmp_path, BASE))
    api.hoja.editar(0, 0, "2026-10-05")
    antes = (api.hoja.estado(), api.proyecto.a_dict())
    r = api.abrir_perfil(escribir(tmp_path, BASE, "otra.json"))
    assert r["error"] == "version" and "solo se incorpora una versión mayor" in r["sesion"][0]["texto"]
    assert (api.hoja.estado(), api.proyecto.a_dict()) == antes


def test_fusion_v2_danada_no_toca_nada(tmp_path):
    api = Api(); api.abrir_perfil(escribir(tmp_path, BASE))
    antes = api.proyecto.a_dict()
    r = api.abrir_perfil(escribir(tmp_path, v2(lambda d: d.pop("datos_fijos")), "v2.json"))
    assert r["error"] == "perfil" and api.proyecto.a_dict() == antes
