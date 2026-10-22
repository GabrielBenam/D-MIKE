"""Casos de extremo a extremo E2E-C y E2E-D de ESPEC_flujo_real_dmaic sección 11, con datos SINTÉTICOS (solo en estas pruebas; un proyecto real nunca los genera):
E2E-C: factorial de cribado con límites seguros → respuestas por corrida (RunId) → análisis → sin curvatura, no hace falta DCC (omisión con motivo) → plan de confirmación.
E2E-D: el cribado encuentra curvatura → segundo DOE (DCC) permitido → respuestas por RunId → modelo → óptimo dentro de la región → confirmación."""
import csv
from app.api import Api
from app.nucleo import disenos as DIS

LIM = "80, 140; 5, 45"
BASE = {"nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "limites": LIM, "semilla": "11", "tipo": "fact", "centros": "3"}


def col(a, n): return a.hoja.indice(n)
def num(a, n, i): return float(a.hoja.columnas[col(a, n)].valor(i)[0])


def importa(a, tmp, resp, f, nombre):
    clave = resp; info = a.proyecto.formatos["_disenos"][clave]; ids, _ = DIS.run_ids(a.hoja, info, clave)
    filas = [["RunId", "version_diseno", resp]]
    for i in range(a.hoja.n):
        if ids[i]: filas.append([ids[i], info.get("version_diseno", 1), round(f(num(a, info["factores"][0]["nombre"], i), num(a, info["factores"][1]["nombre"], i)) + 0.02 * (i % 3), 6)])
    ruta = tmp / nombre
    with open(ruta, "w", encoding="utf-8", newline="") as fh: csv.writer(fh).writerows(filas)
    r = a.importar_respuestas(str(ruta), "DIS-" + resp); assert r.get("error") in (None, ""), r["sesion"][-1]["texto"]


def test_e2e_c_cribado_sin_curvatura_omite_el_dcc_y_confirma(tmp_path):
    a = Api()
    r = a.ejecutar_modulo("DISENO-RSM", {**BASE, "respuesta": "Fuerza"}); assert r["error"] is None, r["sesion"][-1]["texto"]
    assert a.disenos()[0]["respuestas"]["n"] == 0 and a.disenos()[0]["region"] == "declarada"          # el diseño nace sin respuestas
    importa(a, tmp_path, "Fuerza", lambda t, ti: 40 + 0.3 * (t - 110) + 0.2 * (ti - 20) + 0.004 * (t - 110) * (ti - 20), "fuerza.csv")
    r = a.ejecutar_modulo("FACTORIAL", {"y": col(a, "Fuerza"), "xs": [col(a, "Temp"), col(a, "Tiempo")]}); assert r["error"] is None, r["sesion"][-1]["texto"]
    rev = {x["id"]: x for x in a.auditar_diseno("DIS-Fuerza")["auditoria"]["revisiones"]}
    assert rev["curvatura"]["estado"] == "cumple" and rev["restricciones"]["estado"] == "cumple" and rev["aleatorizacion"]["estado"] == "cumple"
    assert rev["confirmacion"]["detalle"] == "No hay plan de confirmación registrado."
    assert a.omitir_paso_doe("dcc", "Sin curvatura: el modelo de primer orden basta")["estado"] == "omitido"           # no se necesita DCC
    p = a.registrar_plan_confirmacion(tipo="confirmacion", n_corridas=2, criterio="Diferencia de la media menor a 1.5", condiciones="Lote nuevo, mismo horno",
                                      origen="Factorial de Fuerza en Temp = 120, Tiempo = 30", design_id="DIS-Fuerza", predicho=40 + 0.3 * 10 + 0.2 * 10 + 0.004 * 100)
    assert p["error"] is None
    a.registrar_observados_confirmacion("CONF-001", "45.2; 45.6")
    c = a.comparar_confirmacion("CONF-001")["comparacion"]
    assert abs(c["diferencia_media"] - (45.4 - 45.4)) < 0.2 and c["intervalo"] is None and "No respaldado" in c["nota_intervalo"]
    assert {x["id"]: x for x in a.auditar_diseno("DIS-Fuerza")["auditoria"]["revisiones"]}["confirmacion"]["estado"] == "cumple"
    assert a.omisiones()[0]["que"] == "dcc"


def test_e2e_d_curvatura_segundo_doe_dcc_optimo_en_la_region_y_confirmacion(tmp_path):
    a = Api()
    curvo = lambda t, ti: 60 - 0.05 * (t - 118) ** 2 - 0.04 * (ti - 22) ** 2 + 0.05 * (t - 110) * (ti - 20)
    assert a.ejecutar_modulo("DISENO-RSM", {**BASE, "respuesta": "Cribado"})["error"] is None
    importa(a, tmp_path, "Cribado", curvo, "cribado.csv")
    assert a.ejecutar_modulo("FACTORIAL", {"y": col(a, "Cribado"), "xs": [col(a, "Temp"), col(a, "Tiempo")]})["error"] is None
    c1 = {x["id"]: x for x in a.auditar_diseno("DIS-Cribado")["auditoria"]["revisiones"]}["curvatura"]
    assert c1["estado"] == "no_cumple" and "la curvatura es significativa" in c1["detalle"]                  # el cribado encuentra curvatura
    # segundo DOE: DCC en las caras, dentro de la región autorizada
    r = a.ejecutar_modulo("DISENO-RSM", {**BASE, "tipo": "ccd", "alfa": "caras", "respuesta": "Resistencia"}); assert r["error"] is None, r["sesion"][-1]["texto"]
    assert [d["design_id"] for d in a.disenos()] == ["DIS-Cribado", "DIS-Resistencia"]
    importa(a, tmp_path, "Resistencia", curvo, "dcc.csv")
    fuera = a.ejecutar_modulo("DISENO-RSM", {**BASE, "tipo": "ccd", "alfa": "rotable", "respuesta": "Otra", "limites": "100, 120; 10, 30"})
    assert fuera["error"] == "entrada" and "punto axial" in fuera["sesion"][-1]["texto"]                    # un DCC rotable sale de la región: se rechaza
    fn = [f["nombre"] for f in a.proyecto.formatos["_disenos"]["Resistencia"]["factores"]]            # el segundo diseño trae sus propias columnas de factores
    r = a.ejecutar_modulo("RSM", {"y": col(a, "Resistencia"), "xs": [col(a, fn[0]), col(a, fn[1])]}); assert r["error"] is None, r["sesion"][-1]["texto"]
    assert a.proyecto.resultados[-1]["datos"]["modelo_rsm"]["region"]["estado"] == "declarada"
    uid = a.proyecto.resultados[-1]["uid"]
    o = a.ejecutar_modulo("OPTIMIZADOR", {"r1": uid, "meta1": "max", "inf1": 40, "obj1": 60, "peso1": 1, "imp1": 1}); assert o["error"] is None
    fila = next(b for b in o["resultado"]["bloques"] if b.get("titulo") == "Ajuste óptimo de los factores")["filas"]
    assert 100 <= float(fila[0][1]) <= 120 and 10 <= float(fila[1][1]) <= 30                                # el óptimo no sale de la región
    aud = {x["id"]: x for x in a.auditar_diseno("DIS-Resistencia")["auditoria"]["revisiones"]}
    assert aud["restricciones"]["estado"] == "cumple" and aud["falta_ajuste"]["estado"] in ("cumple", "no_cumple", "no_evaluable")
    p = a.registrar_plan_confirmacion(tipo="confirmacion", n_corridas=3, criterio="Media dentro de 1 unidad de la predicha", condiciones="3 probetas, lote nuevo",
                                      origen="Optimizador sobre el modelo RSM de Resistencia", design_id="DIS-Resistencia", predicho=float(next(b for b in o["resultado"]["bloques"] if b.get("titulo") == "Respuestas")["filas"][0][5]),
                                      resultado_uid=o["resultado"]["uid"])
    assert p["error"] is None and p["plan"]["predicho"]["tipo_modelo"] == "otro"                          # modelo de superficie: sin intervalo
    a.registrar_observados_confirmacion("CONF-001", "59.5; 60.1; 59.8")
    c = a.comparar_confirmacion("CONF-001")["comparacion"]; assert c["intervalo"] is None and "no hay veredicto" in c["nota_intervalo"] and c["faltan"] == 0
