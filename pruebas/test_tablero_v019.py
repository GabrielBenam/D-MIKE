"""Tablero de indicadores en el programa (v0.19): tipo adelantado o atrasado, explicación fuera de meta, avance por fase y detalle.
Datos SINTÉTICOS."""
from playwright.sync_api import expect
from app.api import Api


def armar(a):
    for kid in ("OEE", "LEADTIME", "DISPONIBILIDAD"): a.tablero_kpi("agregar", {"kpi_id": kid})
    d = a.abrir_formato("TABLERO")["datos"]
    for f, (m, vals) in zip(d["tablas"]["kpi"], ((85, (80, 82, 79)), (70, (72, 71, 69)), (90, (92, 93, 91)))):
        f["meta"] = str(m); f.update({f"s{k + 1}": str(v) for k, v in enumerate(vals)})
    a.guardar_formato("TABLERO", d)


def test_api_tipo_explicacion_y_fases():
    a = Api(); armar(a)
    t = a.datos_tablero(); k = t["indicadores"][0]
    assert k["estado"] == "no" and k["tipo"] == "" and k["explicacion"] == "" and t["fases"] == []        # sin perfil no hay avance por fase
    r = a.tablero_kpi("meta", {"i": 0, "meta": "85", "adv": "80", "tipo": "Atrasado", "explicacion": "Paros por cambio de molde"})
    k = r["tablero"]["indicadores"][0]
    assert k["tipo"] == "Atrasado" and k["explicacion"] == "Paros por cambio de molde" and k["estado"] == "no"
    assert a.tablero_kpi("meta", {"i": 0, "tipo": "Cualquiera"})["tablero"]["indicadores"][0]["tipo"] == ""
    a.abrir_perfil("pruebas/sinteticos/perfil_prueba_sintetico.json"); a.marcar_avance("HOJA-DATOS", "hecho")
    f = {x["fase"]: x for x in a.datos_tablero()["fases"]}
    assert f["M"]["hechos"] == 1 and f["M"]["total"] >= 1 and a.datos_tablero()["fase_actual"] == "M"


def test_vista_detalle_guarda_tipo_y_explicacion(pagina):
    armar(pagina.api); pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    pagina.evaluate("ACCIONES_UI.tablero_vista()")
    expect(pagina.locator(".tb-alerta")).to_have_count(1)
    expect(pagina.locator(".tb-alerta .tb-falta")).to_contain_text("Falta la explicación")
    pagina.click(".tb-kpi >> nth=0")
    pagina.select_option(".dialogo select", "Adelantado")
    pagina.fill(".dialogo textarea", "Paros por falta de material")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".tb-kpi >> nth=0")).to_contain_text("adelantado")
    expect(pagina.locator(".tb-alerta .tb-expl")).to_have_text("Paros por falta de material")
    pagina.click(".tb-kpi >> nth=0"); expect(pagina.locator(".tb-detalle")).to_contain_text("en meta 0 de 3 semanas")
