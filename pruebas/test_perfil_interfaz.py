"""Incremento 3 en la interfaz real con el puente de Python. Datos sintéticos."""
from pathlib import Path
from playwright.sync_api import expect

PERFIL = str(Path(__file__).parent / "sinteticos" / "perfil_prueba_sintetico.json")


def abrir_perfil(pagina, ruta=PERFIL):
    pagina.api._elegir = lambda *a, **k: ruta
    pagina.click(".menu > button:text-is('Proyecto')")
    pagina.click("text=Abrir perfil del diagnóstico…")
    expect(pagina.locator("#franja:not([hidden])")).to_have_count(1)        # v0.24: la franja de datos fijos ya no se muestra


def test_abrir_perfil_puebla_panel_franja_y_hoja(pagina):
    abrir_perfil(pagina)
    expect(pagina.locator(".fase[data-fase='M'] .fase-cuenta")).to_have_text("6 de 26")          # 21 del árbol + 5 complementarios de Medir (v0.20)
    expect(pagina.locator(".fase.actual .letra")).to_have_text("M")
    expect(pagina.locator(".fase[data-fase='M'] li.activo[data-id='HOJA-DATOS'] .sig")).to_have_text("siguiente")
    expect(pagina.locator("#franja")).to_contain_text("Proyecto de prueba")
    expect(pagina.locator("#hoja-tabla th.nombre[data-c='6']")).to_have_text("tiempo")
    expect(pagina.locator("#hoja-tabla tr.rol th").nth(7)).to_have_text("respuesta")
    expect(pagina.locator("#sesion")).to_contain_text("Perfil v1 cargado")
    expect(pagina.locator("#sesion")).to_contain_text("Siguiente paso sugerido")


def test_editar_datos_fijos(pagina):
    abrir_perfil(pagina)
    pagina.evaluate("ACCIONES_UI.datos_fijos()")                    # v0.24: desde Proyecto › Datos fijos (la franja ya no se muestra)
    pagina.fill(".dialogo input[name='responsable']", "Persona sintética 2")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".fijo[data-campo='responsable']")).to_contain_text("Persona sintética 2")


def test_ficha_y_avance_de_modulo(pagina):
    abrir_perfil(pagina)
    pagina.click(".fase[data-fase='A'] > button")
    pagina.click(".fase[data-fase='A'] li.activo[data-id='CORREL'] .mod-mas")       # v0.20: clic abre el módulo; «⋯» abre la ficha
    expect(pagina.locator(".dialogo")).to_contain_text("Datos mínimos")
    pagina.check(".dialogo input[value='en_curso']"); pagina.click(".dialogo .primario")
    expect(pagina.locator(".fase[data-fase='A'] li.activo[data-id='CORREL']")).to_have_class("activo en_curso")


def test_perfil_danado_avisa_en_sesion(pagina, tmp_path):
    malo = tmp_path / "malo.json"; malo.write_text("{roto", encoding="utf-8")
    pagina.api._elegir = lambda *a, **k: str(malo)
    pagina.click(".menu > button:text-is('Proyecto')"); pagina.click("text=Abrir perfil del diagnóstico…")
    expect(pagina.locator("#sesion li.aviso")).to_contain_text("no se cargó")
    expect(pagina.locator("#franja[hidden]")).to_have_count(1)
