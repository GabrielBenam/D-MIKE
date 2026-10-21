"""Módulos de superficie de respuesta por el puente real: crear diseño, analizar, contornos, punto estacionario,
ruta de ascenso y optimizador. Procesos SINTÉTICOS con óptimo conocido."""
import math, random, re
import numpy as np
import pytest
from app.api import Api

VERDAD = lambda t, p: 80 - 0.05 * (t - 150) ** 2 - 2.0 * (p - 4) ** 2 + 0.02 * (t - 150) * (p - 4)   # máximo cerca de T=150, P=4
OTRA = lambda t, p: 20 + 0.1 * (t - 140) + 1.5 * (p - 3)                                              # segunda respuesta (costo)


def con_diseno(tipo="ccd", ruido=0.05, f=VERDAD, extra=None):
    a = Api()
    d = a.ejecutar_modulo("DISENO-RSM", {"tipo": tipo, "nombres": "Temperatura, Presion", "bajos": "140, 3", "altos": "160, 5", "limites": "130, 170; 2, 6",
                                         "respuesta": "Rendimiento", "semilla": "7", "centros": "5" if tipo != "ccd" else ""})
    assert d["error"] is None, d["sesion"][0]["texto"]
    info = d["resultado"]["datos"]["diseno"]
    jt, jp, jy = a.hoja.indice("Temperatura"), a.hoja.indice("Presion"), a.hoja.indice("Rendimiento")
    rng = random.Random(1)
    for i in range(a.hoja.n):
        t, p = a.hoja.columnas[jt].valor(i)[2], a.hoja.columnas[jp].valor(i)[2]
        a.hoja.editar(i, jy, str(round(f(t, p) + rng.gauss(0, ruido), 4)))
    if extra:
        a.hoja.editar(0, len(a.hoja.columnas), "")
        a.pegar(-1, len(a.hoja.columnas), "Costo\n" + "\n".join(str(round(extra(a.hoja.columnas[jt].valor(i)[2], a.hoja.columnas[jp].valor(i)[2]), 4))
                                                                  for i in range(a.hoja.n)))
    return a, info, (jt, jp, jy)


def test_crear_diseno_ccd_en_la_hoja():
    a, info, (jt, jp, jy) = con_diseno()
    assert info["corridas"] == 13 and math.isclose(info["alfa"], math.sqrt(2))
    t = [a.hoja.columnas[jt].valor(i)[2] for i in range(13)]
    assert round(min(t), 3) == round(150 - 10 * math.sqrt(2), 3) and sorted(set(round(v, 4) for v in t))[2] == 150
    orden = [a.hoja.columnas[1].valor(i)[2] for i in range(13)]
    assert orden == list(range(1, 14))                                   # orden de corrida consecutivo; OrdenEst aleatorio
    est = [a.hoja.columnas[0].valor(i)[2] for i in range(13)]
    assert sorted(est) == list(range(1, 14)) and est != list(range(1, 14))


def test_analizar_recupera_el_optimo():
    a, info, (jt, jp, jy) = con_diseno()
    r = a.ejecutar_modulo("RSM", {"y": jy, "xs": [jt, jp], "modelo": "cuadratico", "alfa": "0.05"})
    assert r["error"] is None, r["sesion"][0]["texto"]
    res = r["resultado"]
    ps = next(b for b in res["bloques"] if b.get("titulo", "").startswith("Punto estacionario"))
    t_opt, p_opt = float(ps["filas"][0][2].replace(",", "")), float(ps["filas"][1][2])
    assert abs(t_opt - 150) < 0.5 and abs(p_opt - 4) < 0.05 and ps["filas"][3][2] == "máximo"
    assert sum(1 for b in res["bloques"] if b["tipo"] == "grafica") == 3          # contorno, superficie, residuos
    anova = next(b for b in res["bloques"] if b.get("titulo", "").startswith("Análisis de varianza"))
    fuentes = [f[0].strip() for f in anova["filas"]]
    for x in ("Modelo", "Lineal", "Cuadrado", "Interacción de 2 factores", "Falta de ajuste", "Error puro", "Total"): assert x in fuentes
    # la ecuación en unidades reales reproduce la predicción codificada
    ec = next(b["texto"] for b in res["bloques"] if b.get("texto", "").startswith("Ecuación en unidades reales"))
    m = res["datos"]["modelo_rsm"]
    from app.modulos import doe as D
    xc = D.a_codificado([152.0, 3.7], m["bajos"], m["altos"])
    y_cod = D.predecir_codificado((m["b0"], np.array(m["b"]), np.array(m["B"])), xc)
    nums = [float(x.replace(",", "")) for x in re.findall(r"-?[\d,]+\.?\d*(?:e-?\d+)?", ec.split("=", 1)[1].replace(" - ", " -").replace("+ ", ""))]
    k0, lt, lp, tt, pp, tp = nums
    y_real = k0 + lt * 152 + lp * 3.7 + tt * 152 ** 2 + pp * 3.7 ** 2 + tp * 152 * 3.7
    assert abs(y_real - y_cod) < 0.01, (y_real, y_cod)


def test_quitar_terminos_y_jerarquia():
    a, info, (jt, jp, jy) = con_diseno()
    r = a.ejecutar_modulo("RSM", {"y": jy, "xs": [jt, jp], "excluir": "Temperatura, Temperatura*Presion"})
    res = r["resultado"]; coef = next(b for b in res["bloques"] if b.get("titulo", "").startswith("Coeficientes"))
    nombres = [f[0] for f in coef["filas"]]
    assert "Temperatura" in nombres and "Temperatura*Presion" not in nombres and any("jerarquía" in x for x in res["avisos"])


def test_factorial_con_centros_curvatura_y_ascenso():
    a, info, (jt, jp, jy) = con_diseno("fact", f=lambda t, p: 50 + 0.8 * (t - 150) + 3 * (p - 4))
    r = a.ejecutar_modulo("RSM", {"y": jy, "xs": [jt, jp], "modelo": "lineal", "meta": "max"})
    res = r["resultado"]
    assert any(b.get("titulo", "").startswith("Ruta de ascenso") for b in res["bloques"])
    ruta = next(b for b in res["bloques"] if b.get("titulo", "").startswith("Ruta de ascenso"))
    assert ruta["filas"][1][1] == "160" and "Temperatura" in ruta["titulo"]
    assert any("curvatura no es significativa" in b.get("texto", "") for b in res["bloques"])


def test_optimizador_una_y_dos_respuestas():
    a, info, (jt, jp, jy) = con_diseno(extra=OTRA)
    r1 = a.ejecutar_modulo("RSM", {"y": jy, "xs": [jt, jp]})["resultado"]
    jc = a.hoja.indice("Costo")
    r2 = a.ejecutar_modulo("RSM", {"y": jc, "xs": [jt, jp], "modelo": "lineal"})["resultado"]
    d = a.dialogo_modulo("OPTIMIZADOR")["dialogo"]
    assert [o[0] for o in d["campos"][0]["opciones"]] == [r1["uid"], r2["uid"]]
    o = a.ejecutar_modulo("OPTIMIZADOR", {"r1": r1["uid"], "meta1": "max", "inf1": "70", "obj1": "80"})
    assert o["error"] is None
    fac = next(b for b in o["resultado"]["bloques"] if b.get("titulo") == "Ajuste óptimo de los factores")
    assert abs(float(fac["filas"][0][1].replace(",", "")) - 150) < 0.6 and abs(float(fac["filas"][1][1]) - 4) < 0.05
    o = a.ejecutar_modulo("OPTIMIZADOR", {"r1": r1["uid"], "meta1": "max", "inf1": "70", "obj1": "80",
                                          "r2": r2["uid"], "meta2": "min", "obj2": "18", "sup2": "24", "imp2": "2"})
    res = o["resultado"]; fac = next(b for b in res["bloques"] if b.get("titulo") == "Ajuste óptimo de los factores")
    assert float(fac["filas"][0][1].replace(",", "")) < 150                # el costo empuja la temperatura hacia abajo
    assert len(next(b for b in res["bloques"] if b.get("titulo") == "Respuestas")["filas"]) == 2


def test_optimizador_validaciones():
    a, info, (jt, jp, jy) = con_diseno()
    assert a.ejecutar_modulo("OPTIMIZADOR", {})["error"] == "entrada"
    r1 = a.ejecutar_modulo("RSM", {"y": jy, "xs": [jt, jp]})["resultado"]
    assert a.ejecutar_modulo("OPTIMIZADOR", {"r1": r1["uid"], "meta1": "max", "inf1": "90", "obj1": "80"})["error"] == "entrada"
    assert a.ejecutar_modulo("OPTIMIZADOR", {"r1": r1["uid"], "meta1": "objetivo", "inf1": "70", "obj1": "75", "sup1": "79"})["error"] is None


def test_diseno_validaciones_y_box_behnken():
    a = Api()
    assert a.ejecutar_modulo("DISENO-RSM", {"nombres": "A", "bajos": "1", "altos": "2", "limites": "0, 10"})["error"] == "entrada"
    assert a.ejecutar_modulo("DISENO-RSM", {"nombres": "A, B", "bajos": "1, 5", "altos": "2, 4", "limites": "0, 10; 0, 10"})["error"] == "entrada"
    assert a.ejecutar_modulo("DISENO-RSM", {"tipo": "bb", "nombres": "A, B", "bajos": "1, 1", "altos": "2, 2", "limites": "0, 10; 0, 10"})["error"] == "entrada"
    r = a.ejecutar_modulo("DISENO-RSM", {"tipo": "bb", "nombres": "A, B, C", "bajos": "1, 1, 1", "altos": "2, 2, 2", "limites": "0, 3; 0, 3; 0, 3", "aleatorio": False})
    assert r["error"] is None and r["resultado"]["datos"]["diseno"]["corridas"] == 15


def test_superficie_guardada_y_repetida(tmp_path):
    a, info, (jt, jp, jy) = con_diseno()
    r1 = a.ejecutar_modulo("RSM", {"y": jy, "xs": [jt, jp]})["resultado"]
    a._elegir = lambda *x, **k: str(tmp_path / "rsm.dmike"); a.guardar()
    b = Api(); b.abrir_proyecto(str(tmp_path / "rsm.dmike"))
    assert b.repetir_resultado(r1["uid"])["error"] is None
    assert b.ejecutar_modulo("OPTIMIZADOR", {"r1": r1["uid"], "meta1": "max", "inf1": "70", "obj1": "80"})["error"] is None
