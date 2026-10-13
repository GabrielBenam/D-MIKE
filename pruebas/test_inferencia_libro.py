"""Verificación de la estadística inferencial contra salidas reales de Minitab (Industrial Statistics with Minitab, caps. 10 y 11, datos del
libro) y contra los ejemplos del curso (25_BB_DISTRIBUCIONES, 17_GB_ANALIZAR, 20_GB_TABLA_F)."""
import math
import pytest
from app.api import Api
from app.modulos.probabilidad import calcular


def corre(datos, mid, p):
    a = Api(); a.pegar(-1, 0, datos); r = a.ejecutar_modulo(mid, p)
    assert r["error"] is None, r["sesion"][0]["texto"]
    return {b["titulo"]: b for b in r["resultado"]["bloques"] if b["tipo"] == "tabla"}


def ic(txt): return [float(v) for v in txt.split(" a ")]


A = "24.3 25.6 26.7 22.7 24.8 23.8 25.9 26.4 25.8 25.4".split(); B = "24.4 21.5 25.1 22.8 25.2 23.5 22.2 23.5 23.3 24.7".split()


def test_t_dos_muestras_ejemplo_10_1():
    t = corre("A\tB\n" + "\n".join(f"{x}\t{y}" for x, y in zip(A, B)), "HIPOTESIS", {"tipo": "t2", "y": 0, "y2": 1, "h0": "0"})["Prueba"]["filas"][0]
    # Minitab: Estimate 1.520; 95% CI (0.350; 2.690); T-Value 2.74; P-Value 0.014; DF 17
    assert t[2] == "1.52" and round(float(t[3]), 2) == 2.74 and t[4] == "17" and t[5] == "0.014"
    assert [round(v, 3) for v in ic(t[6])] == [0.350, 2.690]


def test_t_pareada_ejemplo_10_2():
    ta, tb = "6.7 5.0 3.6 6.2 5.9 4.0 5.2 4.5 4.4 4.1".split(), "6.9 5.8 4.1 7.0 7.0 4.6 5.5 5.0 4.3 4.8".split()
    t = corre("A\tB\n" + "\n".join(f"{x}\t{y}" for x, y in zip(ta, tb)), "HIPOTESIS", {"tipo": "pareada", "y": 0, "y2": 1, "h0": "0"})["Prueba"]["filas"][0]
    # Minitab: T-Value -4.97; P-Value 0.001; 95% CI (-0.786; -0.294)
    assert round(float(t[2]), 2) == -4.97 and t[4] == "0.001" and [round(v, 3) for v in ic(t[5])] == [-0.786, -0.294]


def test_dos_proporciones_ejemplo_10_3():
    t = corre("x\n1", "HIPOTESIS", {"tipo": "p2", "x1": "33", "n1": "300", "x2": "22", "n2": "250", "h0": "0"})["Prueba"]["filas"][0]
    # Minitab: Z 0.86, P-Value 0.387; Fisher 0.476; CI (-0.0278678; 0.0718678)
    assert t[2] == "Z = 0.8647" and t[3] == "0.387" and t[4] == "0.476" and ic(t[5]) == [-0.0279, 0.0719]
    t = corre("x\n1", "HIPOTESIS", {"tipo": "p2", "x1": "33", "n1": "300", "x2": "22", "n2": "250", "h0": "0", "combinada": True})["Prueba"]
    assert "combinada" in t["cabeza"][3] and t["filas"][0][3] == "0.392"


DATOS_11_1 = "y\tg\n" + "\n".join(f"{v}\t{g}" for g, vs in (("A", [1.9, 1.8, 2.1, 1.8]), ("B", [1.6, 1.1, 1.3, 1.4, 1.1]), ("C", [1.3, 1.6, 1.8, 1.1, 1.5, 1.1])) for v in vs)


def test_anova_un_factor_y_tukey_ejemplo_11_1():
    t = corre(DATOS_11_1, "ANOVA", {"y": 0, "factor": 1, "alfa": "0.05"})["Tabla ANOVA"]["filas"]
    # Minitab: Factor 2 0.9000 0.4500 8.44 0.005; Error 12 0.6400 0.0533
    assert t[0][1:4] == ["2", "0.9", "0.45"] and round(float(t[0][4]), 2) == 8.44 and t[0][6] == "0.005" and t[1][3] == "0.0533"
    tk = corre(DATOS_11_1, "TUKEY", {"y": 0, "factor": 1, "alfa": "0.05"})["Diferencias por pares"]["filas"]
    # Minitab: B-A (-1.0130; -0.1870), C-A (-0.8974; -0.1026), C-B (-0.2728; 0.4728). Diferencia de 0.0003 por el cálculo del
    # cuantil del rango estudentizado (scipy exacto: q = 3.773; el de Minitab equivale a 3.770). Se acepta hasta 0.0005.
    esperado = {"B - A": (-1.0130, -0.1870), "C - A": (-0.8974, -0.1026), "C - B": (-0.2728, 0.4728)}
    for f in tk:
        lo, hi = ic(f[3]); assert abs(lo - esperado[f[0]][0]) < 5e-4 and abs(hi - esperado[f[0]][1]) < 5e-4


def test_anova_dos_factores_ejemplo_11_2():
    filas = ["7.3 7.0 7.0 6.5 7.6 6.2 6.5 6.4 7.2 6.3 5.5 6.0 6.7 6.1 6.5", "6.9 7.1 7.2 7.4 6.3 5.7 6.4 6.9 6.0 6.8 6.9 5.7 7.0 6.5 6.3",
             "7.9 6.8 7.8 7.3 6.9 6.4 6.9 6.4 7.2 7.2 6.6 6.2 6.3 6.5 7.0", "7.7 7.6 6.5 7.5 8.0 6.6 6.5 7.1 6.2 6.3 6.0 6.5 6.8 6.4 5.7"]
    d = "dureza\tpintura\tbandeja\n" + "\n".join(f"{x}\tP{k // 5 + 1}\tT{t}" for t, f in enumerate(filas, 1) for k, x in enumerate(f.split()))
    r = corre(d, "ANOVA2", {"y": 0, "a": 1, "b": 2, "interaccion": True})
    t = r["Análisis de varianza"]["filas"]
    # Minitab: Painting 2 8.0003 4.00017 20.01 0.000; Tray 3 0.9298 0.30994 1.55 0.214; Interaction 6 0.7957 0.13261 0.66 0.679;
    # Error 48 9.5960 0.19992; Total 59 19.3218; S = 0.4471, R-Sq = 50.34%, R-Sq(adj) = 38.95%
    assert [x[1] for x in t] == ["2", "3", "6", "48", "59"]
    assert [round(float(x[2]), 4) for x in t] == [8.0003, 0.9298, 0.7957, 9.596, 19.3218]
    assert [round(float(x[4]), 2) for x in t[:3]] == [20.01, 1.55, 0.66] and [x[6] for x in t[1:3]] == ["0.214", "0.679"]
    assert r["Resumen del modelo"]["filas"][0] == ["0.44712", "50.34%", "38.95%"]


@pytest.mark.parametrize("dist,a,b,calc,x,x2,prob,esperado,dec", [
    ("normal", 1.03, .0573, "acum", .9, None, None, .0116, 4),            # DIST-EJ-Z: 1.16%
    ("normal", 1.03, .0573, "mayor", 1.1, None, None, .1109, 4),          # DIST-EJ-Z: 11.10% (el curso redondea Z a 1.22)
    ("weibull", .5, 2000, "acum", 5000, None, None, .794259, 6),          # DIST-WEIBULL
    ("lognormal", 2.32, .2, "acum", 12, None, None, .795182, 6),          # DIST-LOGNORMAL
    ("lognormal", 2.323, 1.429, "mayor", 120, None, None, .0423, 4),      # DIST-IDENTIFICAR, ejemplo 2
    ("binomial", 500, .05, "puntual", 30, None, None, .0456, 4),          # DIST-BINOMIAL
    ("binomial", 500, .05, "acum", 30, None, None, .8691, 4),
    ("poisson", 3, None, "puntual", 5, None, None, .1008, 4),             # DIST-POISSON
    ("f", 2, 6, "inversa", None, None, .95, 5.14, 2),                     # 17_GB ANOVA-TIPOS: F(0.05; 2, 6) = 5.14
    ("normal", 0, 1, "inversa", None, None, .9999901, 4.27, 2),           # DIST-IDENTIFICAR: nivel sigma de largo plazo 4.27
])
def test_distribuciones_contra_el_curso(dist, a, b, calc, x, x2, prob, esperado, dec):
    v, formula, _ = calcular(dist, a, b, calc, x, x2, prob)
    assert round(v, dec) == esperado and formula != "—"


def test_formula_excel_y_modulo():
    v, f, _ = calcular("binomial", 500, .05, "acum", 30); assert f == "=DISTR.BINOM.N(30; 500; 0.05; VERDADERO)"
    v, f, _ = calcular("normal", 1.03, .0573, "mayor", 1.1); assert f == "=1-DISTR.NORM.N(1.1; 1.03; 0.0573; VERDADERO)"
    a = Api(); r = a.ejecutar_modulo("PROBABILIDAD", {"dist": "poisson", "a": "3", "calculo": "acum", "x": "5"})
    assert r["error"] is None and "0.916" in r["resultado"]["titulo"]
    assert a.ejecutar_modulo("PROBABILIDAD", {"dist": "normal", "a": "0", "b": "-1", "x": "1"})["error"] == "entrada"
    assert a.ejecutar_modulo("PROBABILIDAD", {"dist": "normal", "a": "0", "b": "1", "calculo": "entre", "x": "1", "x2": "0"})["error"] == "entrada"


def test_una_proporcion_ejemplo_9_2():
    # Minitab (libro, ej. 9.2): 17 de 200; IC 95% exacto (0.050296; 0.132605); con Ha p < 0.1: cota superior 0.124771, p = 0.285.
    # El valor p de dos colas del libro (0.487) es de una versión antigua de Minitab; la versión actual usa el método exacto de Blaker
    # (documentación de Minitab, «Methods and formulas for 1 Proportion»), que aquí coincide con el de mínima verosimilitud: 0.556.
    t = corre("x\n1", "HIPOTESIS", {"tipo": "p1", "x1": "17", "n1": "200", "h0": "0.1"})["Prueba"]["filas"][0]
    assert [round(v, 6) for v in ic(t[6])] == [0.050296, 0.132605] and t[4] == "0.556"
    t = corre("x\n1", "HIPOTESIS", {"tipo": "p1", "x1": "17", "n1": "200", "h0": "0.1", "alt": "<"})["Prueba"]["filas"][0]
    assert t[4] == "0.285" and round(float(t[6].split(" a ")[1]), 6) == 0.124771


def test_anova_dos_factores_baterias_del_curso():
    # 18_GB FACT-TAMANO-MUESTRA: 3 materiales × 3 temperaturas × 4 baterías; material, temperatura e interacción significativos.
    # Datos y sumas de cuadrados de Montgomery, Design and Analysis of Experiments, ejemplo 5.1 (fuente externa): SC 10683.72, 39118.72,
    # 9613.78, 18230.75; F 7.91, 28.97 y 3.56.
    d = {(1, 15): [130, 155, 74, 180], (1, 70): [34, 40, 80, 75], (1, 125): [20, 70, 82, 58], (2, 15): [150, 188, 159, 126], (2, 70): [136, 122, 106, 115],
         (2, 125): [25, 70, 58, 45], (3, 15): [138, 110, 168, 160], (3, 70): [174, 120, 150, 139], (3, 125): [96, 104, 82, 60]}
    datos = "vida\tmaterial\ttemp\n" + "\n".join(f"{v}\tM{m}\tT{t}" for (m, t), vs in d.items() for v in vs)
    t = corre(datos, "ANOVA2", {"y": 0, "a": 1, "b": 2, "interaccion": True})["Análisis de varianza"]["filas"]
    f = lambda x: float(x.replace(",", ""))
    assert [round(f(x[2]), 2) for x in t[:4]] == [10683.72, 39118.72, 9613.78, 18230.75]
    assert [round(f(x[4]), 2) for x in t[:3]] == [7.91, 28.97, 3.56] and all(float(x[6].replace("< ", "")) < .05 for x in t[:3])


def test_potencia_como_minitab():
    # t no central, como Power and Sample Size de Minitab: diferencia 1, sigma 1, potencia 0.8, dos colas, alfa 0.05:
    # 2 muestras → 17 por grupo (potencia real 0.807); 1 muestra → 10 (0.803).
    from app.modulos import inferencia as I
    assert I.n_para_potencia(1, 1, .05, .8, muestras=2) == 17 and round(I.potencia_t(17, 1, 1, .05, 2), 3) == .807
    assert I.n_para_potencia(1, 1, .05, .8, muestras=1) == 10 and round(I.potencia_t(10, 1, 1, .05, 1), 3) == .803
