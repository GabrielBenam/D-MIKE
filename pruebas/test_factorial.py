"""Diseños factoriales y fraccionados: curso (18_GB FACT-2X2-EJEMPLO; 26_BB FRAC-RESOLUCION y FRAC-CONSTRUCCION) y un ejemplo publicado
sin réplicas (Montgomery, Design and Analysis of Experiments, ejemplo 6.2, tasa de filtración; fuente externa)."""
import numpy as np
from app.api import Api
from app.modulos import doe as D


def efectos(res):
    t = next(b for b in res["bloques"] if b.get("titulo", "").startswith("Efectos"))
    return {f[0]: float(f[1]) for f in t["filas"] if f[1]}, {f[0]: f[5] for f in t["filas"]}


def test_ejemplo_2x2_del_curso():
    a = Api(); a.pegar(-1, 0, "Ra\trecubrimiento\tfluido\n44\tSin\tSin\n32\tCon\tSin\n55\tSin\tCon\n20\tCon\tCon")
    r = a.ejecutar_modulo("FACTORIAL", {"y": 0, "xs": [1, 2], "meta": "min"})["resultado"]
    e, _ = efectos(r)
    assert e == {"A": -23.5, "B": -0.5, "AB": -11.5}               # el recubrimiento tiene el mayor efecto (FACT-EFECTOS-PRINCIPALES)
    assert "recubrimiento = Con" in r["bloques"][0]["texto"] or "Lenth" in r["avisos"][0]


def test_fraccionados_resolucion_y_signo_del_curso():
    assert [D.resolucion(3, 1), D.resolucion(4, 1), D.resolucion(5, 1)] == [3, 4, 5]          # FRAC-RESOLUCION: III, IV y V
    filas, _ = D.diseno_fraccionado(4, 1, signo=-1)
    assert len(filas) == 8 and all(np.prod(f["coded"]) == -1 for f in filas)                   # FRAC-CONSTRUCCION: D = -ABC, ABCD negativo
    pal = D.relacion_definidora(4, 1); assert D.alias("AB", pal) == ["CD"] and D.alias("A", pal) == ["BCD"]


def test_montgomery_filtracion_sin_replicas():
    y = [45, 71, 48, 65, 68, 60, 80, 65, 43, 100, 45, 104, 75, 86, 70, 96]       # orden estándar (1), a, b, ab, c, …, abcd
    filas = ["tasa\tA\tB\tC\tD"]
    for i, v in enumerate(y):
        filas.append("\t".join([str(v)] + [str(1 if (i >> q) & 1 else -1) for q in range(4)]))
    a = Api(); a.pegar(-1, 0, "\n".join(filas))
    r = a.ejecutar_modulo("FACTORIAL", {"y": 0, "xs": [1, 2, 3, 4], "meta": "max"})["resultado"]
    e, p = efectos(r)
    esperado = {"A": 21.625, "B": 3.125, "C": 9.875, "D": 14.625, "AC": -18.125, "AD": 16.625}
    assert all(abs(e[k] - v) < 1e-9 for k, v in esperado.items())
    assert {k for k, v in p.items() if v != "" and float(v.replace("< ", "")) < .05} == {"A", "C", "D", "AC", "AD"}
    assert any("Lenth" in x for x in r["avisos"])


def test_fraccionado_desde_el_diseno_y_alias_en_el_analisis():
    a = Api()
    d = a.ejecutar_modulo("DISENO-RSM", {"tipo": "frac", "nombres": "Temp, Tiempo, Enfr, TempE", "bajos": "180, 6, 3, 100", "altos": "220, 10, 6, 120", "limites": "100, 300; 1, 20; 1, 10; 50, 150",
                                         "fraccion": "1", "signo": "1", "aleatorio": False})
    assert d["error"] is None
    res = d["resultado"]; t = next(b for b in res["bloques"] if b.get("titulo") == "Resumen del diseño")
    assert ["Resolución", "IV"] in t["filas"] and ["Relación definidora", "I = ABCD"] in t["filas"]
    info = res["datos"]["diseno"]; jy = a.hoja.indice(info["respuesta"]); jx = [a.hoja.indice(f["nombre"]) for f in info["factores"]]
    rng = np.random.default_rng(3)
    for i in range(a.hoja.n):
        v = [a.hoja.columnas[j].valor(i)[2] for j in jx]
        a.hoja.editar(i, jy, str(round(50 + 5 * (v[0] - 200) / 20 - 3 * (v[1] - 8) / 2 + rng.normal(0, .3), 3)))
    r = a.ejecutar_modulo("FACTORIAL", {"y": jy, "xs": jx})["resultado"]
    al = next(b for b in r["bloques"] if b.get("titulo", "").startswith("Estructura de alias"))
    assert ["AB", "CD"] in al["filas"] and any("fraccionado" in x for x in r["interpretacion"]) if "interpretacion" in r else True
