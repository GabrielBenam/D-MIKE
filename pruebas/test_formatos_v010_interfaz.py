"""Interfaz de los formatos de v0.10. Datos SINTÉTICOS."""
import re
from playwright.sync_api import expect
from test_modulos_interfaz import menu, poner


def test_tablero_catalogo_y_tarjetas(pagina):
    menu(pagina, "Herramientas de calidad", "Tablero semanal")
    pagina.click("text=Agregar del catálogo…")
    pagina.fill(".dialogo .kpi-filtros input", "oee")
    pagina.check(".dialogo .kpi-op:has-text('OEE') input >> nth=0")
    pagina.click(".dialogo .primario")
    fila = pagina.locator(".tabla-fmt[data-tabla='kpi'] tbody tr").first
    expect(fila.locator("td[data-c='indicador'] input")).to_have_value("OEE")
    expect(fila.locator("td[data-c='categoria'] input")).to_have_value("Equipo")
    for campo, v in (("meta", "85"), ("advertencia", "80"), ("s1", "78"), ("s2", "83")):
        poner(fila, campo, v)
    expect(pagina.locator(".tarjeta.advertencia .t-valor")).to_contain_text("83")
    expect(fila.locator("td[data-c='s1']")).to_have_class(re.compile("no"))


def test_ishikawa_dibuja_diagrama(pagina):
    menu(pagina, "Herramientas de calidad", "Diagrama de Ishikawa")
    pagina.locator(".cabecera-fmt label:has-text('Efecto') textarea").fill("Datos mal capturados")
    pagina.locator(".cabecera-fmt label:has-text('Efecto') textarea").press("Tab")
    fila = pagina.locator(".tabla-fmt tbody tr").first
    poner(fila, "categoria", "Métodos"); poner(fila, "causa", "Formato ambiguo")
    expect(pagina.locator(".bloques-fmt .grafica svg")).to_have_count(1)
    expect(pagina.locator(".bloques-fmt svg")).to_contain_text("Formato ambiguo")


def test_oee_por_hora(pagina):
    menu(pagina, "Lean", "OEE")
    fila = pagina.locator(".tabla-fmt tbody tr").first
    for campo, v in (("total", "60"), ("paro", "10"), ("muerto", "10"), ("capacidad", "5"), ("produccion", "195"), ("rechazo", "2")):
        poner(fila, campo, v)
    expect(fila.locator("td[data-c='oee']")).to_have_text("77.2%")
    expect(fila.locator("td[data-c='oee']")).to_have_class(re.compile("no"))
    expect(pagina.locator("[data-cab='oee_calc']")).to_contain_text("77.2% del tiempo disponible")


def test_kanban_meses_fijos(pagina):
    menu(pagina, "Lean", "Kanban")
    expect(pagina.locator(".tabla-fmt tbody tr")).to_have_count(12)
    expect(pagina.locator(".formato .agregar")).to_have_count(0)


def test_exportar_powerbi_desde_menu(pagina, tmp_path):
    pagina.api._elegir = lambda *a, **k: str(tmp_path)
    menu(pagina, "Archivo", "Exportar para Power BI…")
    expect(pagina.locator("#sesion")).to_contain_text("Datos para Power BI exportados")
