"""Caso integral de D-MIKE con datos SINTÉTICOS: resistencia al cortante de uniones adhesivas en paneles de compuesto.
Usa la mayoría de los módulos terminados, de Definir a Controlar, con un diseño de cribado fraccionado, un diseño central
compuesto, dos superficies de respuesta (maximizar resistencia y minimizar porosidad) y el optimizador.
Uso: python herramientas/generar_caso_integral.py <carpeta_destino>"""
import csv, math, os, random, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "herramientas"))
from generar_ejemplos import Ej          # noqa: E402

NOMBRE = "Resistencia de uniones adhesivas en paneles de compuesto"


def csv_guardar(ruta, cab, filas):
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f: w = csv.writer(f); w.writerow(cab); w.writerows(filas)


def conclusion(res):
    for b in res["bloques"]:
        if b.get("tipo") == "texto" and b.get("clase") == "conclusion": return b["texto"]
    for b in res["bloques"]:
        if b.get("tipo") == "texto": return b["texto"]
    return res["titulo"]


def generar(destino):
    destino = Path(destino); (destino / "datos").mkdir(parents=True, exist_ok=True); g = random.Random(2026)
    e = Ej(NOMBRE, "Ensamble de compuestos, línea 1", "Ing. responsable del proyecto (ficticio)", "C",
           [("CHARTER", "D", "N"), ("SIPOC", "D", "N"), ("KANO", "D", "R"), ("QFD", "D", "R"), ("CTQ-TREE", "D", "N"), ("DEF-PROBLEMA", "D", "N"), ("INTERESADOS", "D", "R"),
            ("HOJA-DATOS", "M", "N"), ("MSA-VAR", "M", "N"), ("DISTRIB", "M", "N"), ("CAPACIDAD", "M", "N"), ("SPC", "C", "N"), ("DESEMPENO", "M", "R"),
            ("PARETO", "A", "N"), ("ISHIKAWA", "A", "N"), ("CINCO-PQ", "A", "R"), ("ANOVA", "A", "N"), ("CORREL", "A", "R"), ("REGRESION", "A", "R"),
            ("RSM", "I", "N"), ("AMEF", "I", "N"), ("POKAYOKE", "I", "R"), ("PLAN-CONTROL", "C", "N"), ("TABLERO", "C", "N"), ("CHECKLIST-FASE", "C", "R"), ("A3", "C", "R")],
           [("RACI", "D"), ("EDT", "D"), ("CRONOGRAMA", "D"), ("MONTECARLO", "D"), ("RIESGOS", "D"), ("JUSTIFICACION", "D"), ("BITACORA", "D"), ("ENFOQUE", "D"),
            ("HIPOTESIS", "A"), ("DISENO-RSM", "I"), ("FACTORIAL", "I"), ("OPTIMIZADOR", "I"), ("VALOR-GANADO", "C"), ("COSTO-CALIDAD", "C"), ("LECCIONES", "C")])
    a = e.a; res = {}
    # ---------------- 1. Cribado: fraccionado 2^(4-1) con 3 centros (Mejorar, primera vuelta) ----------------
    d = e.corre("DISENO-RSM", {"tipo": "frac", "nombres": "Temperatura, Tiempo, Presion, Limpieza", "bajos": "110, 60, 2, 1", "altos": "130, 120, 4, 3",
                               "fraccion": "1", "signo": "1", "centros": "3", "respuesta": "Resistencia_cribado", "aleatorio": True, "semilla": "7"})
    inf = d["datos"]["diseno"]; jx = [e.col(f["nombre"]) for f in inf["factores"]]; jy = e.col(inf["respuesta"]); filas_crib = []
    for i in range(a.hoja.n):
        v = [a.hoja.columnas[j].valor(i)[2] for j in jx]; c = [(v[q] - (f["bajo"] + f["alto"]) / 2) / ((f["alto"] - f["bajo"]) / 2) for q, f in enumerate(inf["factores"])]
        y = round(33.0 + 1.6 * c[0] + 1.0 * c[1] + 0.03 * c[2] + 0.02 * c[3] - 0.5 * c[0] * c[1] - (1.2 if not any(c) else 0) + g.gauss(0, .3), 2)
        a.hoja.editar(i, jy, str(y)); filas_crib.append(v + [y])
    csv_guardar(destino / "datos" / "04_cribado_fraccionado.csv", ["Temperatura_C", "Tiempo_min", "Presion_bar", "Limpieza_nivel", "Resistencia_MPa"], filas_crib)
    res["factorial"] = e.corre("FACTORIAL", {"y": jy, "xs": jx, "meta": "max"})
    # ---------------- 2. Diseño central compuesto en Temperatura y Tiempo ----------------
    d = e.corre("DISENO-RSM", {"tipo": "ccd", "nombres": "Temp_curado, Tiempo_curado", "bajos": "115, 80", "altos": "135, 120", "respuesta": "Resistencia", "centros": "5", "aleatorio": True, "semilla": "11"})
    inf = d["datos"]["diseno"]; jt, jti = e.col(inf["factores"][0]["nombre"]), e.col(inf["factores"][1]["nombre"]); jr = e.col(inf["respuesta"])
    jp = len(a.hoja.columnas); a.pegar(-1, jp, "Porosidad\n" + "\n".join("0" for _ in range(a.hoja.n))); jp = e.col("Porosidad"); filas_ccd = []
    for i in range(a.hoja.n):
        t, ti = a.hoja.columnas[jt].valor(i)[2], a.hoja.columnas[jti].valor(i)[2]
        if t is None: continue
        T, S = (t - 125) / 10, (ti - 100) / 20
        r_ = round(36.2 + 1.1 * T + 0.7 * S - 1.4 * T * T - 0.9 * S * S - 0.5 * T * S + g.gauss(0, .35), 2)
        p_ = round(1.8 - 0.35 * T - 0.25 * S + 0.30 * T * T + 0.20 * S * S + g.gauss(0, .07), 3)
        a.hoja.editar(i, jr, str(r_)); a.hoja.editar(i, jp, str(p_)); filas_ccd.append([t, ti, r_, p_])
    csv_guardar(destino / "datos" / "05_diseno_central_compuesto.csv", ["Temp_curado_C", "Tiempo_curado_min", "Resistencia_MPa", "Porosidad_pct"], filas_ccd)
    res["rsm_r"] = e.corre("RSM", {"y": jr, "xs": [jt, jti], "modelo": "cuadratico", "meta": "max"})
    res["rsm_p"] = e.corre("RSM", {"y": jp, "xs": [jt, jti], "modelo": "cuadratico", "meta": "min"})
    res["opt"] = e.corre("OPTIMIZADOR", {"r1": res["rsm_r"]["uid"], "meta1": "max", "inf1": "34", "obj1": "37", "imp1": "3",
                                         "r2": res["rsm_p"]["uid"], "meta2": "min", "obj2": "1.4", "sup2": "2.2", "imp2": "2"})
    # ---------------- 3. Línea base (Medir), defectos, Gage R&R y después (Controlar) ----------------
    base = []
    for i in range(100):
        lote = f"L{1 + i % 4}"; turno = "ABC"[i % 3]; temp = round(g.gauss(118, 3), 1); tiempo = round(g.gauss(75, 6))
        r_ = round(31.4 + .18 * (temp - 118) + .03 * (tiempo - 75) - (1.9 if lote == "L3" else 0) - (.6 if turno == "C" else 0) + g.gauss(0, 1.1), 2)
        por = round(max(.4, 2.6 - .12 * (r_ - 31) + g.gauss(0, .2)), 2)
        base.append([f"{1 + i // 4:02d}/08/2026", turno, lote, temp, tiempo, r_, por])
    defs = (["Porosidad alta"] * 31 + ["Despegue en borde"] * 22 + ["Adhesivo insuficiente"] * 14 + ["Contaminación de superficie"] * 9 + ["Espesor fuera"] * 6 + ["Otro"] * 4)
    g.shuffle(defs)
    rr = []
    for parte in range(1, 11):
        for op in ("Ana", "Beto", "Carla"):
            for rep in (1, 2):
                rr.append([f"P{parte}", op, rep, round(31 + (parte - 5.5) * .55 + {"Ana": 0, "Beto": .12, "Carla": -.08}[op] + g.gauss(0, .12), 2)])
    despues = [[f"{1 + i // 5:02d}/10/2026", round(g.gauss(35.8, 1.1), 2)] for i in range(60)]
    j0 = len(a.hoja.columnas)
    a.pegar(-1, j0, "\t".join(["fecha", "turno", "lote_adhesivo", "temp_real", "tiempo_real", "resistencia_base", "porosidad_base", "tipo_defecto",
                               "parte_rr", "operador_rr", "replica_rr", "medicion_rr", "fecha_despues", "resistencia_despues"]) + "\n" +
            "\n".join("\t".join(str(x) for x in (base[i] if i < 100 else [""] * 7) + ([defs[i]] if i < len(defs) else [""]) +
                                (rr[i] if i < len(rr) else [""] * 4) + (despues[i] if i < len(despues) else [""] * 2)) for i in range(100)))
    csv_guardar(destino / "datos" / "01_linea_base.csv", ["fecha", "turno", "lote_adhesivo", "temp_real_C", "tiempo_real_min", "resistencia_MPa", "porosidad_pct"], base)
    csv_guardar(destino / "datos" / "02_defectos.csv", ["tipo_defecto"], [[x] for x in defs])
    csv_guardar(destino / "datos" / "03_gage_rr.csv", ["parte", "operador", "replica", "medicion_MPa"], rr)
    csv_guardar(destino / "datos" / "06_despues.csv", ["fecha", "resistencia_MPa"], despues)
    c = e.col
    res["msa"] = e.corre("MSA-VAR", {"pieza": c("parte_rr"), "evaluador": c("operador_rr"), "y": c("medicion_rr"), "tol": "12"})
    res["distrib"] = e.corre("DISTRIB", {"y": c("resistencia_base"), "lie": "30"})
    res["cap_antes"] = e.corre("CAPACIDAD", {"y": c("resistencia_base"), "tam": "4", "lie": "30", "resumen": True})
    res["spc_antes"] = e.corre("SPC", {"tipo": "xr", "y": c("resistencia_base"), "tam": "4", "pruebas": [str(k) for k in range(1, 8)]})
    res["pareto"] = e.corre("PARETO", {"cat": c("tipo_defecto"), "otros": "95"})
    res["anova"] = e.corre("ANOVA", {"y": c("resistencia_base"), "factor": c("lote_adhesivo"), "alfa": "0.05"})
    res["correl"] = e.corre("CORREL", {"vars": [c("temp_real"), c("tiempo_real"), c("resistencia_base"), c("porosidad_base")]})
    res["regresion"] = e.corre("REGRESION", {"y": c("resistencia_base"), "xs": [c("temp_real"), c("tiempo_real")], "x0": "125; 100"})
    res["hipotesis"] = e.corre("HIPOTESIS", {"tipo": "t2", "y": c("resistencia_base"), "y2": c("resistencia_despues"), "h0": "0", "alt": "<"})
    res["cap_despues"] = e.corre("CAPACIDAD", {"y": c("resistencia_despues"), "tam": "5", "lie": "30", "resumen": True})
    res["spc_despues"] = e.corre("SPC", {"tipo": "xr", "y": c("resistencia_despues"), "tam": "5", "pruebas": [str(k) for k in range(1, 8)]})
    # ---------------- 4. Formatos ----------------
    e.fmt("CHARTER", {"caso_negocio": "El 18 % de los paneles se rechaza por baja resistencia al cortante de la unión adhesiva; cada rechazo cuesta retrabajo y pruebas.",
                      "alcance": "Línea 1 de ensamble de compuestos, unión adhesiva de paneles; no incluye laminado ni pintura.", "requisitos": "Resistencia ≥ 30 MPa con Cpk ≥ 1.33.",
                      "riesgo_general": "Medio: depende del proveedor de adhesivo y del horno de curado.", "presupuesto": "250000", "patrocinador": "Gerente de manufactura (ficticio)",
                      "autoridad_patrocinador": "Aprueba recursos, pruebas y cambios de proceso", "criterios_aprobacion": "Cpk ≥ 1.33 sostenido 4 semanas; firma el gerente de manufactura.",
                      "criterios_salida": "Meta sostenida o cancelación si el cliente cambia el adhesivo.", "autoridad_lider": "Define el plan de pruebas y detiene la línea para pruebas."},
          {"proposito": [{"ctq": "Resistencia al cortante (MPa)", "base": "31.3", "objetivo": "36"}], "equipo": [{"rol": "Líder", "nombre": "Responsable del proyecto"}, {"rol": "Champion", "nombre": "Gerente de manufactura"}],
           "hitos": [{"hito": "Línea base", "fecha": "15/08/2026"}, {"hito": "Diseño de experimentos", "fecha": "12/09/2026"}, {"hito": "Cierre", "fecha": "16/10/2026"}]})
    e.fmt("SIPOC", {"proceso": "Unión adhesiva de paneles", "inicio": "Paneles laminados", "fin": "Panel probado"},
          {"entradas": [{"proveedor": "Almacén", "entrada": "Adhesivo epóxico", "m6": "Material"}, {"proveedor": "Laminado", "entrada": "Paneles", "m6": "Material"}, {"proveedor": "Mantenimiento", "entrada": "Horno calibrado", "m6": "Máquina"}],
           "proceso": [{"paso": "Limpiar superficie", "salida": "Superficie preparada", "cliente": "Aplicación"}, {"paso": "Aplicar adhesivo", "salida": "Unión armada", "cliente": "Curado"},
                       {"paso": "Curar en horno", "salida": "Unión curada", "cliente": "Pruebas"}, {"paso": "Probar cortante", "salida": "Resultado", "cliente": "Calidad"}]})
    e.fmt("DEF-PROBLEMA", {"sujeto": "las uniones adhesivas de la línea 1", "predicado": "no alcanzan la resistencia al cortante requerida", "donde": "Horno de curado 2",
                           "cuando": "Desde junio de 2026, todos los turnos, más en el lote de adhesivo L3", "magnitud": "18 % de paneles bajo 30 MPa", "estandar": "≥ 30 MPa, Cpk ≥ 1.33"})
    e.fmt("KANO", {"producto": "Panel con unión adhesiva"}, {"atributos": [{"requisito": "Unión que no se despega", "respuesta_con": "Lo espero", "respuesta_sin": "Me disgusta"},
                                                                         {"requisito": "Certificado de prueba por lote", "respuesta_con": "Me gusta", "respuesta_sin": "Me es indiferente"}]})
    d = a.abrir_formato("QFD")["datos"]
    d["cabecera"].update(producto_servicio="Panel con unión adhesiva", nuestro="Línea 1", comp_nombre_1="Proveedor A", comp_nombre_2="Proveedor B", techo="1-2 +; 1-3 -; 2-4 +")
    for k, (n, di, o) in enumerate([("Temperatura de curado", "obj", "125 °C"), ("Tiempo de curado", "obj", "100 min"), ("Porosidad", "min", "≤ 1.5 %"), ("Limpieza de superficie", "max", "Nivel 3")]):
        d["tablas"]["tecnicos"][k].update(nombre=n, direccion=di, objetivo=o, dificultad=str(2 + k % 3), empresa=str(3 - k % 2), comp_1="4", comp_2="3")
    d["tablas"]["requisitos_cliente"] = [{"requisito": "Unión resistente", "importancia": "5", "rel_1": "9", "rel_2": "9", "rel_3": "3", "rel_4": "3", "empresa": "3", "comp_1": "4", "comp_2": "3", "meta": "5", "punto_venta": "1.5"},
                                         {"requisito": "Sin burbujas visibles", "importancia": "4", "rel_1": "3", "rel_3": "9", "rel_4": "3", "empresa": "3", "comp_1": "4", "comp_2": "4", "meta": "4", "punto_venta": "1.2"},
                                         {"requisito": "Entrega a tiempo", "importancia": "3", "rel_2": "3", "empresa": "4", "comp_1": "4", "comp_2": "3", "meta": "4", "punto_venta": "1"},
                                         {"requisito": "Trazabilidad por lote", "importancia": "2", "rel_4": "1", "empresa": "2", "comp_1": "3", "comp_2": "3", "meta": "4", "punto_venta": "1"}]
    a.guardar_formato("QFD", d)
    e.fmt("CTQ-TREE", {"necesidad": "Panel que no falle en servicio"}, {"ramas": [{"impulsor": "Resistencia", "requisito": "Cortante", "indicador": "MPa por probeta", "meta": "≥ 30 MPa"},
                                                                               {"impulsor": "Calidad de unión", "requisito": "Porosidad", "indicador": "% de área", "meta": "≤ 1.5 %"}]})
    e.fmt("INTERESADOS", {}, {"registro": [{"nombre": "Gerente de manufactura", "rol": "Patrocinador"}, {"nombre": "Supervisor del horno", "rol": "Dueño del proceso"}, {"nombre": "Calidad del cliente", "rol": "Cliente"}],
                              "analisis": [{"poder": "Alto", "interes": "Alto", "actual": "De apoyo", "deseado": "Líder"}, {"poder": "Bajo", "interes": "Alto", "actual": "Neutral", "deseado": "De apoyo", "accion": "Juntas semanales"},
                                           {"poder": "Alto", "interes": "Bajo", "actual": "Neutral", "deseado": "De apoyo", "accion": "Reporte mensual"}]})
    e.fmt("RACI", {"p1": "Líder", "p2": "Gerente", "p3": "Supervisor", "p4": "Calidad"}, {"actividades": [{"actividad": "Diseño de experimentos", "p1": "R/A", "p3": "C", "p4": "C"},
                                                                                                       {"actividad": "Cambio del ciclo de curado", "p1": "R", "p2": "A", "p3": "C", "p4": "I"}, {"actividad": "Plan de control", "p1": "C", "p3": "R/A", "p4": "C"}]})
    d = a.abrir_formato("EDT")["datos"]; d["cabecera"]["plantilla"] = "dmaic"; a.guardar_formato("EDT", d)
    d = a.abrir_formato("CRONOGRAMA")["datos"]; d["cabecera"].update(plantilla="dmaic", inicio="03/08/2026"); d = a.guardar_formato("CRONOGRAMA", d)["datos"]
    for f in d["tablas"]["actividades"]:
        if f.get("m") not in (None, "", "0"): f["o"], f["p"] = str(round(float(f["m"]) * .8, 1)), str(round(float(f["m"]) * 1.5, 1))
    a.guardar_formato("CRONOGRAMA", d); a.guardar_formato("MONTECARLO", a.abrir_formato("MONTECARLO")["datos"])
    e.fmt("RIESGOS", {"reserva_cont": "30000"}, {"registro": [
        {"tipo": "Amenaza", "causa": "Lotes de adhesivo variables", "riesgo": "El lote L3 sigue fuera de especificación", "efecto": "Rechazos", "probabilidad": "Media", "impacto": "Alto", "dueno": "Calidad", "estrategia": "Mitigar", "acciones": "Inspección de recibo por lote", "costo": "40000"},
        {"tipo": "Oportunidad", "riesgo": "Ciclo de curado más corto", "efecto": "Más capacidad del horno", "probabilidad": "Media", "impacto": "Moderado", "dueno": "Líder", "estrategia": "Explotar", "acciones": "Validar con el diseño central compuesto", "costo": "20000"}]})
    e.fmt("JUSTIFICACION", {"inversion": "250000", "tasa": "12"}, {"flujos": [{"beneficio": "180000", "costo": "15000"} for _ in range(3)]})
    e.fmt("ENFOQUE", {"elegido": "Predictivo"})
    e.fmt("BITACORA", {}, {"supuestos": [{"tipo": "Supuesto", "nivel": "Operativo", "descripcion": "El horno 2 mantiene ±2 °C", "estado": "Validado"}],
                          "incidentes": [{"tipo": "Equipo", "quien": "Supervisor", "fecha": "20/08/2026", "descripcion": "Termopar del horno fuera de calibración", "prioridad": "Alta", "asignado": "Mantenimiento", "estado": "Cerrado", "solucion": "Calibración y verificación diaria"}],
                          "cambios": [{"fecha": "15/09/2026", "solicitante": "Líder", "descripcion": "Ciclo de curado 125 °C y 100 min", "afecta": "Procedimiento", "impacto": "Mayor resistencia y menos porosidad", "decision": "Aprobado", "decidio": "Gerente de manufactura"}]})
    e.fmt("HOJA-DATOS", {"inicio": "01/08/2026", "instrumento": "Máquina universal de pruebas", "unidades": "MPa", "caracteristica": "Resistencia al cortante", "tipo_dato": "Continuo"},
          {"plan": [{"medicion": "Resistencia", "estratificacion": "Turno, lote de adhesivo", "definicion": "Probeta de cortante por panel", "tamano": "4 por día", "fuente": "Laboratorio", "quien": "Técnico de pruebas"}]})
    e.fmt("DESEMPENO", {"proceso": "Unión adhesiva"}, {"pasos": [{"paso": "Unión", "unidades": "400", "oportunidades": "2", "defectos": "86"}]})
    e.fmt("ISHIKAWA", {"efecto": "Baja resistencia de la unión"}, {"causas": [{"categoria": "Material", "causa": "Lote de adhesivo L3", "verificada": "Sí"}, {"categoria": "Método", "causa": "Ciclo de curado corto", "verificada": "Sí"},
                                                                            {"categoria": "Máquina", "causa": "Termopar descalibrado", "verificada": "Sí"}, {"categoria": "Mano de obra", "causa": "Limpieza inconsistente"},
                                                                            {"categoria": "Medición", "causa": "Probetas mal alineadas"}, {"categoria": "Medio ambiente", "causa": "Humedad en verano"}]})
    e.fmt("CINCO-PQ", {"problema": "Uniones bajo 30 MPa", "causa_raiz": "El ciclo de curado no se definió con datos; se heredó de otro adhesivo", "accion": "Definir el ciclo con un diseño de experimentos", "responsable": "Líder"},
          {"porques": [{"respuesta": "El adhesivo no cura completo"}, {"respuesta": "La temperatura y el tiempo son bajos"}, {"respuesta": "El ciclo se copió de otro adhesivo"}]})
    e.fmt("AMEF", {}, {"filas": [{"operacion": "Curado", "falla": "Curado incompleto", "efecto": "Baja resistencia", "sev": "8", "causas": "Ciclo corto o termopar descalibrado", "occ": "6", "controles": "Prueba destructiva por muestreo", "det": "5",
                                  "acciones": "Ciclo 125 °C · 100 min y verificación diaria del termopar", "sev2": "8", "occ2": "2", "det2": "3"},
                                 {"operacion": "Limpieza", "falla": "Superficie contaminada", "efecto": "Despegue", "sev": "8", "causas": "Paño reutilizado", "occ": "4", "controles": "Visual", "det": "6",
                                  "acciones": "Paños de un solo uso y prueba de gota", "sev2": "8", "occ2": "2", "det2": "3"}]})
    e.fmt("POKAYOKE", {}, {"casos": [{"error": "Arrancar el horno con el ciclo anterior", "proceso": "Curado", "dispositivo": "Receta bloqueada por número de parte"}]})
    e.fmt("PLAN-CONTROL", {"producto": "Panel con unión adhesiva", "proceso": "Curado"}, {"filas": [
        {"paso": "Curado", "que": "Temperatura de meseta", "limites": "123 a 127 °C", "metodo_control": "Registro del horno", "frecuencia": "Cada ciclo", "quien": "Operador"},
        {"paso": "Prueba", "que": "Resistencia al cortante", "limites": "≥ 30 MPa", "metodo_control": "Carta X̄-R (n = 5)", "tamano": "5", "frecuencia": "Diaria", "quien": "Técnico de pruebas"}]})
    for kid in ("NIVEL-SIGMA", "OEE"): a.tablero_kpi("agregar", {"kpi_id": kid})
    d = a.abrir_formato("TABLERO")["datos"]
    for f, (m, vals, tipo) in zip(d["tablas"]["kpi"], ((4, [2.4, 2.5, 2.6, 3.1, 3.8, 4.3, 4.6, 4.7], "Atrasado"), (85, [79, 80, 81, 83, 85, 86, 87, 86], "Atrasado"))):
        f["meta"] = str(m); f["tipo_ind"] = tipo; f.update({f"s{k + 1}": str(v) for k, v in enumerate(vals)})
    a.guardar_formato("TABLERO", d)
    e.fmt("VALOR-GANADO", {"bac": "250000"}, {"cortes": [{"periodo": f"S{k}", "pv": str(p), "ev": str(v), "ac": str(x)} for k, (p, v, x) in enumerate(((50000, 48000, 52000), (120000, 112000, 118000), (190000, 186000, 191000), (250000, 250000, 247000)), 1)]})
    e.fmt("COSTO-CALIDAD", {"ventas": "12000000"}, {"partidas": [{"categoria": "Prevención", "concepto": "Diseño de experimentos y capacitación", "antes": "20000", "despues": "60000"},
                                                                {"categoria": "Evaluación", "concepto": "Pruebas destructivas", "antes": "90000", "despues": "70000"},
                                                                {"categoria": "Falla interna", "concepto": "Retrabajo y desecho", "antes": "520000", "despues": "110000"}, {"categoria": "Falla externa", "concepto": "Reclamos", "antes": "80000", "despues": "10000"}]})
    d = a.abrir_formato("CHECKLIST-FASE")["datos"]
    for f in d["tablas"]["puntos"]: f["respuesta"] = "Sí"
    d["cabecera"].update(decision="Continuar", decidio="Gerente de manufactura"); a.guardar_formato("CHECKLIST-FASE", d)
    e.fmt("A3", {"titulo": "Resistencia de uniones adhesivas", "antecedentes": "18 % de rechazos por baja resistencia.", "condiciones_actuales": "Media 31.3 MPa, Ppk menor a 1.",
                 "metas_objetivos": "≥ 30 MPa con Cpk ≥ 1.33.", "analisis": "Lote L3 y ciclo de curado corto; el cribado señaló temperatura y tiempo.",
                 "recomendaciones_mejoras": "Ciclo de curado del optimizador e inspección de recibo del adhesivo.", "plan": "Piloto en septiembre; estándar en octubre.", "seguimiento_control": "Carta X̄-R diaria y tablero semanal."})
    e.fmt("LECCIONES", {"transicion": "Se entregó al supervisor del horno con el plan de control y la receta bloqueada.", "aceptacion": "Gerente de manufactura, 16/10/2026"},
          {"objetivos": [{"objetivo": "Resistencia media", "meta": "35", "real": "35.8", "sentido": ">=", "evidencia": "Capacidad después"}, {"objetivo": "Costo del proyecto", "meta": "250000", "real": "247000", "sentido": "<=", "evidencia": "Valor ganado"}],
           "lecciones": [{"fase": "Mejorar", "categoria": "Buena práctica", "situacion": "El cribado redujo el diseño a dos factores", "impacto": "Ahorro de 12 corridas", "recomendacion": "Cribar antes de la superficie de respuesta", "tipo_con": "Explícito (documentable)"}]})
    hechos = ["CHARTER", "SIPOC", "KANO", "QFD", "CTQ-TREE", "DEF-PROBLEMA", "INTERESADOS", "HOJA-DATOS", "MSA-VAR", "DISTRIB", "CAPACIDAD", "DESEMPENO", "PARETO", "ISHIKAWA", "CINCO-PQ",
              "ANOVA", "CORREL", "REGRESION", "RSM", "AMEF", "POKAYOKE", "RACI", "EDT", "CRONOGRAMA", "MONTECARLO", "RIESGOS", "JUSTIFICACION", "BITACORA", "ENFOQUE", "HIPOTESIS",
              "DISENO-RSM", "FACTORIAL", "OPTIMIZADOR", "SPC", "PLAN-CONTROL", "VALOR-GANADO", "COSTO-CALIDAD", "A3", "CHECKLIST-FASE"]
    e.avance(hechos, ("TABLERO", "LECCIONES"))
    nombre = "caso_integral_uniones_adhesivas.dmike"; e.guardar(destino / nombre)
    return e, res, nombre


def caso_md(destino, e, res, nombre):
    a = e.a; opt = res["opt"]
    t_opt = next((b for b in opt["bloques"] if b.get("tipo") == "tabla" and b.get("titulo") == "Ajuste óptimo de los factores"), None)
    t_resp = next((b for b in opt["bloques"] if b.get("tipo") == "tabla" and b is not t_opt and "Respuesta" in (b.get("cabeza") or [])), None)
    filas_opt = "\n".join(f"| {f[0]} | {f[1]} |" for f in (t_opt["filas"] if t_opt else []))
    lineas = [f"# Caso integral D-MIKE: {NOMBRE}", "", "**Datos sintéticos.** Caso inventado para mostrar el programa de principio a fin; no corresponde a ninguna empresa ni cliente.", "",
              "## Situación", "La línea 1 de ensamble de compuestos une paneles con adhesivo epóxico curado en horno. El 18 % de los paneles no alcanza la resistencia al cortante mínima de 30 MPa. "
              "El ciclo de curado se heredó de otro adhesivo y nunca se definió con datos.", "",
              "## Decisión de optimización", "Se decidió **maximizar la resistencia al cortante** (más margen contra el mínimo de 30 MPa) y, al mismo tiempo, **minimizar la porosidad** de la unión "
              "(la causa principal de rechazo en el Pareto). Ambas respuestas se modelaron con superficies de respuesta en 3D sobre temperatura y tiempo de curado, y el optimizador buscó el ciclo que mejor "
              "cumple las dos metas a la vez (deseabilidad compuesta; la resistencia pesa más que la porosidad).", "",
              "## Recorrido por fases y módulos", "",
              "| Fase | Módulos usados en el proyecto |", "|---|---|",
              "| Definir | Acta (Charter), SIPOC, definición del problema, Kano, QFD con techo y benchmark, árbol CTQ, interesados, RACI, EDT, cronograma, Monte Carlo, riesgos, justificación de negocio, enfoque, bitácora |",
              "| Medir | Hoja de recolección, Gage R&R de variable, normalidad, capacidad (antes), desempeño DPMO |",
              "| Analizar | Pareto de defectos, Ishikawa, 5 Porqués, ANOVA por lote de adhesivo, correlación, regresión, prueba t antes contra después |",
              "| Mejorar | Diseño fraccionado 2^(4-1) de cribado y su análisis factorial, diseño central compuesto, dos superficies de respuesta 3D, optimizador, AMEF, Poka Yoke |",
              "| Controlar | Cartas X̄-R antes y después, capacidad después, plan de control, tablero de indicadores, valor ganado, costo de calidad, checklist de fase, A3, cierre y lecciones |", "",
              "## Resultados obtenidos (conclusiones del programa)", ""]
    for k, t in (("msa", "Sistema de medición"), ("cap_antes", "Capacidad antes"), ("pareto", "Pareto de defectos"), ("anova", "ANOVA por lote"), ("factorial", "Cribado fraccionado"),
                 ("rsm_r", "Superficie de resistencia (maximizar)"), ("rsm_p", "Superficie de porosidad (minimizar)"), ("hipotesis", "Antes contra después"), ("cap_despues", "Capacidad después")):
        lineas.append(f"- **{t}.** {conclusion(res[k])}")
    lineas += ["", "## Ciclo de curado recomendado por el optimizador", "", "| Factor | Valor óptimo |", "|---|---|", filas_opt or "| (ver el resultado del optimizador en el proyecto) | |", "",
               *(["| " + " | ".join(t_resp["cabeza"]) + " |", "|" + "---|" * len(t_resp["cabeza"])] + ["| " + " | ".join(str(x) for x in f) + " |" for f in t_resp["filas"]] + [""] if t_resp else []),
               "## Contenido de la carpeta", f"- `{nombre}`: el proyecto completo; ábrelo con Archivo › Abrir proyecto.",
               "- `datos/01_linea_base.csv`: 100 mediciones de resistencia y porosidad con turno, lote, temperatura y tiempo reales.",
               "- `datos/02_defectos.csv`: 86 defectos clasificados para el Pareto.", "- `datos/03_gage_rr.csv`: estudio de Gage R&R (10 partes, 3 operadores, 2 réplicas).",
               "- `datos/04_cribado_fraccionado.csv`: diseño 2^(4-1) con 3 puntos centrales.", "- `datos/05_diseno_central_compuesto.csv`: 13 corridas con resistencia y porosidad.",
               "- `datos/06_despues.csv`: 60 mediciones con el ciclo nuevo.", "",
               "## Cómo recorrerlo en D-MIKE", "1. Abre el proyecto: verás la fase actual (Controlar) en el riel y el avance de cada módulo.",
               "2. En la fase Mejorar abre «Analizar superficie de respuesta»: los resultados de resistencia y porosidad traen la superficie 3D y el contorno.",
               "3. Abre el resultado del optimizador para ver el ciclo recomendado y la deseabilidad de cada respuesta.",
               "4. En Definir, abre el QFD y pulsa «Casa completa a la derecha» para ver la casa de la calidad entera; haz clic en las celdas para probar cambios.",
               "5. El tablero de indicadores (Proyecto › Tablero) muestra el nivel sigma y el OEE semana a semana."]
    (Path(destino) / "CASO.md").write_text("\n".join(lineas), encoding="utf-8")


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "caso_integral"
    e, res, nombre = generar(dest); caso_md(dest, e, res, nombre)
    print("resultados:", len(e.a.proyecto.resultados), "formatos:", len([x for x in e.a.proyecto.formatos if not x.startswith("_")]),
          "módulos con avance:", sum(1 for m in e.a.proyecto.modulos.values() if m.get("avance") != "pendiente"))
