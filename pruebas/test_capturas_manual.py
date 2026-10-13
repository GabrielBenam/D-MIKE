from pathlib import Path
SALIDA = Path(__file__).resolve().parent / "capturas"
SINTETICO = ("fecha\tunidad_id\tcondicion\toperador\ttamano_unidad\ttiempo\terrores\n"
             "2026-10-05\tU-001\tSin\tOp1\t9\t16.2\t3\n2026-10-05\tU-002\tCon\tOp1\t4\t2.7\t0\n"
             "05/10/2026\tU-003\tSin\tOp2\t9\t14.7\t1\n2026-10-06\tU-004\tCon\tOp2\t5\t5.2\t0\n"
             "2026-10-06\tU-005\tSin\tOp1\t7\t12,5 min\t3\n2026-10-06\tU-006\tCon\tOp1\t17\t19\t0\n")


def test_captura_incremento_2(pagina):
    SALIDA.mkdir(exist_ok=True)
    pagina.locator("#hoja-tabla th.nombre[data-c='0']").click()
    pagina.evaluate("""t => { const d = new DataTransfer(); d.setData('text/plain', t);
        document.querySelector('#hoja').dispatchEvent(new ClipboardEvent('paste', {clipboardData: d, bubbles: true})); }""", SINTETICO)
    pagina.wait_for_timeout(200)
    pagina.locator("#hoja-tabla [data-f='6'][data-c='5']").click()
    pagina.keyboard.type("11.8")
    pagina.screenshot(path=str(SALIDA / "inc2_hoja.png"))


def test_captura_incremento_3(pagina):
    SALIDA.mkdir(exist_ok=True)
    pagina.api._elegir = lambda *a, **k: str(Path(__file__).parent / "sinteticos" / "perfil_prueba_sintetico.json")
    pagina.click(".menu > button:text-is('Proyecto')"); pagina.click("text=Abrir perfil del diagnóstico…")
    pagina.wait_for_selector("#franja:not([hidden])")
    pagina.click(".fase[data-fase='A'] > button")
    pagina.wait_for_timeout(300)
    pagina.screenshot(path=str(SALIDA / "inc3_perfil.png"))


def test_capturas_modulos(pagina):
    """Capturas de los módulos del MVP con datos SINTÉTICOS."""
    from test_modulos import SINT
    from test_modulos_interfaz import pegar, menu, poner
    SALIDA.mkdir(exist_ok=True)
    pagina.api.pegar(-1, 0, SINT)
    pagina.api.abrir_perfil(str(Path(__file__).parent / "sinteticos" / "perfil_prueba_sintetico.json"))
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    casos = [("CORRIDA", {"y": 4, "x": 0}), ("BOXPLOT", {"y": 4, "grupo": 2, "puntos": True}),
             ("ANOVA", {"y": 4, "factor": 2, "bloque": 3, "alfa": "0.05"}), ("PARETO", {"cat": 5, "otros": "95"}),
             ("DISTRIB", {"y": 4, "lie": "8", "lse": "18"})]
    for mid, prm in casos:
        r = pagina.evaluate(f"async () => {{ const r = await api().ejecutar_modulo('{mid}', {__import__('json').dumps(prm)}); if (r.error) return r.sesion[0].texto; abrirPestana('res:' + r.resultado.uid, r.resultado); return r.error; }}")
        assert r is None
        pagina.wait_for_timeout(300)
        pagina.screenshot(path=str(SALIDA / f"mod_{mid.lower()}.png"))
    for mid, nombre in (("AMEF", "AMEF"), ("TABLERO", "Tablero semanal"), ("HOJA-DATOS", "Hoja de recolección"), ("PLAN-CONTROL", "Plan de control")):
        menu(pagina, "Herramientas de calidad", nombre)
        pagina.wait_for_selector(f".formato[data-formato='{mid}']")
        if mid == "AMEF":
            fila = pagina.locator(".tabla-fmt tbody tr").first
            for campo, v in (("operacion", "Captura de datos"), ("falla", "Dato mal registrado"), ("efecto", "Análisis erróneo"),
                             ("sev", "7"), ("causas", "Formato ambiguo"), ("occ", "4"), ("controles", "Revisión visual"), ("det", "6")):
                poner(fila, campo, v)
        if mid == "TABLERO":
            cab = pagina.locator(".cabecera-fmt")
            cab.locator("label:has-text('Semanas') input").fill("3"); cab.locator("label:has-text('Semanas') input").press("Tab")
            pagina.wait_for_timeout(300)
            cab = pagina.locator(".cabecera-fmt")
            cab.locator("label:has-text('Inicio de la semana') input").fill("05/10/2026"); cab.locator("label:has-text('Inicio de la semana') input").press("Tab")
            pagina.wait_for_timeout(200)
            pagina.locator(".cabecera-fmt label:has-text('Columna de fecha') select").select_option("fecha")
            pagina.wait_for_timeout(300)
            fila = pagina.locator(".tabla-fmt[data-tabla='kpi'] tbody tr").first
            for campo, v in (("indicador", "Tiempo medio por unidad"), ("unidad", "min"), ("meta", "13")):
                fila.locator(f"td[data-c='{campo}'] input").fill(v); fila.locator(f"td[data-c='{campo}'] input").press("Tab")
            fila.locator("td[data-c='col'] select").select_option("tiempo")
        pagina.wait_for_timeout(400)
        pagina.screenshot(path=str(SALIDA / f"mod_{mid.lower()}.png"))


def test_capturas_v010(pagina):
    """Capturas de los formatos de v0.10 con datos SINTÉTICOS."""
    from test_modulos_interfaz import menu, poner
    SALIDA.mkdir(exist_ok=True)
    pagina.api.fijar_datos({"nombre_proyecto": "Proyecto sintético", "responsable": "Persona sintética"})
    d = pagina.api.abrir_formato("TABLERO")["datos"]
    d["cabecera"]["semanas"] = "6"
    d["tablas"]["kpi"] = [
        {"kpi_id": "OEE", "categoria": "Equipo", "indicador": "OEE", "unidad": "%", "sentido": ">=", "meta": "85", "advertencia": "80",
         **{f"s{i}": v for i, v in enumerate(["71", "74", "79", "81", "84", "86"], 1)}},
        {"kpi_id": "TMU", "categoria": "Producción", "indicador": "Tiempo medio por unidad", "unidad": "min", "sentido": "<=", "meta": "12",
         "advertencia": "14", **{f"s{i}": v for i, v in enumerate(["18.2", "17.5", "15.1", "13.9", "12.6", "13.1"], 1)}},
        {"kpi_id": "DPU", "categoria": "Calidad", "indicador": "Defectos por unidad", "unidad": "def/u", "sentido": "<=", "meta": "0.2",
         **{f"s{i}": v for i, v in enumerate(["0.9", "0.8", "0.5", "0.4", "0.3", "0.2"], 1)}},
        {"kpi_id": "FPY", "categoria": "Calidad", "indicador": "First Pass Yield (FPY)", "unidad": "%", "sentido": ">=", "meta": "95", "advertencia": "90",
         **{f"s{i}": v for i, v in enumerate(["88", "90", "91", "93", "92", "91"], 1)}}]
    d["tablas"]["wip"] = [{"unidad": "U-015", "estado": "En revisión", "responsable": "Op1"}]
    pagina.api.guardar_formato("TABLERO", d)
    ish = pagina.api.abrir_formato("ISHIKAWA")["datos"]
    ish["cabecera"]["efecto"] = "Errores en dibujos técnicos liberados"
    ish["tablas"]["causas"] = [{"categoria": c, "causa": t} for c, t in (
        ("Métodos", "Símbolos dibujados a mano"), ("Métodos", "Sin lista de verificación"), ("Mano de obra", "Rotación de personal"),
        ("Mediciones", "Revisión solo visual"), ("Materiales", "Plantillas desactualizadas"), ("Máquinas", "Bloques sin estándar"),
        ("Medio ambiente", "Interrupciones frecuentes"), ("Mano de obra", "Carga de trabajo alta"))]
    pagina.api.guardar_formato("ISHIKAWA", ish)
    oee = pagina.api.abrir_formato("OEE")["datos"]
    oee["tablas"]["horas"] = [dict(zip(("periodo", "total", "paro", "muerto", "causa", "capacidad", "produccion", "rechazo"), f)) for f in (
        ("7 a 8", "60", "10", "10", "Eléctrica", "5", "195", "2"), ("8 a 9", "60", "0", "35", "Cambio", "5", "120", "1"),
        ("9 a 10", "60", "0", "5", "Material", "7", "370", "3"))]
    pagina.api.guardar_formato("OEE", oee)
    for nombre, mid in (("Tablero semanal", "tablero_v010"), ("Diagrama de Ishikawa", "ishikawa"), ("OEE", "oee"),
                        ("Acta del proyecto (Charter)", "charter")):
        menu(pagina, "Lean" if nombre == "OEE" else "Herramientas de calidad", nombre)
        pagina.wait_for_timeout(500)
        pagina.screenshot(path=str(SALIDA / f"mod_{mid}.png"))
    menu(pagina, "Herramientas de calidad", "Tablero semanal")
    pagina.click("text=Agregar del catálogo…"); pagina.select_option(".dialogo .kpi-filtros select", "Calidad")
    pagina.wait_for_timeout(200)
    pagina.screenshot(path=str(SALIDA / "mod_catalogo_kpi.png"))


def test_capturas_motor_estadistico(pagina):
    """Capturas de SPC, capacidad, correlación y regresión con datos SINTÉTICOS."""
    import json, random
    SALIDA.mkdir(exist_ok=True)
    rng = random.Random(11)
    filas = []
    for i in range(40):
        t = 100 + i
        filas.append(f"{t}\t{round(75 - 0.27 * t + rng.gauss(0, 1.2), 2)}\t{round(rng.uniform(20, 30), 1)}\t{round(10 + rng.gauss(0, 0.8) + (1.6 if i > 27 else 0), 2)}")
    pagina.api.pegar(-1, 0, "temperatura\tdureza\thumedad\tpeso\n" + "\n".join(filas))
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    for nombre, mid, prm in (("spc", "SPC", {"tipo": "xr", "y": 3, "tam": "4", "pruebas": [str(k) for k in range(1, 8)]}),
                             ("capacidad", "CAPACIDAD", {"y": 3, "tam": "4", "lie": "7", "lse": "14", "objetivo": "10.5", "resumen": True}),
                             ("correlacion", "CORREL", {"vars": [0, 1, 2]}),
                             ("regresion", "REGRESION", {"y": 1, "xs": [0], "x0": "112"})):
        r = pagina.evaluate(f"async () => {{ const r = await api().ejecutar_modulo('{mid}', {json.dumps(prm)}); if (r.error) return r.sesion[0].texto; abrirPestana('res:' + r.resultado.uid, r.resultado); return null; }}")
        assert r is None, r
        pagina.wait_for_timeout(400)
        pagina.screenshot(path=str(SALIDA / f"est_{nombre}.png"))


def test_capturas_superficies(pagina):
    """Capturas del flujo de superficie de respuesta con un proceso SINTÉTICO."""
    from test_superficies import con_diseno, OTRA
    SALIDA.mkdir(exist_ok=True)
    a, info, (jt, jp, jy) = con_diseno(extra=OTRA)
    pagina.api.__dict__.update(a.__dict__)
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    pagina.screenshot(path=str(SALIDA / "rsm_diseno_hoja.png"))
    r = pagina.evaluate(f"""async () => {{ const r = await api().ejecutar_modulo('RSM', {{y: {jy}, xs: [{jt}, {jp}]}});
        abrirPestana('res:' + r.resultado.uid, r.resultado); return r.resultado.uid; }}""")
    pagina.wait_for_timeout(500); pagina.screenshot(path=str(SALIDA / "rsm_analisis.png"))
    pagina.locator(".resultado .grafica").nth(1).scroll_into_view_if_needed(); pagina.wait_for_timeout(200)
    pagina.screenshot(path=str(SALIDA / "rsm_superficie.png"))
    pagina.evaluate(f"""async () => {{ const r = await api().ejecutar_modulo('OPTIMIZADOR', {{r1: '{r}', meta1: 'max', inf1: '70', obj1: '80'}});
        abrirPestana('res:' + r.resultado.uid, r.resultado); }}""")
    pagina.wait_for_timeout(500); pagina.screenshot(path=str(SALIDA / "rsm_optimizador.png"))



def test_capturas_formatos_v015(pagina):
    """Capturas de formatos v0.15 con datos SINTÉTICOS (y los del curso en Finanzas)."""
    from test_modulos_interfaz import menu
    SALIDA.mkdir(exist_ok=True)
    a = pagina.api
    d = a.abrir_formato("FINANZAS")["datos"]
    ent = [["239", "239", "272", "272"], ["239", "239", "272", "272"], ["65"] * 4, ["50", "50", "50", "43"], ["50625", "47625", "47625", "47625"], ["25"] * 4]
    for f, vals in zip(d["tablas"]["estados"], ent):
        for j in range(4): f[f"e{j + 1}"] = vals[j]
    a.guardar_formato("FINANZAS", d)
    d = a.abrir_formato("PMAPA")["datos"]; d["cabecera"].update(proceso="Ensamble sintético", y_proyecto="Torque")
    for f, p in zip(d["tablas"]["pasos"], (("Recibir piezas", "pieza inspeccionada", "No"), ("Ensamblar", "subensamble", "Sí"), ("Apretar", "torque", "Sí"), ("Probar", "pieza probada", "Sí"), ("Empacar", "caja", "No"))):
        f.update(paso=p[0], salidas=p[1], valor=p[2])
    for f, e in zip(d["tablas"]["entradas"], (("1", "Proveedor", "Ruido (N)"), ("2", "Instructivo", "Estándar (S)"), ("3", "Presión neumática", "Controlable (C)"), ("4", "Calibración", "Estándar (S)"))):
        f.update(paso_n=e[0], entrada=e[1], clase=e[2])
    a.guardar_formato("PMAPA", d)
    d = a.abrir_formato("TOC")["datos"]; d["cabecera"]["demanda"] = "50"
    for f, (r_, c) in zip(d["tablas"]["recursos"], (("Corte", "70"), ("Soldadura", "48"), ("Pintura", "60"), ("Empaque", "90"))): f.update(recurso=r_, capacidad=c)
    a.guardar_formato("TOC", d)
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    for menu_, nombre, archivo in (("Herramientas de calidad", "Evaluación financiera", "finanzas"), ("Herramientas de calidad", "Mapa de proceso", "pmapa"),
                                   ("Lean", "Teoría de restricciones", "toc"), ("Herramientas de calidad", "Checklist de revisión de fase", "checklist")):
        menu(pagina, menu_, nombre); pagina.wait_for_timeout(500)
        pagina.screenshot(path=str(SALIDA / f"fmt15_{archivo}.png"))


def test_capturas_gestion_v016(pagina):
    """Capturas de los formatos de gestión con datos SINTÉTICOS."""
    from test_modulos_interfaz import menu
    SALIDA.mkdir(exist_ok=True)
    a = pagina.api
    d = a.abrir_formato("INTERESADOS")["datos"]
    gente = (("Gerente de planta", "Alto", "Alto", "Neutral", "Líder"), ("Supervisor línea 3", "Bajo", "Alto", "Resistente", "De apoyo"),
             ("Calidad proveedor", "Alto", "Bajo", "Sin conocimiento", "Neutral"), ("Operadores turno 2", "Bajo", "Bajo", "Neutral", "De apoyo"))
    d["tablas"]["registro"] = [{"nombre": g[0], "rol": "Interesado"} for g in gente]
    d["tablas"]["analisis"] = [{"poder": g[1], "interes": g[2], "actual": g[3], "deseado": g[4], "accion": "Reunión semanal"} for g in gente]
    a.guardar_formato("INTERESADOS", d)
    d = a.abrir_formato("RIESGOS")["datos"]
    d["tablas"]["registro"] = [{"tipo": t, "riesgo": r_, "probabilidad": p, "impacto": i, "dueno": "Líder", "estrategia": e, "acciones": "Plan", "costo": c}
                               for t, r_, p, i, e, c in (("Amenaza", "Retraso de proveedor", "Alta", "Muy alto", "Mitigar", "12000"), ("Amenaza", "Falla del molde", "Media", "Alto", "Transferir", "8000"),
                                                         ("Oportunidad", "Descuento por volumen", "Media", "Moderado", "Mejorar", "3000"), ("Amenaza", "Ausentismo", "Baja", "Bajo", "Aceptar", ""))]
    a.guardar_formato("RIESGOS", d)
    d = a.abrir_formato("VALOR-GANADO")["datos"]; d["cabecera"]["bac"] = "50000"
    d["tablas"]["cortes"] = [{"periodo": f"S{k}", "pv": str(pv), "ev": str(ev), "ac": str(ac)} for k, (pv, ev, ac) in enumerate(((5000, 4800, 5100), (12000, 10500, 11800), (20000, 17500, 20300), (28000, 25000, 29500)), 1)]
    a.guardar_formato("VALOR-GANADO", d)
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    for nombre, archivo in (("Registro de interesados", "interesados"), ("Registro de riesgos", "riesgos"), ("Seguimiento por valor ganado", "valor_ganado")):
        menu(pagina, "Gestión", nombre); pagina.wait_for_timeout(500)
        b = pagina.locator(".bloques-fmt").first
        if b.count(): b.scroll_into_view_if_needed()
        pagina.screenshot(path=str(SALIDA / f"fmt16_{archivo}.png"))


def test_capturas_planeacion_v017(pagina):
    """Capturas de EDT, cronograma y Monte Carlo con las plantillas DMAIC del curso."""
    from test_modulos_interfaz import menu
    SALIDA.mkdir(exist_ok=True)
    a = pagina.api
    d = a.abrir_formato("EDT")["datos"]; d["cabecera"]["plantilla"] = "dmaic"; a.guardar_formato("EDT", d)
    d = a.abrir_formato("CRONOGRAMA")["datos"]; d["cabecera"].update(plantilla="dmaic", inicio="05/10/2026"); d = a.guardar_formato("CRONOGRAMA", d)["datos"]
    for f in d["tablas"]["actividades"]:
        if f.get("m") not in (None, "", "0"): f["o"], f["p"] = str(round(float(f["m"]) * .8, 1)), str(round(float(f["m"]) * 1.6, 1))
    a.guardar_formato("CRONOGRAMA", d); a.guardar_formato("MONTECARLO", a.abrir_formato("MONTECARLO")["datos"])
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    for nombre, archivo in (("EDT y diccionario", "edt"), ("Cronograma y ruta crítica", "cronograma"), ("Monte Carlo del cronograma", "montecarlo")):
        menu(pagina, "Gestión", nombre); pagina.wait_for_timeout(600)
        b = pagina.locator(".bloques-fmt").first
        if b.count(): b.scroll_into_view_if_needed()
        pagina.screenshot(path=str(SALIDA / f"fmt17_{archivo}.png"))


def test_capturas_factorial_v018(pagina):
    """Captura del análisis factorial con el ejemplo de filtración (Montgomery 6.2, datos publicados)."""
    SALIDA.mkdir(exist_ok=True)
    y = [45, 71, 48, 65, 68, 60, 80, 65, 43, 100, 45, 104, 75, 86, 70, 96]
    filas = ["tasa\tTemperatura\tPresion\tConcentracion\tAgitacion"] + ["\t".join([str(v)] + [str(1 if (i >> q) & 1 else -1) for q in range(4)]) for i, v in enumerate(y)]
    pagina.api.pegar(-1, 0, "\n".join(filas)); pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    r = pagina.api.ejecutar_modulo("FACTORIAL", {"y": 0, "xs": [1, 2, 3, 4], "meta": "max"})
    pagina.evaluate("r => abrirPestana('res:' + r.uid, r)", r["resultado"]); pagina.wait_for_timeout(600)
    pagina.screenshot(path=str(SALIDA / "factorial_1.png"))
    pagina.evaluate("document.querySelector('.vista').scrollTop = 900"); pagina.wait_for_timeout(300)
    pagina.screenshot(path=str(SALIDA / "factorial_2.png"))
