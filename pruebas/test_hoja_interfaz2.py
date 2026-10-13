"""Hoja v0.13 en la interfaz real: rangos, portapapeles, atajos, menú contextual, filtro, filas virtuales, panel plegable. SINTÉTICOS."""
import re, time
from playwright.sync_api import expect
from test_modulos_interfaz import menu

DATOS = "a\tb\tc\n" + "\n".join(f"{i}\t{i * 2}\t{'XY'[i % 2]}" for i in range(1, 31))


def cargar(pagina, texto=DATOS):
    pagina.api.pegar(-1, 0, texto); pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    pagina.locator("#hoja").focus()


def celda(pagina, f, c): return pagina.locator(f"#hoja-tabla td[data-r='{f}'][data-c='{c}']")


def test_rango_con_mayus_clic_y_barra_de_estado(pagina):
    cargar(pagina)
    celda(pagina, 0, 0).click(); celda(pagina, 2, 1).click(modifiers=["Shift"])
    expect(pagina.locator("#hoja-tabla td.rango")).to_have_count(6)                          # las 6 celdas del rango (la activa además lleva .sel)
    expect(pagina.locator("#estado-rango")).to_contain_text("Suma 18")                        # 1+2+3 + 2+4+6
    expect(pagina.locator("#celda-activa")).to_contain_text("3 × 2")
    pagina.keyboard.press("Escape"); expect(pagina.locator("#hoja-tabla td.rango")).to_have_count(0)


def test_teclado_extender_saltar_y_seleccionar_todo(pagina):
    cargar(pagina)
    celda(pagina, 0, 0).click()
    pagina.keyboard.press("Shift+ArrowDown"); pagina.keyboard.press("Shift+ArrowDown")
    expect(pagina.locator("#celda-activa")).to_contain_text("3 × 1")
    pagina.keyboard.press("Control+ArrowDown"); expect(pagina.locator("#celda-activa")).to_contain_text("fila 30")
    pagina.keyboard.press("Control+Home"); expect(pagina.locator("#celda-activa")).to_contain_text("C1, fila 1")
    pagina.keyboard.press("Control+a"); expect(pagina.locator("#celda-activa")).to_contain_text("30 × 3")


def test_copiar_cortar_pegar_y_borrar(pagina):
    cargar(pagina)
    celda(pagina, 0, 0).click(); celda(pagina, 1, 1).click(modifiers=["Shift"])
    pagina.keyboard.press("Control+c")
    celda(pagina, 10, 0).click(); pagina.keyboard.press("Control+v")
    expect(celda(pagina, 10, 0)).to_have_text("1"); expect(celda(pagina, 11, 1)).to_have_text("4")
    celda(pagina, 0, 0).click(); celda(pagina, 1, 0).click(modifiers=["Shift"]); pagina.keyboard.press("Control+x")
    expect(celda(pagina, 0, 0)).to_have_text(""); expect(celda(pagina, 1, 0)).to_have_text("")
    pagina.keyboard.press("Control+z"); expect(celda(pagina, 0, 0)).to_have_text("1")
    celda(pagina, 2, 0).click(); celda(pagina, 3, 1).click(modifiers=["Shift"]); pagina.keyboard.press("Delete")
    expect(celda(pagina, 2, 1)).to_have_text(""); expect(celda(pagina, 4, 0)).to_have_text("5")


def test_rellenar_abajo_y_columna_completa(pagina):
    cargar(pagina)
    celda(pagina, 0, 2).click(); celda(pagina, 4, 2).click(modifiers=["Shift"]); pagina.keyboard.press("Control+d")
    expect(celda(pagina, 4, 2)).to_have_text("Y")
    pagina.locator("#hoja-tabla th.enc[data-c='1']").click()
    expect(pagina.locator("#celda-activa")).to_contain_text("30 × 1")
    pagina.keyboard.press("Control+-"); expect(pagina.locator("#hoja-tabla th.nombre[data-c='1']")).to_have_text("c")


def test_editar_con_delta_no_repinta_la_hoja(pagina):
    cargar(pagina)
    celda(pagina, 0, 0).click(); pagina.keyboard.type("99"); pagina.keyboard.press("Enter")
    expect(celda(pagina, 0, 0)).to_have_text("99"); expect(celda(pagina, 1, 0)).to_have_class("sel")
    pagina.keyboard.press("F2"); pagina.keyboard.type("x"); pagina.keyboard.press("Enter")
    expect(celda(pagina, 1, 0)).to_have_class(re.compile(r"\bmal\b"))                            # «x» no es número: queda en rojo


def test_menu_contextual_ordenar_y_filtrar_por_valor(pagina):
    cargar(pagina)
    celda(pagina, 1, 2).click(button="right")
    expect(pagina.locator(".contextual")).to_be_visible()
    pagina.click(".contextual button:has-text('Filtrar por el valor de esta celda')")
    expect(pagina.locator("#info-filtro")).to_contain_text("15 de 30")
    expect(pagina.locator("#hoja-tabla tbody tr:not(.relleno)")).to_have_count(15)
    menu(pagina, "Datos", "Quitar filtro"); expect(pagina.locator("#info-filtro")).to_be_hidden()
    celda(pagina, 0, 1).click(button="right"); pagina.click(".contextual button:has-text('Ordenar de mayor a menor')")
    expect(celda(pagina, 0, 1)).to_have_text("60")


def test_dialogo_de_filtro_con_dos_condiciones(pagina):
    cargar(pagina)
    pagina.keyboard.press("Control+Shift+L")
    pagina.select_option(".dialogo .cond select >> nth=0", "0"); pagina.select_option(".dialogo .cond select >> nth=1", ">")
    pagina.fill(".dialogo .cond input", "25")
    pagina.click(".dialogo button:text-is('Agregar condición')")
    pagina.select_option(".dialogo .cond:nth-of-type(2) select >> nth=0", "2"); pagina.fill(".dialogo .cond:nth-of-type(2) input", "x")
    pagina.click(".dialogo .primario")
    expect(pagina.locator("#info-filtro")).to_contain_text("3 de 30")                          # 26, 28, 30 son pares → 'X'


def test_panel_dmaic_se_oculta_y_se_muestra(pagina):
    cargar(pagina)
    expect(pagina.locator("#fases")).to_be_visible()
    pagina.keyboard.press("Control+b"); pagina.wait_for_timeout(350)
    expect(pagina.locator("#fases")).to_be_hidden()                          # v0.23: sin hueco; se muestra con el botón de las pestañas
    pagina.click("#b-panel"); pagina.wait_for_timeout(350)                     # v0.24: el botón está en la barra de herramientas
    assert pagina.locator("#fases").bounding_box()["width"] > 200
    menu(pagina, "Ver", "Mostrar u ocultar la sesión"); expect(pagina.locator(".sesion")).to_be_hidden()


def test_barra_de_herramientas_deshacer(pagina):
    cargar(pagina)
    celda(pagina, 0, 0).click(); pagina.keyboard.type("7"); pagina.keyboard.press("Enter")
    expect(celda(pagina, 0, 0)).to_have_text("7")
    pagina.click("button.ico[title^='Deshacer']"); expect(celda(pagina, 0, 0)).to_have_text("1")
    pagina.click("button.ico[title^='Rehacer']"); expect(celda(pagina, 0, 0)).to_have_text("7")
    pagina.click("button.ico[title^='Calculadora']"); expect(pagina.locator(".dialogo")).to_contain_text("Calculadora de columnas")


def test_5000_filas_solo_dibuja_las_visibles_y_es_rapido(pagina):
    texto = "id\tvalor\n" + "\n".join(f"{i}\t{i * 0.5}" for i in range(1, 5001))
    t0 = time.time(); cargar(pagina, texto); carga = time.time() - t0
    assert pagina.locator("#hoja-tabla tbody tr").count() < 150
    pagina.evaluate("document.querySelector('#hoja').scrollTop = 80000"); pagina.wait_for_timeout(200)
    expect(pagina.locator("#hoja-tabla td[data-f='3600'][data-c='0']")).to_have_text("3601")
    pagina.keyboard.press("Control+End"); expect(pagina.locator("#celda-activa")).to_contain_text("fila 5000")
    t1 = time.time(); celda_ult = pagina.locator("#hoja-tabla td.sel"); pagina.keyboard.type("5"); pagina.keyboard.press("Enter")
    pagina.wait_for_timeout(100); assert time.time() - t1 < 2.0 and carga < 15


def test_atajos_dialogo(pagina):
    cargar(pagina); menu(pagina, "Ayuda", "Atajos de teclado")
    expect(pagina.locator(".atajos")).to_contain_text("Ctrl+D")
