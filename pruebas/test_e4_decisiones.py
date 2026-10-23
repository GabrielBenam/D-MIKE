"""Entrega 4: decisiones del proyecto (criterios 8 y 9 de ESPEC_flujo_real_dmaic), reglas de decisión e historial de cambios. Datos SINTÉTICOS."""
import json
from app.api import Api
from pruebas.test_e3_6_region import monta, rsm, col


# ---------- criterio 8: terminar la mejora sin DOE ----------
def test_mejora_sin_doe_exige_justificacion_y_queda_registrada(tmp_path):
    a = Api()
    r = a.registrar_mejora_sin_doe("   "); assert r["error"] == "decision" and "justificación" in r["sesion"][-1]["texto"] and a.decisiones()["decisiones"] == []
    r = a.registrar_mejora_sin_doe("El cambio de proveedor ya se verificó con 3 lotes"); assert r["error"] is None and r["decision"]["id"] == "DEC-001" and a._sucio
    d = a.decisiones()["decisiones"][0]; assert d["tipo"] == "mejora_sin_doe" and d["motivo"].startswith("El cambio") and d["fecha"]
    assert a.registrar_mejora_sin_doe("otra", "no-existe")["error"] == "decision"                  # una evidencia citada debe existir


def test_la_decision_se_guarda_con_el_proyecto(tmp_path):
    from app.nucleo import archivo as AR
    a = Api(); a.registrar_mejora_sin_doe("Sin DOE por costo y riesgo bajo"); ruta = str(tmp_path / "p.dmike"); AR.guardar(ruta, a.hoja, a.proyecto, "0.29.0")
    b = Api(); assert b.abrir_proyecto(ruta)["error"] is None and b.decisiones()["decisiones"][0]["motivo"] == "Sin DOE por costo y riesgo bajo"


# ---------- criterio 9: segundo DOE solo tras revisar la evidencia del primero ----------
def test_segundo_doe_sin_respuestas_se_rechaza(tmp_path):
    a = Api(); a.ejecutar_modulo("DISENO-RSM", {"nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "respuesta": "Resistencia", "semilla": "7", "limites": "90, 130; 5, 40", "tipo": "fact"})
    r = a.recomendar_segundo_doe("DIS-Resistencia", "Hay curvatura"); assert r["error"] == "decision" and "no tiene respuestas capturadas" in r["sesion"][-1]["texto"] and a.decisiones()["decisiones"] == []


def test_segundo_doe_con_respuestas_pero_sin_analisis_se_rechaza(tmp_path):
    a = monta(tmp_path, tipo="fact"); r = a.recomendar_segundo_doe("DIS-Resistencia", "Hay curvatura")
    assert r["error"] == "decision" and "no hay un análisis guardado" in r["sesion"][-1]["texto"]


def test_segundo_doe_con_analisis_registra_la_evidencia_y_pide_motivo(tmp_path):
    a = monta(tmp_path, tipo="fact", f=lambda t, ti: 60 - 0.05 * (t - 118) ** 2 - 0.04 * (ti - 22) ** 2)
    assert a.ejecutar_modulo("FACTORIAL", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")]})["error"] is None
    assert a.recomendar_segundo_doe("DIS-Resistencia", "")["error"] == "decision"                      # sin motivo no
    r = a.recomendar_segundo_doe("DIS-Resistencia", "El cribado mostró curvatura"); assert r["error"] is None, r["sesion"][-1]["texto"]
    ev = r["decision"]["evidencia"]; assert r["decision"]["design_id"] == "DIS-Resistencia" and ev["alfa"] == 0.05 and "curvatura_p" in ev and ev["respuestas"] == a.hoja.n
    assert a.recomendar_segundo_doe("DIS-No", "x")["error"] == "decision"


# ---------- reglas e historial ----------
def test_las_reglas_citan_su_fuente():
    reglas = Api().decisiones()["reglas"]; assert {r["id"] for r in reglas} == {"mejora_sin_doe", "segundo_doe", "confirmacion"} and all("ESPEC_flujo" in r["fuente"] for r in reglas)


def test_el_historial_reune_lo_ya_registrado_sin_modificar_nada(tmp_path):
    a = monta(tmp_path, tipo="fact"); a.omitir_paso_doe("dcc", "Sin curvatura")
    a.registrar_plan_confirmacion(tipo="confirmacion", n_corridas=1, criterio="c", condiciones="d", origen="o", predicho=50)
    a.registrar_mejora_sin_doe("Cambio documentado")
    a.editar(0, col(a, "Temp"), "125"); a.registrar_version_diseno("DIS-Resistencia", "Cambió una temperatura")
    antes = json.dumps(a.proyecto.formatos, sort_keys=True, default=str)
    h = a.historial_cambios(); que = [e["que"] for e in h]
    assert {"Versión de diseño", "Importación de respuestas", "Paso omitido", "Plan de confirmación", "Decisión"} <= set(que)
    assert [e["fecha"] for e in h] == sorted((e["fecha"] for e in h), reverse=True) and json.dumps(a.proyecto.formatos, sort_keys=True, default=str) == antes


# ---------- paquete de avance ----------
def test_el_paquete_lleva_las_decisiones_sin_el_motivo(tmp_path):
    a = Api(); a.registrar_mejora_sin_doe("Motivo reservado del usuario")
    a.proyecto.formatos["_receta"] = {"id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c33", "json": "{}", "ids": {}}
    ruta = tmp_path / "av.json"; assert a.exportar_avance(str(ruta)).get("error") is None
    t = ruta.read_text(encoding="utf-8"); pkg = json.loads(t)
    assert pkg["decisiones"] == [{"id": "DEC-001", "tipo": "mejora_sin_doe", "design_id": None}] and "Motivo reservado" not in t


# ---------- interfaz ----------
def test_interfaz_registra_una_decision_y_muestra_el_historial(pagina):
    from playwright.sync_api import expect
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']"); pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.evaluate("ACCIONES_UI.disenos_dialogo()")
    expect(pagina.locator("#decisiones")).to_contain_text("No hay decisiones registradas.")
    pagina.click("#decisiones button:has-text('Terminar la mejora sin DOE')")
    pagina.locator(".dialogo").last.locator(".primario").click()                                  # sin justificación: no se registra
    assert pagina.api.decisiones()["decisiones"] == []
    pagina.locator(".dialogo").last.locator("input[name='motivo']").fill("Verificado con tres lotes"); pagina.locator(".dialogo").last.locator(".primario").click()
    expect(pagina.locator("#decisiones")).to_contain_text("DEC-001"); expect(pagina.locator("#decisiones")).to_contain_text("Verificado con tres lotes")
    pagina.click("#decisiones button:has-text('Historial de cambios')")
    expect(pagina.locator("#historial")).to_contain_text("Decisión"); expect(pagina.locator("#historial")).to_contain_text("Terminar la mejora sin DOE")


# ---------- TUKEY: método no incluido en la base del curso ----------
def test_tukey_dice_que_no_esta_en_la_base_y_con_que_se_verifico():
    a = Api(); a.pegar(-1, 0, "y\tg\n" + "\n".join(f"{v}\t{g}" for g, vs in (("A", [1.9, 1.8, 2.1, 1.8]), ("B", [1.6, 1.1, 1.3, 1.4, 1.1]), ("C", [1.3, 1.6, 1.8, 1.1, 1.5, 1.1])) for v in vs))
    r = a.ejecutar_modulo("TUKEY", {"y": 0, "factor": 1})["resultado"]
    texto = " ".join(b.get("texto", "") for b in r["bloques"])
    assert "Método no incluido en la base del curso" in texto and "ejemplo 11.1" in texto and "no es una fuente del curso" in texto
    g = next(b for b in r["bloques"] if b["tipo"] == "grafica" and b.get("inter", {}).get("g") == "tukey")
    assert g["inter"]["nota"] == "Método no incluido en la base del curso" and "Método no incluido en la base del curso" in g["svg"]
