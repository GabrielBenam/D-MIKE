"""Formatos agregados en v0.10: OEE, TAKT, KANBAN, CHARTER, SIPOC, ISHIKAWA y CINCO-PQ.
Fórmulas: lean.py (06_FORMULAS_Y_KPIS); rubros: plantillas del curso (PL09, PL05, PL14, PL10) y 03_SOLUCION_PROBLEMAS."""
import math
from . import lean as L
from .formatos import Formato, formato, fila_vacia, chispa
from .base import num, figura, a_svg_png, NARANJA, TINTA, SUAVE, CLARO
from ..nucleo.hoja import a_numero

SI_NO = [["", ""], ["Sí", "Sí"], ["No", "No"]]
M6 = [["", ""], ["Mano de obra", "Mano de obra"], ["Materiales", "Materiales"], ["Métodos", "Métodos"],
      ["Máquinas", "Máquinas"], ["Medio ambiente", "Medio ambiente"], ["Mediciones", "Mediciones"]]


def pct(x): return "no definido (denominador 0)" if x is None or x != x else f"{100 * x:.1f}%"


def numeros(f, campos):
    return [a_numero(f.get(c) or "") for c in campos]


# ---------------- OEE ----------------
@formato
class Oee(Formato):
    ID, TITULO = "OEE", "OEE y tablero de OEE"
    CABECERA = [
        {"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
        {"campo": "departamento", "etiqueta": "Departamento"}, {"campo": "linea", "etiqueta": "Línea o máquina"},
        {"campo": "fecha", "etiqueta": "Fecha"}, {"campo": "turno", "etiqueta": "Turno"}, {"campo": "grupo", "etiqueta": "Grupo"},
        {"campo": "disp_calc", "etiqueta": "Disponibilidad del periodo", "calc": True},
        {"campo": "efi_calc", "etiqueta": "Eficiencia del periodo", "calc": True},
        {"campo": "cal_calc", "etiqueta": "Calidad del periodo", "calc": True},
        {"campo": "oee_calc", "etiqueta": "OEE del periodo", "calc": True}]
    TABLAS = [{"id": "horas", "titulo": "Registro por hora o turno", "filas": 8, "columnas": [
        {"campo": "periodo", "etiqueta": "Periodo", "ancho": 90},
        {"campo": "total", "etiqueta": "Tiempo total (min)", "tipo": "numero", "ancho": 80},
        {"campo": "paro", "etiqueta": "Paro planeado (min)", "tipo": "numero", "ancho": 80},
        {"campo": "muerto", "etiqueta": "Tiempo muerto (min)", "tipo": "numero", "ancho": 80},
        {"campo": "causa", "etiqueta": "Causa del tiempo muerto", "ancho": 130},
        {"campo": "capacidad", "etiqueta": "Capacidad (pz/min)", "tipo": "numero", "ancho": 80},
        {"campo": "produccion", "etiqueta": "Producción (pz)", "tipo": "numero", "ancho": 80},
        {"campo": "rechazo", "etiqueta": "Rechazo (pz)", "tipo": "numero", "ancho": 70},
        {"campo": "disponibilidad", "etiqueta": "Disponib.", "calc": True, "ancho": 74},
        {"campo": "eficiencia", "etiqueta": "Eficiencia", "calc": True, "ancho": 74},
        {"campo": "calidad", "etiqueta": "Calidad", "calc": True, "ancho": 74},
        {"campo": "oee", "etiqueta": "OEE", "calc": True, "ancho": 70}]}]
    NOTA = ("FORM-OEE-CURSO (06_FORMULAS_Y_KPIS): disponible = total - paro planeado; operativo = disponible - muerto; disponibilidad = "
            "operativo / disponible; eficiencia = producción / (operativo x capacidad); calidad = (producción - rechazo) / producción. "
            "Umbrales mínimos del tablero del curso (PL09, TABLERO-OEE): disponibilidad 90%, eficiencia 95%, calidad 99%, OEE 85%. "
            "El curso llama Eficiencia a lo que otros llaman Desempeño. El total del periodo suma tiempos y piezas de todas las filas.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        calc, clases, av, ok = [], [], [], []
        for i, f in enumerate(d["tablas"]["horas"]):
            c, k = {}, {}
            if fila_vacia(f): calc.append(c); clases.append(k); continue
            tot, paro, muerto, cap, prod, rech = numeros(f, ("total", "paro", "muerto", "capacidad", "produccion", "rechazo"))
            if None in (paro, muerto, rech) and None not in (tot, cap, prod):     # A1: vacío no es cero; teclea 0 si no hubo paro o rechazo
                k.update({x: "pendiente" for x, v in (("paro", paro), ("muerto", muerto), ("rechazo", rech)) if v is None})
                calc.append(c); clases.append(k); continue
            if None in (tot, cap, prod):
                k.update({x: "falta" for x, v in (("total", tot), ("capacidad", cap), ("produccion", prod)) if v is None})
            else:
                try:
                    r = L.oee(tot, paro, muerto, cap, prod, rech)
                except ValueError as e:
                    av.append(f"Fila {i + 1}: {e}"); calc.append(c); clases.append(k); continue
                for campo, clave in (("disponibilidad", "disponibilidad"), ("eficiencia", "eficiencia"), ("calidad", "calidad"), ("oee", "oee")):
                    c[campo] = pct(r[clave]); k[campo] = "ok" if r[clave] >= L.UMBRALES_OEE[clave] else "no"
                if r["eficiencia"] > 1: av.append(f"Fila {i + 1}: la eficiencia pasa de 100%; revisa la capacidad por minuto.")
                ok.append({**r, "produccion": prod, "rechazo": rech})
            calc.append(c); clases.append(k)
        cab = {}
        if ok:
            t = L.oee_agregado(ok)
            alc = f"periodo de {len(ok)} horas capturadas"
            cab = {"disp_calc": f"{pct(t['disponibilidad'])} del tiempo disponible · {alc}", "efi_calc": f"{pct(t['eficiencia'])} de la producción planeada · {alc}",
                   "cal_calc": f"{pct(t['calidad'])} de la producción total · {alc}", "oee_calc": f"{pct(t['oee'])} del tiempo disponible (D × E × C) · {alc}"}
            bajo = [n for n, kk in (("disponibilidad", "disponibilidad"), ("eficiencia", "eficiencia"), ("calidad", "calidad")) if t[kk] < L.UMBRALES_OEE[kk]]
            if bajo: av.append("Factores debajo del umbral del curso en el periodo: " + ", ".join(bajo) + ".")
        return {"cab": cab, "calc": {"horas": calc}, "clases": {"horas": clases}, "avisos": av}


# ---------------- TAKT ----------------
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


@formato
class Takt(Formato):
    ID, TITULO = "TAKT", "Takt time"
    CABECERA = [
        {"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
        {"campo": "proceso", "etiqueta": "Proceso o producto"},
        {"campo": "disp_simple", "etiqueta": "Cálculo directo: tiempo disponible del periodo", "tipo": "numero"},
        {"campo": "demanda_simple", "etiqueta": "Cálculo directo: demanda del mismo periodo", "tipo": "numero"},
        {"campo": "unidad", "etiqueta": "Unidad de tiempo (cálculo directo)", "tipo": "opcion", "opciones": [["min", "minutos"], ["s", "segundos"]], "defecto": "min"},
        {"campo": "dias", "etiqueta": "Curso: días laborales por mes", "tipo": "numero"},
        {"campo": "horas", "etiqueta": "Curso: horas por turno", "tipo": "numero"},
        {"campo": "turnos", "etiqueta": "Curso: turnos por día", "tipo": "numero"},
        {"campo": "descanso", "etiqueta": "Curso: descansos por turno (min)", "tipo": "numero"},
        {"campo": "takt_simple_calc", "etiqueta": "Takt (cálculo directo)", "calc": True},
        {"campo": "disp_calc", "etiqueta": "Tiempo disponible por día (s)", "calc": True},
        {"campo": "diaria_calc", "etiqueta": "Demanda diaria", "calc": True},
        {"campo": "takt_calc", "etiqueta": "Takt del curso (s por pieza)", "calc": True}]
    TABLAS = [{"id": "demanda", "titulo": "Demanda mensual (12 meses, para el cálculo del curso)", "filas": 12, "fijas": True, "columnas": [
        {"campo": "mes", "etiqueta": "Mes", "ancho": 110}, {"campo": "demanda", "etiqueta": "Demanda", "tipo": "numero", "ancho": 100}]}]
    NOTA = ("Cálculo directo: takt = tiempo disponible / demanda (FORM-TAKT). Cálculo del curso (FORM-TAKT-CURSO, hoja Takt time del VSM): "
            "tiempo disponible (s) = horas x 3600 x turnos - descansos (min) x turnos x 60; demanda diaria = promedio mensual / días "
            "laborales; takt = tiempo disponible / demanda diaria. El tiempo disponible no incluye paros planeados.")

    @classmethod
    def vacio(cls):
        v = super().vacio()
        v["tablas"]["demanda"] = [{"mes": m, "demanda": ""} for m in MESES]
        return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c = d["cabecera"]; cab, av = {}, []
        ts, dm = a_numero(c.get("disp_simple") or ""), a_numero(c.get("demanda_simple") or "")
        if ts is not None and dm:
            cab["takt_simple_calc"] = f"{num(L.takt_simple(ts, dm), 3)} {c.get('unidad') or 'min'} por unidad"
        dem = [a_numero(f.get("demanda") or "") for f in d["tablas"]["demanda"]]
        llenas = [x for x in dem if x is not None]
        dias, horas, turnos, desc = (a_numero(c.get(k) or "") for k in ("dias", "horas", "turnos", "descanso"))
        if llenas and None not in (dias, horas, turnos) and dias > 0:
            if len(llenas) < 12: av.append(f"Hay {len(llenas)} de 12 meses de demanda; el curso usa los 12. No se completan con supuestos.")
            r = L.takt_curso(llenas, dias, horas, turnos, desc or 0)
            cab.update(disp_calc=num(r["tiempo_disponible_s"]), diaria_calc=num(r["demanda_diaria"], 2), takt_calc=num(r["takt_s"], 2))
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av}


# ---------------- KANBAN ----------------
@formato
class Kanban(Formato):
    ID, TITULO = "KANBAN", "Cálculo de Kanban"
    CABECERA = [
        {"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
        {"campo": "no_parte", "etiqueta": "Número de parte"}, {"campo": "descripcion", "etiqueta": "Descripción"},
        {"campo": "entrega", "etiqueta": "Tiempo de entrega (semanas)", "tipo": "numero"},
        {"campo": "ubicaciones", "etiqueta": "Ubicaciones", "tipo": "numero", "defecto": "1"},
        {"campo": "capacidad", "etiqueta": "Capacidad del contenedor (piezas)", "tipo": "numero"},
        {"campo": "prom_calc", "etiqueta": "Demanda promedio mensual", "calc": True},
        {"campo": "desv_calc", "etiqueta": "Desviación estándar", "calc": True},
        {"campo": "var_calc", "etiqueta": "% variación", "calc": True},
        {"campo": "sem_calc", "etiqueta": "Demanda semanal", "calc": True},
        {"campo": "piezas_calc", "etiqueta": "Piezas en Kanban", "calc": True},
        {"campo": "cont_calc", "etiqueta": "Número de contenedores", "calc": True}]
    TABLAS = [{"id": "demanda", "titulo": "Demanda mensual (12 meses)", "filas": 12, "fijas": True, "columnas": [
        {"campo": "mes", "etiqueta": "Mes", "ancho": 110}, {"campo": "demanda", "etiqueta": "Demanda", "tipo": "numero", "ancho": 100}]}]
    NOTA = ("FORM-KANBAN (06_FORMULAS_Y_KPIS; PL05): demanda semanal = promedio mensual x 12 / 52; % variación = desviación estándar "
            "muestral / promedio; piezas = demanda semanal x entrega x ubicaciones x (1 + % variación); contenedores = piezas / capacidad, "
            "redondeado hacia arriba. El factor de seguridad es el coeficiente de variación, no un nivel de servicio; con demanda estacional "
            "mezcla estacionalidad y variabilidad. Si faltan meses no se completan con supuestos.")

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["demanda"] = [{"mes": m, "demanda": ""} for m in MESES]; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c = d["cabecera"]; cab, av = {}, []
        dem = [x for x in (a_numero(f.get("demanda") or "") for f in d["tablas"]["demanda"]) if x is not None]
        ent, ubi, cap = (a_numero(c.get(k) or "") for k in ("entrega", "ubicaciones", "capacidad"))
        if len(dem) >= 2:
            prom = sum(dem) / len(dem); s = math.sqrt(sum((x - prom) ** 2 for x in dem) / (len(dem) - 1))
            cab.update(prom_calc=num(prom, 2), desv_calc=num(s, 2), var_calc=pct(s / prom) if prom else "—")
            if len(dem) < 12: av.append(f"Hay {len(dem)} de 12 meses de demanda; el curso usa los 12.")
            if None not in (ent, ubi, cap) and cap > 0 and prom > 0:
                r = L.kanban(prom, s, ent, ubi, cap)
                cab.update(sem_calc=num(r["demanda_semanal"], 1), piezas_calc=num(r["piezas"], 1), cont_calc=str(r["contenedores"]))
                if r["variacion"] > 0.5: av.append("La variación de la demanda es mayor a 50%: el resultado sube mucho; valídalo.")
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av}


# ---------------- CHARTER ----------------
@formato
class Charter(Formato):
    ID, TITULO = "CHARTER", "Acta del proyecto (Project Charter)"
    CABECERA = [
        {"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
        {"campo": "area", "etiqueta": "Cliente o área", "fijo": "cliente_area"},
        {"campo": "proyecto_num", "etiqueta": "Número de proyecto"}, {"campo": "iniciador", "etiqueta": "Iniciador"},
        {"campo": "fecha", "etiqueta": "Fecha"}, {"campo": "documento_num", "etiqueta": "Documento núm."},
        {"campo": "fecha_inicio", "etiqueta": "Fecha de inicio"}, {"campo": "fecha_fin_esperada", "etiqueta": "Fin esperado"},
        {"campo": "fecha_fin_real", "etiqueta": "Fin real"},
        {"campo": "caso_negocio", "etiqueta": "1. Caso de negocio", "tipo": "largo",
         "ayuda": "Como compañía, el desempeño de nuestro ___ en el área de ___ no está cumpliendo ___ (PL14; DEF-CHARTER)."},
        {"campo": "alcance", "etiqueta": "4. Alcance (dentro y fuera)", "tipo": "largo"},
        {"campo": "recursos", "etiqueta": "6. Recursos", "tipo": "largo"},
        {"campo": "enfoque", "etiqueta": "Enfoque de desarrollo (Gestión > Enfoque de desarrollo)", "calc": True},
        {"campo": "requisitos", "etiqueta": "Requisitos de alto nivel (PMBOK 6, 4.1.3.1)", "tipo": "largo"},
        {"campo": "riesgo_general", "etiqueta": "Riesgo general del proyecto", "tipo": "largo"},
        {"campo": "presupuesto", "etiqueta": "Recursos financieros preaprobados", "tipo": "numero"},
        {"campo": "interesados_clave", "etiqueta": "Interesados clave", "tipo": "largo"},
        {"campo": "interesados_registro", "etiqueta": "Interesados en el registro", "calc": True},
        {"campo": "criterios_aprobacion", "etiqueta": "Requisitos de aprobación: qué es éxito, quién lo decide y quién firma", "tipo": "largo"},
        {"campo": "criterios_salida", "etiqueta": "Criterios de salida: condiciones para cerrar o cancelar el proyecto o fase", "tipo": "largo"},
        {"campo": "autoridad_lider", "etiqueta": "Autoridad del líder del proyecto", "tipo": "largo"},
        {"campo": "patrocinador", "etiqueta": "Patrocinador que autoriza (nombre)"},
        {"campo": "autoridad_patrocinador", "etiqueta": "Autoridad del patrocinador"},
        {"campo": "preparado_por", "etiqueta": "Preparado por", "fijo": "responsable"}, {"campo": "preparado_fecha", "etiqueta": "Fecha de preparación"},
        {"campo": "aprobado_por", "etiqueta": "Aprobado por"}, {"campo": "aprobado_fecha", "etiqueta": "Fecha de aprobación"}]
    TABLAS = [
        {"id": "proposito", "titulo": "2. Propósito: CTQ con línea base y objetivo", "filas": 2, "columnas": [
            {"campo": "ctq", "etiqueta": "CTQ", "ancho": 220}, {"campo": "base", "etiqueta": "Línea base", "ancho": 100},
            {"campo": "objetivo", "etiqueta": "Objetivo", "ancho": 100}]},
        {"id": "objetivos", "titulo": "3. Objetivos del proyecto", "filas": 2, "columnas": [
            {"campo": "ctq", "etiqueta": "CTQ", "ancho": 220}, {"campo": "base", "etiqueta": "Línea base", "ancho": 100},
            {"campo": "objetivo", "etiqueta": "Objetivo", "ancho": 100}, {"campo": "ahorro", "etiqueta": "Ahorro", "tipo": "numero", "ancho": 100}]},
        {"id": "equipo", "titulo": "5. Roles y responsabilidades", "filas": 5, "columnas": [
            {"campo": "rol", "etiqueta": "Rol", "tipo": "opcion", "ancho": 130, "opciones": [["", ""], ["Champion", "Champion"], ["Sponsor", "Sponsor"],
                                                                                      ["Líder", "Líder"], ["Miembro", "Miembro"]]},
            {"campo": "nombre", "etiqueta": "Nombre", "ancho": 170}, {"campo": "email", "etiqueta": "Correo", "ancho": 170},
            {"campo": "tel", "etiqueta": "Teléfono", "ancho": 110}]},
        {"id": "hitos", "titulo": "Cronograma resumido de hitos (PMBOK 6, 4.1.3.1)", "filas": 4, "columnas": [
            {"campo": "hito", "etiqueta": "Hito", "ancho": 260}, {"campo": "fecha", "etiqueta": "Fecha (DD/MM/AAAA)", "ancho": 120}]},
        {"id": "metricas", "titulo": "7. Métricas", "filas": 5, "columnas": [
            {"campo": "metrica", "etiqueta": "Métrica", "ancho": 200}, {"campo": "actual", "etiqueta": "Actual", "ancho": 90},
            {"campo": "objetivo", "etiqueta": "Objetivo", "ancho": 90}, {"campo": "comentario", "etiqueta": "Comentario", "ancho": 220}]}]
    NOTA = ("Siete secciones de la plantilla del curso Green Belt (PL14, PROJECT-CHARTER-GB), más el contenido del acta del PMBOK 6, 4.1.3.1: "
            "requisitos de alto nivel, riesgo general, hitos, recursos financieros preaprobados, interesados clave, requisitos de aprobación, "
            "criterios de salida, autoridad del líder y nombre y autoridad del patrocinador que la autoriza (PMBOK 7, 4.6.1 y apéndice X2). "
            "En Lean Six Sigma el Champion cumple el papel de patrocinador (01_MARCO_Y_ROLES).")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c, av = d["cabecera"], []
        faltan = [n for k, n in (("caso_negocio", "caso de negocio"), ("alcance", "alcance")) if not c.get(k)]
        if faltan: av.append("Falta: " + ", ".join(faltan) + ".")
        if not any(f.get("ctq") for f in d["tablas"]["objetivos"]): av.append("Falta al menos un objetivo con su CTQ.")
        roles = {f.get("rol") for f in d["tablas"]["equipo"]}
        if "Líder" not in roles or not ({"Champion", "Sponsor"} & roles): av.append("Define al menos un líder y un champion o sponsor.")
        if not c.get("patrocinador"): av.append("Falta el patrocinador que autoriza el proyecto (PMBOK 6, 4.1.3.1): sin él el acta no autoriza formalmente.")
        if not c.get("criterios_aprobacion"): av.append("Falta definir qué es éxito, quién lo decide y quién firma (requisitos de aprobación).")
        if not c.get("criterios_salida"): av.append("Faltan los criterios de salida: condiciones para cerrar o cancelar.")
        if not any(f.get("hito") for f in d["tablas"]["hitos"]): av.append("Falta el cronograma resumido de hitos.")
        ahorros = [a_numero(f.get("ahorro") or "") for f in d["tablas"]["objetivos"] if not fila_vacia(f)]       # A1: vacío no es cero
        dados = [x for x in ahorros if x is not None]
        bloques = [{"tipo": "texto", "clase": "conclusion", "texto": f"Ahorro total esperado: {num(sum(dados), 2)} (base: {len(dados)} de {len(ahorros)} "
                    f"objetivos con ahorro capturado" + ("; los demás quedan sin dato, no cuentan como cero)" if len(dados) < len(ahorros) else ")")}] if dados else []
        if dados and len(dados) < len(ahorros): av.append(f"{len(ahorros) - len(dados)} objetivos sin ahorro capturado: el total solo suma los que lo tienen.")
        cab = {}
        enf = ((proyecto.formatos.get("ENFOQUE") or {}).get("cabecera") or {}).get("elegido") if proyecto is not None else None
        if enf: cab["enfoque"] = enf
        reg = (proyecto.formatos.get("INTERESADOS") or {}).get("tablas", {}) if proyecto is not None else {}
        nombres = [f.get("nombre") for f in reg.get("registro", []) if f.get("nombre")]
        if nombres:
            an = reg.get("analisis", [])
            clave = [n for n, a in zip([f.get("nombre") for f in reg.get("registro", [])], an + [{}] * len(nombres)) if n and a.get("poder") == "Alto"]
            cab["interesados_registro"] = f"{len(nombres)} en el registro" + (f"; poder alto: {', '.join(clave[:6])}" if clave else "")
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av, "bloques": bloques}


# ---------------- SIPOC ----------------
@formato
class Sipoc(Formato):
    ID, TITULO = "SIPOC", "Diagrama SIPOC"
    CABECERA = [{"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"}, {"campo": "proceso", "etiqueta": "Proceso"},
                {"campo": "inicio", "etiqueta": "Inicia en"}, {"campo": "fin", "etiqueta": "Termina en"}]
    TABLAS = [
        {"id": "entradas", "titulo": "Proveedores y entradas", "filas": 5, "columnas": [
            {"campo": "proveedor", "etiqueta": "Proveedor", "ancho": 140}, {"campo": "entrada", "etiqueta": "Entrada", "ancho": 160},
            {"campo": "m6", "etiqueta": "6M", "tipo": "opcion", "opciones": M6, "ancho": 120},
            {"campo": "tipo", "etiqueta": "Tipo", "tipo": "opcion", "ancho": 110,
             "opciones": [["", ""], ["N", "N · ruido"], ["C", "C · controlable"], ["S", "S · estándar"], ["X", "X · crítica"]],
             "ayuda": "Clasificación de entradas: ruido, controlable, estándar o crítica (14_GB_MEDIR, MED-CLASIF)."},
            {"campo": "cantidad", "etiqueta": "Cantidad", "ancho": 80}, {"campo": "requisitos", "etiqueta": "Requisitos de entrada", "ancho": 180}]},
        {"id": "proceso", "titulo": "Proceso, salidas y clientes", "filas": 5, "columnas": [
            {"campo": "paso", "etiqueta": "Paso del proceso", "ancho": 170}, {"campo": "salida", "etiqueta": "Salida", "ancho": 160},
            {"campo": "requisitos", "etiqueta": "Requisitos de salida", "ancho": 180}, {"campo": "cliente", "etiqueta": "Cliente", "ancho": 140}]}]
    NOTA = ("SIPOC del curso Green Belt (PL10, SIPOC-GB; 03_SOLUCION_PROBLEMAS, PS-SIPOC): entradas con proveedor, 6M, tipo, cantidad y "
            "requisitos; por cada paso, la salida, sus requisitos y el cliente. Los requisitos deben ser numéricos, específicos y "
            "cuantitativos (14_GB_MEDIR).")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        av = []
        sin_req = [str(i + 1) for i, f in enumerate(d["tablas"]["entradas"]) if not fila_vacia(f) and f.get("tipo") in ("C", "X") and not f.get("requisitos")]
        if sin_req: av.append(f"Entradas controlables o críticas sin requisito: filas {', '.join(sin_req)}.")
        pasos = [f for f in d["tablas"]["proceso"] if not fila_vacia(f)]
        if pasos and not (4 <= len(pasos) <= 7): av.append(f"El proceso tiene {len(pasos)} pasos; a nivel macro suelen ser de 4 a 7 [GENERAL].")
        return {"cab": {}, "calc": {}, "clases": {}, "avisos": av}


# ---------------- ISHIKAWA ----------------
def diagrama_ishikawa(efecto, causas):
    """Espina de pescado con las 6M (03_SOLUCION_PROBLEMAS, PS-ISHIKAWA). Devuelve (svg, png)."""
    fig, ax = figura(9.6, 4.6)
    ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 6)
    ax.annotate("", xy=(8.2, 3), xytext=(0.3, 3), arrowprops={"arrowstyle": "-|>", "color": TINTA, "lw": 1.8})
    ax.text(8.3, 3, efecto or "Efecto (problema)", va="center", ha="left", fontsize=9, fontweight="bold", color=TINTA, wrap=True,
            bbox={"boxstyle": "round,pad=0.4", "fc": CLARO, "ec": NARANJA})
    cats = [c for _, c in M6[1:]]
    xs = [1.6, 4.0, 6.4]
    for k, cat in enumerate(cats):
        arriba = k < 3; x = xs[k % 3]; y0 = 5.4 if arriba else 0.6
        ax.plot([x, x + 1.2], [y0, 3], color=SUAVE, lw=1.2)
        ax.text(x, y0 + (0.18 if arriba else -0.18), cat, ha="center", va="bottom" if arriba else "top", fontsize=8.5, fontweight="bold", color=NARANJA)
        lista = causas.get(cat, [])[:5]
        for j, t in enumerate(lista):
            fr = (j + 1) / (len(lista) + 1)
            yy = y0 + (3 - y0) * fr; xx = x + 1.2 * fr
            ax.plot([xx - 1.0, xx], [yy, yy], color=SUAVE, lw=0.7)
            ax.text(xx - 0.08, yy + 0.05, t[:34] + ("…" if len(t) > 34 else ""), ha="right", va="bottom", fontsize=6.8, color=TINTA)
        if len(causas.get(cat, [])) > 5:
            ax.text(x + 1.25, (y0 + 3) / 2, f"+{len(causas[cat]) - 5}", fontsize=7, color=SUAVE)
    return a_svg_png(fig)


@formato
class Ishikawa(Formato):
    ID, TITULO = "ISHIKAWA", "Diagrama de Ishikawa"
    CABECERA = [{"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
                {"campo": "efecto", "etiqueta": "Efecto (problema, en una frase específica)", "tipo": "largo"},
                {"campo": "fecha", "etiqueta": "Fecha"}, {"campo": "equipo", "etiqueta": "Equipo"}]
    TABLAS = [{"id": "causas", "titulo": "Causas potenciales por categoría (6M)", "filas": 8, "columnas": [
        {"campo": "categoria", "etiqueta": "Categoría (6M)", "tipo": "opcion", "opciones": M6, "ancho": 140},
        {"campo": "causa", "etiqueta": "Causa potencial", "ancho": 240}, {"campo": "subcausa", "etiqueta": "Subcausa o detalle", "ancho": 200},
        {"campo": "verificada", "etiqueta": "Verificada con datos", "tipo": "opcion", "ancho": 110,
         "opciones": [["", ""], ["Pendiente", "Pendiente"], ["Sí, es causa", "Sí, es causa"], ["No es causa", "No es causa"]]}]}]
    NOTA = ("Diagrama causa-efecto con las 6M: mano de obra, materiales, métodos, máquinas, medio ambiente y mediciones "
            "(03_SOLUCION_PROBLEMAS, PS-ISHIKAWA). Las causas son potenciales hasta verificarlas con datos; las verificadas pasan "
            "a los 5 Porqués o al análisis estadístico.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        causas, av = {}, []
        sin_cat = 0
        for f in d["tablas"]["causas"]:
            if not f.get("causa"): continue
            if not f.get("categoria"): sin_cat += 1; continue
            causas.setdefault(f["categoria"], []).append(f["causa"] + (" (verificada)" if f.get("verificada") == "Sí, es causa" else ""))
        if sin_cat: av.append(f"{sin_cat} causas sin categoría no aparecen en el diagrama.")
        vacias = [c for _, c in M6[1:] if c not in causas]
        if causas and vacias: av.append("Categorías sin causas: " + ", ".join(vacias) + ". Revisa si de verdad no aplican.")
        svg, png = diagrama_ishikawa(d["cabecera"].get("efecto"), causas)
        return {"cab": {}, "calc": {}, "clases": {}, "avisos": av, "bloques": [{"tipo": "grafica", "svg": svg}], "png": png}


# ---------------- 5 PORQUÉS ----------------
@formato
class CincoPq(Formato):
    ID, TITULO = "CINCO-PQ", "5 Porqués"
    CABECERA = [{"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
                {"campo": "problema", "etiqueta": "Problema (enunciado específico)", "tipo": "largo",
                 "ayuda": "Ejemplo del curso: «La maleta está perdida», no «Se perdió la maleta» (EJ-PS-DEFINICION)."},
                {"campo": "causa_raiz", "etiqueta": "Causa raíz", "tipo": "largo"},
                {"campo": "accion", "etiqueta": "Acción permanente", "tipo": "largo"},
                {"campo": "responsable", "etiqueta": "Responsable de la acción"}, {"campo": "fecha", "etiqueta": "Fecha compromiso"}]
    TABLAS = [{"id": "porques", "titulo": "Cadena de por qués", "filas": 5, "columnas": [
        {"campo": "respuesta", "etiqueta": "¿Por qué? (respuesta)", "ancho": 360},
        {"campo": "evidencia", "etiqueta": "Evidencia", "ancho": 220},
        {"campo": "verificado", "etiqueta": "Verificado", "tipo": "opcion", "opciones": SI_NO, "ancho": 80}]}]
    NOTA = ("Se pregunta «por qué» hasta la causa raíz y se verifica la cadena en sentido inverso con «entonces» (03_SOLUCION_PROBLEMAS, "
            "PS-5PQ). Cinco es una guía: detenerse en una causa sobre la que se pueda actuar de forma permanente [COMP].")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c, av = d["cabecera"], []
        cadena = [f["respuesta"] for f in d["tablas"]["porques"] if f.get("respuesta")]
        bloques = []
        if cadena:
            inversa = list(reversed(cadena)) + ([c["problema"]] if c.get("problema") else [])
            bloques.append({"tipo": "texto", "clase": "conclusion",
                            "texto": "Lectura inversa: " + " → entonces ".join(t.rstrip(".") for t in inversa) + "."})
            sin_ev = sum(1 for f in d["tablas"]["porques"] if f.get("respuesta") and f.get("verificado") != "Sí")
            if sin_ev: av.append(f"{sin_ev} eslabones sin verificar.")
        if cadena and not c.get("causa_raiz"): av.append("Anota la causa raíz (normalmente el último por qué).")
        if c.get("causa_raiz") and not c.get("accion"): av.append("Falta la acción permanente sobre la causa raíz.")
        return {"cab": {}, "calc": {}, "clases": {}, "avisos": av, "bloques": bloques}
