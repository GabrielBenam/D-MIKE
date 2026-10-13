"""Gage R&R cruzado. Verificado contra las sumas de cuadrados y los resultados de Minitab publicados en
Industrial Statistics with Minitab (cap. 13, RR_CROSSED: 10 piezas, 3 evaluadores, 3 repeticiones, tolerancia 0.2)."""
import math, random
from app.api import Api
from app.modulos import msa_variable as M


def test_contra_minitab_del_libro():
    c = M.componentes(0.0025457, 0.0037278, 0.0011029, 0.0046340, 10, 3, 3, alfa_inter=0.25)
    assert not c["con_inter"] and round(c["p_inter"], 3) == 0.700
    assert [round(f[3], 7) for f in c["tabla"]][:2] == [0.0002829, 0.0018639] and round(c["tabla"][2][3], 7) == 0.0000735
    assert (round(c["v_grr"], 7), round(c["v_rep"], 7), round(c["v_repro"], 7), round(c["v_p"], 7), round(c["v_tot"], 7)) == (0.0001332, 0.0000735, 0.0000597, 0.0000233, 0.0001565)
    filas, ndc = M.resumen(c, tolerancia=0.2)
    f = {x["fuente"].strip(): x for x in filas}
    assert [round(f[k]["pct_contrib"], 2) for k in ("R&R total", "Repetibilidad", "Reproducibilidad", "Pieza a pieza")] == [85.14, 47.00, 38.14, 14.86]
    sds = [f[k]["sd"] for k in ("R&R total", "Repetibilidad", "Evaluador", "Pieza a pieza", "Variación total")]
    assert all(abs(x - y) < 2e-7 for x, y in zip(sds, [0.0115424, 0.0085761, 0.0077252, 0.0048225, 0.0125094]))   # las SC del libro vienen redondeadas
    assert [round(f[k]["pct_sv"], 2) for k in ("R&R total", "Repetibilidad", "Evaluador", "Pieza a pieza")] == [92.27, 68.56, 61.76, 38.55]
    assert [round(f[k]["pct_tol"], 2) for k in ("R&R total", "Repetibilidad", "Evaluador", "Pieza a pieza", "Variación total")] == [34.63, 25.73, 23.18, 14.47, 37.53]
    assert abs(f["R&R total"]["sv"] - 0.0692546) < 1e-6 and ndc == 0


def test_con_interaccion_es_el_modelo_completo():
    c = M.componentes(0.0025457, 0.0037278, 0.0011029, 0.0046340, 10, 3, 3, alfa_inter=1.0)     # conservar siempre
    assert c["con_inter"] and c["v_po"] == max(0.0, (0.0011029 / 18 - 0.0046340 / 60) / 3)
    assert math.isclose(c["v_grr"], c["v_rep"] + c["v_o"] + c["v_po"])


def datos_sinteticos(sd_p=2.0, sd_o=0.3, sd_e=0.2, seed=3, p=10, o=3, r=3):
    rng = random.Random(seed)
    pz = [rng.gauss(0, sd_p) for _ in range(p)]; op = [rng.gauss(0, sd_o) for _ in range(o)]
    filas = ["pieza\tevaluador\tmedicion"]
    for i in range(p):
        for j in range(o):
            for _ in range(r): filas.append(f"P{i + 1}\tE{j + 1}\t{round(10 + pz[i] + op[j] + rng.gauss(0, sd_e), 4)}")
    return "\n".join(filas)


def test_modulo_sobre_la_hoja_y_ss_suman():
    a = Api(); a.pegar(-1, 0, datos_sinteticos())
    r = a.ejecutar_modulo("MSA-VAR", {"pieza": 0, "evaluador": 1, "y": 2, "tol": "12"})
    assert r["error"] is None, r["sesion"][0]["texto"]
    res = r["resultado"]
    assert sum(1 for b in res["bloques"] if b["tipo"] == "grafica") == 1 and res["datos"]["ndc"] >= 5
    assert any("aceptable" in b.get("texto", "") for b in res["bloques"])
    from app.modulos.base import filas_validas, valor
    from collections import OrderedDict
    d = OrderedDict()
    for i in range(a.hoja.n): d.setdefault((a.hoja.columnas[0].valor(i)[2], a.hoja.columnas[1].valor(i)[2]), []).append(a.hoja.columnas[2].valor(i)[2])
    s = M.anova_dos_factores(d); todos = [v for g in d.values() for v in g]; m = sum(todos) / len(todos)
    assert math.isclose(s["ss_p"] + s["ss_o"] + s["ss_po"] + s["ss_e"], sum((v - m) ** 2 for v in todos))
    # recupera la proporción conocida de varianzas (4 vs 0.09 vs 0.04): pieza domina
    c = M.componentes(s["ss_p"], s["ss_o"], s["ss_po"], s["ss_e"], s["p"], s["o"], s["r"])
    assert c["v_p"] > 10 * c["v_grr"]


def test_sistema_malo_y_validaciones():
    a = Api(); a.pegar(-1, 0, datos_sinteticos(sd_p=0.5, sd_o=1.0, sd_e=1.0))
    r = a.ejecutar_modulo("MSA-VAR", {"pieza": 0, "evaluador": 1, "y": 2})["resultado"]
    assert any("inaceptable" in b.get("texto", "") for b in r["bloques"])
    assert a.ejecutar_modulo("MSA-VAR", {"pieza": 0, "evaluador": 0, "y": 2})["error"] == "entrada"
    a.editar(0, 2, "")                                                      # medición faltante: desbalanceado
    assert "balanceado" in a.ejecutar_modulo("MSA-VAR", {"pieza": 0, "evaluador": 1, "y": 2})["sesion"][0]["texto"]
    b = Api(); b.pegar(-1, 0, "p\to\ty\nA\tX\t1\nB\tX\t2\nA\tY\t1\nB\tY\t3")
    assert b.ejecutar_modulo("MSA-VAR", {"pieza": 0, "evaluador": 1, "y": 2})["error"] == "entrada"       # una sola repetición
