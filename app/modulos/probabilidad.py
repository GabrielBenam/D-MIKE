"""Calc > Distribuciones de probabilidad (como Calc > Probability Distributions de Minitab): densidad o probabilidad puntual,
acumulada, cola superior, entre dos valores e inversa, con la fórmula equivalente de Excel en español que usa el curso.
Fuente: 25_BB_DISTRIBUCIONES (DIST-NORMAL, DIST-Z, DIST-EJ-Z, DIST-LOGNORMAL, DIST-WEIBULL, DIST-BINOMIAL, DIST-POISSON,
DIST-IDENTIFICAR) y 20_GB_TABLA_F. Verificado con los ejemplos de esos bloques."""
import math
import numpy as np
from scipy import stats as st
from . import registrar
from .base import ErrorEntrada, figura, a_svg_png, num, resultado, b_grafica, b_tabla, b_texto, NARANJA, TINTA, CLARO
from .dialogo import ModuloDialogo

DISTS = [["normal", "Normal (media, desviación)"], ["t", "t de Student (grados de libertad)"], ["chi2", "Chi cuadrada (grados de libertad)"],
         ["f", "F (GL del numerador, GL del denominador)"], ["exponencial", "Exponencial (media)"], ["weibull", "Weibull (forma, escala)"],
         ["lognormal", "Lognormal (ubicación = media del ln, escala = desviación del ln)"], ["uniforme", "Uniforme (mínimo, máximo)"],
         ["binomial", "Binomial (n, p)"], ["poisson", "Poisson (media λ)"]]
CALCULOS = [["acum", "Probabilidad acumulada P(X ≤ x)"], ["mayor", "Cola superior P(X > x)"], ["entre", "Entre dos valores P(a < X ≤ b)"],
            ["puntual", "Densidad f(x) o probabilidad puntual P(X = x)"], ["inversa", "Inversa: x tal que P(X ≤ x) = probabilidad"]]
DISCRETAS = ("binomial", "poisson")


def distribucion(nombre, a, b):
    """Objeto de scipy y fórmula de Excel en español (versión 2010 o posterior) para cada distribución."""
    if nombre == "normal":
        if b is None or b <= 0: raise ErrorEntrada("La desviación debe ser mayor que cero.")
        return st.norm(a, b), ("DISTR.NORM.N({x}; " + f"{num(a)}; {num(b)}" + "; {c})", "INV.NORM({p}; " + f"{num(a)}; {num(b)})")
    if nombre == "t":
        if a is None or a <= 0: raise ErrorEntrada("Los grados de libertad deben ser mayores que cero.")
        return st.t(a), ("DISTR.T.N({x}; " + f"{num(a)}" + "; {c})", "INV.T({p}; " + f"{num(a)})")
    if nombre == "chi2":
        if a is None or a <= 0: raise ErrorEntrada("Los grados de libertad deben ser mayores que cero.")
        return st.chi2(a), ("DISTR.CHICUAD({x}; " + f"{num(a)}" + "; {c})", "INV.CHICUAD({p}; " + f"{num(a)})")
    if nombre == "f":
        if not a or not b or a <= 0 or b <= 0: raise ErrorEntrada("Los grados de libertad deben ser mayores que cero.")
        return st.f(a, b), ("DISTR.F.N({x}; " + f"{num(a)}; {num(b)}" + "; {c})", "INV.F({p}; " + f"{num(a)}; {num(b)})")
    if nombre == "exponencial":
        if a is None or a <= 0: raise ErrorEntrada("La media debe ser mayor que cero.")
        return st.expon(scale=a), ("DISTR.EXP.N({x}; " + f"{num(1 / a, 6)}" + "; {c})", None)
    if nombre == "weibull":
        if not a or not b or a <= 0 or b <= 0: raise ErrorEntrada("Forma y escala deben ser mayores que cero.")
        return st.weibull_min(a, scale=b), ("DISTR.WEIBULL({x}; " + f"{num(a)}; {num(b)}" + "; {c})", None)
    if nombre == "lognormal":
        if b is None or b <= 0: raise ErrorEntrada("La escala (desviación del logaritmo) debe ser mayor que cero.")
        return st.lognorm(b, scale=math.exp(a)), ("DISTR.LOGNORM({x}; " + f"{num(a)}; {num(b)}" + "; {c})", "INV.LOGNORM({p}; " + f"{num(a)}; {num(b)})")
    if nombre == "uniforme":
        if a is None or b is None or b <= a: raise ErrorEntrada("El máximo debe ser mayor que el mínimo.")
        return st.uniform(a, b - a), (None, None)
    if nombre == "binomial":
        if a is None or a < 1 or a != int(a) or b is None or not 0 <= b <= 1: raise ErrorEntrada("n debe ser entero positivo y p estar entre 0 y 1.")
        return st.binom(int(a), b), ("DISTR.BINOM.N({x}; " + f"{int(a)}; {num(b)}" + "; {c})", "INV.BINOM(" + f"{int(a)}; {num(b)}" + "; {p})")
    if nombre == "poisson":
        if a is None or a <= 0: raise ErrorEntrada("La media λ debe ser mayor que cero.")
        return st.poisson(a), ("POISSON.DIST({x}; " + f"{num(a)}" + "; {c})", None)
    raise ErrorEntrada("Distribución no reconocida.")


def calcular(nombre, a, b, calculo, x=None, x2=None, prob=None):
    d, (fx, fi) = distribucion(nombre, a, b); disc = nombre in DISCRETAS
    exc = lambda xx, c: fx.format(x=num(xx), c=c) if fx else "—"
    if calculo == "inversa":
        if prob is None or not 0 < prob < 1: raise ErrorEntrada("La probabilidad debe estar entre 0 y 1 (sin incluirlos).")
        v = float(d.ppf(prob)); return v, (fi.format(p=num(prob)) if fi else "—"), (None, v)
    if x is None: raise ErrorEntrada("Escribe el valor de x.")
    if calculo == "acum": return float(d.cdf(x)), "=" + exc(x, "VERDADERO"), (None, x)
    if calculo == "mayor": return float(d.sf(x)), "=1-" + exc(x, "VERDADERO"), (x, None)
    if calculo == "puntual": return float(d.pmf(x) if disc else d.pdf(x)), "=" + exc(x, "FALSO"), (x, x)
    if x2 is None or x2 <= x: raise ErrorEntrada("Para «entre dos valores» indica b mayor que a.")
    return float(d.cdf(x2) - d.cdf(x)), f"={exc(x2, 'VERDADERO')}-{exc(x, 'VERDADERO')}", (x, x2)


@registrar
class Probabilidad(ModuloDialogo):
    ID, TITULO, HOJA_VACIA_OK = "PROBABILIDAD", "Distribuciones de probabilidad", True
    CAMPOS = [{"campo": "dist", "etiqueta": "Distribución", "tipo": "opcion", "opciones": DISTS, "defecto": "normal"},
              {"campo": "a", "etiqueta": "Parámetro 1 (media, GL, forma, ubicación, mínimo, n o λ)", "tipo": "numero", "defecto": "0"},
              {"campo": "b", "etiqueta": "Parámetro 2 (desviación, GL del denominador, escala, máximo o p)", "tipo": "numero", "defecto": "1"},
              {"campo": "calculo", "etiqueta": "Cálculo", "tipo": "opcion", "opciones": CALCULOS, "defecto": "acum"},
              {"campo": "x", "etiqueta": "x (o a, el límite inferior)", "tipo": "numero"},
              {"campo": "x2", "etiqueta": "b, el límite superior (solo «entre dos valores»)", "tipo": "numero"},
              {"campo": "prob", "etiqueta": "Probabilidad (solo inversa)", "tipo": "numero"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        nombre, calculo = p.get("dist") or "normal", p.get("calculo") or "acum"
        a, b = cls.numero(p, "a", "El parámetro 1"), cls.numero(p, "b", "El parámetro 2")
        x, x2, prob = cls.numero(p, "x", "x"), cls.numero(p, "x2", "b"), cls.numero(p, "prob", "La probabilidad")
        v, formula, (lo, hi) = calcular(nombre, a, b, calculo, x, x2, prob)
        d, _ = distribucion(nombre, a, b); disc = nombre in DISCRETAS
        etiqueta = dict(CALCULOS)[calculo]; nom = dict(DISTS)[nombre].split(" (")[0]
        texto = (f"x = {num(v, 6)}" if calculo == "inversa" else f"{etiqueta.split(' ', 1)[1] if calculo != 'puntual' else ('P(X = x)' if disc else 'f(x)')} = {num(v, 6)}"
                 + (f" ({100 * v:.4g}%)" if calculo != "inversa" and calculo != "puntual" or disc and calculo == "puntual" else ""))
        # gráfica de la distribución con el área marcada
        fig, ax = figura(6.0, 3.4)
        lo_q, hi_q = d.ppf(.0005), d.ppf(.9995)
        if disc:
            ks = np.arange(max(int(lo_q) - 1, 0), int(hi_q) + 2); pm = d.pmf(ks)
            sel = [((lo is None or k > lo) if calculo == "mayor" else (lo is None or k >= lo)) and (hi is None or k <= hi) for k in ks]
            if calculo == "entre": sel = [lo < k <= hi for k in ks]
            ax.bar(ks, pm, color=[NARANJA if s_ else CLARO for s_ in sel], edgecolor=TINTA, linewidth=.3)
        else:
            xs = np.linspace(lo_q, hi_q, 400); ys = d.pdf(xs)
            ax.plot(xs, ys, color=TINTA, lw=1.4)
            if calculo != "puntual":
                m = np.ones_like(xs, bool)
                if lo is not None: m &= xs > lo
                if hi is not None: m &= xs <= hi
                ax.fill_between(xs, 0, ys, where=m, color=NARANJA, alpha=.55)
            else: ax.axvline(x, color=NARANJA, lw=1.5)
        ax.set_title(f"{nom}: {texto}", fontsize=9); ax.set_ylabel("Probabilidad" if disc else "Densidad")
        svg, png = a_svg_png(fig)
        tabla = [["Distribución", dict(DISTS)[nombre]], ["Parámetros", f"{num(a)}" + (f", {num(b)}" if b is not None and nombre not in ("t", "chi2", "exponencial", "poisson") else "")],
                 ["Cálculo", etiqueta], ["Resultado", num(v, 8)], ["Equivalente en Excel (español)", formula]]
        if nombre == "normal" and calculo in ("acum", "mayor") and b:
            tabla.insert(3, ["Z = (x − media) / desviación", num((x - a) / b, 4)])
        notas = []
        if calculo == "mayor" and disc: notas.append("En distribuciones discretas, P(X > x) excluye a x; para P(X ≥ x) usa x − 1.")
        return resultado(cls.ID, f"{nom}: {etiqueta.split(' ')[0].lower()} {texto}", p, [
            b_texto(texto, "conclusion"), b_grafica(svg), b_tabla("Cálculo", ["Concepto", "Valor"], tabla),
            b_texto("Fórmulas y ejemplos: 25_BB_DISTRIBUCIONES (DIST-Z, DIST-EJ-Z, DIST-LOGNORMAL, DIST-WEIBULL, DIST-BINOMIAL, DIST-POISSON). Los nombres "
                    "de las funciones de Excel corresponden a Excel en español 2010 o posterior; el curso usa también DISTR.NORM.ESTAND para la normal estándar.")],
            notas, datos={"columnas": []}, png=png)
