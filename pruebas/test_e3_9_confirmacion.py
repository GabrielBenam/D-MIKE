"""E3-9: plan de confirmación (confirmación experimental o vigilancia posterior). Tipo, número de corridas, criterio de éxito y condiciones los define el usuario; el
valor predicho lleva su origen. Observado menos predicho siempre; el intervalo de predicción solo en regresión simple (27_BB REG-PREDICCION); modelos múltiples o de
superficie: «no respaldado» y sin veredicto. Datos SINTÉTICOS."""
import json
from app.api import Api
from app.nucleo import archivo as AR

BASE = {"nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "respuesta": "Resistencia", "semilla": "7", "limites": "90, 130; 5, 40", "tipo": "fact"}
PLAN = dict(tipo="confirmacion", n_corridas=3, criterio="La media observada difiere de la predicha en menos de 2 unidades",
            condiciones="Lote nuevo, horno 2, operador distinto", origen="Modelo del DOE 1", predicho=57.5)


def api_con_regresion():
    a = Api()
    a.pegar(-1, 0, "X\tY\n" + "\n".join(f"{x}\t{2 + 3 * x + (0.2 if x % 2 else -0.2)}" for x in range(1, 13)))
    r = a.ejecutar_modulo("REGRESION", {"y": 1, "xs": [0], "grado": "1"}); assert r["error"] is None, r["sesion"][-1]["texto"]
    return a, r["resultado"]["uid"]


def plan(a, **k): return a.registrar_plan_confirmacion(**{**PLAN, **k})


# ---------- registrar el plan ----------
def test_el_plan_exige_lo_que_define_el_usuario():
    a = Api()
    for campo, vacio, frag in (("criterio", "", "criterio de éxito"), ("condiciones", "  ", "condiciones"), ("origen", "", "de dónde sale el valor predicho"),
                               ("n_corridas", 0, "no propone un tamaño"), ("n_corridas", "x", "no propone un tamaño"), ("tipo", "otro", "Tipo de plan"), ("predicho", "", "valor predicho")):
        r = plan(a, **{campo: vacio}); assert r["error"] == "confirmacion" and frag in r["sesion"][-1]["texto"], campo
    assert a.planes_confirmacion() == []


def test_plan_valido_queda_registrado_y_se_guarda_con_el_proyecto(tmp_path):
    a = Api(); r = plan(a); assert r["error"] is None and r["plan"]["id"] == "CONF-001" and r["plan"]["predicho"]["origen"] == "Modelo del DOE 1" and a._sucio
    assert plan(a, tipo="vigilancia")["plan"]["id"] == "CONF-002"
    ruta = str(tmp_path / "p.dmike"); AR.guardar(ruta, a.hoja, a.proyecto, "0.28.0")
    b = Api(); assert b.abrir_proyecto(ruta)["error"] is None and [p["id"] for p in b.planes_confirmacion()] == ["CONF-001", "CONF-002"]


def test_plan_ligado_a_un_diseno_que_no_existe_se_rechaza():
    assert plan(Api(), design_id="DIS-No")["error"] == "confirmacion"


# ---------- observaciones ----------
def test_observaciones_no_pasan_del_numero_de_corridas_ni_aceptan_texto():
    a = Api(); plan(a)
    assert a.registrar_observados_confirmacion("CONF-001", "57,1; 58.0")["error"] is None
    assert a.registrar_observados_confirmacion("CONF-001", "abc")["error"] == "confirmacion"
    r = a.registrar_observados_confirmacion("CONF-001", "1, 2"); assert r["error"] == "confirmacion" and "prevé 3 corridas y ya tiene 2" in r["sesion"][-1]["texto"]
    assert a.planes_confirmacion()[0]["observados"] == [57.1, 58.0]
    assert a.registrar_observados_confirmacion("CONF-009", "1")["error"] == "confirmacion"


# ---------- comparación ----------
def test_diferencia_observado_menos_predicho_siempre_y_sin_intervalo_en_otro_modelo():
    a = Api(); plan(a); a.registrar_observados_confirmacion("CONF-001", "56.5; 58.5")
    c = a.comparar_confirmacion("CONF-001")["comparacion"]
    assert c["diferencias"] == [-1.0, 1.0] and c["diferencia_media"] == 0.0 and c["media"] == 57.5 and c["faltan"] == 1
    assert c["intervalo"] is None and c["fuera_del_intervalo"] is None and "No respaldado" in c["nota_intervalo"] and "no hay veredicto" in c["nota_intervalo"]
    assert c["criterio_exito"] == PLAN["criterio"]                                                       # el criterio es el del usuario; no hay veredicto de D-MIKE
    assert not any(k in c for k in ("veredicto", "confirmado", "exito"))


def test_sin_observaciones_la_comparacion_no_inventa_cifras():
    a = Api(); plan(a); c = a.comparar_confirmacion("CONF-001")["comparacion"]
    assert c["media"] is None and c["diferencia_media"] is None and c["diferencias"] == [] and c["faltan"] == 3


def test_regresion_simple_da_el_valor_predicho_y_el_intervalo_de_prediccion():
    a, uid = api_con_regresion()
    r = a.registrar_plan_confirmacion(tipo="confirmacion", n_corridas=2, criterio="Dentro del intervalo", condiciones="Lote 2", origen="Regresión de Y contra X", resultado_uid=uid, x0="6")
    assert r["error"] is None, r["sesion"][-1]["texto"]
    assert abs(r["plan"]["predicho"]["valor"] - 20.0) < 0.2 and r["plan"]["predicho"]["tipo_modelo"] == "regresion_simple" and not r["plan"]["predicho"]["extrapolacion"]
    a.registrar_observados_confirmacion("CONF-001", "20.1; 40")
    c = a.comparar_confirmacion("CONF-001")["comparacion"]
    assert c["intervalo"]["inferior"] < 20 < c["intervalo"]["superior"] and "REG-PREDICCION" in c["intervalo"]["fuente"]
    assert c["fuera_del_intervalo"] == [False, True] and "no su promedio" in c["nota_intervalo"]


def test_regresion_simple_extrapolando_avisa_y_exige_el_valor_de_x():
    a, uid = api_con_regresion()
    r = a.registrar_plan_confirmacion(tipo="confirmacion", n_corridas=1, criterio="c", condiciones="d", origen="o", resultado_uid=uid)
    assert r["error"] == "confirmacion" and "indica el valor de X" in r["sesion"][-1]["texto"]
    r = a.registrar_plan_confirmacion(tipo="confirmacion", n_corridas=1, criterio="c", condiciones="d", origen="o", resultado_uid=uid, x0="50")
    assert r["plan"]["predicho"]["extrapolacion"] is True
    a.registrar_observados_confirmacion("CONF-001", "150"); assert any("extrapolación" in x for x in a.comparar_confirmacion("CONF-001")["comparacion"]["avisos"])


def test_resultado_de_superficie_no_da_intervalo(tmp_path):
    a = Api(); a.ejecutar_modulo("DISENO-RSM", BASE)
    r = plan(a, design_id="DIS-Resistencia", resultado_uid=a.resultados()[0]["uid"]); assert r["error"] is None
    assert r["plan"]["predicho"]["tipo_modelo"] == "otro"; a.registrar_observados_confirmacion("CONF-001", "50")
    c = a.comparar_confirmacion("CONF-001")["comparacion"]; assert c["intervalo"] is None and "No respaldado" in c["nota_intervalo"]


# ---------- auditoría y paquete de avance ----------
def test_la_auditoria_lee_el_plan_del_diseno(tmp_path):
    a = Api(); a.ejecutar_modulo("DISENO-RSM", BASE)
    rev = lambda: {x["id"]: x for x in a.auditar_diseno("DIS-Resistencia")["auditoria"]["revisiones"]}["confirmacion"]
    assert rev()["detalle"] == "No hay plan de confirmación registrado." and rev()["estado"] == "aviso"
    plan(a, design_id="DIS-Resistencia", n_corridas=2); x = rev()
    assert x["estado"] == "aviso" and "CONF-001" in x["detalle"] and "0 de 2" in x["detalle"]
    a.registrar_observados_confirmacion("CONF-001", "50; 51"); assert rev()["estado"] == "cumple" and "2 de 2" in rev()["detalle"]


def test_el_paquete_de_avance_no_lleva_planes(tmp_path):
    a = Api(); plan(a); a.proyecto.formatos["_receta"] = {"id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c22", "json": "{}", "ids": {}}
    ruta = tmp_path / "av.json"
    if a.exportar_avance(str(ruta)).get("error") is None:
        t = ruta.read_text(encoding="utf-8"); assert "CONF-001" not in t and "criterio_exito" not in t and "observados" not in t


# ---------- interfaz ----------
def test_interfaz_registra_un_plan_y_compara(pagina):
    from playwright.sync_api import expect
    assert pagina.api.ejecutar_modulo("DISENO-RSM", BASE)["error"] is None
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']"); pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.evaluate("ACCIONES_UI.disenos_dialogo()")
    pagina.click("#disenos button:has-text('Plan de confirmación')")
    d = pagina.locator(".dialogo").last
    d.locator("input[name='n_corridas']").fill("2"); d.locator("input[name='criterio']").fill("Diferencia menor a 2")
    d.locator("input[name='condiciones']").fill("Lote nuevo"); d.locator("input[name='origen']").fill("Modelo del DOE"); d.locator("input[name='predicho']").fill("55")
    d.locator(".primario").click()
    assert pagina.api.planes_confirmacion()[0]["design_id"] == "DIS-Resistencia"
    expect(pagina.locator("#disenos")).to_contain_text("CONF-001")                             # el diálogo se recarga solo y lista el plan
    pagina.click("#disenos button:has-text('Capturar observaciones')")
    d = pagina.locator(".dialogo").last; d.locator("input").fill("54; 56"); d.locator(".primario").click()
    assert pagina.api.planes_confirmacion()[0]["observados"] == [54.0, 56.0]
    pagina.click("#disenos button:has-text('Comparar')")
    expect(pagina.locator("#comparacion")).to_contain_text("Diferencia media (observado − predicho): 0"); expect(pagina.locator("#comparacion")).to_contain_text("No respaldado")
