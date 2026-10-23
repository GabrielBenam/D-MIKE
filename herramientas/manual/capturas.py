"""Capturas anotadas de la interfaz web para el manual: python herramientas/manual/capturas.py [--salida CARPETA] [--solo ID]
Abre la interfaz real (app/ui) con Playwright y el Api real de Python como puente (PUENTE_JS de pruebas/conftest.py), carga datos SINTÉTICOS de la ficha,
y toma capturas numeradas <ID>_<n>.png más capturas.json (ID, número, título, descripción, punto de la ficha, leyenda, huella SHA-256).
Solo interfaz web: los diálogos nativos de Windows (abrir archivo, guardar, instalador) no se capturan; se declaran en «pendientes».
Toda captura de demostración lleva la etiqueta «SINTÉTICO / NO EMPRESARIAL». Si un selector no se encuentra, se reporta y el programa termina con error: no se salta."""
import argparse, functools, hashlib, http.server, json, os, shutil, sys, tempfile, threading
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "pruebas"))
ETIQUETA = "SINTÉTICO / NO EMPRESARIAL"
VIEWPORT = {"width": 1280, "height": 760}


class FalloCaptura(Exception):
    pass


def servidor(ui):
    """Servidor local de app/ui (igual que el fixture «servidor» de pruebas/conftest.py)."""
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k): super().__init__(*a, directory=str(ui), **k)
        def log_message(self, *a): pass
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, f"http://127.0.0.1:{s.server_address[1]}/index.html"


JS_ANOTAR = """items => {
  const mk = (css, txt) => { const d = document.createElement('div'); d.className = 'dmike-anot'; d.style.cssText = css; if (txt) d.textContent = txt; document.body.append(d); };
  for (const it of items) {
    mk(`position:fixed;left:${it.x - 2}px;top:${it.y - 2}px;width:${it.w + 4}px;height:${it.h + 4}px;border:2px solid #dd5813;border-radius:4px;z-index:99998;pointer-events:none`);
    mk(`position:fixed;left:${Math.max(2, it.x - 12)}px;top:${Math.max(2, it.y - 12)}px;width:22px;height:22px;border-radius:50%;background:#dd5813;color:#fff;font:700 13px sans-serif;display:flex;align-items:center;justify-content:center;z-index:99999;box-shadow:0 0 0 2px #fff;pointer-events:none`, String(it.n));
  }
}"""
JS_ETIQUETA = """t => { const d = document.createElement('div'); d.className = 'dmike-anot'; d.textContent = t;
  d.style.cssText = 'position:fixed;right:8px;bottom:8px;z-index:99999;background:#fdecc8;color:#7a2f08;border:2px solid #dd5813;border-radius:4px;padding:3px 10px;font:700 12px sans-serif;pointer-events:none'; document.body.append(d); }"""
JS_ENMASCARAR = """() => { document.querySelectorAll('.sesion-lista .hora').forEach(e => { e.textContent = '--:--:--'; });
  document.querySelectorAll('.vista-fecha').forEach(e => { e.textContent = 'AAAA-MM-DD hh:mm'; }); }"""


class Escena:
    """Una sesión de interfaz limpia (Api nuevo, APPDATA temporal) en modo demostración, con los datos sintéticos de la ficha."""
    def __init__(self, p, url, ficha_id, salida, modo="demo"):
        from app.api import Api
        from conftest import PUENTE_JS
        self.id, self.salida, self.modo, self.caps = ficha_id, salida, modo, []
        self.api = Api()
        if modo == "demo": self.api.cambiar_modo("demostracion")        # en modo real nunca se cargan datos sintéticos; las capturas de demostración se rotulan
        self.nav = p.chromium.launch(); self.pg = self.nav.new_page(viewport=VIEWPORT)
        self.pg.expose_function("__py", lambda n, a: getattr(self.api, n)(*a))
        self.pg.add_init_script(PUENTE_JS)
        self.pg.add_init_script("try { localStorage.setItem('dmike_inicio', '0'); } catch (e) {}")
        self.pg.goto(url); self.pg.wait_for_selector("body[data-listo='1']")

    def cerrar(self): self.nav.close()

    # --- acciones de interfaz ---
    def pegar(self, texto):
        if self.modo != "demo": raise FalloCaptura("en modo real nunca se cargan datos sintéticos")
        self.pg.locator("#hoja-tabla th.nombre[data-c='0']").click()
        self.pg.evaluate("""t => { const d = new DataTransfer(); d.setData('text/plain', t);
            document.querySelector('#hoja').dispatchEvent(new ClipboardEvent('paste', {clipboardData: d, bubbles: true})); }""", texto)
        self.pg.wait_for_timeout(200)

    def cinta(self, pestana, boton=None):
        self.pg.click(f"#menus .menu > button:text-is('{pestana}')")
        if boton: self.pg.locator("#cinta .cinta-b").filter(has_text=boton).first.click()
        self.pg.wait_for_timeout(250)

    def aceptar(self):
        self.pg.click(".dialogo .primario"); self.pg.wait_for_timeout(400)

    # --- captura con anotaciones ---
    def captura(self, n, titulo, descripcion, punto, anot=(), enmascarar=True):
        pg = self.pg; items, ley = [], []
        for i, (sel, texto) in enumerate(anot, 1):
            loc = pg.locator(sel).first
            if loc.count() == 0: raise FalloCaptura(f"{self.id}_{n}: el selector «{sel}» no existe en la pantalla")
            loc.scroll_into_view_if_needed(); bb = loc.bounding_box()
            if not bb or bb["width"] == 0 or bb["height"] == 0: raise FalloCaptura(f"{self.id}_{n}: el selector «{sel}» no tiene área visible")
            if bb["y"] < 0 or bb["y"] + 4 > VIEWPORT["height"] or bb["x"] + 4 > VIEWPORT["width"]:
                raise FalloCaptura(f"{self.id}_{n}: el selector «{sel}» queda fuera de la pantalla capturada")
            items.append({"n": i, "x": bb["x"], "y": bb["y"], "w": min(bb["width"], VIEWPORT["width"] - bb["x"]), "h": min(bb["height"], VIEWPORT["height"] - bb["y"])})
            ley.append({"n": i, "texto": texto, "selector": sel})
        pg.add_style_tag(content="*, *::before, *::after { transition: none !important; animation: none !important; caret-color: transparent !important; }")
        pg.mouse.move(2, 2); pg.wait_for_timeout(250)                               # sin cursor encima de botones (hover) ni transiciones a medias
        if enmascarar: pg.evaluate(JS_ENMASCARAR)
        if self.modo == "demo": pg.evaluate(JS_ETIQUETA, ETIQUETA)
        if items: pg.evaluate(JS_ANOTAR, items)
        archivo = f"{self.id}_{n}.png"; ruta = self.salida / archivo
        pg.screenshot(path=str(ruta), animations="disabled", caret="hide")
        pg.evaluate("() => document.querySelectorAll('.dmike-anot').forEach(e => e.remove())")
        self.caps.append({"id": self.id, "n": n, "archivo": archivo, "titulo": titulo, "descripcion": descripcion, "punto": punto, "leyenda": ley,
                          "sintetico": self.modo == "demo", "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest()})


# ---------- escenas (una por ficha con capturas) ----------
def escena_estadisticos(e):
    e.pegar("tiempo\n8\n10\n10\n12\n15")
    e.captura(1, "Datos pegados en la hoja", "El nombre «tiempo» queda en el encabezado de la columna y los cinco valores debajo, uno por fila.", 8,
              [("#hoja-tabla th.nombre[data-c='0']", "nombre de la columna (la variable)"), ("#hoja-tabla [data-f='0'][data-c='0']", "primer dato; los cinco forman la columna")])
    e.pg.click("#menus .menu > button:text-is('Calc')")
    e.captura(2, "Ruta en la cinta", "La pestaña Calc muestra el subgrupo «Probabilidad y resumen» con el botón «Estadísticos de columna».", 8,
              [("#menus .menu > button:text-is('Calc')", "pestaña Calc"), ("#cinta .cinta-b:has-text('Estadísticos de columna')", "botón Estadísticos de columna")])
    e.pg.locator("#cinta .cinta-b").filter(has_text="Estadísticos de columna").first.click()
    e.pg.wait_for_selector(".dialogo select[name='y']"); e.pg.select_option(".dialogo select[name='y']", "0")
    e.captura(3, "Diálogo del módulo", "«Variable» es obligatoria; «Por grupo (opcional)» se deja en «(ninguna)» para obtener una sola fila «Todos».", 8,
              [(".dialogo select[name='y']", "Variable (columna numérica)"), (".dialogo select[name='grupo']", "Por grupo (opcional)"), (".dialogo .primario", "Aceptar: abre el resultado")])
    e.aceptar()
    e.pg.wait_for_selector(".tabla-res")
    e.captura(4, "Resultado: tabla de estadísticos descriptivos", "Una fila «Todos» con las 19 columnas; la etiqueta de la barra recuerda que los datos son sintéticos.", 9,
              [(".tabla-res", "tabla «Estadísticos descriptivos» (19 columnas; se desplaza hacia la derecha)"), (".pestana.activa", "pestaña del resultado")])


def escena_reemplazar(e):
    e.pegar("operador\ttiempo\nOp1\t12,5\nop1\t14,0\nOp2\t13,1\nOp1 \t\n")
    e.pg.click("#menus .menu > button:text-is('Editar')")
    e.captura(1, "Ruta en la cinta", "La pestaña Editar tiene el subgrupo «Selección y búsqueda» con «Buscar y reemplazar».", 8,
              [("#menus .menu > button:text-is('Editar')", "pestaña Editar"), ("#cinta .cinta-b:has-text('Buscar y reemplazar')", "botón Buscar y reemplazar")])
    e.pg.locator("#cinta .cinta-b").filter(has_text="Buscar y reemplazar").first.click()
    e.pg.wait_for_selector(".dialogo input[name='buscar']")
    e.pg.fill(".dialogo input[name='buscar']", ","); e.pg.fill(".dialogo input[name='nuevo']", "."); e.pg.select_option(".dialogo select[name='col']", "1")
    e.captura(2, "Diálogo con coma por punto en la columna tiempo", "Se busca «,», se reemplaza por «.» y se limita a la columna «tiempo». Las dos casillas quedan apagadas.", 8,
              [(".dialogo input[name='buscar']", "Buscar"), (".dialogo input[name='nuevo']", "Reemplazar por (vacío = borrar)"), (".dialogo select[name='col']", "En la columna (vacío = todas)"),
               (".dialogo input[name='completa']", "Solo celdas completas"), (".dialogo .primario", "Aceptar: el cambio se aplica directo")])
    e.aceptar()
    e.pg.click(".sesion-titulo"); e.pg.wait_for_timeout(250)
    e.captura(3, "La hoja después del reemplazo", "Los tres valores con coma pasaron a punto y el mensaje de la sesión cuenta las celdas cambiadas.", 9,
              [("#hoja-tabla [data-f='0'][data-c='1']", "celda cambiada: 12,5 ahora es 12.5"), ("#sesion li:last-child", "mensaje «Reemplazos hechos: 3.»")])


def _poner(e, formato, tabla, fila, campo, valor):
    td = e.pg.locator(f".tabla-fmt[data-tabla='{tabla}'] tbody tr[data-i='{fila}'] td[data-c='{campo}']")
    if td.locator("select").count(): td.locator("select").select_option(valor)
    else: td.locator("input").fill(valor); td.locator("input").press("Tab")


def escena_charter(e):
    e.cinta("Herramientas de calidad")
    e.captura(1, "Ruta en la cinta", "La pestaña Herramientas de calidad tiene el subgrupo «Definir el problema» con el botón «Acta del proyecto».", 4,
              [("#menus .menu > button:text-is('Herramientas de calidad')", "pestaña Herramientas de calidad"), ("#cinta .cinta-b:has-text('Acta del proyecto')", "botón Acta del proyecto")])
    e.pg.locator("#cinta .cinta-b").filter(has_text="Acta del proyecto").first.click()
    e.pg.wait_for_selector("#avisos-CHARTER .aviso-res")
    e.captura(2, "Acta vacía con sus siete avisos", "Sin llenar nada, el formato avisa lo que falta; nada bloquea guardar.", 10,
              [("#avisos-CHARTER", "siete avisos de completitud"), (".cabecera-fmt textarea[name='caso_negocio']", "caso de negocio")])
    e.pg.fill(".cabecera-fmt textarea[name='caso_negocio']", "Como compañía, el desempeño de la unión adhesiva en el área de ensamble no cumple 30 MPa. (SINTÉTICO)")
    e.pg.press(".cabecera-fmt textarea[name='caso_negocio']", "Tab")
    e.pg.fill(".cabecera-fmt textarea[name='alcance']", "Proceso de curado de paneles (SINTÉTICO)"); e.pg.press(".cabecera-fmt textarea[name='alcance']", "Tab")
    for i, (ctq, base, obj, ah) in enumerate([("Resistencia de unión", "30.8 MPa", "35 MPa", "120000"), ("Porosidad", "2.2 %", "1.5 %", "")]):
        for campo, v in (("ctq", ctq), ("base", base), ("objetivo", obj), ("ahorro", ah)):
            if v: _poner(e, "CHARTER", "objetivos", i, campo, v)
    _poner(e, "CHARTER", "equipo", 0, "rol", "Líder"); _poner(e, "CHARTER", "equipo", 0, "nombre", "Persona A (sintética)")
    e.pg.wait_for_timeout(400)
    e.pg.evaluate("for (let x = document.querySelector('#avisos-CHARTER'); x; x = x.parentElement) x.scrollTop = 0")
    e.captura(3, "Acta diligenciada con datos sintéticos", "Con dos objetivos (uno con ahorro) y un líder quedan cinco avisos de completitud más dos sobre el ahorro, y el total esperado.", 11,
              [("#avisos-CHARTER", "avisos que siguen abiertos"), ("#bloques-CHARTER", "«Ahorro total esperado» con su base: 1 de 2 objetivos")])


ESCENAS = {"ESTADISTICOS": escena_estadisticos, "REEMPLAZAR": escena_reemplazar, "CHARTER": escena_charter}
PENDIENTES = [
    {"id": "ESTADISTICOS", "punto": 8, "motivo": "«Archivo › Importar archivo» abre el diálogo nativo de Windows para elegir el archivo; solo se capturó el pegado en la hoja."},
    {"id": "ESTADISTICOS", "punto": 14, "motivo": "«Exportar…» abre el cuadro nativo de Windows para guardar el .xlsx."},
    {"id": "CHARTER", "punto": 14, "motivo": "«Exportar a Excel…» abre el cuadro nativo de Windows para guardar el .xlsx."}]


def generar(salida, solo=None):
    """Genera las capturas en `salida`. Devuelve (lista de capturas, lista de fallos). Usa APPDATA temporal."""
    from playwright.sync_api import sync_playwright
    from importlib.metadata import version
    salida = Path(salida); salida.mkdir(parents=True, exist_ok=True)
    for viejo in list(salida.glob("*.png")) + [salida / "capturas.json"]:
        if solo is None: viejo.unlink(missing_ok=True)
    previo = os.environ.get("APPDATA"); tmp = tempfile.mkdtemp(prefix="dmike_capturas_"); os.environ["APPDATA"] = tmp
    srv, url = servidor(RAIZ / "app" / "ui"); caps, fallos = [], []
    try:
        with sync_playwright() as p:
            for fid, fn in ESCENAS.items():
                if solo and fid != solo: continue
                e = Escena(p, url, fid, salida)
                try: fn(e)
                except Exception as ex: fallos.append(f"{fid}: {type(ex).__name__}: {str(ex).splitlines()[0][:300]}")
                finally: caps += e.caps; e.cerrar()
    finally:
        srv.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
        if previo is None: os.environ.pop("APPDATA", None)
        else: os.environ["APPDATA"] = previo
    if not fallos and not solo:
        from app.api import VERSION
        (salida / "capturas.json").write_text(json.dumps({"version": VERSION, "playwright": version("playwright"), "etiqueta": ETIQUETA, "capturas": caps,
                                                         "pendientes": PENDIENTES}, ensure_ascii=False, indent=1), encoding="utf-8")
    return caps, fallos


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", default=str(AQUI / "salida" / "capturas"), help="carpeta de salida (por omisión herramientas/manual/salida/capturas)")
    ap.add_argument("--solo", help="genera solo las capturas de este ID de ficha (no escribe capturas.json)")
    a = ap.parse_args()
    caps, fallos = generar(a.salida, a.solo)
    for c in caps: print(f"{c['archivo']}  {c['sha256'][:12]}  {c['titulo']}")
    for f in fallos: print("FALLO:", f, file=sys.stderr)
    sys.exit(2 if fallos else 0)
