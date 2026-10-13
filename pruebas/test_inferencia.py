"""Inferencia (E7, E8, E10, E11). Verificación contra la base (MUE-DISCRETA, MUE-CONTINUA, DIST-TRANSFORMACION) y,
donde la base no da números, contra las funciones de referencia de scipy. Datos SINTÉTICOS."""
import math
import numpy as np
import pytest
from scipy import stats as st
from app.api import Api
from app.modulos import inferencia as I

rng = np.random.default_rng(12)
A = np.round(rng.normal(10, 2, 25), 3); B = np.round(rng.normal(11.5, 3, 30), 3)


def api_con(*cols, nombres=None):
    a = Api(); n = max(len(c) for c in cols); nombres = nombres or [f"c{k}" for k in range(len(cols))]
    a.pegar(-1, 0, "\t".join(nombres) + "\n" + "\n".join("\t".join(str(c[i]) if i < len(c) else "" for c in cols) for i in range(n))); return a


def prueba(res): return next(b for b in res["bloques"] if b.get("titulo") == "Prueba")


def test_base_tamano_de_muestra():
    assert I.n_proporcion(.09, .01, 1.64, 400) == (2203, 339)      # 15_GB MUE-DISCRETA (Logistics Company)
    assert I.n_media(.458, .1, 1.96, 3200) == (81, 81)               # 15_GB MUE-CONTINUA (Chemical Manufacturing)
    r = Api().ejecutar_modulo("POTENCIA", {"tipo": "prop", "conf": "90", "p": ".09", "d": ".01", "N": "400"})
    assert r["error"] is None and "339" in r["resultado"]["titulo"]


def test_base_box_cox_limites_transformados():
    r = I.fuera_transformado(1.624, .5380, .80, 5.60, .5)                 # 25_BB DIST-TRANSFORMACION
    assert [round(v, 3) for v in r["lim_t"]] == [.894, 2.366] and [round(v, 2) for v in r["z"]] == [-1.36, 1.38]
    assert round(r["p"][0], 4) == .0875 and round(r["p"][1], 4) == .0838 and round(r["total"], 4) == .1713
    r = I.fuera_transformado(.5, .1, 2, 4, -1)                            # λ negativo: los límites se invierten
    assert r["lim_t"][0] < r["lim_t"][1]


def test_box_cox_encuentra_raiz_cuadrada():
    x = (rng.normal(3, .5, 200)) ** 2
    lam, ic, red = I.boxcox_lambda(x)
    assert ic[0] < lam < ic[1] and red == .5
    a = api_con(np.round(x, 4)); res = a.ejecutar_modulo("BOXCOX", {"y": 0, "lie": "1", "lse": "20", "dest": "raiz"})["resultado"]
    assert res["datos"]["lambda"] == .5 and a.hoja.indice("raiz") is not None
    assert a.ejecutar_modulo("BOXCOX", {"y": 0, "usar": "valor"})["error"] == "entrada"


def test_t_y_z_contra_scipy():
    a = api_con(A, B)
    r = a.ejecutar_modulo("HIPOTESIS", {"tipo": "t1", "y": 0, "h0": "9"})["resultado"]
    ref = st.ttest_1samp(A, 9); assert prueba(r)["filas"][0][2] == f"{ref.statistic:.4f}".rstrip("0").rstrip(".") or abs(float(prueba(r)["filas"][0][2]) - ref.statistic) < 1e-3
    for iguales, ev in ((False, False), (True, True)):
        r = a.ejecutar_modulo("HIPOTESIS", {"tipo": "t2", "y": 0, "y2": 1, "iguales": iguales})["resultado"]
        ref = st.ttest_ind(A, B, equal_var=ev); assert abs(float(prueba(r)["filas"][0][3]) - ref.statistic) < 1e-3
    r = a.ejecutar_modulo("HIPOTESIS", {"tipo": "pareada", "y": 0, "y2": 1})["resultado"]
    ref = st.ttest_rel(A, B[:25]); assert abs(float(prueba(r)["filas"][0][2]) - ref.statistic) < 1e-3
    r = a.ejecutar_modulo("HIPOTESIS", {"tipo": "z1", "y": 0, "h0": "10", "sigma": "2", "alt": ">"})["resultado"]
    z = (A.mean() - 10) / (2 / 5); assert abs(float(prueba(r)["filas"][0][2]) - z) < 1e-3


def test_proporciones_y_varianzas():
    a = Api()
    r = a.ejecutar_modulo("HIPOTESIS", {"tipo": "p1", "x1": "18", "n1": "100", "h0": "0.1"})["resultado"]
    assert prueba(r)["filas"][0][4] == I.p_texto(st.binomtest(18, 100, .1).pvalue)
    r = a.ejecutar_modulo("HIPOTESIS", {"tipo": "p2", "x1": "30", "n1": "200", "x2": "45", "n2": "210"})["resultado"]
    p1, p2 = .15, 45 / 210; z = (p1 - p2) / math.sqrt(p1 * (1 - p1) / 200 + p2 * (1 - p2) / 210)     # por omisión, estimaciones separadas (Minitab)
    assert prueba(r)["filas"][0][2] == f"Z = {I.num(z, 4)}"
    r = a.ejecutar_modulo("HIPOTESIS", {"tipo": "p2", "x1": "30", "n1": "200", "x2": "45", "n2": "210", "combinada": True})["resultado"]
    pc = 75 / 410; z = (p1 - p2) / math.sqrt(pc * (1 - pc) * (1 / 200 + 1 / 210)); assert prueba(r)["filas"][0][2] == f"Z = {I.num(z, 4)}"
    b = api_con(A, B)
    r = b.ejecutar_modulo("HIPOTESIS", {"tipo": "v2", "y": 0, "y2": 1})["resultado"]
    assert abs(float(prueba(r)["filas"][1][1]) - st.levene(A, B, center="median").statistic) < 1e-3
    r = b.ejecutar_modulo("HIPOTESIS", {"tipo": "v1", "y": 0, "h0": "2"})["resultado"]
    assert abs(float(prueba(r)["filas"][0][2]) - 24 * np.var(A, ddof=1) / 4) < 1e-3
    assert a.ejecutar_modulo("HIPOTESIS", {"tipo": "p1", "x1": "120", "n1": "100", "h0": ".5"})["error"] == "entrada"


def test_anova2_balanceado_contra_formulas_clasicas():
    a_, b_, r_ = 3, 2, 4; y, fa, fb = [], [], []
    for i in range(a_):
        for j in range(b_):
            for k in range(r_): y.append(10 + i + 2 * j + (1.5 if (i, j) == (2, 1) else 0) + rng.normal(0, .5)); fa.append(f"A{i}"); fb.append(f"B{j}")
    r = I.anova2(y, fa, fb); y = np.array(y); g = y.mean()
    ma = [y[[k for k in range(len(y)) if fa[k] == f"A{i}"]].mean() for i in range(a_)]; mb = [y[[k for k in range(len(y)) if fb[k] == f"B{j}"]].mean() for j in range(b_)]
    ssa = b_ * r_ * sum((m - g) ** 2 for m in ma); ssb = a_ * r_ * sum((m - g) ** 2 for m in mb)
    mc = {(i, j): y[[k for k in range(len(y)) if fa[k] == f"A{i}" and fb[k] == f"B{j}"]].mean() for i in range(a_) for j in range(b_)}
    ssab = r_ * sum((mc[(i, j)] - ma[i] - mb[j] + g) ** 2 for i in range(a_) for j in range(b_))
    f = {x["fuente"]: x for x in r["filas"]}
    assert math.isclose(f["A"]["ss"], ssa) and math.isclose(f["B"]["ss"], ssb) and math.isclose(f["AB"]["ss"], ssab) and r["gle"] == 18
    api = api_con(np.round(y, 4), fa, fb, nombres=["y", "presion", "gas"])
    res = api.ejecutar_modulo("ANOVA2", {"y": 0, "a": 1, "b": 2})["resultado"]
    import json; assert "interacción" in json.dumps(res, ensure_ascii=False).lower()


def test_tukey_contra_scipy():
    g = {"A": list(rng.normal(10, 1, 6)), "B": list(rng.normal(12, 1, 6)), "C": list(rng.normal(10.3, 1, 8))}
    t = I.tukey(g); ref = st.tukey_hsd(*g.values())
    for pp in t["pares"]:
        i, j = "ABC".index(pp["par"][1]), "ABC".index(pp["par"][0])
        assert abs(pp["p"] - ref.pvalue[i, j]) < 2e-3
    assert t["letras"]["B"] != t["letras"]["A"][0] and t["letras"]["A"].strip() and t["letras"]["C"]


def test_identificacion_de_distribucion():
    x = np.round(np.random.default_rng(2).lognormal(2.3, .6, 60), 4)
    r = {d["nombre"]: d for d in I.identificar(x)}
    assert r["Lognormal"]["p"] > .05 and r["Normal"]["p"] < .05
    assert math.isclose(r["Lognormal"]["par"]["Ubicación"], np.mean(np.log(x)))
    a = api_con(x); res = a.ejecutar_modulo("DIST-ID", {"y": 0, "x0": "30"})["resultado"]
    assert "Lognormal" in res["bloques"][0]["texto"] and len(res["bloques"][1]["cabeza"]) == 5
    neg = api_con(np.round(rng.normal(0, 1, 30), 3)); res = neg.ejecutar_modulo("DIST-ID", {"y": 0})["resultado"]
    assert any("mayores que cero" in str(f) for f in res["bloques"][1]["filas"])


def test_potencia_t():
    assert abs(I.potencia_t(10, 1, 1, .05, 1) - .8031) < 5e-4                # referencia conocida (n = 10, d = 1)
    assert I.n_para_potencia(1, 1, .05, .8, 1) == 10
    r = Api().ejecutar_modulo("POTENCIA", {"tipo": "t2", "d": "1", "s": "1", "pot": ".8"})["resultado"]
    assert r["titulo"].startswith("n = 17 por grupo")


def test_no_parametricas_y_chi2():
    a = api_con(A, B, ["X" if i % 3 else "Y" for i in range(25)], nombres=["a", "b", "g"])
    for tipo, extra, ref in (("mann", {"y2": 1}, st.mannwhitneyu(A, B).pvalue), ("wilcoxon", {"h0": "9"}, st.wilcoxon(A - 9).pvalue),
                             ("signos", {"h0": "9"}, None), ("pareada", {"y2": 1}, st.wilcoxon(A - B[:25]).pvalue)):
        r = a.ejecutar_modulo("NOPARAM", {"tipo": tipo, "y": 0, **extra}); assert r["error"] is None, (tipo, r["sesion"][0]["texto"])
        if ref is not None: assert prueba(r["resultado"])["filas"][0][2] == I.p_texto(ref)
    assert a.ejecutar_modulo("NOPARAM", {"tipo": "kruskal", "y": 0, "grupo": 2})["error"] is None
    c = api_con(["A", "A", "B", "B", "A", "B"], ["si", "no", "si", "no", "no", "si"], [20, 30, 25, 15, 1, 4], nombres=["f", "c", "n"])
    r = c.ejecutar_modulo("CHI2", {"filas": 0, "cols": 1, "frec": 2})["resultado"]
    ref = st.chi2_contingency([[20, 31], [29, 15]], correction=False)
    assert abs(float(prueba(r)["filas"][0][1]) - ref[0]) < 1e-3
