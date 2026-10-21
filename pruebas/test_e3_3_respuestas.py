"""E3-3: respuestas de un diseño por RunId con verificación de niveles y de versión; no se mezclan versiones; un proyecto real nunca genera ni precarga
respuestas sintéticas. ESPEC_flujo_real_dmaic sección 5 y criterios 5 y 6. Datos SINTÉTICOS."""
import csv, gzip, hashlib, json, shutil
from pathlib import Path
import pytest
from app.api import Api
from app.nucleo import modo as MD, disenos as DIS

DISENO = {"tipo": "fact", "nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "centros": "2", "replicas": "1",
          "respuesta": "Resistencia", "aleatorio": True, "semilla": "7", "limites": "90, 130; 5, 40"}


def api(demo=False, **extra):
    a = Api()
    if demo: MD.fijar(a.proyecto, MD.DEMO, MD.DECLARADO)
    r = a.ejecutar_modulo("DISENO-RSM", {**DISENO, **extra}); assert r["error"] is None, r["sesion"][0]["texto"]
    return a


def col(a, n): return a.hoja.indice(n)


def celdas(a, n): return list(a.hoja.columnas[col(a, n)].celdas[:a.hoja.n])


def d0(a): return a.disenos()[0]


def corridas(a):
    """[(RunId, Temp, Tiempo, OrdenEst)] de la hoja, en el orden de la hoja."""
    ids, _ = DIS.run_ids(a.hoja, a.proyecto.formatos["_disenos"]["Resistencia"], "Resistencia")
    return [(ids[i], a.hoja.columnas[col(a, "Temp")].valor(i)[0], a.hoja.columnas[col(a, "Tiempo")].valor(i)[0], int(a.hoja.columnas[col(a, "OrdenEst")].valor(i)[2]))
            for i in range(a.hoja.n)]


def escribir(tmp, filas, nombre="resp.csv"):
    ruta = tmp / nombre
    with open(ruta, "w", encoding="utf-8", newline="") as f: csv.writer(f).writerows(filas)
    return str(ruta)


def archivo(a, tmp, version=1, factores=True, valor=lambda oe: 50 + oe * 1.5, invertir=True, nombre="resp.csv", resp="Resistencia"):
    filas = [["RunId", "version_diseno"] + (["Temp", "Tiempo"] if factores else []) + [resp]]
    cuerpo = [[r, version] + ([t, ti] if factores else []) + [valor(oe)] for r, t, ti, oe in corridas(a)]
    if invertir: cuerpo.reverse()
    return escribir(tmp, filas + cuerpo, nombre)


def importa(a, ruta, **k):
    r = a.importar_respuestas(ruta, **k); return r


def errores(r): return r["importacion"]["errores"]


# ---------- importación por RunId ----------
def test_importa_por_runid_y_no_por_posicion(tmp_path):
    a = api(); ruta = archivo(a, tmp_path)                                 # el archivo va en orden inverso al de la hoja
    r = importa(a, ruta); assert r["error"] is None and r["importacion"]["escritas"] == 6
    for rid, t, ti, oe in corridas(a):
        i = [c[0] for c in corridas(a)].index(rid)
        assert float(celdas(a, "Resistencia")[i]) == 50 + oe * 1.5          # cada respuesta cayó en la corrida de su RunId
    d = d0(a)
    assert d["respuestas"] == {"n": 6, "version": 1} and d["importaciones"] == 1
    imp = a.proyecto.formatos["_disenos"]["Resistencia"]["importaciones"][0]
    assert imp["archivo"] == "resp.csv" and imp["huella"] == hashlib.sha256(Path(ruta).read_bytes()).hexdigest() and imp["version"] == 1 and imp["escritas"] == 6


def test_importa_excel_y_sin_columnas_de_factores_con_aviso(tmp_path):
    import openpyxl
    a = api(); wb = openpyxl.Workbook(); ws = wb.active
    ws.append(["RunId", "version_diseno", "Resistencia"])
    for rid, *_resto, oe in corridas(a): ws.append([rid, 1, 40 + oe])
    ruta = str(tmp_path / "r.xlsx"); wb.save(ruta)
    r = importa(a, ruta); assert r["error"] is None and r["importacion"]["escritas"] == 6
    assert any("no trae las columnas de los factores" in x for x in r["importacion"]["avisos"])


def test_reimportar_el_mismo_archivo_es_idempotente(tmp_path):
    a = api(); ruta = archivo(a, tmp_path); importa(a, ruta)
    r = importa(a, ruta); assert r["error"] is None and r["importacion"]["escritas"] == 0 and r["importacion"]["iguales"] == 6


def test_demostracion_importa_igual(tmp_path):
    a = api(demo=True); r = importa(a, archivo(a, tmp_path)); assert r["error"] is None and d0(a)["respuestas"]["n"] == 6


# ---------- rechazos atómicos ----------
def rechaza(a, ruta, fragmento, **k):
    antes = celdas(a, "Resistencia"); proy = json.dumps(a.proyecto.formatos["_disenos"], sort_keys=True, default=str)
    r = importa(a, ruta, **k)
    assert r["error"] == "respuestas", r["sesion"][-1]["texto"]
    assert any(fragmento in e for e in errores(r)), errores(r)
    assert celdas(a, "Resistencia") == antes and json.dumps(a.proyecto.formatos["_disenos"], sort_keys=True, default=str) == proy       # no se escribió nada
    return r


def test_rechaza_corrida_repetida(tmp_path):
    a = api(); filas = list(csv.reader(open(archivo(a, tmp_path), encoding="utf-8")))
    rechaza(a, escribir(tmp_path, filas + [filas[1]], "dup.csv"), "Corridas repetidas en el archivo")


def test_rechaza_version_incompatible(tmp_path):
    a = api(); r = rechaza(a, archivo(a, tmp_path, version=2), "Versión de diseño incompatible (la vigente es la 1)")
    assert "trae versión «2»" in errores(r)[0]
    rechaza(a, archivo(a, tmp_path, version=0, nombre="v0.csv"), "Versión de diseño incompatible")


def test_rechaza_runid_que_no_es_del_diseno(tmp_path):
    a = api(); filas = list(csv.reader(open(archivo(a, tmp_path), encoding="utf-8")))
    filas[1][0] = "DIS-Resistencia-R099"
    rechaza(a, escribir(tmp_path, filas, "x.csv"), "RunId que no pertenecen a DIS-Resistencia")


def test_rechaza_respuesta_asociada_al_factor_equivocado(tmp_path):
    a = api(); filas = list(csv.reader(open(archivo(a, tmp_path), encoding="utf-8")))
    cab = filas[0]; it, itm = cab.index("Temp"), cab.index("Tiempo")
    for f in filas[1:]: f[it], f[itm] = f[itm], f[it]                      # columnas de factores intercambiadas
    r = rechaza(a, escribir(tmp_path, filas, "sw.csv"), "Los niveles no coinciden con los del diseño")
    assert "Temp del archivo" in errores(r)[0] or "Tiempo del archivo" in errores(r)[0]
    # un RunId puesto en la corrida equivocada también se detecta por sus niveles
    filas = list(csv.reader(open(archivo(a, tmp_path, nombre="ok.csv"), encoding="utf-8")))
    filas[1][0], filas[2][0] = filas[2][0], filas[1][0]
    rechaza(a, escribir(tmp_path, filas, "id.csv"), "Los niveles no coinciden")


def test_rechaza_faltas_de_columnas_obligatorias_y_filas_sin_runid(tmp_path):
    a = api(); ruta = archivo(a, tmp_path)
    filas = list(csv.reader(open(ruta, encoding="utf-8")))
    sin_run = [[c for i, c in enumerate(f) if i != 0] for f in filas]
    rechaza(a, escribir(tmp_path, sin_run, "s1.csv"), "Falta la columna RunId")                         # por posición nunca
    sin_ver = [[c for i, c in enumerate(f) if i != 1] for f in filas]
    rechaza(a, escribir(tmp_path, sin_ver, "s2.csv"), "Falta la columna version_diseno")
    sin_resp = [f[:-1] for f in filas]
    rechaza(a, escribir(tmp_path, sin_resp, "s3.csv"), "Falta la columna de la respuesta «Resistencia»")
    huerfana = [list(f) for f in filas]; huerfana[2][0] = ""
    rechaza(a, escribir(tmp_path, huerfana, "s4.csv"), "Filas con respuesta y sin RunId")


def test_rechaza_respuestas_que_no_son_numeros(tmp_path):
    a = api(); filas = list(csv.reader(open(archivo(a, tmp_path), encoding="utf-8"))); filas[1][-1] = "alto"
    rechaza(a, escribir(tmp_path, filas, "n.csv"), "Respuestas que no son números")


def test_rechaza_si_la_definicion_cambio_sin_registrar(tmp_path):
    a = api(); ruta = archivo(a, tmp_path)
    a.editar(0, col(a, "Temp"), "999")
    rechaza(a, ruta, "cambió y no está registrada")


def test_respuestas_existentes_distintas_se_rechazan_salvo_sobrescribir(tmp_path):
    a = api(); importa(a, archivo(a, tmp_path)); a.editar(0, col(a, "Resistencia"), "1")
    ruta = archivo(a, tmp_path, nombre="otra.csv")
    rechaza(a, ruta, "Ya hay respuestas distintas en la hoja")
    r = importa(a, ruta, sobrescribir=True); assert r["error"] is None and r["importacion"]["sobrescritas"] == 1
    assert a.proyecto.formatos["_disenos"]["Resistencia"]["importaciones"][-1]["sobrescritas"] == 1          # queda auditado


def test_varios_disenos_se_distinguen_por_el_runid_y_no_se_mezclan(tmp_path):
    a = api(); a.ejecutar_modulo("DISENO-RSM", {**DISENO, "nombres": "P, Q"})
    ds = {x["respuesta"]: x["design_id"] for x in a.disenos()}
    assert ds == {"Resistencia": "DIS-Resistencia", "Resistencia_2": "DIS-Resistencia_2"}
    filas = list(csv.reader(open(archivo(a, tmp_path), encoding="utf-8")))            # RunId del primer diseño
    r = importa(a, escribir(tmp_path, filas, "ok.csv")); assert r["error"] is None and r["importacion"]["design_id"] == "DIS-Resistencia"
    mezcla = filas + [["DIS-Resistencia_2-R001", 1] + ["", ""] + [5]]
    r2 = importa(a, escribir(tmp_path, mezcla, "mez.csv"), sobrescribir=True)
    assert r2["error"] == "respuestas" and any("más de un diseño" in e for e in errores(r2))


# ---------- sin datos y N/A ----------
def test_respuesta_vacia_no_se_toma_como_cero_y_na_se_respeta(tmp_path):
    a = api(); filas = list(csv.reader(open(archivo(a, tmp_path), encoding="utf-8")))
    filas[1][-1] = ""; filas[2][-1] = "N/A"
    r = importa(a, escribir(tmp_path, filas, "v.csv")); assert r["error"] is None
    assert r["importacion"]["sin_dato"] == 1 and r["importacion"]["escritas"] == 5
    assert any("Sin datos: 1 corridas" in x for x in r["importacion"]["avisos"])
    vals = celdas(a, "Resistencia"); assert "0" not in vals and vals.count(None) + vals.count("") == 1 and "N/A" in vals


# ---------- versiones: no se mezclan ----------
def _registrar_cambio(a):
    """Sube la temperatura alta de 120 a 140 (y el centro de 110 a 120): sigue siendo un factorial de 2 niveles con centros, pero otra definición."""
    nuevo = {"100": "100", "120": "140", "110": "120"}
    for i, t in enumerate(a.hoja.columnas[col(a, "Temp")].celdas[:a.hoja.n]): a.editar(i, col(a, "Temp"), nuevo[t])
    r = a.registrar_version_diseno("DIS-Resistencia", "Cambió la temperatura alta"); assert r["estado"] == "nueva"


def test_analisis_rechaza_respuestas_de_otra_version_y_se_resuelve_con_importacion_nueva(tmp_path):
    a = api(); importa(a, archivo(a, tmp_path))
    p = {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")]}
    assert a.ejecutar_modulo("FACTORIAL", p)["error"] is None                               # versión 1 con respuestas de la versión 1: corre
    _registrar_cambio(a)                                                                    # versión 2; las respuestas son de la 1
    r = a.ejecutar_modulo("FACTORIAL", p)
    assert r["error"] == "entrada" and "son de la versión 1" in r["sesion"][-1]["texto"] and "no se mezclan versiones" in r["sesion"][-1]["texto"]
    assert a.ejecutar_modulo("RSM", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")], "modelo": "lineal"})["error"] == "entrada"
    # importar versión 2 con respuestas de la 1 en la hoja: tampoco se mezcla
    rechaza(a, archivo(a, tmp_path, version=2, nombre="v2.csv"), "ya tiene respuestas de la versión 1")
    # se borran las respuestas y se importan las de la versión 2
    a.borrar_rango(0, col(a, "Resistencia"), a.hoja.n - 1, col(a, "Resistencia"))
    assert d0(a)["respuestas"] == {"n": 0, "version": None}
    r = importa(a, archivo(a, tmp_path, version=2, nombre="v2b.csv")); assert r["error"] is None and d0(a)["respuestas"] == {"n": 6, "version": 2}
    assert a.ejecutar_modulo("FACTORIAL", p)["error"] is None


def test_confirmacion_manual_auditable_exige_motivo(tmp_path):
    a = api(); importa(a, archivo(a, tmp_path)); _registrar_cambio(a)
    r = a.confirmar_respuestas_diseno("DIS-Resistencia", ""); assert r["error"] == "confirmar" and "motivo" in r["sesion"][-1]["texto"]
    r = a.confirmar_respuestas_diseno("DIS-Resistencia", "Solo cambió el nombre de un nivel, las corridas son las mismas")
    assert r["error"] is None and r["estado"] == "confirmadas" and d0(a)["respuestas"]["version"] == 2
    log = a.proyecto.formatos["_disenos"]["Resistencia"]["confirmaciones_respuestas"]
    assert log[0]["de_version"] == 1 and log[0]["a_version"] == 2 and "mismas" in log[0]["motivo"]
    p = {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")]}
    assert a.ejecutar_modulo("FACTORIAL", p)["error"] is None
    assert a.confirmar_respuestas_diseno("DIS-Resistencia", "otra")["estado"] == "sin_cambios"


def test_analisis_rechaza_si_la_definicion_cambio_sin_registrar(tmp_path):
    a = api(); importa(a, archivo(a, tmp_path)); a.editar(0, col(a, "Temp"), "130")
    r = a.ejecutar_modulo("FACTORIAL", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")]})
    assert r["error"] == "entrada" and "no está registrada" in r["sesion"][-1]["texto"]


def test_respuestas_tecleadas_a_mano_se_etiquetan_con_la_version_vigente():
    a = api()
    for i in range(a.hoja.n): a.editar(i, col(a, "Resistencia"), str(50 + i))
    assert d0(a)["respuestas"] == {"n": 6, "version": 1}
    assert a.ejecutar_modulo("FACTORIAL", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")]})["error"] is None


def test_deshacer_quita_las_respuestas_importadas_y_su_etiqueta(tmp_path):
    a = api(); importa(a, archivo(a, tmp_path)); assert d0(a)["respuestas"]["n"] == 6
    a.deshacer(); assert d0(a)["respuestas"] == {"n": 0, "version": None} and all(c in (None, "") for c in celdas(a, "Resistencia"))


# ---------- diseños anteriores a 0.29 ----------
def test_diseno_anterior_importa_y_toma_linea_base(tmp_path):
    a = api(); info = a.proyecto.formatos["_disenos"]["Resistencia"]
    for k in ("design_id", "version_diseno", "huella_diseno", "historial_versiones", "orden_est", "orden_corrida", "col_runid"): info.pop(k, None)
    a.hoja.eliminar_columna(col(a, "RunId")); assert d0(a)["estado_definicion"] == "sin_linea_base"
    r = importa(a, archivo(a, tmp_path)); assert r["error"] is None, errores(r) if "importacion" in r else r["sesion"][-1]["texto"]
    d = d0(a); assert d["estado_definicion"] == "vigente" and d["respuestas"] == {"n": 6, "version": 1}
    assert any("anterior a 0.29" in x for x in r["importacion"]["avisos"])


# ---------- un proyecto real nunca genera ni precarga respuestas sintéticas ----------
def test_real_el_diseno_nace_sin_respuestas_y_solo_se_escribe_lo_importado(tmp_path):
    a = api(); assert MD.valor(a.proyecto) == "real" and d0(a)["respuestas"]["n"] == 0
    assert all(c in (None, "") for c in celdas(a, "Resistencia"))
    filas = list(csv.reader(open(archivo(a, tmp_path), encoding="utf-8")))[:4]                 # solo 3 corridas
    r = importa(a, escribir(tmp_path, filas, "parcial.csv")); assert r["error"] is None and r["importacion"]["escritas"] == 3
    v = celdas(a, "Resistencia"); assert sum(1 for x in v if x not in (None, "")) == 3 and sum(1 for x in v if x in (None, "")) == 3     # lo demás sigue vacío


def test_real_no_genera_datos_aleatorios_sobre_las_respuestas():
    a = api(); antes = celdas(a, "Resistencia")
    r = a.ejecutar_modulo("ALEATORIOS", {"destino": "Resistencia", "n": "6", "distribucion": "normal"})
    assert r["error"] is not None and celdas(a, "Resistencia") == antes and d0(a)["respuestas"]["n"] == 0


def test_real_rechaza_recetas_con_datos_sinteticos_y_no_crea_el_diseno(tmp_path):
    from app.nucleo import receta as RC
    rc = {"tipo": "dmike-receta", "receta_version": 2, "dmike_minimo": "0.26", "modo_proyecto": "real", "id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c12",
          "datos_fijos": {}, "hojas": [{"hoja": "Corridas", "origen_datos": "sintetico", "columnas": []}],
          "disenos": [{"id": "d1", "modulo": "DISENO-RSM", "hoja": "Corridas", "respuestas": ["Resistencia"], "parametros": dict(DISENO)}]}
    rc["huella"] = RC.huella_receta({k: v for k, v in rc.items() if k != "huella"})
    ruta = tmp_path / "s.json"; ruta.write_text(json.dumps(rc), encoding="utf-8")
    a = Api(); r = a.abrir_receta(str(ruta))
    assert r["error"] == "receta" and "no se cargan datos sintéticos" in r["sesion"][-1]["texto"]
    assert a.hoja.n == 0 and not a.proyecto.formatos.get("_disenos")


# ---------- caso maestro: la demo no cambia ----------
def test_caso_maestro_con_diseno_etiquetado_sigue_reproduciendo(tmp_path):
    S = Path(__file__).parent / "sinteticos"
    a = Api(); r = a.ejecutar_receta(str(S / "caso_integral_datos_llenos.xlsx")); assert r["error"] is None
    assert len(a.resultados()) == 17 and all(d["respuestas"]["version"] in (None, 1) for d in a.disenos())
    assert all(a.reproducir_resultado(x["uid"])["error"] is None for x in a.resultados())


# ---------- interfaz ----------
def test_interfaz_disenos_del_proyecto_registra_version_y_el_menu_trae_las_opciones(pagina, tmp_path):
    from playwright.sync_api import expect
    r = pagina.api.ejecutar_modulo("DISENO-RSM", DISENO); assert r["error"] is None
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']"); pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.click(".menu > button:text-is('Estadística')")
    expect(pagina.locator("text=Importar respuestas del diseño…")).to_be_visible(); expect(pagina.locator("text=Diseños del proyecto…")).to_be_visible()
    pagina.click("text=Diseños del proyecto…")
    expect(pagina.locator("#disenos")).to_contain_text("DIS-Resistencia · versión 1 · 6 corridas"); expect(pagina.locator("#disenos")).to_contain_text("Definición: vigente")
    pagina.click(".dialogo-botones button:has-text('Cerrar')")
    pagina.api.editar(0, col(pagina.api, "Temp"), "130")                         # cambia un nivel real de Temp: la definición cambia
    pagina.evaluate("ACCIONES_UI.disenos_dialogo()")
    expect(pagina.locator("#disenos")).to_contain_text("cambió: registra una versión nueva")
    pagina.click("#disenos button:has-text('Registrar versión nueva')")
    pagina.locator(".dialogo").last.locator("input").fill("Cambió una temperatura"); pagina.locator(".dialogo").last.locator(".primario").click()
    expect(pagina.locator("#disenos")).to_contain_text("versión 2"); expect(pagina.locator("#disenos")).to_contain_text("v1 (Cambió una temperatura)")
