"""Motor de control estadístico de procesos (SPC). Funciones puras: reciben números y devuelven límites,
puntos y violaciones. Fuente principal: 19_GB_CONTROLAR (SPC-TIPOS-CARTA, SPC-CONSTANTES, SPC-PATRONES,
SPC-CARTAS-VARIABLE, SPC-CARTAS-ATRIBUTO, SPC-RECALCULO).

Constantes: A2, D3 y D4 para n = 2 a 10 y 2.66 / 3.27 de la I-mR, tal como los da la base. d2 (para la sigma
interna) no tiene valores en la base [GENERAL]; una prueba verifica que es coherente con A2 = 3/(d2·raíz(n)). Las de la carta X-S (c4, A3, B3, B4) no están
en la base [GENERAL].
"""
import math

# d2 y d3 por tamaño de subgrupo [GENERAL; reproducen A2, D3 y D4 de 19_GB SPC-CONSTANTES]
D2 = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534, 7: 2.704, 8: 2.847, 9: 2.970, 10: 3.078,
      11: 3.173, 12: 3.258, 13: 3.336, 14: 3.407, 15: 3.472, 16: 3.532, 17: 3.588, 18: 3.640, 19: 3.689, 20: 3.735,
      21: 3.778, 22: 3.819, 23: 3.858, 24: 3.895, 25: 3.931}
D3T = {2: 0.853, 3: 0.888, 4: 0.880, 5: 0.864, 6: 0.848, 7: 0.833, 8: 0.820, 9: 0.808, 10: 0.797}

PRUEBAS = {
    1: "1 punto fuera de los límites de control",
    2: "2 de 3 puntos consecutivos en la zona A o más allá (mismo lado)",
    3: "4 de 5 puntos consecutivos en la zona B o más allá (mismo lado)",
    4: "8 puntos consecutivos del mismo lado de la línea central (racha)",
    5: "6 o más puntos consecutivos sin cambio de dirección (tendencia)",
    6: "15 puntos consecutivos en la zona C (estratificación)",
    7: "8 puntos consecutivos a ambos lados sin ninguno en la zona C (mezcla)",
}


# [BASE] 19_GB SPC-CONSTANTES: valores del curso (se usan tal cual para reproducir sus ejemplos)
A2 = {2: 1.881, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
D4 = {2: 3.27, 3: 2.57, 4: 2.28, 5: 2.11, 6: 2.00, 7: 1.92, 8: 1.86, 9: 1.82, 10: 1.78}
D3 = {2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.08, 8: 0.14, 9: 0.18, 10: 0.22}
E2_IMR = 2.66      # 19_GB SPC-CONSTANTES, carta I-mR


def a2(n): return A2[n]
def d4(n): return D4[n]
def d3(n): return D3[n]


def c4(n): return math.sqrt(2 / (n - 1)) * math.exp(math.lgamma(n / 2) - math.lgamma((n - 1) / 2))
def a3(n): return 3 / (c4(n) * math.sqrt(n))
def b4(n): return 1 + 3 * math.sqrt(1 - c4(n) ** 2) / c4(n)
def b3(n): return max(0.0, 1 - 3 * math.sqrt(1 - c4(n) ** 2) / c4(n))


def _media(x): return sum(x) / len(x)


def _desv(x):
    m = _media(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))


def _base(vals, k):
    """Datos para calcular los límites: los primeros k (límites históricos o de una fase) o todos."""
    return vals[:k] if k else vals


# ---------------- cartas de variable ----------------
def carta_imr(x, k=None):
    """[BASE] SPC-CONSTANTES, carta I-mR: UCL/LCL(x) = x̄ ± 2.66·R̄s; UCL(Rs) = 3.27·R̄s; LCL(Rs) no aplica.
    Sigma interna = R̄s / d2(2) [GENERAL], que se usa para las zonas de las pruebas."""
    if len(x) < 3: raise ValueError("La carta I-MR necesita al menos 3 valores.")
    mr = [abs(x[i] - x[i - 1]) for i in range(1, len(x))]
    xb = _media(_base(x, k)); mrb = _media(_base(mr, k - 1 if k else None))
    s = mrb / D2[2]
    return [
        {"nombre": "Individuales", "puntos": list(x), "cl": [xb] * len(x), "ucl": [xb + E2_IMR * mrb] * len(x),
         "lcl": [xb - E2_IMR * mrb] * len(x), "sigma": [E2_IMR * mrb / 3] * len(x), "pruebas": True},
        {"nombre": "Rango móvil", "puntos": [None] + mr, "cl": [mrb] * len(x), "ucl": [d4(2) * mrb] * len(x),
         "lcl": [0.0] * len(x), "sigma": None, "pruebas": False}], {"sigma_dentro": s, "mr_barra": mrb, "media": xb}


def carta_xr(subgrupos, k=None):
    """[BASE] SPC-CONSTANTES, carta X-R: UCL/LCL(x̄) = x̿ ± A2·R̄; UCL(R) = D4·R̄; LCL(R) = D3·R̄. n de 2 a 10."""
    n = _tam_constante(subgrupos)
    if not 2 <= n <= 10: raise ValueError("La carta X̄-R es para subgrupos de 2 a 10; con más de 10 usa X̄-S (SPC-PROCEDIMIENTO).")
    xb = [_media(g) for g in subgrupos]; r = [max(g) - min(g) for g in subgrupos]
    xbb = _media(_base(xb, k)); rb = _media(_base(r, k))
    m = len(subgrupos); s = rb / D2[n]
    return [
        {"nombre": "Medias (X̄)", "puntos": xb, "cl": [xbb] * m, "ucl": [xbb + a2(n) * rb] * m, "lcl": [xbb - a2(n) * rb] * m,
         "sigma": [a2(n) * rb / 3] * m, "pruebas": True},
        {"nombre": "Rangos (R)", "puntos": r, "cl": [rb] * m, "ucl": [d4(n) * rb] * m, "lcl": [d3(n) * rb] * m,
         "sigma": None, "pruebas": False}], {"sigma_dentro": s, "r_barra": rb, "media": xbb, "n": n}


def carta_xs(subgrupos, k=None):
    """Carta X-S (19_GB SPC-CARTAS-VARIABLE: para n > 10). Constantes c4, A3, B3, B4 [GENERAL]."""
    n = _tam_constante(subgrupos)
    if n < 2: raise ValueError("La carta X̄-S necesita subgrupos de 2 o más.")
    xb = [_media(g) for g in subgrupos]; sd = [_desv(g) for g in subgrupos]
    xbb = _media(_base(xb, k)); sb = _media(_base(sd, k))
    m = len(subgrupos); s = sb / c4(n)
    return [
        {"nombre": "Medias (X̄)", "puntos": xb, "cl": [xbb] * m, "ucl": [xbb + a3(n) * sb] * m, "lcl": [xbb - a3(n) * sb] * m,
         "sigma": [s / math.sqrt(n)] * m, "pruebas": True},
        {"nombre": "Desviaciones (S)", "puntos": sd, "cl": [sb] * m, "ucl": [b4(n) * sb] * m, "lcl": [b3(n) * sb] * m,
         "sigma": None, "pruebas": False}], {"sigma_dentro": s, "s_barra": sb, "media": xbb, "n": n}


def _tam_constante(subgrupos):
    tams = {len(g) for g in subgrupos}
    if len(tams) != 1: raise ValueError("Todos los subgrupos deben tener el mismo tamaño.")
    if len(subgrupos) < 2: raise ValueError("Se necesitan al menos 2 subgrupos.")
    return tams.pop()


# ---------------- cartas de atributo ----------------
def carta_p(defectuosos, tamanos, k=None):
    """[BASE] SPC-CARTAS-ATRIBUTO, carta p: p̄ = ΣX/Σn; UCL/LCL = p̄ ± 3·raíz(p̄(1-p̄)/n), límites variables si n varía;
    un límite inferior negativo se toma como 0 (mismo criterio que la carta c del curso)."""
    _validar_conteos(defectuosos, tamanos, True)
    pb = sum(_base(defectuosos, k)) / sum(_base(tamanos, k))
    ps = [x / n for x, n in zip(defectuosos, tamanos)]
    sig = [math.sqrt(pb * (1 - pb) / n) for n in tamanos]
    return [{"nombre": "Proporción defectuosa (p)", "puntos": ps, "cl": [pb] * len(ps), "ucl": [min(1.0, pb + 3 * s) for s in sig],
             "lcl": [max(0.0, pb - 3 * s) for s in sig], "sigma": sig, "pruebas": True}], {"p_barra": pb}


def carta_np(defectuosos, n, k=None):
    """[BASE] carta np (n constante): np̄ = ΣX/k; UCL/LCL = np̄ ± 3·raíz(np̄(1-p̄)), p̄ = np̄/n."""
    _validar_conteos(defectuosos, [n] * len(defectuosos), True)
    npb = _media(_base(defectuosos, k)); pb = npb / n
    s = math.sqrt(npb * (1 - pb)); m = len(defectuosos)
    return [{"nombre": "Número de defectuosos (np)", "puntos": list(defectuosos), "cl": [npb] * m, "ucl": [npb + 3 * s] * m,
             "lcl": [max(0.0, npb - 3 * s)] * m, "sigma": [s] * m, "pruebas": True}], {"np_barra": npb, "p_barra": pb}


def carta_c(defectos, k=None):
    """[BASE] carta c: c̄ = promedio de defectos; UCL/LCL = c̄ ± 3·raíz(c̄); LCL negativo se ajusta a 0."""
    _validar_conteos(defectos, None, False)
    cb = _media(_base(defectos, k)); s = math.sqrt(cb); m = len(defectos)
    return [{"nombre": "Número de defectos (c)", "puntos": list(defectos), "cl": [cb] * m, "ucl": [cb + 3 * s] * m,
             "lcl": [max(0.0, cb - 3 * s)] * m, "sigma": [s] * m, "pruebas": True}], {"c_barra": cb}


def carta_u(defectos, tamanos, k=None):
    """[BASE] carta u: ū = Σc/Σn; UCL/LCL = ū ± 3·raíz(ū/n), límites variables si n varía."""
    _validar_conteos(defectos, tamanos, False)
    ub = sum(_base(defectos, k)) / sum(_base(tamanos, k))
    us = [c / n for c, n in zip(defectos, tamanos)]
    sig = [math.sqrt(ub / n) for n in tamanos]
    return [{"nombre": "Defectos por unidad (u)", "puntos": us, "cl": [ub] * len(us), "ucl": [ub + 3 * s for s in sig],
             "lcl": [max(0.0, ub - 3 * s) for s in sig], "sigma": sig, "pruebas": True}], {"u_barra": ub}


def _validar_conteos(x, n, defectuosos):
    if len(x) < 2: raise ValueError("Se necesitan al menos 2 subgrupos.")
    if any(v < 0 or not float(v).is_integer() for v in x): raise ValueError("Los conteos deben ser enteros de 0 o más.")
    if n is not None:
        if any(t <= 0 for t in n): raise ValueError("Los tamaños de muestra deben ser mayores a cero.")
        if defectuosos and any(v > t for v, t in zip(x, n)): raise ValueError("Hay subgrupos con más defectuosos que piezas inspeccionadas.")


# ---------------- pruebas de causas especiales ----------------
def pruebas(carta, activas=tuple(PRUEBAS)):
    """[BASE] 19_GB SPC-PATRONES: zonas A, B y C (tercios entre la línea central y el límite); inestabilidad
    (pruebas 1 a 4), tendencia (5), estratificación (6) y mezcla (7). Cada violación se marca en el último punto
    de la secuencia que la cumple. Devuelve {índice: [pruebas]}."""
    pts, cl, ucl, lcl, sg = carta["puntos"], carta["cl"], carta["ucl"], carta["lcl"], carta["sigma"]
    out = {}

    def marcar(i, t): out.setdefault(i, []).append(t) if t not in out.get(i, []) else None

    z = []
    for i, v in enumerate(pts):
        if v is None or not sg or sg[i] in (None, 0): z.append(None); continue
        z.append((v - cl[i]) / sg[i])
    idx = [i for i, v in enumerate(pts) if v is not None]
    for i in idx:
        if 1 in activas and (pts[i] > ucl[i] + 1e-12 or pts[i] < lcl[i] - 1e-12): marcar(i, 1)
    if not sg: return out
    for pos, i in enumerate(idx):
        ventana = lambda m: [idx[q] for q in range(pos - m + 1, pos + 1)] if pos - m + 1 >= 0 else None
        for t, m, req, lim in ((2, 3, 2, 2), (3, 5, 4, 1)):
            w = ventana(m)
            if t in activas and w:
                for lado in (1, -1):
                    if sum(1 for q in w if z[q] is not None and lado * z[q] > lim) >= req and lado * z[i] > lim: marcar(i, t)
        w = ventana(8)
        if 4 in activas and w and (all(z[q] > 0 for q in w) or all(z[q] < 0 for q in w)): marcar(i, 4)
        w = ventana(6)
        if 5 in activas and w:
            d = [pts[w[q + 1]] - pts[w[q]] for q in range(5)]
            if all(x > 0 for x in d) or all(x < 0 for x in d): marcar(i, 5)
        w = ventana(15)
        if 6 in activas and w and all(abs(z[q]) < 1 for q in w): marcar(i, 6)
        w = ventana(8)
        if 7 in activas and w and all(abs(z[q]) > 1 for q in w) and any(z[q] > 0 for q in w) and any(z[q] < 0 for q in w): marcar(i, 7)
    return out
