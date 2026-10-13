"""Fuente única de la identidad visual (design tokens). De aquí salen los colores de las gráficas, de las
plantillas de Excel y del tema de Power BI; una prueba verifica que estilos.css use los mismos valores."""
TOKENS = {
    "papel": "#faf8f4", "panel": "#f3efe7", "superficie": "#ffffff", "linea": "#e2dcd0", "rejilla": "#e9e4da",
    "encabezado": "#f0ece4", "tinta": "#2b2620", "tinta-suave": "#6f675b", "tinta-tenue": "#a79f92",
    "acento": "#dd5813", "acento-suave": "#fbe8dd",
    "ok": "#e3f1e0", "advertencia": "#fff4d6", "no": "#fdecea",
}
PALETA_DATOS = ["#dd5813", "#2b6f8f", "#7a8c2e", "#8b4f9e", "#b8860b", "#5a5a5a", "#e8915c", "#6fa3bd"]
FUENTE = "Montserrat"


def tema_power_bi():
    """Tema de informe de Power BI (JSON). [GENERAL] Estructura del tema según la documentación de Microsoft;
    no viene de la base LSS. Si Montserrat no está instalada, Power BI usa la siguiente fuente de la lista."""
    t = TOKENS
    fuente = f"{FUENTE}, 'Segoe UI', sans-serif"
    return {
        "name": "D-MIKE",
        "dataColors": PALETA_DATOS,
        "background": t["superficie"], "foreground": t["tinta"], "tableAccent": t["acento"],
        "good": "#3d8b37", "neutral": "#b8860b", "bad": "#b3261e",
        "maximum": t["acento"], "center": t["acento-suave"], "minimum": t["superficie"],
        "textClasses": {
            "callout": {"fontSize": 28, "fontFace": fuente, "color": t["tinta"]},
            "title": {"fontSize": 12, "fontFace": fuente, "color": t["tinta"]},
            "header": {"fontSize": 12, "fontFace": fuente, "color": t["tinta-suave"]},
            "label": {"fontSize": 10, "fontFace": fuente, "color": t["tinta-suave"]},
        },
    }
