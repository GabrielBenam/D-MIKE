"""E3-8: auditoría de un diseño (alias, aleatorización, restricciones, curvatura, falta de ajuste y confirmación). Cada revisión cita su fuente o dice «no respaldado»;
sin datos suficientes es «no evaluable»; sin respuestas no se muestra ningún valor p. Datos SINTÉTICOS."""
import csv, json, re
from app.api import Api
from app.nucleo import modo as MD, disenos as DIS

BASE = {"nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "respuesta": "Resistencia", "semilla": "7", "limites": "90, 130; 5, 40"}


def col(a, n): return a.hoja.indice(n)


def crea(demo=False, **p):
    a = Api()
    if demo: MD.fijar(a.proyecto, MD.DEMO, MD.DECLARADO)
    r = a.ejecutar_modulo("DISENO-RSM", {**BASE, **p}); assert r["error"] is None, r["sesion"][-1]["texto"]
    return a


def aud(a, did="DIS-Resistencia"):
    r = a.auditar_diseno(did); assert r["error"] is None, r
    return {x["id"]: x for x in r["auditoria"]["revisiones"]}


def responde(a, tmp, f=lambda t, ti: 50 + 0.5 * (t - 110) + 0.3 * (ti - 20) - 0.01 * (t - 110) ** 2):
    info = a.proyecto.formatos["_disenos"]["Resistencia"]; ids, _ = DIS.run_ids(a.hoja, info, "Resistencia")
    filas = [["RunId", "version_diseno", "Resistencia"]]
    for i in range(a.hoja.n):
        t = float(a.hoja.columnas[col(a, "Temp")].valor(i)[0]); ti = float(a.hoja.columnas[col(a, "Tiempo")].valor(i)[0])
        filas.append([ids[i], 1, f(t, ti) + 0.05 * (i % 3)])
    ruta = tmp / "r.csv"
    with open(ruta, "w", encoding="utf-8", newline="") as fh: csv.writer(fh).writerows(filas)
    assert a.importar_respuestas(str(ruta)).get("error") in (None, "")


# ---------- estructura y fuentes ----------
def test_siempre_hay_seis_revisiones_y_cada_una_cita_su_fuente():
    a = crea(tipo="ccd", alfa="caras"); r = aud(a)
    assert list(r) == ["alias", "aleatorizacion", "restricciones", "curvatura", "falta_ajuste", "confirmacion"]
    assert all(x["fuente"] and x["estado"] in ("cumple", "no_cumple", "no_evaluable", "no_aplica", "aviso") for x in r.values())
    assert "No respaldado" in r["aleatorizacion"]["fuente"] and "28_BB_SUPERFICIES_RESPUESTA" in r["curvatura"]["fuente"] and "REG-FALTA-AJUSTE" in r["falta_ajuste"]["fuente"]
    assert "26_BB_DOE_FRACCIONADOS" in r["alias"]["fuente"] and "no está respaldado" in r["alias"]["fuente"]


def test_diseno_inexistente():
    assert Api().auditar_diseno("DIS-No")["error"] == "auditoria"


def test_confirmacion_solo_avisa_que_no_hay_plan():
    r = aud(crea(tipo="fact")); assert r["confirmacion"]["estado"] == "aviso" and r["confirmacion"]["detalle"] == "No hay plan de confirmación registrado."


# ---------- alias ----------
def test_alias_de_un_fraccionado_lista_terminos_y_advierte_de_la_causalidad():
    a = Api(); r = a.ejecutar_modulo("DISENO-RSM", {"tipo": "frac", "nombres": "A1, B1, C1, D1", "bajos": "0, 0, 0, 0", "altos": "1, 1, 1, 1", "fraccion": "1",
                                                   "respuesta": "Y", "limites": "-1, 2; -1, 2; -1, 2; -1, 2"}); assert r["error"] is None, r["sesion"][-1]["texto"]
    x = aud(a, "DIS-Y")["alias"]
    assert x["estado"] == "aviso" and "I = ABCD" in x["detalle"] and "resolución 4" in x["detalle"] and "AB = CD" in x["detalle"] and "A = BCD" in x["detalle"]
    assert "no se interpreta como causal" in x["detalle"]


def test_alias_no_aplica_a_un_diseno_que_no_es_fraccionado():
    assert aud(crea(tipo="fact"))["alias"]["estado"] == "no_aplica"


# ---------- aleatorización ----------
def test_aleatorizado_y_en_su_orden_cumple_con_la_semilla():
    x = aud(crea(tipo="fact", aleatorio=True))["aleatorizacion"]; assert x["estado"] == "cumple" and "semilla 7" in x["detalle"]


def test_creado_sin_aleatorizar_no_cumple():
    x = aud(crea(tipo="fact", aleatorio=False))["aleatorizacion"]; assert x["estado"] == "no_cumple" and "sin aleatorizar" in x["detalle"]


def test_reordenar_la_hoja_deja_de_cumplir():
    a = crea(tipo="fact", aleatorio=True); j = col(a, "OrdenCorrida"); c = a.hoja.columnas[j].celdas
    c[0], c[1] = c[1], c[0]
    x = aud(a)["aleatorizacion"]; assert x["estado"] == "no_cumple" and "ya no es el de creación" in x["detalle"]


def test_diseno_anterior_sin_el_dato_es_no_evaluable():
    a = crea(tipo="fact")
    for k in ("aleatorizado", "semilla", "orden_creacion"): a.proyecto.formatos["_disenos"]["Resistencia"].pop(k)
    x = aud(a)["aleatorizacion"]; assert x["estado"] == "no_evaluable" and "antes de la 0.29" in x["detalle"]


# ---------- restricciones ----------
def test_restricciones_cumple_y_detecta_una_edicion_posterior():
    a = crea(tipo="fact"); assert aud(a)["restricciones"]["estado"] == "cumple"
    a.editar(0, col(a, "Temp"), "200")                                                                     # edición posterior a la creación, fuera de [90, 130]
    x = aud(a)["restricciones"]; assert x["estado"] == "no_cumple" and "Temp = 200 fuera de [90, 130]" in x["detalle"] and "DIS-Resistencia-R" in x["detalle"]


def test_restricciones_sin_region_es_no_evaluable():
    a = Api(); a.ejecutar_modulo("DISENO-RSM", {**BASE, "tipo": "fact", "limites": "", "limites_opcionales": True})
    x = aud(a)["restricciones"]; assert x["estado"] == "no_evaluable" and "no está declarada" in x["detalle"]


# ---------- curvatura y falta de ajuste ----------
def test_sin_respuestas_no_hay_valor_p_ni_cifras():
    a = crea(tipo="ccd", alfa="caras", centros="3"); r = aud(a)
    assert r["curvatura"]["estado"] == "no_evaluable" and r["falta_ajuste"]["estado"] == "no_evaluable"
    texto = json.dumps(r, ensure_ascii=False)
    assert "valor p" not in texto and "R²" not in texto and "Cpk" not in texto and "ahorro" not in texto.lower()


def test_con_respuestas_pero_sin_analisis_es_no_evaluable(tmp_path):
    a = crea(tipo="ccd", alfa="caras"); responde(a, tmp_path)
    assert aud(a)["curvatura"]["estado"] == "no_evaluable" and "No hay un análisis" in aud(a)["curvatura"]["detalle"]


def test_con_analisis_cita_el_p_y_el_alfa_del_propio_analisis(tmp_path):
    a = crea(tipo="ccd", alfa="caras", centros="3"); responde(a, tmp_path)
    r = a.ejecutar_modulo("RSM", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")], "modelo": "lineal_interacciones", "alfa": "0.01"}); assert r["error"] is None
    x = aud(a); c = x["curvatura"]
    assert c["estado"] in ("cumple", "no_cumple") and "nivel de significancia 0.01" in c["detalle"] and re.search(r"valor p = \d\.\d{4}", c["detalle"])
    assert x["falta_ajuste"]["estado"] in ("cumple", "no_cumple", "no_evaluable")


def test_sin_puntos_centrales_la_curvatura_es_no_evaluable(tmp_path):
    a = crea(tipo="ccd", alfa="caras")
    responde(a, tmp_path)
    a.ejecutar_modulo("RSM", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")], "modelo": "cuadratico"})
    assert aud(a)["curvatura"]["estado"] == "no_evaluable"                  # el modelo cuadrático ya incluye los cuadrados: no se prueba curvatura aparte


# ---------- solo en pantalla ----------
def test_la_auditoria_no_entra_al_paquete_de_avance(tmp_path):
    a = crea(tipo="fact"); a.proyecto.formatos["_receta"] = {"id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c21", "json": "{}", "ids": {}}
    ruta = tmp_path / "av.json"; r = a.exportar_avance(str(ruta))
    if r.get("error") is None:
        t = ruta.read_text(encoding="utf-8"); assert "auditoria" not in t and "revisiones" not in t and "aleatorizacion" not in t


def test_auditar_no_modifica_el_proyecto():
    a = crea(tipo="ccd", alfa="caras"); antes = json.dumps(a.proyecto.formatos, sort_keys=True, default=str); sucio = a._sucio
    aud(a); assert json.dumps(a.proyecto.formatos, sort_keys=True, default=str) == antes and a._sucio == sucio


# ---------- interfaz ----------
def test_interfaz_audita_el_diseno_y_omite_un_paso_con_motivo(pagina):
    from playwright.sync_api import expect
    r = pagina.api.ejecutar_modulo("DISENO-RSM", {**BASE, "tipo": "fact"}); assert r["error"] is None
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']"); pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.evaluate("ACCIONES_UI.disenos_dialogo()")
    pagina.click("#disenos button:has-text('Auditar diseño')")
    expect(pagina.locator("#auditoria")).to_contain_text("No hay plan de confirmación registrado."); expect(pagina.locator("#auditoria")).to_contain_text("Aleatorización")
    expect(pagina.locator("#auditoria")).to_contain_text("No respaldado por la base")
    pagina.click(".dialogo-botones button:has-text('Cerrar')")
    pagina.evaluate("ACCIONES_UI.disenos_dialogo()")
    expect(pagina.locator("#disenos")).to_contain_text("No se ha omitido ningún paso.")
    pagina.click("#disenos button:has-text('Omitir cribado')")
    pagina.locator(".dialogo").last.locator(".primario").click()                                  # sin motivo: no se omite
    assert pagina.api.omisiones() == []
    pagina.locator(".dialogo").last.locator("input").fill("Historial suficiente de los factores"); pagina.locator(".dialogo").last.locator(".primario").click()
    expect(pagina.locator("#disenos")).to_contain_text("Historial suficiente de los factores")
    assert pagina.api.omisiones()[0]["que"] == "cribado"
