"""Superficies de respuesta en la interfaz real. Datos SINTÉTICOS."""
from playwright.sync_api import expect
from test_modulos_interfaz import menu
from test_superficies import VERDAD


def test_flujo_completo_diseno_analisis_optimizador(pagina):
    menu(pagina, "Estadística", "Crear diseño de experimentos…")
    pagina.fill(".dialogo input[name='nombres']", "Temperatura, Presion")
    pagina.fill(".dialogo input[name='bajos']", "140, 3"); pagina.fill(".dialogo input[name='altos']", "160, 5")
    pagina.fill(".dialogo input[name='respuesta']", "Rendimiento"); pagina.fill(".dialogo input[name='semilla']", "3")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".pestana.activa")).to_contain_text("Diseño central compuesto")
    a = pagina.api
    jt, jp, jy = a.hoja.indice("Temperatura"), a.hoja.indice("Presion"), a.hoja.indice("Rendimiento")
    for i in range(a.hoja.n):
        a.hoja.editar(i, jy, str(round(VERDAD(a.hoja.columnas[jt].valor(i)[2], a.hoja.columnas[jp].valor(i)[2]), 3)))
    menu(pagina, "Estadística", "Analizar superficie de respuesta…")
    pagina.select_option(".dialogo select[name='y']", str(jy))
    pagina.check(f".dialogo .multi[data-campo='xs'] input[value='{jt}']"); pagina.check(f".dialogo .multi[data-campo='xs'] input[value='{jp}']")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".pestana.activa")).to_contain_text("Superficie de respuesta de Rendimiento")
    expect(pagina.locator(".resultado .grafica svg")).to_have_count(3)
    expect(pagina.locator(".resultado")).to_contain_text("máximo")
    menu(pagina, "Estadística", "Optimizador de respuestas…")
    expect(pagina.locator(".dialogo select[name='r1'] option")).to_have_count(1)
    pagina.fill(".dialogo input[name='inf1']", "70"); pagina.fill(".dialogo input[name='obj1']", "80")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".pestana.activa")).to_contain_text("Optimización de Rendimiento")
    expect(pagina.locator(".texto-res.conclusion")).to_contain_text("Temperatura = 150")
