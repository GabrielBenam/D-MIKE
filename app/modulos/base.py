"""Piezas comunes de los módulos: validación de entradas, lectura de columnas, gráficas y bloques de resultado."""
import base64, io, math, uuid
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from ..nucleo.rutas import recurso

from ..nucleo.tokens import TOKENS, PALETA_DATOS
NARANJA, TINTA, SUAVE, REJILLA, CLARO = (TOKENS[k] for k in ("acento", "tinta", "tinta-suave", "rejilla", "acento-suave"))
PALETA = PALETA_DATOS
_fuente_lista = False


class ErrorEntrada(Exception):
    """Datos insuficientes o inválidos: el mensaje explica qué falta. No se genera resultado."""


def preparar_fuente():
    global _fuente_lista
    if _fuente_lista: return
    # Instancias estáticas (400 y 700) de la Montserrat variable: la variable trae «Thin» como instancia por omisión
    # y las imágenes PNG salían con trazo delgado.
    hay = False
    for nombre in ("Montserrat-Regular.ttf", "Montserrat-Bold.ttf"):
        ttf = recurso("datos", "fuentes", nombre)
        if ttf.exists(): font_manager.fontManager.addfont(str(ttf)); hay = True
    if hay: plt.rcParams["font.family"] = "Montserrat"
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": SUAVE, "axes.labelcolor": TINTA, "xtick.color": SUAVE,
                         "ytick.color": SUAVE, "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.8,
                         "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none",
                         "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlecolor": TINTA})
    _fuente_lista = True


def figura(ancho=6.4, alto=3.6, ncols=1, nrows=1):
    preparar_fuente()
    return plt.subplots(nrows, ncols, figsize=(ancho, alto), dpi=100)


def a_svg_png(fig):
    fig.tight_layout()
    b = io.StringIO(); fig.savefig(b, format="svg", transparent=True)
    p = io.BytesIO(); fig.savefig(p, format="png", dpi=150, facecolor="white")
    plt.close(fig)
    svg = b.getvalue(); svg = svg[svg.index("<svg"):]
    return svg, base64.b64encode(p.getvalue()).decode("ascii")


# ---------- columnas ----------
def columna(hoja, j, etiqueta, tipo=None, obligatoria=True):
    if j is None or j == "" or j < 0:
        if obligatoria: raise ErrorEntrada(f"Falta elegir {etiqueta}.")
        return None
    if j >= len(hoja.columnas): raise ErrorEntrada(f"La columna elegida para {etiqueta} ya no existe.")
    c = hoja.columnas[j]
    if tipo and c.tipo != tipo:
        nom = {"num": "numérica", "texto": "de texto", "fecha": "de fecha"}[tipo]
        raise ErrorEntrada(f"{nombre_col(hoja, j)} no es una columna {nom}.")
    return c


def nombre_col(hoja, j):
    c = hoja.columnas[j]
    return f"C{j + 1} {c.nombre}".strip()


def filas_validas(hoja, cols):
    """Filas donde todas las columnas dadas tienen un valor válido. Devuelve (filas, excluidas)."""
    buenas, fuera = [], 0
    act = hoja.filas_activas()
    for i in range(hoja.n):
        if act is not None and i not in act: continue                   # fila oculta por el filtro
        vals = [hoja.columnas[j].valor(i) for j in cols]
        if all(v[2] is None and v[1] for v in vals): continue          # fila vacía en esas columnas
        if all(v[1] and v[2] is not None for v in vals): buenas.append(i)
        else: fuera += 1
    return buenas, fuera


def valor(hoja, j, i):
    return hoja.columnas[j].valor(i)[2]


# ---------- formato de números ----------
def num(x, d=4):
    if x is None: return "—"
    if isinstance(x, str): return x
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)): return "—"
    if isinstance(x, int) or float(x).is_integer() and abs(x) < 1e12: return f"{int(x):,}"
    return f"{x:,.{d}f}".rstrip("0").rstrip(".") if abs(x) >= 1e-4 else f"{x:.2e}"


def p_texto(p, piso=0.001):
    """Valor p con tres decimales, como Minitab (que muestra 0.000 cuando redondea a cero; aquí «< 0.001»).
    Para Anderson-Darling Minitab reporta «< 0.005»: usar piso=0.005."""
    if piso > 0.001: return f"< {piso:g}" if p < piso else f"{p:.3f}"
    r = f"{p:.3f}"
    return "< 0.001" if r == "0.000" else r


def p_igual(p, piso=0.001):
    t = p_texto(p, piso)
    return f"p {t}" if t.startswith("<") else f"p = {t}"


# ---------- resultado ----------
def resultado(modulo, titulo, params, bloques, avisos=(), datos=None, png=None, supuestos=(), interpretacion=()):
    """Resultado de análisis. La definición reproducible (columnas por nombre, parámetros, fecha) la agrega
    api.ejecutar_modulo. supuestos: [(supuesto, cómo se revisó, qué se encontró)]; interpretación: frases
    cuidadas («no se rechaza H0» no es «son iguales»; asociación no es causalidad)."""
    bl = list(bloques)
    if interpretacion:
        bl.insert(1 if bl and bl[0]["tipo"] == "grafica" else 0, {"tipo": "texto", "clase": "interpretacion",
                                                                   "texto": " ".join(interpretacion)})
    if supuestos:
        bl.append(b_tabla("Supuestos del análisis", ["Supuesto", "Cómo se revisó", "Qué se encontró"], [list(s) for s in supuestos],
                          ["i", "i", "i"]))
    return {"uid": uuid.uuid4().hex[:10], "modulo": modulo, "titulo": titulo,
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "params": params, "bloques": bl,
            "avisos": list(avisos), "datos": datos or {}, "png": png}


def frase_p(p, alfa, h0, ha):
    """Conclusión de una prueba con redacción correcta (no afirma igualdad cuando no se rechaza H0)."""
    if p < alfa:
        return (f"Con α = {alfa}, {p_igual(p)} es menor que α: se rechaza H0 ({h0}). Hay evidencia estadística de que {ha}. "
                "Que sea significativo no dice si el efecto importa en la práctica: compáralo con lo que el proceso necesita.")
    return (f"Con α = {alfa}, {p_igual(p)} no es menor que α: no se rechaza H0 ({h0}). La evidencia no alcanza para afirmar que {ha}; "
            "esto no demuestra que H0 sea cierta (puede faltar tamaño de muestra).")


def b_grafica(svg, inter=None):
    """Gráfica: la imagen fija (reportes y exportación) y, opcional, su especificación para dibujarla interactiva en la interfaz."""
    b = {"tipo": "grafica", "svg": svg}
    if inter: b["inter"] = inter
    return b


def _f(v):
    """Número para la especificación interactiva (None si no es finito)."""
    try:
        v = float(v)
        return v if v == v and abs(v) != float("inf") else None
    except (TypeError, ValueError):
        return None


def b_tabla(titulo, cabeza, filas, alinear=None):
    """A4: «filas» trae el texto redondeado para mostrar; «crudas» conserva la precisión completa de cada número para exportar."""
    crudas = [[float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v == v else None for v in f] for f in filas]
    extra = {"crudas": crudas} if any(x is not None for f in crudas for x in f) else {}
    return {"tipo": "tabla", "titulo": titulo, "cabeza": cabeza, **extra, "filas": [[num(v) if not isinstance(v, str) else v
                                                                          for v in f] for f in filas],
            "alinear": alinear or ["i"] + ["d"] * (len(cabeza) - 1)}


def b_texto(texto, clase="nota"): return {"tipo": "texto", "texto": texto, "clase": clase}
