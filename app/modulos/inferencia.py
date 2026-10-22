"""Inferencia estadística (etapa E7, E8, E10 y E11 del plan).
Respaldo de la base: ANOVA-QUE-ES y ANOVA-TIPOS (17_GB), DIST-IDENTIFICAR y DIST-TRANSFORMACION (25_BB), MUE-DISCRETA y
MUE-CONTINUA (15_GB). [GENERAL, no respaldado por la base]: las pruebas t, Z, de proporciones y de varianzas, Tukey,
la potencia, las pruebas no paramétricas y la chi cuadrada (la base solo las menciona); sus fórmulas son las estándar."""
import math
import numpy as np
from scipy import stats as st, optimize
from . import registrar, estadistica as E
from .analisis import _prob_normal
from .base import _f, espec_residuos
from .base import (ErrorEntrada, columna, filas_validas, valor, figura, a_svg_png, num, p_igual, p_texto, frase_p, resultado,
                   b_grafica, b_tabla, b_texto, NARANJA, TINTA, SUAVE, CLARO, PALETA)
from .dialogo import ModuloDialogo

ALFAS = [["0.10", "0.10"], ["0.05", "0.05"], ["0.01", "0.01"]]
ALTS = [["!=", "Distinta (dos colas)"], ["<", "Menor que"], [">", "Mayor que"]]
SIGNO = {"!=": "≠", "<": "<", ">": ">"}
GENERAL = "Fórmulas estándar de inferencia; la base del curso no las detalla (no respaldado por la base)."


def _nom(hoja, j): return hoja.columnas[j].nombre or f"C{j + 1}"


def _num_col(hoja, j, etiqueta):
    columna(hoja, j, etiqueta, "num")
    filas, fuera = filas_validas(hoja, [j])
    return np.array([valor(hoja, j, i) for i in filas], float), fuera


def _dos_muestras(hoja, p, etiqueta="los datos"):
    """Dos muestras desde dos columnas (y, y2) o desde una columna y una de grupo con 2 niveles."""
    yj, y2, g = p.get("y"), p.get("y2"), p.get("grupo")
    if g is not None:
        columna(hoja, yj, etiqueta, "num"); columna(hoja, g, "el grupo")
        filas, fuera = filas_validas(hoja, [yj, g])
        niveles = sorted({str(valor(hoja, g, i)) for i in filas}, key=str)
        if len(niveles) != 2: raise ErrorEntrada(f"La columna de grupo debe tener exactamente 2 niveles (tiene {len(niveles)}).")
        a = np.array([valor(hoja, yj, i) for i in filas if str(valor(hoja, g, i)) == niveles[0]], float)
        b = np.array([valor(hoja, yj, i) for i in filas if str(valor(hoja, g, i)) == niveles[1]], float)
        return a, b, niveles, fuera
    if y2 is None: raise ErrorEntrada("Elige la segunda muestra o una columna de grupo.")
    a, f1 = _num_col(hoja, yj, etiqueta); b, f2 = _num_col(hoja, y2, "la segunda muestra")
    return a, b, [_nom(hoja, yj), _nom(hoja, y2)], f1 + f2


def p_valor(estad, dist, alt):
    if alt == "<": return float(dist.cdf(estad))
    if alt == ">": return float(dist.sf(estad))
    return float(2 * min(dist.cdf(estad), dist.sf(estad)))


def intervalo(centro, ee, crit_dos, crit_una, alt):
    if alt == "<": return (-math.inf, centro + crit_una * ee)
    if alt == ">": return (centro - crit_una * ee, math.inf)
    return (centro - crit_dos * ee, centro + crit_dos * ee)


def _ic_txt(ic, d=4): return f"{'−∞' if ic[0] == -math.inf else num(ic[0], d)} a {'∞' if ic[1] == math.inf else num(ic[1], d)}"


def _resumen(nombres, muestras):
    return [[n_, len(x), num(np.mean(x), 4), num(np.std(x, ddof=1), 4) if len(x) > 1 else "—",
             num(np.std(x, ddof=1) / math.sqrt(len(x)), 4) if len(x) > 1 else "—"] for n_, x in zip(nombres, muestras)]


def _graf_muestras(muestras, nombres, h0=None, ic=None, titulo=""):
    fig, ax = figura(5.6, 3.2)
    for k, x in enumerate(muestras):
        jit = np.linspace(-0.08, 0.08, len(x)) if len(x) > 1 else [0]
        ax.scatter(np.full(len(x), k) + jit, x, s=12, color=NARANJA, alpha=.75, zorder=3)
        ax.plot([k - .22, k + .22], [np.mean(x)] * 2, color=TINTA, lw=2)
    if ic is not None and len(muestras) == 1:
        lo, hi = [v if math.isfinite(v) else (np.min(muestras[0]) if v < 0 else np.max(muestras[0])) for v in ic]
        ax.errorbar([0.35], [np.mean(muestras[0])], yerr=[[np.mean(muestras[0]) - lo], [hi - np.mean(muestras[0])]], fmt="o", color=TINTA, capsize=4)
    if h0 is not None: ax.axhline(h0, color="#b3261e", lw=1, ls="--"); ax.text(len(muestras) - .5, h0, " H0", color="#b3261e", va="bottom", fontsize=8)
    ax.set_xticks(range(len(muestras))); ax.set_xticklabels(nombres); ax.set_xlim(-.6, len(muestras) - .4); ax.set_title(titulo, fontsize=9)
    return a_svg_png(fig)


# ===================== E7 pruebas de hipótesis =====================
TIPOS_H = [["t1", "t de 1 muestra (media contra un valor)"], ["z1", "Z de 1 muestra (sigma conocida)"], ["t2", "t de 2 muestras (medias)"],
           ["pareada", "t pareada (antes y después)"], ["p1", "1 proporción"], ["p2", "2 proporciones"],
           ["v1", "1 varianza (desviación contra un valor)"], ["v2", "2 varianzas (F y Levene)"]]


@registrar
class Hipotesis(ModuloDialogo):
    ID, TITULO = "HIPOTESIS", "Pruebas de hipótesis"
    INDEPENDIENTES = True        # A1: las muestras pueden tener distinto tamaño; las celdas vacías al final no son faltantes
    CAMPOS = [{"campo": "tipo", "etiqueta": "Prueba", "tipo": "opcion", "opciones": TIPOS_H, "defecto": "t1"},
              {"campo": "y", "etiqueta": "Datos (muestra 1)", "tipo": "col", "filtro": "num", "rol": ["respuesta"], "opcional": True},
              {"campo": "y2", "etiqueta": "Muestra 2 o «después» (2 muestras y pareada)", "tipo": "col", "filtro": "num", "opcional": True},
              {"campo": "grupo", "etiqueta": "o una columna de grupo con 2 niveles (en lugar de la muestra 2)", "tipo": "col", "opcional": True},
              {"campo": "h0", "etiqueta": "Valor de la hipótesis nula (media, proporción, desviación o diferencia)", "tipo": "numero"},
              {"campo": "sigma", "etiqueta": "Sigma conocida (solo Z)", "tipo": "numero"},
              {"campo": "x1", "etiqueta": "Proporciones: eventos de la muestra 1", "tipo": "numero"},
              {"campo": "n1", "etiqueta": "Proporciones: tamaño de la muestra 1", "tipo": "numero"},
              {"campo": "x2", "etiqueta": "Proporciones: eventos de la muestra 2", "tipo": "numero"},
              {"campo": "n2", "etiqueta": "Proporciones: tamaño de la muestra 2", "tipo": "numero"},
              {"campo": "iguales", "etiqueta": "t de 2 muestras: suponer varianzas iguales", "tipo": "bool", "defecto": False},
              {"campo": "combinada", "etiqueta": "2 proporciones: usar la estimación combinada de p en la prueba", "tipo": "bool", "defecto": False},
              {"campo": "alt", "etiqueta": "Hipótesis alterna", "tipo": "opcion", "opciones": ALTS, "defecto": "!="},
              {"campo": "alfa", "etiqueta": "Nivel de significancia (alfa)", "tipo": "opcion", "opciones": ALFAS, "defecto": "0.05"}]
    HOJA_VACIA_OK = True

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        tipo, alt, alfa = p.get("tipo") or "t1", p.get("alt") or "!=", float(p.get("alfa") or .05)
        conf = 1 - alfa; z2, z1 = st.norm.ppf(1 - alfa / 2), st.norm.ppf(1 - alfa)
        h0 = cls.numero(p, "h0", "El valor de H0")
        graf, res, cab, filas_t, tit, extra, supuestos, avisos = None, [], [], [], "", [], [], []
        if tipo in ("t1", "z1", "v1"):
            if p.get("y") is None: raise ErrorEntrada("Elige la columna de datos.")
            x, fuera = _num_col(hoja, p["y"], "los datos"); n = len(x)
            if n < 2: raise ErrorEntrada("Se necesitan al menos 2 datos.")
            if fuera: avisos.append(f"{fuera} celdas vacías o no numéricas quedaron fuera.")
            m, s = float(np.mean(x)), float(np.std(x, ddof=1)); nom = _nom(hoja, p["y"])
            res = _resumen([nom], [x])
            if tipo == "v1":
                if h0 is None or h0 <= 0: raise ErrorEntrada("Indica la desviación estándar de la hipótesis nula (mayor que cero).")
                chi = (n - 1) * s ** 2 / h0 ** 2; d = st.chi2(n - 1); pv = p_valor(chi, d, alt)
                lo = math.sqrt((n - 1) * s ** 2 / d.ppf(1 - alfa / 2)); hi = math.sqrt((n - 1) * s ** 2 / d.ppf(alfa / 2))
                ic = (lo, hi) if alt == "!=" else ((0, math.sqrt((n - 1) * s ** 2 / d.ppf(alfa))) if alt == "<" else (math.sqrt((n - 1) * s ** 2 / d.ppf(1 - alfa)), math.inf))
                tit = f"Prueba de 1 varianza: σ de {nom}"; cab = ["H0", "Ha", "Chi cuadrada", "GL", "Valor p", f"IC {100 * conf:.0f}% de σ"]
                filas_t = [[f"σ = {num(h0)}", f"σ {SIGNO[alt]} {num(h0)}", num(chi, 4), n - 1, p_texto(pv), _ic_txt(ic)]]
                h0t, hat = f"la desviación estándar es {num(h0)}", f"la desviación estándar es {'distinta de' if alt == '!=' else 'menor que' if alt == '<' else 'mayor que'} {num(h0)}"
                graf = _graf_muestras([x], [nom], titulo=f"Valores individuales de {nom}")
            else:
                if h0 is None: raise ErrorEntrada("Indica la media de la hipótesis nula.")
                if tipo == "z1":
                    sg = cls.numero(p, "sigma", "La sigma conocida", opcional=False, minimo=0); ee = sg / math.sqrt(n)
                    est = (m - h0) / ee; pv = p_valor(est, st.norm, alt); ic = intervalo(m, ee, z2, z1, alt); gl = "—"; nomb = "Z"
                else:
                    ee = s / math.sqrt(n); est = (m - h0) / ee; d = st.t(n - 1); pv = p_valor(est, d, alt)
                    ic = intervalo(m, ee, d.ppf(1 - alfa / 2), d.ppf(1 - alfa), alt); gl = n - 1; nomb = "t"
                tit = f"Prueba {nomb} de 1 muestra: media de {nom}"
                cab = ["H0", "Ha", nomb, "GL", "Valor p", f"IC {100 * conf:.0f}% de la media"]
                filas_t = [[f"μ = {num(h0)}", f"μ {SIGNO[alt]} {num(h0)}", num(est, 4), gl, p_texto(pv), _ic_txt(ic)]]
                h0t, hat = f"la media es {num(h0)}", f"la media es {'distinta de' if alt == '!=' else 'menor que' if alt == '<' else 'mayor que'} {num(h0)}"
                graf = _graf_muestras([x], [nom], h0=h0, ic=ic, titulo=f"Valores individuales de {nom} con IC de la media")
            ad = E.anderson_darling(list(x)) if n >= 8 else None
            supuestos = [("Datos normales (o n grande)", "Anderson-Darling", f"{p_igual(ad['p'], .005)}" if ad else "pocos datos; con n < 8 no se evalúa"),
                         ("Muestra aleatoria e independiente", "Procedimiento de muestreo", "Revísalo en el plan de muestreo")]
        elif tipo in ("t2", "v2"):
            a, b, nombres, fuera = _dos_muestras(hoja, p)
            if min(len(a), len(b)) < 2: raise ErrorEntrada("Cada muestra necesita al menos 2 datos.")
            res = _resumen(nombres, [a, b]); s1, s2 = np.std(a, ddof=1), np.std(b, ddof=1); n1, n2 = len(a), len(b)
            if tipo == "t2":
                d0 = h0 or 0.0; dif = float(np.mean(a) - np.mean(b))
                if p.get("iguales"):
                    sp = math.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2)); ee = sp * math.sqrt(1 / n1 + 1 / n2); gl = n1 + n2 - 2
                else:
                    v1, v2 = s1 ** 2 / n1, s2 ** 2 / n2; ee = math.sqrt(v1 + v2)
                    gl = math.floor((v1 + v2) ** 2 / (v1 ** 2 / (n1 - 1) + v2 ** 2 / (n2 - 1)))   # Welch-Satterthwaite truncado al entero, como Minitab
                d = st.t(gl); est = (dif - d0) / ee; pv = p_valor(est, d, alt); ic = intervalo(dif, ee, d.ppf(1 - alfa / 2), d.ppf(1 - alfa), alt)
                tit = f"Prueba t de 2 muestras: {nombres[0]} contra {nombres[1]}"
                cab = ["H0", "Ha", "Diferencia", "t", "GL", "Valor p", f"IC {100 * conf:.0f}% de la diferencia"]
                filas_t = [[f"μ1 - μ2 = {num(d0)}", f"μ1 - μ2 {SIGNO[alt]} {num(d0)}", num(dif, 4), num(est, 4), gl, p_texto(pv), _ic_txt(ic)]]
                h0t, hat = "las medias son iguales" if not d0 else f"la diferencia de medias es {num(d0)}", "las medias son distintas" if alt == "!=" else f"la media 1 es {'menor' if alt == '<' else 'mayor'}"
                extra.append("Varianzas " + ("supuestas iguales (desviación combinada)." if p.get("iguales") else "no supuestas iguales (Welch), como en Minitab por omisión; los grados de libertad se truncan al entero, como Minitab."))
            else:
                f = s1 ** 2 / s2 ** 2; d = st.f(n1 - 1, n2 - 1); pv = p_valor(f, d, alt)
                lev = st.levene(a, b, center="median")
                tit = f"Prueba de 2 varianzas: {nombres[0]} contra {nombres[1]}"
                cab = ["Método", "Estadístico", "GL", "Valor p"]
                filas_t = [["F (datos normales)", num(f, 4), f"{n1 - 1}, {n2 - 1}", p_texto(pv)], ["Levene (cualquier distribución)", num(float(lev.statistic), 4), f"1, {n1 + n2 - 2}", p_texto(float(lev.pvalue))]]
                h0t, hat = "las varianzas son iguales", "las varianzas son distintas"
                extra.append("Usa F si los datos son normales; si no, usa Levene (centrado en la mediana).")
            graf = _graf_muestras([a, b], nombres, titulo="Valores individuales por muestra")
            supuestos = [("Datos normales en cada muestra (o n grande)", "Anderson-Darling por muestra",
                          ", ".join(f"{n_}: {p_igual(E.anderson_darling(list(x))['p'], .005)}" if len(x) >= 8 else f"{n_}: pocos datos" for n_, x in zip(nombres, (a, b)))),
                         ("Muestras independientes", "Diseño del estudio", "Si son las mismas unidades medidas dos veces, usa la t pareada")]
            if fuera: avisos.append(f"{fuera} celdas vacías o no numéricas quedaron fuera.")
        elif tipo == "pareada":
            yj, y2 = p.get("y"), p.get("y2")
            if yj is None or y2 is None: raise ErrorEntrada("Elige las columnas «antes» (muestra 1) y «después» (muestra 2).")
            columna(hoja, yj, "la muestra 1", "num"); columna(hoja, y2, "la muestra 2", "num")
            filas, fuera = filas_validas(hoja, [yj, y2]); a = np.array([valor(hoja, yj, i) for i in filas]); b = np.array([valor(hoja, y2, i) for i in filas])
            if len(a) < 2: raise ErrorEntrada("Se necesitan al menos 2 pares completos.")
            dd = a - b; d0 = h0 or 0.0; n = len(dd); ee = np.std(dd, ddof=1) / math.sqrt(n); d = st.t(n - 1)
            est = (np.mean(dd) - d0) / ee; pv = p_valor(est, d, alt); ic = intervalo(float(np.mean(dd)), ee, d.ppf(1 - alfa / 2), d.ppf(1 - alfa), alt)
            nombres = [_nom(hoja, yj), _nom(hoja, y2), "Diferencia"]; res = _resumen(nombres, [a, b, dd])
            tit = f"Prueba t pareada: {nombres[0]} - {nombres[1]}"
            cab = ["H0", "Ha", "t", "GL", "Valor p", f"IC {100 * conf:.0f}% de la diferencia media"]
            filas_t = [[f"μd = {num(d0)}", f"μd {SIGNO[alt]} {num(d0)}", num(est, 4), n - 1, p_texto(pv), _ic_txt(ic)]]
            h0t, hat = "la diferencia media es cero" if not d0 else f"la diferencia media es {num(d0)}", "hay diferencia entre antes y después"
            graf = _graf_muestras([dd], ["Diferencias"], h0=d0, ic=ic, titulo="Diferencias con IC de la media")
            supuestos = [("Diferencias normales (o n grande)", "Anderson-Darling de las diferencias", p_igual(E.anderson_darling(list(dd))["p"]) if n >= 8 else "pocos datos")]
            if fuera: avisos.append(f"{fuera} filas incompletas quedaron fuera.")
        else:
            x1 = cls.numero(p, "x1", "Los eventos de la muestra 1", opcional=False, minimo=-1); n1 = cls.numero(p, "n1", "El tamaño de la muestra 1", opcional=False, minimo=0)
            if x1 > n1: raise ErrorEntrada("Los eventos no pueden ser más que el tamaño de la muestra.")
            x1, n1 = int(x1), int(n1); p1 = x1 / n1
            if tipo == "p1":
                if h0 is None or not 0 < h0 < 1: raise ErrorEntrada("Indica la proporción de H0 entre 0 y 1.")
                bt = st.binomtest(x1, n1, h0, alternative={"!=": "two-sided", "<": "less", ">": "greater"}[alt])
                ci = bt.proportion_ci(conf, method="exact")
                ic = (ci.low, ci.high) if alt == "!=" else ((0, st.binomtest(x1, n1, h0, alternative="less").proportion_ci(1 - alfa).high) if alt == "<" else (st.binomtest(x1, n1, h0, alternative="greater").proportion_ci(1 - alfa).low, 1))
                zc = (p1 - h0) / math.sqrt(h0 * (1 - h0) / n1)
                tit = "Prueba de 1 proporción"; cab = ["H0", "Ha", "Eventos / N", "Proporción", "Valor p (exacto; dos colas por mínima verosimilitud)", "Z (aprox. normal)", f"IC {100 * conf:.0f}% exacto"]
                filas_t = [[f"p = {num(h0)}", f"p {SIGNO[alt]} {num(h0)}", f"{x1} / {n1}", num(p1, 4), p_texto(bt.pvalue), num(zc, 3), _ic_txt(ic, 6)]]; pv = bt.pvalue
                h0t, hat = f"la proporción es {num(h0)}", f"la proporción es {'distinta de' if alt == '!=' else 'menor que' if alt == '<' else 'mayor que'} {num(h0)}"
            else:
                x2 = cls.numero(p, "x2", "Los eventos de la muestra 2", opcional=False, minimo=-1); n2 = cls.numero(p, "n2", "El tamaño de la muestra 2", opcional=False, minimo=0)
                if x2 > n2: raise ErrorEntrada("Los eventos no pueden ser más que el tamaño de la muestra.")
                x2, n2 = int(x2), int(n2); p2 = x2 / n2; pc = (x1 + x2) / (n1 + n2)
                ee = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2); ic = intervalo(p1 - p2, ee, z2, z1, alt)
                if p.get("combinada"):
                    zc = (p1 - p2) / math.sqrt(pc * (1 - pc) * (1 / n1 + 1 / n2)) if 0 < pc < 1 else 0.0; metodo_z = "Z combinada"
                else:
                    zc = (p1 - p2) / ee if ee > 0 else 0.0; metodo_z = "Z con estimación separada"   # Minitab por omisión
                pv = p_valor(zc, st.norm, alt)
                fis = st.fisher_exact([[x1, n1 - x1], [x2, n2 - x2]], alternative={"!=": "two-sided", "<": "less", ">": "greater"}[alt]).pvalue
                tit = "Prueba de 2 proporciones"; cab = ["Muestra", "Eventos / N", "Proporción"]
                res = [["1", f"{x1} / {n1}", num(p1, 4)], ["2", f"{x2} / {n2}", num(p2, 4)]]
                filas_t = [["H0: p1 - p2 = 0", f"Ha: p1 - p2 {SIGNO[alt]} 0", f"Z = {num(zc, 4)}", f"Valor p {p_texto(pv)}", f"Fisher exacta {p_texto(fis)}", f"IC {100 * conf:.0f}%: {_ic_txt(ic)}"]]
                cab2 = ["H0", "Ha", "Estadístico", f"Valor p ({metodo_z})", "Valor p (Fisher)", "IC de la diferencia"]
                h0t, hat = "las proporciones son iguales", "las proporciones son distintas" if alt == "!=" else f"la proporción 1 es {'menor' if alt == '<' else 'mayor'}"
                if min(x1, n1 - x1, x2, n2 - x2) < 5: avisos.append("Hay menos de 5 eventos o no eventos en alguna muestra: confía en la prueba exacta de Fisher.")
                return resultado(cls.ID, tit, p, [b_texto(frase_p(pv, alfa, h0t, hat), "conclusion"), b_tabla("Muestras", cab, res),
                                                  b_tabla("Prueba", cab2, [["p1 - p2 = 0", f"p1 - p2 {SIGNO[alt]} 0", f"Z = {num(zc, 4)}", p_texto(pv), p_texto(fis), _ic_txt(ic)]]), b_texto(GENERAL)],
                                 avisos, datos={"columnas": []}, interpretacion=["Una diferencia estadísticamente significativa no siempre importa en la práctica: compárala con lo que necesita el proceso."])
        bloques = [b_texto(frase_p(pv, alfa, h0t, hat), "conclusion")]
        if graf: bloques.append(b_grafica(graf[0]))
        if res and tipo not in ("p1",): bloques.append(b_tabla("Estadísticos descriptivos", ["Muestra", "N", "Media", "Desv. est.", "EE de la media"], res))
        bloques.append(b_tabla("Prueba", cab, filas_t))
        bloques += [b_texto(t) for t in extra] + [b_texto(GENERAL)]
        cols = [p.get(k) for k in ("y", "y2", "grupo") if p.get(k) is not None]
        return resultado(cls.ID, tit, p, bloques, avisos, datos={"columnas": cols}, png=graf[1] if graf else None, supuestos=supuestos,
                         interpretacion=["«No se rechaza H0» no prueba que H0 sea cierta: solo que los datos no alcanzan para rechazarla.",
                                         "Una diferencia significativa no siempre importa en la práctica: compárala con lo que necesita el proceso."])


# ===================== E8 ANOVA de dos factores y Tukey =====================
def _codif(niveles, vals):
    """Codificación de efectos (suma cero): k-1 columnas."""
    k = len(niveles); M = np.zeros((len(vals), k - 1))
    for r, v in enumerate(vals):
        i = niveles.index(v)
        if i < k - 1: M[r, i] = 1
        else: M[r, :] = -1
    return M


def anova2(y, a, b, interaccion=True):
    y = np.asarray(y, float); la, lb = sorted(set(a), key=str), sorted(set(b), key=str)
    A, B = _codif(la, a), _codif(lb, b); n = len(y)
    grupos = {"A": A, "B": B}
    if interaccion: grupos["AB"] = np.column_stack([A[:, i] * B[:, j] for i in range(A.shape[1]) for j in range(B.shape[1])])
    X = np.column_stack([np.ones(n)] + list(grupos.values()))
    def sse(M):
        bb = np.linalg.lstsq(M, y, rcond=None)[0]; e = y - M @ bb; return float(e @ e), bb
    sce, beta = sse(X); rank = np.linalg.matrix_rank(X); gle = n - rank
    if gle <= 0: raise ValueError("No quedan grados de libertad para el error: se necesitan réplicas (o quita la interacción).")
    mce = sce / gle; filas = []; idx = 1
    for k, M in grupos.items():
        cols = list(range(idx, idx + M.shape[1])); idx += M.shape[1]
        ss = sse(np.delete(X, cols, axis=1))[0] - sce; gl = M.shape[1]
        f = (ss / gl) / mce if mce > 0 else math.inf
        filas.append({"fuente": k, "gl": gl, "ss": ss, "ms": ss / gl, "f": f, "p": float(st.f.sf(f, gl, gle)), "f_tablas": float(st.f.ppf(.95, gl, gle))})
    sct = float(((y - y.mean()) ** 2).sum()); aj = X @ beta
    return {"filas": filas, "sce": sce, "gle": gle, "mce": mce, "sct": sct, "n": n, "la": la, "lb": lb, "r2": 1 - sce / sct if sct else 0,
            "r2_aj": 1 - (sce / gle) / (sct / (n - 1)) if sct else 0, "s": math.sqrt(mce), "residuos": y - aj, "ajustados": aj}


@registrar
class Anova2(ModuloDialogo):
    ID, TITULO = "ANOVA2", "ANOVA de dos factores"
    CAMPOS = [{"campo": "y", "etiqueta": "Respuesta", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "a", "etiqueta": "Factor A", "tipo": "col", "rol": ["factor"]}, {"campo": "b", "etiqueta": "Factor B", "tipo": "col"},
              {"campo": "interaccion", "etiqueta": "Incluir la interacción A×B", "tipo": "bool", "defecto": True},
              {"campo": "alfa", "etiqueta": "Nivel de significancia (alfa)", "tipo": "opcion", "opciones": ALFAS, "defecto": "0.05"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        yj, aj, bj = p.get("y"), p.get("a"), p.get("b"); alfa = float(p.get("alfa") or .05)
        columna(hoja, yj, "la respuesta", "num"); columna(hoja, aj, "el factor A"); columna(hoja, bj, "el factor B")
        if len({yj, aj, bj}) < 3: raise ErrorEntrada("Respuesta, factor A y factor B deben ser columnas distintas.")
        filas, fuera = filas_validas(hoja, [yj, aj, bj])
        y = [valor(hoja, yj, i) for i in filas]; a = [str(valor(hoja, aj, i)) for i in filas]; b = [str(valor(hoja, bj, i)) for i in filas]
        if len(set(a)) < 2 or len(set(b)) < 2: raise ErrorEntrada("Cada factor necesita al menos 2 niveles.")
        celdas = {}
        for yi, ai, bi in zip(y, a, b): celdas.setdefault((ai, bi), []).append(yi)
        inter = bool(p.get("interaccion", True)); avisos = [f"{fuera} filas incompletas quedaron fuera."] if fuera else []
        faltan = [(x, z) for x in set(a) for z in set(b) if (x, z) not in celdas]
        if faltan: raise ErrorEntrada(f"Faltan combinaciones de niveles (por ejemplo {faltan[0][0]} con {faltan[0][1]}): el diseño debe ser cruzado.")
        if inter and max(len(v) for v in celdas.values()) < 2:
            inter = False; avisos.append("Sin réplicas no se puede estimar la interacción: se ajustó el modelo sin A×B.")
        if len({len(v) for v in celdas.values()}) > 1: avisos.append("Diseño desbalanceado: se usan sumas de cuadrados ajustadas (cada término después de los demás).")
        try:
            r = anova2(y, a, b, inter)
        except ValueError as e:
            raise ErrorEntrada(str(e))
        na, nb, ny = _nom(hoja, aj), _nom(hoja, bj), _nom(hoja, yj)
        nombre = {"A": na, "B": nb, "AB": f"{na}×{nb}"}
        tabla = [[nombre[f["fuente"]], f["gl"], num(f["ss"], 5), num(f["ms"], 5), num(f["f"], 3), num(f["f_tablas"], 3) if alfa == .05 else num(float(st.f.ppf(1 - alfa, f["gl"], r["gle"])), 3), p_texto(f["p"])] for f in r["filas"]]
        tabla += [["Error", r["gle"], num(r["sce"], 5), num(r["mce"], 5), "", "", ""], ["Total", r["n"] - 1, num(r["sct"], 5), "", "", "", ""]]
        # gráficas: efectos principales e interacción
        fig, axs = figura(9.6, 3.2, ncols=3)
        for ax, lv, vals, nm in ((axs[0], r["la"], a, na), (axs[1], r["lb"], b, nb)):
            ms = [np.mean([yi for yi, v in zip(y, vals) if v == l]) for l in lv]
            ax.plot(range(len(lv)), ms, marker="o", color=NARANJA); ax.axhline(np.mean(y), color=SUAVE, lw=.8, ls="--")
            ax.set_xticks(range(len(lv))); ax.set_xticklabels(lv, fontsize=7); ax.set_title(f"Efecto principal de {nm}", fontsize=8)
        for k, lb_ in enumerate(r["lb"]):
            axs[2].plot(range(len(r["la"])), [np.mean(celdas[(la_, lb_)]) for la_ in r["la"]], marker="o", color=PALETA[k % len(PALETA)], label=str(lb_))
        axs[2].set_xticks(range(len(r["la"]))); axs[2].set_xticklabels(r["la"], fontsize=7); axs[2].legend(fontsize=6, title=nb, title_fontsize=6, frameon=False)
        axs[2].set_title("Interacción (líneas no paralelas = interacción)", fontsize=8)
        svg, png = a_svg_png(fig)
        _ef2 = [{"factor": nm_, "niveles": [str(l) for l in lv], "medias": [_f(np.mean([yi for yi, v in zip(y, vals) if v == l])) for l in lv]} for lv, vals, nm_ in ((r["la"], a, na), (r["lb"], b, nb))]
        _in2 = [{"par": f"{na} × {nb}", "niveles": [str(l) for l in r["la"]], "series": [{"nivel": str(lb_), "medias": [_f(np.mean(celdas[(la_, lb_)])) for la_ in r["la"]]} for lb_ in r["lb"]]}]
        fig, ax4 = figura(9.6, 5.4, nrows=2, ncols=2)
        _prob_normal(ax4[0][0], list(r["residuos"]), "Probabilidad normal de residuos")
        ax4[0][1].scatter(r["ajustados"], r["residuos"], s=12, color=NARANJA); ax4[0][1].axhline(0, color=TINTA, lw=1); ax4[0][1].set_title("Residuos contra ajustados")
        ax4[1][0].hist(r["residuos"], bins=min(10, max(5, int(math.sqrt(r["n"])))), color=CLARO, edgecolor=NARANJA); ax4[1][0].set_title("Histograma de residuos")
        ax4[1][1].plot(range(1, r["n"] + 1), r["residuos"], color=NARANJA, marker="o", ms=3, lw=.8); ax4[1][1].axhline(0, color=TINTA, lw=1); ax4[1][1].set_title("Residuos contra orden")
        svg_r, _ = a_svg_png(fig)
        sig = {f["fuente"]: f["p"] < alfa for f in r["filas"]}
        interp = []
        if sig.get("AB"): interp.append(f"La interacción {nombre['AB']} es significativa: el efecto de un factor depende del nivel del otro; interpreta los efectos principales con cuidado (17_GB ANOVA-TIPOS, ejemplo de lámparas).")
        for k in ("A", "B"): interp.append(f"{nombre[k]}: " + ("significativo" if sig[k] else "no significativo") + f" ({p_igual(next(f['p'] for f in r['filas'] if f['fuente'] == k))}).")
        interp.append("Para saber qué niveles difieren, usa Estadística > Comparaciones de Tukey con cada factor.")
        ad = E.anderson_darling(list(r["residuos"])) if r["n"] >= 8 else None
        return resultado(cls.ID, f"ANOVA de dos factores: {ny} contra {na} y {nb}", p, [
            b_grafica(svg, {"g": "interaccion", "titulo": f"Interacción {na} × {nb} (y efectos principales)", "pares": _in2}) if len(r["la"]) > 1 else b_grafica(svg),
            b_tabla("Análisis de varianza", ["Fuente", "GL", "SC", "CM", "F", f"F de tablas ({alfa:g})", "Valor p"], tabla),
            b_tabla("Resumen del modelo", ["S", "R²", "R² ajustado"], [[num(r["s"], 5), f"{100 * r['r2']:.2f}%", f"{100 * r['r2_aj']:.2f}%"]]),
            b_grafica(svg_r, espec_residuos(list(r["residuos"]), list(r["ajustados"]), f"Residuos de {ny}")), b_texto("Regla de decisión de 17_GB ANOVA-QUE-ES: si F calculada < F de tablas (valor p > alfa) no se rechaza H0. Tipos de ANOVA: 17_GB ANOVA-TIPOS. "
                                       "No respaldado por la base: la codificación de efectos y las sumas de cuadrados ajustadas en diseños desbalanceados.")],
            avisos, datos={"columnas": [yj, aj, bj]}, png=png, interpretacion=interp,
            supuestos=[("Residuos normales", "Anderson-Darling", p_igual(ad["p"], .005) if ad else "pocos datos"),
                       ("Varianza constante", "Residuos contra ajustados", "Revisa que no haya forma de embudo"),
                       ("Independencia", "Residuos contra orden", "Corre los experimentos en orden aleatorio")])


def tukey(grupos, alfa=.05):
    """grupos: {nombre: datos}. Comparaciones por pares de Tukey (Tukey-Kramer si los tamaños difieren)."""
    nombres = list(grupos); k = len(nombres); N = sum(len(v) for v in grupos.values())
    medias = {g: float(np.mean(v)) for g, v in grupos.items()}
    mce = sum(((np.asarray(v) - np.mean(v)) ** 2).sum() for v in grupos.values()) / (N - k); gl = N - k
    q = float(st.studentized_range.ppf(1 - alfa, k, gl)); pares = []
    for i in range(k):
        for j in range(i + 1, k):
            gi, gj = nombres[i], nombres[j]; d = medias[gj] - medias[gi]
            ee = math.sqrt(mce / 2 * (1 / len(grupos[gi]) + 1 / len(grupos[gj])))
            pares.append({"par": (gj, gi), "dif": d, "ee": ee, "ic": (d - q * ee, d + q * ee), "t": d / ee,
                          "p": float(st.studentized_range.sf(abs(d) / ee, k, gl))})
    orden = sorted(nombres, key=lambda g: -medias[g]); dif = {frozenset(pp["par"]): pp["p"] < alfa for pp in pares}
    letras, grupos_l = {g: "" for g in nombres}, []
    for i in range(k):
        s = [orden[i]]
        for j in range(i + 1, k):
            if all(not dif[frozenset((orden[j], x))] for x in s): s.append(orden[j])
            else: break
        if not any(set(s) <= set(g) for g in grupos_l): grupos_l.append(s)
    for n_, g in enumerate(grupos_l):
        for x in g: letras[x] += chr(65 + n_)
    return {"medias": medias, "mce": mce, "gl": gl, "q": q, "pares": pares, "letras": letras, "orden": orden}


@registrar
class Tukey(ModuloDialogo):
    ID, TITULO = "TUKEY", "Comparaciones de Tukey"
    CAMPOS = [{"campo": "y", "etiqueta": "Respuesta", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "factor", "etiqueta": "Factor (niveles a comparar)", "tipo": "col", "rol": ["factor"]},
              {"campo": "alfa", "etiqueta": "Nivel de significancia de la familia", "tipo": "opcion", "opciones": ALFAS, "defecto": "0.05"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        yj, fj = p.get("y"), p.get("factor"); alfa = float(p.get("alfa") or .05)
        columna(hoja, yj, "la respuesta", "num"); columna(hoja, fj, "el factor")
        filas, fuera = filas_validas(hoja, [yj, fj]); g = {}
        for i in filas: g.setdefault(str(valor(hoja, fj, i)), []).append(valor(hoja, yj, i))
        if len(g) < 3: raise ErrorEntrada("Tukey compara 3 o más niveles; con 2 usa la prueba t de 2 muestras.")
        if any(len(v) < 2 for v in g.values()): raise ErrorEntrada("Cada nivel necesita al menos 2 datos.")
        t = tukey(dict(sorted(g.items(), key=lambda kv: str(kv[0]))), alfa)
        ag = [[x, len(g[x]), num(t["medias"][x], 4), t["letras"][x]] for x in t["orden"]]
        pr = [[f"{a_} - {b_}", num(pp["dif"], 4), num(pp["ee"], 4), f"{num(pp['ic'][0], 4)} a {num(pp['ic'][1], 4)}", num(pp["t"], 3), p_texto(pp["p"]),
               "sí" if pp["p"] < alfa else "no"] for pp in t["pares"] for a_, b_ in [pp["par"]]]
        fig, ax = figura(6.0, max(2.4, .42 * len(t["pares"]) + 1))
        for r_, pp in enumerate(t["pares"]):
            col = NARANJA if pp["p"] < alfa else SUAVE
            ax.plot(pp["ic"], [r_, r_], color=col, lw=2); ax.plot([pp["dif"]], [r_], "o", color=col)
        ax.axvline(0, color=TINTA, lw=1, ls="--"); ax.set_yticks(range(len(t["pares"]))); ax.set_yticklabels([f"{a} - {b}" for a, b in (pp["par"] for pp in t["pares"])], fontsize=7)
        ax.set_title(f"IC simultáneos de {100 * (1 - alfa):.0f}% (los que no cruzan el cero difieren)", fontsize=8)
        svg, png = a_svg_png(fig)
        return resultado(cls.ID, f"Tukey: {_nom(hoja, yj)} por {_nom(hoja, fj)}", p, [
            b_tabla("Agrupación (niveles que no comparten letra son distintos)", ["Nivel", "N", "Media", "Grupo"], ag),
            b_grafica(svg, {"g": "tukey", "titulo": f"IC simultáneos de {100 * (1 - alfa):.0f}% (Tukey)", "xl": "Diferencia de medias",
                            "pares": [{"par": f"{pp['par'][0]} - {pp['par'][1]}", "dif": _f(pp["dif"]), "lo": _f(pp["ic"][0]), "hi": _f(pp["ic"][1]), "sig": bool(pp["p"] < alfa)} for pp in t["pares"]]}),
            b_tabla("Diferencias por pares", ["Diferencia", "Diferencia de medias", "EE", f"IC simultáneo {100 * (1 - alfa):.0f}%", "t", "Valor p ajustado", "Distinta"], pr),
            b_texto(f"Método de Tukey (Tukey-Kramer con tamaños distintos), CM del error = {num(t['mce'], 5)} con {t['gl']} GL, q crítico = {num(t['q'], 4)}. " + GENERAL)],
            [f"{fuera} filas incompletas quedaron fuera."] if fuera else [], datos={"columnas": [yj, fj]}, png=png,
            interpretacion=["Las comparaciones controlan el error de toda la familia de pares, no de cada par por separado."])


# ===================== E10 identificación de distribución y Box-Cox =====================
def ad_estadistico(x, cdf):
    x = np.sort(np.asarray(x, float)); n = len(x); F = np.clip(cdf(x), 1e-12, 1 - 1e-12); i = np.arange(1, n + 1)
    return float(-n - np.sum((2 * i - 1) * (np.log(F) + np.log(1 - F[::-1]))) / n)


def _ajustar(nombre, x):
    if nombre == "Normal": m, s = np.mean(x), np.std(x, ddof=1); return st.norm(m, s), {"Media": m, "Desv. est.": s}
    if nombre == "Lognormal": l = np.log(x); m, s = np.mean(l), np.std(l, ddof=1); return st.lognorm(s, scale=math.exp(m)), {"Ubicación": m, "Escala": s}
    if nombre == "Exponencial": m = np.mean(x); return st.expon(scale=m), {"Escala (media)": m}
    if nombre == "Weibull": c, _, sc = st.weibull_min.fit(x, floc=0); return st.weibull_min(c, scale=sc), {"Forma": c, "Escala": sc}
    if nombre == "Gamma": a_, _, sc = st.gamma.fit(x, floc=0); return st.gamma(a_, scale=sc), {"Forma": a_, "Escala": sc}
    raise ValueError(nombre)


def identificar(x, B=300, semilla=1):
    """AD y valor p de 5 distribuciones. Normal: fórmula de la base actual; lognormal: normalidad de ln(x);
    exponencial, Weibull y gamma: valor p por simulación paramétrica (B réplicas, semilla fija) [GENERAL]."""
    x = np.asarray(x, float); pos = bool(np.all(x > 0)); out = []; rng = np.random.default_rng(semilla)
    for nm in ("Normal", "Lognormal", "Exponencial", "Weibull", "Gamma"):
        if nm != "Normal" and not pos: out.append({"nombre": nm, "error": "requiere datos mayores que cero"}); continue
        try:
            d, par = _ajustar(nm, x); a2 = ad_estadistico(x, d.cdf)
            if nm == "Normal": pv = E.anderson_darling(list(x))["p"]
            elif nm == "Lognormal": pv = E.anderson_darling(list(np.log(x)))["p"]
            else:
                sims = 0
                for _ in range(B):
                    xs = d.rvs(size=len(x), random_state=rng)
                    try: ds, _ = _ajustar(nm, xs); sims += ad_estadistico(xs, ds.cdf) >= a2
                    except Exception: pass
                pv = (sims + 1) / (B + 1)
            out.append({"nombre": nm, "dist": d, "par": par, "a2": a2, "p": float(pv)})
        except Exception as e:
            out.append({"nombre": nm, "error": f"no se pudo ajustar ({e.__class__.__name__})"})
    return out


@registrar
class DistId(ModuloDialogo):
    ID, TITULO = "DIST-ID", "Identificación de distribución"
    CAMPOS = [{"campo": "y", "etiqueta": "Datos", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "x0", "etiqueta": "Probabilidad de superar este valor (opcional)", "tipo": "numero"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        x, fuera = _num_col(hoja, p.get("y"), "los datos")
        if len(x) < 8: raise ErrorEntrada("Se necesitan al menos 8 datos para comparar distribuciones.")
        x0 = cls.numero(p, "x0", "El valor"); r = identificar(x); nom = _nom(hoja, p["y"])
        tab = []
        for d in r:
            if "error" in d: tab.append([d["nombre"], "—", "—", d["error"]] + ([""] if x0 is not None else [])); continue
            tab.append([d["nombre"], "; ".join(f"{k} {num(v, 4)}" for k, v in d["par"].items()), num(d["a2"], 3), p_texto(d["p"])] +
                       ([f"{100 * float(d['dist'].sf(x0)):.2f}%"] if x0 is not None else []))
        ok = [d for d in r if "error" not in d]
        fig, axs = figura(9.6, 5.6, nrows=2, ncols=3); fl = list(axs.flat)
        xs = np.sort(x); n = len(xs); pr = (np.arange(1, n + 1) - .3) / (n + .4)
        for ax, d in zip(fl, ok):
            teo = d["dist"].ppf(pr); ax.scatter(teo, xs, s=9, color=NARANJA, zorder=3)
            lo, hi = min(teo.min(), xs.min()), max(teo.max(), xs.max()); ax.plot([lo, hi], [lo, hi], color=TINTA, lw=1)
            ax.set_title(f"{d['nombre']}  AD={num(d['a2'], 3)}  {p_igual(d['p'])}", fontsize=8); ax.tick_params(labelsize=6)
        for ax in fl[len(ok):]: ax.axis("off")
        svg, png = a_svg_png(fig)
        buenas = [d["nombre"] for d in ok if d["p"] > .05]
        concl = (("Distribuciones que no se rechazan (p > 0.05): " + ", ".join(buenas) + ". Elige la que corresponda al origen de los datos (por ejemplo, tiempos: lognormal o Weibull), "
                  "como indica 25_BB DIST-IDENTIFICAR.") if buenas else "Ninguna de las cinco distribuciones se ajusta (todas con p ≤ 0.05): revisa si hay mezcla de procesos o considera una transformación (Box-Cox).")
        return resultado(cls.ID, f"Identificación de distribución de {nom}", p, [
            b_texto(concl, "conclusion"), b_tabla("Bondad de ajuste (Anderson-Darling)", ["Distribución", "Parámetros", "AD", "Valor p"] + ([f"P(X > {num(x0)})"] if x0 is not None else []), tab),
            b_grafica(svg),
            b_texto("Procedimiento: 25_BB DIST-IDENTIFICAR (probar varias distribuciones y quedarse con las de p > 0.05 según el origen de los datos). "
                    "No respaldado por la base: los valores p de exponencial, Weibull y gamma se calculan por simulación paramétrica (300 réplicas, semilla fija), "
                    "y los parámetros por máxima verosimilitud; Minitab usa tablas, por lo que pueden diferir ligeramente.")],
            [f"{fuera} celdas vacías o no numéricas quedaron fuera."] if fuera else [], datos={"columnas": [p["y"]]}, png=png)


LAMBDAS = [-2, -1, -.5, 0, .5, 1, 2]


def transformar(x, lam): x = np.asarray(x, float); return np.log(x) if lam == 0 else x ** lam


def boxcox_lambda(x):
    """λ por máxima verosimilitud, IC 95% por perfil de verosimilitud y λ redondeado a un valor común dentro del IC [GENERAL]."""
    x = np.asarray(x, float); lam = float(st.boxcox_normmax(x, method="mle"))
    llf = lambda l: st.boxcox_llf(l, x); lim = llf(lam) - .5 * st.chi2.ppf(.95, 1)
    g = lambda l: llf(l) - lim
    try: lo = optimize.brentq(g, lam - 10, lam)
    except ValueError: lo = -math.inf
    try: hi = optimize.brentq(g, lam, lam + 10)
    except ValueError: hi = math.inf
    cand = [l for l in LAMBDAS if lo <= l <= hi]
    red = min(cand, key=lambda l: abs(l - lam)) if cand else round(lam * 2) / 2
    return lam, (lo, hi), red


def fuera_transformado(media_t, sd_t, lie, lse, lam):
    """[BASE] 25_BB DIST-TRANSFORMACION: los límites se transforman con la misma fórmula y se usa la normal con la media y
    desviación de los datos transformados. Con λ < 0 la transformación invierte el orden y los límites se intercambian."""
    tl = [None if v is None else float(transformar([v], lam)[0]) for v in (lie, lse)]
    if lam < 0: tl = tl[::-1]
    zi = (tl[0] - media_t) / sd_t if tl[0] is not None else None; zs = (tl[1] - media_t) / sd_t if tl[1] is not None else None
    pi = float(st.norm.cdf(zi)) if zi is not None else 0.0; ps = float(st.norm.sf(zs)) if zs is not None else 0.0
    return {"lim_t": tl, "z": (zi, zs), "p": (pi, ps), "total": pi + ps}


@registrar
class BoxCox(ModuloDialogo):
    ID, TITULO = "BOXCOX", "Transformación Box-Cox"
    CAMPOS = [{"campo": "y", "etiqueta": "Datos (mayores que cero)", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "usar", "etiqueta": "λ a usar", "tipo": "opcion", "defecto": "redondeado",
               "opciones": [["redondeado", "Redondeado a un valor común (como Minitab)"], ["optimo", "Óptimo estimado"], ["valor", "Un valor que yo indique"]]},
              {"campo": "lam", "etiqueta": "λ (si eliges indicarlo)", "tipo": "numero"},
              {"campo": "lie", "etiqueta": "LIE (opcional)", "tipo": "numero"}, {"campo": "lse", "etiqueta": "LSE (opcional)", "tipo": "numero"},
              {"campo": "dest", "etiqueta": "Guardar los datos transformados en la columna (opcional)", "tipo": "texto"}]
    CAMBIA_HOJA = True

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        x, fuera = _num_col(hoja, p.get("y"), "los datos")
        if len(x) < 8: raise ErrorEntrada("Se necesitan al menos 8 datos.")
        if np.any(x <= 0): raise ErrorEntrada("Box-Cox requiere datos mayores que cero; suma una constante o usa otra transformación.")
        lam_o, ic, red = boxcox_lambda(x)
        uso = p.get("usar") or "redondeado"
        lam = red if uso == "redondeado" else lam_o if uso == "optimo" else cls.numero(p, "lam", "El valor de λ", opcional=False)
        t = transformar(x, lam); mt, sdt = float(np.mean(t)), float(np.std(t, ddof=1))
        ad0, ad1 = E.anderson_darling(list(x)), E.anderson_darling(list(t))
        lie, lse = cls.numero(p, "lie", "El LIE"), cls.numero(p, "lse", "El LSE")
        nom = _nom(hoja, p["y"]); bloques = []
        forma = "ln(Y)" if lam == 0 else ("√Y" if lam == .5 else f"Y^{num(lam, 4)}")
        bloques.append(b_texto(f"Transformación {forma} (λ = {num(lam, 4)}). Normalidad antes {p_igual(ad0['p'])}; después {p_igual(ad1['p'])}: "
                               + ("los datos transformados ya pueden tratarse como normales." if ad1["p"] > .05 else "aun transformados no se comportan como normales; revisa la causa física o usa otra distribución."), "conclusion"))
        bloques.append(b_tabla("Estimación de λ", ["Concepto", "Valor"], [["λ óptimo (máxima verosimilitud)", num(lam_o, 4)], ["IC 95% de λ", _ic_txt(ic, 3)],
                               ["λ redondeado", num(red, 2)], ["λ usado", num(lam, 4)], ["Media transformada", num(mt, 4)], ["Desv. est. transformada", num(sdt, 4)]]))
        if lie is not None or lse is not None:
            r = fuera_transformado(mt, sdt, lie, lse, lam)
            if lam < 0 and lie is not None and lse is not None: bloques.append(b_texto("Con λ negativo la transformación invierte el orden: el LSE transformado queda abajo.", "aviso"))
            bloques.append(b_tabla("Fuera de especificación (con los datos transformados)", ["Límite", "Original", "Transformado", "Z", "Probabilidad fuera"], [
                ["Inferior", num(lie) if lie is not None else "—", num(r["lim_t"][0], 4) if r["lim_t"][0] is not None else "—", num(r["z"][0], 3) if r["z"][0] is not None else "—", f"{r['p'][0]:.5f}"],
                ["Superior", num(lse) if lse is not None else "—", num(r["lim_t"][1], 4) if r["lim_t"][1] is not None else "—", num(r["z"][1], 3) if r["z"][1] is not None else "—", f"{r['p'][1]:.5f}"],
                ["Total", "", "", "", f"{r['total']:.5f} ({100 * r['total']:.2f}%)"]]))
        fig, axs = figura(9.6, 3.0, ncols=3)
        axs[0].hist(x, bins=min(15, max(5, int(math.sqrt(len(x))))), color=CLARO, edgecolor=NARANJA); axs[0].set_title(f"Original ({p_igual(ad0['p'])})", fontsize=8)
        axs[1].hist(t, bins=min(15, max(5, int(math.sqrt(len(x))))), color=CLARO, edgecolor=NARANJA); axs[1].set_title(f"Transformado ({p_igual(ad1['p'])})", fontsize=8)
        ls = np.linspace(max(-3, (ic[0] if math.isfinite(ic[0]) else lam_o - 2) - 1), min(3, (ic[1] if math.isfinite(ic[1]) else lam_o + 2) + 1), 80)
        axs[2].plot(ls, [st.boxcox_llf(l, x) for l in ls], color=TINTA); axs[2].axvline(lam_o, color=NARANJA, lw=1); axs[2].axvline(lam, color="#b3261e", lw=1, ls="--")
        axs[2].set_title("Log-verosimilitud contra λ", fontsize=8)
        svg, png = a_svg_png(fig); bloques.append(b_grafica(svg))
        if (p.get("dest") or "").strip():
            from .calc_hoja import escribir_columna
            vals = [None] * hoja.n; filas, _ = filas_validas(hoja, [p["y"]])
            for i, v in zip(filas, t): vals[i] = float(v)
            j = escribir_columna(hoja, p["dest"], vals, "num"); bloques.append(b_texto(f"Datos transformados guardados en C{j + 1} {hoja.columnas[j].nombre}."))
        bloques.append(b_texto("Método y transformación de límites: 25_BB DIST-TRANSFORMACION (Y elevada a λ; ln si λ = 0; las transformaciones son el último recurso). "
                               "No respaldados por la base: la estimación de λ por máxima verosimilitud, su intervalo por perfil y el redondeo."))
        return resultado(cls.ID, f"Box-Cox de {nom}", p, bloques, [f"{fuera} celdas vacías o no numéricas quedaron fuera."] if fuera else [],
                         datos={"columnas": [p["y"]], "lambda": lam}, png=png,
                         interpretacion=["Antes de transformar, busca un efecto físico que explique la no normalidad, o analiza promedios de subgrupos (25_BB DIST-TRANSFORMACION)."])


# ===================== E11 potencia y tamaño de muestra =====================
Z_CURSO = {"90": 1.64, "95": 1.96, "99": 2.58}


def n_proporcion(p, d, z, N=None):
    """[BASE] 15_GB MUE-DISCRETA: n = p(1-p)/(d/z)²; si n/N > 0.05, n/(1 + n/N)."""
    n0 = math.ceil(p * (1 - p) / (d / z) ** 2 - 1e-9); return n0, (math.ceil(n0 / (1 + n0 / N) - 1e-9) if N and n0 / N > .05 else n0)


def n_media(s, d, z, N=None):
    """[BASE] 15_GB MUE-CONTINUA: n = (z·s/d)²; mismo ajuste por población finita."""
    n0 = math.ceil((z * s / d) ** 2 - 1e-9); return n0, (math.ceil(n0 / (1 + n0 / N) - 1e-9) if N and n0 / N > .05 else n0)


def potencia_t(n, delta, sigma, alfa=.05, muestras=1, alt="!="):
    """[GENERAL] Potencia de la prueba t con la t no central (n por grupo cuando hay 2 muestras)."""
    if muestras == 1: gl, nc = n - 1, delta / sigma * math.sqrt(n)
    else: gl, nc = 2 * n - 2, delta / sigma * math.sqrt(n / 2)
    if alt == "!=":
        c = st.t.ppf(1 - alfa / 2, gl); return float(st.nct.sf(c, gl, nc) + st.nct.cdf(-c, gl, nc))
    c = st.t.ppf(1 - alfa, gl); return float(st.nct.sf(c, gl, abs(nc)))


def n_para_potencia(delta, sigma, alfa, objetivo, muestras=1, alt="!="):
    for n in range(2, 100001):
        if potencia_t(n, delta, sigma, alfa, muestras, alt) >= objetivo: return n
    return None


@registrar
class Potencia(ModuloDialogo):
    ID, TITULO, HOJA_VACIA_OK = "POTENCIA", "Potencia y tamaño de muestra", True
    CAMPOS = [{"campo": "tipo", "etiqueta": "Cálculo", "tipo": "opcion", "defecto": "media",
               "opciones": [["prop", "Tamaño de muestra para estimar una proporción (datos discretos)"], ["media", "Tamaño de muestra para estimar una media (datos continuos)"],
                            ["t1", "Potencia o tamaño de muestra: t de 1 muestra"], ["t2", "Potencia o tamaño de muestra: t de 2 muestras"]]},
              {"campo": "conf", "etiqueta": "Confianza (estimación)", "tipo": "opcion", "defecto": "95", "opciones": [["90", "90% (z = 1.64)"], ["95", "95% (z = 1.96)"], ["99", "99% (z = 2.58)"]]},
              {"campo": "p", "etiqueta": "Proporción estimada (p)", "tipo": "numero"}, {"campo": "s", "etiqueta": "Desviación estándar estimada (s o σ)", "tipo": "numero"},
              {"campo": "d", "etiqueta": "Precisión ±d (estimación) o diferencia a detectar (pruebas)", "tipo": "numero"},
              {"campo": "N", "etiqueta": "Tamaño de la población (opcional)", "tipo": "numero"},
              {"campo": "n", "etiqueta": "Pruebas: tamaño de muestra (para calcular la potencia)", "tipo": "numero"},
              {"campo": "pot", "etiqueta": "Pruebas: potencia deseada (para calcular n), ej. 0.8", "tipo": "numero"},
              {"campo": "alt", "etiqueta": "Pruebas: hipótesis alterna", "tipo": "opcion", "opciones": ALTS, "defecto": "!="},
              {"campo": "alfa", "etiqueta": "Pruebas: alfa", "tipo": "opcion", "opciones": ALFAS, "defecto": "0.05"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        tipo = p.get("tipo") or "media"; d = cls.numero(p, "d", "La precisión o diferencia", opcional=False, minimo=0); N = cls.numero(p, "N", "La población", minimo=0)
        if tipo in ("prop", "media"):
            z = Z_CURSO[p.get("conf") or "95"]
            if tipo == "prop":
                pp = cls.numero(p, "p", "La proporción", opcional=False, minimo=0, maximo=1); n0, n = n_proporcion(pp, d, z, N); form = "n = p(1-p)/(d/z)²"
            else:
                s = cls.numero(p, "s", "La desviación estándar", opcional=False, minimo=0); n0, n = n_media(s, d, z, N); form = "n = (z·s/d)²"
            filas = [["Fórmula (15_GB " + ("MUE-DISCRETA" if tipo == "prop" else "MUE-CONTINUA") + ")", form], ["z", num(z)], ["n sin ajustar", f"{n0:,}"]]
            if N: filas += [["n / N", num(n0 / N, 4)], ["n ajustado por población finita" if n != n0 else "Ajuste por población finita", f"{n:,}" if n != n0 else "no necesario (n/N ≤ 0.05)"]]
            return resultado(cls.ID, f"Tamaño de muestra: {n:,} unidades", p, [b_texto(f"Toma una muestra de {n:,} unidades.", "conclusion"), b_tabla("Cálculo", ["Concepto", "Valor"], filas),
                             b_texto("Los valores de z son los del curso (1.64, 1.96 y 2.58) para reproducir sus ejemplos.")], datos={"columnas": []})
        s = cls.numero(p, "s", "La desviación estándar", opcional=False, minimo=0); alfa = float(p.get("alfa") or .05); alt = p.get("alt") or "!="
        m = 1 if tipo == "t1" else 2; nn = cls.numero(p, "n", "El tamaño de muestra", minimo=1); pot = cls.numero(p, "pot", "La potencia", minimo=0, maximo=1)
        if nn is None and pot is None: raise ErrorEntrada("Indica el tamaño de muestra (para calcular la potencia) o la potencia deseada (para calcular n).")
        if nn is not None: n = int(nn); pw = potencia_t(n, d, s, alfa, m, alt); titulo = f"Potencia {pw:.4f} con n = {n}"
        else:
            n = n_para_potencia(d, s, alfa, pot, m, alt); pw = potencia_t(n, d, s, alfa, m, alt); titulo = f"n = {n} {'por grupo ' if m == 2 else ''}para potencia {pot:g}"
        ds = np.linspace(0, 2.5 * d, 60)
        fig, ax = figura(5.8, 3.2); ax.plot(ds, [potencia_t(n, x, s, alfa, m, alt) for x in ds], color=NARANJA); ax.axvline(d, color=SUAVE, ls="--", lw=.8)
        ax.axhline(pw, color=SUAVE, ls="--", lw=.8); ax.set_xlabel("Diferencia"); ax.set_ylabel("Potencia"); ax.set_ylim(0, 1.02); ax.set_title(f"Curva de potencia con n = {n}", fontsize=9)
        svg, png = a_svg_png(fig)
        return resultado(cls.ID, titulo, p, [b_texto(f"Con n = {n}{' por grupo' if m == 2 else ''}, la probabilidad de detectar una diferencia de {num(d)} es {pw:.4f}.", "conclusion"), b_grafica(svg),
                         b_tabla("Datos", ["Concepto", "Valor"], [["Prueba", "t de 1 muestra" if m == 1 else "t de 2 muestras"], ["Diferencia", num(d)], ["Desv. est.", num(s)], ["Alfa", alfa],
                                                                   ["n" + (" por grupo" if m == 2 else ""), n], ["Potencia", f"{pw:.4f}"]]), b_texto(GENERAL)], datos={"columnas": []}, png=png)


# ===================== E11 no paramétricas y chi cuadrada =====================
@registrar
class NoParam(ModuloDialogo):
    ID, TITULO = "NOPARAM", "Pruebas no paramétricas"
    INDEPENDIENTES = True
    CAMPOS = [{"campo": "tipo", "etiqueta": "Prueba", "tipo": "opcion", "defecto": "mann",
               "opciones": [["mann", "Mann-Whitney (2 muestras independientes)"], ["kruskal", "Kruskal-Wallis (3 o más grupos)"], ["mood", "Mediana de Mood (2 o más grupos)"],
                            ["wilcoxon", "Wilcoxon (mediana contra un valor)"], ["pareada", "Wilcoxon pareada (antes y después)"], ["signos", "Prueba de signos (mediana contra un valor)"]]},
              {"campo": "y", "etiqueta": "Datos", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "grupo", "etiqueta": "Columna de grupo (Mann-Whitney, Kruskal-Wallis, Mood)", "tipo": "col", "opcional": True},
              {"campo": "y2", "etiqueta": "Segunda muestra o «después» (en lugar del grupo)", "tipo": "col", "filtro": "num", "opcional": True},
              {"campo": "h0", "etiqueta": "Mediana de la hipótesis nula (1 muestra)", "tipo": "numero"},
              {"campo": "alt", "etiqueta": "Hipótesis alterna", "tipo": "opcion", "opciones": ALTS, "defecto": "!="},
              {"campo": "alfa", "etiqueta": "Alfa", "tipo": "opcion", "opciones": ALFAS, "defecto": "0.05"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        tipo, alfa, alt = p.get("tipo") or "mann", float(p.get("alfa") or .05), p.get("alt") or "!="
        A = {"!=": "two-sided", "<": "less", ">": "greater"}[alt]; avisos = []
        if tipo in ("kruskal", "mood"):
            yj, g = p.get("y"), p.get("grupo"); columna(hoja, yj, "los datos", "num"); columna(hoja, g, "el grupo")
            filas, fuera = filas_validas(hoja, [yj, g]); gr = {}
            for i in filas: gr.setdefault(str(valor(hoja, g, i)), []).append(valor(hoja, yj, i))
            if len(gr) < 2: raise ErrorEntrada("Se necesitan al menos 2 grupos.")
            nombres = sorted(gr, key=str); ms = [gr[k] for k in nombres]
            if tipo == "kruskal": r = st.kruskal(*ms); est, pv, nm = float(r.statistic), float(r.pvalue), "H"
            else: r = st.median_test(*ms); est, pv, nm = float(r.statistic), float(r.pvalue), "Chi cuadrada"
            h0t, hat = "las medianas de los grupos son iguales", "al menos una mediana es distinta"; ttl = ("Kruskal-Wallis" if tipo == "kruskal" else "Mediana de Mood")
        elif tipo == "mann":
            a, b, nombres, fuera = _dos_muestras(hoja, p); ms = [list(a), list(b)]
            r = st.mannwhitneyu(a, b, alternative=A); est, pv, nm = float(r.statistic), float(r.pvalue), "U"
            h0t, hat = "las medianas son iguales", "las medianas son distintas" if alt == "!=" else f"la mediana 1 es {'menor' if alt == '<' else 'mayor'}"; ttl = "Mann-Whitney"
        else:
            if tipo == "pareada":
                yj, y2 = p.get("y"), p.get("y2"); columna(hoja, yj, "los datos", "num"); columna(hoja, y2, "la segunda muestra", "num")
                filas, fuera = filas_validas(hoja, [yj, y2]); x = np.array([valor(hoja, yj, i) - valor(hoja, y2, i) for i in filas]); m0 = 0.0; nombres = ["Diferencias"]
            else:
                x, fuera = _num_col(hoja, p.get("y"), "los datos"); m0 = cls.numero(p, "h0", "La mediana de H0", opcional=False); nombres = [_nom(hoja, p["y"])]
            ms = [list(x)]
            if tipo == "signos":
                arriba, abajo = int((x > m0).sum()), int((x < m0).sum()); r = st.binomtest(arriba, arriba + abajo, .5, alternative=A)
                est, pv, nm = arriba, float(r.pvalue), "Arriba de la mediana"; ttl = "Prueba de signos"
            else:
                r = st.wilcoxon(x - m0, alternative=A); est, pv, nm = float(r.statistic), float(r.pvalue), "W"; ttl = "Wilcoxon" + (" pareada" if tipo == "pareada" else "")
            h0t, hat = f"la mediana es {num(m0)}", f"la mediana es {'distinta de' if alt == '!=' else 'menor que' if alt == '<' else 'mayor que'} {num(m0)}"
        med = [[n_, len(v), num(float(np.median(v)), 4)] for n_, v in zip(nombres, ms)]
        fig, ax = figura(5.6, 3.0); ax.boxplot(ms, patch_artist=True, medianprops={"color": NARANJA}, boxprops={"facecolor": CLARO, "edgecolor": NARANJA})
        ax.set_xticks(range(1, len(nombres) + 1)); ax.set_xticklabels(nombres, fontsize=7); svg, png = a_svg_png(fig)
        if fuera: avisos.append(f"{fuera} celdas vacías o incompletas quedaron fuera.")
        return resultado(cls.ID, f"{ttl}", p, [b_texto(frase_p(pv, alfa, h0t, hat), "conclusion"), b_tabla("Medianas", ["Muestra", "N", "Mediana"], med),
                         b_tabla("Prueba", ["Estadístico", "Valor", "Valor p"], [[nm, num(est, 4), p_texto(pv)]]), b_grafica(svg),
                         b_texto("Útiles cuando los datos no son normales y la muestra es pequeña; comparan medianas o rangos. " + GENERAL)],
                         avisos, datos={"columnas": [p.get(k) for k in ("y", "y2", "grupo") if p.get(k) is not None]}, png=png)


@registrar
class Chi2(ModuloDialogo):
    ID, TITULO = "CHI2", "Tabla cruzada y chi cuadrada"
    CAMPOS = [{"campo": "filas", "etiqueta": "Variable en filas", "tipo": "col"}, {"campo": "cols", "etiqueta": "Variable en columnas", "tipo": "col"},
              {"campo": "frec", "etiqueta": "Frecuencias (opcional; si cada fila ya es un conteo)", "tipo": "col", "filtro": "num", "opcional": True},
              {"campo": "alfa", "etiqueta": "Alfa", "tipo": "opcion", "opciones": ALFAS, "defecto": "0.05"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        fj, cj, wj = p.get("filas"), p.get("cols"), p.get("frec"); alfa = float(p.get("alfa") or .05)
        columna(hoja, fj, "la variable en filas"); columna(hoja, cj, "la variable en columnas"); columna(hoja, wj, "las frecuencias", "num", obligatoria=False)
        filas, fuera = filas_validas(hoja, [fj, cj] + ([wj] if wj is not None else []))
        rs = sorted({str(valor(hoja, fj, i)) for i in filas}, key=str); cs = sorted({str(valor(hoja, cj, i)) for i in filas}, key=str)
        if len(rs) < 2 or len(cs) < 2: raise ErrorEntrada("Cada variable necesita al menos 2 categorías.")
        T = np.zeros((len(rs), len(cs)))
        for i in filas: T[rs.index(str(valor(hoja, fj, i))), cs.index(str(valor(hoja, cj, i)))] += valor(hoja, wj, i) if wj is not None else 1
        chi, pv, gl, esp = st.chi2_contingency(T, correction=False); g2 = st.chi2_contingency(T, correction=False, lambda_="log-likelihood")
        tab = [[r] + [f"{int(T[a, b]) if float(T[a, b]).is_integer() else num(T[a, b])} ({num(esp[a, b], 2)})" for b in range(len(cs))] + [num(T[a].sum())] for a, r in enumerate(rs)]
        tab.append(["Total"] + [num(T[:, b].sum()) for b in range(len(cs))] + [num(T.sum())])
        bajos = int((esp < 5).sum()); avisos = [f"{bajos} celdas con conteo esperado menor que 5: la prueba puede no ser confiable; agrupa categorías."] if bajos else []
        fig, ax = figura(6.0, 3.2); base = np.zeros(len(rs))
        for b, c in enumerate(cs):
            ax.bar(rs, T[:, b] / T.sum(axis=1) * 100, bottom=base, color=PALETA[b % len(PALETA)], label=c); base += T[:, b] / T.sum(axis=1) * 100
        ax.set_ylabel("% de la fila"); ax.legend(fontsize=6, frameon=False); svg, png = a_svg_png(fig)
        return resultado(cls.ID, f"Tabla cruzada: {_nom(hoja, fj)} por {_nom(hoja, cj)}", p, [
            b_texto(frase_p(pv, alfa, "las variables son independientes", "hay asociación entre las variables"), "conclusion"),
            b_tabla("Conteos (esperados entre paréntesis)", [""] + cs + ["Total"], tab),
            b_tabla("Prueba", ["Método", "Chi cuadrada", "GL", "Valor p"], [["Pearson", num(chi, 4), gl, p_texto(pv)], ["Razón de verosimilitud", num(float(g2[0]), 4), gl, p_texto(float(g2[1]))]]),
            b_grafica(svg), b_texto(GENERAL)], avisos + ([f"{fuera} filas incompletas quedaron fuera."] if fuera else []),
            datos={"columnas": [fj, cj] + ([wj] if wj is not None else [])}, png=png)
