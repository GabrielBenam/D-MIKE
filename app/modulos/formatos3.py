"""Formatos de la base LSS agregados en v0.13: SMED (PL02), GANTT-DMAIC, 4Qs y A3 (PL08), KAIZEN y TARJETAS (PL01),
MUDAS (PL03) y KATA (PL07). Los campos salen de las fichas de esos archivos; los cálculos y avisos, de sus
«Revisión de calidad» y «Cálculos»."""
from datetime import date, timedelta
from .formatos import Formato, formato, fila_vacia
from .base import num
from ..nucleo.hoja import a_numero, a_fecha

X = [["", ""], ["X", "X"]]
SI = lambda *v: [["", ""]] + [[x, x] for x in v]


def f_txt(c, t=None, **k): return {"campo": c, "etiqueta": t or c.replace("_", " ").capitalize(), **k}


def fecha(d): return a_fecha(d.strip()) if d and d.strip() else None


# ---------------- SMED ----------------
@formato
class Smed(Formato):
    ID, TITULO = "SMED", "SMED (cambio de producto)"
    CABECERA = [f_txt("proyecto", "Proyecto", fijo="nombre_proyecto"), f_txt("fecha", "Fecha (DD/MM/AAAA)"), f_txt("area", "Área", fijo="cliente_area"),
                f_txt("clasificacion", "Clasificación del cambio"), f_txt("kaizen", "Evento Kaizen"),
                {"campo": "unidad", "etiqueta": "Unidad de tiempo (no mezclar)", "tipo": "opcion", "opciones": [["min", "minutos"], ["s", "segundos"]], "defecto": "min"},
                f_txt("total_real", "Tiempo total real", calc=True), f_txt("total_pot", "Tiempo total potencial", calc=True),
                f_txt("desp_real", "Desperdicio real", calc=True), f_txt("desp_pot", "Desperdicio potencial", calc=True),
                f_txt("ahorro", "Ahorro posible", calc=True), f_txt("observaciones", "Observaciones", tipo="largo")]
    TABLAS = [{"id": "ops", "titulo": "Operaciones del cambio (0 a 21), empezando con la máquina parada", "filas": 22, "columnas": [
        {"campo": "operacion", "etiqueta": "Operación", "ancho": 220},
        *[{"campo": f"op{k}", "etiqueta": f"Op. {k}", "tipo": "opcion", "opciones": X, "ancho": 52} for k in range(1, 6)],
        {"campo": "acumulado", "etiqueta": "Acumulado", "calc": True, "ancho": 80},
        {"campo": "real", "etiqueta": "Tiempo real", "tipo": "numero", "ancho": 76}, {"campo": "pot", "etiqueta": "Tiempo potencial", "tipo": "numero", "ancho": 84},
        {"campo": "clase", "etiqueta": "Clasificación", "tipo": "opcion", "opciones": SI("Interna", "Externa", "Desperdicio"), "ancho": 110},
        {"campo": "comentario", "etiqueta": "Comentario", "ancho": 200}]}]
    NOTA = ("PL02 SMED-FORMATO: acumulado = suma del tiempo real hasta la fila; totales = suma de la columna; desperdicio = tiempo clasificado como desperdicio. "
            "Revisión de calidad de la base: la suma de los reales debe coincidir con el tiempo del video; el potencial no debe superar al real sin explicación; "
            "lo externo debe poder hacerse con la máquina en marcha. Prerrequisito: 5S. Meta del dígito único de minuto: menos de 10 minutos.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = d["tablas"]["ops"]; cc, kk, av = [], [], []
        acum = tot_r = tot_p = dr = dp = 0.0; interna = externa = 0.0
        for i, f in enumerate(filas):
            c, k = {}, {}
            if fila_vacia(f): cc.append(c); kk.append(k); continue
            r, p = a_numero(f.get("real") or ""), a_numero(f.get("pot") or "")
            for campo in ("real", "pot"):
                if f.get(campo) and a_numero(f[campo]) is None: k[campo] = "mal"
            if r is not None:
                acum += r; tot_r += r; c["acumulado"] = num(acum, 3)
                if f.get("clase") == "Desperdicio": dr += r
                if f.get("clase") == "Interna": interna += r
                if f.get("clase") == "Externa": externa += r
            if p is not None:
                tot_p += p
                if f.get("clase") == "Desperdicio": dp += p
            if r is not None and p is not None and p > r: k["pot"] = "alerta"; av.append(f"Operación {i}: el tiempo potencial supera al real; explícalo en el comentario.")
            if f.get("real") and not f.get("clase"): k["clase"] = "falta"
            cc.append(c); kk.append(k)
        u = d["cabecera"].get("unidad") or "min"
        cab = {}
        if tot_r or tot_p:
            cab = {"total_real": f"{num(tot_r, 3)} {u}", "total_pot": f"{num(tot_p, 3)} {u}", "desp_real": f"{num(dr, 3)} {u}", "desp_pot": f"{num(dp, 3)} {u}",
                   "ahorro": f"{num(tot_r - tot_p, 3)} {u}" + (f" ({100 * (tot_r - tot_p) / tot_r:.0f}%)" if tot_r else "")}
            if externa and externa >= interna: av.append("Hay más tiempo externo que interno: pasa lo externo a hacerse con la máquina en marcha.")
            if u == "min" and tot_p >= 10: av.append("El potencial es de 10 minutos o más; la meta del dígito único de minuto es menos de 10 (PL02).")
        return {"cab": cab, "calc": {"ops": cc}, "clases": {"ops": kk}, "avisos": av}


# ---------------- GANTT DMAIC ----------------
FASES_G = [("definicion", "Definición", 5), ("medir", "Medir y mapear", 5), ("analizar", "Analizar", 5), ("implementar", "Implementar", 5), ("controlar", "Controlar", 2)]


def _barras(filas_g, ini):
    """Gantt SVG sencillo de 12 semanas. filas_g: [(texto, s0, s1, color)]."""
    w, lh, izq = 760, 20, 190; alto = 26 + lh * len(filas_g) + 6
    s = [f'<svg viewBox="0 0 {w} {alto}" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="Montserrat,Segoe UI,sans-serif" font-size="10">']
    cw = (w - izq - 6) / 12
    for k in range(12):
        x = izq + k * cw
        s.append(f'<text x="{x + cw / 2:.1f}" y="12" text-anchor="middle" fill="#6f675b">S{k + 1}</text>')
        if ini: s.append(f'<text x="{x + cw / 2:.1f}" y="23" text-anchor="middle" fill="#a79f92" font-size="8">{(ini + timedelta(days=7 * k)).strftime("%d/%m")}</text>')
        s.append(f'<line x1="{x:.1f}" y1="26" x2="{x:.1f}" y2="{alto - 4}" stroke="#e9e4da"/>')
    for r, (t, a, b, col) in enumerate(filas_g):
        y = 28 + r * lh
        s.append(f'<text x="4" y="{y + 12}" fill="#2b2620">{t[:34].replace("&", "y").replace("<", "")}</text>')
        if a is not None:
            s.append(f'<rect x="{izq + (a - 1) * cw + 1:.1f}" y="{y + 2}" width="{(b - a + 1) * cw - 2:.1f}" height="{lh - 6}" rx="3" fill="{col}"/>')
    return "".join(s) + "</svg>"


@formato
class Gantt(Formato):
    ID, TITULO = "GANTT", "Cronograma DMAIC (Gantt de 12 semanas)"
    CABECERA = [f_txt("proyecto", "Proyecto (unos 30 caracteres)", fijo="nombre_proyecto"), f_txt("semana1", "Fecha de la semana 1 (un lunes, DD/MM/AAAA)")]
    TABLAS = [{"id": fid, "titulo": nom, "filas": n, "columnas": [
        {"campo": "actividad", "etiqueta": "Actividad", "ancho": 240}, {"campo": "inicio", "etiqueta": "Inicio (DD/MM/AAAA)", "ancho": 110},
        {"campo": "fin", "etiqueta": "Fin (DD/MM/AAAA)", "ancho": 110}, {"campo": "dias", "etiqueta": "Días", "calc": True, "ancho": 56},
        {"campo": "semanas", "etiqueta": "Semanas", "calc": True, "ancho": 90}, {"campo": "comentario", "etiqueta": "Comentario", "ancho": 200}]}
        for fid, nom, n in FASES_G]
    NOTA = ("PL08 GANTT-DMAIC: proyecto de 12 semanas en cinco fases (5, 5, 5, 5 y 2 actividades). Las semanas activas se calculan con las fechas de inicio y fin "
            "y la fecha de la semana 1. Si una actividad pasa de la semana 12 la plantilla no la cubre. Aquí las fechas se escriben DD/MM/AAAA (la plantilla del curso "
            "usa mes-día-año).")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        s1 = fecha(d["cabecera"].get("semana1")); av, calc, clases, barras = [], {}, {}, []
        if d["cabecera"].get("semana1") and s1 is None: av.append("La fecha de la semana 1 no es válida (usa DD/MM/AAAA).")
        elif s1 and s1.weekday() != 0: av.append("La semana 1 debería iniciar en lunes.")
        colores = ["#dd5813", "#2b6f8f", "#7a8c2e", "#8b4f9e", "#b8860b"]
        for q, (fid, nom, n) in enumerate(FASES_G):
            cc, kk = [], []
            for i, f in enumerate(d["tablas"][fid]):
                c, k = {}, {}
                a, b = fecha(f.get("inicio")), fecha(f.get("fin"))
                for campo in ("inicio", "fin"):
                    if f.get(campo) and fecha(f[campo]) is None: k[campo] = "mal"
                if a and b:
                    if b < a: k["fin"] = "mal"; av.append(f"{nom}, fila {i + 1}: el fin es anterior al inicio.")
                    else:
                        c["dias"] = str((b - a).days + 1)
                        if s1:
                            w0, w1 = (a - s1).days // 7 + 1, (b - s1).days // 7 + 1
                            c["semanas"] = f"{max(w0, 1)} a {w1}" if w1 != w0 else str(w0)
                            if w0 < 1: av.append(f"{nom}, fila {i + 1}: empieza antes de la semana 1.")
                            if w1 > 12: k["fin"] = "alerta"; av.append(f"{nom}, fila {i + 1}: pasa de la semana 12 (la plantilla cubre 12).")
                            barras.append((f"{nom.split()[0]}: {f.get('actividad') or ''}", max(w0, 1), min(w1, 12), colores[q]))
                elif f.get("actividad"):
                    barras.append((f"{nom.split()[0]}: {f['actividad']}", None, None, colores[q]))
                cc.append(c); kk.append(k)
            calc[fid] = cc; clases[fid] = kk
        bl = [{"tipo": "grafica", "svg": _barras(barras, s1)}] if barras else []
        return {"cab": {}, "calc": calc, "clases": clases, "avisos": av, "bloques": bl}


# ---------------- 4Qs ----------------
@formato
class CuatroQ(Formato):
    ID, TITULO = "CUATRO-Q", "4 Preguntas (4Qs)"
    CABECERA = [f_txt("area", "Área", fijo="cliente_area"), f_txt("fecha", "Fecha (DD/MM/AAAA)"), f_txt("semana", "Semana"),
                f_txt("metrico", "Métrico (qué se mide)"), f_txt("objetivo", "Objetivo"),
                f_txt("acciones", "Acciones (resumen)", tipo="largo")]
    TABLAS = [{"id": "porques", "titulo": "5 Porqués", "filas": 5, "fijas": True, "columnas": [
                  {"campo": "respuesta", "etiqueta": "¿Por qué?", "ancho": 460}]},
              {"id": "plan", "titulo": "Plan de acciones", "filas": 4, "columnas": [
                  {"campo": "accion", "etiqueta": "Acción", "ancho": 300}, {"campo": "responsable", "etiqueta": "Responsable", "ancho": 130},
                  {"campo": "fecha", "etiqueta": "Fecha compromiso", "ancho": 120},
                  {"campo": "estado", "etiqueta": "Estado", "tipo": "opcion", "opciones": SI("Pendiente", "En curso", "Hecha"), "ancho": 100}]}]
    NOTA = "PL08 4QS: métrico y objetivo, cinco porqués y acciones. Se revisa en el seguimiento semanal; cierra con acciones concretas, responsable y fecha (03_SOLUCION_PROBLEMAS, formato 4 Q's)."

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        av = []; cadena = [f["respuesta"] for f in d["tablas"]["porques"] if f.get("respuesta")]
        if cadena and not d["cabecera"].get("metrico"): av.append("Indica el métrico: qué se está midiendo.")
        sin = sum(1 for f in d["tablas"]["plan"] if f.get("accion") and not (f.get("responsable") and f.get("fecha")))
        if sin: av.append(f"{sin} acciones sin responsable o fecha.")
        return {"cab": {}, "calc": {}, "clases": {}, "avisos": av}

    @classmethod
    def vacio(cls):
        return super().vacio()


# ---------------- A3 ----------------
@formato
class A3(Formato):
    ID, TITULO = "A3", "Informe A3"
    CABECERA = [f_txt("compania", "Compañía"), f_txt("titulo", "Título"), f_txt("control", "Control (número)"), f_txt("fecha", "Fecha"),
                f_txt("responsable", "Responsable", fijo="responsable"),
                f_txt("antecedentes", "1. Antecedentes", tipo="largo"), f_txt("condiciones_actuales", "2. Condiciones actuales", tipo="largo"),
                f_txt("metas_objetivos", "3. Metas y objetivos", tipo="largo"), f_txt("analisis", "4. Análisis", tipo="largo"),
                f_txt("recomendaciones_mejoras", "5. Recomendaciones y mejoras", tipo="largo"), f_txt("plan", "6. Plan", tipo="largo"),
                f_txt("seguimiento_control", "7. Seguimiento y control", tipo="largo")]
    TABLAS = []
    NOTA = "PL08 A3: una hoja que cuenta el problema de izquierda a derecha, de antecedentes a seguimiento. Las secciones vienen de la ficha del curso."

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c = d["cabecera"]; llenas = [k for k in ("antecedentes", "condiciones_actuales", "metas_objetivos", "analisis", "recomendaciones_mejoras", "plan", "seguimiento_control") if c.get(k)]
        av = []
        if llenas and len(llenas) < 7: av.append(f"Faltan {7 - len(llenas)} de las 7 secciones del A3.")
        if c.get("metas_objetivos") and not any(ch.isdigit() for ch in c["metas_objetivos"]): av.append("La meta debería ser medible (con un número y una fecha).")
        return {"cab": {}, "calc": {}, "clases": {}, "avisos": av}


# ---------------- Kaizen ----------------
@formato
class Kaizen(Formato):
    ID, TITULO = "KAIZEN", "Evento Kaizen (Kaizen Charter)"
    CABECERA = [f_txt("clave", "Clave"), f_txt("nombre_proyecto", "Nombre del evento", fijo="nombre_proyecto"), f_txt("directriz", "Directriz"),
                f_txt("estrategias", "Estrategias"), f_txt("oportunidad", "Oportunidad", tipo="largo"), f_txt("propuesta", "Propuesta", tipo="largo"),
                f_txt("fecha_inicio", "Fecha de inicio"), f_txt("horas", "Horas requeridas", tipo="numero"), f_txt("fecha_promesa", "Fecha promesa"),
                f_txt("fecha_fin", "Fecha de finalización"), f_txt("alcance", "Alcance", tipo="largo"), f_txt("herramientas", "Herramientas"),
                f_txt("entregables", "Entregables", tipo="largo")]
    TABLAS = [{"id": "equipo", "titulo": "Equipo", "filas": 6, "columnas": [
        {"campo": "nombre", "etiqueta": "Nombre", "ancho": 200}, {"campo": "rol", "etiqueta": "Rol", "ancho": 150}, {"campo": "area", "etiqueta": "Área", "ancho": 150}]}]
    NOTA = "PL01 KAIZEN-CHARTER: ficha del evento. La fecha promesa y la de finalización permiten ver cumplimiento; las horas requeridas ayudan a planear al equipo."

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c, av = d["cabecera"], []
        a, b, pr = fecha(c.get("fecha_inicio")), fecha(c.get("fecha_fin")), fecha(c.get("fecha_promesa"))
        if a and b and b < a: av.append("La fecha de finalización es anterior al inicio.")
        if b and pr and b > pr: av.append(f"El evento terminó {(b - pr).days} días después de la fecha promesa.")
        if not c.get("alcance") and (c.get("oportunidad") or c.get("propuesta")): av.append("Define el alcance del evento (qué entra y qué no).")
        if not any(f.get("nombre") for f in d["tablas"]["equipo"]) and c.get("oportunidad"): av.append("Falta el equipo.")
        return {"cab": {}, "calc": {}, "clases": {}, "avisos": av}


# ---------------- Tarjetas de oportunidad ----------------
@formato
class Tarjetas(Formato):
    ID, TITULO = "TARJETAS", "Listado de oportunidades (tarjetas)"
    CABECERA = [f_txt("evento", "Evento Kaizen o proceso"), f_txt("resumen", "Resumen", calc=True)]
    TABLAS = [{"id": "op", "titulo": "Oportunidades", "filas": 10, "columnas": [
        {"campo": "fecha", "etiqueta": "Fecha", "ancho": 100}, {"campo": "folio", "etiqueta": "Folio", "ancho": 70}, {"campo": "area", "etiqueta": "Área", "ancho": 110},
        {"campo": "oportunidad", "etiqueta": "Oportunidad", "ancho": 240}, {"campo": "propuesta", "etiqueta": "Propuesta", "ancho": 240},
        {"campo": "por", "etiqueta": "Propuesto por", "ancho": 120}, {"campo": "observaciones", "etiqueta": "Observaciones", "ancho": 180},
        {"campo": "estado", "etiqueta": "Estado", "tipo": "opcion", "opciones": SI("Nueva", "Aprobada", "En curso", "Hecha", "Descartada"), "ancho": 100},
        {"campo": "esfuerzo", "etiqueta": "Esfuerzo (1 a 5)", "tipo": "opcion", "opciones": SI("1", "2", "3", "4", "5"), "ancho": 90},
        {"campo": "valor", "etiqueta": "Valor (1 a 5)", "tipo": "opcion", "opciones": SI("1", "2", "3", "4", "5"), "ancho": 90},
        {"campo": "cuadrante", "etiqueta": "Prioridad", "calc": True, "ancho": 130}]}]
    NOTA = ("PL01 TARJETA-OPORTUNIDAD y LISTADO-OPORTUNIDADES: una tarjeta por oportunidad con fecha, folio, área, propuesta y quién la propone. "
            "Matriz de priorización de PMBOK 7, 4.6.6: esfuerzo en el eje horizontal y valor en el vertical, en cuatro cuadrantes. Los nombres de los "
            "cuadrantes y el corte en 3 son [criterio de uso].")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = [f for f in d["tablas"]["op"] if not fila_vacia(f)]; av = []
        folios = [f.get("folio") for f in filas if f.get("folio")]
        if len(folios) != len(set(folios)): av.append("Hay folios repetidos.")
        por_area, por_estado = {}, {}
        for f in filas:
            por_area[f.get("area") or "(sin área)"] = por_area.get(f.get("area") or "(sin área)", 0) + 1
            por_estado[f.get("estado") or "Sin estado"] = por_estado.get(f.get("estado") or "Sin estado", 0) + 1
        cab = {"resumen": f"{len(filas)} oportunidades; " + ", ".join(f"{k}: {v}" for k, v in sorted(por_estado.items()))} if filas else {}
        cc, pts = [], []
        for i, f in enumerate(d["tablas"]["op"]):
            c = {}; e, v = a_numero(f.get("esfuerzo") or ""), a_numero(f.get("valor") or "")
            if e and v:
                c["cuadrante"] = ("Victoria rápida" if e <= 3 else "Proyecto mayor") if v >= 3 else ("Relleno" if e <= 3 else "Evitar")
                pts.append((f.get("folio") or str(i + 1), e, v))
            cc.append(c)
        bl = []
        if pts:
            w, h = 520, 330; s = '<rect x="50" y="10" width="460" height="280" fill="none" stroke="#c9bfae"/><line x1="280" x2="280" y1="10" y2="290" stroke="#c9bfae"/><line x1="50" x2="510" y1="150" y2="150" stroke="#c9bfae"/>'
            for x, y, t in ((56, 26, "Victorias rápidas"), (286, 26, "Proyectos mayores"), (56, 284, "Rellenos"), (286, 284, "Evitar")): s += f'<text x="{x}" y="{y}" fill="#dd5813" font-weight="600">{t}</text>'
            s += '<text x="280" y="320" text-anchor="middle" fill="#6f675b">Esfuerzo →</text><text x="20" y="150" fill="#6f675b" transform="rotate(-90 20 150)" text-anchor="middle">Valor →</text>'
            ocup = {}
            for fo, e, v in pts:
                k = ocup.get((e, v), 0); ocup[(e, v)] = k + 1
                x = 50 + (e - .5) * 92 + 14 * (k % 3); y = 290 - (v - .5) * 56 - 12 * (k // 3)
                s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="#2b2620"/><text x="{x:.1f}" y="{y + 3:.1f}" text-anchor="middle" fill="#fff" font-size="8">{str(fo)[:3]}</text>'
            bl = [{"tipo": "grafica", "svg": f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:600px" xmlns="http://www.w3.org/2000/svg" font-family="Montserrat,Segoe UI,sans-serif" font-size="10">{s}</svg>'}]
        sin = sum(1 for f in filas if f.get("oportunidad") and not f.get("propuesta"))
        if sin: av.append(f"{sin} oportunidades sin propuesta.")
        return {"cab": cab, "calc": {"op": cc}, "clases": {}, "avisos": av, "bloques": bl}


# ---------------- Mudas ----------------
MUDAS = ["Sobreproducción", "Retrabajo", "Transporte", "Sobreprocesamiento", "Inventario", "Espera", "Movimientos", "Defectos"]


@formato
class Mudas(Formato):
    ID, TITULO = "MUDAS", "Identificación de mudas"
    CABECERA = [f_txt("area", "Área", fijo="cliente_area"), f_txt("responsable", "Responsable", fijo="responsable"), f_txt("fecha", "Fecha")]
    TABLAS = [{"id": "mudas", "titulo": "Mudas observadas", "filas": 8, "fijas": True, "columnas": [
        {"campo": "muda", "etiqueta": "Muda", "ancho": 150}, {"campo": "observacion", "etiqueta": "Qué se observó (ejemplos)", "ancho": 320},
        {"campo": "impacto", "etiqueta": "Impacto", "tipo": "opcion", "opciones": SI("Alto", "Medio", "Bajo"), "ancho": 90},
        {"campo": "accion", "etiqueta": "Acción propuesta", "ancho": 240}]}]
    NOTA = "PL03 MUDAS: los ocho desperdicios de la plantilla. Califica el impacto y propón una acción por cada uno que observes."

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["mudas"] = [{"muda": m, "observacion": "", "impacto": "", "accion": ""} for m in MUDAS]; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = d["tablas"]["mudas"]; av = []
        altos = [f["muda"] for f in filas if f.get("impacto") == "Alto"]
        if altos: av.append("Impacto alto: " + ", ".join(altos) + ".")
        sin = [f["muda"] for f in filas if f.get("impacto") in ("Alto", "Medio") and not f.get("accion")]
        if sin: av.append("Sin acción propuesta: " + ", ".join(sin) + ".")
        return {"cab": {}, "calc": {}, "clases": {"mudas": [{"impacto": {"Alto": "no", "Medio": "advertencia", "Bajo": "ok"}.get(f.get("impacto"), "")} for f in filas]}, "avisos": av}


# ---------------- Kata ----------------
@formato
class Kata(Formato):
    ID, TITULO = "KATA", "Tablero Kata"
    CABECERA = [f_txt("proceso", "Proceso de enfoque", fijo=None), f_txt("reto", "Reto (largo plazo)", tipo="largo"),
                f_txt("objetivo", "Condición objetivo (medible y con fecha)", tipo="largo"), f_txt("actual", "Condición actual (con su dato)", tipo="largo"),
                f_txt("resumen", "Problemas", calc=True)]
    TABLAS = [{"id": "ciclos", "titulo": "Ciclos de mejora", "filas": 6, "columnas": [
                  {"campo": "fecha", "etiqueta": "Fecha", "ancho": 100}, {"campo": "obstaculo", "etiqueta": "Obstáculo", "ancho": 200},
                  {"campo": "experimento", "etiqueta": "Experimento", "ancho": 220}, {"campo": "resultado", "etiqueta": "Resultado", "ancho": 180},
                  {"campo": "aprendizaje", "etiqueta": "Aprendizaje", "ancho": 200}, {"campo": "coach", "etiqueta": "Coach", "ancho": 110}]},
              {"id": "problemas", "titulo": "Problemas por resolver, en curso y resueltos", "filas": 8, "columnas": [
                  {"campo": "problema", "etiqueta": "Problema", "ancho": 320},
                  {"campo": "estado", "etiqueta": "Estado", "tipo": "opcion", "opciones": SI("Por resolver", "Haciendo", "Hecho"), "ancho": 110}]}]
    NOTA = "PL07 KATA-TABLERO y KATA-CICLOS: proceso de enfoque, reto, condición objetivo y actual, ciclos de mejora y tres columnas de problemas."

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        pr = [f for f in d["tablas"]["problemas"] if f.get("problema")]; av = []
        cnt = {e: sum(1 for f in pr if f.get("estado") == e) for e in ("Por resolver", "Haciendo", "Hecho")}
        sin = len(pr) - sum(cnt.values())
        cab = {"resumen": f"Por resolver {cnt['Por resolver']} · Haciendo {cnt['Haciendo']} · Hecho {cnt['Hecho']}" + (f" · sin estado {sin}" if sin else "")} if pr else {}
        c = d["cabecera"]
        if c.get("objetivo") and not any(ch.isdigit() for ch in c["objetivo"]): av.append("La condición objetivo debería ser medible y llevar fecha (por ejemplo, en 4 meses producir X piezas por turno).")
        if cnt["Haciendo"] > 3: av.append("Hay más de 3 problemas en curso a la vez; el Kata trabaja un obstáculo por ciclo.")
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av}
