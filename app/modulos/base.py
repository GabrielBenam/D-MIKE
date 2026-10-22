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
class Num(str):
    """A4: texto para mostrar que conserva el número sin redondear (atributo «crudo»). Es un str normal para todo lo demás;
    b_tabla lo usa para guardar la precisión completa y exportar sin el redondeo de la pantalla."""
    crudo = None


def num(x, d=4):
    if x is None: return "—"
    if isinstance(x, str): return x
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)): return "—"
    if isinstance(x, int) or float(x).is_integer() and abs(x) < 1e12: t = f"{int(x):,}"
    else: t = f"{x:,.{d}f}".rstrip("0").rstrip(".") if abs(x) >= 1e-4 else f"{x:.2e}"
    r = Num(t); r.crudo = float(x)
    return r


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


# ---------- A1: faltante no es cero ----------
def auditar_estados(hoja, cols, independientes=False):
    """Cuenta, en las columnas que usa un análisis, las celdas «sin datos» (vacías o declaradas) y «N/A». Un faltante queda fuera
    del cálculo y genera aviso; N/A también queda fuera pero no cuenta como faltante. Solo se miran las filas del rango de datos
    (hasta el último dato de las columnas usadas, o de cada columna si son muestras independientes) y las no ocultas por el filtro.
    Devuelve (avisos, resumen por columna)."""
    act = hoja.filas_activas()
    filas = [i for i in range(hoja.n) if act is None or i in act]
    est = {j: [hoja.columnas[j].estado(i) for i in filas] for j in cols}
    ultimo = lambda lista: max([k for k, e in enumerate(lista) if e != "sin_datos"], default=-1)
    ext = {j: ultimo(est[j]) for j in cols} if independientes else {j: max([ultimo(est[q]) for q in cols], default=-1) for j in cols}
    avisos, resumen = [], {}
    for j in cols:
        dentro = est[j][:ext[j] + 1]
        falt = [filas[k] + 1 for k, e in enumerate(dentro) if e == "sin_datos"]
        n_na = sum(e == "na" for e in est[j])
        if not falt and not n_na: continue
        nom = nombre_col(hoja, j)
        resumen[nom] = {"sin_datos": len(falt), "na": n_na}
        if falt:
            lista = ", ".join(map(str, falt[:5])) + (f" y {len(falt) - 5} más" if len(falt) > 5 else "")
            avisos.append(f"Sin datos: {nom} tiene {len(falt)} {'celda' if len(falt) == 1 else 'celdas'} sin dato (filas {lista}); "
                          "quedan fuera del cálculo y no se cuentan como cero.")
    return avisos, resumen


def agregar_estados_entrada(res, cls, hoja, cols):
    """Agrega al resultado los avisos de faltantes y la nota de N/A (A1)."""
    avisos, resumen = auditar_estados(hoja, cols, getattr(cls, "INDEPENDIENTES", False))
    if not resumen: return res
    res["avisos"] = list(res["avisos"]) + avisos
    res.setdefault("datos", {})["estados_entrada"] = resumen
    n_na = sum(v["na"] for v in resumen.values())
    if n_na:
        res["bloques"].append(b_texto(f"N/A (no aplica): {n_na} {'celda' if n_na == 1 else 'celdas'} quedaron fuera del cálculo y "
                                      "no cuentan como datos faltantes.", "nota"))
    return res


# ---------- G7: análisis por persona ----------
NOTA_PERSONA = ("Atención: no compares el desempeño individual de personas sin normalizar por tipo y complejidad del trabajo. "
                "Las diferencias entre personas pueden venir de la mezcla de trabajos que recibe cada una y no de su desempeño. "
                "Esta nota no bloquea el cálculo.")
_PERSONA = ("persona", "operador", "analista", "tecnico", "inspector", "revisor", "responsable", "empleado", "colaborador",
            "capturista", "autor", "redactor", "evaluador", "ingeniero", "dibujante", "auditor", "usuario", "trabajador", "elaboro", "asignado")
SIN_NOTA_PERSONA = ("MSA-ATR", "MSA-VAR")     # en un MSA los evaluadores son parte del sistema de medición que se estudia


def _sin_acentos(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(c) != "Mn")


def es_columna_persona(nombre):
    n = _sin_acentos(nombre)
    return any(k in n for k in _PERSONA)


def nota_persona(cls, hoja, params):
    """G7: bloque de texto (o None) para el Pareto y para cualquier análisis cuya columna de agrupación parezca identificar personas."""
    if cls.ID in SIN_NOTA_PERSONA: return None
    if cls.ID == "PARETO": return b_texto(NOTA_PERSONA, "advertencia")
    for c in getattr(cls, "CAMPOS", []):
        j = params.get(c["campo"])
        if c.get("tipo") == "col" and c.get("filtro") == "texto" and isinstance(j, int) and 0 <= j < len(hoja.columnas) \
                and es_columna_persona(hoja.columnas[j].nombre or ""):
            return b_texto(NOTA_PERSONA, "advertencia")
    return None


def agregar_nota_persona(res, cls, hoja, params):
    b = nota_persona(cls, hoja, params)
    if b and not any(x.get("clase") == "advertencia" and x.get("texto") == NOTA_PERSONA for x in res["bloques"]):
        res["bloques"].append(b)
    return res


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

def espec_probnormal(x, titulo, xl="", etiq=None, marcar=None):
    """Especificación interactiva de la gráfica de probabilidad normal. [GENERAL] posiciones de Benard, como Minitab. etiq/marcar (por valor, en el orden de x)
    sirven para rotular y destacar puntos (por ejemplo los efectos significativos)."""
    import math
    from scipy import stats as st
    n = len(x)
    pares = sorted(zip([float(v) for v in x], etiq or [""] * n, marcar or [False] * n), key=lambda t: t[0])
    q = [float(st.norm.ppf((i - 0.3) / (n + 0.4))) for i in range(1, n + 1)]
    o = [t[0] for t in pares]; m = sum(o) / n if n else 0
    sd = math.sqrt(sum((v - m) ** 2 for v in o) / (n - 1)) if n > 1 else 0
    pct = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    sp = {"g": "probnormal", "titulo": titulo, "xl": xl, "x": [_f(v) for v in o], "q": q, "etiq": [t[1] for t in pares], "marcar": [bool(t[2]) for t in pares],
          "tq": [float(st.norm.ppf(c / 100)) for c in pct], "tl": [str(c) for c in pct]}
    if sd > 0 and n: sp["linea"] = {"x": [_f(m + q[0] * sd), _f(m + q[-1] * sd)], "q": [q[0], q[-1]]}
    return sp


def espec_residuos(res, aj, titulo="Residuos"):
    """Especificación interactiva de la gráfica de residuos 4 en 1 (probabilidad normal, contra ajustados, histograma y contra orden)."""
    return {"g": "residuos", "titulo": titulo, "pn": espec_probnormal(res, ""), "res": [_f(v) for v in res], "aj": [_f(v) for v in aj]}



def b_tabla(titulo, cabeza, filas, alinear=None):
    """A4: «filas» trae el texto redondeado para mostrar; «crudas» conserva la precisión completa de cada número para exportar."""
    def cruda(v):
        if isinstance(v, Num): return v.crudo
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v == v else None
    crudas = [[cruda(v) for v in f] for f in filas]
    extra = {"crudas": crudas} if any(x is not None for f in crudas for x in f) else {}
    return {"tipo": "tabla", "titulo": titulo, "cabeza": cabeza, **extra, "filas": [[num(v) if not isinstance(v, str) else v
                                                                          for v in f] for f in filas],
            "alinear": alinear or ["i"] + ["d"] * (len(cabeza) - 1)}


def b_texto(texto, clase="nota"): return {"tipo": "texto", "texto": texto, "clase": clase}
