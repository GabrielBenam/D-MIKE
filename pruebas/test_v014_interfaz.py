"""v0.14: tablero de indicadores en el programa, tema oscuro con gráficas adaptadas y diálogos nuevos. Datos SINTÉTICOS."""
import re
from playwright.sync_api import expect
from app.api import Api
from test_modulos_interfaz import menu


def test_api_tablero_agregar_meta_quitar():
    a = Api()
    assert a.datos_tablero()["indicadores"] == [] and len(a.datos_tablero()["catalogo"]) == 109
    r = a.tablero_kpi("agregar", {"kpi_id": "OEE"}); assert r["error"] is None and r["tablero"]["indicadores"][0]["nombre"] == "OEE"
    assert "ya está" in a.tablero_kpi("agregar", {"kpi_id": "OEE"})["sesion"][0]["texto"]
    d = a.abrir_formato("TABLERO")["datos"]; d["tablas"]["kpi"][0].update({"s1": "80", "s2": "84", "s3": "88"}); a.guardar_formato("TABLERO", d)
    r = a.tablero_kpi("meta", {"i": 0, "meta": "85", "adv": "80"}); k = r["tablero"]["indicadores"][0]
    assert k["ultimo"] == 88 and k["estado"] == "ok" and k["delta"] == 4 and k["estados"][:3] == ["advertencia", "advertencia", "ok"]
    assert a.tablero_kpi("quitar", {"i": 0})["tablero"]["indicadores"] == [] and a.modificado()
    assert a.tablero_kpi("agregar", {"kpi_id": "NO-EXISTE"})["error"] == "kpi"


def test_vista_tablero_en_el_programa(pagina):
    menu(pagina, "Proyecto", "Tablero de indicadores")
    expect(pagina.locator(".pestana.activa")).to_contain_text("Tablero de indicadores")
    expect(pagina.locator(".tb-vacio")).to_be_visible()
    pagina.click(".tb-seg button:text-is('Exploración')")
    expect(pagina.locator(".tb-item")).to_have_count(109)
    pagina.fill("#tb-busca", "OEE"); pagina.click(".tb-item:has-text('OEE') [data-agregar]")
    expect(pagina.locator("#sesion")).to_contain_text("agregado al tablero")
    pagina.click(".tb-seg button:text-is('Ejecutivo')")
    expect(pagina.locator(".tb-kpi")).to_have_count(1)
    pagina.click(".tb-kpi"); pagina.fill(".tb-campos input[type=number] >> nth=0", "85"); pagina.click(".dialogo .primario")
    expect(pagina.locator(".tb-kpi .tb-m")).to_contain_text("Meta ≥ 85")


def test_tema_oscuro_adapta_las_graficas(pagina):
    pagina.api.pegar(-1, 0, "y\n" + "\n".join(str(10 + i % 7) for i in range(30))); pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    pagina.keyboard.press("Control+Shift+D")
    expect(pagina.locator("html")).to_have_attribute("data-tema", "oscuro")
    pagina.evaluate("async () => { const r = await api().ejecutar_modulo('CORRIDA', {y: 0}); abrirPestana('res:' + r.resultado.uid, r.resultado); }")
    pagina.wait_for_selector(".resultado .grafica svg")
    fondo = pagina.evaluate("getComputedStyle(document.body).backgroundColor")
    assert fondo == "rgb(28, 25, 22)"
    usa_var = pagina.evaluate("[...document.querySelectorAll('.resultado .grafica svg *')].some(e => (e.getAttribute('style') || '').includes('var(--g-'))")
    assert usa_var
    pagina.evaluate("alternarTema()"); expect(pagina.locator("html")).not_to_have_attribute("data-tema", "oscuro")


def test_dialogo_pruebas_de_hipotesis(pagina):
    pagina.api.pegar(-1, 0, "x\n" + "\n".join(str(10 + (i * 7) % 5) for i in range(20))); pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    menu(pagina, "Estadística", "Pruebas de hipótesis…")
    pagina.select_option(".dialogo select[name='y']", "0"); pagina.fill(".dialogo input[name='h0']", "11")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".pestana.activa")).to_contain_text("Prueba t de 1 muestra")
    expect(pagina.locator(".texto-res.conclusion")).to_contain_text("α = 0.05")
