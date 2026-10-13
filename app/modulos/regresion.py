"""Correlación y regresión lineal (mínimos cuadrados). Fuente: 27_BB_REGRESION y 17_GB_ANALIZAR (CORR-*).
Funciones puras; la interfaz está en relaciones.py."""
import math
import numpy as np
from scipy import stats as st


def simple_desde_sumas(n, sx, sy, sxy, sxx_raw, syy_raw, alfa=0.05, x0=None):
    """[BASE] 27_BB REG-ESTIMACION, REG-SIGNIFICADO, REG-PRUEBAS-PARAMETROS, REG-IC, REG-PREDICCION, REG-R2 y
    REG-CORRELACION, con las sumas tal como las usa el curso. Sirve para verificar el motor general."""
    sxy_c = sxy - sx * sy / n; sxx = sxx_raw - sx ** 2 / n; syy = syy_raw - sy ** 2 / n
    b1 = sxy_c / sxx; b0 = sy / n - b1 * sx / n
    scr = b1 * sxy_c; sce = syy - scr; mce = sce / (n - 2)
    t = st.t.ppf(1 - alfa / 2, n - 2); xm = sx / n
    se_b1 = math.sqrt(mce / sxx); se_b0 = math.sqrt(mce * (1 / n + xm ** 2 / sxx))
    r = {"b0": b0, "b1": b1, "sct": syy, "scr": scr, "sce": sce, "mce": mce, "f": scr / mce, "t_b1": b1 / se_b1, "t_b0": b0 / se_b0,
         "ic_b1": (b1 - t * se_b1, b1 + t * se_b1), "ic_b0": (b0 - t * se_b0, b0 + t * se_b0), "r2": scr / syy,
         "r": sxy_c / math.sqrt(syy * sxx), "s": math.sqrt(mce)}
    if x0 is not None:
        y0 = b0 + b1 * x0
        r["pred"] = y0
        r["ip"] = (y0 - t * math.sqrt(mce * (1 + 1 / n + (x0 - xm) ** 2 / sxx)), y0 + t * math.sqrt(mce * (1 + 1 / n + (x0 - xm) ** 2 / sxx)))
        r["ic_media"] = (y0 - t * math.sqrt(mce * (1 / n + (x0 - xm) ** 2 / sxx)), y0 + t * math.sqrt(mce * (1 / n + (x0 - xm) ** 2 / sxx)))
    return r


def pearson(x, y):
    """[BASE] REG-CORRELACION y REG-PRUEBA-R: r = Sxy/raíz(Sxx·Syy); n < 50: t = r·raíz(n-2)/raíz(1-r²);
    n >= 50: z = r·raíz(n-1). El valor p bilateral se calcula con t o z [GENERAL: la base usa valores de tablas]."""
    n = len(x); mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y)); sxx = sum((a - mx) ** 2 for a in x); syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0: raise ValueError("Una de las variables no varía; la correlación no está definida.")
    r = sxy / math.sqrt(sxx * syy)
    if n < 50:
        est = r * math.sqrt(n - 2) / math.sqrt(max(1e-300, 1 - r * r)); p = 2 * st.t.sf(abs(est), n - 2); prueba = "t"
    else:
        est = r * math.sqrt(n - 1); p = 2 * st.norm.sf(abs(est)); prueba = "z"
    # IC de Fisher [GENERAL]
    ic = None
    if n > 3 and abs(r) < 1:
        z = math.atanh(r); h = 1.96 / math.sqrt(n - 3); ic = (math.tanh(z - h), math.tanh(z + h))
    return {"r": r, "n": n, "estadistico": est, "prueba": prueba, "p": p, "ic": ic}


def fuerza(r):
    """[BASE] 17_GB CORR-INTERPRETACION (Western Electric)."""
    a = abs(r)
    if a >= 0.85: return "lineal fuerte"
    if a > 0.30: return "lineal moderada o débil"
    return "lineal prácticamente inexistente"


def ajustar(X, y, nombres, alfa=0.05, constante=True):
    """Regresión lineal por mínimos cuadrados en forma matricial (27_BB REG-MULTIPLE-MATRICIAL: b = (X'X)^-1 X'y).
    Devuelve coeficientes con EE, t, p e IC; ANOVA; R², R² ajustado (REG-R2-AJUSTADO), S; PRESS y R² de
    predicción, Cook y Durbin-Watson (REG-COOK-PRESS-DW); VIF (REG-MULTICOLINEALIDAD); residuos y apalancamiento."""
    X = np.asarray(X, float); y = np.asarray(y, float); n = len(y)
    A = np.column_stack([np.ones(n), X]) if constante else X
    p = A.shape[1]
    if n <= p: raise ValueError(f"Hay {n} observaciones para {p} coeficientes; se necesitan más datos que coeficientes.")
    if np.linalg.matrix_rank(A) < p: raise ValueError("Los predictores son linealmente dependientes (uno es combinación de otros).")
    xtx_inv = np.linalg.inv(A.T @ A)
    b = xtx_inv @ A.T @ y
    ajus = A @ b; e = y - ajus
    sce = float(e @ e); gl_e = n - p; mce = sce / gl_e
    sct = float(((y - y.mean()) ** 2).sum()) if constante else float((y ** 2).sum())
    scr = sct - sce; gl_r = p - 1 if constante else p
    ee = np.sqrt(np.diag(xtx_inv) * mce); t = b / ee
    pv = 2 * st.t.sf(np.abs(t), gl_e); tc = st.t.ppf(1 - alfa / 2, gl_e)
    h = np.einsum("ij,jk,ik->i", A, xtx_inv, A)
    press = float(((e / (1 - h)) ** 2).sum()) if np.all(h < 1) else float("nan")
    with np.errstate(divide="ignore", invalid="ignore"):          # apalancamiento 1 (punto que define solo un término)
        ok = h < 1 - 1e-12
        cook = np.where(ok, (e ** 2 / (p * mce)) * h / np.where(ok, (1 - h) ** 2, 1), np.nan) if mce > 0 else np.full(n, np.nan)
        est_res = np.where(ok, e / np.sqrt(np.where(ok, mce * (1 - h), 1)), np.nan) if mce > 0 else np.full(n, np.nan)
    dw = float((np.diff(e) ** 2).sum() / sce) if sce > 0 else float("nan")
    vif = []
    Xs = A[:, 1:] if constante else A
    for k in range(Xs.shape[1]):
        if Xs.shape[1] < 2: vif.append(None); break
        otros = np.delete(Xs, k, axis=1)
        B = np.column_stack([np.ones(n), otros])
        coef = np.linalg.lstsq(B, Xs[:, k], rcond=None)[0]
        res = Xs[:, k] - B @ coef; tot = ((Xs[:, k] - Xs[:, k].mean()) ** 2).sum()
        r2k = 1 - (res @ res) / tot if tot > 0 else 1.0
        vif.append(1 / (1 - r2k) if r2k < 1 else float("inf"))
    nombres_c = (["Constante"] if constante else []) + list(nombres)
    coef = [{"termino": nm, "coef": float(b[i]), "ee": float(ee[i]), "t": float(t[i]), "p": float(pv[i]),
             "ic": (float(b[i] - tc * ee[i]), float(b[i] + tc * ee[i])),
             "vif": (vif[i - 1] if constante and i > 0 and vif else (vif[i] if not constante and vif else None))}
            for i, nm in enumerate(nombres_c)]
    f = (scr / gl_r) / mce if gl_r > 0 and mce > 0 else float("inf")
    return {"coef": coef, "n": n, "p": p, "gl_r": gl_r, "gl_e": gl_e, "scr": scr, "sce": sce, "sct": sct, "mce": mce,
            "f": f, "p_f": float(st.f.sf(f, gl_r, gl_e)), "f_tablas": float(st.f.ppf(1 - alfa, gl_r, gl_e)),
            "r2": scr / sct if sct > 0 else float("nan"), "r2_aj": 1 - (sce / gl_e) / (sct / (n - 1)) if constante and sct > 0 else float("nan"),
            "r2_pred": 1 - press / sct if sct > 0 and press == press else float("nan"), "s": math.sqrt(mce), "press": press,
            "dw": dw, "ajustados": ajus.tolist(), "residuos": e.tolist(), "est_res": est_res.tolist(), "h": h.tolist(),
            "cook": cook.tolist(), "xtx_inv": xtx_inv, "b": b, "constante": constante, "alfa": alfa, "tc": float(tc)}


def predecir(modelo, x0):
    """[BASE] REG-PREDICCION generalizado: ŷ0 ± t·raíz(MCE·(1 + x0'(X'X)^-1 x0)) (individual) y sin el 1 (media)."""
    v = np.concatenate([[1.0], np.asarray(x0, float)]) if modelo["constante"] else np.asarray(x0, float)
    y0 = float(v @ modelo["b"]); q = float(v @ modelo["xtx_inv"] @ v); m = modelo["mce"]; t = modelo["tc"]
    return {"pred": y0, "ic_media": (y0 - t * math.sqrt(m * q), y0 + t * math.sqrt(m * q)),
            "ip": (y0 - t * math.sqrt(m * (1 + q)), y0 + t * math.sqrt(m * (1 + q)))}
