"""Gráficas de prioridad media, primera tanda (aprobada por el usuario el 22/10/2026): residuos 4 en 1, normal de efectos, probabilidad normal, ruta de ascenso
y optimizador. Cada una entrega su especificación junto a la imagen fija (que sigue sirviendo a los reportes) y se dibuja interactiva y editable. Datos SINTÉTICOS."""
import json
from pathlib import Path
from app.api import Api
from pruebas.test_e3_6_region import monta, rsm, col


def insp(r): return [b for b in r["bloques"] if b["tipo"] == "grafica"]
def tipos(r): return [b.get("inter", {}).get("g") for b in insp(r)]


def test_rsm_entrega_residuos_4_en_1_con_imagen_fija(tmp_path):
    a = monta(tmp_path); r = rsm(a)["resultado"]; g = next(b for b in insp(r) if b.get("inter", {}).get("g") == "residuos")
    assert g["svg"].startswith("<svg") and len(g["inter"]["res"]) == len(g["inter"]["aj"]) == a.hoja.n and len(g["inter"]["pn"]["x"]) == a.hoja.n
    assert g["inter"]["pn"]["tq"] and g["inter"]["pn"]["tl"][4] == "50"


def test_factorial_entrega_la_normal_de_efectos_con_los_significativos_marcados(tmp_path):
    a = monta(tmp_path, tipo="fact", f=lambda t, ti: 50 + 3 * (t - 110) + 0.1 * (ti - 20))
    r = a.ejecutar_modulo("FACTORIAL", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")]})["resultado"]
    g = next(b for b in insp(r) if b.get("inter", {}).get("g") == "probnormal")["inter"]
    assert len(g["x"]) == len(g["etiq"]) == len(g["marcar"]) >= 3 and any(g["marcar"]) and g["linea"]["x"][0] < g["linea"]["x"][1]


def test_normalidad_entrega_la_probabilidad_normal():
    a = Api(); a.pegar(-1, 0, "x\n" + "\n".join(str(10 + (i * 7) % 11 + i / 10) for i in range(30)))
    r = a.ejecutar_modulo("DISTRIB", {"y": 0})
    assert r["error"] is None and "probnormal" in tipos(r["resultado"])


def test_ruta_de_ascenso_lleva_los_limites_y_avisa_si_se_detiene(tmp_path):
    f = lambda t, ti: 50 + 2 * (t - 110) + 0.5 * (ti - 20)
    a = monta(tmp_path, tipo="fact", limites="100, 125; 10, 30", centros="2", f=f)
    r = a.ejecutar_modulo("RSM", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")], "modelo": "lineal"})["resultado"]
    g = next(b for b in insp(r) if b.get("inter", {}).get("g") == "ascenso"); sp = g["inter"]
    assert g["svg"].startswith("<svg") and sp["detenida"] is True and len(sp["pasos"]) < 6 and len(sp["factores"]) == 2
    assert sp["factores"][0]["limite"] == [100, 125] and max(sp["factores"][0]["valores"]) <= 125 + 1e-9


def test_optimizador_entrega_curvas_por_respuesta_y_factor(tmp_path):
    a = monta(tmp_path); rsm(a); uid = a.proyecto.resultados[-1]["uid"]
    r = a.ejecutar_modulo("OPTIMIZADOR", {"r1": uid, "meta1": "max", "inf1": 50, "obj1": 100, "peso1": 1, "imp1": 1})["resultado"]
    sp = next(b for b in insp(r) if b.get("inter", {}).get("g") == "optimizacion")["inter"]
    assert sp["factores"] == ["Temp", "Tiempo"] and len(sp["optimo"]) == 2 and len(sp["resps"]) == 1 and len(sp["resps"][0]["curvas"]) == 2
    assert len(sp["resps"][0]["curvas"][0]["x"]) == len(sp["resps"][0]["curvas"][0]["y"]) and sp["autorizada"] is True


def test_en_la_interfaz_las_cinco_se_dibujan_con_plotly(pagina, tmp_path):
    from playwright.sync_api import expect
    a = pagina.api
    resultados = []
    a.ejecutar_modulo("DISENO-RSM", {"nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "respuesta": "Resistencia", "semilla": "11", "limites": "80, 140; 5, 45",
                                      "tipo": "ccd", "alfa": "caras", "centros": "3"})
    info = a.proyecto.formatos["_disenos"]["Resistencia"]
    from app.nucleo import disenos as DIS
    ids, _ = DIS.run_ids(a.hoja, info, "Resistencia")
    import csv
    ruta = tmp_path / "r.csv"
    with open(ruta, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh); w.writerow(["RunId", "version_diseno", "Resistencia"])
        for i in range(a.hoja.n):
            t = float(a.hoja.columnas[col(a, "Temp")].valor(i)[0]); ti = float(a.hoja.columnas[col(a, "Tiempo")].valor(i)[0])
            w.writerow([ids[i], 1, 60 - 0.05 * (t - 112) ** 2 - 0.04 * (ti - 22) ** 2 + 0.03 * (i % 3)])
    a.importar_respuestas(str(ruta))
    r1 = a.ejecutar_modulo("RSM", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")]}); assert r1["error"] is None, r1["sesion"][-1]["texto"]; r1 = r1["resultado"]; resultados.append(("residuos", r1))
    r2 = a.ejecutar_modulo("OPTIMIZADOR", {"r1": r1["uid"], "meta1": "max", "inf1": 40, "obj1": 60})["resultado"]; resultados.append(("optimizacion", r2))
    a.pegar(-1, len(a.hoja.columnas), "Z\n" + "\n".join(str(10 + (i * 7) % 11 + i / 10) for i in range(a.hoja.n)))
    r3 = a.ejecutar_modulo("DISTRIB", {"y": col(a, "Z")})["resultado"]; resultados.append(("probnormal", r3))
    r4 = a.ejecutar_modulo("RSM", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")], "modelo": "lineal"})["resultado"]; resultados.append(("ascenso", r4))
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']"); pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.evaluate('localStorage.setItem("dmike_graficas_int", "1")')               # las pruebas antiguas arrancan con las gráficas interactivas apagadas
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e))); pagina.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
    for g, r in resultados:
        res = a.resultado(r["uid"])
        pagina.evaluate("r => abrirPestana('res:' + r.uid, r)", res)
        pagina.wait_for_selector(".js-plotly-plot", timeout=8000)
        n = pagina.evaluate("g => [...document.querySelectorAll('.js-plotly-plot')].filter(d => d.data && d.data.length && d.offsetParent !== null).length", g)
        assert n >= 1, g
    assert not errores, errores


# =============== tanda 2: Gage R&R, ANOVA y Tukey, rendimientos y tendencia del tablero ===============
def _gage_datos():
    import random
    rng = random.Random(3); pz = [rng.gauss(0, 2) for _ in range(10)]; op = [rng.gauss(0, .3) for _ in range(3)]
    f = ["pieza\tevaluador\tmedicion"]
    for i in range(10):
        for j in range(3):
            for _ in range(3): f.append(f"P{i + 1}\tE{j + 1}\t{round(10 + pz[i] + op[j] + rng.gauss(0, .2), 4)}")
    return "\n".join(f)


def _grupos_datos():
    f = ["y\tnivel\tbloque"]
    for k, (nivel, base) in enumerate((("A", 10), ("B", 12), ("C", 15))):
        for i in range(8): f.append(f"{base + (i % 4) * .7 + k * .1:.2f}\t{nivel}\t{'X' if i % 2 else 'Y'}")
    return "\n".join(f)


def _g(r, nombre): return next(b for b in insp(r) if b.get("inter", {}).get("g") == nombre)


def test_gage_entrega_sus_seis_paneles():
    a = Api(); a.pegar(-1, 0, _gage_datos())
    r = a.ejecutar_modulo("MSA-VAR", {"pieza": 0, "evaluador": 1, "y": 2, "tol": "12"})["resultado"]; sp = _g(r, "gage")["inter"]
    assert _g(r, "gage")["svg"].startswith("<svg") and len(sp["componentes"]["nombres"]) == 4 and len(sp["componentes"]["series"]) == 3
    assert len(sp["cartaR"]["ops"]) == 3 and len(sp["cartaR"]["ops"][0]["rg"]) == 10 and sp["cartaX"]["lsc"] > sp["cartaX"]["mg"] > sp["cartaX"]["lic"]
    assert len(sp["piezas"]["x"]) == len(sp["piezas"]["y"]) == 90 and len(sp["piezas"]["medias"]) == 10 and len(sp["evaluadores"]["grupos"]) == 3


def test_tukey_entrega_los_intervalos_por_par():
    a = Api(); a.pegar(-1, 0, _grupos_datos())
    r = a.ejecutar_modulo("TUKEY", {"y": 0, "factor": 1})["resultado"]; sp = _g(r, "tukey")["inter"]
    assert len(sp["pares"]) == 3 and all(q["lo"] < q["dif"] < q["hi"] for q in sp["pares"]) and any(q["sig"] for q in sp["pares"])


def test_anova_un_factor_entrega_caja_y_residuos_4_en_1():
    a = Api(); a.pegar(-1, 0, _grupos_datos())
    r = a.ejecutar_modulo("ANOVA", {"y": 0, "factor": 1})["resultado"]
    assert sorted(_g(r, "caja")["inter"]["grupos"]) == ["A", "B", "C"] and len(_g(r, "residuos")["inter"]["res"]) == 24


def test_anova_dos_factores_entrega_la_interaccion_y_los_residuos():
    a = Api(); a.pegar(-1, 0, "y\ta\tb\n" + "\n".join(f"{10 + i + 2 * j + (r % 2) * .3 + (1.5 if (i, j) == (1, 1) else 0):.2f}\tA{i}\tB{j}" for i in range(3) for j in range(2) for r in range(3)))
    r = a.ejecutar_modulo("ANOVA2", {"y": 0, "a": 1, "b": 2, "interaccion": True})["resultado"]; sp = _g(r, "interaccion")["inter"]
    assert len(sp["pares"][0]["series"]) == 2 and len(sp["pares"][0]["niveles"]) == 3 and len(_g(r, "residuos")["inter"]["res"]) == 18


def test_rendimiento_entrega_las_barras_por_paso_y_el_rty():
    from pruebas.test_g4_rendimiento import eventos_a_mano
    a = Api(); a.pegar(-1, 0, eventos_a_mano())
    r = a.ejecutar_modulo("RENDIMIENTO", {"unidad": 0, "paso": 1, "resultado": 2, "intento": 3})["resultado"]; sp = _g(r, "rendimiento")["inter"]
    assert sp["etiq"] == ["Revisión", "Liberación", "RTY"] and [round(v, 1) for v in sp["vals"]] == [80.0, 90.0, 72.0] and sp["rty"] is True and sp["ok"] == [True, True, True]


def test_en_la_interfaz_las_seis_nuevas_se_dibujan_y_la_tendencia_del_tablero_usa_plotly(pagina):
    from pruebas.test_g4_rendimiento import eventos_a_mano
    a = pagina.api; resultados = []
    a.pegar(-1, 0, _gage_datos()); resultados.append(("gage", a.ejecutar_modulo("MSA-VAR", {"pieza": 0, "evaluador": 1, "y": 2, "tol": "12"})["resultado"]))
    a.pegar(-1, len(a.hoja.columnas), _grupos_datos().replace("\t", "\t").split("\n")[0].replace("y\tnivel\tbloque", "yy\tnivel2\tbloque2") + "\n" + "\n".join(_grupos_datos().split("\n")[1:1 + a.hoja.n]))
    j = a.hoja.indice("yy")
    resultados.append(("tukey", a.ejecutar_modulo("TUKEY", {"y": j, "factor": a.hoja.indice("nivel2")})["resultado"]))
    resultados.append(("caja", a.ejecutar_modulo("ANOVA", {"y": j, "factor": a.hoja.indice("nivel2")})["resultado"]))
    a2 = Api(); a2.pegar(-1, 0, eventos_a_mano()); rr = a2.ejecutar_modulo("RENDIMIENTO", {"unidad": 0, "paso": 1, "resultado": 2, "intento": 3})["resultado"]
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']"); pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.evaluate('localStorage.setItem("dmike_graficas_int", "1")')                  # el arranque de las pruebas antiguas las apaga
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e))); pagina.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
    for g, r in resultados + [("rendimiento", rr)]:
        pagina.evaluate("r => abrirPestana('res:' + r.uid, r)", r)
        pagina.wait_for_selector(".js-plotly-plot", timeout=8000)
        assert pagina.evaluate("() => [...document.querySelectorAll('.js-plotly-plot')].filter(d => d.data && d.data.length && d.offsetParent !== null).length") >= 1, g
    # tendencia del tablero con Plotly
    from pruebas.test_a2_indicadores import tablero, fila
    tablero(a, [fila(s1="28", s2="27", s3="24", s4="26", s5="25", s6="29")])
    pagina.evaluate("ACCIONES_UI.tablero_vista()"); pagina.click(".tb-kpi >> nth=0")
    pagina.wait_for_selector(".tb-detalle .tb-plot.js-plotly-plot", timeout=8000)
    assert pagina.evaluate("() => document.querySelector('.tb-plot').data[0].y.filter(v => v !== null).length") == 6
    assert not errores, errores
