"""E3-2: identidad del diseño (design_id, run_id, version_diseno) y columna RunId de solo lectura en proyectos reales.
ESPEC_receta_v2 secciones 2.1 y 6.4; ESPEC_flujo_real_dmaic sección 5. Datos SINTÉTICOS."""
import copy, gzip, json, shutil
from pathlib import Path
import pytest
from app.api import Api
from app.nucleo import modo as MD, disenos as DIS, archivo

S = Path(__file__).parent / "sinteticos"
DISENO = {"tipo": "fact", "nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "centros": "2", "replicas": "1",
          "respuesta": "Resistencia", "aleatorio": True, "semilla": "7"}          # 2^2 + 2 centros = 6 corridas


def api(demo=False, **extra):
    a = Api()
    if demo: MD.fijar(a.proyecto, MD.DEMO, MD.DECLARADO)
    r = a.ejecutar_modulo("DISENO-RSM", {**DISENO, **extra}); assert r["error"] is None, r["sesion"][0]["texto"]
    return a, r["resultado"]


def col(a, nombre): return a.hoja.indice(nombre)


def textos(a, nombre): return [a.hoja.columnas[col(a, nombre)].valor(i)[0] for i in range(a.hoja.n)]


def desc(a): return a.disenos()[0]


# ---------- modo real: columna RunId de solo lectura ----------
def test_real_agrega_runid_derivado_de_ordenest():
    a, res = api()
    d = desc(a)
    assert d["design_id"] == "DIS-Resistencia" and d["version_diseno"] == 1 and d["estado_definicion"] == "vigente" and d["col_runid"] == "RunId"
    assert [c.nombre for c in a.hoja.columnas][-1] == "RunId" and a.hoja.columnas[-1].rol == "run_id"
    oe = textos(a, "OrdenEst")
    assert textos(a, "RunId") == [f"DIS-Resistencia-R{int(x):03d}" for x in oe]          # de OrdenEst, no de la fila
    assert oe != sorted(oe, key=int)                                                       # el orden de corrida está aleatorizado: fila y OrdenEst difieren
    assert res["datos"]["columnas"][-1] == col(a, "RunId") and res["datos"]["diseno"]["design_id"] == "DIS-Resistencia"
    assert d["run_ids"] == 6 and d["problemas"] == {"sin_columna": False, "sin_orden": [], "repetidos": {}}


def test_real_runid_es_de_solo_lectura_por_todas_las_vias():
    a, _ = api(); j = col(a, "RunId"); antes = textos(a, "RunId")
    for r in (a.editar(0, j, "X"), a.pegar(0, j, "X\nY"), a.pegar(0, j - 1, "1\tZ"), a.borrar_rango(0, j, 2, j), a.llenar_con(0, j, 2, j, "Q"),
              a.rellenar(0, j, 2, j, "abajo"), a.cambiar_tipo(j, "num"), a.renombrar(j, "Otro")):
        assert r["error"] == "solo_lectura" and "solo lectura" in r["sesion"][-1]["texto"]
    assert textos(a, "RunId") == antes and a.hoja.columnas[j].nombre == "RunId" and a.hoja.columnas[j].tipo == "texto"
    # un intento que sí sobrevive (módulo que escribe sobre toda la hoja) se deshace en la respuesta siguiente
    a.hoja.columnas[j].celdas[0] = "intruso"; a.editar(0, col(a, "Resistencia"), "5")
    assert textos(a, "RunId") == antes


def test_real_editar_ordenest_actualiza_su_runid_y_envia_la_hoja_completa():
    a, _ = api(); je = col(a, "OrdenEst")
    r = a.editar(0, je, "99")
    assert r["error"] is None and "hoja" in r and "delta" not in r                          # RunId cambió: hoja completa
    assert textos(a, "RunId")[0] == "DIS-Resistencia-R099"
    d = desc(a); assert d["estado_definicion"] == "cambiada"                                # OrdenEst es parte de la definición
    a.deshacer(); assert textos(a, "RunId")[0] == f"DIS-Resistencia-R{int(textos(a, 'OrdenEst')[0]):03d}" and desc(a)["estado_definicion"] == "vigente"


def test_real_ordenar_y_filtrar_no_cambian_el_run_id_de_cada_corrida():
    a, _ = api()
    pares = lambda: sorted(zip(textos(a, "OrdenEst"), textos(a, "RunId")))
    base = pares()
    r = a.ejecutar_modulo("ORDENAR", {"col": col(a, "OrdenCorrida"), "orden": "desc"}); assert r["error"] is None
    assert pares() == base and textos(a, "OrdenCorrida") == sorted(textos(a, "OrdenCorrida"), key=int, reverse=True)
    a.filtrar([{"col": col(a, "TipoPunto"), "op": "=", "valor": "1"}])
    visibles = a.hoja.filas_activas()
    assert len(visibles) == 4 and all(textos(a, "RunId")[i] == f"DIS-Resistencia-R{int(textos(a, 'OrdenEst')[i]):03d}" for i in visibles)
    assert pares() == base                                                                  # ni la fila ni el filtro intervienen
    assert desc(a)["estado_definicion"] == "vigente"                                        # ordenar no cambia la definición (OrdenCorrida no cuenta)


def test_real_guardar_y_abrir_conserva_identidad_y_proteccion(tmp_path):
    a, _ = api(); ruta = str(tmp_path / "d.dmike"); a._elegir = lambda *x, **k: ruta; assert a.guardar()["error"] is None
    b = Api(); assert b.abrir_proyecto(ruta)["error"] is None
    d = b.disenos()[0]
    assert d["design_id"] == "DIS-Resistencia" and d["estado_definicion"] == "vigente" and d["col_runid"] == "RunId"
    assert b.editar(0, col(b, "RunId"), "x")["error"] == "solo_lectura"


# ---------- modo demostración: la hoja no se toca ----------
def test_demostracion_no_agrega_columnas_pero_deriva_el_run_id():
    a, res = api(demo=True)
    nombres = [c.nombre for c in a.hoja.columnas]
    assert nombres == ["OrdenEst", "OrdenCorrida", "TipoPunto", "Bloque", "Temp", "Tiempo", "Resistencia"] and all(c.rol is None for c in a.hoja.columnas)
    d = desc(a)
    assert d["design_id"] == "DIS-Resistencia" and d["version_diseno"] == 1 and d["col_runid"] is None and d["run_ids"] == 6
    ids, _ = DIS.run_ids(a.hoja, a.proyecto.formatos["_disenos"]["Resistencia"], "Resistencia")
    assert ids == [f"DIS-Resistencia-R{int(x):03d}" for x in textos(a, "OrdenEst")]
    assert res["datos"]["columnas"] == list(range(7)) and "solo lectura" not in " ".join(str(b) for b in res["bloques"] if b["tipo"] == "texto").lower().replace("derivado", "")
    assert a.editar(0, col(a, "OrdenEst"), "42")["error"] is None                           # sin protección: no hay columna RunId


def test_demostracion_y_real_comparten_la_misma_identidad_de_corridas():
    r, _ = api(); d, _ = api(demo=True)
    ids = lambda a: sorted(DIS.run_ids(a.hoja, a.proyecto.formatos["_disenos"]["Resistencia"], "Resistencia")[0])
    assert ids(r) == ids(d)


# ---------- design_id ----------
def test_design_id_unico_con_dos_disenos_de_la_misma_respuesta():
    a, _ = api(); r = a.ejecutar_modulo("DISENO-RSM", {**DISENO, "nombres": "P, Q"}); assert r["error"] is None
    ds = {x["respuesta"]: x for x in a.disenos()}
    assert set(ds) == {"Resistencia", "Resistencia_2"} and ds["Resistencia_2"]["design_id"] == "DIS-Resistencia_2"
    assert len({x["design_id"] for x in ds.values()}) == 2


def test_runid_y_design_id_no_viajan_en_la_receta_ni_los_asigna_la_receta():
    a, _ = api()
    info = a.proyecto.formatos["_disenos"]["Resistencia"]
    assert info["design_id"] and "design_id" not in json.dumps(DISENO)                      # el identificador lo asigna D-MIKE, no el usuario


# ---------- version_diseno ----------
def test_version_nace_en_1_y_solo_sube_al_registrar_un_cambio_de_definicion():
    a, _ = api()
    assert desc(a)["version_diseno"] == 1
    jy = col(a, "Resistencia")
    for i in range(a.hoja.n): a.editar(i, jy, str(50 + i))                                  # capturar respuestas no cambia la definición
    assert desc(a)["estado_definicion"] == "vigente" and desc(a)["version_diseno"] == 1
    r = a.registrar_version_diseno("DIS-Resistencia")
    assert r["estado"] == "sin_cambios" and desc(a)["version_diseno"] == 1
    a.editar(0, col(a, "Temp"), "130")                                                      # cambia un nivel real
    assert desc(a)["estado_definicion"] == "cambiada" and desc(a)["version_diseno"] == 1    # detectar no incrementa: lo registra el usuario
    r = a.registrar_version_diseno("DIS-Resistencia", "Se subió la temperatura de la corrida 1")
    d = desc(a)
    assert r["estado"] == "nueva" and d["version_diseno"] == 2 and d["estado_definicion"] == "vigente"
    h = d["historial_versiones"]
    assert len(h) == 1 and h[0]["version"] == 1 and h[0]["motivo"] == "Se subió la temperatura de la corrida 1" and len(h[0]["huella"]) == 64
    assert a.registrar_version_diseno("DIS-Resistencia")["estado"] == "sin_cambios"
    assert a.registrar_version_diseno("DIS-No-Existe")["error"] == "version"


def test_nueva_aleatorizacion_del_orden_no_es_nueva_version():
    a, _ = api(); jc = col(a, "OrdenCorrida")
    n = a.hoja.n
    for i in range(n): a.editar(i, jc, str(n - int(textos(a, "OrdenCorrida")[i]) + 1))      # invierte el orden en que se corre
    assert desc(a)["estado_definicion"] == "vigente"


def test_version_y_historial_sobreviven_guardar_y_abrir(tmp_path):
    a, _ = api(); a.editar(0, col(a, "Tiempo"), "99"); a.registrar_version_diseno("DIS-Resistencia", "m")
    ruta = str(tmp_path / "v.dmike"); a._elegir = lambda *x, **k: ruta; a.guardar()
    b = Api(); b.abrir_proyecto(ruta); d = b.disenos()[0]
    assert d["version_diseno"] == 2 and d["estado_definicion"] == "vigente" and d["historial_versiones"][0]["version"] == 1


# ---------- diseños anteriores a 0.29: identidad al vuelo, sin tocar nada ----------
def _viejo(a):
    """Convierte el diseño del proyecto en uno anterior a 0.29: sin identidad guardada y sin columna RunId."""
    info = a.proyecto.formatos["_disenos"]["Resistencia"]
    for k in ("design_id", "version_diseno", "huella_diseno", "historial_versiones", "orden_est", "orden_corrida", "col_runid"): info.pop(k, None)
    j = col(a, "RunId")
    if j is not None: a.hoja.eliminar_columna(j)
    return info


def test_diseno_anterior_recibe_identidad_derivada_sin_modificar_lo_guardado():
    a, _ = api(); _viejo(a)
    antes_p = copy.deepcopy(a.proyecto.formatos["_disenos"]); antes_h = copy.deepcopy(a.hoja.a_dict())
    d = a.disenos()[0]
    assert d["design_id"] == "DIS-Resistencia" and d["version_diseno"] == 1 and d["estado_definicion"] == "sin_linea_base" and d["run_ids"] == 6
    ids, prob = DIS.run_ids(a.hoja, a.proyecto.formatos["_disenos"]["Resistencia"], "Resistencia")
    assert ids == [f"DIS-Resistencia-R{int(x):03d}" for x in textos(a, "OrdenEst")] and prob["repetidos"] == {}
    assert a.proyecto.formatos["_disenos"] == antes_p and a.hoja.a_dict() == antes_h        # determinista y reversible: nada se escribió


def test_diseno_anterior_toma_linea_base_al_registrar_y_luego_detecta_cambios():
    a, _ = api(); _viejo(a)
    r = a.registrar_version_diseno("DIS-Resistencia")
    assert r["estado"] == "linea_base" and desc(a)["estado_definicion"] == "vigente" and desc(a)["version_diseno"] == 1
    a.editar(0, col(a, "Tiempo"), "77")
    assert desc(a)["estado_definicion"] == "cambiada"
    assert a.registrar_version_diseno("DIS-Resistencia")["estado"] == "nueva" and desc(a)["version_diseno"] == 2


def test_dmike_025_y_026_abren_sin_cambios_y_se_les_deriva_la_identidad(tmp_path):
    for version in ("0.25.0", "0.26.0"):
        ruta = tmp_path / f"c{version}.dmike"
        with gzip.open(S / f"caso_integral_v{version}.dmike.gz", "rb") as g, open(ruta, "wb") as f: shutil.copyfileobj(g, f)
        a = Api(); assert a.abrir_proyecto(str(ruta))["error"] is None
        claves = copy.deepcopy(a.proyecto.formatos["_disenos"])
        ds = a.disenos()
        assert len(ds) == len(claves) >= 1 and all(d["design_id"] == "DIS-" + d["clave"] and d["version_diseno"] == 1 for d in ds)
        assert all(d["run_ids"] == d["corridas"] for d in ds) and all(d["estado_definicion"] == "sin_linea_base" for d in ds)
        assert a.proyecto.formatos["_disenos"] == claves and MD.estado(a.proyecto)["valor"] == "demostracion"   # nada escrito, sigue siendo demostración
        assert all(c.rol != "run_id" for c in a.hoja.columnas)                               # la demo no gana columna


# ---------- receta en proyecto real ----------
def test_receta_real_con_diseno_crea_runid_y_no_precarga_respuestas(tmp_path):
    from app.nucleo import receta as RC
    rc = {"tipo": "dmike-receta", "receta_version": 2, "dmike_minimo": "0.26", "modo_proyecto": "real", "id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c11",
          "datos_fijos": {}, "hojas": [{"hoja": "Corridas", "origen_datos": "vacia", "columnas": []}],
          "disenos": [{"id": "d1", "modulo": "DISENO-RSM", "hoja": "Corridas", "respuestas": ["Resistencia"], "parametros": dict(DISENO)}]}
    rc["huella"] = RC.huella_receta({k: v for k, v in rc.items() if k != "huella"})
    ruta = tmp_path / "r.json"; ruta.write_text(json.dumps(rc), encoding="utf-8")
    a = Api(); r = a.ejecutar_receta(str(ruta)); assert r["error"] is None, r["sesion"][0]["texto"]
    assert MD.valor(a.proyecto) == "real" and col(a, "RunId") is not None and desc(a)["design_id"] == "DIS-Resistencia"
    assert all(v == "" for v in textos(a, "Resistencia"))                                    # sin respuestas inventadas ni precargadas


# ---------- interfaz ----------
def test_interfaz_runid_se_ve_de_solo_lectura_y_no_se_edita(pagina):
    from playwright.sync_api import expect
    r = pagina.api.ejecutar_modulo("DISENO-RSM", DISENO); assert r["error"] is None
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    expect(pagina.locator("#hoja-tabla td.ro:has-text(\"DIS-\")")).to_have_count(6)
    expect(pagina.locator("#hoja-tabla td.ro").first).to_contain_text("DIS-Resistencia-R")
    antes = pagina.locator("#hoja-tabla td.ro").first.inner_text()
    pagina.locator("#hoja-tabla td.ro").first.dblclick(); pagina.keyboard.type("intruso"); pagina.keyboard.press("Enter")
    expect(pagina.locator("#sesion")).to_contain_text("RunId es de solo lectura")
    assert pagina.locator("#hoja-tabla td.ro").first.inner_text() == antes
