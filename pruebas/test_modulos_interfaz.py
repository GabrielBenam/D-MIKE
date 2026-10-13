"""Módulos en la interfaz real con el puente de Python. Datos SINTÉTICOS."""
import re
from playwright.sync_api import expect
from test_modulos import SINT


def pegar(p, texto):
    p.locator("#hoja-tabla th.nombre[data-c='0']").click()
    p.evaluate("""t => { const d = new DataTransfer(); d.setData('text/plain', t);
        document.querySelector('#hoja').dispatchEvent(new ClipboardEvent('paste', {clipboardData: d, bubbles: true})); }""", texto)
    p.wait_for_timeout(150)


def poner(fila, campo, v):
    """Escribe en una celda de formato, sea campo de texto o lista desplegable."""
    td = fila.locator(f"td[data-c='{campo}']")
    if td.locator("select").count(): td.locator("select").select_option(v)
    else: td.locator("input").fill(v); td.locator("input").press("Tab")


def menu(p, titulo, opcion):
    p.click(f".menu > button:text-is('{titulo}')"); p.click(f".menu.abierto button:text-is('{opcion}')")


def test_boxplot_dialogo_y_resultado(pagina):
    pegar(pagina, SINT)
    menu(pagina, "Gráficas", "Diagrama de caja…")
    pagina.select_option(".dialogo select[name='y']", "4")
    pagina.select_option(".dialogo select[name='grupo']", "2")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".pestana.activa")).to_contain_text("Diagrama de caja de tiempo por condicion")
    expect(pagina.locator(".resultado .grafica svg")).to_have_count(1)
    expect(pagina.locator(".tabla-res tbody tr")).to_have_count(2)
    pagina.click(".pestana[data-p='hoja']")
    expect(pagina.locator("#marco-hoja")).to_be_visible()


def test_error_de_entrada_queda_en_el_dialogo(pagina):
    pegar(pagina, SINT)
    menu(pagina, "Estadística", "ANOVA de un factor…")
    pagina.select_option(".dialogo select[name='y']", "")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".error-dialogo")).to_contain_text("Falta elegir la respuesta")
    expect(pagina.locator(".dialogo")).to_be_visible()


def test_anova_y_lista_de_resultados(pagina):
    pegar(pagina, SINT)
    menu(pagina, "Estadística", "ANOVA de un factor…")
    pagina.select_option(".dialogo select[name='y']", "4"); pagina.select_option(".dialogo select[name='factor']", "2")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".texto-res.conclusion").first).to_contain_text("H0")
    pagina.click(".pestana-x")
    menu(pagina, "Proyecto", "Resultados del proyecto…")
    pagina.click(".lista-res .boton")
    expect(pagina.locator(".pestana.activa")).to_contain_text("ANOVA")


def test_amef_rpn_en_vivo(pagina):
    menu(pagina, "Herramientas de calidad", "AMEF")
    fila = pagina.locator(".tabla-fmt[data-tabla='filas'] tbody tr").first
    for campo, v in (("falla", "Falla sintética"), ("sev", "9"), ("occ", "3"), ("det", "4")):
        poner(fila, campo, v)
    expect(fila.locator("td[data-c='rpn']")).to_have_text("108")
    expect(fila.locator("td[data-c='sev']")).to_have_class(re.compile("alerta"))
    expect(pagina.locator(".avisos-fmt")).to_contain_text("Severidad 9 a 10")


def test_hoja_datos_calcula_muestra(pagina):
    menu(pagina, "Herramientas de calidad", "Hoja de recolección")
    cab = pagina.locator(".cabecera-fmt")
    cab.locator("label:has-text('Tipo de dato') select").select_option("continuo")
    for et, v in (("Tamaño de la población", "3200"), ("Desviación estándar", "0.458"), ("Precisión", "0.1"), ("Tiempo disponible", "480")):
        i = cab.locator(f"label:has-text('{et}') input"); i.fill(v); i.press("Tab")
    expect(pagina.locator("[data-cab='n_calc']")).to_have_text("81")
    expect(pagina.locator("[data-cab='frecuencia_calc']")).to_have_text("5.93")


def test_tablero_colores(pagina):
    menu(pagina, "Herramientas de calidad", "Tablero semanal")
    fila = pagina.locator(".tabla-fmt[data-tabla='kpi'] tbody tr").first
    for campo, v in (("indicador", "Unidades sintéticas"), ("meta", "25"), ("s1", "21"), ("s2", "26")):
        fila.locator(f"td[data-c='{campo}'] input").fill(v); fila.locator(f"td[data-c='{campo}'] input").press("Tab")
    fila.locator("td[data-c='sentido'] select").select_option(">=")
    expect(fila.locator("td[data-c='s1']")).to_have_class(re.compile("no"))
    expect(fila.locator("td[data-c='s2']")).to_have_class(re.compile("ok"))
    expect(fila.locator("td[data-c='tendencia'] svg")).to_have_count(1)
