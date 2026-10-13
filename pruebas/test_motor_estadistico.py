"""Etapa motor estadístico: E1 (resultado reproducible), E3 (SPC), E4 (capacidad) y E6 (correlación y regresión).
Verificación contra la base (27_BB, 19_GB, 16_GB) y contra el libro de estadística descriptiva con Minitab."""
import math, random
import numpy as np
import pytest
from app.api import Api
from app.modulos import regresion as R, estadistica as E, capacidad as C
from test_modulos import SINT


@pytest.fixture
def api():
    a = Api(); a.pegar(-1, 0, SINT); return a


def ok(api, mid, p):
    r = api.ejecutar_modulo(mid, p)
    assert r["error"] is None, r["sesion"][0]["texto"]
    return r["resultado"]


def textos(res): return " ".join(b.get("texto", "") for b in res["bloques"])


# ---------- verificación contra la base y los libros ----------
def test_regresion_ejemplo_dureza_temperatura():
    # 27_BB REG-EJ-SIMPLE a REG-CORRELACION: n=15, Σx=1,818, Σy=641, Σxy=77,062, Σx²=222,678, Σy²=27,589
    r = R.simple_desde_sumas(15, 1818, 641, 77062, 222678, 27589, x0=112)
    assert round(r["b1"], 4) == -0.2684 and round(r["b0"], 2) == 75.27
    assert round(r["sct"], 3) == 196.933 and round(r["scr"], 2) == 168.37 and round(r["sce"], 2) == 28.56
    assert round(r["f"], 2) == 76.63 and round(r["t_b1"], 2) == -8.75 and round(r["t_b0"], 2) == 20.14
    assert [round(v, 4) for v in r["ic_b1"]] == [-0.3347, -0.2022] and [round(v, 2) for v in r["ic_b0"]] == [67.20, 83.34]
    assert [round(v, 2) for v in r["ip"]] == [41.84, 48.57] and round(r["pred"], 3) == 45.203
    assert round(r["r2"], 3) == 0.855 and round(r["r"], 3) == -0.925 and round(r["s"], 5) == 1.48229   # S de Minitab del curso


def test_motor_matricial_coincide_con_formulas_del_curso():
    random.seed(4)                                                      # sintéticos
    x = [random.uniform(100, 140) for _ in range(15)]; y = [75 - 0.27 * v + random.gauss(0, 1.5) for v in x]
    m = R.ajustar([[v] for v in x], y, ["x"])
    s = R.simple_desde_sumas(15, sum(x), sum(y), sum(a * b for a, b in zip(x, y)), sum(a * a for a in x), sum(b * b for b in y), x0=120)
    assert math.isclose(m["coef"][1]["coef"], s["b1"]) and math.isclose(m["coef"][0]["coef"], s["b0"])
    assert math.isclose(m["r2"], s["r2"]) and math.isclose(m["f"], s["f"]) and math.isclose(m["coef"][1]["t"], s["t_b1"])
    q = R.predecir(m, [120])
    assert all(math.isclose(a, b) for a, b in zip(q["ip"], s["ip"]))
    assert math.isclose(m["r2_aj"], 1 - (1 - m["r2"]) * 14 / 13)      # REG-R2-AJUSTADO


def test_regresion_multiple_contra_numpy_y_vif():
    rng = np.random.default_rng(5)                                      # sintéticos
    X = rng.normal(size=(30, 3)); X[:, 2] = X[:, 0] * 0.9 + rng.normal(scale=0.3, size=30)
    y = 2 + X @ np.array([1.5, -0.7, 0.4]) + rng.normal(scale=0.5, size=30)
    m = R.ajustar(X, y, ["a", "b", "c"])
    b = np.linalg.lstsq(np.column_stack([np.ones(30), X]), y, rcond=None)[0]
    assert np.allclose([c["coef"] for c in m["coef"]], b)
    assert m["coef"][1]["vif"] > 3 and m["coef"][2]["vif"] < 2
    h = np.diag(np.column_stack([np.ones(30), X]) @ m["xtx_inv"] @ np.column_stack([np.ones(30), X]).T)
    assert np.allclose(m["h"], h) and math.isclose(sum(m["h"]), 4)


def test_correlacion_prueba_t_del_curso():
    # REG-PRUEBA-R: t = r·raíz(n-2)/raíz(1-r²) = -8.75 con la r del ejemplo sin redondear (con r = -0.925 daría -8.78)
    r, n = R.simple_desde_sumas(15, 1818, 641, 77062, 222678, 27589)["r"], 15
    assert round(r * math.sqrt(n - 2) / math.sqrt(1 - r * r), 2) == -8.75
    x = [1, 2, 3, 4, 5, 6]; y = [2.1, 3.9, 6.2, 7.8, 10.1, 12.2]
    p = R.pearson(x, y)
    assert math.isclose(p["r"], float(np.corrcoef(x, y)[0, 1])) and p["prueba"] == "t"


def test_cuartiles_libro_descriptiva_minitab():
    # Vinasco, Estadística descriptiva con Minitab, 3.3.2.1: posición (n+1)p; Q1 = 26.675, Q3 = 37.60, RI = 10.93.
    # El OCR del libro perdió un mes; el único valor compatible con Q3 = 37.60 es 38.0 (repetido).
    datos = [13.0, 20.6, 25.6, 29.9, 30.55, 33.5, 35.1, 36.2, 36.4, 38.0, 39.3, 38.0]
    o = sorted(datos)
    assert round(E.cuartil(o, 0.25), 3) == 26.675 and round(E.cuartil(o, 0.75), 2) == 37.60
    assert round(E.cuartil(o, 0.75) - E.cuartil(o, 0.25), 2) == 10.93 or round(E.cuartil(o, 0.75) - E.cuartil(o, 0.25), 3) == 10.925


def test_sigma_combinada():
    # Industrial Statistics with Minitab, 14.6.2: la interna es la raíz de la media de las varianzas (sin insesgar)
    g = [[1, 2, 3, 4], [2, 4, 5, 7], [0, 1, 3, 4]]
    v = [np.var(s, ddof=1) for s in g]
    assert math.isclose(C.sigma_combinada(g, insesgar=False), math.sqrt(sum(v) / 3))
    assert C.sigma_combinada(g) > C.sigma_combinada(g, insesgar=False)
    assert math.isclose(C.cpm([9, 10, 11], 7, 13, 10), 1.0)


# ---------- E1: resultado reproducible ----------
def test_definicion_por_nombre_y_repetir(api):
    r = ok(api, "BOXPLOT", {"y": 4, "grupo": 2})
    assert r["definicion"]["columnas"] == {"y": "tiempo", "grupo": "condicion"}
    api.insertar_columna(0)                                             # las posiciones cambian
    api.editar(0, 5, "99")                                              # dato nuevo en «tiempo»
    r2 = api.repetir_resultado(r["uid"])
    assert r2["error"] is None and r2["resultado"]["definicion"]["columnas"]["y"] == "tiempo"
    assert sum(int(f[1]) for f in r2["resultado"]["bloques"][1]["filas"]) == 40
    api.renombrar(5, "otro")
    assert api.repetir_resultado(r["uid"])["error"] == "columnas"


def test_texto_para_copiar_y_redaccion(api):
    r = ok(api, "DISTRIB", {"y": 4})
    t = api.texto_resultado(r["uid"])
    assert "Estadísticos" in t and "\t" in t
    assert "no permiten rechazar la normalidad" in textos(r) or "se rechaza la normalidad" in textos(r)
    assert "se asume que los datos siguen" not in textos(r)


def test_descriptivos_completos(api):
    api.editar(3, 4, "abc")
    r = ok(api, "ESTADISTICOS", {"y": 4})
    cab, fila = r["bloques"][0]["cabeza"], r["bloques"][0]["filas"][0]
    d = dict(zip(cab, fila))
    assert d["N"] == "39" and d["N faltante"] == "1" and "Curtosis" in d and "CV (%)" in d


def test_anova_supuestos_e_interpretacion(api):
    r = ok(api, "ANOVA", {"y": 4, "factor": 2, "alfa": "0.05"})
    sup = next(b for b in r["bloques"] if b.get("titulo") == "Supuestos del análisis")
    assert len(sup["filas"]) == 3 and "Levene" in sup["filas"][1][1]


# ---------- E3, E4, E6 por el puente ----------
TODAS = [str(k) for k in range(1, 8)]


def test_spc_por_tipo(api):
    assert ok(api, "SPC", {"tipo": "imr", "y": 4, "pruebas": TODAS})["titulo"].startswith("Carta I-MR")
    r = ok(api, "SPC", {"tipo": "xr", "y": 4, "tam": "4", "pruebas": TODAS})
    assert "X̄-R" in r["titulo"] and r["bloques"][2]["filas"][0][0] == "Medias (X̄)"
    assert api.ejecutar_modulo("SPC", {"tipo": "xr", "y": 4, "tam": "7"})["error"] == "entrada"     # 40 no es múltiplo de 7
    a = Api(); a.pegar(-1, 0, "defectuosos\tn\tdefectos\n" + "\n".join(f"{3 + i % 4}\t{50 + 10 * (i % 3)}\t{i % 5}" for i in range(20)))
    assert ok(a, "SPC", {"tipo": "p", "y": 0, "ncol": 1, "pruebas": TODAS})["bloques"][2]["filas"][0][2] == "variable"
    assert ok(a, "SPC", {"tipo": "c", "y": 2, "pruebas": TODAS})
    assert a.ejecutar_modulo("SPC", {"tipo": "np", "y": 0, "ncol": 1})["error"] == "entrada"     # n variable


def test_spc_limites_historicos(api):
    r = ok(api, "SPC", {"tipo": "imr", "y": 4, "k": "20", "pruebas": ["1"]})
    assert any("primeros 20" in a for a in r["avisos"])


def test_capacidad(api):
    r = ok(api, "CAPACIDAD", {"y": 4, "tam": "4", "lie": "8", "lse": "18", "objetivo": "13", "metodo": "combinada", "resumen": True})
    t = r["bloques"][3] if r["bloques"][2]["tipo"] == "grafica" else r["bloques"][2]
    nombres = [f[0] for f in t["filas"]]
    assert "Cpk / Ppk" in nombres and "Cpm (con objetivo)" in nombres
    assert sum(1 for b in r["bloques"] if b["tipo"] == "grafica") == 2
    assert any("Proceso estable" in f[0] for f in next(b for b in r["bloques"] if b.get("titulo") == "Supuestos del análisis")["filas"])
    assert api.ejecutar_modulo("CAPACIDAD", {"y": 4, "lie": "20", "lse": "10"})["error"] == "entrada"


def test_correlacion_y_regresion(api):
    a = Api()
    rng = random.Random(9)
    filas = [(t, round(75 - 0.27 * t + rng.gauss(0, 1.5), 2), round(rng.uniform(0, 1), 3)) for t in range(100, 145, 3)]
    a.pegar(-1, 0, "temperatura\tdureza\truido\n" + "\n".join("\t".join(map(str, f)) for f in filas))
    r = ok(a, "CORREL", {"vars": [0, 1, 2], "spearman": True})
    assert len(next(b for b in r["bloques"] if b.get("titulo") == "Correlaciones")["filas"]) == 3 and "causa y efecto" in textos(r)
    r = ok(a, "REGRESION", {"y": 1, "xs": [0], "grado": "1", "x0": "112", "alfa": "0.05"})
    assert any(b.get("texto", "").startswith("Ecuación: dureza =") for b in r["bloques"]) and any(b.get("titulo") == "Predicción" for b in r["bloques"])
    r = ok(a, "REGRESION", {"y": 1, "xs": [0, 2], "x0": "112; 0.5"})
    assert len(next(b for b in r["bloques"] if b.get("titulo") == "Coeficientes")["filas"]) == 3
    assert a.ejecutar_modulo("REGRESION", {"y": 1, "xs": [1]})["error"] == "entrada"
    r = ok(a, "REGRESION", {"y": 1, "xs": [0], "grado": "2"})
    assert "grado 2" in r["titulo"] and r["definicion"]["columnas"]["xs"] == ["temperatura"]
