import sys, threading, functools, http.server
from pathlib import Path
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
UI = RAIZ / "app" / "ui"

PUENTE_JS = """
window.pywebview = { api: new Proxy({}, { get: (_, n) => (...a) => window.__py(n, a) }) };
"""
# Las pruebas anteriores a v0.21 corren con la disposición clásica (menú desplegable, panel ancho, sin pantalla de inicio).
# test_ui_v021.py prueba la interfaz nueva con NUEVA_UI_JS.
CLASICA_JS = """
try { if (!sessionStorage.getItem("dmike_ui_nueva")) { localStorage.setItem("dmike_cinta", "0"); localStorage.setItem("dmike_riel", "0"); localStorage.setItem("dmike_inicio", "0"); localStorage.setItem("dmike_graficas_int", "0"); } } catch (e) {}
"""


@pytest.fixture(scope="session")
def servidor():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(UI))
    h.log_message = lambda *a: None
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{s.server_address[1]}/index.html"
    s.shutdown()


@pytest.fixture
def pagina(servidor):
    """Abre la interfaz real con el Api real de Python como puente (igual que pywebview)."""
    from playwright.sync_api import sync_playwright
    from app.api import Api
    api = Api()
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:                       # sin el navegador de pruebas (p. ej. en GitHub Actions): se omite, no falla
            pytest.skip(f"Prueba de interfaz omitida: no hay navegador de Playwright instalado ({str(e).splitlines()[0][:80]})")
        pg = b.new_page(viewport={"width": 1366, "height": 768})
        pg.expose_function("__py", lambda n, a: getattr(api, n)(*a))
        pg.add_init_script(PUENTE_JS); pg.add_init_script(CLASICA_JS)
        pg.goto(servidor)
        pg.wait_for_selector("body[data-listo='1']")
        pg.api = api
        yield pg
        b.close()


def pytest_configure(config):
    config.addinivalue_line("markers", "interfaz: prueba que abre la interfaz en un navegador (Playwright)")


def pytest_collection_modifyitems(config, items):
    """Toda prueba que usa el fixture «pagina» se marca como «interfaz», esté en el archivo que esté.
    En la compilación se corre con -m "not interfaz" (solo el motor)."""
    for it in items:
        if "pagina" in getattr(it, "fixturenames", ()): it.add_marker(pytest.mark.interfaz)
