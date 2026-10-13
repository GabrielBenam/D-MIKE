"""Verificación de los cálculos contra los ejemplos resueltos de la base LSS (se cita archivo y sección).
Donde la base no trae los datos crudos, se verifica lo que sí trae y se contrasta con scipy."""
import math, random
import pytest
from scipy import stats as st
from app.modulos import estadistica as E


def test_descriptivos_calificaciones():
    # 15_GB_ESTADISTICA_Y_MUESTREO, EST-CENTRAL y EST-VARIABILIDAD
    d = E.descriptivos([64, 88, 66, 82, 68, 68, 70, 78, 76, 80, 90])
    assert round(d["media"], 1) == 75.5 and d["mediana"] == 76 and d["modas"] == [68]
    # El curso escribe s = 8.94 (truncado); el valor es 8.948 = raíz de 80.07, que sí coincide.
    assert d["rango"] == 26 and abs(d["desv"] - 8.94) < 0.01 and round(d["varianza"], 2) == 80.07


def test_muestra_discreta_logistics():
    # 15_GB, MUE-DISCRETA: N=400, p=0.09, d=0.01, z=1.64 -> 2,203 sin ajuste, n/N=5.51, ajustada 339
    r = E.tamano_muestra("discreto", 1.64, 0.01, p=0.09, N=400)
    assert r["n_sin_ajuste"] == 2203 and round(r["razon"], 2) == 5.51 and r["ajustado"] and r["n"] == 339


def test_muestra_continua_chemical():
    # 15_GB, MUE-CONTINUA: N=3,200, s=0.458, d=0.100, z=1.96 -> 81; frecuencia 480/81 = 5.93 min
    r = E.tamano_muestra("continuo", 1.96, 0.100, s=0.458, N=3200)
    assert r["n"] == 81 and not r["ajustado"] and round(480 / r["n"], 2) == 5.93


def test_anova_tornillos_f_y_p():
    # 17_GB_ANALIZAR, ANOVA-TIPOS: F=22.08, gl (2, 6), F tablas 5.14 (20_GB_TABLA_F), p=0.0017.
    # La base no trae las 9 mediciones: se verifica la parte de tablas y valor p con esos gl.
    assert round(st.f.ppf(0.95, 2, 6), 2) == 5.14
    assert round(st.f.sf(22.08, 2, 6), 4) == 0.0017


def test_anova_un_factor_contra_scipy():
    random.seed(1)  # datos sintéticos
    g = {"A": [random.gauss(10, 1) for _ in range(5)], "B": [random.gauss(11, 1) for _ in range(4)],
         "C": [random.gauss(12.5, 1) for _ in range(6)]}
    r = E.anova_un_factor(g)
    f, p = st.f_oneway(*g.values())
    assert math.isclose(r["tratamientos"]["f"], f) and math.isclose(r["tratamientos"]["p"], p)
    assert r["tratamientos"]["gl"] == 2 and r["error"]["gl"] == 12


def test_anova_bloque_contra_modelo_lineal():
    # Diseño 3 niveles x 4 bloques, una observación por celda (plantilla del curso, PL12). Sintético.
    import numpy as np
    random.seed(2)
    cel = {(i, j): [5 + i + 0.8 * j + random.gauss(0, 0.3)] for i in range(3) for j in range(4)}
    r = E.anova_bloque(cel)
    y = np.array([cel[(i, j)][0] for i in range(3) for j in range(4)])
    X = np.column_stack([np.ones(12)] + [[1.0 if i == k else 0 for i in range(3) for j in range(4)] for k in (1, 2)]
                        + [[1.0 if j == k else 0 for i in range(3) for j in range(4)] for k in (1, 2, 3)])
    sse = float(np.sum((y - X @ np.linalg.lstsq(X, y, rcond=None)[0]) ** 2))
    assert math.isclose(r["error"]["ss"], sse, rel_tol=1e-9) and r["error"]["gl"] == 6
    assert r["tratamientos"]["gl"] == 2 and r["bloque"]["gl"] == 3


def test_fuera_de_especificacion_tornillo():
    # 25_BB_DISTRIBUCIONES, DIST-EJ-Z: media 1.03, s 0.0573, LIE 0.9, LSE 1.1 -> ZI -2.27, ZS 1.22, total 12.26%
    r = E.fuera_de_especificacion(1.03, 0.0573, 0.9, 1.1)
    assert round(r["z_inf"], 2) == -2.27 and round(r["z_sup"], 2) == 1.22
    assert round(100 * r["p_inf"], 2) == 1.16 and round(100 * r["p_total"], 2) == 12.26


def test_nivel_sigma_manufacturera_quimica():
    # 25_BB, DIST-IDENTIFICAR ejemplo 1: media 25.53, s 0.1097, LIE 25, LSE 26 -> 7e-7, 9.2e-6, 4.27 y 5.77
    r = E.fuera_de_especificacion(25.53, 0.1097, 25.0, 26.0)
    assert round(r["p_inf"], 7) == 7e-7 and round(r["p_sup"], 7) == 9.2e-6
    assert round(r["sigma_lp"], 2) == 4.27 and round(r["sigma_cp"], 2) == 5.77


@pytest.mark.filterwarnings("ignore::FutureWarning")
def test_anderson_darling_estadistico_contra_scipy():
    random.seed(3); x = [random.gauss(0, 1) for _ in range(40)]  # sintéticos
    assert math.isclose(E.anderson_darling(x)["a2"], st.anderson(x).statistic, rel_tol=1e-6)
    assert E.anderson_darling(x)["p"] > 0.05
    y = [random.expovariate(1) ** 2 for _ in range(60)]
    assert E.anderson_darling(y)["p"] < 0.05


def test_caja_bigotes_y_atipicos():
    c = E.caja([1, 2, 3, 4, 5, 6, 7, 8, 30])
    assert c["mediana"] == 5 and c["q1"] == 2.5 and c["q3"] == 7.5 and c["atipicos"] == [30] and c["bigote_sup"] == 8


def test_corridas():
    r = E.corridas([1, 2, 3, 4, 5, 6, 7, 3, 2, 8, 1])
    assert r["tendencia_max"] == 7 and r["hay_tendencia"]
    r = E.corridas([5, 6, 5.5, 6.2, 5.8, 6.1, 6.3, 7, 8, 7.5, 9, 8.8, 9.1, 9.2, 1, 1])
    assert r["racha_max"] >= 8 and r["hay_racha"]


def test_pareto():
    r = E.pareto({"A": 50, "B": 30, "C": 15, "D": 3, "E": 2})
    assert [f["categoria"] for f in r["filas"]] == ["A", "B", "C", "Otros"] and r["filas"][-1]["conteo"] == 5
    assert r["filas"][2]["acum"] == 95.0


def test_msa_chelsea_footwear():
    # 14_GB_MEDIR, MED-RR-ATRIBUTO: Ben 90% consigo mismo y 70% contra el estándar (1 falso negativo,
    # 1 falso positivo y 1 muestra contradicha); Cynthia 100% y 100%. La base no trae las 10 calificaciones:
    # se reconstruye una tabla sintética coherente con esa descripción.
    ref = ["P", "P", "P", "P", "P", "F", "F", "F", "F", "F"]
    ben1 = ["P", "F", "P", "P", "P", "P", "F", "F", "F", "F"]
    ben2 = ["P", "F", "F", "P", "P", "P", "F", "F", "F", "F"]
    r = E.msa_atributos({"Ben": [ben1, ben2], "Cynthia": [ref, ref]}, ref, "P")
    b, c = r["evaluadores"]["Ben"], r["evaluadores"]["Cynthia"]
    assert b["consigo"]["pct"] == 90 and b["vs_ref"]["pct"] == 70
    assert (b["falso_negativo"], b["falso_positivo"], b["mixto"]) == (1, 1, 1)
    assert c["consigo"]["pct"] == 100 and c["vs_ref"]["pct"] == 100


def test_wilson_y_kappa():
    li, ls = E.wilson(9, 10)
    assert round(li, 4) == 0.5958 and round(ls, 4) == 0.9821
    assert E.kappa_fleiss([["a", "a"], ["b", "b"], ["a", "a"]]) == 1.0
