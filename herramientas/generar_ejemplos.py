"""Genera 10 proyectos de ejemplo (.dmike) con datos SINTÉTICOS y varios módulos usados en cada uno.
Uso (desde la carpeta del proyecto): python herramientas/generar_ejemplos.py <carpeta_destino>
No son casos reales: los nombres, cifras y personas son inventados para mostrar el programa."""
import copy, json, math, random, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from app.api import Api  # noqa: E402

PLANTILLA = json.load(open(RAIZ / "pruebas" / "sinteticos" / "perfil_prueba_sintetico.json", encoding="utf-8"))
NOTA = "Proyecto de ejemplo con datos sintéticos generados por D-MIKE; no es un caso real."


def perfil(nombre, area, responsable, fase, modulos, giro="manufactura"):
    """modulos: [(id, fase, prioridad)] con ids del árbol."""
    from app.nucleo.catalogo import Catalogo
    cat = Catalogo(); p = copy.deepcopy(PLANTILLA)
    p["datos_fijos"] = {"nombre_proyecto": nombre, "cliente_area": area, "responsable": responsable, "logo": None, "notas": NOTA}
    p["diagnostico"]["fase_actual"] = fase; p["perfil_empresa"]["giro"] = giro
    p["modulos"] = [{"id": m, "nombre": cat.modulos[m]["nombre"], "fase_asignada": f, "estado": "activo", "prioridad": pr,
                     "motivos": ["seleccionado para el ejemplo"], "tipo": cat.modulos[m]["tipo"], "plantilla": "",
                     "datos_minimos": cat.modulos[m].get("datos_minimos", "")} for m, f, pr in modulos]
    p["sugeridos"] = []; p["no_recomendados"] = []; p["siguiente_paso"] = modulos[-1][0]; p["version_perfil"] = 1
    return p


class Ej:
    def __init__(self, nombre, area, responsable, fase, modulos, complementarios=(), giro="manufactura"):
        self.a = Api(); self.nombre = nombre
        ruta = Path("/tmp") / f"perfil_{abs(hash(nombre))}.json"
        json.dump(perfil(nombre, area, responsable, fase, modulos, giro), open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
        r = self.a.abrir_perfil(str(ruta))
        assert r["error"] is None, r["sesion"]
        from app.nucleo.hoja import Hoja
        self.a.hoja = Hoja()
        for mid, f in complementarios: self.a.activar_modulo(mid, f)

    def hoja(self, encabezados, filas):
        from app.nucleo.hoja import Hoja
        self.a.hoja = Hoja()                      # sin las columnas sugeridas del perfil, para que el ejemplo quede limpio
        self.a.pegar(-1, 0, "\t".join(encabezados) + "\n" + "\n".join("\t".join(str(x) for x in f) for f in filas))

    def col(self, nombre): return self.a.hoja.indice(nombre)

    def corre(self, mid, p):
        r = self.a.ejecutar_modulo(mid, p)
        assert r["error"] is None, (self.nombre, mid, r["sesion"][0]["texto"])
        return r["resultado"]

    def fmt(self, fid, cab=None, tablas=None):
        d = self.a.abrir_formato(fid)["datos"]; d["cabecera"].update(cab or {})
        for t, filas in (tablas or {}).items():
            base = d["tablas"].get(t, [])
            for i, f in enumerate(filas):
                if i < len(base): base[i].update(f)
                else: base.append(dict(f))
            d["tablas"][t] = base
        r = self.a.guardar_formato(fid, d); assert r["error"] is None, (self.nombre, fid, r["sesion"])
        return r

    def avance(self, hechos=(), en_curso=()):
        for m in hechos: self.a.marcar_avance(m, "hecho")
        for m in en_curso: self.a.marcar_avance(m, "en_curso")

    def guardar(self, ruta):
        self.a._elegir = lambda *x, **k: str(ruta); r = self.a.guardar(True); assert r["error"] is None, r["sesion"]


def r(seed): return random.Random(seed)


# ---------------------------------------------------------------- 1
def ej_remachado():
    e = Ej("Retrabajo en remachado de paneles", "Ensamble estructural, línea 2", "Ing. Laura Méndez (ficticia)", "C",
           [("CHARTER", "D", "N"), ("SIPOC", "D", "R"), ("HOJA-DATOS", "M", "N"), ("PARETO", "A", "N"), ("ISHIKAWA", "A", "R"), ("CINCO-PQ", "A", "R"),
            ("ANOVA", "A", "R"), ("AMEF", "I", "N"), ("PLAN-CONTROL", "C", "N"), ("SPC", "C", "N")], [("INTERESADOS", "D")])
    g = r(1); defs = ["Remache inclinado", "Cabeza sin asentar", "Agujero ovalado", "Rayadura", "Remache faltante", "Rebaba"]
    pes = [.34, .24, .16, .1, .08, .08]; filas = []
    for i in range(60):
        turno = "ABC"[i % 3]; panel = f"P-{1000 + i}"; d = g.choices(defs, pes)[0]; lote = 20; defect = max(0, int(g.gauss(3.2 if turno != "C" else 4.6, 1.1)))
        filas.append([f"2026-08-{1 + i // 3:02d}", turno, panel, d, defect, lote, round(g.gauss(48 if turno != "C" else 55, 6), 1)])
    e.hoja(["fecha", "turno", "panel", "defecto", "defectuosos", "tamano", "minutos_retrabajo"], filas)
    e.corre("PARETO", {"cat": e.col("defecto"), "otros": "95"})
    e.corre("ANOVA", {"y": e.col("minutos_retrabajo"), "factor": e.col("turno"), "alfa": "0.05"})
    e.corre("SPC", {"tipo": "p", "y": e.col("defectuosos"), "ncol": e.col("tamano"), "pruebas": [str(k) for k in range(1, 8)]})
    e.fmt("CHARTER", {"caso_negocio": "El retrabajo de remachado consume 2.1 horas por turno y retrasa la entrega de paneles.", "alcance": "Línea 2, paneles de fuselaje; no incluye pintura.",
                      "criterios_aprobacion": "Gerente de planta aprueba; éxito = retrabajo menor a 1 h por turno.", "criterios_salida": "Meta sostenida 4 semanas o cancelación por cambio de producto.",
                      "patrocinador": "Gerente de planta (ficticio)", "autoridad_patrocinador": "Aprueba recursos y cambios de método"},
          {"proposito": [{"ctq": "Minutos de retrabajo por panel", "base": "50", "objetivo": "25"}], "equipo": [{"rol": "Líder", "nombre": "Laura Méndez"}, {"rol": "Champion", "nombre": "Gerente de planta"}],
           "hitos": [{"hito": "Línea base", "fecha": "15/08/2026"}, {"hito": "Piloto", "fecha": "20/09/2026"}]})
    e.fmt("SIPOC", {"proceso": "Remachado de paneles", "inicio": "Panel taladrado", "fin": "Panel inspeccionado"},
          {"entradas": [{"proveedor": "Almacén", "entrada": "Remaches", "m6": "Material"}, {"proveedor": "Taladrado", "entrada": "Panel con agujeros", "m6": "Material"}],
           "proceso": [{"paso": "Insertar remache", "salida": "Remache colocado", "cliente": "Inspección"}, {"paso": "Remachar", "salida": "Unión", "cliente": "Inspección"}]})
    e.fmt("ISHIKAWA", {"efecto": "Retrabajo en remachado"}, {"causas": [{"categoria": "Método", "causa": "Secuencia de remachado no estándar", "verificada": "Sí"},
                                                                        {"categoria": "Máquina", "causa": "Remachadora sin calibrar"}, {"categoria": "Mano de obra", "causa": "Rotación del turno C", "verificada": "Sí"},
                                                                        {"categoria": "Material", "causa": "Agujeros ovalados del taladrado"}]})
    e.fmt("CINCO-PQ", {"problema": "Remache inclinado", "causa_raiz": "No hay guía de perpendicularidad en la herramienta", "accion": "Instalar guía y capacitar", "responsable": "Laura Méndez"},
          {"porques": [{"respuesta": "La herramienta entra inclinada"}, {"respuesta": "El operador no ve el ángulo"}, {"respuesta": "No hay guía física"}]})
    e.fmt("AMEF", {}, {"filas": [{"operacion": "Remachar", "falla": "Remache inclinado", "efecto": "Retrabajo y posible rechazo", "sev": "7", "causas": "Sin guía", "occ": "6", "controles": "Inspección visual", "det": "5",
                                  "acciones": "Guía de perpendicularidad", "sev2": "7", "occ2": "2", "det2": "4"}]})
    e.fmt("PLAN-CONTROL", {"producto": "Panel de fuselaje", "proceso": "Remachado"}, {"filas": [{"paso": "Remachar", "que": "Proporción de paneles con defecto", "metodo_control": "Carta p", "tamano": "20", "frecuencia": "Por turno", "quien": "Inspector"}]})
    e.fmt("INTERESADOS", {}, {"registro": [{"nombre": "Gerente de planta", "rol": "Patrocinador"}, {"nombre": "Supervisor turno C", "rol": "Dueño del proceso"}],
                              "analisis": [{"poder": "Alto", "interes": "Alto", "actual": "De apoyo", "deseado": "Líder"}, {"poder": "Bajo", "interes": "Alto", "actual": "Resistente", "deseado": "De apoyo", "accion": "Reunión semanal de resultados"}]})
    e.avance(("CHARTER", "SIPOC", "HOJA-DATOS", "PARETO", "ISHIKAWA", "CINCO-PQ", "ANOVA", "AMEF"), ("PLAN-CONTROL", "SPC"))
    return e


# ---------------------------------------------------------------- 2
def ej_torneado():
    e = Ej("Capacidad del diámetro en torneado CNC", "Maquinado, celda 4", "Ing. Ramiro Ortega (ficticio)", "C",
           [("MSA-VAR", "M", "N"), ("DISTRIB", "M", "N"), ("CAPACIDAD", "M", "N"), ("CORREL", "A", "R"), ("REGRESION", "A", "R"), ("SPC", "C", "N"), ("PLAN-CONTROL", "C", "N"), ("TABLERO", "C", "R")])
    g = r(2); filas = []
    for i in range(100):
        t = round(g.uniform(18, 30), 1); d = round(25.000 + .0018 * (t - 24) + g.gauss(0, .004), 4)
        filas.append([i + 1, t, d] + ([f"P{1 + (i % 10)}", f"Op{1 + (i // 10) % 3}", round(25 + ((i % 10) - 4.5) * .006 + g.gauss(0, .0015) + ((i // 10) % 3) * .0008, 4)] if i < 90 else ["", "", ""]))
    e.hoja(["pieza", "temperatura", "diametro", "parte_rr", "operador_rr", "medicion_rr"], filas)
    e.corre("MSA-VAR", {"pieza": e.col("parte_rr"), "evaluador": e.col("operador_rr"), "y": e.col("medicion_rr"), "tol": "0.06"})
    e.corre("DISTRIB", {"y": e.col("diametro"), "lie": "24.97", "lse": "25.03"})
    e.corre("CAPACIDAD", {"y": e.col("diametro"), "tam": "5", "lie": "24.97", "lse": "25.03", "objetivo": "25", "resumen": True})
    e.corre("CORREL", {"vars": [e.col("temperatura"), e.col("diametro")]})
    e.corre("REGRESION", {"y": e.col("diametro"), "xs": [e.col("temperatura")], "x0": "24"})
    e.corre("SPC", {"tipo": "xr", "y": e.col("diametro"), "tam": "5", "pruebas": [str(k) for k in range(1, 8)]})
    e.fmt("PLAN-CONTROL", {"producto": "Eje de actuador", "proceso": "Torneado"}, {"filas": [{"paso": "Torneado final", "que": "Diámetro", "limites": "25.00 ± 0.03", "metodo_control": "Carta X̄-R", "tamano": "5", "frecuencia": "Cada hora", "quien": "Operador"},
                                                                                            {"paso": "Refrigerante", "que": "Temperatura", "limites": "22 a 26 °C", "metodo_control": "Registro", "frecuencia": "Cada turno", "quien": "Técnico"}]})
    for kid in ("NIVEL-SIGMA", "OEE"): e.a.tablero_kpi("agregar", {"kpi_id": kid})
    d = e.a.abrir_formato("TABLERO")["datos"]
    for f, (m, vals) in zip(d["tablas"]["kpi"], ((4, [3.4, 3.5, 3.6, 3.8, 3.9, 4.1, 4.2, 4.1]), (85, [78, 80, 81, 83, 84, 86, 85, 87]))):
        f["meta"] = str(m); f.update({f"s{k + 1}": str(v) for k, v in enumerate(vals)}); f["tipo_ind"] = "Atrasado"
    e.a.guardar_formato("TABLERO", d)
    e.avance(("MSA-VAR", "DISTRIB", "CAPACIDAD", "CORREL", "REGRESION"), ("SPC", "PLAN-CONTROL", "TABLERO"))
    return e


# ---------------------------------------------------------------- 3
def ej_smed():
    e = Ej("Cambio rápido de molde en inyección", "Inyección de plásticos, prensa 7", "Ing. Sofía Navarro (ficticia)", "I",
           [("CHARTER", "D", "N"), ("OEE", "M", "N"), ("SMED", "I", "N"), ("KAIZEN", "I", "R"), ("TABLERO", "C", "R")])
    e.hoja(["cambio", "minutos_antes", "minutos_despues"], [[i + 1, 92 + (i * 7) % 15, 38 + (i * 5) % 9] for i in range(12)])
    e.corre("ESTADISTICOS", {"y": e.col("minutos_antes")})
    e.fmt("CHARTER", {"caso_negocio": "Los cambios de molde de 95 min limitan los lotes pequeños.", "alcance": "Prensa 7, moldes de la familia A."},
          {"proposito": [{"ctq": "Minutos de cambio", "base": "95", "objetivo": "40"}]})
    e.fmt("SMED", {"unidad": "min", "clasificacion": "Molde completo"}, {"ops": [
        {"operacion": "Buscar molde en almacén", "real": "12", "pot": "0", "clase": "Externa"}, {"operacion": "Desmontar molde", "real": "18", "pot": "12", "clase": "Interna"},
        {"operacion": "Buscar herramientas", "real": "9", "pot": "0", "clase": "Desperdicio"}, {"operacion": "Montar molde", "real": "22", "pot": "14", "clase": "Interna"},
        {"operacion": "Precalentar molde", "real": "20", "pot": "0", "clase": "Externa"}, {"operacion": "Ajuste y primeras piezas", "real": "14", "pot": "8", "clase": "Interna"}]})
    e.fmt("OEE", {"linea": "Prensa 7", "turno": "1"}, {"horas": [{"periodo": str(h + 1), "total": "60", "paro": "0", "muerto": str([5, 0, 12, 0, 0, 8, 0, 3][h]), "capacidad": "120", "produccion": str([108, 118, 95, 117, 119, 100, 116, 112][h]), "rechazo": str([2, 1, 4, 0, 1, 3, 1, 1][h])} for h in range(8)]})
    e.fmt("KAIZEN", {"oportunidad": "Cambio de molde largo", "propuesta": "Preparación externa, carro de herramientas y sujeción rápida", "fecha_inicio": "01/09/2026", "fecha_promesa": "26/09/2026", "fecha_fin": "24/09/2026", "alcance": "Prensa 7"},
          {"equipo": [{"nombre": "Sofía Navarro", "rol": "Líder"}, {"nombre": "Técnico de moldes", "rol": "Ejecución"}]})
    e.a.tablero_kpi("agregar", {"kpi_id": "OEE"}); d = e.a.abrir_formato("TABLERO")["datos"]
    f = d["tablas"]["kpi"][0]; f.update(meta="85", advertencia="80", tipo_ind="Atrasado", **{f"s{k + 1}": str(v) for k, v in enumerate([74, 76, 79, 83, 86, 87])}); e.a.guardar_formato("TABLERO", d)
    e.avance(("CHARTER", "OEE", "SMED"), ("KAIZEN", "TABLERO"))
    return e


# ---------------------------------------------------------------- 4
def ej_arneses():
    e = Ej("Flujo de valor en ensamble de arneses", "Arneses eléctricos", "Ing. Tomás Rivas (ficticio)", "I",
           [("VSM", "M", "N"), ("TIEMPOS", "M", "N"), ("TAKT", "M", "N"), ("BALANCE", "A", "N"), ("MUDAS", "A", "R"), ("ESPAGUETI", "A", "R"), ("KANBAN", "I", "R"), ("TRABAJO-EST", "I", "N")])
    e.hoja(["estacion", "tiempo_ciclo_s"], [[f"E{k}", t] for k, t in enumerate([52, 61, 48, 70, 55, 44], 1)])
    e.corre("ESTADISTICOS", {"y": e.col("tiempo_ciclo_s")})
    e.fmt("TAKT", {"proceso": "Ensamble de arneses", "disp_simple": "25200", "demanda_simple": "420", "unidad": "s"})
    e.fmt("BALANCE", {"t_disponible": "25200", "demanda": "420"}, {"operaciones": [{"numero": str(k), "descripcion": f"Estación {k}", "tiempo": str(t)} for k, t in enumerate([52, 61, 48, 70, 55, 44], 1)]})
    e.fmt("TIEMPOS", {"proceso": "Estación 4: conectores"}, {"elementos": [{"elemento": "Tomar conector", **{f"m{j}": str(8 + (j % 3)) for j in range(1, 11)}},
                                                                          {"elemento": "Insertar terminales", **{f"m{j}": str(45 + (j % 5)) for j in range(1, 11)}}]})
    e.fmt("MUDAS", {}, {"mudas": [{"impacto": "Alto", "observacion": "Lotes de 50 arneses entre estaciones", "accion": "Flujo de una pieza"}, {}, {"impacto": "Medio", "observacion": "Traslado a pruebas eléctricas", "accion": "Mover probador"},
                                  {}, {"impacto": "Alto", "observacion": "Inventario de 2 días", "accion": "Kanban"}, {"impacto": "Medio", "observacion": "Espera de conectores", "accion": "Supermercado"}]})
    e.fmt("ESPAGUETI", {"quien": "Operador de la estación 4"}, {"antes": [{"desde": "E4", "hasta": "Almacén", "distancia": "35", "veces": "4", "retorno": "Sí"}, {"desde": "E4", "hasta": "Probador", "distancia": "18", "veces": "2"}],
                                                              "despues": [{"desde": "E4", "hasta": "Supermercado", "distancia": "6", "veces": "4"}, {"desde": "E4", "hasta": "Probador", "distancia": "5", "veces": "2"}]})
    e.fmt("KANBAN", {"no_parte": "CN-220", "descripcion": "Conector de 12 vías", "entrega": "2", "capacidad": "50"}, {"demanda": [{"mes": m, "demanda": str(d)} for m, d in zip(["Ene", "Feb", "Mar"], [8400, 9100, 8800])]})
    e.fmt("TRABAJO-EST", {"proceso": "Ensamble de arneses", "operacion": "Estación 4", "takt": "60"}, {"pasos": [{"paso": "Tomar conector", "manual": "9", "caminata": "2"}, {"paso": "Insertar terminales", "manual": "47"}]})
    e.fmt("VSM", {f"proceso_{k}": n for k, n in enumerate(["Corte", "Ponchado", "Ensamble", "Conectores", "Prueba", "Empaque"], 1)},
          {"modelos": [{"modelo": "ARN-100", "descripcion": "Arnés de cabina", **{f"tc_proceso_{k}": str(t) for k, t in enumerate([52, 61, 48, 70, 55, 44], 1)}, **{f"vol_{m}": "420" for m in ("ene", "feb", "mar")}}],
           "resultados": [{"indicador": "Tiempo de entrega (días)", "antes": "6.5", "despues": "2.0"}, {"indicador": "Inventario en proceso (piezas)", "antes": "320", "despues": "90"}]})
    e.avance(("VSM", "TIEMPOS", "TAKT", "BALANCE", "MUDAS", "ESPAGUETI"), ("KANBAN", "TRABAJO-EST"))
    return e


# ---------------------------------------------------------------- 5
def ej_curado():
    e = Ej("Optimización del curado de material compuesto", "Laminado de compuestos", "Ing. Daniela Prieto (ficticia)", "I",
           [("CHARTER", "D", "N"), ("CORREL", "A", "R"), ("RSM", "I", "N"), ("PLAN-CONTROL", "C", "R")], [("DISENO-RSM", "I"), ("OPTIMIZADOR", "I")])
    d = e.corre("DISENO-RSM", {"tipo": "ccd", "nombres": "Temperatura, Tiempo", "bajos": "170, 90", "altos": "190, 130", "respuesta": "Resistencia", "semilla": "4"})
    info = d["datos"]["diseno"]; jt, jp, jy = (e.col(info["factores"][0]["nombre"]), e.col(info["factores"][1]["nombre"]), e.col(info["respuesta"]))
    g = r(5)
    for i in range(e.a.hoja.n):
        t, ti = e.a.hoja.columnas[jt].valor(i)[2], e.a.hoja.columnas[jp].valor(i)[2]
        e.a.hoja.editar(i, jy, str(round(612 - .9 * (t - 182) ** 2 - .05 * (ti - 115) ** 2 + .08 * (t - 182) * (ti - 115) + g.gauss(0, 3), 1)))
    res = e.corre("RSM", {"y": jy, "xs": [jt, jp], "modelo": "cuadratico"})
    e.corre("OPTIMIZADOR", {"r1": res["uid"], "meta1": "max", "inf1": "590", "obj1": "615"})
    e.corre("CORREL", {"vars": [jt, jp, jy]})
    e.fmt("CHARTER", {"caso_negocio": "La resistencia interlaminar varía y obliga a repetir pruebas.", "alcance": "Autoclave 2, prepreg tipo B."},
          {"proposito": [{"ctq": "Resistencia (MPa)", "base": "585", "objetivo": "610"}]})
    e.fmt("PLAN-CONTROL", {"producto": "Laminado tipo B", "proceso": "Curado"}, {"filas": [{"paso": "Curado", "que": "Temperatura de meseta", "limites": "181 a 185 °C", "metodo_control": "Registro del autoclave", "frecuencia": "Cada ciclo", "quien": "Operador"}]})
    e.avance(("CHARTER", "CORREL", "DISENO-RSM", "RSM"), ("OPTIMIZADOR", "PLAN-CONTROL"))
    return e


# ---------------------------------------------------------------- 6
def ej_pintura():
    e = Ej("Defectos de pintura por condiciones de cabina", "Pintura de componentes", "Ing. Marco Leal (ficticio)", "I",
           [("PARETO", "A", "N"), ("ANOVA", "A", "R")], [("DISENO-RSM", "I"), ("FACTORIAL", "I"), ("CHI2", "A"), ("HIPOTESIS", "A")])
    d = e.corre("DISENO-RSM", {"tipo": "frac", "nombres": "Viscosidad, Presion, Distancia, Humedad", "bajos": "18, 30, 15, 40", "altos": "24, 45, 25, 60",
                               "respuesta": "Espesor_defectuoso", "fraccion": "1", "signo": "1", "centros": "3", "aleatorio": False})
    info = d["datos"]["diseno"]; jx = [e.col(f["nombre"]) for f in info["factores"]]; jy = e.col(info["respuesta"]); g = r(6)
    for i in range(e.a.hoja.n):
        v = [e.a.hoja.columnas[j].valor(i)[2] for j in jx]; c = [(v[q] - (f["bajo"] + f["alto"]) / 2) / ((f["alto"] - f["bajo"]) / 2) for q, f in enumerate(info["factores"])]
        e.a.hoja.editar(i, jy, str(round(8 + 2.5 * c[0] - 1.8 * c[1] + 1.2 * c[0] * c[1] + g.gauss(0, .4), 2)))
    e.corre("FACTORIAL", {"y": jy, "xs": jx, "meta": "min"})
    col0 = len(e.a.hoja.columnas)
    filas = [[["Escurrido", "Piel de naranja", "Polvo", "Burbuja", "Escurrido", "Polvo"][i % 6], "AB"[i % 2], 1] for i in range(48)]
    e.a.pegar(-1, col0, "tipo_defecto\tturno\tconteo\n" + "\n".join("\t".join(map(str, f)) for f in filas))
    e.corre("PARETO", {"cat": e.col("tipo_defecto"), "otros": "95"})
    e.corre("CHI2", {"filas": e.col("tipo_defecto"), "cols": e.col("turno"), "alfa": "0.05"})
    e.corre("HIPOTESIS", {"tipo": "p2", "x1": "31", "n1": "400", "x2": "17", "n2": "410", "h0": "0"})
    e.avance(("PARETO", "CHI2", "HIPOTESIS", "DISENO-RSM"), ("FACTORIAL",))
    return e


# ---------------------------------------------------------------- 7
def ej_gestion():
    e = Ej("Reubicación del almacén de refacciones", "Logística interna", "Ing. Paula Garza (ficticia)", "C",
           [("CHARTER", "D", "N"), ("RIESGOS", "I", "N"), ("LECCIONES", "C", "N")],
           [("EDT", "D"), ("CRONOGRAMA", "D"), ("MONTECARLO", "D"), ("RACI", "D"), ("BITACORA", "D"), ("VALOR-GANADO", "C")])
    e.hoja(["semana", "pedidos_surtidos", "minutos_por_pedido"], [[k, 180 + 6 * k, round(24 - .9 * k, 1)] for k in range(1, 13)])
    e.corre("CORRIDA", {"y": e.col("minutos_por_pedido")})
    e.fmt("CHARTER", {"caso_negocio": "Reubicar el almacén reduce el recorrido de surtido.", "alcance": "Almacén de refacciones de mantenimiento.", "patrocinador": "Director de operaciones (ficticio)",
                      "criterios_aprobacion": "Minutos por pedido menor a 15", "criterios_salida": "Almacén operando 4 semanas sin incidentes"})
    d = e.a.abrir_formato("EDT")["datos"]; d["cabecera"]["plantilla"] = "dmaic"; e.a.guardar_formato("EDT", d)
    d = e.a.abrir_formato("CRONOGRAMA")["datos"]; d["cabecera"].update(plantilla="dmaic", inicio="03/08/2026"); d = e.a.guardar_formato("CRONOGRAMA", d)["datos"]
    for f in d["tablas"]["actividades"]:
        if f.get("m") not in (None, "", "0"): f["o"], f["p"] = str(round(float(f["m"]) * .8, 1)), str(round(float(f["m"]) * 1.5, 1))
    e.a.guardar_formato("CRONOGRAMA", d); e.a.guardar_formato("MONTECARLO", e.a.abrir_formato("MONTECARLO")["datos"])
    e.fmt("RACI", {"p1": "Líder", "p2": "Director", "p3": "Almacén", "p4": "Mantenimiento"}, {"actividades": [
        {"actividad": "Layout nuevo", "p1": "R", "p2": "A", "p3": "C"}, {"actividad": "Mudanza", "p1": "C", "p3": "R/A", "p4": "C"}, {"actividad": "Capacitación", "p1": "R/A", "p3": "I", "p4": "I"}]})
    e.fmt("RIESGOS", {"reserva_cont": "40000"}, {"registro": [
        {"tipo": "Amenaza", "causa": "Mudanza en temporada alta", "riesgo": "Falta de refacciones críticas", "efecto": "Paro de equipo", "probabilidad": "Media", "impacto": "Muy alto", "dueno": "Almacén", "estrategia": "Mitigar", "acciones": "Inventario de seguridad temporal", "costo": "60000"},
        {"tipo": "Oportunidad", "riesgo": "Depurar refacciones obsoletas", "efecto": "Liberar espacio", "probabilidad": "Alta", "impacto": "Moderado", "dueno": "Mantenimiento", "estrategia": "Explotar", "acciones": "Inventario físico", "costo": "15000"}]})
    e.fmt("BITACORA", {}, {"supuestos": [{"tipo": "Supuesto", "nivel": "Operativo", "descripcion": "El montacargas estará disponible 3 días", "estado": "Validado"}],
                          "incidentes": [{"tipo": "Logística", "quien": "Almacén", "fecha": "18/08/2026", "descripcion": "Estantería llegó incompleta", "prioridad": "Alta", "asignado": "Compras", "estado": "Cerrado", "solucion": "Reposición del proveedor"}],
                          "cambios": [{"fecha": "20/08/2026", "solicitante": "Mantenimiento", "descripcion": "Agregar zona de cuarentena", "afecta": "Alcance", "impacto": "+2 días", "decision": "Aprobado", "decidio": "Director"}]})
    e.fmt("VALOR-GANADO", {"bac": "250000"}, {"cortes": [{"periodo": f"S{k}", "pv": str(p), "ev": str(v), "ac": str(c)} for k, (p, v, c) in enumerate(((40000, 38000, 41000), (95000, 90000, 98000), (160000, 152000, 163000), (250000, 245000, 252000)), 1)]})
    e.fmt("LECCIONES", {"transicion": "Se entregó al jefe de almacén con instructivo y layout.", "aceptacion": "Director de operaciones, 30/09/2026"},
          {"objetivos": [{"objetivo": "Reubicar", "meta": "1", "real": "1", "sentido": ">=", "evidencia": "Acta"}, {"objetivo": "Minutos por pedido", "meta": "15", "real": "14.2", "sentido": "<=", "evidencia": "Hoja de datos"}],
           "lecciones": [{"fase": "Mejorar", "categoria": "Problema", "situacion": "Estantería incompleta", "impacto": "2 días de atraso", "recomendacion": "Inspección de recepción antes de la mudanza", "tipo_con": "Explícito (documentable)"}]})
    e.avance(("CHARTER", "RIESGOS", "EDT", "CRONOGRAMA", "RACI", "BITACORA", "VALOR-GANADO"), ("LECCIONES", "MONTECARLO"))
    return e


# ---------------------------------------------------------------- 8
def ej_tpm():
    e = Ej("Confiabilidad de bancos de prueba hidráulica", "Laboratorio de pruebas", "Ing. Javier Soto (ficticio)", "I",
           [("TPM", "I", "N"), ("OEE", "M", "N"), ("CINCO-S", "I", "R"), ("POKAYOKE", "I", "R"), ("A3", "C", "R")], [("DIST-ID", "M"), ("BOXCOX", "M")])
    g = r(8); e.hoja(["falla", "horas_entre_fallas"], [[i + 1, round(g.weibullvariate(320, 1.6), 1)] for i in range(40)])
    e.corre("DIST-ID", {"y": e.col("horas_entre_fallas")})
    e.corre("BOXCOX", {"y": e.col("horas_entre_fallas"), "usar": "redondeado"})
    e.fmt("TPM", {"equipo": "Banco hidráulico 3", "t_operacion": "2000"}, {"fallas": [{"fecha": "05/08/2026", "descripcion": "Fuga en válvula", "tipo": "Avería", "reparacion": "3", "causa": "Sello desgastado", "accion": "Cambio preventivo de sellos"},
                                                                                     {"fecha": "19/08/2026", "descripcion": "Sensor de presión fuera", "tipo": "Avería", "reparacion": "2", "causa": "Conector suelto", "accion": "Fijación con seguro"}]})
    e.fmt("CINCO-S", {"auditor": "Javier Soto", "fecha": "01/09/2026"}, {"s": [{"calif": c} for c in ("3", "2", "4", "2", "3")]})
    e.fmt("POKAYOKE", {}, {"casos": [{"error": "Conectar manguera en puerto equivocado", "proceso": "Preparación de prueba", "dispositivo": "Conectores de diámetro distinto por puerto"}]})
    e.fmt("A3", {"titulo": "Paros del banco hidráulico 3", "antecedentes": "3 paros al mes en promedio.", "condiciones_actuales": "MTBF 290 h.", "metas_objetivos": "MTBF 450 h en diciembre 2026.",
                 "analisis": "Sellos y conectores explican 70% de los paros.", "recomendaciones_mejoras": "Cambio preventivo y poka yoke de conexión.", "plan": "Septiembre: sellos; octubre: conectores.", "seguimiento_control": "Registro mensual de MTBF."})
    e.avance(("DIST-ID", "BOXCOX", "TPM", "CINCO-S"), ("POKAYOKE", "A3"))
    return e


# ---------------------------------------------------------------- 9
def ej_quejas():
    e = Ej("Tiempo de respuesta a quejas de cliente", "Servicio al cliente", "Lic. Andrea Ruiz (ficticia)", "A",
           [("KANO", "D", "R"), ("QFD", "D", "R"), ("CTQ-TREE", "D", "N"), ("DEF-PROBLEMA", "D", "N"), ("PARETO", "A", "N")], [("HIPOTESIS", "A"), ("NOPARAM", "A")])
    g = r(9); filas = []
    for i in range(80):
        canal = "Correo" if i % 2 else "Teléfono"; filas.append([i + 1, canal, ["Entrega tardía", "Producto dañado", "Factura", "Entrega tardía", "Atención"][i % 5], round(g.lognormvariate(3.1 if canal == "Correo" else 2.7, .45), 1)])
    e.hoja(["queja", "canal", "motivo", "horas_respuesta"], filas)
    e.corre("PARETO", {"cat": e.col("motivo"), "otros": "95"})
    e.corre("NOPARAM", {"tipo": "mann", "y": e.col("horas_respuesta"), "grupo": e.col("canal"), "alt": "!=", "alfa": "0.05"})
    e.fmt("DEF-PROBLEMA", {"sujeto": "las quejas por correo", "predicado": "tardan más de 24 horas en recibir respuesta", "donde": "Servicio al cliente", "cuando": "Desde junio de 2026, todos los turnos", "magnitud": "62% de las quejas por correo", "estandar": "Respuesta en menos de 24 h"})
    e.fmt("KANO", {"producto": "Atención de quejas"}, {"atributos": [{"requisito": "Respuesta en menos de 24 h", "respuesta_con": "Lo espero", "respuesta_sin": "Me disgusta"},
                                                                  {"requisito": "Seguimiento por mensaje", "respuesta_con": "Me gusta", "respuesta_sin": "Me es indiferente"}]})
    e.fmt("CTQ-TREE", {"necesidad": "Respuesta rápida y útil"}, {"ramas": [{"impulsor": "Rapidez", "requisito": "Respuesta inicial", "indicador": "Horas a la primera respuesta", "meta": "≤ 24 h"},
                                                                         {"impulsor": "Solución", "requisito": "Cierre", "indicador": "% resueltas al primer contacto", "meta": "≥ 70%"}]})
    d = e.a.abrir_formato("QFD")["datos"]; d["cabecera"]["producto_servicio"] = "Atención de quejas"
    for k, (n, di) in enumerate([("Horas a la primera respuesta", "min"), ("% resueltas al primer contacto", "max"), ("Plantillas de respuesta", "max")]): d["tablas"]["tecnicos"][k].update(nombre=n, direccion=di)
    d["tablas"]["requisitos_cliente"] = [{"requisito": "Respuesta rápida", "importancia": "5", "rel_1": "9", "rel_3": "3", "empresa": "2", "meta": "4"}, {"requisito": "Solución completa", "importancia": "4", "rel_2": "9", "rel_3": "3", "empresa": "3", "meta": "4"}]
    e.a.guardar_formato("QFD", d)
    e.avance(("KANO", "CTQ-TREE", "DEF-PROBLEMA", "PARETO"), ("NOPARAM", "QFD"))
    return e


# ---------------------------------------------------------------- 10
def ej_estrategia():
    e = Ej("Despliegue Lean de la planta 2027", "Dirección de planta", "Ing. Ricardo Peña (ficticio)", "D",
           [("HOSHIN", "D", "N"), ("FINANZAS", "D", "R"), ("TOC", "A", "R"), ("CHECKLIST-FASE", "D", "R"), ("GEMBA", "M", "R"), ("LSW", "C", "R"), ("TABLERO", "C", "N")],
           [("JUSTIFICACION", "D"), ("COSTO-CALIDAD", "A")])
    e.hoja(["mes", "ventas_miles", "costo_calidad_miles"], [[m, 1500 + 40 * k, 160 - 6 * k] for k, m in enumerate(["Ene", "Feb", "Mar", "Abr", "May", "Jun"])])
    e.corre("CORRIDA", {"y": e.col("costo_calidad_miles")})
    e.fmt("HOSHIN", {"organizacion": "Planta 2 (ficticia)", "periodo": "2027"}, {
        "objetivos": [{"perspectiva": "Finanzas", "nombre": "Incrementar ROI", "metrica": "ROI %", "base": "7", "meta": "12", "actual": "8.5"}],
        "estrategias": [{"perspectiva": "Operaciones", "nombre": "Lean Company", "metrica": "Inventario (M$)", "base": "24", "meta": "16", "actual": "21", "vinculo": "1"}],
        "proyectos": [{"perspectiva": "Operaciones", "nombre": "Reducir inventario en proceso", "metrica": "Días de inventario", "base": "18", "meta": "10", "actual": "14", "vinculo": "1"}]})
    e.fmt("JUSTIFICACION", {"inversion": "1200000", "tasa": "12"}, {"flujos": [{"beneficio": "520000", "costo": "60000"} for _ in range(4)]})
    e.fmt("COSTO-CALIDAD", {"ventas": "18000000"}, {"partidas": [{"categoria": "Prevención", "concepto": "Capacitación", "antes": "80000", "despues": "150000"},
                                                                {"categoria": "Falla interna", "concepto": "Desecho y retrabajo", "antes": "900000", "despues": "620000"},
                                                                {"categoria": "Falla externa", "concepto": "Garantías", "antes": "300000", "despues": "210000"}]})
    e.fmt("TOC", {"sistema": "Línea de ensamble final", "demanda": "48"}, {"recursos": [{"recurso": "Soldadura", "capacidad": "52"}, {"recurso": "Pintura", "capacidad": "44"}, {"recurso": "Prueba", "capacidad": "60"}]})
    e.fmt("GEMBA", {"tema": "Flujo de material", "proceso": "Ensamble final"}, {"obs": [{"lugar": "Pintura", "observacion": "Fila de 30 piezas esperando", "desperdicio": "Espera", "accion": "Balancear con TOC", "responsable": "Supervisor"}]})
    e.fmt("LSW", {"nombre": "Supervisor de ensamble (ficticio)"}, {"diario": [{"hora": "07:00", "tarea": "Junta de arranque con el tablero"}, {"hora": "13:00", "tarea": "Caminata Gemba"}]})
    d = e.a.abrir_formato("CHECKLIST-FASE")["datos"]
    for f in d["tablas"]["puntos"][:5]: f["respuesta"] = "Sí"
    e.a.guardar_formato("CHECKLIST-FASE", d)
    for kid in ("OEE", "ENTREGAS-TIEMPO", "LEADTIME"): e.a.tablero_kpi("agregar", {"kpi_id": kid})
    d = e.a.abrir_formato("TABLERO")["datos"]
    for f, (m, vals) in zip(d["tablas"]["kpi"], ((85, [79, 81, 82, 84, 86]), (95, [90, 92, 94, 95, 96]), (8, [12, 11, 10, 9, 8.5]))):
        f["meta"] = str(m); f.update({f"s{k + 1}": str(v) for k, v in enumerate(vals)})
    e.a.guardar_formato("TABLERO", d)
    d = e.a.abrir_formato("FINANZAS")["datos"]
    ent = [["239", "239", "272", "272"], ["239", "239", "272", "272"], ["65"] * 4, ["50", "50", "50", "43"], ["50625", "47625", "47625", "47625"], ["25"] * 4]
    for f, vals in zip(d["tablas"]["estados"], ent): f.update({f"e{j + 1}": vals[j] for j in range(4)})
    e.a.guardar_formato("FINANZAS", d)
    e.avance(("HOSHIN", "FINANZAS", "JUSTIFICACION"), ("CHECKLIST-FASE", "TOC", "TABLERO"))
    return e


EJEMPLOS = [ej_remachado, ej_torneado, ej_smed, ej_arneses, ej_curado, ej_pintura, ej_gestion, ej_tpm, ej_quejas, ej_estrategia]


def main(destino):
    destino = Path(destino); destino.mkdir(parents=True, exist_ok=True); salidas = []
    for k, f in enumerate(EJEMPLOS, 1):
        e = f(); nombre = f"{k:02d}_" + "_".join(e.nombre.lower().replace(",", "").split()[:5]) + ".dmike"
        for a_, b_ in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")): nombre = nombre.replace(a_, b_)
        e.guardar(destino / nombre)
        salidas.append((nombre, len(e.a.proyecto.resultados), len([x for x in e.a.proyecto.formatos if not x.startswith("_")]),
                        sum(1 for m in e.a.proyecto.modulos.values() if m.get("avance") != "pendiente")))
    return salidas


if __name__ == "__main__":
    for s in main(sys.argv[1] if len(sys.argv) > 1 else "ejemplos"): print(s)
