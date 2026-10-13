"""Verificación del motor de superficies de respuesta.
Estructura del diseño y del modelo: contra la salida de Minitab de Industrial Statistics with Minitab, cap. 28
(4 factores, DCC en 2 bloques, 30 corridas): errores estándar / S, grados de libertad y falta de ajuste.
Cálculos: contra funciones cuadráticas conocidas (datos SINTÉTICOS sin ruido) y contra 28_BB RSM-ASCENSO."""
import math, random
import numpy as np
import pytest
from app.modulos import doe as D

NOMBRES = ["T", "Co1", "Co2", "rpm"]


def ccd_libro():
    filas, a = D.diseno_ccd(4, "rotable", bloques=2)
    return filas, a


def test_estructura_del_dcc_de_4_factores():
    filas, a = ccd_libro()
    assert len(filas) == 30 and a == 2.0
    assert sum(f["tipo"] == 1 for f in filas) == 16 and sum(f["tipo"] == -1 for f in filas) == 8 and sum(f["tipo"] == 0 for f in filas) == 6
    assert [f["bloque"] for f in filas].count(1) == 20


def _ajuste(filas, ts, y=None, bloques=True):
    X = [f["coded"] for f in filas]
    y = y if y is not None else [random.Random(i).gauss(10, 1) for i in range(len(filas))]
    return D.ajustar_superficie(X, y, NOMBRES, ts, [f["bloque"] for f in filas] if bloques else None)


def _se_sobre_s(sup):
    m = sup["modelo"]; return {c["termino"]: c["ee"] / m["s"] for c in m["coef"]}


def test_errores_estandar_relativos_como_minitab():
    filas, _ = ccd_libro()
    ts, _, _ = D.terminos(NOMBRES, "cuadratico")
    sup = _ajuste(filas, ts)
    r = _se_sobre_s(sup)
    # Minitab (cap. 28.2, modelo completo con bloque): S = 0.888594; SE Constante 0.3673, Bloque 0.1721, lineal 0.1814,
    # cuadrado 0.1697, interacción 0.2221
    s = 0.888594
    assert round(r["Constante"] * s, 4) == 0.3673 and round(r["Bloque 1"] * s, 4) == 0.1721
    assert round(r["T"] * s, 4) == 0.1814 and round(r["T*T"] * s, 4) == 0.1697 and round(r["T*Co1"] * s, 4) == 0.2221
    m = sup["modelo"]
    assert m["gl_e"] == 14 and sup["lof"]["gl"] == 10 and sup["lof"]["pe"]["gl"] == 4      # ANOVA del libro
    assert [a["gl"] for a in sup["anova"][:5]] == [1, 14, 4, 4, 6]


def test_modelos_reducidos_como_minitab():
    filas, _ = ccd_libro()
    ts, _, _ = D.terminos(NOMBRES, "lineal_cuadrados")
    r = _se_sobre_s(_ajuste(filas, ts, bloques=False))
    s = 0.801385                                       # sin interacciones ni bloque
    assert round(r["Constante"] * s, 4) == 0.3272 and round(r["T"] * s, 4) == 0.1636 and round(r["T*T"] * s, 4) == 0.1530
    ts, ret, _ = D.terminos(NOMBRES, "lineal_cuadrados", ["rpm", "rpm*rpm", "Co1*Co1", "Co2*Co2"])
    assert [D.nombre_termino(t, NOMBRES) for t in ts] == ["T", "Co1", "Co2", "T*T"] and ret == []
    r = _se_sobre_s(_ajuste(filas, ts, bloques=False))
    s = 0.786644                                       # modelo final del libro
    assert round(r["Constante"] * s, 4) == 0.1854 and round(r["T"] * s, 4) == 0.1606 and round(r["T*T"] * s, 4) == 0.1466


def test_jerarquia_no_quita_lineal_con_cuadrado():
    ts, ret, desc = D.terminos(NOMBRES, "cuadratico", ["T", "Co1*T", "xyz"])
    nombres = [D.nombre_termino(t, NOMBRES) for t in ts]
    assert "T" in nombres and ret == ["T"] and "T*Co1" not in nombres and desc == ["xyz"]


def test_recupera_cuadratica_exacta_y_punto_estacionario():
    filas, a = D.diseno_ccd(2, "rotable")
    X = np.array([f["coded"] for f in filas])
    f = lambda x: 50 + 3 * x[0] - 2 * x[1] - 4 * x[0] ** 2 - 3 * x[1] ** 2 + 1.5 * x[0] * x[1]      # sintética
    y = [f(x) for x in X]
    ts, _, _ = D.terminos(["A", "B"], "cuadratico")
    sup = D.ajustar_superficie(X, y, ["A", "B"], ts)
    b0, b, B = D.coeficientes_modelo(sup)
    assert math.isclose(b0, 50, abs_tol=1e-9) and np.allclose(b, [3, -2]) and np.allclose(B, [[-4, 0.75], [0.75, -3]])
    ps = D.punto_estacionario(b0, b, B)
    xs = np.linalg.solve(np.array([[-8, 1.5], [1.5, -6]]), [-3, 2])           # gradiente = 0
    assert np.allclose(ps["x"], xs) and ps["tipo"] == "máximo" and math.isclose(ps["y"], f(xs))
    opt = D.optimizar([{"modelo": (b0, b, B), "meta": "max", "inferior": 40, "objetivo": 60}], 2, a)
    assert np.allclose(opt["x"], xs, atol=1e-4) and 0 < opt["D"] < 1
    opt = D.optimizar([{"modelo": (b0, b, B), "meta": "objetivo", "inferior": 40, "objetivo": 45, "superior": 50}], 2, a)
    assert abs(opt["y"][0] - 45) < 1e-3 and opt["D"] > 0.999


def test_deseabilidad():
    assert D.deseabilidad(5, "max", 0, 10) == 0.5 and D.deseabilidad(12, "max", 0, 10) == 1 and D.deseabilidad(-1, "max", 0, 10) == 0
    assert D.deseabilidad(5, "min", objetivo=0, superior=10, peso=2) == 0.25
    assert D.deseabilidad(7.5, "objetivo", 5, 10, 15) == 0.5 and D.deseabilidad(16, "objetivo", 5, 10, 15) == 0


def test_ascenso_ejemplo_helicoptero():
    # 28_BB RSM-ASCENSO: Tiempo = 189.94 + 23.31 Alas - 8.94 Cuerpo; ΔX1 = 1, ΔX2 = -0.3835; con Alas 2-3 y Cuerpo 2-3:
    # 1 Delta: Alas 3.000, Cuerpo 2.308 (el curso escribe 2.308 con ΔO2 = -0.192)
    i, pasos = D.ascenso([23.31, -8.94], pasos=3)
    assert i == 0 and round(pasos[1][1], 4) == -0.3835
    orig = [D.a_original(p, [2, 2], [3, 3]) for p in pasos]
    assert [round(o[0], 3) for o in orig] == [2.5, 3.0, 3.5, 4.0] and round(orig[1][1], 3) == 2.308 and round(orig[3][1], 3) == 1.925


def test_falta_de_ajuste_detecta_curvatura():
    filas, _ = D.diseno_factorial(2, centros=4)
    rng = random.Random(3)
    y = [10 + 2 * f["coded"][0] + (3 if f["tipo"] == 0 else 0) + rng.gauss(0, 0.1) for f in filas]   # centros más altos
    ts, _, _ = D.terminos(["A", "B"], "lineal_interacciones")
    sup = D.ajustar_superficie([f["coded"] for f in filas], y, ["A", "B"], ts, curvatura=[f["tipo"] == 0 for f in filas])
    curv = next(a for a in sup["anova"] if a["fuente"] == "Curvatura")
    assert curv["p"] < 0.001
    sup = D.ajustar_superficie([f["coded"] for f in filas], y, ["A", "B"], ts)
    assert sup["lof"]["p"] < 0.001


def test_box_behnken_y_factorial():
    f, _ = D.diseno_box_behnken(3); assert len(f) == 15
    f, _ = D.diseno_factorial(3, centros=3); assert len(f) == 11
    assert D.a_codificado(D.a_original([1, -1, 0.5], [10, 0, 2], [20, 4, 6]), [10, 0, 2], [20, 4, 6]) == [1, -1, 0.5]
