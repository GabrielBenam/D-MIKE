"""Formatos de gestión de proyectos, v0.16. Fuentes: PMBOK 6.ª edición (procesos y contenido de registros) y PMBOK 7.ª edición
(dominios de desempeño y artefactos). Se cita la sección en la NOTA de cada formato. Las escalas de probabilidad e impacto son
el ejemplo del PMBOK 6 (tabla 11-1 y figura 11-5): cada proyecto puede adaptarlas (11.1.3.1).
INTERESADOS, RIESGOS, LECCIONES, BITACORA, RACI, VALOR-GANADO, COSTO-CALIDAD y JUSTIFICACION."""
import math
from .formatos import Formato, formato, fila_vacia
from .formatos4 import SI, F, N, _svg, _t, barras_svg
from .base import num


def pct(x, d=1): return "no definido (denominador 0)" if x is None or x != x else f"{100 * x:.{d}f}%"


# ======================= INTERESADOS =======================
NIVELES = ["Sin conocimiento", "Resistente", "Neutral", "De apoyo", "Líder"]          # PMBOK 6, 13.2.2.5
NIV = SI(*NIVELES)
ALTO_BAJO = SI("Alto", "Bajo")
DIRECCION = SI("Ascendente", "Descendente", "Hacia afuera", "Lateral")


def cuadrante(poder, interes):
    """Cuadrícula poder/interés (PMBOK 6, 13.1.2.4). Las estrategias por cuadrante son de uso común [GENERAL, no en la base]."""
    if not poder or not interes: return ""
    return {("Alto", "Alto"): "Gestionar de cerca", ("Alto", "Bajo"): "Mantener satisfecho",
            ("Bajo", "Alto"): "Mantener informado", ("Bajo", "Bajo"): "Monitorear"}[(poder, interes)]


def prominencia(poder, urgencia, legitimidad):
    """Modelo de prominencia (PMBOK 6, 13.1.2.4; PMBOK 7, 4.2.7.5): cuántos de los tres atributos tiene el interesado.
    Los nombres de las clases (latente, expectante, definitivo) son de Mitchell, Agle y Wood [GENERAL]."""
    n = sum(1 for x in (poder, urgencia, legitimidad) if x == "Sí")
    return {0: "", 1: "Latente (1 atributo)", 2: "Expectante (2 atributos)", 3: "Definitivo (3 atributos)"}[n]


def matriz_compromiso_svg(filas):
    """Matriz de evaluación del compromiso: C actual y D deseado por interesado (PMBOK 6, figura 13-6)."""
    if not filas: return None
    w, iz, lh = 760, 200, 26; h = 34 + lh * len(filas); cw = (w - iz - 10) / 5
    s = ""
    for k, n in enumerate(NIVELES):
        x = iz + k * cw; s += f'<rect x="{x:.1f}" y="4" width="{cw - 2:.1f}" height="24" rx="4" fill="#fbe8dd"/><text x="{x + cw / 2:.1f}" y="20" text-anchor="middle" fill="#2b2620" font-weight="600">{n}</text>'
    for r, (nom, c, d) in enumerate(filas):
        y = 32 + r * lh
        s += f'<line x1="4" x2="{w - 6}" y1="{y + lh - 2}" y2="{y + lh - 2}" stroke="#e9e4da"/><text x="6" y="{y + 16}" fill="#2b2620">{_t(nom)[:28]}</text>'
        for etq, lvl, col in (("C", c, "#6f675b"), ("D", d, "#dd5813")):
            if lvl in NIVELES:
                k = NIVELES.index(lvl); dx = -10 if etq == "C" and lvl == d else 10 if etq == "D" and lvl == c else 0
                s += f'<circle cx="{iz + k * cw + cw / 2 + dx:.1f}" cy="{y + 11}" r="9" fill="{col}"/><text x="{iz + k * cw + cw / 2 + dx:.1f}" y="{y + 15}" text-anchor="middle" fill="#fff" font-weight="700">{etq}</text>'
        if c in NIVELES and d in NIVELES and c != d:
            x1, x2 = iz + NIVELES.index(c) * cw + cw / 2, iz + NIVELES.index(d) * cw + cw / 2
            s += f'<line x1="{x1 + (10 if x2 > x1 else -10):.1f}" x2="{x2 + (-10 if x2 > x1 else 10):.1f}" y1="{y + 11}" y2="{y + 11}" stroke="#dd5813" stroke-width="1.5" stroke-dasharray="4 3"/>'
    return _svg(w, h, s)


def poder_interes_svg(puntos):
    """Cuadrícula poder/interés con los nombres en su cuadrante."""
    if not puntos: return None
    w, h = 520, 330; s = '<rect x="40" y="10" width="470" height="290" fill="none" stroke="#c9bfae"/><line x1="275" x2="275" y1="10" y2="300" stroke="#c9bfae"/><line x1="40" x2="510" y1="155" y2="155" stroke="#c9bfae"/>'
    s += '<text x="275" y="322" text-anchor="middle" fill="#6f675b">Interés →</text><text x="16" y="155" fill="#6f675b" transform="rotate(-90 16 155)" text-anchor="middle">Poder →</text>'
    zonas = {("Alto", "Bajo"): (45, 24, "Mantener satisfecho"), ("Alto", "Alto"): (280, 24, "Gestionar de cerca"),
             ("Bajo", "Bajo"): (45, 169, "Monitorear"), ("Bajo", "Alto"): (280, 169, "Mantener informado")}
    for (x, y, t) in zonas.values(): s += f'<text x="{x}" y="{y}" fill="#dd5813" font-weight="600">{t}</text>'
    cont = {}
    for nom, p, i in puntos:
        if (p, i) not in zonas: continue
        x, y, _ = zonas[(p, i)]; n = cont.get((p, i), 0); cont[(p, i)] = n + 1
        if n < 8: s += f'<text x="{x + 6}" y="{y + 20 + 15 * n}" fill="#2b2620">• {_t(nom)[:26]}</text>'
        elif n == 8: s += f'<text x="{x + 6}" y="{y + 20 + 15 * n}" fill="#6f675b">y más…</text>'
    return _svg(w, h, s)


@formato
class Interesados(Formato):
    ID, TITULO, REDIBUJAR = "INTERESADOS", "Registro de interesados", True
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("resumen", "Resumen", calc=True),
                F("estrategia", "Plan de involucramiento: estrategias generales (PMBOK 6, 13.2.3.1)", tipo="largo")]
    TABLAS = [{"id": "registro", "titulo": "Registro: identificación, evaluación y clasificación", "filas": 6, "columnas": [
                  {"campo": "nombre", "etiqueta": "Nombre", "ancho": 150}, {"campo": "puesto", "etiqueta": "Puesto", "ancho": 130},
                  {"campo": "contacto", "etiqueta": "Ubicación y contacto", "ancho": 150}, {"campo": "rol", "etiqueta": "Rol en el proyecto", "ancho": 130},
                  {"campo": "requisitos", "etiqueta": "Requisitos principales", "ancho": 180}, {"campo": "expectativas", "etiqueta": "Expectativas", "ancho": 180},
                  {"campo": "fase", "etiqueta": "Fase de mayor influencia", "tipo": "opcion", "opciones": SI("Definir", "Medir", "Analizar", "Mejorar", "Controlar"), "ancho": 110},
                  {"campo": "tipo", "etiqueta": "Interno o externo", "tipo": "opcion", "opciones": SI("Interno", "Externo"), "ancho": 100},
                  {"campo": "direccion", "etiqueta": "Dirección de influencia", "tipo": "opcion", "opciones": DIRECCION, "ancho": 120}]},
              {"id": "analisis", "titulo": "Análisis, prominencia y compromiso (una fila por interesado, en el mismo orden)", "filas": 6, "columnas": [
                  {"campo": "nombre", "etiqueta": "Nombre", "calc": True, "ancho": 150},
                  {"campo": "poder", "etiqueta": "Poder", "tipo": "opcion", "opciones": ALTO_BAJO, "ancho": 80},
                  {"campo": "interes", "etiqueta": "Interés", "tipo": "opcion", "opciones": ALTO_BAJO, "ancho": 80},
                  {"campo": "cuadrante", "etiqueta": "Estrategia por cuadrante", "calc": True, "ancho": 150},
                  {"campo": "urgencia", "etiqueta": "¿Urgencia?", "tipo": "opcion", "opciones": SI("Sí", "No"), "ancho": 84},
                  {"campo": "legitimidad", "etiqueta": "¿Legitimidad?", "tipo": "opcion", "opciones": SI("Sí", "No"), "ancho": 90},
                  {"campo": "prominencia", "etiqueta": "Prominencia", "calc": True, "ancho": 150},
                  {"campo": "actual", "etiqueta": "Compromiso actual (C)", "tipo": "opcion", "opciones": NIV, "ancho": 130},
                  {"campo": "deseado", "etiqueta": "Compromiso deseado (D)", "tipo": "opcion", "opciones": NIV, "ancho": 130},
                  {"campo": "brecha", "etiqueta": "Brecha", "calc": True, "ancho": 70},
                  {"campo": "comunicacion", "etiqueta": "Comunicación", "tipo": "opcion", "opciones": SI("De envío (push)", "De consulta (pull)", "Interactiva"), "ancho": 130},
                  {"campo": "accion", "etiqueta": "Acción para cerrar la brecha", "ancho": 200}, {"campo": "responsable", "etiqueta": "Responsable", "ancho": 120},
                  {"campo": "revision", "etiqueta": "Última revisión", "ancho": 100}]}]
    NOTA = ("PMBOK 6: registro de interesados 13.1.3.1 (identificación, evaluación y clasificación); mapeo 13.1.2.4 (cuadrícula poder/interés, "
            "prominencia por poder, urgencia y legitimidad, direcciones de influencia, priorización); matriz de evaluación del compromiso 13.2.2.5 "
            "(sin conocimiento, resistente, neutral, de apoyo y líder; la brecha entre actual y deseado dirige la comunicación y cerrarla es lo que se "
            "monitorea). PMBOK 7: dominio de interesados 2.1 (identificar, entender y analizar, priorizar, involucrar y monitorear; comunicación de envío, "
            "de consulta e interactiva, 2.1.1.4). No respaldados por la base: los nombres de estrategia por cuadrante y de las clases de prominencia.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        reg, an = d["tablas"]["registro"], d["tablas"]["analisis"]
        while len(an) < len(reg): an.append({})
        cc, kk, av, puntos, compromiso = [], [], [], [], []
        brechas = 0
        for i, f in enumerate(an):
            nom = (reg[i].get("nombre") if i < len(reg) else "") or ""
            c, k = {"nombre": nom}, {}
            if nom:
                c["cuadrante"] = cuadrante(f.get("poder"), f.get("interes"))
                c["prominencia"] = prominencia(f.get("poder") == "Alto" and "Sí" or "", f.get("urgencia"), f.get("legitimidad"))
                if f.get("actual") and f.get("deseado"):
                    b = NIVELES.index(f["deseado"]) - NIVELES.index(f["actual"]); c["brecha"] = f"{b:+d}" if b else "0"
                    k["brecha"] = "ok" if b <= 0 else "advertencia" if b == 1 else "no"
                    if b > 0:
                        brechas += 1
                        if not f.get("accion"): k["accion"] = "falta"
                    compromiso.append((nom, f["actual"], f["deseado"]))
                if f.get("poder") and f.get("interes"): puntos.append((nom, f["poder"], f["interes"]))
                if not (f.get("poder") and f.get("interes")): k["poder"] = k["interes"] = "falta"
                if f.get("actual") == "Resistente" and not f.get("accion"): av.append(f"«{nom}» está resistente y no tiene acción planeada.")
            elif not fila_vacia(f): av.append(f"Análisis, fila {i + 1}: no hay interesado en esa fila del registro.")
            cc.append(c); kk.append(k)
        kreg = [{} for _ in reg]
        for i, f in enumerate(reg):
            if f.get("nombre") and not f.get("rol"): kreg[i]["rol"] = "falta"
        n = sum(1 for f in reg if f.get("nombre"))
        if n and not any(f.get("poder") == "Alto" and f.get("interes") == "Alto" for f in an[:len(reg)]):
            av.append("Ningún interesado está en «poder alto e interés alto»; revisa si falta el patrocinador o el dueño del proceso.")
        cab = {"resumen": f"{n} interesados; {brechas} con brecha de compromiso por cerrar"} if n else {}
        bl = [b for b in (poder_interes_svg(puntos), matriz_compromiso_svg(compromiso)) if b]
        return {"cab": cab, "calc": {"analisis": cc}, "clases": {"analisis": kk, "registro": kreg}, "avisos": av,
                "bloques": [{"tipo": "grafica", "svg": s} for s in bl]}


# ======================= RIESGOS =======================
PROB = [("Muy alta", .90), ("Alta", .70), ("Media", .50), ("Baja", .30), ("Muy baja", .10)]        # PMBOK 6, figura 11-5
IMP = [("Muy alto", .80), ("Alto", .40), ("Moderado", .20), ("Bajo", .10), ("Muy bajo", .05)]
P_OP, I_OP = SI(*[p for p, _ in PROB]), SI(*[i for i, _ in IMP])
ESTR_AMENAZA = ["Escalar", "Evitar", "Transferir", "Mitigar", "Aceptar"]                             # 11.5.2.4
ESTR_OPORT = ["Escalar", "Explotar", "Compartir", "Mejorar", "Aceptar"]                              # 11.5.2.5


def zona(puntaje):
    """Zonas de prioridad leídas de la figura 11-5 del PMBOK 6 (ejemplo): alta desde 0.24, media de 0.08 a 0.20, baja menor que 0.08."""
    if puntaje is None: return None
    return "Alta" if puntaje >= .24 - 1e-9 else "Media" if puntaje >= .08 - 1e-9 else "Baja"


def matriz_pi_svg(riesgos):
    """Matriz probabilidad-impacto con amenazas a la izquierda y oportunidades a la derecha (figura 11-5)."""
    w, h, iz, arr, cw, ch = 772, 270, 82, 30, 66, 38
    s = ""; color = {"Alta": "#e9a07a", "Media": "#f6d6c2", "Baja": "#fbf6ef"}
    for lado, x0, imps in (("Amenazas", iz, IMP[::-1]), ("Oportunidades", iz + 5 * cw + 14, IMP)):
        s += f'<text x="{x0 + 2.5 * cw}" y="20" text-anchor="middle" font-weight="700" fill="#2b2620">{lado}</text>'
        for r, (pn, pv) in enumerate(PROB):
            for c, (inom, iv) in enumerate(imps):
                sc = pv * iv; x, y = x0 + c * cw, arr + r * ch
                s += f'<rect x="{x}" y="{y}" width="{cw - 2}" height="{ch - 2}" fill="{color[zona(sc)]}" stroke="#e2dcd0"/><text x="{x + 4}" y="{y + 12}" fill="#6f675b" font-size="8">{sc:.2f}</text>'
                ids = [rid for rid, tipo, p, i in riesgos if (tipo == "Oportunidad") == (lado == "Oportunidades") and p == pn and i == inom]
                if ids: s += f'<text x="{x + cw / 2 - 1}" y="{y + 27}" text-anchor="middle" fill="#2b2620" font-weight="700">{", ".join(ids)[:12]}</text>'
            if lado == "Amenazas": s += f'<text x="{iz - 4}" y="{arr + r * ch + 22}" text-anchor="end" fill="#6f675b">{pn} {pv:.2f}</text>'
        for c, (inom, iv) in enumerate(imps):
            s += f'<text x="{x0 + c * cw + cw / 2}" y="{arr + 5 * ch + 12}" text-anchor="middle" fill="#6f675b" font-size="8">{inom} {iv:.2f}</text>'
    return _svg(w, h, s)


@formato
class Riesgos(Formato):
    ID, TITULO = "RIESGOS", "Registro de riesgos"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"),
                F("apetito", "Apetito y umbrales de riesgo de los interesados (PMBOK 6, 11.1.3.1)", tipo="largo"),
                F("reserva_cont", "Reserva de contingencia (riesgos identificados)", tipo="numero"), F("reserva_gest", "Reserva de gestión (imprevistos)", tipo="numero"),
                F("vem_total", "Valor monetario esperado de los riesgos con costo", calc=True), F("resumen", "Informe de riesgos (resumen)", calc=True)]
    TABLAS = [{"id": "registro", "titulo": "Registro de riesgos", "filas": 6, "columnas": [
        {"campo": "id", "etiqueta": "Id", "calc": True, "ancho": 50},
        {"campo": "tipo", "etiqueta": "Tipo", "tipo": "opcion", "opciones": SI("Amenaza", "Oportunidad"), "ancho": 110},
        {"campo": "causa", "etiqueta": "Causa (como resultado de…)", "ancho": 170}, {"campo": "riesgo", "etiqueta": "Riesgo (puede ocurrir…)", "ancho": 190},
        {"campo": "efecto", "etiqueta": "Efecto (lo que llevaría a…)", "ancho": 170},
        {"campo": "categoria", "etiqueta": "Categoría (RBS)", "tipo": "opcion", "opciones": SI("Técnico", "Gestión", "Comercial", "Externo"), "ancho": 110},
        {"campo": "probabilidad", "etiqueta": "Probabilidad", "tipo": "opcion", "opciones": P_OP, "ancho": 100},
        {"campo": "impacto", "etiqueta": "Impacto", "tipo": "opcion", "opciones": I_OP, "ancho": 100},
        {"campo": "puntaje", "etiqueta": "Puntaje P×I", "calc": True, "ancho": 80}, {"campo": "prioridad", "etiqueta": "Prioridad", "calc": True, "ancho": 80},
        {"campo": "urgencia", "etiqueta": "Fecha límite para actuar", "ancho": 110}, {"campo": "dueno", "etiqueta": "Dueño", "ancho": 120},
        {"campo": "disparador", "etiqueta": "Disparador o señal", "ancho": 160},
        {"campo": "estrategia", "etiqueta": "Estrategia", "tipo": "opcion", "opciones": SI(*sorted(set(ESTR_AMENAZA + ESTR_OPORT))), "ancho": 110},
        {"campo": "acciones", "etiqueta": "Acciones de respuesta", "ancho": 200}, {"campo": "contingencia", "etiqueta": "Plan de contingencia", "ancho": 170},
        {"campo": "respaldo", "etiqueta": "Plan de respaldo (fallback)", "ancho": 160},
        {"campo": "residual", "etiqueta": "Riesgo residual", "ancho": 140}, {"campo": "secundario", "etiqueta": "Riesgo secundario", "ancho": 140},
        {"campo": "costo", "etiqueta": "Costo o beneficio si ocurre ($)", "tipo": "numero", "ancho": 120}, {"campo": "vem", "etiqueta": "VME", "calc": True, "ancho": 90},
        {"campo": "estado", "etiqueta": "Estado", "tipo": "opcion", "opciones": SI("Abierto", "En vigilancia", "Ocurrido", "Cerrado", "Escalado"), "ancho": 110}]}]
    NOTA = ("PMBOK 6: registro de riesgos 11.2.3.1 (identificador, enunciado causa-riesgo-efecto, dueño, respuestas, categoría, estado, disparadores, "
            "tiempos), actualizaciones del análisis cualitativo 11.3.3 (probabilidad, impacto, puntaje, urgencia, lista de vigilancia) y de la planeación "
            "de respuestas 11.5.3 (acciones, disparadores, contingencia, respaldo, residual, secundario); estrategias 11.5.2.4 (escalar, evitar, transferir, "
            "mitigar, aceptar) y 11.5.2.5 (escalar, explotar, compartir, mejorar, aceptar); escalas y puntaje P×I de la figura 11-5 (ejemplo: probabilidad "
            "0.90 a 0.10, impacto 0.80 a 0.05; zonas alta ≥ 0.24, media 0.08 a 0.20, baja < 0.08); categorías como RBS de la figura 11-4. PMBOK 7: dominio "
            "de incertidumbre 2.8 y reservas 2.8.5.3; valor monetario esperado (VME = probabilidad × costo, signo negativo para amenazas) en 4.4.1. Si el "
            "proyecto define otras escalas (tabla 11-1), anótalas en el apetito y umbrales.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = d["tablas"]["registro"]; cc, kk, av, ubic = [], [], [], []
        pd, idic = dict(PROB), dict(IMP)
        n_a = n_o = alta = vig = 0; vem_tot = 0.0; hay_vem = False
        for i, f in enumerate(filas):
            c, k = {}, {}
            if fila_vacia(f): cc.append(c); kk.append(k); continue
            rid = f"R{i + 1}"; c["id"] = rid
            tipo = f.get("tipo") or ""
            if not tipo: k["tipo"] = "falta"
            n_a += tipo == "Amenaza"; n_o += tipo == "Oportunidad"
            if not f.get("riesgo"): k["riesgo"] = "falta"
            p, im = f.get("probabilidad"), f.get("impacto")
            if p in pd and im in idic:
                sc = pd[p] * idic[im]; z = zona(sc); c["puntaje"] = f"{sc:.2f}"; c["prioridad"] = z
                k["prioridad"] = {"Alta": "no", "Media": "advertencia", "Baja": "ok"}[z] if tipo != "Oportunidad" else "ok"
                ubic.append((rid, tipo, p, im))
                if z == "Alta":
                    alta += 1
                    if not f.get("dueno"): k["dueno"] = "falta"; av.append(f"{rid}: prioridad alta sin dueño.")
                    if not f.get("estrategia"): k["estrategia"] = "falta"
                if z == "Baja" and f.get("estado") == "En vigilancia": vig += 1
                if f.get("costo"):
                    cost = N(f["costo"])
                    if cost is None: k["costo"] = "mal"
                    else:
                        v = pd[p] * cost * (-1 if tipo == "Amenaza" else 1); c["vem"] = f"{v:,.2f}"; vem_tot += v; hay_vem = True
            else:
                k["probabilidad"] = k.get("probabilidad") or ("falta" if not p else ""); k["impacto"] = "falta" if not im else ""
            e = f.get("estrategia")
            if e and tipo == "Amenaza" and e not in ESTR_AMENAZA: k["estrategia"] = "mal"; av.append(f"{rid}: «{e}» es una estrategia de oportunidades, no de amenazas.")
            if e and tipo == "Oportunidad" and e not in ESTR_OPORT: k["estrategia"] = "mal"; av.append(f"{rid}: «{e}» es una estrategia de amenazas, no de oportunidades.")
            if e == "Aceptar" and tipo == "Amenaza" and not f.get("contingencia") and (c.get("prioridad") in ("Alta", "Media")):
                av.append(f"{rid}: aceptación activa: define el plan de contingencia o la reserva (11.5.2.4).")
            if e in ("Mitigar", "Evitar", "Transferir", "Explotar", "Mejorar", "Compartir") and not f.get("acciones"): k["acciones"] = "falta"
            if f.get("contingencia") and not f.get("disparador"): k["disparador"] = "falta"
            if e == "Escalar" and f.get("estado") != "Escalado": av.append(f"{rid}: un riesgo escalado pasa a otro nivel de la organización; marca su estado como «Escalado».")
            cc.append(c); kk.append(k)
        cab = {}
        if n_a or n_o:
            cab["resumen"] = f"{n_a} amenazas, {n_o} oportunidades; {alta} de prioridad alta"
        if hay_vem:
            cab["vem_total"] = f"{vem_tot:,.2f}"
            rc = N(d["cabecera"].get("reserva_cont"))
            if rc is not None and vem_tot < 0 and rc < -vem_tot:
                av.append(f"La reserva de contingencia ({rc:,.2f}) es menor que el VME de las amenazas ({-vem_tot:,.2f}); revísala (análisis de reservas, PMBOK 7 4.4.1).")
        bl = [{"tipo": "grafica", "svg": matriz_pi_svg(ubic)}] if ubic else []
        return {"cab": cab, "calc": {"registro": cc}, "clases": {"registro": kk}, "avisos": av, "bloques": bl}


# ======================= BITÁCORA =======================
@formato
class Bitacora(Formato):
    ID, TITULO = "BITACORA", "Bitácora del proyecto: supuestos, incidentes y cambios"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("resumen", "Resumen", calc=True)]
    TABLAS = [{"id": "supuestos", "titulo": "Supuestos y restricciones (PMBOK 6, 4.1.3.2)", "filas": 4, "columnas": [
                  {"campo": "tipo", "etiqueta": "Tipo", "tipo": "opcion", "opciones": SI("Supuesto", "Restricción"), "ancho": 110},
                  {"campo": "nivel", "etiqueta": "Nivel", "tipo": "opcion", "opciones": SI("Estratégico", "Operativo", "De actividad"), "ancho": 110},
                  {"campo": "descripcion", "etiqueta": "Descripción", "ancho": 300}, {"campo": "responsable", "etiqueta": "Responsable de validarlo", "ancho": 140},
                  {"campo": "estado", "etiqueta": "Estado", "tipo": "opcion", "opciones": SI("Por validar", "Validado", "Falso"), "ancho": 110}]},
              {"id": "incidentes", "titulo": "Incidentes (PMBOK 6, 4.3.3.3)", "filas": 4, "columnas": [
                  {"campo": "tipo", "etiqueta": "Tipo", "ancho": 110}, {"campo": "quien", "etiqueta": "Quién lo reportó", "ancho": 120},
                  {"campo": "fecha", "etiqueta": "Fecha (DD/MM/AAAA)", "ancho": 100}, {"campo": "descripcion", "etiqueta": "Descripción", "ancho": 240},
                  {"campo": "prioridad", "etiqueta": "Prioridad", "tipo": "opcion", "opciones": SI("Alta", "Media", "Baja"), "ancho": 90},
                  {"campo": "asignado", "etiqueta": "Asignado a", "ancho": 120}, {"campo": "objetivo", "etiqueta": "Fecha objetivo", "ancho": 100},
                  {"campo": "estado", "etiqueta": "Estado", "tipo": "opcion", "opciones": SI("Abierto", "En proceso", "Cerrado"), "ancho": 100},
                  {"campo": "solucion", "etiqueta": "Solución final", "ancho": 200}, {"campo": "dias", "etiqueta": "Días abierto", "calc": True, "ancho": 80}]},
              {"id": "cambios", "titulo": "Solicitudes de cambio (PMBOK 6, 4.3.3.4 y 4.6.3.3)", "filas": 4, "columnas": [
                  {"campo": "id", "etiqueta": "Id", "calc": True, "ancho": 50}, {"campo": "fecha", "etiqueta": "Fecha", "ancho": 100},
                  {"campo": "solicitante", "etiqueta": "Solicitante", "ancho": 120}, {"campo": "descripcion", "etiqueta": "Cambio propuesto", "ancho": 240},
                  {"campo": "afecta", "etiqueta": "Afecta a", "tipo": "opcion", "opciones": SI("Alcance", "Cronograma", "Costo", "Calidad", "Procedimiento", "Documento"), "ancho": 110},
                  {"campo": "impacto", "etiqueta": "Impacto evaluado", "ancho": 180},
                  {"campo": "decision", "etiqueta": "Decisión", "tipo": "opcion", "opciones": SI("Pendiente", "Aprobado", "Rechazado", "Diferido"), "ancho": 100},
                  {"campo": "decidio", "etiqueta": "Decidió (comité de cambios)", "ancho": 140}, {"campo": "fecha_decision", "etiqueta": "Fecha de decisión", "ancho": 100}]}]
    NOTA = ("PMBOK 6: bitácora de supuestos y restricciones 4.1.3.2 (estratégicos y operativos desde el caso de negocio y el acta; de actividad durante "
            "el proyecto); bitácora de incidentes 4.3.3.3 (tipo, quién y cuándo, descripción, prioridad, asignado, fecha objetivo, estado, solución "
            "final); solicitudes de cambio 4.3.3.4 y bitácora de cambios 4.6.3.3. PMBOK 7: 4.6.2 (registros) y comité de control de cambios 4.4.3.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        from datetime import date
        from ..nucleo.hoja import a_fecha
        av, calc, clases = [], {"incidentes": [], "cambios": []}, {"supuestos": [], "incidentes": [], "cambios": []}
        hoy = date.today()
        for f in d["tablas"]["supuestos"]:
            k = {}
            if f.get("descripcion") and not f.get("tipo"): k["tipo"] = "falta"
            if f.get("estado") == "Falso": k["estado"] = "no"
            clases["supuestos"].append(k)
        falsos = sum(1 for f in d["tablas"]["supuestos"] if f.get("estado") == "Falso")
        if falsos: av.append(f"{falsos} supuestos resultaron falsos: revisa si generan un riesgo o una solicitud de cambio.")
        abiertos = vencidos = 0
        for i, f in enumerate(d["tablas"]["incidentes"]):
            c, k = {}, {}
            if f.get("descripcion"):
                if not f.get("asignado"): k["asignado"] = "falta"
                fe, ob = a_fecha((f.get("fecha") or "").strip()), a_fecha((f.get("objetivo") or "").strip())
                if f.get("fecha") and fe is None: k["fecha"] = "mal"
                if f.get("objetivo") and ob is None: k["objetivo"] = "mal"
                if f.get("estado") != "Cerrado":
                    abiertos += 1
                    if fe: c["dias"] = str((hoy - fe).days)
                    if ob and ob < hoy: vencidos += 1; k["objetivo"] = "no"
                elif not f.get("solucion"): k["solucion"] = "falta"
            calc["incidentes"].append(c); clases["incidentes"].append(k)
        if vencidos: av.append(f"{vencidos} incidentes abiertos pasaron su fecha objetivo.")
        pend = 0
        for i, f in enumerate(d["tablas"]["cambios"]):
            c, k = {}, {}
            if f.get("descripcion"):
                c["id"] = f"CC{i + 1}"
                if not f.get("impacto"): k["impacto"] = "falta"
                if f.get("decision") in ("Aprobado", "Rechazado", "Diferido") and not f.get("decidio"): k["decidio"] = "falta"
                if f.get("decision") in ("", "Pendiente", None): pend += 1
            calc["cambios"].append(c); clases["cambios"].append(k)
        ns = sum(1 for f in d["tablas"]["supuestos"] if f.get("descripcion"))
        cab = {"resumen": f"{ns} supuestos o restricciones · {abiertos} incidentes abiertos · {pend} cambios pendientes"} if ns or abiertos or pend else {}
        return {"cab": cab, "calc": calc, "clases": clases, "avisos": av}


# ======================= RACI =======================
RACI_OP = SI("R", "A", "C", "I", "R/A")


@formato
class Raci(Formato):
    ID, TITULO = "RACI", "Matriz de responsabilidades (RACI)"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto")] + [F(f"p{k}", f"Persona o grupo {k}") for k in range(1, 7)]
    TABLAS = [{"id": "actividades", "titulo": "Actividades o entregables (R responsable · A rinde cuentas · C consultado · I informado)", "filas": 8, "columnas": [
        {"campo": "actividad", "etiqueta": "Actividad o entregable", "ancho": 260}] + [{"campo": f"p{k}", "etiqueta": f"P{k}", "tipo": "opcion", "opciones": RACI_OP, "ancho": 70} for k in range(1, 7)]
        + [{"campo": "revision", "etiqueta": "Revisión", "calc": True, "ancho": 220}]}]
    NOTA = ("PMBOK 6, 9.1.2.2: la matriz de asignación de responsabilidades muestra a todas las personas de cada actividad y asegura que solo una "
            "persona rinda cuentas (A) por actividad; la RACI es un ejemplo (figura 9-4). PMBOK 7, 4.6.6. «R/A» marca a quien hace el trabajo y "
            "además rinde cuentas. Los encabezados P1 a P6 toman los nombres de la cabecera.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        nombres = {k: d["cabecera"].get(f"p{k}") or f"P{k}" for k in range(1, 7)}
        cc, kk, av = [], [], []
        carga = {k: 0 for k in range(1, 7)}
        for i, f in enumerate(d["tablas"]["actividades"]):
            c, k = {}, {}
            if f.get("actividad"):
                cods = {j: f.get(f"p{j}") for j in range(1, 7) if f.get(f"p{j}")}
                a = [j for j, v in cods.items() if "A" in v]; r = [j for j, v in cods.items() if "R" in v]
                for j in cods: carga[j] += 1
                prob = []
                if len(a) == 0: prob.append("falta A")
                if len(a) > 1: prob.append(f"{len(a)} con A")
                if not r: prob.append("falta R")
                c["revision"] = "; ".join(prob) or "correcta"; k["revision"] = "no" if prob else "ok"
                for j in a:
                    if len(a) > 1: k[f"p{j}"] = "mal"
                if prob: av.append(f"«{f['actividad']}»: " + ", ".join(prob) + " (debe haber una sola persona que rinda cuentas).")
                for j in cods:
                    if not d["cabecera"].get(f"p{j}"): k[f"p{j}"] = "advertencia"
            cc.append(c); kk.append(k)
        usados = [j for j in range(1, 7) if d["cabecera"].get(f"p{j}")]
        sin = [nombres[j] for j in usados if carga[j] == 0]
        if sin and any(f.get("actividad") for f in d["tablas"]["actividades"]): av.append("Sin asignaciones: " + ", ".join(sin) + ".")
        return {"cab": {}, "calc": {"actividades": cc}, "clases": {"actividades": kk}, "avisos": av, "encabezados": {f"p{k}": nombres[k] for k in range(1, 7)}}


# ======================= CIERRE Y LECCIONES =======================
@formato
class Lecciones(Formato):
    ID, TITULO = "LECCIONES", "Cierre del proyecto y lecciones aprendidas"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("descripcion", "Descripción resumida del proyecto o fase (informe final)", tipo="largo"),
                F("transicion", "Transición: a quién se entrega el proceso o resultado y cómo (4.7.3.2)", tipo="largo"),
                F("aceptacion", "Aceptación final: quién la firmó y cuándo"), F("beneficios_futuros", "Beneficios no alcanzados al cierre: estimación y fecha", tipo="largo"),
                F("riesgos_incidentes", "Riesgos e incidentes relevantes y cómo se atendieron", tipo="largo"),
                F("archivo", "Dónde quedan archivados los documentos del proyecto"), F("cumplimiento", "Cumplimiento de objetivos", calc=True)]
    TABLAS = [{"id": "objetivos", "titulo": "Informe final: objetivos contra resultados (PMBOK 6, 4.7.3.3)", "filas": 4, "fijas": True, "columnas": [
                  {"campo": "dimension", "etiqueta": "Dimensión", "ancho": 110, "lectura": True}, {"campo": "objetivo", "etiqueta": "Objetivo", "ancho": 180},
                  {"campo": "criterio", "etiqueta": "Criterio de evaluación", "ancho": 180}, {"campo": "meta", "etiqueta": "Meta (número)", "tipo": "numero", "ancho": 90},
                  {"campo": "real", "etiqueta": "Real (número)", "tipo": "numero", "ancho": 90},
                  {"campo": "sentido", "etiqueta": "Mejor si", "tipo": "opcion", "opciones": [["", ""], ["<=", "≤ menor"], [">=", "≥ mayor"]], "ancho": 84},
                  {"campo": "cumple", "etiqueta": "¿Cumple?", "calc": True, "ancho": 80}, {"campo": "evidencia", "etiqueta": "Evidencia", "ancho": 180},
                  {"campo": "variacion", "etiqueta": "Razón de la variación", "ancho": 200}]},
              {"id": "lecciones", "titulo": "Registro de lecciones aprendidas (PMBOK 6, 4.4.3.1)", "filas": 5, "columnas": [
                  {"campo": "fase", "etiqueta": "Fase", "tipo": "opcion", "opciones": SI("Definir", "Medir", "Analizar", "Mejorar", "Controlar", "Cierre"), "ancho": 100},
                  {"campo": "categoria", "etiqueta": "Categoría", "tipo": "opcion", "opciones": SI("Desafío", "Problema", "Riesgo ocurrido", "Oportunidad aprovechada", "Buena práctica"), "ancho": 140},
                  {"campo": "situacion", "etiqueta": "Situación", "ancho": 220}, {"campo": "impacto", "etiqueta": "Impacto", "ancho": 160},
                  {"campo": "recomendacion", "etiqueta": "Recomendación", "ancho": 200}, {"campo": "accion", "etiqueta": "Acción propuesta", "ancho": 180},
                  {"campo": "tipo_con", "etiqueta": "Conocimiento", "tipo": "opcion", "opciones": SI("Explícito (documentable)", "Tácito (de persona a persona)"), "ancho": 160},
                  {"campo": "registro", "etiqueta": "Quién lo registró", "ancho": 120}]}]
    NOTA = ("PMBOK 6: informe final 4.7.3.3 (descripción, objetivos de alcance, calidad, costo y cronograma con criterios, evidencia y razones de "
            "variación; beneficios y necesidades de negocio alcanzados o su estimación futura; riesgos e incidentes), transición 4.7.3.2 y registro de "
            "lecciones aprendidas 4.4.3.1 (categoría, situación, impacto, recomendaciones y acciones; se crea al inicio y al cierre pasa al "
            "repositorio de la organización). PMBOK 7: aprendizaje 2.5.8 (conocimiento explícito y tácito), fase de cierre 2.3.5, reunión de lecciones "
            "y retrospectiva 4.4.3, y el patrocinador vigila los beneficios después del cierre (X2.2).")

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["objetivos"] = [{"dimension": x} for x in ("Alcance", "Calidad", "Costo", "Cronograma")]; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        cc, kk, av = [], [], []; cumplen = evaluados = 0
        for f in d["tablas"]["objetivos"]:
            c, k = {}, {}; m, r = N(f.get("meta")), N(f.get("real"))
            for x in ("meta", "real"):
                if f.get(x) and N(f[x]) is None: k[x] = "mal"
            if m is not None and r is not None and f.get("sentido"):
                ok = r <= m if f["sentido"] == "<=" else r >= m; evaluados += 1; cumplen += ok
                c["cumple"] = "Sí" if ok else "No"; k["cumple"] = "ok" if ok else "no"
                if not ok and not f.get("variacion"): k["variacion"] = "falta"
                if not f.get("evidencia"): k["evidencia"] = "falta"
            elif m is not None and r is not None: k["sentido"] = "falta"
            cc.append(c); kk.append(k)
        kl = []
        for f in d["tablas"]["lecciones"]:
            k = {}
            if f.get("situacion") and not f.get("recomendacion"): k["recomendacion"] = "falta"
            kl.append(k)
        nl = sum(1 for f in d["tablas"]["lecciones"] if f.get("situacion"))
        cab = {"cumplimiento": f"{cumplen} de {evaluados} objetivos cumplidos · {nl} lecciones registradas"} if evaluados or nl else {}
        if evaluados and not d["cabecera"].get("transicion"): av.append("Falta la transición: a quién se entrega el proceso mejorado (en DMAIC, al dueño del proceso en Controlar).")
        if evaluados and not d["cabecera"].get("aceptacion"): av.append("Falta registrar la aceptación final (reunión de cierre, PMBOK 7 4.4.3).")
        if evaluados and cumplen < evaluados and not d["cabecera"].get("beneficios_futuros"): av.append("Hay objetivos no cumplidos: indica el grado alcanzado y la estimación de beneficios futuros (4.7.3.3).")
        if evaluados and nl == 0: av.append("No hay lecciones registradas; el registro se alimenta desde el inicio, no solo al cierre (4.4.3.1).")
        return {"cab": cab, "calc": {"objetivos": cc}, "clases": {"objetivos": kk, "lecciones": kl}, "avisos": av}


# ======================= VALOR GANADO =======================
def evm(bac, pv, ev, ac):
    """PMBOK 7, 2.7.2.3 y 2.7.2.7 (figuras 2-24 y 2-26); PMBOK 6, 7.4.2.2 y tabla 7-1."""
    r = {"SV": ev - pv, "CV": ev - ac, "SPI": ev / pv if pv else None, "CPI": ev / ac if ac else None}
    if r["CPI"]:
        r["EAC"] = bac / r["CPI"]; r["ETC"] = (bac - ev) / r["CPI"]; r["VAC"] = bac - r["EAC"]
    r["TCPI"] = (bac - ev) / (bac - ac) if bac != ac else None
    return r


def curva_s_svg(periodos, pv, ev, ac, bac):
    if not periodos: return None
    w, h, iz, ab = 720, 240, 60, 30; mx = max([x for x in pv + ev + ac + [bac or 0] if x is not None] + [1e-9]) * 1.08; n = len(periodos)
    X = lambda i: iz + (w - iz - 10) * (i / max(n - 1, 1)); Y = lambda v: h - ab - (h - ab - 10) * v / mx
    s = ""
    for k in range(5):
        y = h - ab - (h - ab - 10) * k / 4; s += f'<line x1="{iz}" x2="{w - 6}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e9e4da"/><text x="{iz - 4}" y="{y + 3:.1f}" text-anchor="end" fill="#6f675b">{num(mx * k / 4, 3)}</text>'
    for i, p in enumerate(periodos): s += f'<text x="{X(i):.1f}" y="{h - ab + 14}" text-anchor="middle" fill="#6f675b">{_t(p)[:8]}</text>'
    for nom, ser, col, das in (("PV", pv, "#6f675b", "6 4"), ("EV", ev, "#dd5813", ""), ("AC", ac, "#2b6f8f", "")):
        pts = [(X(i), Y(v)) for i, v in enumerate(ser) if v is not None]
        if pts:
            s += f'<polyline fill="none" stroke="{col}" stroke-width="2" stroke-dasharray="{das}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>'
            s += f'<text x="{pts[-1][0] + 4:.1f}" y="{pts[-1][1] - 4:.1f}" fill="{col}" font-weight="700">{nom}</text>'
    if bac: s += f'<line x1="{iz}" x2="{w - 6}" y1="{Y(bac):.1f}" y2="{Y(bac):.1f}" stroke="#b3261e" stroke-dasharray="3 3"/><text x="{w - 8}" y="{Y(bac) - 4:.1f}" text-anchor="end" fill="#b3261e">BAC</text>'
    return _svg(w, h, s)


@formato
class ValorGanado(Formato):
    ID, TITULO = "VALOR-GANADO", "Seguimiento por valor ganado"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("bac", "Presupuesto total (BAC)", tipo="numero"),
                F("umbral_sup", "Umbral: desviación de costo tolerada en exceso (%)", tipo="numero", defecto="10"),
                F("umbral_inf", "Umbral: desviación tolerada por debajo (%)", tipo="numero", defecto="20"),
                F("plan_excepcion", "Plan de excepción si se cruza un umbral (PMBOK 7, 2.7.5)", tipo="largo"),
                F("estado", "Estado al último corte", calc=True), F("pronostico", "Pronóstico", calc=True)]
    TABLAS = [{"id": "cortes", "titulo": "Cortes de seguimiento (acumulados)", "filas": 6, "columnas": [
        {"campo": "periodo", "etiqueta": "Corte (semana o fecha)", "ancho": 120}, {"campo": "pv", "etiqueta": "Valor planeado PV", "tipo": "numero", "ancho": 110},
        {"campo": "ev", "etiqueta": "Valor ganado EV", "tipo": "numero", "ancho": 110}, {"campo": "ac", "etiqueta": "Costo real AC", "tipo": "numero", "ancho": 110},
        {"campo": "sv", "etiqueta": "SV = EV − PV", "calc": True, "ancho": 100}, {"campo": "cv", "etiqueta": "CV = EV − AC", "calc": True, "ancho": 100},
        {"campo": "spi", "etiqueta": "SPI = EV/PV", "calc": True, "ancho": 90}, {"campo": "cpi", "etiqueta": "CPI = EV/AC", "calc": True, "ancho": 90},
        {"campo": "gasto", "etiqueta": "AC contra PV", "calc": True, "ancho": 90}, {"campo": "explicacion", "etiqueta": "Explicación si sale del umbral", "ancho": 200}]}]
    NOTA = ("PMBOK 7, 2.7.2.3 y 2.7.2.7, figuras 2-24 y 2-26: SV = EV − PV; CV = EV − AC; SPI = EV/PV; CPI = EV/AC; ETC = (BAC − EV)/CPI; "
            "EAC = BAC/CPI (supone que el desempeño pasado continúa); VAC = BAC − EAC; TCPI = (BAC − EV)/(BAC − AC). PMBOK 6, 7.4.2.2 y tabla 7-1. "
            "Umbrales y plan de excepción: PMBOK 7, 2.7.5 (ejemplo de la figura 2-31: +10% y −20% del gasto previsto). Curva S: PMBOK 7, 4.6.6. "
            "Los valores son acumulados al corte.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        bac = N(d["cabecera"].get("bac")); us = N(d["cabecera"].get("umbral_sup")); ui = N(d["cabecera"].get("umbral_inf"))
        us = 10 if us is None else us; ui = 20 if ui is None else ui
        cc, kk, av, per, PV, EV, AC, ult = [], [], [], [], [], [], [], None
        for f in d["tablas"]["cortes"]:
            c, k = {}, {}; pv, ev, ac = N(f.get("pv")), N(f.get("ev")), N(f.get("ac"))
            for x in ("pv", "ev", "ac"):
                if f.get(x) and (N(f[x]) is None or N(f[x]) < 0): k[x] = "mal"
            if None not in (pv, ev, ac):
                r = evm(bac or 0, pv, ev, ac); ult = (f.get("periodo") or f"Corte {len(per) + 1}", pv, ev, ac, r)
                c.update(sv=f"{r['SV']:,.2f}", cv=f"{r['CV']:,.2f}", spi=num(r["SPI"], 3) if r["SPI"] else "—", cpi=num(r["CPI"], 3) if r["CPI"] else "—")
                k["spi"] = "ok" if r["SPI"] and r["SPI"] >= 1 else "no"; k["cpi"] = "ok" if r["CPI"] and r["CPI"] >= 1 else "no"
                if pv:
                    g = (ac - pv) / pv; c["gasto"] = f"{100 * g:+.0f}% sobre lo planeado (PV)"
                    fuera = g > us / 100 or g < -ui / 100; k["gasto"] = "no" if fuera else "ok"
                    if fuera and not f.get("explicacion"): k["explicacion"] = "falta"
                per.append(f.get("periodo") or str(len(per) + 1)); PV.append(pv); EV.append(ev); AC.append(ac)
                if bac and (pv > bac or ev > bac): av.append(f"{f.get('periodo') or 'Un corte'}: PV o EV supera el BAC (los valores deben ser acumulados dentro del presupuesto).")
            cc.append(c); kk.append(k)
        cab = {}
        if ult:
            nom, pv, ev, ac, r = ult
            cab["estado"] = (f"{nom}: {'adelantado' if r['SV'] >= 0 else 'atrasado'} (SPI {num(r['SPI'], 3) if r['SPI'] else '—'}) y "
                             f"{'bajo' if r['CV'] >= 0 else 'sobre'} presupuesto (CPI {num(r['CPI'], 3) if r['CPI'] else '—'})")
            if bac and r.get("EAC") is not None:
                cab["pronostico"] = (f"EAC {r['EAC']:,.2f} · ETC {r['ETC']:,.2f} · VAC {r['VAC']:,.2f}" + (f" · TCPI {num(r['TCPI'], 3)}" if r["TCPI"] is not None else ""))
                if r["TCPI"] is not None and r["TCPI"] > 1.1: av.append(f"Para terminar dentro del BAC se necesita un CPI de {num(r['TCPI'], 3)} en lo que falta: revisa el plan o el presupuesto.")
            elif not bac: av.append("Captura el presupuesto total (BAC) para pronosticar EAC, ETC, VAC y TCPI.")
        if any(k.get("explicacion") == "falta" for k in kk) and not d["cabecera"].get("plan_excepcion"):
            av.append("Hay cortes fuera del umbral: explica la causa y define el plan de excepción (PMBOK 7, 2.7.5).")
        bl = [{"tipo": "grafica", "svg": curva_s_svg(per, PV, EV, AC, bac)}] if per else []
        return {"cab": cab, "calc": {"cortes": cc}, "clases": {"cortes": kk}, "avisos": av, "bloques": bl}


# ======================= COSTO DE CALIDAD =======================
CATEG = [("Prevención", "Requisitos y especificaciones, planeación de calidad, aseguramiento de calidad, capacitación"),
         ("Evaluación", "Verificación e inspección, auditorías de calidad, calificación de proveedores"),
         ("Falla interna", "Desperdicio, desecho, retrabajo, análisis de fallas"),
         ("Falla externa", "Reparaciones y servicio, garantías, quejas, devoluciones, reputación")]


@formato
class CostoCalidad(Formato):
    ID, TITULO = "COSTO-CALIDAD", "Costo de calidad"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("periodo", "Periodo"), F("ventas", "Ventas del periodo (opcional, para el % de ventas)", tipo="numero"),
                F("total", "Costo de calidad total", calc=True), F("conformidad", "Conformidad (prevención + evaluación)", calc=True),
                F("no_conformidad", "No conformidad (fallas internas + externas)", calc=True)]
    TABLAS = [{"id": "partidas", "titulo": "Partidas de costo", "filas": 8, "columnas": [
        {"campo": "categoria", "etiqueta": "Categoría", "tipo": "opcion", "opciones": SI(*[c for c, _ in CATEG]), "ancho": 120},
        {"campo": "concepto", "etiqueta": "Concepto", "ancho": 260}, {"campo": "antes", "etiqueta": "Costo antes del proyecto", "tipo": "numero", "ancho": 130},
        {"campo": "despues", "etiqueta": "Costo después", "tipo": "numero", "ancho": 110}, {"campo": "cambio", "etiqueta": "Cambio", "calc": True, "ancho": 100}]}]
    NOTA = ("PMBOK 7, 2.6.3.1 y 4.4.1: el costo de calidad equilibra la inversión en prevención y evaluación contra los costos de falla interna y "
            "externa. Ejemplos de cada categoría: " + "; ".join(f"{c}: {e}" for c, e in CATEG) + ". PMBOK 7, 2.6.3.2: mientras más tarde se encuentra un "
            "defecto, más cuesta corregirlo. La separación conformidad y no conformidad es de uso común [GENERAL].")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        tot = {c: [0.0, 0.0] for c, _ in CATEG}; cc, kk, av = [], [], []
        for f in d["tablas"]["partidas"]:
            c, k = {}, {}; a, b = N(f.get("antes")), N(f.get("despues"))
            for x in ("antes", "despues"):
                if f.get(x) and (N(f[x]) is None or N(f[x]) < 0): k[x] = "mal"
            if (a is not None or b is not None) and not f.get("categoria"): k["categoria"] = "falta"
            if f.get("categoria") in tot:
                if a is not None: tot[f["categoria"]][0] += a
                if b is not None: tot[f["categoria"]][1] += b
            if a is not None and b is not None: c["cambio"] = f"{b - a:+,.2f}"; k["cambio"] = "ok" if b <= a else "advertencia"
            cc.append(c); kk.append(k)
        cab = {}
        T = [sum(v[i] for v in tot.values()) for i in (0, 1)]
        if any(T):
            ven = N(d["cabecera"].get("ventas"))
            fmt = lambda i: f"{T[i]:,.2f}" + (f" ({pct(T[i] / ven)} de ventas)" if ven else "")
            cab["total"] = f"Antes {fmt(0)} · después {fmt(1)}"
            conf = [tot["Prevención"][i] + tot["Evaluación"][i] for i in (0, 1)]; nc = [tot["Falla interna"][i] + tot["Falla externa"][i] for i in (0, 1)]
            cab["conformidad"] = f"{conf[0]:,.2f} → {conf[1]:,.2f}"; cab["no_conformidad"] = f"{nc[0]:,.2f} → {nc[1]:,.2f}"
            if T[0] and nc[0] > conf[0] * 2: av.append("Las fallas superan por mucho a la prevención y evaluación: invertir en prevención suele bajar el costo total (2.6.3.1).")
            if tot["Falla externa"][1] > tot["Falla externa"][0] and T[1]: av.append("La falla externa aumentó: es la más cara porque llega al cliente (2.6.3.2).")
        bl = [{"tipo": "grafica", "svg": barras_svg([f"{c[:9]} A" if i == 0 else f"{c[:9]} D" for c, _ in CATEG for i in (0, 1)],
                                                    [tot[c][i] for c, _ in CATEG for i in (0, 1)], colores={j: "#2b6f8f" for j in range(1, 8, 2)})}] if any(T) else []
        return {"cab": cab, "calc": {"partidas": cc}, "clases": {"partidas": kk}, "avisos": av, "bloques": bl}


# ======================= JUSTIFICACIÓN DE NEGOCIO =======================
def vpn(tasa, flujos): return sum(f / (1 + tasa) ** t for t, f in enumerate(flujos))


def tir(flujos):
    """Tasa que hace VPN = 0 (bisección entre -99% y 1000%). None si no cambia de signo."""
    lo, hi = -.99, 10.0
    flo, fhi = vpn(lo, flujos), vpn(hi, flujos)
    if flo * fhi > 0: return None
    for _ in range(200):
        m = (lo + hi) / 2; fm = vpn(m, flujos)
        if flo * fm <= 0: hi, fhi = m, fm
        else: lo, flo = m, fm
    return (lo + hi) / 2


def recuperacion(flujos):
    """Periodo de recuperación con interpolación dentro del periodo en que el acumulado cruza cero."""
    acum = flujos[0]
    if acum >= 0: return 0.0
    for t in range(1, len(flujos)):
        nuevo = acum + flujos[t]
        if nuevo >= 0: return t - 1 + (-acum / flujos[t]) if flujos[t] else float(t)
        acum = nuevo
    return None


@formato
class Justificacion(Formato):
    ID, TITULO = "JUSTIFICACION", "Justificación de negocio (VPN, TIR, recuperación, ROI)"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("inversion", "Inversión inicial (periodo 0)", tipo="numero"),
                F("tasa", "Tasa de descuento por periodo (%)", tipo="numero", defecto="10"),
                F("unidad", "Periodo", tipo="opcion", opciones=[["año", "Años"], ["mes", "Meses"]], defecto="año"),
                F("vpn", "Valor presente neto (VPN)", calc=True), F("tir", "Tasa interna de retorno (TIR)", calc=True),
                F("recuperacion", "Periodo de recuperación", calc=True), F("roi", "ROI (PMBOK)", calc=True), F("bc", "Relación beneficio/costo", calc=True)]
    TABLAS = [{"id": "flujos", "titulo": "Beneficios y costos por periodo (sin la inversión inicial)", "filas": 5, "columnas": [
        {"campo": "periodo", "etiqueta": "Periodo", "calc": True, "ancho": 70}, {"campo": "beneficio", "etiqueta": "Beneficio", "tipo": "numero", "ancho": 120},
        {"campo": "costo", "etiqueta": "Costo de operación", "tipo": "numero", "ancho": 120}, {"campo": "neto", "etiqueta": "Neto", "calc": True, "ancho": 110},
        {"campo": "acumulado", "etiqueta": "Acumulado (con inversión)", "calc": True, "ancho": 140}]}]
    NOTA = ("PMBOK 7, 4.4.1, métodos de justificación de negocio: periodo de recuperación; TIR (rendimiento anual proyectado de la inversión); "
            "ROI = promedio de los beneficios netos entre el costo inicial; VPN (beneficios futuros al valor del momento de la inversión); análisis "
            "costo-beneficio. Relación B/C = valor presente de beneficios / (inversión + valor presente de costos) [forma de uso común]. Ojo: el ROI de "
            "la base Black Belt (PL18, árbol DuPont) es otro indicador: utilidad sobre ventas por rotación del capital; no son comparables. "
            "PMBOK 7, 4.6.1: el caso de negocio es la propuesta de valor con beneficios financieros y no financieros.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c0 = N(d["cabecera"].get("inversion")); tasa_v = N(d["cabecera"].get("tasa")); tasa = (tasa_v or 0) / 100; u = d["cabecera"].get("unidad") or "año"
        cc, kk, av, netos, ben, cos = [], [], [], [], [], []
        pend = 0                                                     # A1: un vacío no es cero; con pendientes no se calculan VPN ni TIR
        acum = -(c0 or 0)
        for i, f in enumerate(d["tablas"]["flujos"]):
            c, k = {"periodo": str(i + 1)}, {}; b, co = N(f.get("beneficio")), N(f.get("costo"))
            for x in ("beneficio", "costo"):
                if f.get(x) and N(f[x]) is None: k[x] = "mal"
            if (b is None) != (co is None):
                k["beneficio" if b is None else "costo"] = "pendiente"; pend += 1; cc.append(c); kk.append(k); continue
            if b is not None or co is not None:
                n = (b or 0) - (co or 0); netos.append(n); ben.append(b or 0); cos.append(co or 0); acum += n
                c["neto"] = f"{n:,.2f}"; c["acumulado"] = f"{acum:,.2f}"; k["acumulado"] = "ok" if acum >= 0 else ""
            cc.append(c); kk.append(k)
        cab = {}
        if pend: av.append(f"{pend} periodos con beneficio o costo vacío quedan como «pendiente»: VPN, TIR y recuperación no se calculan hasta llenarlos (teclea 0 si no hay).")
        if tasa_v is None and netos: av.append("La tasa de descuento está vacía: queda «pendiente» y no se calcula el VPN.")
        if c0 and netos and not pend and tasa_v is not None:
            fl = [-c0] + netos
            cab["vpn"] = f"{vpn(tasa, fl):,.2f} a {100 * tasa:g}% por {u}"
            t = tir(fl); cab["tir"] = f"{100 * t:.2f}% por {u}" if t is not None else "no se puede calcular (los flujos no cambian de signo)"
            r = recuperacion(fl); cab["recuperacion"] = f"{r:.2f} {u}s" if r is not None else "no se recupera en el horizonte capturado"
            cab["roi"] = pct(sum(netos) / len(netos) / c0); cab["bc"] = num(vpn(tasa, [0] + ben) / (c0 + vpn(tasa, [0] + cos)), 3)
            if vpn(tasa, fl) < 0: av.append("El VPN es negativo: a esa tasa el proyecto no recupera el valor del dinero invertido.")
            if r is None: av.append("La inversión no se recupera en los periodos capturados.")
        elif netos and not c0: av.append("Captura la inversión inicial para calcular los indicadores.")
        return {"cab": cab, "calc": {"flujos": cc}, "clases": {"flujos": kk}, "avisos": av}
