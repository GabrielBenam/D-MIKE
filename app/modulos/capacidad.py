"""Capacidad de proceso (datos normales). Fuente: 16_GB_HISTOGRAMAS_CAPACIDAD_DESEMPENO (CAP-CP, CAP-CPK,
CAP-INTERPRETACION, CAP-LARGO-CORTO-PLAZO, CAP-NIVEL-SIGMA). Límites de ESPECIFICACIÓN (voz del cliente): no
son los límites de control de las cartas (voz del proceso)."""
import math
from scipy import stats as st


def indices(media, s_dentro, s_global, lie=None, lse=None):
    """[BASE] Cp = (LSE - LIE)/6s; Cpk = min[(x̄ - LIE)/3s, (LSE - x̄)/3s]; unilateral (SL - x̄)/3s.
    Cp/Cpk con la desviación interna (corto plazo); Pp/Ppk con la global (largo plazo).
    Nivel sigma: corto plazo = Cpk x 3, largo plazo = Ppk x 3 (CAP-NIVEL-SIGMA).
    PPM esperados con la distribución normal [GENERAL: la base da la tabla DPMO-sigma, no el cálculo]."""
    if lie is None and lse is None: raise ValueError("Indica al menos un límite de especificación.")
    if lie is not None and lse is not None and lie >= lse: raise ValueError("El LIE debe ser menor que el LSE.")
    r = {}
    for nombre, s in (("C", s_dentro), ("P", s_global)):
        u = (lse - media) / (3 * s) if lse is not None else None
        l = (media - lie) / (3 * s) if lie is not None else None
        r[f"{nombre}pu"], r[f"{nombre}pl"] = u, l
        r[f"{nombre}p"] = (lse - lie) / (6 * s) if lie is not None and lse is not None else None
        r[f"{nombre}pk"] = min(v for v in (u, l) if v is not None)
        ppm_inf = st.norm.cdf((lie - media) / s) * 1e6 if lie is not None else 0.0
        ppm_sup = st.norm.sf((lse - media) / s) * 1e6 if lse is not None else 0.0
        r[f"ppm_{nombre}"] = {"inf": ppm_inf, "sup": ppm_sup, "total": ppm_inf + ppm_sup}
    r["sigma_cp"] = 3 * r["Cpk"]; r["sigma_lp"] = 3 * r["Ppk"]
    return r


def ppm_observado(x, lie=None, lse=None):
    n = len(x)
    inf = sum(1 for v in x if lie is not None and v < lie) / n * 1e6
    sup = sum(1 for v in x if lse is not None and v > lse) / n * 1e6
    return {"inf": inf, "sup": sup, "total": inf + sup}


def clasificar(indice):
    """[BASE] CAP-INTERPRETACION: < 1 incapaz; 1 a 1.33 apenas capaz; > 1.33 capaz."""
    if indice is None: return "—"
    return "incapaz" if indice < 1 else "apenas capaz" if indice <= 1.33 else "capaz"


def sigma_combinada(subgrupos, insesgar=True):
    """Sigma interna por desviación estándar combinada: raíz(Σ(ni-1)si² / Σ(ni-1)), dividida entre c4(d+1)
    con d = Σ(ni-1) si se insesga. Es el método por omisión que describe Industrial Statistics with Minitab
    (cap. 14.5.2) [GENERAL: la base no fija el método]."""
    from .spc import c4
    d = sum(len(g) - 1 for g in subgrupos)
    if d <= 0: raise ValueError("Se necesitan subgrupos con más de un dato.")
    sp2 = sum((len(g) - 1) * (sum((v - sum(g) / len(g)) ** 2 for v in g) / (len(g) - 1)) for g in subgrupos if len(g) > 1) / d
    sp = math.sqrt(sp2)
    return sp / c4(d + 1) if insesgar else sp


def cpm(x, lie, lse, objetivo):
    """[GENERAL] Cpm (índice de Taguchi): min(T - LIE, LSE - T) / (3·raíz(Σ(x - T)²/(n - 1))). Según el libro de
    Minitab (cap. 14.5.3) se calcula como Cpk sustituyendo la media por el objetivo."""
    if objetivo is None or lie is None or lse is None: return None
    n = len(x); s_t = math.sqrt(sum((v - objetivo) ** 2 for v in x) / (n - 1))
    return min(objetivo - lie, lse - objetivo) / (3 * s_t) if s_t > 0 else None
