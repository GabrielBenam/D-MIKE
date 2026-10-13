"""Formatos de gestión (PMBOK) en la interfaz real. Datos SINTÉTICOS."""
from playwright.sync_api import expect
from test_modulos_interfaz import menu


def test_raci_encabezados_y_riesgos(pagina):
    menu(pagina, "Gestión", "Matriz de responsabilidades (RACI)")
    pagina.fill(".formato input[name='p1']", "Líder"); pagina.keyboard.press("Tab")
    expect(pagina.locator(".tabla-fmt th[data-campo='p1']")).to_have_text("Líder")
    menu(pagina, "Gestión", "Registro de riesgos")
    pagina.select_option(".tabla-fmt select[name='tipo'] >> nth=0", "Amenaza")
    pagina.fill(".tabla-fmt input[name='riesgo'] >> nth=0", "Falla del molde"); pagina.keyboard.press("Tab")
    pagina.select_option(".tabla-fmt select[name='probabilidad'] >> nth=0", "Alta")
    pagina.select_option(".tabla-fmt select[name='impacto'] >> nth=0", "Alto")
    expect(pagina.locator(".tabla-fmt td[data-c='puntaje']").first).to_have_text("0.28")
    expect(pagina.locator(".formato svg")).to_have_count(1)


def test_interesados_crea_filas_de_analisis(pagina):
    menu(pagina, "Gestión", "Registro de interesados")
    pagina.fill(".tabla-fmt[data-tabla='registro'] input[name='nombre'] >> nth=0", "Gerente"); pagina.keyboard.press("Tab")
    expect(pagina.locator(".tabla-fmt[data-tabla='analisis'] td[data-c='nombre']").first).to_have_text("Gerente")


def test_cronograma_fija_linea_base_y_dibuja(pagina):
    a = pagina.api
    d = a.abrir_formato("CRONOGRAMA")["datos"]
    for f, v in zip(d["tablas"]["actividades"], ({"id": "A", "m": "5"}, {"id": "B", "m": "5", "pred": "A"}, {"id": "C", "m": "10", "pred": "A"}, {"id": "D", "m": "15", "pred": "B, C"})):
        f.update(v)
    a.guardar_formato("CRONOGRAMA", d)
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    menu(pagina, "Gestión", "Cronograma y ruta crítica")
    expect(pagina.locator(".formato output[data-cab='ruta']")).to_have_text("A → C → D")
    pagina.select_option(".formato select[name='fijar_base']", "fijar")
    expect(pagina.locator(".formato input[name='base_fecha']")).not_to_have_value("")
    expect(pagina.locator(".formato input[name='base_fin']").nth(3)).to_have_value("30.0")
    expect(pagina.locator(".formato select[name='fijar_base']")).to_have_value("")
    menu(pagina, "Gestión", "EDT y diccionario"); expect(pagina.locator(".pestana.activa")).to_contain_text("EDT")
