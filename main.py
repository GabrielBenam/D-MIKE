"""Arranque de D-MIKE: abre la interfaz en una ventana propia (WebView2 en Windows).

D-MIKE.exe                 abre el programa vacío
D-MIKE.exe archivo.dmike   abre ese proyecto (doble clic en un .dmike)
D-MIKE.exe --prueba        verifica que el ejecutable trae todo lo necesario y sale (lo usa la compilación)
"""
import sys


def prueba():
    """Revisión sin ventana: catálogo, fuentes, librerías de cálculo, guardado y exportación."""
    import os, tempfile
    from app.api import Api
    from app.nucleo.rutas import recurso
    for r in (("ui", "index.html"), ("ui", "app.js"), ("ui", "fuentes", "Montserrat.woff2"),
              ("datos", "arbol_diagnostico.json"), ("datos", "fuentes", "Montserrat-Regular.ttf"), ("datos", "fuentes", "Montserrat-Bold.ttf")):
        if not recurso(*r).exists(): raise FileNotFoundError("/".join(r))
    import numpy, scipy.stats, matplotlib, openpyxl, webview  # noqa: F401
    if sys.platform == "win32":
        from webview.platforms import winforms  # noqa: F401  (carga pythonnet y WebView2)
    api = Api(); api.pegar(-1, 0, "x\n1\n2\n3")
    with tempfile.TemporaryDirectory() as d:
        api._elegir = lambda *a, **k: os.path.join(d, "p.dmike")
        assert api.guardar()["error"] is None
        assert api.exportar(os.path.join(d, "x.xlsx"))["error"] is None
    from app import modulos
    modulos.autoprueba()
    return 0


def main():
    if "--prueba" in sys.argv:
        try:
            sys.exit(prueba())
        except Exception as e:  # el código de salida lo lee la compilación
            with open("prueba_error.txt", "w", encoding="utf-8") as f: f.write(repr(e))
            sys.exit(1)
    import webview
    from app.api import Api
    from app.nucleo.rutas import recurso
    api = Api()
    archivo = next((a for a in sys.argv[1:] if a.lower().endswith(".dmike")), None)
    if archivo: api.abrir_proyecto(archivo)
    ventana = webview.create_window("D-MIKE", url=str(recurso("ui", "index.html")), js_api=api,
                                    width=1366, height=820, min_size=(1100, 680))
    api._ventana = ventana

    def al_cerrar():
        # Si hay cambios sin guardar, pregunta antes de cerrar. Devolver False cancela el cierre.
        if not api.modificado(): return True
        try:
            return ventana.create_confirmation_dialog("D-MIKE", "Hay cambios sin guardar. ¿Salir sin guardar?")
        except Exception:
            return True

    ventana.events.closing += al_cerrar
    webview.start()


if __name__ == "__main__":
    main()
