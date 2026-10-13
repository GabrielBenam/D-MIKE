"""Formatos de v0.14: KANO y QFD (PL10, DEF-KANO, DEF-QFD), CTQ-TREE (PL15, DEF-CTQTREE), VSM, TIEMPOS y BALANCE (PL03),
TPM (LEAN-TPM), POKAYOKE (11_GUIA_POKAYOKE), CINCO-S (LEAN-5S), GEMBA (32_BB), SCRUM (PL17), LSW (PL19) y TRABAJO-EST
(hoja de dinámica 3_14_c de PL07). Lo que no viene de la base se marca en la NOTA de cada formato."""
from collections import Counter
from .formatos import Formato, formato, fila_vacia
from .base import num
from ..nucleo.hoja import a_numero, a_fecha

SI = lambda *v: [["", ""]] + [[x, x] for x in v]
F = lambda c, t=None, **k: {"campo": c, "etiqueta": t or c.replace("_", " ").capitalize(), **k}
N = lambda t: a_numero(t) if t and str(t).strip() else None
FUENTE = 'font-family="Montserrat,Segoe UI,sans-serif" font-size="10"'


def _svg(w, h, cuerpo): return f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{round(w * 1.15)}px" xmlns="http://www.w3.org/2000/svg" {FUENTE}>{cuerpo}</svg>'
def _t(s): return str(s).replace("&", "y").replace("<", "").replace(">", "")[:40]


def barras_svg(etiquetas, valores, linea=None, nombre_linea="", colores=None):
    w, h, izq, ab = 720, 220, 46, 40; n = max(len(valores), 1); mx = max([v for v in valores if v] + [linea or 0, 1e-9]) * 1.12
    bw = (w - izq - 10) / n; s = ""
    for k in range(5):
        y = h - ab - (h - ab - 10) * k / 4; s += f'<line x1="{izq}" x2="{w - 6}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e9e4da"/><text x="{izq - 4}" y="{y + 3:.1f}" text-anchor="end" fill="#6f675b">{num(mx * k / 4, 3)}</text>'
    for i, (e, v) in enumerate(zip(etiquetas, valores)):
        if v is None: continue
        bh = (h - ab - 10) * v / mx; x = izq + i * bw + bw * .15; col = (colores or {}).get(i, "#dd5813")
        s += f'<rect x="{x:.1f}" y="{h - ab - bh:.1f}" width="{bw * .7:.1f}" height="{bh:.1f}" rx="2" fill="{col}"/><text x="{x + bw * .35:.1f}" y="{h - ab + 13}" text-anchor="middle" fill="#2b2620">{_t(e)[:12]}</text>'
    if linea:
        y = h - ab - (h - ab - 10) * linea / mx
        s += f'<line x1="{izq}" x2="{w - 6}" y1="{y:.1f}" y2="{y:.1f}" stroke="#b3261e" stroke-width="1.5" stroke-dasharray="5 4"/><text x="{w - 8}" y="{y - 4:.1f}" text-anchor="end" fill="#b3261e">{nombre_linea} {num(linea, 3)}</text>'
    return _svg(w, h, s)


# ---------------- KANO ----------------
RESP = SI("Satisfecho", "Neutral", "No le importa", "Insatisfecho")
REGLAS_KANO = {("Neutral", "Insatisfecho"): "Básico", ("Satisfecho", "Insatisfecho"): "Desempeño", ("Satisfecho", "No le importa"): "Deleite"}


@formato
class Kano(Formato):
    ID, TITULO = "KANO", "Modelo de Kano"
    CABECERA = [F("producto", "Producto o servicio"), F("cliente", "Cliente o segmento"), F("resumen", "Clasificación", calc=True)]
    TABLAS = [{"id": "atributos", "titulo": "Requisitos potenciales del cliente", "filas": 8, "columnas": [
        {"campo": "requisito", "etiqueta": "Requisito o atributo", "ancho": 300},
        {"campo": "respuesta_con", "etiqueta": "Si lo TUVIERA, el cliente estaría…", "tipo": "opcion", "opciones": RESP, "ancho": 190},
        {"campo": "respuesta_sin", "etiqueta": "Si NO lo tuviera, estaría…", "tipo": "opcion", "opciones": RESP, "ancho": 190},
        {"campo": "clasificacion", "etiqueta": "Clasificación", "calc": True, "ancho": 120}]}]
    NOTA = ("PL10 KANO-MODEL y 13_GB DEF-KANO: básico = neutral si lo tiene e insatisfecho si no; desempeño = satisfecho e insatisfecho; deleite = satisfecho "
            "y no le importa. Otra combinación se marca para revisar la respuesta antes de clasificar.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        cc, kk, av, cnt = [], [], [], Counter()
        for i, f in enumerate(d["tablas"]["atributos"]):
            c, k = {}, {}
            if f.get("respuesta_con") and f.get("respuesta_sin"):
                cl = REGLAS_KANO.get((f["respuesta_con"], f["respuesta_sin"]))
                if cl: c["clasificacion"] = cl; cnt[cl] += 1; k["clasificacion"] = {"Básico": "advertencia", "Desempeño": "ok", "Deleite": "ok"}[cl]
                else: c["clasificacion"] = "Revisar"; k["clasificacion"] = "no"; av.append(f"Fila {i + 1}: la combinación «{f['respuesta_con']}» y «{f['respuesta_sin']}» no corresponde a ningún tipo; revisa la respuesta.")
            elif f.get("requisito"): k["respuesta_con" if not f.get("respuesta_con") else "respuesta_sin"] = "falta"
            cc.append(c); kk.append(k)
        cab = {"resumen": " · ".join(f"{t} {cnt[t]}" for t in ("Básico", "Desempeño", "Deleite") if cnt[t])} if cnt else {}
        if cnt["Básico"]: av.append("Los básicos no dan satisfacción extra, pero su falta genera insatisfacción: asegúralos primero.")
        return {"cab": cab, "calc": {"atributos": cc}, "clases": {"atributos": kk}, "avisos": av}


# ---------------- QFD ----------------
REL = [["", ""], ["9", "9 fuerte"], ["3", "3 media"], ["1", "1 débil"]]


@formato
class Qfd(Formato):
    ID, TITULO = "QFD", "QFD (casa de la calidad, primera matriz)"
    CABECERA = [F("producto_servicio", "Producto o servicio"), F("linea_valor", "Línea o flujo de valor")] + \
               [F(f"tecnico_{k}", f"Requisito técnico {k} (cómo)") for k in range(1, 6)] + [F("importancia", "Importancia absoluta (relativa) por requisito técnico", calc=True)]
    TABLAS = [{"id": "requisitos_cliente", "titulo": "Requisitos del cliente (qués) y su relación con los técnicos", "filas": 6, "columnas": [
                  {"campo": "requisito", "etiqueta": "Requisito del cliente", "ancho": 220}, {"campo": "importancia", "etiqueta": "Importancia (1 a 5)", "tipo": "numero", "ancho": 90}] +
                  [{"campo": f"rel_{k}", "etiqueta": f"T{k}", "tipo": "opcion", "opciones": REL, "ancho": 74} for k in range(1, 6)] +
                  [{"campo": "quejas", "etiqueta": "Quejas", "tipo": "numero", "ancho": 70}, {"campo": "empresa", "etiqueta": "Nuestra empresa (1 a 5)", "tipo": "numero", "ancho": 90}] +
                  [{"campo": f"comp_{k}", "etiqueta": f"Competidor {k}", "tipo": "numero", "ancho": 84} for k in range(1, 5)]},
              {"id": "eval_tecnica", "titulo": "Evaluación técnica (por requisito técnico)", "filas": 5, "fijas": True, "columnas": [
                  {"campo": "quien", "etiqueta": "Quién", "ancho": 160}] + [{"campo": f"t{k}", "etiqueta": f"T{k}", "tipo": "numero", "ancho": 80} for k in range(1, 6)]},
              {"id": "valores_objetivo", "titulo": "Valores objetivo", "filas": 1, "fijas": True, "columnas": [{"campo": f"t{k}", "etiqueta": f"T{k}", "ancho": 120} for k in range(1, 6)]}]
    NOTA = ("PL10 QFD: hasta 5 requisitos técnicos y 6 de cliente; la importancia absoluta de cada requisito técnico es la suma de importancia × relación (9, 3, 1). "
            "Revisión de la base: un requisito de cliente sin ninguna relación indica que ningún cómo cubre ese qué. El techo de correlaciones se marca aparte.")

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["eval_tecnica"] = [{"quien": q} for q in ("Nuestra empresa", "Competidor 1", "Competidor 2", "Competidor 3", "Competidor 4")]; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = d["tablas"]["requisitos_cliente"]; imp = [0.0] * 5; av, kk = [], []
        for i, f in enumerate(filas):
            k = {}; w = N(f.get("importancia"))
            if f.get("importancia") and (w is None or not 1 <= w <= 5): k["importancia"] = "mal"; av.append(f"Fila {i + 1}: la importancia va de 1 a 5.")
            rels = [N(f.get(f"rel_{t}")) for t in range(1, 6)]
            if f.get("requisito") and not any(rels): av.append(f"«{f['requisito']}» no tiene relación con ningún requisito técnico: ningún cómo cubre ese qué."); k["requisito"] = "advertencia"
            if w:
                for t in range(5): imp[t] += w * (rels[t] or 0)
            kk.append(k)
        tot = sum(imp); cab = {}
        if tot:
            cab["importancia"] = " · ".join(f"{d['cabecera'].get(f'tecnico_{t + 1}') or f'T{t + 1}'}: {num(imp[t])} ({100 * imp[t] / tot:.0f}%)" for t in range(5) if d["cabecera"].get(f"tecnico_{t + 1}") or imp[t])
        nom = [d["cabecera"].get(f"tecnico_{t + 1}") or f"T{t + 1}" for t in range(5)]
        bl = [{"tipo": "grafica", "svg": barras_svg(nom, imp)}] if tot else []
        return {"cab": cab, "calc": {}, "clases": {"requisitos_cliente": kk}, "avisos": av, "bloques": bl}


# ---------------- CTQ ----------------
@formato
class Ctq(Formato):
    ID, TITULO = "CTQ-TREE", "Árbol CTQ (crítico para la calidad)"
    CABECERA = [F("necesidad", "Necesidad crítica del cliente (en términos genéricos)")]
    TABLAS = [{"id": "ramas", "titulo": "Impulsores de calidad y requisitos de desempeño medibles", "filas": 8, "columnas": [
        {"campo": "impulsor", "etiqueta": "Impulsor (driver)", "ancho": 220}, {"campo": "requisito", "etiqueta": "Requisito de desempeño (medible)", "ancho": 300},
        {"campo": "indicador", "etiqueta": "Indicador", "ancho": 140}, {"campo": "meta", "etiqueta": "Meta o especificación", "ancho": 140}]}]
    NOTA = ("13_GB DEF-CTQTREE y PL15: necesidad → impulsores de calidad → requisitos de desempeño medibles (uno o varios por impulsor). "
            "Repite el impulsor en cada fila que le corresponda; el árbol se dibuja abajo.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = [f for f in d["tablas"]["ramas"] if not fila_vacia(f)]; av, kk = [], []
        for i, f in enumerate(d["tablas"]["ramas"]):
            k = {}
            if f.get("requisito") and not any(ch.isdigit() for ch in f["requisito"] + (f.get("meta") or "")): k["requisito"] = "advertencia"
            if f.get("impulsor") and not f.get("requisito"): k["requisito"] = "falta"
            kk.append(k)
        if any(k.get("requisito") == "advertencia" for k in kk): av.append("Hay requisitos sin número: un requisito de desempeño debe ser medible (por ejemplo, «espera menor a 5 minutos»).")
        bl = []
        if filas and d["cabecera"].get("necesidad"):
            imp = list(dict.fromkeys(f.get("impulsor") or "(sin impulsor)" for f in filas)); filas_s = sum(max(1, sum(1 for f in filas if (f.get("impulsor") or "(sin impulsor)") == x)) for x in imp)
            h = 30 + 26 * filas_s; s = f'<rect x="6" y="{h / 2 - 22:.0f}" width="190" height="44" rx="8" fill="#dd5813"/><text x="101" y="{h / 2 + 4:.0f}" text-anchor="middle" fill="#fff" font-weight="700">{_t(d["cabecera"]["necesidad"])[:30]}</text>'
            y = 18
            for x in imp:
                reqs = [f for f in filas if (f.get("impulsor") or "(sin impulsor)") == x]; yc = y + 26 * (len(reqs) - 1) / 2
                s += f'<path d="M196 {h / 2:.0f}C230 {h / 2:.0f} 230 {yc + 4:.0f} 262 {yc + 4:.0f}" fill="none" stroke="#a79f92"/><rect x="262" y="{yc - 10:.0f}" width="200" height="28" rx="6" fill="#fbe8dd" stroke="#dd5813"/><text x="272" y="{yc + 8:.0f}" fill="#2b2620">{_t(x)[:30]}</text>'
                for r in reqs:
                    s += f'<path d="M462 {yc + 4:.0f}C480 {yc + 4:.0f} 480 {y + 4:.0f} 500 {y + 4:.0f}" fill="none" stroke="#a79f92"/><text x="506" y="{y + 8}" fill="#2b2620">{_t(r.get("requisito") or "—")[:34]}{(" · " + _t(r["meta"])[:14]) if r.get("meta") else ""}</text>'
                    y += 26
            bl = [{"tipo": "grafica", "svg": _svg(760, h, s)}]
        return {"cab": {}, "calc": {}, "clases": {"ramas": kk}, "avisos": av, "bloques": bl}


# ---------------- VSM (familias y resultados) ----------------
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
RES_VSM = ["Área utilizada", "Número de operadores", "Distancia recorrida", "Tiempo de puerta a puerta (días)", "Inventario en material (días)", "Inventario en proceso (días)", "Inventario terminado (días)"]


@formato
class Vsm(Formato):
    ID, TITULO = "VSM", "VSM: familias de productos y resultados"
    CABECERA = [F(f"proceso_{k}", f"Proceso {k}") for k in range(1, 9)] + [F("familias", "Familias (misma ruta de procesos)", calc=True), F("vueltas", "Vueltas de inventario antes / después", calc=True)]
    TABLAS = [{"id": "modelos", "titulo": "Matriz de productos contra procesos: tiempo de ciclo o «x» si no pasa por el proceso", "filas": 7, "columnas": [
                  {"campo": "modelo", "etiqueta": "Modelo", "ancho": 100}, {"campo": "descripcion", "etiqueta": "Descripción", "ancho": 150}] +
                  [{"campo": f"tc_proceso_{k}", "etiqueta": f"P{k}", "ancho": 56} for k in range(1, 9)] +
                  [{"campo": "total_tc", "etiqueta": "Total TC", "calc": True, "ancho": 76}, {"campo": "familia", "etiqueta": "Familia", "calc": True, "ancho": 66}] +
                  [{"campo": f"vol_{m}", "etiqueta": m.capitalize(), "tipo": "numero", "ancho": 62} for m in MESES] + [{"campo": "vol_total", "etiqueta": "Volumen anual", "calc": True, "ancho": 90}]},
              {"id": "resultados", "titulo": "Resultados antes y después", "filas": 7, "fijas": True, "columnas": [
                  {"campo": "indicador", "etiqueta": "Indicador", "ancho": 240}, {"campo": "antes", "etiqueta": "Antes", "tipo": "numero", "ancho": 100},
                  {"campo": "despues", "etiqueta": "Después", "tipo": "numero", "ancho": 100}, {"campo": "ahorro", "etiqueta": "Ahorro", "calc": True, "ancho": 130}]}]
    NOTA = ("PL03 VSM-FAMILIAS y VSM-RESULTADOS: total de tiempo de ciclo por modelo, volumen anual y, como ayuda (no en la plantilla), la familia por ruta común de procesos. "
            "Resultados: ahorro = antes - después; vueltas de inventario = 264 días al año / días de inventario total, con el 264 fijo como en la plantilla (FORM-RESULTADOS).")

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["resultados"] = [{"indicador": x} for x in RES_VSM]; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        cc, kk, av, rutas = [], [], [], {}
        for f in d["tablas"]["modelos"]:
            c, k = {}, {}
            if f.get("modelo"):
                tcs = [f.get(f"tc_proceso_{j}") or "" for j in range(1, 9)]
                for j, t in enumerate(tcs, 1):
                    if t and t.lower() != "x" and N(t) is None: k[f"tc_proceso_{j}"] = "mal"
                c["total_tc"] = num(sum(N(t) or 0 for t in tcs if t.lower() != "x"), 3)
                ruta = tuple(bool(t) and t.lower() != "x" for t in tcs); rutas.setdefault(ruta, []).append(f["modelo"]); c["familia"] = chr(64 + list(rutas).index(ruta) + 1)
                vols = [N(f.get(f"vol_{m}")) for m in MESES]; c["vol_total"] = num(sum(v or 0 for v in vols)) if any(vols) else ""
            cc.append(c); kk.append(k)
        cab = {"familias": " · ".join(f"{chr(65 + i)}: {', '.join(m)}" for i, m in enumerate(rutas.values()))} if rutas else {}
        rc, rk = [], []; inv = {"antes": 0.0, "despues": 0.0}
        for i, f in enumerate(d["tablas"]["resultados"]):
            a, b = N(f.get("antes")), N(f.get("despues")); c = {}
            if a is not None and b is not None: c["ahorro"] = f"{num(a - b)}" + (f" ({100 * (a - b) / a:.0f}%)" if a else "")
            if i >= 4:
                inv["antes"] += a or 0; inv["despues"] += b or 0
            rc.append(c); rk.append({})
        if inv["antes"] and inv["despues"]: cab["vueltas"] = f"{num(264 / inv['antes'], 3)} / {num(264 / inv['despues'], 3)}"
        return {"cab": cab, "calc": {"modelos": cc, "resultados": rc}, "clases": {"modelos": kk, "resultados": rk}, "avisos": av}


# ---------------- TIEMPOS (VSM-TIEMPOS) ----------------
def repetido_bajo(vals):
    """Valor más bajo que se repite (lo que pide el título de la plantilla; ver conflicto C12 de PL03)."""
    c = Counter(round(v, 6) for v in vals); rep = [v for v, k in c.items() if k >= 2]
    return min(rep) if rep else None


@formato
class Tiempos(Formato):
    ID, TITULO = "TIEMPOS", "Hoja de medición de tiempos"
    CABECERA = [F("proceso", "Proceso"), F("fecha_analisis", "Fecha del análisis"), F("hora_analisis", "Hora"), F("numero_proceso", "Número de proceso"),
                F("observador", "Observador"), F("ciclo", "Tiempo de ciclo (suma de los tiempos elegidos)", calc=True)]
    TABLAS = [{"id": "elementos", "titulo": "Elementos de trabajo y mediciones (segundos)", "filas": 8, "columnas": [
        {"campo": "elemento", "etiqueta": "Elemento de trabajo", "ancho": 200}] + [{"campo": f"m{k}", "etiqueta": str(k), "tipo": "numero", "ancho": 50} for k in range(1, 16)] +
        [{"campo": "repetido", "etiqueta": "Repetido más bajo", "calc": True, "ancho": 90}, {"campo": "moda", "etiqueta": "Moda", "calc": True, "ancho": 70},
         {"campo": "minimo", "etiqueta": "Mínimo", "calc": True, "ancho": 70}]}]
    NOTA = ("PL03 VSM-TIEMPOS: 8 elementos y hasta 15 mediciones. Conflicto C12 de la base: la plantilla titula la columna «tiempo repetido más bajo» pero usa MODA; "
            "aquí se muestran ambos y el mínimo. El tiempo de ciclo suma el repetido más bajo (o el mínimo si ningún valor se repite).")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        cc, kk, av, tot = [], [], [], 0.0
        for i, f in enumerate(d["tablas"]["elementos"]):
            c, k = {}, {}; vals = []
            for j in range(1, 16):
                t = f.get(f"m{j}")
                if t:
                    v = N(t)
                    if v is None: k[f"m{j}"] = "mal"
                    else: vals.append(v)
            if vals:
                rb = repetido_bajo(vals); mo = Counter(vals).most_common(1)[0]; mn = min(vals)
                c["repetido"] = num(rb, 3) if rb is not None else "no se repite"; c["moda"] = num(mo[0], 3) if mo[1] > 1 else "—"; c["minimo"] = num(mn, 3)
                if rb is None: k["repetido"] = "advertencia"; av.append(f"Elemento {i + 1}: ningún tiempo se repite; se usó el mínimo. Toma más mediciones.")
                tot += rb if rb is not None else mn
                if len(vals) < 10: av.append(f"Elemento {i + 1}: {len(vals)} mediciones; la hoja prevé hasta 15.")
            cc.append(c); kk.append(k)
        return {"cab": {"ciclo": f"{num(tot, 3)} s"} if tot else {}, "calc": {"elementos": cc}, "clases": {"elementos": kk}, "avisos": av}


# ---------------- BALANCE (VSM-BALANCE) ----------------
@formato
class Balance(Formato):
    ID, TITULO = "BALANCE", "Balance de operaciones contra el takt"
    CABECERA = [F("t_disponible", "Tiempo disponible por día (s)", tipo="numero"), F("demanda", "Demanda por día (piezas)", tipo="numero"),
                F("takt", "Takt time", calc=True), F("operadores", "Operadores necesarios (Σ tiempos / takt)", calc=True)]
    TABLAS = [{"id": "operaciones", "titulo": "Operaciones", "filas": 8, "columnas": [
        {"campo": "numero", "etiqueta": "N.º", "ancho": 50}, {"campo": "codigo", "etiqueta": "Código", "ancho": 90}, {"campo": "descripcion", "etiqueta": "Descripción", "ancho": 240},
        {"campo": "tiempo", "etiqueta": "Tiempo de ciclo (s)", "tipo": "numero", "ancho": 110}, {"campo": "pct", "etiqueta": "% del takt", "calc": True, "ancho": 90}]}]
    NOTA = "PL03 VSM-BALANCE y FORM-TAKT-CURSO: takt = tiempo disponible / demanda. Las operaciones por encima del takt son el cuello de botella."

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        td, dem = N(d["cabecera"].get("t_disponible")), N(d["cabecera"].get("demanda")); takt = td / dem if td and dem else None
        cc, kk, av, ts, et = [], [], [], [], []
        for f in d["tablas"]["operaciones"]:
            c, k = {}, {}; t = N(f.get("tiempo"))
            if f.get("tiempo") and t is None: k["tiempo"] = "mal"
            if t is not None:
                ts.append(t); et.append(f.get("codigo") or f.get("numero") or f.get("descripcion") or str(len(ts)))
                if takt: c["pct"] = f"{100 * t / takt:.0f}% del takt"; k["pct"] = "no" if t > takt else "advertencia" if t > .9 * takt else "ok"
            cc.append(c); kk.append(k)
        cab = {}
        if takt:
            cab["takt"] = f"{num(takt, 3)} s"
            if ts: cab["operadores"] = num(sum(ts) / takt, 3)
            exc = [e for e, t in zip(et, ts) if t > takt]
            if exc: av.append("Exceden el takt: " + ", ".join(map(str, exc)) + ". Rebalancea o reduce su tiempo.")
        bl = [{"tipo": "grafica", "svg": barras_svg(et, ts, takt, "Takt", {i: "#b3261e" for i, t in enumerate(ts) if takt and t > takt})}] if ts else []
        return {"cab": cab, "calc": {"operaciones": cc}, "clases": {"operaciones": kk}, "avisos": av, "bloques": bl}


# ---------------- TPM ----------------
PILARES = SI("Mantenimiento autónomo", "Mantenimiento planificado", "Mejoras enfocadas", "Mantenimiento de calidad", "Educación y entrenamiento",
             "Gestión temprana de equipos", "Seguridad y medio ambiente", "TPM administrativo")


@formato
class Tpm(Formato):
    ID, TITULO = "TPM", "TPM: registro de fallas y pilares"
    CABECERA = [F("equipo", "Equipo"), F("area", "Área", fijo="cliente_area"), F("periodo", "Periodo"), F("t_operacion", "Tiempo de operación del periodo (h)", tipo="numero"),
                F("mtbf", "MTBF (h)", calc=True), F("mttr", "MTTR (h)", calc=True), F("disp", "Disponibilidad MTBF / (MTBF + MTTR)", calc=True)]
    TABLAS = [{"id": "fallas", "titulo": "Fallas del periodo", "filas": 8, "columnas": [
        {"campo": "fecha", "etiqueta": "Fecha", "ancho": 100}, {"campo": "descripcion", "etiqueta": "Falla", "ancho": 220},
        {"campo": "tipo", "etiqueta": "Tipo", "tipo": "opcion", "opciones": SI("Mecánica", "Eléctrica", "Operación", "Material", "Otra"), "ancho": 110},
        {"campo": "reparacion", "etiqueta": "Tiempo de reparación (h)", "tipo": "numero", "ancho": 120}, {"campo": "causa", "etiqueta": "Causa raíz", "ancho": 200},
        {"campo": "accion", "etiqueta": "Acción", "ancho": 200}, {"campo": "pilar", "etiqueta": "Pilar TPM", "tipo": "opcion", "opciones": PILARES, "ancho": 190}]}]
    NOTA = ("04 LEAN-TPM: MTBF (estabilidad) y MTTR (capacidad de respuesta). MTBF = tiempo de operación / número de fallas; MTTR = tiempo total de reparación / número "
            "de fallas. No respaldados por la base: la disponibilidad MTBF/(MTBF+MTTR) y los 8 pilares del modelo JIPM (complemento [COMP] de la base). Prerrequisito: 5S.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        fl = [f for f in d["tablas"]["fallas"] if not fila_vacia(f)]; kk, av = [], []
        rep = []
        for f in d["tablas"]["fallas"]:
            k = {}; r = N(f.get("reparacion"))
            if f.get("reparacion") and r is None: k["reparacion"] = "mal"
            if r is not None: rep.append(r)
            if f.get("descripcion") and not f.get("causa"): k["causa"] = "falta"
            kk.append(k)
        to = N(d["cabecera"].get("t_operacion")); cab = {}
        if fl and to:
            mtbf = to / len(fl); cab["mtbf"] = num(mtbf, 3)
            if rep: mttr = sum(rep) / len(fl); cab["mttr"] = num(mttr, 3); cab["disp"] = (f"{100 * mtbf / (mtbf + mttr):.1f}% = MTBF / (MTBF + MTTR) · {len(fl)} fallas" if (mtbf + mttr) else "no definido (MTBF + MTTR = 0)")
        tipos = Counter(f.get("tipo") for f in fl if f.get("tipo"))
        if tipos: av.append("Fallas por tipo: " + ", ".join(f"{t} {n}" for t, n in tipos.most_common()) + ".")
        return {"cab": cab, "calc": {}, "clases": {"fallas": kk}, "avisos": av}


# ---------------- POKA YOKE ----------------
@formato
class PokaYoke(Formato):
    ID, TITULO = "POKAYOKE", "Poka Yoke (a prueba de errores)"
    CABECERA = [F("area", "Área", fijo="cliente_area"), F("responsable", "Responsable", fijo="responsable"), F("resumen", "Resumen", calc=True)]
    TABLAS = [{"id": "casos", "titulo": "Errores y dispositivos", "filas": 6, "columnas": [
        {"campo": "error", "etiqueta": "Error o defecto", "ancho": 200}, {"campo": "proceso", "etiqueta": "Proceso u operación", "ancho": 150},
        {"campo": "tipo", "etiqueta": "Tipo", "tipo": "opcion", "opciones": SI("Físico", "Secuencial"), "ancho": 100},
        {"campo": "fase", "etiqueta": "Fase", "tipo": "opcion", "opciones": SI("Proactiva", "Reactiva"), "ancho": 100},
        {"campo": "protege", "etiqueta": "Protege", "tipo": "opcion", "opciones": SI("Producto", "Proceso", "Ambos"), "ancho": 100},
        {"campo": "dispositivo", "etiqueta": "Dispositivo o mecanismo", "ancho": 220},
        {"campo": "estado", "etiqueta": "Estado", "tipo": "opcion", "opciones": SI("Idea", "En prueba", "Implantado"), "ancho": 100}]}]
    NOTA = ("11_GUIA_POKAYOKE (POKA-CLAVES): físico = plantilla, guía o sensor; secuencial = obliga un orden; proactiva = evita el error; reactiva = lo detecta y detiene o "
            "alerta antes de que pase al siguiente proceso. Consulta los 6 casos de la guía del curso para elegir dispositivo.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        fl = [f for f in d["tablas"]["casos"] if f.get("error")]; av, kk = [], []
        for f in d["tablas"]["casos"]:
            k = {}
            if f.get("error") and not f.get("dispositivo"): k["dispositivo"] = "falta"
            kk.append(k)
        re = sum(1 for f in fl if f.get("fase") == "Reactiva")
        if re: av.append(f"{re} dispositivos reactivos: confirma que detienen o alertan antes de que el defecto pase al siguiente proceso; si se puede, busca uno proactivo.")
        cab = {"resumen": f"{len(fl)} errores · proactivos {sum(1 for f in fl if f.get('fase') == 'Proactiva')} · reactivos {re} · implantados {sum(1 for f in fl if f.get('estado') == 'Implantado')}"} if fl else {}
        return {"cab": cab, "calc": {}, "clases": {"casos": kk}, "avisos": av}


# ---------------- 5S ----------------
S5 = [("1S Clasificar (Seiri)", "Solo está lo necesario; lo innecesario tiene tarjeta roja"), ("2S Ordenar (Seiton)", "Cada cosa tiene un lugar definido y rotulado"),
      ("3S Limpiar (Seiso)", "Limpieza como inspección; se detectan anomalías"), ("4S Estandarizar (Seiketsu)", "Hay estándares visuales para mantener 1S a 3S"),
      ("5S Disciplina (Shitsuke)", "Se audita y se sostiene en el tiempo")]


@formato
class CincoS(Formato):
    ID, TITULO = "CINCO-S", "Auditoría 5S"
    CABECERA = [F("area", "Área", fijo="cliente_area"), F("auditor", "Auditor"), F("fecha", "Fecha"), F("total", "Resultado", calc=True)]
    TABLAS = [{"id": "s", "titulo": "Calificación por S (0 = no existe, 4 = excelente)", "filas": 5, "fijas": True, "columnas": [
        {"campo": "s", "etiqueta": "S", "ancho": 190}, {"campo": "criterio", "etiqueta": "Qué se revisa", "ancho": 300},
        {"campo": "calif", "etiqueta": "Calificación", "tipo": "opcion", "opciones": [["", ""]] + [[str(k), str(k)] for k in range(5)], "ancho": 100},
        {"campo": "hallazgos", "etiqueta": "Hallazgos", "ancho": 220}, {"campo": "accion", "etiqueta": "Acción", "ancho": 200}]}]
    NOTA = ("04 LEAN-5S: clasificar, ordenar, limpiar, estandarizar y disciplina; es prerrequisito de SMED (mandatorio) y de TPM autónomo. "
            "No respaldados por la base: la escala de 0 a 4 y los criterios de revisión (práctica habitual [COMP]).")

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["s"] = [{"s": s, "criterio": c} for s, c in S5]; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        cal = [N(f.get("calif")) for f in d["tablas"]["s"]]; av = []; cab = {}
        kk = [{"calif": "" if c is None else "ok" if c >= 3 else "advertencia" if c >= 2 else "no"} for c in cal]
        if any(c is not None for c in cal):
            tot = sum(c or 0 for c in cal); cab["total"] = f"{num(tot)} de 20 ({100 * tot / 20:.0f}%)"
            if all(c is not None for c in cal[:3]) and min(cal[:3]) >= 3 and any(c is not None and c < 3 for c in cal[3:]): av.append("Error común de la base: llegar a 3S y no sostener 4S y 5S.")
            for f, c in zip(d["tablas"]["s"], cal):
                if c is not None and c < 2 and not f.get("accion"): av.append(f"{f['s']}: calificación baja sin acción.")
        return {"cab": cab, "calc": {}, "clases": {"s": kk}, "avisos": av}


# ---------------- GEMBA ----------------
MUDAS8 = SI("Ninguno", "Sobreproducción", "Retrabajo", "Transporte", "Sobreprocesamiento", "Inventario", "Espera", "Movimientos", "Defectos")


@formato
class Gemba(Formato):
    ID, TITULO = "GEMBA", "Caminata Gemba"
    CABECERA = [F("tema", "Tema a observar (ir con un tema específico)"), F("proceso", "Proceso"), F("fecha", "Fecha"), F("participantes", "Participantes"),
                F("ruta", "Ruta"), F("resumen", "Resumen", calc=True)]
    TABLAS = [{"id": "obs", "titulo": "Observaciones", "filas": 8, "columnas": [
        {"campo": "lugar", "etiqueta": "Lugar", "ancho": 110}, {"campo": "observacion", "etiqueta": "Qué se observó", "ancho": 240},
        {"campo": "condicion", "etiqueta": "Normal o anormal", "tipo": "opcion", "opciones": SI("Normal", "Anormal"), "ancho": 110},
        {"campo": "desperdicio", "etiqueta": "Desperdicio", "tipo": "opcion", "opciones": MUDAS8, "ancho": 140},
        {"campo": "pregunta", "etiqueta": "Pregunta hecha (por qué, cómo)", "ancho": 200}, {"campo": "accion", "etiqueta": "Acción", "ancho": 180},
        {"campo": "responsable", "etiqueta": "Responsable", "ancho": 110}, {"campo": "fecha", "etiqueta": "Fecha compromiso", "ancho": 110}]}]
    NOTA = ("32_BB GEMBA-ELEMENTOS-OBSERVAR, GEMBA-PREGUNTAS y GEMBA-FORMATO: observar qué es normal y anormal, dónde se crea valor, qué limita la productividad "
            "(desperdicios), preguntar con respeto y validar después (GEMBA-PASO4-VALIDAR).")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        fl = [f for f in d["tablas"]["obs"] if f.get("observacion")]; kk, av = [], []
        for f in d["tablas"]["obs"]:
            k = {}
            if f.get("condicion") == "Anormal": k["condicion"] = "no"
            if f.get("condicion") == "Anormal" and not f.get("accion"): k["accion"] = "falta"
            if f.get("accion") and not (f.get("responsable") and f.get("fecha")): k["responsable"] = "falta"
            kk.append(k)
        if not d["cabecera"].get("tema") and fl: av.append("Define el tema de la caminata: la base pide ir con un tema específico.")
        des = Counter(f.get("desperdicio") for f in fl if f.get("desperdicio") and f.get("desperdicio") != "Ninguno")
        cab = {"resumen": f"{len(fl)} observaciones · {sum(1 for f in fl if f.get('condicion') == 'Anormal')} anormales" + (" · " + ", ".join(f"{t} {n}" for t, n in des.most_common()) if des else "")} if fl else {}
        return {"cab": cab, "calc": {}, "clases": {"obs": kk}, "avisos": av}


# ---------------- SCRUM ----------------
@formato
class Scrum(Formato):
    ID, TITULO = "SCRUM", "Scrum: visión, entregas y sprint"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("vision", "Visión: Para (segmento de clientes)… quiero (necesidad)…", tipo="largo"),
                F("fecha_inicio", "Fecha de inicio"), F("fecha_entrega", "Fecha de entrega"), F("dias", "Días disponibles", calc=True),
                F("dueno_producto", "Dueño del producto"), F("scrum_master", "Scrum Master"), F("equipo", "Equipo de desarrollo"),
                F("meta_sprint", "Meta del sprint"), F("horas_disponibles", "Horas disponibles del sprint", tipo="numero"), F("carga", "Carga del sprint", calc=True)]
    TABLAS = [{"id": "historias", "titulo": "Historias de usuario y tareas", "filas": 8, "columnas": [
                  {"campo": "historia", "etiqueta": "Historia o tarea", "ancho": 260}, {"campo": "prioridad", "etiqueta": "Prioridad", "tipo": "opcion", "opciones": SI("Alta", "Media", "Baja"), "ancho": 90},
                  {"campo": "horas", "etiqueta": "Estimación (h)", "tipo": "numero", "ancho": 100}, {"campo": "responsable", "etiqueta": "Responsable", "ancho": 120},
                  {"campo": "estado", "etiqueta": "Estado", "tipo": "opcion", "opciones": SI("Por hacer", "Haciendo", "Hecho"), "ancho": 100}]},
              {"id": "burndown", "titulo": "Burndown: horas restantes al final de cada día", "filas": 10, "columnas": [
                  {"campo": "dia", "etiqueta": "Día", "ancho": 70}, {"campo": "restante", "etiqueta": "Horas restantes", "tipo": "numero", "ancho": 120},
                  {"campo": "ideal", "etiqueta": "Ideal", "calc": True, "ancho": 90}]}]
    NOTA = "PL17 SCRUM-VISION-MAPA, SCRUM-PLAN-ENTREGAS y SCRUM-PLAN-SPRINT; burndown según SCRUM-BURNDOWN de la base (la línea ideal baja en forma pareja hasta cero)."

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c = d["cabecera"]; cab, av = {}, []; a, b = a_fecha(c.get("fecha_inicio") or ""), a_fecha(c.get("fecha_entrega") or "")
        if a and b: cab["dias"] = str((b - a).days + 1) if b >= a else "fin antes del inicio"
        est = sum(N(f.get("horas")) or 0 for f in d["tablas"]["historias"]); hd = N(c.get("horas_disponibles"))
        if est and hd: cab["carga"] = f"{num(est)} h estimadas de {num(hd)} h ({100 * est / hd:.0f}%)"; av += ["El sprint está sobrecargado: las horas estimadas superan las disponibles."] if est > hd else []
        bd = d["tablas"]["burndown"]; dias = [i for i, f in enumerate(bd) if N(f.get("restante")) is not None]; cc = [{} for _ in bd]; bl = []
        if dias:
            ini = N(bd[dias[0]]["restante"]); n = len(bd) - 1
            for i in range(len(bd)): cc[i]["ideal"] = num(ini * (1 - i / n), 2) if n else ""
            vals = [N(f.get("restante")) for f in bd]; w, h, iz = 720, 200, 40; mx = max([v for v in vals if v is not None] + [ini]) * 1.1 or 1
            X = lambda i: iz + i * (w - iz - 10) / max(n, 1); Y = lambda v: h - 26 - (h - 40) * v / mx
            s = f'<line x1="{X(0)}" y1="{Y(ini):.1f}" x2="{X(n)}" y2="{Y(0):.1f}" stroke="#a79f92" stroke-dasharray="5 4"/>'
            pts = [(X(i), Y(v)) for i, v in enumerate(vals) if v is not None]
            s += f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="#dd5813" stroke-width="2.5"/>' + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#dd5813"/>' for x, y in pts)
            s += "".join(f'<text x="{X(i):.1f}" y="{h - 8}" text-anchor="middle" fill="#6f675b">{bd[i].get("dia") or i + 1}</text>' for i in range(len(bd)))
            bl = [{"tipo": "grafica", "svg": _svg(w, h, s)}]
            ult = dias[-1]
            if N(bd[ult]["restante"]) > ini * (1 - ult / n) * 1.1 if n else False: av.append("El avance va por arriba de la línea ideal: revisa impedimentos en la reunión diaria.")
        return {"cab": cab, "calc": {"burndown": cc}, "clases": {}, "avisos": av, "bloques": bl}


# ---------------- LSW (trabajo estándar de líderes) ----------------
HT = [{"campo": "hora", "etiqueta": "Hora", "ancho": 80}, {"campo": "tarea", "etiqueta": "Tarea", "ancho": 340}]


@formato
class Lsw(Formato):
    ID, TITULO = "LSW", "Trabajo estándar de líderes (LSW)"
    CABECERA = [F("nombre", "Nombre"), F("cargo", "Cargo"), F("fecha", "Fecha")]
    TABLAS = ([{"id": "diario", "titulo": "Diario", "filas": 7, "columnas": HT}, {"id": "situaciones", "titulo": "Situaciones, interrupciones y seguimientos", "filas": 7,
               "columnas": [{"campo": "situacion", "etiqueta": "Situación", "ancho": 420}]},
               {"id": "varias_veces_al_dia", "titulo": "Varias veces al día", "filas": 7, "columnas": HT}] +
              [{"id": f"semanal_{d}", "titulo": f"Semanal: {n}", "filas": 3, "columnas": HT} for d, n in (("lun", "lunes"), ("mar", "martes"), ("mie", "miércoles"), ("jue", "jueves"), ("vie", "viernes"))] +
              [{"id": "mensual", "titulo": "Mensual", "filas": 6, "columnas": HT}])
    NOTA = "PL19 LSW-FORMATO-BB y 31_BB (LSW-ACCIONES-DIARIAS): cuatro horizontes en la misma hoja: diario, varias veces al día, semanal (lunes a viernes) y mensual."

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        av, clases = [], {}
        for t in cls.TABLAS:
            if "hora" not in [c["campo"] for c in t["columnas"]]: continue
            kk = []
            for f in d["tablas"][t["id"]]:
                k = {}
                if f.get("tarea") and not f.get("hora"): k["hora"] = "falta"
                kk.append(k)
            clases[t["id"]] = kk
        if not any(f.get("tarea") for f in d["tablas"]["diario"]) and any(any(f.values()) for f in d["tablas"]["mensual"]): av.append("Empieza por lo diario: es lo que sostiene los avances (31_BB LSW-SOSTIENE-AVANCES).")
        return {"cab": {}, "calc": {}, "clases": clases, "avisos": av}


# ---------------- Trabajo estándar (tabla combinada) ----------------
@formato
class TrabajoEst(Formato):
    ID, TITULO = "TRABAJO-EST", "Tabla combinada de operaciones estandarizadas"
    CABECERA = [F("proceso", "Proceso"), F("operacion", "Operación"), F("fecha", "Fecha de preparación"), F("hecho_por", "Hecho por"),
                F("unidades_turno", "Unidades por turno", tipo="numero"), F("takt", "Takt time (s)", tipo="numero"), F("totales", "Totales", calc=True)]
    TABLAS = [{"id": "pasos", "titulo": "Pasos", "filas": 10, "columnas": [
        {"campo": "paso", "etiqueta": "Paso", "ancho": 260}, {"campo": "manual", "etiqueta": "Manual (s)", "tipo": "numero", "ancho": 90},
        {"campo": "auto", "etiqueta": "Automático (s)", "tipo": "numero", "ancho": 100}, {"campo": "caminata", "etiqueta": "Caminata (s)", "tipo": "numero", "ancho": 100},
        {"campo": "acumulado", "etiqueta": "Acumulado del operador (s)", "calc": True, "ancho": 150}]}]
    NOTA = ("PL07 (hojas de dinámica 3_14_c) y 04 LEAN-TRABAJO-EST: tiempo manual (línea continua), automático (punteada) y caminata (ondulada) contra el takt. "
            "El acumulado del operador suma manual y caminata; el automático corre en paralelo con la máquina.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        cc, kk, av, seg = [], [], [], []; t0 = 0.0; tm = ta = tc = 0.0
        for f in d["tablas"]["pasos"]:
            c, k = {}, {}; m, a, w = (N(f.get(x)) for x in ("manual", "auto", "caminata"))
            for x in ("manual", "auto", "caminata"):
                if f.get(x) and N(f[x]) is None: k[x] = "mal"
            if f.get("paso") or any(v is not None for v in (m, a, w)):
                seg.append((f.get("paso") or "", t0, m or 0, a or 0, w or 0)); t0 += (m or 0) + (w or 0); c["acumulado"] = num(t0, 3)
                tm += m or 0; ta += a or 0; tc += w or 0
            cc.append(c); kk.append(k)
        takt = N(d["cabecera"].get("takt")); cab = {"totales": f"manual {num(tm)} · automático {num(ta)} · caminata {num(tc)} · ciclo del operador {num(t0)} s"} if seg else {}
        if takt and t0 > takt: av.append(f"El ciclo del operador ({num(t0)} s) supera el takt ({num(takt)} s).")
        bl = []
        if seg:
            fin = max([t0, takt or 0] + [s[1] + s[2] + s[3] for s in seg]) * 1.08; w, iz = 760, 220; h = 30 + 22 * len(seg); X = lambda t: iz + (w - iz - 10) * t / fin
            s = "".join(f'<text x="{X(fin * k / 8):.1f}" y="12" text-anchor="middle" fill="#6f675b">{num(fin * k / 8, 0)}</text><line x1="{X(fin * k / 8):.1f}" x2="{X(fin * k / 8):.1f}" y1="16" y2="{h}" stroke="#e9e4da"/>' for k in range(9))
            for i, (p, ini, m, a, wk) in enumerate(seg):
                y = 28 + 22 * i; s += f'<text x="4" y="{y + 4}" fill="#2b2620">{_t(p)[:32]}</text>'
                if m: s += f'<line x1="{X(ini):.1f}" x2="{X(ini + m):.1f}" y1="{y}" y2="{y}" stroke="#2b2620" stroke-width="3"/>'
                if a: s += f'<line x1="{X(ini + m):.1f}" x2="{X(ini + m + a):.1f}" y1="{y}" y2="{y}" stroke="#dd5813" stroke-width="2.5" stroke-dasharray="4 3"/>'
                if wk:
                    xs, xe = X(ini + m), X(ini + m + wk); n = max(2, int((xe - xs) / 6))
                    s += '<polyline fill="none" stroke="#2b6f8f" stroke-width="2" points="' + " ".join(f"{xs + (xe - xs) * j / n:.1f},{y + (3 if j % 2 else -3)}" for j in range(n + 1)) + '"/>'
            if takt: s += f'<line x1="{X(takt):.1f}" x2="{X(takt):.1f}" y1="16" y2="{h}" stroke="#b3261e" stroke-width="2"/><text x="{X(takt) + 4:.1f}" y="26" fill="#b3261e">takt</text>'
            bl = [{"tipo": "grafica", "svg": _svg(w, h + 6, s)}]
        return {"cab": cab, "calc": {"pasos": cc}, "clases": {"pasos": kk}, "avisos": av, "bloques": bl}
