def test_diez_menus(pagina):
    titulos = pagina.locator(".menu > button").all_inner_texts()
    assert titulos == ["Archivo", "Editar", "Datos", "Calc", "Estadística", "Gráficas",
                       "Herramientas de calidad", "Lean", "Gestión", "Proyecto", "Ver", "Ayuda"]


def test_cinco_fases_dmaic(pagina):
    assert pagina.locator(".fase .letra").all_inner_texts() == ["D", "M", "A", "I", "C"]


def test_disponibles_por_fase(pagina):
    pagina.click(".fase[data-fase='M'] > button")
    n = pagina.locator(".fase[data-fase='M'] li").count()
    assert n == len(pagina.api.catalogo.por_fase()["M"]) and n > 0
    assert pagina.locator(".fase[data-fase='M'] li[data-id='HOJA-DATOS']:not(.pendiente)").count() == 1


def test_hoja_vacia_20x50(pagina):
    assert pagina.locator(".hoja tr.num th").count() == 21
    assert pagina.locator(".hoja tbody tr:not(.relleno)").count() == 50
    pagina.click("td[data-f='4'][data-c='2']")
    assert pagina.inner_text("#celda-activa") == "C3, fila 5"


def test_sesion_y_menu_ayuda(pagina):
    assert "62 módulos" in pagina.inner_text("#sesion")
    pagina.click(".menu:has-text('Ayuda') > button")
    pagina.click("text=Acerca de D-MIKE")
    from playwright.sync_api import expect; expect(pagina.locator(".dialogo .acerca")).to_contain_text("Versión")   # v0.23: ventana Acerca de


def test_todas_las_opciones_de_calc_estan_construidas(pagina):
    pagina.click(".menu > button:text-is('Calc')")
    assert not pagina.locator(".menu.abierto button:has-text('Calculadora de columnas')").is_disabled()


def test_fuente_montserrat_cargada(pagina):
    assert pagina.evaluate("document.fonts.check('13px Montserrat')")
    assert pagina.evaluate("[...document.fonts].some(f => f.family.includes('Montserrat') && f.status === 'loaded')")
