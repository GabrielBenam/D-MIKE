"""Cálculos estadísticos del MVP. Cada función indica de dónde sale su fórmula.

[BASE] = respaldado por la base LSS (archivo y sección en el comentario).
[GENERAL] = NO respaldado por la base: conocimiento general (Minitab / literatura), marcado como tal.
"""
import math
from collections import Counter
from scipy import stats as st


# ---------- estadística descriptiva ----------
def cuartil(orden, p):
    """[GENERAL] Método de Minitab: posición p(n+1) con interpolación lineal; fuera de rango, mín o máx.
    La base (17_GB_ANALIZAR, BOX-PROCEDIMIENTO) pide Q1, Q2 y Q3 pero no fija el método."""
    n = len(orden)
    pos = p * (n + 1)
    if pos <= 1: return orden[0]
    if pos >= n: return orden[-1]
    k = int(math.floor(pos)); f = pos - k
    return orden[k - 1] + f * (orden[k] - orden[k - 1])


def descriptivos(x):
    """[BASE] 15_GB_ESTADISTICA_Y_MUESTREO, EST-CENTRAL y EST-VARIABILIDAD: media, mediana, moda, rango,
    desviación estándar y varianza muestrales (n-1). Cuartiles: ver cuartil()."""
    n = len(x)
    if n == 0: return None
    o = sorted(x); media = sum(o) / n
    mediana = (o[(n - 1) // 2] + o[n // 2]) / 2
    cuenta = Counter(o); maxc = max(cuenta.values())
    modas = sorted(v for v, c in cuenta.items() if c == maxc) if maxc > 1 else []
    var = sum((v - media) ** 2 for v in o) / (n - 1) if n > 1 else float("nan")
    desv = math.sqrt(var) if n > 1 else float("nan")
    q1, q3 = cuartil(o, 0.25), cuartil(o, 0.75)
    # [GENERAL] suma, error estándar de la media, CV, RIC, asimetría y curtosis (corregidas por sesgo, como Excel).
    asim = float(st.skew(o, bias=False)) if n > 2 and desv > 0 else float("nan")
    curt = float(st.kurtosis(o, bias=False)) if n > 3 and desv > 0 else float("nan")
    return {"n": n, "media": media, "mediana": mediana, "modas": modas, "n_moda": maxc if modas else 0,
            "minimo": o[0], "maximo": o[-1], "rango": o[-1] - o[0], "varianza": var, "desv": desv,
            "q1": q1, "q3": q3, "ric": q3 - q1, "suma": sum(o), "ee_media": desv / math.sqrt(n) if n > 1 else float("nan"),
            "cv": 100 * desv / media if n > 1 and media != 0 else float("nan"), "asimetria": asim, "curtosis": curt}


def caja(x):
    """[BASE] 17_GB_ANALIZAR, BOX-PROCEDIMIENTO: Q1, Q2, Q3; bigotes hasta 1.5 x RIC; más allá, atípicos."""
    d = descriptivos(x); o = sorted(x)
    ric = d["q3"] - d["q1"]
    li, ls = d["q1"] - 1.5 * ric, d["q3"] + 1.5 * ric
    dentro = [v for v in o if li <= v <= ls]
    return {**d, "ric": ric, "bigote_inf": min(dentro), "bigote_sup": max(dentro),
            "atipicos": [v for v in o if v < li or v > ls]}


# ---------- muestreo ----------
def tamano_muestra(tipo, z, d, p=None, s=None, N=None):
    """[BASE] 15_GB_ESTADISTICA_Y_MUESTREO, MUE-DISCRETA y MUE-CONTINUA.
    discreto n = p(1-p)/(d/z)^2 ; continuo n = (z s / d)^2 ; si n/N > 0.05, n/(1+n/N).
    Redondeo hacia arriba (el curso da 2,203, 339 y 81)."""
    n0 = p * (1 - p) / (d / z) ** 2 if tipo == "discreto" else (z * s / d) ** 2
    r = {"n_sin_ajuste": math.ceil(n0 - 1e-9), "n0": n0, "ajustado": False, "razon": None}
    if N:
        r["razon"] = n0 / N
        if r["razon"] > 0.05:
            r["ajustado"] = True
            return {**r, "n": math.ceil(n0 / (1 + n0 / N) - 1e-9)}
    return {**r, "n": r["n_sin_ajuste"]}


# ---------- ANOVA ----------
def _tabla_f(ss, gl, ss_err, gl_err, alfa):
    ms, mse = ss / gl, ss_err / gl_err
    f = ms / mse if mse > 0 else float("inf")
    return {"ss": ss, "gl": gl, "ms": ms, "f": f, "p": float(st.f.sf(f, gl, gl_err)),
            "f_tablas": float(st.f.ppf(1 - alfa, gl, gl_err))}


def anova_un_factor(grupos, alfa=0.05):
    """[BASE] 17_GB_ANALIZAR, ANOVA-TIPOS: SSt (gl a-1), SSE (gl N-a), F = MSt/MSE; se rechaza H0 si
    F > F de tablas (p < alfa). F de tablas: 20_GB_TABLA_F. grupos: {nivel: [valores]}."""
    todos = [v for g in grupos.values() for v in g]
    N, a = len(todos), len(grupos)
    gm = sum(todos) / N
    ss_t = sum(len(g) * (sum(g) / len(g) - gm) ** 2 for g in grupos.values())
    ss_e = sum((v - sum(g) / len(g)) ** 2 for g in grupos.values() for v in g)
    trat = _tabla_f(ss_t, a - 1, ss_e, N - a, alfa)
    res = [v - sum(g) / len(g) for g in grupos.values() for v in g]
    return {"tratamientos": trat, "error": {"ss": ss_e, "gl": N - a, "ms": ss_e / (N - a)},
            "total": {"ss": ss_t + ss_e, "gl": N - 1}, "alfa": alfa, "significativo": trat["p"] < alfa,
            "r2": ss_t / (ss_t + ss_e) if ss_t + ss_e > 0 else float("nan")}


def anova_bloque(celdas, alfa=0.05):
    """[BASE] 17_GB_ANALIZAR, ANOVA-TIPOS (un factor con bloqueo): tratamientos, bloque y error;
    bloqueo efectivo si MSBL >= 2 a 2.5 veces MSE. celdas: {(nivel, bloque): [valores]}, diseño balanceado.
    Con una observación por celda es exactamente el diseño de la plantilla del curso (PL12);
    con r réplicas por celda se usa el mismo modelo aditivo (sin interacción) [GENERAL]."""
    niveles = sorted({k[0] for k in celdas}, key=str); bloques = sorted({k[1] for k in celdas}, key=str)
    a, b = len(niveles), len(bloques); r = len(next(iter(celdas.values())))
    todos = [v for g in celdas.values() for v in g]; N = len(todos); gm = sum(todos) / N
    m_niv = {i: sum(v for (x, _), g in celdas.items() if x == i for v in g) / (b * r) for i in niveles}
    m_bl = {j: sum(v for (_, y), g in celdas.items() if y == j for v in g) / (a * r) for j in bloques}
    ss_tot = sum((v - gm) ** 2 for v in todos)
    ss_t = b * r * sum((m - gm) ** 2 for m in m_niv.values())
    ss_b = a * r * sum((m - gm) ** 2 for m in m_bl.values())
    ss_e = ss_tot - ss_t - ss_b; gl_e = N - a - b + 1
    trat, bl = _tabla_f(ss_t, a - 1, ss_e, gl_e, alfa), _tabla_f(ss_b, b - 1, ss_e, gl_e, alfa)
    mse = ss_e / gl_e
    return {"tratamientos": trat, "bloque": bl, "error": {"ss": ss_e, "gl": gl_e, "ms": mse},
            "total": {"ss": ss_tot, "gl": N - 1}, "alfa": alfa, "significativo": trat["p"] < alfa,
            "bloque_significativo": bl["p"] < alfa, "razon_bloque": bl["ms"] / mse if mse > 0 else float("inf"),
            "medias_nivel": m_niv, "medias_bloque": m_bl, "gran_media": gm, "replicas": r}


# ---------- normalidad y especificaciones ----------
def anderson_darling(x):
    """[GENERAL] Prueba de normalidad de Anderson-Darling, la que usa Minitab por omisión, con el valor p de
    D'Agostino y Stephens (1986). La base (25_BB_DISTRIBUCIONES, DIST-IDENTIFICAR) solo fija el criterio:
    p > 0.05, se asumen normales."""
    n = len(x); o = sorted(x); m = sum(o) / n
    s = math.sqrt(sum((v - m) ** 2 for v in o) / (n - 1))
    z = [st.norm.cdf((v - m) / s) for v in o]
    eps = 1e-15
    a2 = -n - sum((2 * i - 1) * (math.log(max(z[i - 1], eps)) + math.log(max(1 - z[n - i], eps)))
                  for i in range(1, n + 1)) / n
    a = a2 * (1 + 0.75 / n + 2.25 / n ** 2)
    if a < 0.2: p = 1 - math.exp(-13.436 + 101.14 * a - 223.73 * a * a)
    elif a < 0.34: p = 1 - math.exp(-8.318 + 42.796 * a - 59.938 * a * a)
    elif a < 0.6: p = math.exp(0.9177 - 4.279 * a - 1.38 * a * a)
    else: p = math.exp(1.2937 - 5.709 * a + 0.0186 * a * a)
    return {"a2": a2, "p": min(max(p, 0.0), 1.0)}


def fuera_de_especificacion(media, desv, lie=None, lse=None):
    """[BASE] 25_BB_DISTRIBUCIONES, DIST-Z y DIST-EJ-Z: Z = (X - media)/s; probabilidad normal estándar.
    Nivel sigma: DIST-IDENTIFICAR ejemplo 1 y CAP-NIVEL-SIGMA (16_GB): largo plazo = Z(1 - fuera),
    corto plazo = largo plazo + 1.5."""
    r = {"z_inf": None, "z_sup": None, "p_inf": 0.0, "p_sup": 0.0}
    if lie is not None:
        r["z_inf"] = (lie - media) / desv; r["p_inf"] = float(st.norm.cdf(r["z_inf"]))
    if lse is not None:
        r["z_sup"] = (lse - media) / desv; r["p_sup"] = float(st.norm.sf(r["z_sup"]))
    r["p_total"] = r["p_inf"] + r["p_sup"]
    if 0 < r["p_total"] < 1:
        r["sigma_lp"] = float(st.norm.isf(r["p_total"])); r["sigma_cp"] = r["sigma_lp"] + 1.5
    else:
        r["sigma_lp"] = r["sigma_cp"] = None
    return r


# ---------- corridas (gráfica de corrida) ----------
def corridas(x):
    """Rachas y tendencias de una serie en orden.
    [BASE, adaptado] 19_GB_CONTROLAR, SPC-PATRONES: racha = 8 puntos consecutivos del mismo lado de la línea
    central; tendencia = 6 o más puntos consecutivos sin cambio de dirección. Aquí la línea central es la
    mediana (la base lo define para cartas de control).
    [GENERAL] Pruebas de corridas de Minitab (aproximación normal): corridas sobre la mediana
    (agrupamiento / mezcla) y corridas arriba-abajo (tendencias / oscilación). Los puntos iguales a la
    mediana no cuentan en las corridas sobre la mediana."""
    n = len(x); o = sorted(x); med = (o[(n - 1) // 2] + o[n // 2]) / 2
    lados = [1 if v > med else -1 for v in x if v != med]
    na, nb = lados.count(1), lados.count(-1)
    r_med = 1 + sum(1 for i in range(1, len(lados)) if lados[i] != lados[i - 1]) if lados else 0
    largo_lado = max_racha(lados)
    res = {"mediana": med, "n": n, "corridas_mediana": r_med, "arriba": na, "abajo": nb,
           "racha_max": largo_lado}
    m = na + nb
    if na and nb and m > 1:
        e = 1 + 2 * na * nb / m
        v = 2 * na * nb * (2 * na * nb - m) / (m * m * (m - 1))
        zz = (r_med - e) / math.sqrt(v) if v > 0 else 0.0
        res.update(esperadas_mediana=e, p_agrupamiento=float(st.norm.cdf(zz)), p_mezcla=float(st.norm.sf(zz)))
    dif = [1 if x[i] > x[i - 1] else -1 for i in range(1, n) if x[i] != x[i - 1]]
    if dif:
        r_ud = 1 + sum(1 for i in range(1, len(dif)) if dif[i] != dif[i - 1])
        e = (2 * n - 1) / 3; v = (16 * n - 29) / 90
        zz = (r_ud - e) / math.sqrt(v) if v > 0 else 0.0
        res.update(corridas_arriba_abajo=r_ud, esperadas_arriba_abajo=e,
                   p_tendencia=float(st.norm.cdf(zz)), p_oscilacion=float(st.norm.sf(zz)))
        res["tendencia_max"] = max_racha(dif) + 1        # puntos, no diferencias
    else:
        res["tendencia_max"] = 1
    res["hay_racha"] = largo_lado >= 8
    res["hay_tendencia"] = res["tendencia_max"] >= 6
    return res


def max_racha(seq):
    mejor = act = 0; prev = None
    for s in seq:
        act = act + 1 if s == prev else 1; prev = s; mejor = max(mejor, act)
    return mejor


# ---------- Pareto ----------
def pareto(conteos, otros_despues=95.0):
    """[GENERAL] Diagrama de Pareto: categorías de mayor a menor, porcentaje y porcentaje acumulado; las
    categorías después del porcentaje acumulado indicado se agrupan en «Otros» (opción de Minitab, 95%).
    La base menciona el Pareto (03_SOLUCION_PROBLEMAS, formato 4 Q's; PL08) pero no su cálculo."""
    items = sorted(((k, v) for k, v in conteos.items() if v > 0), key=lambda t: (-t[1], str(t[0])))
    total = sum(v for _, v in items)
    filas, acum = [], 0.0
    for k, v in items:
        if otros_despues is not None and filas and acum >= otros_despues and len(items) - len(filas) > 1:
            resto = sum(c for kk, c in items[len(filas):])
            filas.append({"categoria": "Otros", "conteo": resto, "pct": 100 * resto / total,
                          "acum": 100.0, "agrupa": len(items) - len(filas)})
            break
        acum += 100 * v / total
        filas.append({"categoria": k, "conteo": v, "pct": 100 * v / total, "acum": acum})
    return {"total": total, "filas": filas}


# ---------- MSA de atributos ----------
def wilson(k, n, z=1.96):
    """[GENERAL] Intervalo de confianza de Wilson al 95%. La base (PL16, MSA-RR-ATRIBUTO-GB) indica que la
    plantilla del curso usa este método, sin dar la fórmula."""
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z / den * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, c - h), min(1.0, c + h))


def kappa_fleiss(tabla):
    """[GENERAL] Kappa de Fleiss. tabla: lista (una por muestra) de listas de calificaciones.
    La base (14_GB_MEDIR, MED-RR-ATRIBUTO) da el criterio: >= 0.75 apropiado, > 0.90 ideal."""
    cats = sorted({c for fila in tabla for c in fila}, key=str)
    m = len(tabla[0]); N = len(tabla)
    if m < 2 or N == 0: return None
    pj = {c: sum(f.count(c) for f in tabla) / (N * m) for c in cats}
    Pi = [(sum(f.count(c) ** 2 for c in cats) - m) / (m * (m - 1)) for f in tabla]
    P, Pe = sum(Pi) / N, sum(v * v for v in pj.values())
    return 1.0 if Pe == 1 else (P - Pe) / (1 - Pe)


def msa_atributos(evaluadores, referencia=None, valor_pasa=None):
    """[BASE] 14_GB_MEDIR, MED-RR-ATRIBUTO y PL16, MSA-RR-ATRIBUTO-GB: acuerdo de cada evaluador consigo
    mismo, contra el valor conocido, entre evaluadores y de todos contra el valor conocido; desacuerdos
    como falso negativo, falso positivo y mixto.
    Definiciones usadas [GENERAL]: falso negativo = en todas sus rondas rechazó una muestra que pasa;
    falso positivo = en todas sus rondas aceptó una muestra que no pasa; mixto = sus rondas no coinciden.
    evaluadores: {nombre: [[ronda1...], [ronda2...]]} alineado por muestra; referencia: [valores] o None."""
    nombres = list(evaluadores); n = len(next(iter(evaluadores.values()))[0])
    salida = {"n": n, "evaluadores": {}}
    for nom, rondas in evaluadores.items():
        filas = list(zip(*rondas))
        propio = [len(set(f)) == 1 for f in filas]
        e = {"consigo": _acuerdo(sum(propio), n), "kappa_consigo": kappa_fleiss([list(f) for f in filas])}
        if referencia is not None:
            ok = [all(v == referencia[i] for v in f) for i, f in enumerate(filas)]
            e["vs_ref"] = _acuerdo(sum(ok), n)
            e["mixto"] = sum(1 for f in filas if len(set(f)) > 1)
            if valor_pasa is not None:
                e["falso_negativo"] = sum(1 for i, f in enumerate(filas) if len(set(f)) == 1
                                          and referencia[i] == valor_pasa and f[0] != valor_pasa)
                e["falso_positivo"] = sum(1 for i, f in enumerate(filas) if len(set(f)) == 1
                                          and referencia[i] != valor_pasa and f[0] == valor_pasa)
        salida["evaluadores"][nom] = e
    todas = [[r[i] for nom in nombres for r in evaluadores[nom]] for i in range(n)]
    if len(nombres) > 1:
        salida["entre"] = _acuerdo(sum(1 for f in todas if len(set(f)) == 1), n)
        salida["kappa_entre"] = kappa_fleiss(todas)
    if referencia is not None:
        salida["todos_vs_ref"] = _acuerdo(sum(1 for i, f in enumerate(todas) if all(v == referencia[i] for v in f)), n)
    return salida


def _acuerdo(k, n):
    li, ls = wilson(k, n)
    return {"k": k, "n": n, "pct": 100 * k / n if n else float("nan"), "ic_inf": 100 * li, "ic_sup": 100 * ls}
