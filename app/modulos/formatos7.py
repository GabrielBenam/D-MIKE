"""Formatos de gestión v0.17 (PMBOK 6 y 7): EDT (estructura de desglose del trabajo), CRONOGRAMA (red, ruta crítica, tres puntos y
línea base), MONTECARLO (riesgo cuantitativo del cronograma), ARBOL-DECISION (valor monetario esperado), FODA, AFINIDAD y ENFOQUE
(enfoque de desarrollo). Verificados contra las figuras 6-16 (ruta crítica) y 11-15 (árbol de decisión) del PMBOK 6."""
import math, re
from datetime import timedelta
import numpy as np
from .formatos import Formato, formato, fila_vacia
from .formatos4 import SI, F, N, _svg, _t
from .base import num
from ..nucleo.hoja import a_fecha


def pct(x, d=0): return "no definido (denominador 0)" if x is None or x != x else f"{100 * x:.{d}f}%"


# ======================= EDT =======================
# Plantilla DMAIC: actividades y duraciones del curso (13_GB DEF-GANTT-DMAIC); en la EDT, las fases son el segundo nivel (PMBOK 6, figura 5-13)
PLANTILLA_DMAIC = [
    ("Definir", [("Definir el proyecto y crear el acta", 7), ("Definir el proceso y las métricas del problema", 3), ("Formar el equipo", 2), ("Aprobación del proyecto", 1)]),
    ("Medir", [("Describir el proceso", 2), ("Medir el desempeño del proceso", 2), ("Análisis de sistemas de medición", 2), ("Definir la línea base", 10), ("Revisar y actualizar el estatus (Medir)", 0)]),
    ("Analizar", [("Analizar el proceso", 8), ("Analizar las fuentes de variación", 10), ("Determinar variables significativas", 10), ("Revisar y actualizar el estatus (Analizar)", 0)]),
    ("Mejorar", [("Determinar nuevas condiciones de operación", 10), ("Estimar los beneficios del proceso mejorado", 5), ("Determinar y ajustar los modos de falla", 5),
                 ("Implementar y verificar los cambios", 5), ("Revisar y actualizar el estatus (Mejorar)", 0)]),
    ("Controlar", [("Implementar acciones de control", 9), ("Implementar el plan de control con el dueño del proceso", 2), ("Análisis del plan de logros mensual", 5),
                   ("Documentar lecciones aprendidas", 1), ("Cierre formal del proyecto", 0)])]


def plantilla_edt():
    filas = [{"codigo": "1", "nombre": "Proyecto DMAIC", "tipo": "Proyecto"}]
    for k, (fase, acts) in enumerate(PLANTILLA_DMAIC, 1):
        filas.append({"codigo": f"1.{k}", "nombre": fase, "tipo": "Cuenta de control"})
        filas += [{"codigo": f"1.{k}.{j}", "nombre": a, "tipo": "Paquete de trabajo"} for j, (a, t) in enumerate(acts, 1) if t > 0]
    filas.append({"codigo": "1.6", "nombre": "Gestión del proyecto", "tipo": "Cuenta de control"})
    filas += [{"codigo": "1.6.1", "nombre": "Seguimiento semanal y reportes", "tipo": "Paquete de trabajo"}, {"codigo": "1.6.2", "nombre": "Revisiones de fase", "tipo": "Paquete de trabajo"}]
    return filas


def plantilla_cronograma():
    filas, prev = [], None
    for fase, acts in PLANTILLA_DMAIC:
        for j, (a, t) in enumerate(acts, 1):
            i = f"{dict(Definir='D', Medir='M', Analizar='A', Mejorar='I', Controlar='C')[fase]}{j}"
            filas.append({"id": i, "nombre": a, "m": str(t), "pred": prev or "", "hito": "Sí" if t == 0 else ""}); prev = i
    return filas


TIPOS_EDT = SI("Proyecto", "Entregable", "Cuenta de control", "Paquete de planificación", "Paquete de trabajo")
COD = re.compile(r"^\d+(\.\d+)*$")


def padre_de(c): return c.rsplit(".", 1)[0] if "." in c else None


def clave_cod(c): return tuple(int(x) for x in c.split("."))


def arbol_svg(nodos):
    """EDT legible: el proyecto arriba, el segundo nivel en una fila de cajas y los niveles inferiores listados debajo de cada rama
    (sangría por nivel). nodos: {codigo: (nombre, tipo)}."""
    cods = sorted(nodos, key=clave_cod)
    if not cods: return None
    raices = [c for c in cods if padre_de(c) not in nodos]
    raiz = raices[0]
    ramas = [c for c in cods if padre_de(c) == raiz] or [raiz]
    desc = {r: [c for c in cods if c.startswith(r + ".")] for r in ramas}
    n = len(ramas); w = max(760, n * 165); bw = (w - 20) / n - 10
    filas_max = max([len(v) for v in desc.values()] + [0]); h = 120 + filas_max * 17 + 12
    nom = lambda c: _t(nodos[c][0])
    s = f'<rect x="{w / 2 - 140}" y="8" width="280" height="34" rx="6" fill="#dd5813"/><text x="{w / 2}" y="30" text-anchor="middle" fill="#fff" font-weight="700">{raiz} {nom(raiz)[:32]}</text>'
    if n > 1: s += f'<line x1="{w / 2}" x2="{w / 2}" y1="42" y2="56" stroke="#6f675b"/><line x1="{15 + bw / 2}" x2="{15 + (n - 1) * (bw + 10) + bw / 2}" y1="56" y2="56" stroke="#6f675b"/>'
    for k, r in enumerate(ramas):
        x = 15 + k * (bw + 10)
        s += f'<line x1="{x + bw / 2}" x2="{x + bw / 2}" y1="56" y2="66" stroke="#6f675b"/><rect x="{x}" y="66" width="{bw}" height="32" rx="6" fill="#fbe8dd" stroke="#dd5813"/>'
        s += f'<text x="{x + bw / 2}" y="86" text-anchor="middle" fill="#2b2620" font-weight="700">{r} {nom(r)[:max(int(bw / 7.2) - len(r), 4)]}</text>'
        for j2, c in enumerate(desc[r]):
            prof = c.count(".") - r.count(".") - 1; hoja = nodos[c][1] == "Paquete de trabajo" or not any(x.startswith(c + ".") for x in cods)
            maxc = max(int((bw - 8 - prof * 10) / 6.1) - len(c) - 1, 4)
            s += f'<text x="{x + 6 + prof * 10}" y="{116 + j2 * 17}" fill="{"#2b2620" if hoja else "#dd5813"}" font-weight="{400 if hoja else 600}">{c} {nom(c)[:maxc]}</text>'
    return _svg(w, h, s)


@formato
class Edt(Formato):
    ID, TITULO, REDIBUJAR = "EDT", "EDT: estructura de desglose del trabajo y diccionario", True
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"),
                F("plantilla", "Cargar plantilla en una EDT vacía", tipo="opcion", opciones=[["", "(ninguna)"], ["dmaic", "Fases DMAIC como segundo nivel (actividades del curso)"]]), F("enunciado", "Enunciado del alcance: descripción, entregables principales, supuestos y restricciones (5.3.3.1)", tipo="largo"),
                F("resumen", "Resumen", calc=True), F("costo_total", "Costo total (suma de paquetes de trabajo)", calc=True)]
    TABLAS = [{"id": "elementos", "titulo": "Elementos de la EDT y su diccionario (código 1, 1.1, 1.1.1…)", "filas": 8, "columnas": [
        {"campo": "codigo", "etiqueta": "Código", "ancho": 80}, {"campo": "nivel", "etiqueta": "Nivel", "calc": True, "ancho": 56},
        {"campo": "nombre", "etiqueta": "Nombre del elemento", "ancho": 200}, {"campo": "tipo", "etiqueta": "Tipo", "tipo": "opcion", "opciones": TIPOS_EDT, "ancho": 150},
        {"campo": "responsable", "etiqueta": "Responsable", "ancho": 120}, {"campo": "descripcion", "etiqueta": "Descripción del trabajo", "ancho": 220},
        {"campo": "supuestos", "etiqueta": "Supuestos y restricciones", "ancho": 170}, {"campo": "hitos", "etiqueta": "Hitos", "ancho": 130},
        {"campo": "actividades", "etiqueta": "Actividades asociadas (ids del cronograma)", "ancho": 150}, {"campo": "recursos", "etiqueta": "Recursos", "ancho": 140},
        {"campo": "costo", "etiqueta": "Costo estimado", "tipo": "numero", "ancho": 100}, {"campo": "costo_total", "etiqueta": "Costo acumulado", "calc": True, "ancho": 110},
        {"campo": "calidad", "etiqueta": "Requisitos de calidad", "ancho": 160}, {"campo": "aceptacion", "etiqueta": "Criterios de aceptación", "ancho": 170},
        {"campo": "revision", "etiqueta": "Revisión", "calc": True, "ancho": 200}]}]
    NOTA = ("PMBOK 6, 5.4.2.2: descomposición en elementos más manejables hasta el paquete de trabajo (nivel más bajo, donde costo y duración se "
            "pueden estimar y gestionar), con códigos de identificación; la suma del trabajo de los niveles bajos debe dar el de los altos sin "
            "faltantes ni trabajo extra (regla del 100%). 5.4.3.1: cada paquete de trabajo pertenece a una sola cuenta de control; una cuenta de "
            "control tiene dos o más paquetes de trabajo; el paquete de planificación está entre la cuenta y el paquete de trabajo, sin "
            "actividades detalladas. El diccionario incluye código, descripción, supuestos y restricciones, organización responsable, hitos, "
            "actividades, recursos, costo, requisitos de calidad y criterios de aceptación. PMBOK 7, 4.6.4. El segundo nivel puede ser por fases "
            "(Definir, Medir, Analizar, Mejorar, Controlar) o por entregables principales (figuras 5-13 y 5-14).")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        if d["cabecera"].get("plantilla") == "dmaic":
            if not any(f.get("codigo") or f.get("nombre") for f in d["tablas"]["elementos"]): d["tablas"]["elementos"] = plantilla_edt()
            d["cabecera"]["plantilla"] = ""
        filas = d["tablas"]["elementos"]; cc, kk, av = [{} for _ in filas], [{} for _ in filas], []
        idx = {}
        for i, f in enumerate(filas):
            c = (f.get("codigo") or "").strip()
            if not c: continue
            if not COD.match(c): kk[i]["codigo"] = "mal"; continue
            if c in idx: kk[i]["codigo"] = "mal"; kk[idx[c]]["codigo"] = "mal"; av.append(f"El código {c} está repetido."); continue
            idx[c] = i
        hijos = {c: [] for c in idx}
        for c in idx:
            p = padre_de(c)
            if p is not None:
                if p in hijos: hijos[p].append(c)
                else: kk[idx[c]]["codigo"] = "mal"; av.append(f"{c}: no existe su elemento padre {p}.")
        raices = [c for c in idx if padre_de(c) is None]
        if len(raices) > 1: av.append("Hay más de un elemento de nivel 1: la EDT tiene una sola raíz, el proyecto.")
        total = {}
        def suma(c):
            f = filas[idx[c]]
            if not hijos[c]: total[c] = N(f.get("costo")); return total[c]
            vals = [suma(h) for h in hijos[c]]
            total[c] = sum(v for v in vals if v is not None) if any(v is not None for v in vals) else None
            return total[c]
        for r in raices: suma(r)
        def descendientes(c):
            for h in hijos[c]:
                yield h; yield from descendientes(h)
        hay_cuentas = any((filas[i].get("tipo") == "Cuenta de control") for i in idx.values())
        n_pt = 0
        for c, i in idx.items():
            f = filas[i]; tipo = f.get("tipo") or ""; prob = []
            cc[i]["nivel"] = str(c.count(".") + 1)
            if total.get(c) is not None: cc[i]["costo_total"] = f"{total[c]:,.2f}"
            if not tipo: kk[i]["tipo"] = "falta"
            if hijos[c] and tipo == "Paquete de trabajo": prob.append("un paquete de trabajo no se descompone"); kk[i]["tipo"] = "mal"
            if not hijos[c] and tipo in ("Proyecto", "Entregable", "Cuenta de control"): prob.append("el nivel más bajo debe ser paquete de trabajo o de planificación")
            if tipo == "Paquete de trabajo":
                n_pt += 1
                if not f.get("responsable"): kk[i]["responsable"] = "falta"
                if not f.get("aceptacion"): kk[i]["aceptacion"] = "falta"
                if hay_cuentas:
                    anc, p = [], padre_de(c)
                    while p in idx: anc.append(filas[idx[p]].get("tipo")); p = padre_de(p)
                    if anc.count("Cuenta de control") != 1: prob.append("debe pertenecer a una sola cuenta de control")
            if tipo == "Cuenta de control" and sum(1 for x in descendientes(c) if filas[idx[x]].get("tipo") == "Paquete de trabajo") < 2:
                prob.append("una cuenta de control tiene dos o más paquetes de trabajo")
            propio = N(f.get("costo"))
            if hijos[c] and propio is not None and total.get(c) is not None and abs(propio - total[c]) > max(.005 * abs(propio), .01):
                prob.append(f"regla del 100%: su costo ({propio:,.2f}) no es la suma de sus elementos ({total[c]:,.2f})"); kk[i]["costo"] = "mal"
            cc[i]["revision"] = "; ".join(prob) or "correcta"; kk[i]["revision"] = "no" if prob else "ok"
        cab = {}
        if idx:
            cab["resumen"] = f"{len(idx)} elementos · {n_pt} paquetes de trabajo · {max(c.count('.') for c in idx) + 1} niveles"
            if len(raices) == 1 and total.get(raices[0]) is not None: cab["costo_total"] = f"{total[raices[0]]:,.2f}"
            if not n_pt: av.append("Aún no hay paquetes de trabajo: descompón hasta el nivel donde se pueda estimar costo y duración.")
        g = arbol_svg({c: (filas[i].get("nombre") or "", filas[i].get("tipo") or "") for c, i in idx.items()})
        return {"cab": cab, "calc": {"elementos": cc}, "clases": {"elementos": kk}, "avisos": av, "bloques": [{"tipo": "grafica", "svg": g}] if g else []}


# ======================= CRONOGRAMA (método de la ruta crítica) =======================
RELACION = {"FS": "FS", "FC": "FS", "SS": "SS", "CC": "SS", "FF": "FF", "SF": "SF", "CF": "SF"}
TOKEN = re.compile(r"^\s*([A-Za-z0-9_.\-]+?)\s*(FS|SS|FF|SF|FC|CC|CF)?\s*([+-]\s*\d+(?:\.\d+)?)?\s*$", re.I)


def leer_pred(texto):
    """«A, B FS+2, C CC-1» -> [(id, tipo, retraso)]. FS/FC fin-comienzo (por omisión), SS/CC comienzo-comienzo, FF fin-fin, SF/CF comienzo-fin."""
    out = []
    for t in [x for x in (texto or "").replace(";", ",").split(",") if x.strip()]:
        m = TOKEN.match(t)
        if not m: raise ValueError(t.strip())
        out.append((m.group(1), RELACION[(m.group(2) or "FS").upper()], float((m.group(3) or "0").replace(" ", ""))))
    return out


def duracion_esperada(o, m, p, dist="triangular"):
    """PMBOK 6, 6.4.2.4: triangular tE = (tO + tM + tP)/3. Beta (PERT) (tO + 4tM + tP)/6 tomada de 7.2.2.5 (costos)."""
    if None in (o, m, p): return m
    return (o + 4 * m + p) / 6 if dist == "beta" else (o + m + p) / 3


def cpm(acts):
    """acts: {id: (duración, [(pred, tipo, retraso)])}. Pasadas hacia adelante y hacia atrás (PMBOK 6, 6.5.2.2) con FS, SS, FF y SF.
    Devuelve dict por actividad con ES, EF, LS, LF, holgura total y libre (base 0), la duración del proyecto y el orden."""
    suc = {a: [] for a in acts}
    for a, (_, ps) in acts.items():
        for p, t, l in ps:
            if p not in acts: raise KeyError(p)
            suc[p].append((a, t, l))
    gin = {a: len(ps) for a, (_, ps) in acts.items()}; orden = [a for a in acts if gin[a] == 0]; k = 0
    while k < len(orden):
        for s, _, _ in suc[orden[k]]:
            gin[s] -= 1
            if gin[s] == 0: orden.append(s)
        k += 1
    if len(orden) < len(acts): raise RecursionError("ciclo")
    r = {}
    for a in orden:
        d, ps = acts[a]; es = 0.0
        for p, t, l in ps:
            P = r[p]
            es = max(es, {"FS": P["EF"] + l, "SS": P["ES"] + l, "FF": P["EF"] + l - d, "SF": P["ES"] + l - d}[t])
        r[a] = {"ES": es, "EF": es + d, "d": d}
    fin = max((x["EF"] for x in r.values()), default=0.0)
    for a in reversed(orden):
        d = r[a]["d"]; lf = fin
        for s, t, l in suc[a]:
            S = r[s]
            lf = min(lf, {"FS": S["LS"] - l, "SS": S["LS"] - l + d, "FF": S["LF"] - l, "SF": S["LF"] - l + d}[t])
        r[a]["LF"] = lf; r[a]["LS"] = lf - d; r[a]["TF"] = lf - d - r[a]["ES"]
        ff = fin - r[a]["EF"]
        for s, t, l in suc[a]:
            S = r[s]; ff = min(ff, {"FS": S["ES"] - l - r[a]["EF"], "SS": S["ES"] - l - r[a]["ES"], "FF": S["EF"] - l - r[a]["EF"], "SF": S["EF"] - l - r[a]["ES"]}[t])
        r[a]["FF"] = ff
    return r, fin, orden


def fecha_de(inicio, dias, habiles):
    """Fecha del día `dias` (base 0) a partir de `inicio`; en días hábiles salta sábados y domingos."""
    if inicio is None: return None
    if not habiles: return inicio + timedelta(days=dias)
    f = inicio
    while f.weekday() >= 5: f += timedelta(days=1)
    k = 0
    while k < dias:
        f += timedelta(days=1)
        if f.weekday() < 5: k += 1
    return f


def gantt_svg(filas, fin):
    if not filas: return None
    w, lh, iz = 760, 22, 170; h = 30 + lh * len(filas); esc = (w - iz - 20) / max(fin, 1)
    s = ""
    paso = max(1, int(math.ceil(fin / 12)))
    for k in range(0, int(fin) + 1, paso):
        x = iz + k * esc; s += f'<line x1="{x:.1f}" x2="{x:.1f}" y1="16" y2="{h}" stroke="#ede7dc"/><text x="{x:.1f}" y="12" text-anchor="middle" fill="#6f675b" font-size="9">{k}</text>'
    for r, (nom, es, ef, crit, hito, bi, bf) in enumerate(filas):
        y = 24 + r * lh
        s += f'<text x="4" y="{y + 12}" fill="#2b2620">{_t(nom)[:26]}</text>'
        if bi is not None and bf is not None:
            s += f'<rect x="{iz + bi * esc:.1f}" y="{y + 13}" width="{max((bf - bi) * esc, 2):.1f}" height="4" fill="#a79f92"/>'
        if hito:
            x = iz + ef * esc; s += f'<path d="M{x:.1f} {y + 2}l7 7l-7 7l-7-7z" fill="{"#b3261e" if crit else "#2b2620"}"/>'
        else:
            s += f'<rect x="{iz + es * esc:.1f}" y="{y + 2}" width="{max((ef - es) * esc, 2):.1f}" height="11" rx="3" fill="{"#b3261e" if crit else "#dd5813"}"/>'
    s += f'<text x="{w - 4}" y="{h - 2}" text-anchor="end" fill="#6f675b" font-size="9">rojo: ruta crítica · gris: línea base · días desde el inicio</text>'
    return _svg(w, h + 8, s)


@formato
class Cronograma(Formato):
    ID, TITULO, REDIBUJAR = "CRONOGRAMA", "Cronograma: red, ruta crítica y línea base", True
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("inicio", "Fecha de inicio (DD/MM/AAAA)"),
                F("plantilla", "Cargar plantilla en un cronograma vacío", tipo="opcion", opciones=[["", "(ninguna)"], ["dmaic", "Actividades DMAIC del curso, en secuencia"]]),
                F("calendario", "Calendario", tipo="opcion", opciones=[["habiles", "Días hábiles (lunes a viernes)"], ["naturales", "Días naturales"]], defecto="habiles"),
                F("distribucion", "Distribución para tres puntos", tipo="opcion", opciones=[["triangular", "Triangular (O + M + P)/3"], ["beta", "Beta o PERT (O + 4M + P)/6"]], defecto="triangular"),
                F("fijar_base", "Línea base", tipo="opcion", opciones=[["", "—"], ["fijar", "Fijar la línea base con las fechas actuales"], ["borrar", "Borrar la línea base"]]),
                F("base_fecha", "Línea base fijada el", lectura=True),
                F("duracion", "Duración del proyecto", calc=True), F("fin", "Fin temprano del proyecto", calc=True), F("ruta", "Ruta crítica", calc=True),
                F("desvio", "Desvío contra la línea base", calc=True)]
    TABLAS = [{"id": "actividades", "titulo": "Actividades (predecesoras: «A, B FS+2, C CC-1»; FS fin-comienzo, SS comienzo-comienzo, FF fin-fin, SF comienzo-fin)", "filas": 8, "columnas": [
        {"campo": "id", "etiqueta": "Id", "ancho": 56}, {"campo": "nombre", "etiqueta": "Actividad", "ancho": 190}, {"campo": "edt", "etiqueta": "Código EDT", "ancho": 80},
        {"campo": "hito", "etiqueta": "Hito", "tipo": "opcion", "opciones": SI("Sí"), "ancho": 56},
        {"campo": "o", "etiqueta": "Optimista", "tipo": "numero", "ancho": 70}, {"campo": "m", "etiqueta": "Más probable", "tipo": "numero", "ancho": 80},
        {"campo": "p", "etiqueta": "Pesimista", "tipo": "numero", "ancho": 70}, {"campo": "te", "etiqueta": "Duración", "calc": True, "ancho": 70},
        {"campo": "pred", "etiqueta": "Predecesoras", "ancho": 120},
        {"campo": "es", "etiqueta": "Inicio temprano", "calc": True, "ancho": 100}, {"campo": "ef", "etiqueta": "Fin temprano", "calc": True, "ancho": 100},
        {"campo": "ls", "etiqueta": "Inicio tardío", "calc": True, "ancho": 100}, {"campo": "lf", "etiqueta": "Fin tardío", "calc": True, "ancho": 100},
        {"campo": "ht", "etiqueta": "Holgura total", "calc": True, "ancho": 80}, {"campo": "hl", "etiqueta": "Holgura libre", "calc": True, "ancho": 80},
        {"campo": "base_ini", "etiqueta": "Inicio en línea base", "lectura": True, "ancho": 100}, {"campo": "base_fin", "etiqueta": "Fin en línea base", "lectura": True, "ancho": 100},
        {"campo": "desv", "etiqueta": "Desvío del fin (días)", "calc": True, "ancho": 90}]}]
    NOTA = ("PMBOK 6: actividades e hitos 6.2.3.1 y 6.2.3.3; relaciones FS, FF, SS y SF, adelantos y retrasos 6.3.2 (FS es la más común, SF casi "
            "no se usa; se evitan ciclos); tres puntos 6.4.2.4 (triangular; la beta (O + 4M + P)/6 viene de 7.2.2.5, costos); ruta crítica 6.5.2.2 "
            "con pasadas hacia adelante y hacia atrás, holgura total y libre (verificado con la figura 6-16: A-C-D = 30 días, holgura de B = 5); "
            "línea base del cronograma 6.5.3.1 (versión aprobada, se compara con lo real). Los días se muestran con la convención del PMBOK de "
            "iniciar el día 1. Para programar fechas la duración esperada se redondea hacia arriba a días enteros [criterio de uso]. PMBOK 7, 2.4.2.3.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        if d["cabecera"].get("plantilla") == "dmaic":
            if not any(f.get("id") or f.get("nombre") for f in d["tablas"]["actividades"]): d["tablas"]["actividades"] = plantilla_cronograma()
            d["cabecera"]["plantilla"] = ""
        c = d["cabecera"]; filas = d["tablas"]["actividades"]; cc, kk, av = [{} for _ in filas], [{} for _ in filas], []
        inicio = a_fecha((c.get("inicio") or "").strip()); habiles = (c.get("calendario") or "habiles") == "habiles"
        if c.get("inicio") and inicio is None: av.append("La fecha de inicio no es válida (DD/MM/AAAA).")
        dist = c.get("distribucion") or "triangular"; edt = {(f.get("codigo") or "").strip() for f in ((proyecto.formatos.get("EDT") or {}).get("tablas", {}).get("elementos", []) if proyecto else [])}
        acts, pos = {}, {}
        for i, f in enumerate(filas):
            a = (f.get("id") or "").strip()
            if not a:
                if not fila_vacia(f): kk[i]["id"] = "falta"
                continue
            if a in acts: kk[i]["id"] = "mal"; av.append(f"El id {a} está repetido."); continue
            o, m, p = N(f.get("o")), N(f.get("m")), N(f.get("p"))
            for x in ("o", "m", "p"):
                if f.get(x) and (N(f[x]) is None or N(f[x]) < 0): kk[i][x] = "mal"
            if f.get("hito") == "Sí": dur = 0.0
            else:
                if m is None: kk[i]["m"] = "falta"; continue
                if None not in (o, p) and not (o <= m <= p): kk[i]["o"] = kk[i]["p"] = "mal"; av.append(f"{a}: debe cumplirse optimista ≤ más probable ≤ pesimista.")
                te = duracion_esperada(o, m, p, dist); cc[i]["te"] = num(te, 3); dur = float(math.ceil(te - 1e-9))
            try:
                ps = leer_pred(f.get("pred"))
            except ValueError as e:
                kk[i]["pred"] = "mal"; av.append(f"{a}: no entiendo la predecesora «{e}». Usa por ejemplo «B», «B FS+2» o «C CC-1»."); ps = []
            if f.get("edt") and edt and f["edt"].strip() not in edt: kk[i]["edt"] = "advertencia"; av.append(f"{a}: el código EDT {f['edt']} no está en la EDT del proyecto.")
            acts[a] = (dur, ps); pos[a] = i
        for a, (_, ps) in list(acts.items()):
            malos = [p for p, _, _ in ps if p not in acts]
            if malos: kk[pos[a]]["pred"] = "mal"; av.append(f"{a}: predecesora inexistente {', '.join(malos)}."); acts[a] = (acts[a][0], [x for x in ps if x[0] in acts])
        cab, bl = {}, []
        if not acts: return {"cab": cab, "calc": {"actividades": cc}, "clases": {"actividades": kk}, "avisos": av}
        try:
            r, fin, orden = cpm(acts)
        except RecursionError:
            av.append("Las predecesoras forman un ciclo (una actividad termina dependiendo de sí misma); revísalas.")
            return {"cab": cab, "calc": {"actividades": cc}, "clases": {"actividades": kk}, "avisos": av}
        dia = lambda x: num(x, 3)
        def mostrar(v, es_fin, dur):
            if inicio: f = fecha_de(inicio, v - (1 if es_fin and dur > 0 else 0), habiles); return f.strftime("%d/%m/%Y")
            return "día " + dia(v + (0 if es_fin else 1) if dur > 0 else v)
        accion = c.get("fijar_base") or ""
        criticas = []
        for a in orden:
            i = pos[a]; x = r[a]; dur = x["d"]
            cc[i].update(es=mostrar(x["ES"], False, dur), ef=mostrar(x["EF"], True, dur), ls=mostrar(x["LS"], False, dur), lf=mostrar(x["LF"], True, dur),
                         ht=dia(x["TF"]), hl=dia(x["FF"]))
            crit = abs(x["TF"]) < 1e-9; kk[i]["ht"] = "no" if crit else "ok"
            if crit: criticas.append(a)
            if x["TF"] < -1e-9: av.append(f"{a}: holgura negativa.")
            if accion == "fijar": filas[i]["base_ini"], filas[i]["base_fin"] = str(x["ES"]), str(x["EF"])
            if accion == "borrar": filas[i]["base_ini"] = filas[i]["base_fin"] = ""
        if accion == "fijar":
            from datetime import date
            c["base_fecha"] = date.today().strftime("%d/%m/%Y"); c["fijar_base"] = ""
        elif accion == "borrar": c["base_fecha"] = ""; c["fijar_base"] = ""
        atraso = []
        for a in orden:
            i = pos[a]; bf = N(filas[i].get("base_fin"))
            if bf is not None:
                dv = r[a]["EF"] - bf; cc[i]["desv"] = f"{dv:+g}" if dv else "0"; kk[i]["desv"] = "no" if dv > 0 else "ok"
                if dv > 0: atraso.append((a, dv))
        cab["duracion"] = f"{dia(fin)} días {'hábiles' if habiles else 'naturales'}"
        if inicio: cab["fin"] = fecha_de(inicio, fin - 1 if fin > 0 else 0, habiles).strftime("%d/%m/%Y")
        cab["ruta"] = " → ".join(criticas)
        bases = [N(filas[pos[a]].get("base_fin")) for a in orden]
        if any(b is not None for b in bases):
            fin_base = max(b for b in bases if b is not None); cab["desvio"] = f"{fin - fin_base:+g} días en el fin del proyecto" if fin != fin_base else "sin desvío"
            if atraso: av.append("Terminan después de la línea base: " + ", ".join(f"{a} (+{dv:g})" for a, dv in atraso) + ". Si el cambio es aprobado, regístralo en la bitácora de cambios.")
        bl = [{"tipo": "grafica", "svg": gantt_svg([(f"{a} {filas[pos[a]].get('nombre') or ''}", r[a]["ES"], r[a]["EF"], a in criticas, r[a]["d"] == 0,
                                                     N(filas[pos[a]].get("base_ini")), N(filas[pos[a]].get("base_fin"))) for a in orden], fin)}]
        return {"cab": cab, "calc": {"actividades": cc}, "clases": {"actividades": kk}, "avisos": av, "bloques": bl}


# ======================= MONTE CARLO del cronograma =======================
def muestrear(o, m, p, n, rng, dist):
    if o is None or p is None or p <= o: return np.full(n, float(m))
    if dist == "beta":                                                       # beta-PERT
        a = 1 + 4 * (m - o) / (p - o); b = 1 + 4 * (p - m) / (p - o)
        return o + (p - o) * rng.beta(a, b, n)
    return rng.triangular(o, m, p, n)


def simular(acts3, n, semilla, dist):
    """acts3: {id: (o, m, p, [(pred, tipo, retraso)])}. CPM vectorizado sobre n iteraciones. Devuelve duraciones del proyecto e índice de criticidad."""
    rng = np.random.default_rng(semilla)
    D = {a: (np.zeros(n) if (o, m, p) == (0, 0, 0) else muestrear(o, m, p, n, rng, dist)) for a, (o, m, p, _) in acts3.items()}
    _, _, orden = cpm({a: (1.0, ps) for a, (_, _, _, ps) in acts3.items()})
    suc = {a: [] for a in acts3}
    for a, (*_, ps) in acts3.items():
        for p_, t, l in ps: suc[p_].append((a, t, l))
    ES, EF = {}, {}
    for a in orden:
        es = np.zeros(n)
        for p_, t, l in acts3[a][3]:
            es = np.maximum(es, {"FS": EF[p_] + l, "SS": ES[p_] + l, "FF": EF[p_] + l - D[a], "SF": ES[p_] + l - D[a]}[t])
        ES[a] = es; EF[a] = es + D[a]
    fin = np.max(np.vstack([EF[a] for a in orden]), axis=0)
    LS, LF = {}, {}
    for a in reversed(orden):
        lf = fin.copy()
        for s, t, l in suc[a]:
            lf = np.minimum(lf, {"FS": LS[s] - l, "SS": LS[s] - l + D[a], "FF": LF[s] - l, "SF": LF[s] - l + D[a]}[t])
        LF[a] = lf; LS[a] = lf - D[a]
    crit = {a: float(np.mean(np.abs(LS[a] - ES[a]) < 1e-7)) for a in orden}
    simular.muestras = D                       # duraciones simuladas por actividad (para la sensibilidad)
    return fin, crit


def histograma_svg(x, meta=None):
    w, h, iz, ab = 720, 240, 50, 30
    cuentas, bordes = np.histogram(x, bins=min(30, max(8, int(math.sqrt(len(x)) / 2))))
    mx = cuentas.max(); lo, hi = bordes[0], bordes[-1]; esc = (w - iz - 50) / (hi - lo if hi > lo else 1)
    s = ""; bw = esc * (bordes[1] - bordes[0])
    for c_, b in zip(cuentas, bordes[:-1]):
        bh = (h - ab - 20) * c_ / mx; s += f'<rect x="{iz + (b - lo) * esc:.1f}" y="{h - ab - bh:.1f}" width="{max(bw - 1, 1):.1f}" height="{bh:.1f}" fill="#f6c9a8"/>'
    xs = np.sort(x); ys = np.arange(1, len(xs) + 1) / len(xs); pts = xs[:: max(1, len(xs) // 200)]
    s += '<polyline fill="none" stroke="#dd5813" stroke-width="2" points="' + " ".join(f"{iz + (v - lo) * esc:.1f},{h - ab - (h - ab - 20) * np.searchsorted(xs, v, 'right') / len(xs):.1f}" for v in pts) + '"/>'
    for q, et in ((.5, "P50"), (.8, "P80")):
        v = float(np.quantile(x, q)); xx = iz + (v - lo) * esc
        s += f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="14" y2="{h - ab}" stroke="#2b2620" stroke-dasharray="4 3"/><text x="{xx + 3:.1f}" y="24" fill="#2b2620">{et} {num(v, 4)}</text>'
    if meta is not None and lo <= meta <= hi:
        xx = iz + (meta - lo) * esc; s += f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="14" y2="{h - ab}" stroke="#b3261e" stroke-width="2"/><text x="{xx + 3:.1f}" y="40" fill="#b3261e">meta</text>'
    for k in range(6):
        v = lo + (hi - lo) * k / 5; s += f'<text x="{iz + (v - lo) * esc:.1f}" y="{h - ab + 14}" text-anchor="middle" fill="#6f675b">{num(v, 3)}</text>'
    s += f'<text x="{w - 6}" y="{h - 4}" text-anchor="end" fill="#6f675b">duración del proyecto (días) · barras: frecuencia · línea: probabilidad acumulada (curva S)</text>'
    return _svg(w, h, s)


@formato
class MonteCarlo(Formato):
    ID, TITULO = "MONTECARLO", "Riesgo del cronograma por Monte Carlo"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("iteraciones", "Iteraciones (100 a 20,000)", tipo="numero", defecto="2000"),
                F("semilla", "Semilla (la misma semilla da el mismo resultado)", tipo="numero", defecto="1"),
                F("distribucion", "Distribución de cada duración", tipo="opcion", opciones=[["triangular", "Triangular"], ["beta", "Beta (PERT)"]], defecto="triangular"),
                F("meta", "Duración meta a evaluar (días, opcional)", tipo="numero"),
                F("determinista", "Duración con los valores más probables", calc=True), F("p50", "P50 / P80 / P90", calc=True),
                F("prob_meta", "Probabilidad de cumplir la meta", calc=True), F("media", "Media y desviación estándar", calc=True)]
    TABLAS = []
    NOTA = ("PMBOK 6, 11.4.2.5: la simulación combina los efectos de las incertidumbres; para el cronograma usa la red y las estimaciones de "
            "duración, se itera miles de veces con valores al azar y da un histograma y una curva S de probabilidad acumulada (figura 11-13); "
            "el índice de criticidad es el porcentaje de iteraciones en que cada actividad queda en la ruta crítica; el análisis de sensibilidad se muestra como diagrama de tornado con la correlación de cada duración con la del proyecto (11.4.2.5). PMBOK 7, 2.4.2.2 y 4.4.1. Los "
            "datos se toman del formato Cronograma (optimista, más probable y pesimista de cada actividad). En la simulación las duraciones no se "
            "redondean.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c = d["cabecera"]; av, cab = [], {}
        crono = (proyecto.formatos.get("CRONOGRAMA") or {}) if proyecto else {}
        filas = (crono.get("tablas") or {}).get("actividades", [])
        acts3 = {}
        for f in filas:
            a = (f.get("id") or "").strip()
            if not a or a in acts3: continue
            o, m, p = N(f.get("o")), N(f.get("m")), N(f.get("p"))
            if f.get("hito") == "Sí": o = m = p = 0.0
            if m is None: continue
            try: ps = leer_pred(f.get("pred"))
            except ValueError: ps = []
            acts3[a] = (o, m, p, ps)
        for a in list(acts3):
            o, m, p, ps = acts3[a]; acts3[a] = (o, m, p, [x for x in ps if x[0] in acts3])
        if not acts3:
            av.append("Primero captura las actividades en Gestión > Cronograma (con optimista, más probable y pesimista).")
            return {"cab": cab, "calc": {}, "clases": {}, "avisos": av}
        sin_rango = [a for a, (o, m, p, _) in acts3.items() if (o is None or p is None) and m]
        if sin_rango: av.append("Sin optimista y pesimista (se toman fijas): " + ", ".join(sin_rango) + ".")
        n = int(min(max(N(c.get("iteraciones")) or 2000, 100), 20000)); sem = int(N(c.get("semilla")) or 1)
        try:
            det, _, _ = cpm({a: (m, ps) for a, (_, m, _, ps) in acts3.items()})[0:3]
            fin_det = cpm({a: (m, ps) for a, (_, m, _, ps) in acts3.items()})[1]
            x, crit = simular(acts3, n, sem, c.get("distribucion") or "triangular")
        except RecursionError:
            av.append("Las predecesoras del cronograma forman un ciclo."); return {"cab": cab, "calc": {}, "clases": {}, "avisos": av}
        q = lambda k: float(np.quantile(x, k))
        cab["determinista"] = f"{num(fin_det, 4)} días"
        cab["p50"] = f"{num(q(.5), 4)} / {num(q(.8), 4)} / {num(q(.9), 4)} días"
        cab["media"] = f"{num(float(x.mean()), 4)} ± {num(float(x.std(ddof=1)), 3)} días ({n:,} iteraciones)"
        meta = N(c.get("meta"))
        if meta is not None:
            pm = float(np.mean(x <= meta)); cab["prob_meta"] = pct(pm, 1)
            if pm < .5: av.append(f"Solo hay {pct(pm, 0)} de probabilidad de terminar en {num(meta, 4)} días o menos.")
        if np.mean(x <= fin_det) < .5:
            av.append(f"La duración con los valores más probables ({num(fin_det, 4)} días) tiene solo {pct(float(np.mean(x <= fin_det)))} de probabilidad: "
                      "las estimaciones de un solo punto suelen ser optimistas.")
        orden = sorted(crit.items(), key=lambda t: -t[1])
        w, lh, iz = 720, 20, 160; hh = 24 + lh * len(orden)
        s = '<text x="4" y="14" fill="#2b2620" font-weight="700">Índice de criticidad (% de iteraciones en la ruta crítica)</text>'
        for k, (a, v) in enumerate(orden):
            y = 22 + k * lh; s += f'<text x="4" y="{y + 12}" fill="#2b2620">{_t(a)[:24]}</text><rect x="{iz}" y="{y + 2}" width="{(w - iz - 60) * v:.1f}" height="12" rx="2" fill="{"#b3261e" if v > .5 else "#dd5813"}"/><text x="{iz + (w - iz - 60) * v + 4:.1f}" y="{y + 12}" fill="#6f675b">{pct(v)}</text>'
        bl = [{"tipo": "grafica", "svg": histograma_svg(x, meta)}, {"tipo": "grafica", "svg": _svg(w, hh, s)}]
        # Sensibilidad: correlación de rangos de Spearman entre cada duración y la del proyecto, en forma de tornado (PMBOK 6, 11.4.2.5)
        from scipy.stats import spearmanr
        rho = []
        for a, dv in getattr(simular, "muestras", {}).items():
            if np.std(dv) > 0: rho.append((a, float(spearmanr(dv, x).statistic)))
        rho = sorted(rho, key=lambda t: -abs(t[1]))[:10]
        if rho:
            wt, lt, it = 720, 22, 170; ht = 30 + lt * len(rho); mid = it + (wt - it - 20) / 2; e = (wt - it - 20) / 2
            st_ = '<text x="4" y="14" fill="#2b2620" font-weight="700">Diagrama de tornado: correlación de cada duración con la del proyecto</text>'
            st_ += f'<line x1="{mid}" x2="{mid}" y1="20" y2="{ht - 4}" stroke="#c9bfae"/>'
            for k2, (a, r_) in enumerate(rho):
                y = 22 + k2 * lt; an = abs(r_) * e
                st_ += f'<text x="4" y="{y + 12}" fill="#2b2620">{_t(a)[:22]}</text><rect x="{mid if r_ >= 0 else mid - an:.1f}" y="{y + 1}" width="{an:.1f}" height="14" rx="2" fill="#dd5813"/>'
                st_ += f'<text x="{mid + (an + 4 if r_ >= 0 else -an - 4):.1f}" y="{y + 12}" text-anchor="{"start" if r_ >= 0 else "end"}" fill="#6f675b">{r_:.2f}</text>'
            bl.append({"tipo": "grafica", "svg": _svg(wt, ht, st_)})
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av, "bloques": bl}


# ======================= ÁRBOL DE DECISIÓN =======================
@formato
class ArbolDecision(Formato):
    ID, TITULO = "ARBOL-DECISION", "Árbol de decisión (valor monetario esperado)"
    CABECERA = [F("decision", "Decisión a tomar"), F("criterio", "Criterio", tipo="opcion", opciones=[["max", "Maximizar valor (ganancias)"], ["min", "Minimizar costo"]], defecto="max"),
                F("resultado", "Decisión recomendada", calc=True)]
    TABLAS = [{"id": "nodos", "titulo": "Nodos (cada fila es una rama que sale de su nodo padre; la raíz no tiene padre)", "filas": 7, "columnas": [
        {"campo": "n", "etiqueta": "N.º", "calc": True, "ancho": 50}, {"campo": "padre", "etiqueta": "Padre (N.º)", "tipo": "numero", "ancho": 80},
        {"campo": "tipo", "etiqueta": "Tipo de nodo", "tipo": "opcion", "opciones": SI("Decisión", "Azar", "Resultado"), "ancho": 110},
        {"campo": "etiqueta", "etiqueta": "Rama o escenario", "ancho": 200}, {"campo": "prob", "etiqueta": "Probabilidad (%) si viene de un nodo de azar", "tipo": "numero", "ancho": 140},
        {"campo": "costo", "etiqueta": "Costo o inversión de la rama", "tipo": "numero", "ancho": 120}, {"campo": "valor", "etiqueta": "Pago al final (resultados)", "tipo": "numero", "ancho": 120},
        {"campo": "vme", "etiqueta": "VME del nodo", "calc": True, "ancho": 100}, {"campo": "neto", "etiqueta": "Valor neto de la ruta", "calc": True, "ancho": 110}]}]
    NOTA = ("PMBOK 6, 11.4.2.5 y figura 11-15: las ramas representan decisiones o eventos con sus costos; los extremos dan el resultado de seguir esa "
            "ruta; se evalúa calculando el valor monetario esperado de cada rama y se elige la mejor. Verificado con el ejemplo del libro: construir "
            "(inversión 120M; demanda fuerte 60% a 200M, débil 40% a 90M) da 36M; mejorar (50M; 120M y 60M) da 46M; se elige mejorar. PMBOK 7, 4.4.1.")

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["nodos"][0] = {"tipo": "Decisión", "etiqueta": "Decisión"}; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = d["tablas"]["nodos"]; cc, kk, av = [{"n": str(i + 1)} for i in range(len(filas))], [{} for _ in filas], []
        usadas = [i for i, f in enumerate(filas) if f.get("tipo") or f.get("etiqueta")]
        hijos = {i: [] for i in usadas}; raices = []
        for i in usadas:
            p = N(filas[i].get("padre"))
            if p is None: raices.append(i); continue
            p = int(p) - 1
            if p not in hijos or p == i: kk[i]["padre"] = "mal"; av.append(f"Nodo {i + 1}: el padre {p + 1} no existe."); continue
            hijos[p].append(i)
        if len(raices) != 1:
            if usadas: av.append("Debe haber exactamente un nodo raíz (sin padre).")
            return {"cab": {}, "calc": {"nodos": cc}, "clases": {"nodos": kk}, "avisos": av}
        maxim = (d["cabecera"].get("criterio") or "max") == "max"; vme, elegido = {}, {}
        visit = set()
        def valor(i):
            if i in visit: raise RecursionError
            visit.add(i); f = filas[i]; t = f.get("tipo")
            if not t: kk[i]["tipo"] = "falta"
            if t == "Resultado" or not hijos[i]:
                if hijos[i]: kk[i]["tipo"] = "mal"; av.append(f"Nodo {i + 1}: un resultado no tiene ramas.")
                v = N(f.get("valor"))
                if v is None: kk[i]["valor"] = "falta"; v = 0.0
                if t in ("Decisión", "Azar"): av.append(f"Nodo {i + 1}: un nodo de {t.lower()} necesita ramas.")
                vme[i] = v; return v
            if t == "Azar":
                tot = 0.0; sp = 0.0
                for h in hijos[i]:
                    pr = N(filas[h].get("prob"))
                    if pr is None: kk[h]["prob"] = "falta"; pr = 0.0
                    sp += pr; tot += pr / 100 * (valor(h) - (N(filas[h].get("costo")) or 0))
                if abs(sp - 100) > 1e-6: av.append(f"Nodo {i + 1}: las probabilidades de sus ramas suman {num(sp, 4)}%, deben sumar 100%.")
                vme[i] = tot; return tot
            opciones = [(valor(h) - (N(filas[h].get("costo")) or 0), h) for h in hijos[i]]
            mejor = max(opciones) if maxim else min(opciones)
            elegido[i] = mejor[1]; vme[i] = mejor[0]; return mejor[0]
        try:
            valor(raices[0])
        except RecursionError:
            av.append("Las referencias de padre forman un ciclo."); return {"cab": {}, "calc": {"nodos": cc}, "clases": {"nodos": kk}, "avisos": av}
        def neto(i, acum):
            acum -= N(filas[i].get("costo")) or 0
            if not hijos[i]: cc[i]["neto"] = f"{acum + (N(filas[i].get('valor')) or 0):,.2f}"
            for h in hijos[i]: neto(h, acum)
        neto(raices[0], 0.0)
        for i, v in vme.items():
            cc[i]["vme"] = f"{v:,.2f}"
            if filas[i].get("tipo") in ("Decisión", "Azar") and i != raices[0]:
                cc[i]["vme"] = f"{v:,.2f} (neto {v - (N(filas[i].get('costo')) or 0):,.2f})"
        for p, h in elegido.items(): kk[h]["etiqueta"] = "ok"
        r = raices[0]
        cab = {"resultado": f"{filas[elegido[r]].get('etiqueta') or 'Nodo ' + str(elegido[r] + 1)} · VME {vme[r]:,.2f}"} if r in elegido else {}
        # dibujo
        prof = {r: 0}; orden = [r]
        for i in orden:
            for h in hijos[i]: prof[h] = prof[i] + 1; orden.append(h)
        hojas = [i for i in orden if not hijos[i]]; y = {}
        def asignar(i, cont=[0]):
            if not hijos[i]: y[i] = cont[0]; cont[0] += 1
            else:
                for h in hijos[i]: asignar(h, cont)
                y[i] = sum(y[h] for h in hijos[i]) / len(hijos[i])
        asignar(r, [0])
        P = max(prof.values()) + 1; w = 760; hh = 30 + 46 * max(len(hojas), 1); dx = (w - 200) / max(P - 1, 1)
        X = lambda i: 30 + prof[i] * dx; Y = lambda i: 24 + y[i] * 46
        s = ""
        for i in orden:
            for h in hijos[i]:
                ok = elegido.get(i) == h
                s += f'<path d="M{X(i):.1f} {Y(i):.1f}L{X(i) + 26:.1f} {Y(h):.1f}H{X(h):.1f}" fill="none" stroke="{"#dd5813" if ok else "#a79f92"}" stroke-width="{3 if ok else 1.4}"/>'
                lab = (filas[h].get("etiqueta") or "")[:22] + (f" {num(N(filas[h].get('prob')) or 0, 3)}%" if filas[i].get("tipo") == "Azar" else "")
                s += f'<text x="{X(i) + 30:.1f}" y="{Y(h) - 5:.1f}" fill="#2b2620">{_t(lab)}</text>'
        for i in orden:
            t = filas[i].get("tipo"); x0, y0 = X(i), Y(i)
            if t == "Decisión": s += f'<rect x="{x0 - 8:.1f}" y="{y0 - 8:.1f}" width="16" height="16" fill="#2b2620"/>'
            elif t == "Azar": s += f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="8" fill="#2b2620"/>'
            else: s += f'<path d="M{x0 + 8:.1f} {y0 - 8:.1f}L{x0 - 6:.1f} {y0:.1f}L{x0 + 8:.1f} {y0 + 8:.1f}Z" fill="#2b2620"/>'
            if i in vme: s += f'<text x="{x0 + (14 if not hijos[i] else 0):.1f}" y="{y0 + (4 if not hijos[i] else 22):.1f}" fill="#dd5813" font-weight="700">{num(vme[i], 4) if not hijos[i] else "VME " + num(vme[i], 4)}</text>'
        return {"cab": cab, "calc": {"nodos": cc}, "clases": {"nodos": kk}, "avisos": av, "bloques": [{"tipo": "grafica", "svg": _svg(w, hh, s)}]}


# ======================= FODA =======================
def cuadros_svg(titulos, listas, colores):
    w, h = 760, 40 + 18 * max(max((len(l) for l in listas), default=1), 4) * 2 // 2 + 60
    cw, ch = (w - 30) / 2, (h - 30) / 2; s = ""
    for k, (t, l, col) in enumerate(zip(titulos, listas, colores)):
        x, y = 10 + (k % 2) * (cw + 10), 10 + (k // 2) * (ch + 10)
        s += f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="8" fill="{col}" stroke="#e2dcd0"/><text x="{x + 10:.1f}" y="{y + 20:.1f}" fill="#2b2620" font-weight="700">{t} ({len(l)})</text>'
        for j, it in enumerate(l[:int((ch - 30) / 16)]): s += f'<text x="{x + 14:.1f}" y="{y + 40 + 16 * j:.1f}" fill="#2b2620">• {_t(it)[:48]}</text>'
    return _svg(w, h, s)


@formato
class Foda(Formato):
    ID, TITULO = "FODA", "Análisis FODA"
    CABECERA = [F("objeto", "Qué se analiza (proyecto, organización o área)"), F("resumen", "Riesgos derivados", calc=True)]
    COLS = lambda extra: [{"campo": "factor", "etiqueta": "Factor", "ancho": 320}, {"campo": "impacto", "etiqueta": "Peso", "tipo": "opcion", "opciones": SI("Alto", "Medio", "Bajo"), "ancho": 90}] + extra
    TABLAS = [{"id": "fortalezas", "titulo": "Fortalezas (internas)", "filas": 4, "columnas": COLS([{"campo": "deriva", "etiqueta": "Oportunidad que puede generar", "ancho": 240}])},
              {"id": "debilidades", "titulo": "Debilidades (internas)", "filas": 4, "columnas": COLS([{"campo": "deriva", "etiqueta": "Amenaza que puede generar", "ancho": 240}])},
              {"id": "oportunidades", "titulo": "Oportunidades (externas)", "filas": 4, "columnas": COLS([])},
              {"id": "amenazas", "titulo": "Amenazas (externas)", "filas": 4, "columnas": COLS([{"campo": "compensa", "etiqueta": "Fortaleza que la compensa", "ancho": 240}])}]
    NOTA = ("PMBOK 6, 11.2.2.3: el FODA amplía la identificación de riesgos; parte de las fortalezas y debilidades, identifica oportunidades que "
            "pueden surgir de las fortalezas y amenazas que resultan de las debilidades, y revisa si las fortalezas compensan amenazas y si las "
            "debilidades impiden oportunidades. PMBOK 7, 4.4.1. Las amenazas y oportunidades derivadas se pasan al registro de riesgos.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        t = d["tablas"]; listas = [[f["factor"] for f in t[k] if f.get("factor")] for k in ("fortalezas", "debilidades", "oportunidades", "amenazas")]
        av = []
        der = [f["deriva"] for f in t["fortalezas"] + t["debilidades"] if f.get("factor") and f.get("deriva")]
        sin = [f["factor"] for f in t["amenazas"] if f.get("factor") and f.get("impacto") == "Alto" and not f.get("compensa")]
        if sin: av.append("Amenazas de peso alto sin fortaleza que las compense: " + ", ".join(sin) + ".")
        reg = " ".join((f.get("riesgo") or "").lower() for f in ((proyecto.formatos.get("RIESGOS") or {}).get("tablas", {}).get("registro", []) if proyecto else []))
        falt = [x for x in der if x.lower()[:25] not in reg]
        if falt: av.append("Derivados que aún no están en el registro de riesgos: " + ", ".join(falt[:6]) + ".")
        cab = {"resumen": f"{len(der)} amenazas u oportunidades derivadas"} if der else {}
        bl = [{"tipo": "grafica", "svg": cuadros_svg(["Fortalezas", "Debilidades", "Oportunidades", "Amenazas"], listas, ["#e3f1e0", "#fdecea", "#e3edf5", "#fff3d6"])}] if any(listas) else []
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av, "bloques": bl}


# ======================= AFINIDAD =======================
@formato
class Afinidad(Formato):
    ID, TITULO = "AFINIDAD", "Diagrama de afinidad"
    CABECERA = [F("tema", "Tema o pregunta de la lluvia de ideas"), F("resumen", "Resumen", calc=True)]
    TABLAS = [{"id": "ideas", "titulo": "Ideas", "filas": 10, "columnas": [
        {"campo": "idea", "etiqueta": "Idea", "ancho": 340}, {"campo": "grupo", "etiqueta": "Grupo (nombre del encabezado)", "ancho": 200}, {"campo": "autor", "etiqueta": "Autor", "ancho": 120}]}]
    NOTA = ("PMBOK 6, 5.2.2.5: el diagrama de afinidad clasifica muchas ideas en grupos para revisarlas y analizarlas; 8.2.2.5 lo usa para organizar "
            "causas posibles. PMBOK 7, 4.6.6.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        grupos = {}; kk = []
        for f in d["tablas"]["ideas"]:
            k = {}
            if f.get("idea"):
                g = (f.get("grupo") or "").strip()
                if not g: k["grupo"] = "falta"
                else: grupos.setdefault(g, []).append(f["idea"])
            kk.append(k)
        av = []
        sueltas = sum(1 for f in d["tablas"]["ideas"] if f.get("idea") and not (f.get("grupo") or "").strip())
        if sueltas: av.append(f"{sueltas} ideas sin grupo.")
        solas = [g for g, l in grupos.items() if len(l) == 1]
        if solas and len(grupos) > 2: av.append("Grupos con una sola idea: " + ", ".join(solas) + "; revisa si caben en otro grupo.")
        bl = []
        if grupos:
            G = list(grupos.items()); w = 760; cw = (w - 10) / min(len(G), 5); filas = math.ceil(len(G) / 5); mx = max(len(l) for _, l in G)
            hh = filas * (40 + 22 * mx) + 10; s = ""
            for k, (g, l) in enumerate(G):
                x, y = 5 + (k % 5) * cw, 5 + (k // 5) * (40 + 22 * mx)
                s += f'<rect x="{x + 3:.1f}" y="{y}" width="{cw - 6:.1f}" height="26" rx="6" fill="#dd5813"/><text x="{x + cw / 2:.1f}" y="{y + 17}" text-anchor="middle" fill="#fff" font-weight="700">{_t(g)[:22]} ({len(l)})</text>'
                for j, it in enumerate(l):
                    s += f'<rect x="{x + 6:.1f}" y="{y + 32 + 22 * j}" width="{cw - 12:.1f}" height="19" rx="4" fill="#fbe8dd"/><text x="{x + 10:.1f}" y="{y + 45 + 22 * j}" fill="#2b2620" font-size="9">{_t(it)[:30]}</text>'
            bl = [{"tipo": "grafica", "svg": _svg(w, hh, s)}]
        n = sum(len(l) for l in grupos.values())
        return {"cab": {"resumen": f"{n} ideas en {len(grupos)} grupos"} if grupos else {}, "calc": {}, "clases": {"ideas": kk}, "avisos": av, "bloques": bl}


# ======================= ENFOQUE DE DESARROLLO =======================
VARIABLES = [
    ("Producto", "Grado de innovación", "Conocido y con experiencia → predictivo; muy innovador o sin experiencia → adaptativo"),
    ("Producto", "Certeza de los requisitos", "Requisitos claros → predictivo; inciertos o cambiantes → adaptativo"),
    ("Producto", "Estabilidad del alcance", "Estable → predictivo; con muchos cambios esperados → adaptativo"),
    ("Producto", "Facilidad para cambiar", "Difícil incorporar cambios → predictivo; fácil → adaptativo"),
    ("Producto", "Opciones de entrega", "Se entrega completo → predictivo; se puede entregar por partes → incremental o adaptativo"),
    ("Producto", "Riesgo", "Alto riesgo que exige planeación previa → predictivo; riesgo que baja construyendo por módulos → adaptativo"),
    ("Producto", "Requisitos de seguridad", "Rigurosos → predictivo"),
    ("Producto", "Regulaciones", "Mucha supervisión regulatoria y documentación → predictivo"),
    ("Proyecto", "Interesados", "Poca participación continua → predictivo; dueño del producto muy involucrado → adaptativo"),
    ("Proyecto", "Restricciones de cronograma", "Hay que entregar algo pronto, aunque no esté terminado → iterativo o adaptativo"),
    ("Proyecto", "Disponibilidad de fondos", "Fondos inciertos → adaptativo o iterativo (producto mínimo viable)"),
    ("Organización", "Estructura", "Muchos niveles y burocracia → predictivo; estructura plana → adaptativo"),
    ("Organización", "Cultura", "Dirigir y medir contra líneas base → predictivo; equipos autogestionados → adaptativo"),
    ("Organización", "Capacidad organizacional", "Sin experiencia ágil → predictivo; con políticas y mentalidad ágil → adaptativo"),
    ("Organización", "Tamaño y ubicación del equipo", "Equipos grandes o virtuales → predictivo; 7 ± 2 en un mismo lugar → adaptativo")]


@formato
class Enfoque(Formato):
    ID, TITULO = "ENFOQUE", "Enfoque de desarrollo y ciclo de vida"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("sugerencia", "Sugerencia según las valoraciones", calc=True),
                F("elegido", "Enfoque elegido", tipo="opcion", opciones=SI("Predictivo", "Iterativo", "Incremental", "Adaptativo (ágil)", "Híbrido")),
                F("justificacion", "Justificación y adaptación (tailoring)", tipo="largo")]
    TABLAS = [{"id": "variables", "titulo": "Variables (1 = favorece lo predictivo · 5 = favorece lo adaptativo)", "filas": len(VARIABLES), "fijas": True, "columnas": [
        {"campo": "categoria", "etiqueta": "Categoría", "lectura": True, "ancho": 100}, {"campo": "variable", "etiqueta": "Variable", "lectura": True, "ancho": 190},
        {"campo": "guia", "etiqueta": "Guía (PMBOK 7, 2.3.4)", "lectura": True, "ancho": 380},
        {"campo": "valor", "etiqueta": "Valoración", "tipo": "opcion", "opciones": SI("1", "2", "3", "4", "5"), "ancho": 90}, {"campo": "comentario", "etiqueta": "Comentario", "ancho": 200}]}]
    NOTA = ("PMBOK 7, 2.3.4: variables del producto, del proyecto y de la organización que influyen en el enfoque; 2.3.3 y 3.4 adaptación. PMBOK 6, "
            "1.2.4.1 y X3: ciclo predictivo (alcance, tiempo y costo definidos al inicio), iterativo, incremental, adaptativo (ágil) e híbrido (lo "
            "conocido de forma predictiva y lo que evoluciona de forma adaptativa). La escala de 1 a 5 y los cortes de la sugerencia (≤ 2.3 "
            "predictivo, ≥ 3.7 adaptativo, en medio híbrido) son [criterio de uso, no de la base]. DMAIC es un ciclo por fases; Kaizen y Scrum "
            "aportan ciclos cortos dentro de Mejorar.")

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["variables"] = [{"categoria": c, "variable": n, "guia": g} for c, n, g in VARIABLES]; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = d["tablas"]["variables"]; vals = [(f.get("categoria"), f.get("variable"), N(f.get("valor"))) for f in filas]
        dados = [v for *_, v in vals if v is not None]; av, cab = [], {}
        if dados:
            m = sum(dados) / len(dados)
            sug = "Predictivo" if m <= 2.3 else "Adaptativo (ágil)" if m >= 3.7 else "Híbrido"
            por = {}
            for c, _, v in vals:
                if v is not None: por.setdefault(c, []).append(v)
            cab["sugerencia"] = f"{sug} (promedio {m:.2f}; " + ", ".join(f"{c} {sum(l) / len(l):.1f}" for c, l in por.items()) + ")"
            el = d["cabecera"].get("elegido")
            if el and len(dados) >= 8 and ((sug == "Predictivo" and el.startswith("Adaptativo")) or (sug.startswith("Adaptativo") and el == "Predictivo")):
                av.append("El enfoque elegido es opuesto a la sugerencia: deja la justificación.")
            if len(dados) < len(filas): av.append(f"Faltan {len(filas) - len(dados)} variables por valorar.")
            seg = [n for c, n, v in vals if v is not None and n in ("Requisitos de seguridad", "Regulaciones") and v <= 2]
            if seg and sug != "Predictivo": av.append("Seguridad o regulación piden planeación previa: considera un enfoque híbrido con esas partes predictivas.")
        w, lh, iz = 720, 20, 200; h = 30 + lh * len(vals); s = f'<text x="{iz}" y="12" fill="#6f675b">Predictivo</text><text x="{w - 10}" y="12" text-anchor="end" fill="#6f675b">Adaptativo</text>'
        for k, (c, n, v) in enumerate(vals):
            y = 20 + k * lh; s += f'<text x="4" y="{y + 12}" fill="#2b2620">{_t(n)[:30]}</text><line x1="{iz}" x2="{w - 10}" y1="{y + 8}" y2="{y + 8}" stroke="#e2dcd0"/>'
            if v is not None: s += f'<circle cx="{iz + (w - 10 - iz) * (v - 1) / 4:.1f}" cy="{y + 8}" r="6" fill="#dd5813"/>'
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av, "bloques": [{"tipo": "grafica", "svg": _svg(w, h, s)}] if dados else []}
