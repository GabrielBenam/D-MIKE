"""Interfaz de la etapa estadística: casillas múltiples, Repetir y Copiar. Datos SINTÉTICOS."""
from playwright.sync_api import expect
from test_modulos import SINT
from test_modulos_interfaz import pegar, menu


def test_carta_de_control_con_pruebas_elegidas(pagina):
    pegar(pagina, SINT)
    menu(pagina, "Estadística", "Cartas de control…")
    pagina.select_option(".dialogo select[name='tipo']", "xr"); pagina.select_option(".dialogo select[name='y']", "4")
    pagina.fill(".dialogo input[name='tam']", "4")
    pagina.uncheck(".dialogo .multi[data-campo='pruebas'] input[value='7']")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".pestana.activa")).to_contain_text("Carta X̄-R de tiempo")
    expect(pagina.locator(".resultado .grafica svg")).to_have_count(1)
    expect(pagina.locator(".tabla-res").first).to_contain_text("LSC")


def test_regresion_varios_predictores_repetir_y_copiar(pagina):
    pegar(pagina, "x1\tx2\ty\n" + "\n".join(f"{i}\t{(i * 7) % 5}\t{2 + 0.5 * i + 0.3 * ((i * 7) % 5) + (0.1 if i % 2 else -0.1)}" for i in range(20)))
    menu(pagina, "Estadística", "Regresión…")
    pagina.select_option(".dialogo select[name='y']", "2")
    pagina.check(".dialogo .multi[data-campo='xs'] input[value='0']"); pagina.check(".dialogo .multi[data-campo='xs'] input[value='1']")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".pestana.activa")).to_contain_text("Regresión de y contra x1, x2")
    expect(pagina.locator(".texto-res.interpretacion")).to_contain_text("α = 0.05")
    pagina.click(".vista-barra button:text-is('Copiar')")
    expect(pagina.locator("#sesion")).to_contain_text("Resultado copiado")
    pagina.click(".vista-barra button:text-is('Repetir con datos actuales')")
    expect(pagina.locator(".pestana")).to_have_count(3)
