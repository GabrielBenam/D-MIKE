"""Formatos v0.15 en la interfaz real. Datos SINTÉTICOS."""
from playwright.sync_api import expect
from test_modulos_interfaz import menu


def test_checklist_cambia_de_fase_y_menu_lean(pagina):
    menu(pagina, "Herramientas de calidad", "Checklist de revisión de fase")
    expect(pagina.locator(".formato table").first.locator("tbody tr")).to_have_count(7)
    pagina.select_option(".formato select[name='fase']", "M")
    expect(pagina.locator(".formato table").first.locator("tbody tr")).to_have_count(11)
    expect(pagina.locator(".formato input[name='punto']").nth(2)).to_have_value("Hay definiciones operacionales de las características a medir.")
    expect(pagina.locator(".formato input[name='punto']").nth(2)).to_have_attribute("readonly", "")
    menu(pagina, "Lean", "Teoría de restricciones")
    expect(pagina.locator(".pestana.activa")).to_contain_text("TOC")


def test_muestreo_calcula_en_pantalla(pagina):
    menu(pagina, "Herramientas de calidad", "Plan de muestreo")
    pagina.select_option(".formato select[name='tipo']", "continuo")
    for campo, v in (("poblacion", "3200"), ("s", "0.458"), ("d", "0.1"), ("periodo", "480")):
        pagina.fill(f".formato input[name='{campo}']", v); pagina.keyboard.press("Tab")
    expect(pagina.locator(".formato")).to_contain_text("una muestra cada 5.93 min")
