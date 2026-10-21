"""A6: las gráficas de prioridad alta (12 tipos) ya son editables desde v0.25; las de prioridad media esperan confirmación del usuario."""

def test_a6_resultado_viejo_avisa_que_la_grafica_es_fija(pagina):
    """A6 (pendiente de v0.25): un resultado sin especificación de gráfica editable indica cómo obtenerla."""
    from playwright.sync_api import expect
    a = pagina.api
    a.pegar(-1, 0, "y\n" + "\n".join(str(10 + i % 5) for i in range(20)))
    r = a.ejecutar_modulo("CORRIDA", {"y": 0})["resultado"]
    for b in r["bloques"]: b.pop("inter", None)                                  # como un resultado guardado antes de v0.25
    pagina.evaluate("r => abrirPestana('res:' + r.uid, r)", r)
    expect(pagina.locator(".texto-res.nota").first).to_contain_text("imagen fija de una versión anterior")
