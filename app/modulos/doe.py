"""Motor de superficies de respuesta y diseños para optimizar procesos. Funciones puras, sin interfaz.

Fuente principal: 28_BB_SUPERFICIES_RESPUESTA (RSM-PROCEDIMIENTO, RSM-PUNTOS-CENTRALES, RSM-ASCENSO, RSM-DCC,
RSM-PRUEBAS-2DO-ORDEN, RSM-CONTORNO-FINAL, RSM-PUNTO-ESTACIONARIO), 27_BB_REGRESION (pruebas del modelo,
REG-FALTA-AJUSTE) y 18_GB_MEJORAR (FACT-NOTACION, FACT-DISEÑO-GENERAL).
[GENERAL, no respaldado por la base]: el valor de alfa rotable (2^(k/4)), el diseño de Box-Behnken, la cantidad
de puntos centrales por omisión, la codificación de bloques y la función de deseabilidad (Derringer y Suich).
Estructuras verificadas contra la salida de Minitab del libro Industrial Statistics with Minitab, cap. 28.
"""
import itertools, math, random
import numpy as np
from scipy import stats as st
from scipy import optimize

# ---------------- diseños ----------------
CENTROS_CCD = {2: (5, 0), 3: (6, 0), 4: (4, 2), 5: (6, 1), 6: (8, 2)}   # (centros en cubo, centros en estrella) con 2 bloques [GENERAL]
CENTROS_CCD_1B = {2: 5, 3: 6, 4: 7, 5: 10, 6: 15}
CENTROS_BB = {3: 3, 4: 3, 5: 6, 6: 6, 7: 6}


def alfa_rotable(k): return (2 ** k) ** 0.25


def diseno_ccd(k, alfa="rotable", bloques=1, centros_cubo=None, centros_estrella=None, replicas=1):
    """Diseño central compuesto (28_BB RSM-DCC: puntos del cubo, axiales y centrales, en unidades codificadas).
    alfa: «rotable» (2^(k/4)), «caras» (1) o un número. Con 2 bloques: cubo y centros del cubo en el bloque 1;
    estrella y sus centros en el bloque 2 [GENERAL]. Devuelve filas {coded, tipo, bloque}."""
    if not 2 <= k <= 6: raise ValueError("El diseño central compuesto se arma para 2 a 6 factores.")
    a = alfa_rotable(k) if alfa == "rotable" else 1.0 if alfa == "caras" else float(alfa)
    if bloques == 2: cc, ce = CENTROS_CCD[k]
    else: cc, ce = CENTROS_CCD_1B[k], 0
    if centros_cubo is not None: cc = centros_cubo
    if centros_estrella is not None: ce = centros_estrella
    filas = []
    for _ in range(replicas):
        for p in itertools.product([-1, 1], repeat=k):
            filas.append({"coded": list(reversed(p)), "tipo": 1, "bloque": 1})          # orden estándar: A varía más rápido
        filas += [{"coded": [0.0] * k, "tipo": 0, "bloque": 1} for _ in range(cc)]
        bq = 2 if bloques == 2 else 1
        for i in range(k):
            for s in (-a, a):
                v = [0.0] * k; v[i] = s; filas.append({"coded": v, "tipo": -1, "bloque": bq})
        filas += [{"coded": [0.0] * k, "tipo": 0, "bloque": bq} for _ in range(ce)]
    return filas, a


def diseno_box_behnken(k, centros=None, replicas=1):
    """Box-Behnken [GENERAL; no está en la base]: pares de factores en ±1 con el resto en 0, más centros. 3 a 7 factores."""
    if not 3 <= k <= 7: raise ValueError("Box-Behnken se arma para 3 a 7 factores.")
    c = CENTROS_BB[k] if centros is None else centros
    filas = []
    for _ in range(replicas):
        for i, j in itertools.combinations(range(k), 2):
            for si, sj in itertools.product([-1, 1], repeat=2):
                v = [0.0] * k; v[i], v[j] = si, sj; filas.append({"coded": v, "tipo": 2, "bloque": 1})
        filas += [{"coded": [0.0] * k, "tipo": 0, "bloque": 1} for _ in range(c)]
    return filas, 1.0


def diseno_factorial(k, centros=0, replicas=1):
    """Factorial completo 2^k con puntos centrales (18_GB FACT-DISEÑO-GENERAL; 28_BB RSM-PUNTOS-CENTRALES)."""
    if not 2 <= k <= 7: raise ValueError("El factorial completo se arma para 2 a 7 factores.")
    filas = []
    for _ in range(replicas):
        filas += [{"coded": list(reversed(p)), "tipo": 1, "bloque": 1} for p in itertools.product([-1, 1], repeat=k)]
    filas += [{"coded": [0.0] * k, "tipo": 0, "bloque": 1} for _ in range(centros)]
    return filas, 1.0


def aleatorizar(n, semilla=None):
    orden = list(range(n)); random.Random(semilla).shuffle(orden); return orden


def a_original(coded, bajo, alto):
    return [(b + a) / 2 + c * (a - b) / 2 for c, b, a in zip(coded, bajo, alto)]


NOMBRE_PUNTO = {1: "punto del cubo", -1: "punto axial", 0: "punto central", 2: "punto de arista (Box-Behnken)"}


def puntos_fuera(filas, bajos, altos, limites, tol=1e-9):
    """Región autorizada (Entrega 3, Decisión 5): puntos del diseño, en unidades reales, que quedan fuera de [mínimo, máximo] seguros de algún
    factor. filas: salida de diseno_*; limites: [(mínimo, máximo)] por factor. Devuelve [(número de corrida estándar, tipo de punto, índice del factor,
    valor real)] en orden de corrida estándar; vacío si todo punto está dentro. Incluye los puntos axiales."""
    fuera = []
    for i, f in enumerate(filas, 1):
        for q, v in enumerate(a_original(f["coded"], bajos, altos)):
            lo, hi = limites[q]
            if v < lo - tol * max(1.0, abs(lo)) or v > hi + tol * max(1.0, abs(hi)): fuera.append((i, f["tipo"], q, v))
    return fuera


def a_codificado(orig, bajo, alto):
    return [(o - (b + a) / 2) / ((a - b) / 2) for o, b, a in zip(orig, bajo, alto)]


# ---------------- modelo ----------------
MODELOS = {"lineal": "Lineal", "lineal_cuadrados": "Lineal + cuadrados", "lineal_interacciones": "Lineal + interacciones",
           "cuadratico": "Cuadrático completo"}


def terminos(nombres, modelo="cuadratico", excluir=()):
    """Términos del modelo en el orden de Minitab: lineales, cuadrados, interacciones de dos factores.
    Cada término es una tupla de índices: (i,) lineal, (i, i) cuadrado, (i, j) interacción.
    Jerarquía: si queda un cuadrado o una interacción, su término lineal no se quita (RSM-PRUEBAS-2DO-ORDEN).
    Devuelve (términos, nombres de los lineales que se conservaron por jerarquía, nombres a excluir no reconocidos)."""
    k = len(nombres)
    t = [(i,) for i in range(k)]
    if modelo in ("lineal_cuadrados", "cuadratico"): t += [(i, i) for i in range(k)]
    if modelo in ("lineal_interacciones", "cuadratico"): t += list(itertools.combinations(range(k), 2))
    norm = lambda x: x.replace(" ", "").replace("×", "*").lower()
    exc = {norm(e) for e in excluir if e.strip()}
    todos = {norm(nombre_termino(x, nombres)) for x in t} | {norm(f"{nombres[b]}*{nombres[a]}") for a, b in itertools.combinations(range(k), 2)}
    desconocidos = [e for e in excluir if e.strip() and norm(e) not in todos]
    def quitado(x):
        n1 = norm(nombre_termino(x, nombres))
        return n1 in exc or (len(x) == 2 and norm(f"{nombres[x[1]]}*{nombres[x[0]]}") in exc)
    pedidos = [x for x in t if not quitado(x)]
    retenidos = []
    for x in t:
        if quitado(x) and len(x) == 1 and any(len(y) == 2 and x[0] in y for y in pedidos):
            pedidos.append(x); retenidos.append(nombres[x[0]])
    orden = lambda x: (0 if len(x) == 1 else 1 if x[0] == x[1] else 2, x)
    return sorted(pedidos, key=orden), retenidos, desconocidos


def nombre_termino(t, nombres):
    if len(t) == 1: return nombres[t[0]]
    return f"{nombres[t[0]]}*{nombres[t[1]]}"


def grupo(t): return "Lineal" if len(t) == 1 else "Cuadrado" if t[0] == t[1] else "Interacción de 2 factores"


def matriz(X, ts):
    X = np.asarray(X, float)
    return np.column_stack([X[:, t[0]] if len(t) == 1 else X[:, t[0]] * X[:, t[1]] for t in ts]) if ts else np.empty((len(X), 0))


def _sse(A, y):
    b = np.linalg.lstsq(A, y, rcond=None)[0]; e = y - A @ b
    return float(e @ e)


def ajustar_superficie(Xc, y, nombres, ts, bloques=None, curvatura=None, alfa=0.05):
    """Ajusta y = b0 + Σ b·términos en unidades codificadas, con efecto de bloque opcional (codificación de efectos,
    suma cero) y término de curvatura opcional (indicador de punto central, para el factorial con centros).
    ANOVA por grupos con suma de cuadrados ajustada (extra, 27_BB REG-SUMAS-EXTRAS); falta de ajuste y error puro
    (27_BB REG-FALTA-AJUSTE) agrupando corridas con la misma combinación de factores y bloque."""
    from . import regresion as R
    Xc = np.asarray(Xc, float); y = np.asarray(y, float); n = len(y)
    cols, nombres_c, grupos_c = [], [], []
    if bloques is not None:
        niveles = sorted(set(bloques), key=str)
        if len(niveles) > 1:
            ult = niveles[-1]
            for b in niveles[:-1]:
                cols.append([1.0 if v == b else (-1.0 if v == ult else 0.0) for v in bloques]); nombres_c.append(f"Bloque {b}"); grupos_c.append("Bloques")
    for t in ts:
        cols.append(matriz(Xc, [t])[:, 0].tolist()); nombres_c.append(nombre_termino(t, nombres)); grupos_c.append(grupo(t))
    if curvatura is not None:
        cols.append([1.0 if c else 0.0 for c in curvatura]); nombres_c.append("Curvatura (puntos centrales)"); grupos_c.append("Curvatura")
    M = np.column_stack(cols) if cols else np.empty((n, 0))
    m = R.ajustar(M, y, nombres_c, alfa)
    A = np.column_stack([np.ones(n), M]); sse = m["sce"]; mce = m["mce"]
    anova = []
    if bloques is not None and "Bloques" in grupos_c:
        anova.append(_fila_grupo("Bloques", A, y, [i + 1 for i, g in enumerate(grupos_c) if g == "Bloques"], sse, mce, m["gl_e"]))
    idx_mod = [i + 1 for i, g in enumerate(grupos_c) if g != "Bloques"]
    anova.append(_fila_grupo("Modelo", A, y, idx_mod, sse, mce, m["gl_e"]))
    for g in ("Lineal", "Cuadrado", "Interacción de 2 factores", "Curvatura"):
        idx = [i + 1 for i, gg in enumerate(grupos_c) if gg == g]
        if idx: anova.append(dict(_fila_grupo(g, A, y, idx, sse, mce, m["gl_e"]), sub=True))
    for i, nm in enumerate(nombres_c):
        if grupos_c[i] != "Bloques":
            anova.append(dict(_fila_grupo(nm, A, y, [i + 1], sse, mce, m["gl_e"]), sub=2))
    # falta de ajuste
    clave = [tuple(np.round(Xc[r], 9)) + ((bloques[r],) if bloques is not None else ()) for r in range(n)]
    gr = {}
    for r, c in enumerate(clave): gr.setdefault(c, []).append(y[r])
    sspe = sum(sum((v - sum(g) / len(g)) ** 2 for v in g) for g in gr.values()); glpe = sum(len(g) - 1 for g in gr.values())
    lof = None
    if glpe > 0 and m["gl_e"] - glpe > 0:
        sslof = sse - sspe; gllof = m["gl_e"] - glpe
        f = (sslof / gllof) / (sspe / glpe) if sspe > 0 else float("inf")
        lof = {"ss": sslof, "gl": gllof, "ms": sslof / gllof, "f": f, "p": float(st.f.sf(f, gllof, glpe)) if sspe > 0 else 0.0,
               "f_tablas": float(st.f.ppf(1 - alfa, gllof, glpe)), "pe": {"ss": sspe, "gl": glpe, "ms": sspe / glpe}}
    return {"modelo": m, "nombres": nombres_c, "grupos": grupos_c, "anova": anova, "lof": lof, "ts": ts, "n": n,
            "con_bloques": bloques is not None and "Bloques" in grupos_c, "con_curvatura": curvatura is not None}


def _fila_grupo(nombre, A, y, idx, sse, mce, gl_e):
    red = np.delete(A, idx, axis=1)
    ss = _sse(red, y) - sse; gl = len(idx); ms = ss / gl
    f = ms / mce if mce > 0 else float("inf")
    return {"fuente": nombre, "gl": gl, "ss": ss, "ms": ms, "f": f, "p": float(st.f.sf(f, gl, gl_e))}


def coeficientes_modelo(sup):
    """b0, vector b (lineales) y matriz B (cuadrática simétrica) en unidades codificadas, sin bloques ni curvatura."""
    k = max([t[-1] for t in sup["ts"]], default=-1) + 1
    coef = {c["termino"]: c["coef"] for c in sup["modelo"]["coef"]}
    b0 = coef["Constante"]; b = np.zeros(k); B = np.zeros((k, k))
    for t, nm in zip(sup["ts"], [c for c, g in zip(sup["nombres"], sup["grupos"]) if g not in ("Bloques", "Curvatura")]):
        v = coef[nm]
        if len(t) == 1: b[t[0]] = v
        elif t[0] == t[1]: B[t[0], t[0]] = v
        else: B[t[0], t[1]] = B[t[1], t[0]] = v / 2
    return b0, b, B


def predecir_codificado(modelo, xc):
    """modelo = (b0, b, B). ŷ = b0 + x'b + x'Bx."""
    b0, b, B = modelo; x = np.asarray(xc, float)
    return float(b0 + x @ b + x @ B @ x)


def punto_estacionario(b0, b, B):
    """[BASE] RSM-PUNTO-ESTACIONARIO; análisis canónico [GENERAL]: xs = -½·B⁻¹·b; los valores propios de B indican
    máximo (todos negativos), mínimo (todos positivos) o punto silla (signos mezclados)."""
    if not np.any(B): return None
    try:
        xs = -0.5 * np.linalg.solve(B, b)
    except np.linalg.LinAlgError:
        return None
    ev = np.linalg.eigvalsh(B)
    tipo = "máximo" if np.all(ev < 0) else "mínimo" if np.all(ev > 0) else "punto silla"
    return {"x": xs.tolist(), "y": float(b0 + 0.5 * xs @ b), "valores_propios": ev.tolist(), "tipo": tipo}


def ascenso(b, pasos=5, maximizar=True, base=None):
    """[BASE] RSM-ASCENSO: el factor con mayor |b| avanza ΔXi = 1 (codificado); los demás ΔXj = bj·ΔXi/bi.
    Para minimizar se cambian los signos de las b."""
    b = np.asarray(b, float) * (1 if maximizar else -1)
    i = int(np.argmax(np.abs(b)))
    if b[i] == 0: return None, []
    delta = b / abs(b[i])
    base = np.zeros(len(b)) if base is None else np.asarray(base, float)
    return i, [(base + s * delta).tolist() for s in range(0, pasos + 1)]


# ---------------- deseabilidad y optimizador ----------------
def deseabilidad(y, meta, inferior=None, objetivo=None, superior=None, peso=1.0):
    """[GENERAL] Derringer y Suich (la que usa el optimizador de respuesta de Minitab): maximizar, minimizar u objetivo."""
    if meta == "max":
        if y <= inferior: return 0.0
        if y >= objetivo: return 1.0
        return ((y - inferior) / (objetivo - inferior)) ** peso
    if meta == "min":
        if y <= objetivo: return 1.0
        if y >= superior: return 0.0
        return ((superior - y) / (superior - objetivo)) ** peso
    if y < inferior or y > superior: return 0.0
    if y <= objetivo: return ((y - inferior) / (objetivo - inferior)) ** peso if objetivo > inferior else 1.0
    return ((superior - y) / (superior - objetivo)) ** peso if superior > objetivo else 1.0


def optimizar(respuestas, k, limite, semilla=0):
    """Busca la combinación de factores (codificados, dentro de ±limite) que maximiza la deseabilidad compuesta
    D = (Π di^ri)^(1/Σri). respuestas: [{modelo: (b0,b,B), meta, inferior, objetivo, superior, peso, importancia}]."""
    def D(x):
        ds, rs = [], []
        for r in respuestas:
            y = predecir_codificado(r["modelo"], x)
            ds.append(deseabilidad(y, r["meta"], r.get("inferior"), r.get("objetivo"), r.get("superior"), r.get("peso", 1.0)))
            rs.append(r.get("importancia", 1.0))
        if any(d <= 0 for d in ds): return 0.0, ds
        return math.exp(sum(ri * math.log(d) for d, ri in zip(ds, rs)) / sum(rs)), ds

    # suavizado: si D = 0, guiar con la distancia al rango aceptable de la primera respuesta en falla
    def objetivo_neg(x):
        d, _ = D(x)
        if d > 0: return -d
        pen = 0.0
        for r in respuestas:
            y = predecir_codificado(r["modelo"], x)
            if r["meta"] == "max": pen += max(0.0, r["inferior"] - y)
            elif r["meta"] == "min": pen += max(0.0, y - r["superior"])
            else: pen += max(0.0, r["inferior"] - y) + max(0.0, y - r["superior"])
        return pen * 1e3
    lim = [(-limite, limite)] * k
    res = optimize.differential_evolution(objetivo_neg, lim, seed=semilla, tol=1e-10, polish=True, maxiter=400)
    x = np.clip(res.x, -limite, limite)
    d, ds = D(x)
    return {"x": x.tolist(), "D": d, "d": ds, "y": [predecir_codificado(r["modelo"], x) for r in respuestas]}


# ---------------- fraccionados (26_BB_DOE_FRACCIONADOS) ----------------
LETRAS = "ABCDEFGHJ"
# Generadores de máxima resolución para 2^(k-p). [BASE] 2^(4-1) con D = ABC (FRAC-CONSTRUCCION) y resoluciones III, IV y V de 2^(3-1),
# 2^(4-1) y 2^(5-1) (FRAC-RESOLUCION). [GENERAL] el resto de la tabla (Montgomery, tabla 8.14).
GENERADORES = {(3, 1): ["AB"], (4, 1): ["ABC"], (5, 1): ["ABCD"], (5, 2): ["AB", "AC"], (6, 1): ["ABCDE"], (6, 2): ["ABC", "BCD"],
               (6, 3): ["AB", "AC", "BC"], (7, 1): ["ABCDEF"], (7, 2): ["ABCD", "ABDE"], (7, 3): ["ABC", "BCD", "ACD"], (7, 4): ["AB", "AC", "BC", "ABC"]}


def _mult(a, b): return "".join(sorted(set(a) ^ set(b)))


def relacion_definidora(k, p, gens=None):
    """Palabras de la relación definidora I = ... (todas las combinaciones de los generadores)."""
    gens = gens or GENERADORES[(k, p)]
    base = [_mult(LETRAS[k - p + i], g) for i, g in enumerate(gens)]
    palabras = set()
    for r in range(1, len(base) + 1):
        for comb in itertools.combinations(base, r):
            w = ""
            for x in comb: w = _mult(w, x)
            palabras.add(w)
    return sorted(palabras, key=lambda w: (len(w), w))


def resolucion(k, p, gens=None):
    """FRAC-RESOLUCION: longitud de la palabra más corta de la relación definidora."""
    return min(len(w) for w in relacion_definidora(k, p, gens)) if p else None


def alias(efecto, palabras):
    """Efectos confundidos con «efecto»: efecto × cada palabra de la relación definidora."""
    return sorted({_mult(efecto, w) for w in palabras} - {""}, key=lambda w: (len(w), w))


def diseno_fraccionado(k, p, signo=1, centros=0, replicas=1, gens=None):
    """2^(k-p): factorial completo de los k-p factores base y columnas generadas como productos (FRAC-CONSTRUCCION).
    signo = -1 usa la fracción alterna (ej. D = -ABC, como el ejemplo del curso)."""
    if p == 0: return diseno_factorial(k, centros, replicas)
    if (k, p) not in GENERADORES and gens is None: raise ValueError(f"No hay generadores definidos para 2^({k}-{p}).")
    gens = gens or GENERADORES[(k, p)]; kb = k - p
    filas = []
    for _ in range(replicas):
        for comb in itertools.product([-1, 1], repeat=kb):
            base = list(reversed(comb)); fila = base[:]
            for g in gens: fila.append(signo * int(np.prod([base[LETRAS.index(c)] for c in g])))
            filas.append({"coded": fila, "tipo": 1, "bloque": 1})
    filas += [{"coded": [0.0] * k, "tipo": 0, "bloque": 1} for _ in range(centros)]
    return filas, 1.0


def lenth(efectos):
    """Seudo error estándar de Lenth (1989) para factoriales sin réplicas, como usa Minitab: s0 = 1.5·mediana|e|;
    PSE = 1.5·mediana(|e| < 2.5·s0); grados de libertad = m/3. [GENERAL, no respaldado por la base]."""
    e = np.abs(np.asarray(efectos, float)); s0 = 1.5 * np.median(e)
    pse = 1.5 * np.median(e[e < 2.5 * s0]) if np.any(e < 2.5 * s0) else s0
    return float(pse), len(e) / 3
