from playwright.sync_api import expect


def menu(p, titulo, opcion):
    p.click(f".menu > button:text-is('{titulo}')"); p.click(f".menu.abierto button:text-is('{opcion}')")


def test_guardar_abrir_y_descartar(pagina, tmp_path):
    ruta = str(tmp_path / "p.dmike"); pagina.api._elegir = lambda *a, **k: ruta
    pagina.locator("#hoja-tabla [data-f='0'][data-c='0']").click(); pagina.keyboard.type("5"); pagina.keyboard.press("Enter")
    expect(pagina.locator("#archivo")).to_have_text("Sin guardar •")
    pagina.keyboard.press("Control+s")
    expect(pagina.locator("#archivo")).to_have_text("p.dmike")
    pagina.keyboard.type("6"); pagina.keyboard.press("Enter")
    menu(pagina, "Archivo", "Nuevo proyecto")                               # v0.23: el nuevo abre en otra pestaña; nada se descarta
    expect(pagina.locator("#hoja-tabla [data-f='0'][data-c='0']")).to_have_text("")
    expect(pagina.locator(".doc-tab[data-doc]")).to_have_count(2)
    pagina.click(".doc-tab[data-doc='1'] .doc-x")                           # cerrar el proyecto con cambios pide confirmación
    expect(pagina.locator(".dialogo")).to_contain_text("cambios sin guardar")
    pagina.click(".dialogo .primario"); expect(pagina.locator(".doc-tab[data-doc]")).to_have_count(1)
    menu(pagina, "Archivo", "Abrir proyecto…")
    expect(pagina.locator("#hoja-tabla [data-f='0'][data-c='0']")).to_have_text("5")
    expect(pagina.locator("#sesion")).to_contain_text("Proyecto abierto: p.dmike")
