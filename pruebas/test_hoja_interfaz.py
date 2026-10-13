import re
from playwright.sync_api import expect


def celda(p, f, c): return p.locator(f"#hoja-tabla [data-f='{f}'][data-c='{c}']")


def test_escribir_enter_baja_una_fila(pagina):
    celda(pagina, 0, 0).click()
    pagina.keyboard.type("16.2"); pagina.keyboard.press("Enter")
    pagina.keyboard.type("2.7"); pagina.keyboard.press("Enter")
    expect(celda(pagina, 0, 0)).to_have_text("16.2") and celda(pagina, 1, 0).inner_text() == "2.7"
    expect(pagina.locator("#celda-activa")).to_have_text("C1, fila 3")
    expect(pagina.locator("#hoja-tabla tr.num th").nth(1)).to_have_text("C1")


def test_texto_en_columna_numerica_se_marca(pagina):
    celda(pagina, 0, 0).click(); pagina.keyboard.type("5"); pagina.keyboard.press("Enter")
    pagina.keyboard.type("12,5 min"); pagina.keyboard.press("Enter")
    expect(celda(pagina, 1, 0)).to_have_class(re.compile("mal"))
    expect(pagina.locator("#sesion")).to_contain_text("no es numérico")


def test_tab_y_flechas(pagina):
    celda(pagina, 3, 3).click()
    pagina.keyboard.type("Op1"); pagina.keyboard.press("Tab")
    pagina.keyboard.press("ArrowDown")
    expect(pagina.locator("#celda-activa")).to_have_text("C5, fila 5")
    expect(pagina.locator("#hoja-tabla tr.num th").nth(4)).to_have_text("C4-T")


def pegar(pagina, texto):
    pagina.evaluate("""t => { const d = new DataTransfer(); d.setData('text/plain', t);
        document.querySelector('#hoja').dispatchEvent(new ClipboardEvent('paste', {clipboardData: d, bubbles: true})); }""", texto)
    pagina.wait_for_timeout(150)


def test_pegar_desde_excel_con_nombres(pagina):
    pagina.locator("#hoja-tabla th.nombre[data-c='0']").click()
    pegar(pagina, "condicion\ttiempo\r\nSin\t16.2\r\nCon\t2.7\r\n")
    expect(pagina.locator("#hoja-tabla th.nombre[data-c='1']")).to_have_text("tiempo")
    expect(celda(pagina, 1, 1)).to_have_text("2.7")
    expect(pagina.locator("#sesion")).to_contain_text("Pegados 2 filas por 2 columnas")


def test_renombrar_duplicado_avisa(pagina):
    for j in (0, 1):
        pagina.locator(f"#hoja-tabla th.nombre[data-c='{j}']").click()
        pagina.keyboard.type("tiempo"); pagina.keyboard.press("Enter")
    expect(pagina.locator("#hoja-tabla th.nombre[data-c='1']")).to_have_text("")
    expect(pagina.locator("#sesion")).to_contain_text("Ya existe una columna")


def test_dialogo_tipo_de_columna(pagina):
    pegar(pagina, "x\nabc\n3")
    pagina.click(".menu > button:text-is('Datos')"); pagina.click("text=Tipo de columna…")
    pagina.check("input[value='num']"); pagina.click(".dialogo .primario")
    expect(celda(pagina, 1, 0)).to_have_class(re.compile("mal"))
    expect(celda(pagina, 0, 0)).to_have_class(re.compile("mal"))
    expect(pagina.locator("#hoja-tabla tr.num th").nth(1)).to_have_text("C1")


def test_insertar_fila_desde_menu(pagina):
    pegar(pagina, "a\nb")
    celda(pagina, 0, 0).click()
    pagina.click(".menu > button:text-is('Datos')"); pagina.click("text=Insertar fila")
    expect(celda(pagina, 0, 0)).to_have_text("") and celda(pagina, 1, 0).inner_text() == "a"


def test_suprimir_borra(pagina):
    pegar(pagina, "7"); celda(pagina, 0, 0).click(); pagina.keyboard.press("Delete")
    expect(celda(pagina, 0, 0)).to_have_text("")
