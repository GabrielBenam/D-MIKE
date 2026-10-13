"""Interfaz v0.23: varios proyectos abiertos, botones del riel, riel oculto sin hueco, cinta fija sin barra, tarjeta de ayuda,
Acerca de, nota de módulo con enlace a la ayuda y QFD con la casa visible desde el inicio. Datos SINTÉTICOS."""
import os
from pathlib import Path
from playwright.sync_api import expect
from test_ui_v021 import nueva

CASO = str(Path(__file__).parent / "sinteticos" / "caso_integral_datos_llenos.xlsx")


def test_varios_proyectos_y_riel(pagina, tmp_path):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    nueva(pagina, tmp_path, con_reciente=False)
    pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.api.pegar(-1, 0, "x\n1\n2"); pagina.evaluate("ACCIONES_UI.nuevo_proyecto()"); pagina.wait_for_timeout(400)
    expect(pagina.locator(".doc-tab[data-doc]")).to_have_count(2)
    pagina.click(".doc-tab[data-doc='1']"); pagina.wait_for_timeout(400)
    assert pagina.api.hoja.n == 2
    pagina.click(".doc-tab[data-doc='2'] .doc-x"); expect(pagina.locator(".doc-tab[data-doc]")).to_have_count(1)
    # riel: sin la palabra DMAIC, botones arriba y sin hueco al ocultarlo
    assert not pagina.locator(".dmaic-raiz").is_visible()
    ancho = pagina.locator(".trabajo").bounding_box()["width"]
    pagina.click("#b-panel"); pagina.wait_for_timeout(300)
    assert pagina.locator(".trabajo").bounding_box()["width"] > ancho + 40
    pagina.click("#b-panel"); expect(pagina.locator("#fases")).to_be_visible()
    # v0.24: la barra de herramientas siempre se ve, debajo de las pestañas; sin luna ni atajos; el riel empieza debajo de ella
    expect(pagina.locator("#herramientas")).to_be_visible(); expect(pagina.locator("#b-tema, #b-atajos, #b-proyectos")).to_have_count(0)
    assert pagina.locator("#docs").bounding_box()["y"] < pagina.locator("#pestanas").bounding_box()["y"] < pagina.locator("#herramientas").bounding_box()["y"] < pagina.locator("#fases").bounding_box()["y"]
    # tarjeta de ayuda
    pagina.click("#menus .menu > button:text-is('Estadística')"); pagina.hover("#cinta .cinta-b >> nth=0"); pagina.wait_for_timeout(700)
    expect(pagina.locator(".tip-cmd")).to_contain_text("Presiona F1"); pagina.mouse.move(5, 700)
    pagina.evaluate("ACCIONES_UI.acerca_de()"); expect(pagina.locator(".acerca")).to_contain_text("Versión")
    assert not errores, errores


def test_qfd_casa_visible_y_nota_con_ayuda(pagina, tmp_path):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    nueva(pagina, tmp_path, con_reciente=False)
    pagina.evaluate("abrirModulo('QFD')"); pagina.wait_for_timeout(600)
    expect(pagina.locator(".formato.dividida .qfd-casa svg")).to_be_visible()
    assert pagina.locator(".qfd-casa [data-cor]").count() >= 10
    expect(pagina.locator(".acerca-mod")).to_contain_text("ver en la ayuda")
    pagina.click(".acerca-mod .enlace"); expect(pagina.locator(".ay-cuerpo h1")).to_contain_text("QFD")
    assert not errores, errores
