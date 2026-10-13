"""Formatos v0.15: DEF-PROBLEMA (03 PS-3PASOS, PS-DEFINICION), HOSHIN (05 EST-HOSHIN, EST-CANVAS, 09 EJ-HOSHIN),
PMAPA (14_GB MED-PMAP, MED-CLASIF), TOC (24_BB), ESPAGUETI y FLUJO y VISUAL (04 LEAN-*), FINANZAS (23_BB, PL18),
MUESTREO (15_GB MUE-*, PL11), DESEMPENO (16_GB DES-*, PL12) y CHECKLIST-FASE (13_GB DEF-CHECKLIST, 16_GB DES-CHECKLIST,
17_GB CORR-CHECKLIST-ANALIZAR). Lo que no viene de la base se marca en la NOTA de cada formato.
Pendientes por falta de fuente: RIESGOS, INTERESADOS y LECCIONES (PMBOK sin procesar) y las listas de Mejorar y Controlar."""
import math
from scipy import stats as st
from .formatos import Formato, formato, fila_vacia
from .formatos4 import SI, F, N, _svg, _t, barras_svg
from .base import num


def pct(x, d=1): return "no definido (denominador 0)" if x is None or x != x else f"{100 * x:.{d}f}%"


# ---------------- Definición del problema ----------------
GENERICAS = ("condiciones", "problemas", "situación", "deficiente", "mala calidad", "falta de", "no hay", "baja moral", "la moral")
PASADO = ("se perdió", "se rompió", "se cayó", "falló", "se dañó", "ocurrió", "hubo", "fue ", "estuvo", "se quedó")


@formato
class DefProblema(Formato):
    ID, TITULO = "DEF-PROBLEMA", "Definición del problema (3 pasos)"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("area", "Área", fijo="cliente_area"),
                F("sujeto", "Sujeto: qué objeto o resultado presenta la desviación"), F("predicado", "Predicado: qué le pasa, en presente"),
                F("enunciado", "Enunciado del problema", calc=True),
                F("donde", "Dónde se observa"), F("cuando", "Cuándo se observa (desde, frecuencia, turno)"),
                F("magnitud", "Magnitud (cuánto, con su unidad)"), F("estandar", "Estándar o valor esperado"),
                F("causa_raiz", "2. Causa raíz encontrada (cuando se tenga)", tipo="largo"),
                F("solucion", "3. Solución y estándar que la sostiene", tipo="largo")]
    TABLAS = []
    NOTA = ("03_SOLUCION_PROBLEMAS PS-3PASOS y PS-DEFINICION: 1. describir el problema de forma objetiva; 2. encontrar la causa raíz; 3. implementar la "
            "solución con acciones permanentes y estándares. El enunciado es sujeto + predicado, en presente, específico y sin confundir síntomas. "
            "Datos mínimos del árbol: síntoma observable, dónde, cuándo y magnitud. Las palabras que disparan los avisos son una ayuda, no una regla de la base.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c, av = d["cabecera"], []
        s, p = (c.get("sujeto") or "").strip(), (c.get("predicado") or "").strip()
        cab = {"enunciado": f"{s[0].upper() + s[1:] if s else ''} {p}".strip() + ("." if s and p and not p.endswith(".") else "")} if s or p else {}
        txt = f" {s} {p} ".lower()
        if s and p:
            if any(w in txt for w in PASADO): av.append("Escribe el predicado en presente («la maleta está perdida», no «se perdió la maleta»).")
            if any(w in txt for w in GENERICAS): av.append("El enunciado parece genérico o un síntoma; hazlo específico y observable («el piso está mojado», no «hay condiciones inseguras»).")
            if any(w in txt for w in ("porque", "debido a", "por culpa", "causado")): av.append("El enunciado incluye una causa; descríbelo sin causas ni soluciones.")
        faltan = [n for k, n in (("donde", "dónde"), ("cuando", "cuándo"), ("magnitud", "magnitud")) if not c.get(k)]
        if s and faltan: av.append("Completa los datos mínimos: " + ", ".join(faltan) + ".")
        if c.get("magnitud") and not any(ch.isdigit() for ch in c["magnitud"]): av.append("La magnitud debe ser un dato medido (con número y unidad).")
        if c.get("solucion") and not c.get("causa_raiz"): av.append("Hay solución sin causa raíz: el paso 2 va antes del 3.")
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av}


# ---------------- Hoshin Kanri ----------------
PERSPECTIVAS = SI("Finanzas", "Operaciones", "Cliente", "Calidad")


def _avance(base, meta, actual):
    if None in (base, meta, actual) or meta == base: return None
    return (actual - base) / (meta - base)


@formato
class Hoshin(Formato):
    ID, TITULO = "HOSHIN", "Hoshin Kanri: matriz de estrategias y proyectos"
    CABECERA = [F("organizacion", "Organización o unidad"), F("periodo", "Periodo"), F("vision", "Visión u objetivo de alto nivel", tipo="largo"),
                F("propuesta_valor", "Canvas: propuesta de valor", tipo="largo"), F("actividades_clave", "Canvas: actividades clave", tipo="largo"),
                F("resumen", "Avance general", calc=True)]
    COLS = [{"campo": "perspectiva", "etiqueta": "Perspectiva", "tipo": "opcion", "opciones": PERSPECTIVAS, "ancho": 110},
            {"campo": "nombre", "etiqueta": "Objetivo / estrategia / proyecto", "ancho": 240}, {"campo": "metrica", "etiqueta": "Métrica", "ancho": 140},
            {"campo": "base", "etiqueta": "Línea base", "tipo": "numero", "ancho": 84}, {"campo": "meta", "etiqueta": "Meta", "tipo": "numero", "ancho": 76},
            {"campo": "actual", "etiqueta": "Actual", "tipo": "numero", "ancho": 76}, {"campo": "avance", "etiqueta": "Avance", "calc": True, "ancho": 70},
            {"campo": "responsable", "etiqueta": "Responsable", "ancho": 120}, {"campo": "vinculo", "etiqueta": "Contribuye a (n.º del nivel superior)", "ancho": 110}]
    TABLAS = [{"id": "objetivos", "titulo": "Nivel 1 · Alta dirección: objetivos", "filas": 4, "columnas": COLS},
              {"id": "estrategias", "titulo": "Nivel 2 · Planeación: estrategias", "filas": 4, "columnas": COLS},
              {"id": "proyectos", "titulo": "Nivel 3 · Táctico: proyectos con métricas", "filas": 6, "columnas": COLS}]
    NOTA = ("05_ESTRATEGIA EST-HOSHIN: jerarquía de tres niveles (dirección, planeación, táctico), matriz organizada por perspectivas (finanzas, "
            "operaciones, cliente, calidad), cada objetivo con métrica, línea base y meta; la propuesta de valor y las actividades clave del Canvas "
            "(EST-CANVAS) se convierten en estrategias y proyectos. Ejemplo del curso (EJ-HOSHIN): ROI de 7% a 12%; estrategia Lean Company; proyecto "
            "reducir inventario de 24M a 16M. Avance = (actual - base) / (meta - base) [GENERAL, no respaldado por la base].")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        calc, clases, av, avs = {}, {}, [], []
        for t in ("objetivos", "estrategias", "proyectos"):
            cc, kk = [], []
            n_sup = sum(1 for f in d["tablas"][{"estrategias": "objetivos", "proyectos": "estrategias"}.get(t, t)] if f.get("nombre"))
            for i, f in enumerate(d["tablas"][t]):
                c, k = {}, {}
                if fila_vacia(f): cc.append(c); kk.append(k); continue
                for x in ("base", "meta", "actual"):
                    if f.get(x) and N(f[x]) is None: k[x] = "mal"
                a = _avance(N(f.get("base")), N(f.get("meta")), N(f.get("actual")))
                if a is not None:
                    c["avance"] = pct(a, 0); avs.append(a); k["avance"] = "ok" if a >= 1 else "advertencia" if a >= .5 else "no"
                if f.get("nombre") and not (f.get("metrica") and f.get("base") and f.get("meta")):
                    av.append(f"{t.capitalize()}, fila {i + 1}: cada elemento necesita métrica, línea base y meta.")
                if t != "objetivos" and f.get("nombre"):
                    v = N(f.get("vinculo"))
                    if v is None: av.append(f"{t.capitalize()}, fila {i + 1}: indica a qué elemento del nivel superior contribuye.")
                    elif not 1 <= v <= max(n_sup, 1): k["vinculo"] = "mal"
                cc.append(c); kk.append(k)
            calc[t], clases[t] = cc, kk
        cab = {"resumen": f"{len(avs)} métricas con avance; promedio {pct(sum(avs) / len(avs), 0)}"} if avs else {}
        if any(f.get("nombre") for f in d["tablas"]["proyectos"]) and not any(f.get("nombre") for f in d["tablas"]["estrategias"]):
            av.append("Hay proyectos sin estrategias: el despliegue va de objetivos a estrategias y de ahí a proyectos.")
        return {"cab": cab, "calc": calc, "clases": clases, "avisos": av}


# ---------------- Mapa de proceso ----------------
CLASIF = SI("Ruido (N)", "Controlable (C)", "Estándar (S)", "Crítica (X)")


def flujo_svg(pasos):
    """Cajas de proceso de izquierda a derecha, en filas de 4, con flechas."""
    if not pasos: return None
    w, bw, bh, gx, gy = 760, 160, 46, 32, 34; por_fila = 4; filas = math.ceil(len(pasos) / por_fila); h = 14 + filas * (bh + gy)
    s = '<defs><marker id="fl" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8z" fill="#6f675b"/></marker></defs>'
    pos = []
    for i, t in enumerate(pasos):
        r, c = divmod(i, por_fila); c = c if r % 2 == 0 else por_fila - 1 - c
        x, y = 10 + c * (bw + gx), 10 + r * (bh + gy); pos.append((x, y))
        s += f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8" fill="#fbe8dd" stroke="#dd5813" stroke-width="1.5"/>'
        s += f'<text x="{x + bw / 2}" y="{y + 19}" text-anchor="middle" fill="#2b2620" font-weight="600">{i + 1}. {_t(t)[:20]}</text>'
        if len(_t(t)) > 20: s += f'<text x="{x + bw / 2}" y="{y + 33}" text-anchor="middle" fill="#2b2620">{_t(t)[20:40]}</text>'
    for (x1, y1), (x2, y2) in zip(pos, pos[1:]):
        if y1 == y2: a, b = (x1 + bw, x2) if x2 > x1 else (x1, x2 + bw); s += f'<line x1="{a}" y1="{y1 + bh / 2}" x2="{b}" y2="{y2 + bh / 2}" stroke="#6f675b" stroke-width="1.5" marker-end="url(#fl)"/>'
        else: s += f'<line x1="{x1 + bw / 2}" y1="{y1 + bh}" x2="{x2 + bw / 2}" y2="{y2}" stroke="#6f675b" stroke-width="1.5" marker-end="url(#fl)"/>'
    return _svg(w, h, s)


@formato
class Pmapa(Formato):
    ID, TITULO = "PMAPA", "Mapa de proceso (entradas X y salidas Y)"
    CABECERA = [F("proceso", "Proceso"), F("nivel", "Nivel de detalle", tipo="opcion", opciones=SI("Organizacional o macro", "Proceso", "Subproceso")),
                F("y_proyecto", "Y del proyecto (salida que se quiere mejorar)"), F("resumen", "Resumen de entradas", calc=True)]
    TABLAS = [{"id": "pasos", "titulo": "Pasos del proceso en orden", "filas": 8, "columnas": [
                  {"campo": "paso", "etiqueta": "Paso u operación", "ancho": 220}, {"campo": "salidas", "etiqueta": "Salidas (Y), separadas por coma", "ancho": 260},
                  {"campo": "valor", "etiqueta": "¿Agrega valor?", "tipo": "opcion", "opciones": SI("Sí", "No"), "ancho": 100}]},
              {"id": "entradas", "titulo": "Entradas (X) por paso", "filas": 12, "columnas": [
                  {"campo": "paso_n", "etiqueta": "N.º de paso", "tipo": "numero", "ancho": 80}, {"campo": "entrada", "etiqueta": "Entrada (X)", "ancho": 240},
                  {"campo": "clase", "etiqueta": "Clasificación", "tipo": "opcion", "opciones": CLASIF, "ancho": 140},
                  {"campo": "comentario", "etiqueta": "Cómo se controla o mide", "ancho": 220}]}]
    NOTA = ("14_GB MED-PMAP y MED-CLASIF: el mapa documenta el flujo con las entradas X y salidas Y de cada operación. Las X se clasifican como "
            "ruido (N), controlable (C), estándar (S) o crítica (X; solo cuando se comprobó estadísticamente su efecto). Error común del curso: no "
            "capturar todas las fuentes de variación; recorre el proceso varias veces, en distintos turnos.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        pasos = [f for f in d["tablas"]["pasos"] if f.get("paso")]; n = len(pasos); av = []
        cc, kk, cnt = [], [], {}
        por_paso = {}
        for i, f in enumerate(d["tablas"]["entradas"]):
            c, k = {}, {}
            if f.get("entrada"):
                p = N(f.get("paso_n"))
                if p is None or not 1 <= p <= max(n, 1) or int(p) != p: k["paso_n"] = "mal"; av.append(f"Entrada «{f['entrada']}»: el número de paso no existe en la tabla de pasos.")
                else: por_paso[int(p)] = por_paso.get(int(p), 0) + 1
                if not f.get("clase"): k["clase"] = "falta"
                else: cnt[f["clase"]] = cnt.get(f["clase"], 0) + 1
            cc.append(c); kk.append(k)
        sin_x = [str(i + 1) for i in range(n) if i + 1 not in por_paso]
        if n and sin_x: av.append("Pasos sin entradas registradas: " + ", ".join(sin_x) + ".")
        sin_y = [str(i + 1) for i, f in enumerate(pasos) if not f.get("salidas")]
        if sin_y: av.append("Pasos sin salida (Y): " + ", ".join(sin_y) + ".")
        if cnt.get("Crítica (X)"): av.append("Marcaste entradas como críticas: confirma que se comprobó estadísticamente su efecto en Y (MED-CLASIF).")
        nva = sum(1 for f in pasos if f.get("valor") == "No")
        if nva: av.append(f"{nva} pasos no agregan valor: candidatos a eliminar, simplificar o hacer en paralelo (MED-PMAP).")
        cab = {"resumen": ", ".join(f"{k.split(' (')[0]}: {v}" for k, v in cnt.items())} if cnt else {}
        g = flujo_svg([f["paso"] for f in pasos])
        return {"cab": cab, "calc": {"entradas": cc}, "clases": {"entradas": kk}, "avisos": av, "bloques": [{"tipo": "grafica", "svg": g}] if g else []}


# ---------------- Teoría de restricciones ----------------
@formato
class Toc(Formato):
    ID, TITULO = "TOC", "Teoría de restricciones (5 pasos)"
    CABECERA = [F("sistema", "Sistema o línea"), F("demanda", "Demanda (unidades por hora)", tipo="numero"),
                F("restriccion", "1. Restricción identificada", calc=True), F("tipo", "Tipo de restricción", calc=True),
                F("explotar", "2. Explotar: cómo se mantiene operando sin pérdidas", tipo="largo"),
                F("subordinar", "3. Subordinar: cómo se sincronizan los demás recursos a su ritmo", tipo="largo"),
                F("elevar", "4. Elevar: acciones o inversiones para aumentar su capacidad", tipo="largo"),
                F("repetir", "5. Repetir: nueva restricción después de la mejora", tipo="largo"),
                F("tambor", "DBR · Tambor (ritmo)"), F("amortiguador", "DBR · Amortiguador (inventario, tiempo o espacio)"), F("cuerda", "DBR · Cuerda (liberación de trabajo)")]
    TABLAS = [{"id": "recursos", "titulo": "Recursos del sistema y su capacidad", "filas": 8, "columnas": [
        {"campo": "recurso", "etiqueta": "Recurso u operación", "ancho": 220}, {"campo": "capacidad", "etiqueta": "Capacidad (unidades por hora)", "tipo": "numero", "ancho": 150},
        {"campo": "uso", "etiqueta": "Carga (demanda / capacidad)", "calc": True, "ancho": 150}]}]
    NOTA = ("24_BB TOC-5-PASOS: identificar, explotar, subordinar, elevar y repetir. TOC-PASO1: si la demanda es mayor que la capacidad, la "
            "restricción es interna; si el proceso tiene más capacidad que demanda, la restricción es el mercado. TOC-DBR: tambor, amortiguador y cuerda. "
            "La restricción se toma como el recurso de menor capacidad.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        dem = N(d["cabecera"].get("demanda")); cc, kk, av, rs = [], [], [], []
        for f in d["tablas"]["recursos"]:
            c, k = {}, {}; cap = N(f.get("capacidad"))
            if f.get("capacidad") and (cap is None or cap <= 0): k["capacidad"] = "mal"
            elif cap:
                rs.append((f.get("recurso") or f"Recurso {len(rs) + 1}", cap))
                if dem: c["uso"] = (pct(dem / cap, 0) + " de la capacidad") if cap else "no definido (capacidad 0)"; k["uso"] = "no" if dem > cap else "advertencia" if dem > .9 * cap else "ok"
            cc.append(c); kk.append(k)
        cab = {}
        if rs:
            nom, cap = min(rs, key=lambda x: x[1]); cab["restriccion"] = f"{nom} ({num(cap, 4)} por hora)"
            if dem:
                cab["tipo"] = "Interna: la demanda supera la capacidad del cuello de botella" if dem > cap else "Externa (mercado): hay más capacidad que demanda"
                if dem <= cap: av.append("La restricción es el mercado: el esfuerzo va a vender o ampliar la demanda, no a subir capacidad (TOC-PASO1).")
            if d["cabecera"].get("elevar") and not d["cabecera"].get("explotar"): av.append("Antes de elevar (invertir), explota la restricción con lo que ya existe (TOC-PASO2).")
        bl = [{"tipo": "grafica", "svg": barras_svg([r for r, _ in rs], [c for _, c in rs], dem, "Demanda", {i: "#b3261e" for i, (_, c) in enumerate(rs) if c == min(x for _, x in rs)})}] if rs else []
        return {"cab": cab, "calc": {"recursos": cc}, "clases": {"recursos": kk}, "avisos": av, "bloques": bl}


# ---------------- Espagueti ----------------
@formato
class Espagueti(Formato):
    ID, TITULO = "ESPAGUETI", "Diagrama de espagueti (recorridos antes y después)"
    CABECERA = [F("area", "Área", fijo="cliente_area"), F("quien", "Qué se sigue (persona o material)"), F("ciclo", "Ciclo observado"),
                F("total_antes", "Distancia por ciclo, antes", calc=True), F("total_despues", "Distancia por ciclo, después", calc=True), F("reduccion", "Reducción", calc=True)]
    COLS = [{"campo": "desde", "etiqueta": "Desde", "ancho": 150}, {"campo": "hasta", "etiqueta": "Hasta", "ancho": 150},
            {"campo": "distancia", "etiqueta": "Distancia (m)", "tipo": "numero", "ancho": 100}, {"campo": "veces", "etiqueta": "Veces por ciclo", "tipo": "numero", "ancho": 100},
            {"campo": "subtotal", "etiqueta": "Metros por ciclo", "calc": True, "ancho": 110},
            {"campo": "retorno", "etiqueta": "¿Cruce o retorno?", "tipo": "opcion", "opciones": SI("Sí", "No"), "ancho": 110}]
    TABLAS = [{"id": "antes", "titulo": "Recorrido actual", "filas": 8, "columnas": COLS}, {"id": "despues", "titulo": "Recorrido con el layout propuesto", "filas": 8, "columnas": COLS}]
    NOTA = ("04_HERRAMIENTAS_LEAN LEAN-ESPAGUETI: se traza sobre el plano el recorrido real de una persona o material durante un ciclo, se mide la "
            "distancia total y se buscan cruces y retornos; ataca la muda de movimiento y transporte. Salida: layout propuesto y distancia antes y después. "
            "El trazo sobre el plano se hace a mano o en el dibujo del área; aquí se registran los tramos.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        calc, clases, tot, ret = {}, {}, {}, {}
        for t in ("antes", "despues"):
            cc, kk, s, r = [], [], 0.0, 0
            for f in d["tablas"][t]:
                c, k = {}, {}; dist, v = N(f.get("distancia")), N(f.get("veces"))
                for x in ("distancia", "veces"):
                    if f.get(x) and (N(f[x]) is None or N(f[x]) < 0): k[x] = "mal"
                if dist is not None and dist >= 0:
                    sub = dist * (v if v is not None else 1); s += sub; c["subtotal"] = num(sub, 4)
                if f.get("retorno") == "Sí": r += 1; k["retorno"] = "advertencia"
                cc.append(c); kk.append(k)
            calc[t], clases[t], tot[t], ret[t] = cc, kk, s, r
        cab, av = {}, []
        if tot["antes"]: cab["total_antes"] = f"{num(tot['antes'], 4)} m"
        if tot["despues"]: cab["total_despues"] = f"{num(tot['despues'], 4)} m"
        if tot["antes"] and tot["despues"]:
            cab["reduccion"] = f"{num(tot['antes'] - tot['despues'], 4)} m ({pct(1 - tot['despues'] / tot['antes'], 0)})"
            if tot["despues"] >= tot["antes"]: av.append("El layout propuesto no reduce la distancia por ciclo.")
        if ret["antes"]: av.append(f"El recorrido actual tiene {ret['antes']} cruces o retornos: son la primera oportunidad.")
        if ret["despues"]: av.append(f"El layout propuesto todavía tiene {ret['despues']} cruces o retornos.")
        bl = [{"tipo": "grafica", "svg": barras_svg(["Antes", "Después"], [tot["antes"], tot["despues"]], colores={1: "#2e7d32"})}] if tot["antes"] or tot["despues"] else []
        return {"cab": cab, "calc": calc, "clases": clases, "avisos": av, "bloques": bl}


# ---------------- Evaluación financiera ----------------
INDICADORES = [("demanda", "Demanda diaria (piezas)"), ("capacidad", "Capacidad diaria (piezas)"), ("precio", "Precio de venta por pieza"),
               ("material", "Costo de materiales por pieza"), ("conversion", "Costo de conversión mensual"), ("dias", "Días de trabajo por mes")]
RESULTADOS = [("vendidas", "Piezas vendidas por día (menor de demanda y capacidad)"), ("ingresos", "Ingresos totales diarios"), ("c_material", "Costo de materiales diario"),
              ("c_conv", "Costo de conversión diario"), ("c_conv_pza", "Costo de conversión por pieza"), ("utilidad", "Utilidades diarias"),
              ("margen", "Utilidad sobre ventas"), ("equilibrio", "Punto de equilibrio diario (piezas)")]


def finanzas(e):
    """Un estado del Ejercicio 7 (23_BB FIN-EJERCICIOS): costos diarios, utilidad y punto de equilibrio (FIN-PUNTO-EQUILIBRIO)."""
    v = min(e["demanda"], e["capacidad"]); ing = v * e["precio"]; cm = v * e["material"]; cd = e["conversion"] / e["dias"]; u = ing - cm - cd
    mv = e["precio"] - e["material"]
    return {"vendidas": v, "ingresos": ing, "c_material": cm, "c_conv": cd, "c_conv_pza": cd / v if v else None, "utilidad": u,
            "margen": u / ing if ing else None, "equilibrio": cd / mv if mv > 0 else None}


@formato
class Finanzas(Formato):
    ID, TITULO = "FINANZAS", "Evaluación financiera (4 estados de mejora)"
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("moneda", "Moneda", defecto="USD"),
                F("ventas_mv", "Margen variable: valor de las ventas", tipo="numero"), F("var_mv", "Margen variable: costos variables", tipo="numero"),
                F("margen_variable", "Margen variable", calc=True), F("mejora", "Mejora de la utilidad diaria, estado 1 a último", calc=True)]
    TABLAS = [{"id": "estados", "titulo": "Indicadores de entrada por estado", "filas": 6, "fijas": True, "columnas": [
                  {"campo": "indicador", "etiqueta": "Indicador", "ancho": 260}] + [{"campo": f"e{k}", "etiqueta": f"Estado {k}", "tipo": "numero", "ancho": 110} for k in range(1, 5)]},
              {"id": "resultados", "titulo": "Resultados (se calculan solos)", "filas": 8, "fijas": True, "columnas": [
                  {"campo": "indicador", "etiqueta": "Resultado", "ancho": 260}] + [{"campo": f"e{k}", "etiqueta": f"Estado {k}", "calc": True, "ancho": 110} for k in range(1, 5)]}]
    NOTA = ("23_BB_EVALUACION_FINANCIERA y PL18 FIN-EJERCICIO7-CALC: ingresos diarios, costo de materiales, costo de conversión diario (mensual / días), "
            "utilidades diarias y utilidad sobre ventas por estado; punto de equilibrio = costos de conversión / (precio - costo variable); margen "
            "variable = ventas - costos variables. Verificado con los ejercicios 1 a 7 del curso. Piezas vendidas = la menor de demanda y capacidad "
            "[criterio del ejercicio, explicitado aquí].")

    @classmethod
    def vacio(cls):
        v = super().vacio()
        v["tablas"]["estados"] = [{"indicador": t, "_k": k, **{f"e{j}": "" for j in range(1, 5)}} for k, t in INDICADORES]
        v["tablas"]["resultados"] = [{"indicador": t, "_k": k, **{f"e{j}": "" for j in range(1, 5)}} for k, t in RESULTADOS]
        return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        ent = {f.get("_k") or k: f for f, (k, _) in zip(d["tablas"]["estados"], INDICADORES)}
        kk_e = [{} for _ in INDICADORES]; res, av, utilidades = {}, [], []
        for j in range(1, 5):
            vals = {}
            for i, (k, _) in enumerate(INDICADORES):
                t = ent[k].get(f"e{j}"); x = N(t)
                if t and (x is None or x < 0 or (k == "dias" and x == 0)): kk_e[i][f"e{j}"] = "mal"
                vals[k] = x
            if all(vals[k] is not None for k, _ in INDICADORES) and vals["dias"] > 0:
                r = finanzas(vals); res[j] = r; utilidades.append((j, r["utilidad"]))
                if r["utilidad"] < 0: av.append(f"Estado {j}: hay pérdida diaria.")
                if vals["precio"] <= vals["material"]: av.append(f"Estado {j}: el precio no cubre el costo de materiales; no hay punto de equilibrio.")
                if vals["demanda"] > vals["capacidad"]: av.append(f"Estado {j}: la demanda supera la capacidad; se venden {num(vals['capacidad'], 4)} piezas.")
            elif any(vals[k] is not None for k, _ in INDICADORES): av.append(f"Estado {j}: faltan indicadores para calcularlo.")
        cc = []
        for k, _ in RESULTADOS:
            c = {}
            for j, r in res.items():
                v = r[k]
                c[f"e{j}"] = "" if v is None else pct(v) if k == "margen" else num(v, 5) if k in ("equilibrio", "vendidas") else f"{v:,.2f}"
            cc.append(c)
        cab = {}
        vm, cv = N(d["cabecera"].get("ventas_mv")), N(d["cabecera"].get("var_mv"))
        if vm and cv is not None: cab["margen_variable"] = f"{(vm - cv):,.2f} ({pct((vm - cv) / vm, 0)})"
        if len(utilidades) > 1:
            a, b = utilidades[0][1], utilidades[-1][1]
            cab["mejora"] = f"{b - a:,.2f} por día" + (f" ({pct((b - a) / abs(a), 0)})" if a else "")
        bl = [{"tipo": "grafica", "svg": barras_svg([f"Estado {j}" for j, _ in utilidades], [u for _, u in utilidades])}] if utilidades and all(u >= 0 for _, u in utilidades) else []
        return {"cab": cab, "calc": {"resultados": cc}, "clases": {"estados": kk_e}, "avisos": av, "bloques": bl}


# ---------------- Plan de muestreo ----------------
Z = {"90": 1.64, "95": 1.96}


def tamano_muestra(tipo, z, d, p=None, s=None, N_pob=None):
    """15_GB MUE-DISCRETA y MUE-CONTINUA. Devuelve (n sin ajustar, n final, ajustado)."""
    n0 = p * (1 - p) / (d / z) ** 2 if tipo == "discreto" else (z * s / d) ** 2
    if N_pob and n0 / N_pob > .05: return n0, math.ceil(n0 / (1 + n0 / N_pob)), True
    return n0, math.ceil(n0), False


@formato
class Muestreo(Formato):
    ID, TITULO = "MUESTREO", "Plan de muestreo"
    CABECERA = [F("tipo", "Tipo de dato", tipo="opcion", opciones=[["discreto", "Discreto (proporción)"], ["continuo", "Continuo (medición)"]], defecto="discreto"),
                F("que", "Qué se va a contar o medir (unidades)"), F("caracteristica", "Característica de medición"),
                F("poblacion", "Tamaño de la población N (opcional)", tipo="numero"),
                F("p", "Discreto: proporción estimada p (ej. 0.09)", tipo="numero"), F("s", "Continuo: desviación estándar estimada", tipo="numero"),
                F("d", "Precisión ± d (discreto en decimales; continuo en las unidades)", tipo="numero"),
                F("confianza", "Nivel de confianza", tipo="opcion", opciones=[["90", "90% (z = 1.64)"], ["95", "95% (z = 1.96)"]], defecto="95"),
                F("metodo", "Método", tipo="opcion", opciones=SI("Aleatorio", "Sistemático")),
                F("periodo", "Tiempo para tomar la muestra, en minutos (para la frecuencia)", tipo="numero"),
                F("n_sin", "Tamaño sin ajustar", calc=True), F("n", "Tamaño de muestra", calc=True), F("frecuencia", "Frecuencia", calc=True)]
    TABLAS = []
    NOTA = ("15_GB MUE-DISCRETA: n = p(1-p) / (d/z)². MUE-CONTINUA: n = (z·s/d)². Si n/N es mayor que 0.05 se ajusta con n / (1 + n/N). "
            "z = 1.64 (90%) o 1.96 (95%). Frecuencia = tiempo disponible / n. Ejemplos del curso verificados: N = 400, p = 0.09, d = 0.01, 90% da "
            "2,203 sin ajustar y 339 ajustado; s = 0.458, d = 0.100, 95% da 81 y una muestra cada 5.93 minutos en 480. Se redondea hacia arriba.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c, av, cab = d["cabecera"], [], {}
        tipo = c.get("tipo") or "discreto"; z = Z.get(c.get("confianza") or "95", 1.96)
        Np, p, s, dd, per = N(c.get("poblacion")), N(c.get("p")), N(c.get("s")), N(c.get("d")), N(c.get("periodo"))
        if tipo == "discreto" and p is not None and not 0 < p < 1: av.append("La proporción p debe estar entre 0 y 1 (ej. 0.09 para 9%)."); p = None
        if tipo == "discreto" and dd is not None and dd >= 1: av.append("En datos discretos la precisión va en decimales (0.01 = ±1%)."); dd = None
        if dd is not None and dd <= 0: av.append("La precisión debe ser mayor que cero."); dd = None
        listo = dd and ((tipo == "discreto" and p) or (tipo == "continuo" and s and s > 0))
        if listo:
            n0, n, aj = tamano_muestra(tipo, z, dd, p, s, Np)
            cab["n_sin"] = f"{math.ceil(n0):,} ({n0:,.2f})"; cab["n"] = f"{n:,}" + (" (ajustado por población finita)" if aj else "")
            if Np and n0 > Np: av.append("El tamaño sin ajustar es mayor que la población; se ajustó con la fórmula de población finita.")
            if per: cab["frecuencia"] = f"una muestra cada {per / n:.2f} min"
        elif any(c.get(k) for k in ("p", "s", "d")):
            av.append("Faltan datos: " + ("proporción p y precisión d." if tipo == "discreto" else "desviación estándar s y precisión d."))
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av}


# ---------------- Desempeño (DPMO y nivel sigma) ----------------
def sigma_de_dpmo(dpmo):
    """16_GB DES-Z-VALUE y PL12 SIGMA-CALC: largo plazo = NORMSINV(1 - DPO); corto plazo = largo + 1.5."""
    dpo = dpmo / 1e6
    if not 0 < dpo < 1: return None, None
    lp = float(st.norm.ppf(1 - dpo)); return lp, lp + 1.5


def dpmo_de_sigma(sigma_cp): return (1 - float(st.norm.cdf(sigma_cp - 1.5))) * 1e6


@formato
class Desempeno(Formato):
    ID, TITULO = "DESEMPENO", "Desempeño: DPMO y nivel sigma"
    CABECERA = [F("proceso", "Proceso"), F("dpmo_total", "DPMO del proceso completo", calc=True), F("sigma_total", "Nivel sigma (largo / corto plazo)", calc=True),
                F("rendimiento", "Rendimiento (1 - DPO)", calc=True), F("prioridad", "Paso a atacar primero", calc=True),
                F("conv_dato", "Convertidor: dato que tienes", tipo="opcion", opciones=[["", ""], ["dpmo", "DPMO"], ["defectuoso", "% defectuoso (fracción)"], ["rendimiento", "Rendimiento (fracción)"], ["sigma", "Nivel sigma de corto plazo"]]),
                F("conv_valor", "Convertidor: valor", tipo="numero"), F("conv_resultado", "Convertidor: equivalencias", calc=True)]
    TABLAS = [{"id": "pasos", "titulo": "Pasos del proceso", "filas": 8, "columnas": [
        {"campo": "paso", "etiqueta": "Paso", "ancho": 200}, {"campo": "unidades", "etiqueta": "Unidades", "tipo": "numero", "ancho": 90},
        {"campo": "oportunidades", "etiqueta": "Oportunidades por unidad", "tipo": "numero", "ancho": 110}, {"campo": "defectos", "etiqueta": "Defectos", "tipo": "numero", "ancho": 90},
        {"campo": "dpo", "etiqueta": "DPO", "calc": True, "ancho": 90}, {"campo": "dpmo", "etiqueta": "DPMO", "calc": True, "ancho": 100},
        {"campo": "sigma_lp", "etiqueta": "Sigma largo plazo", "calc": True, "ancho": 100}, {"campo": "sigma_cp", "etiqueta": "Sigma corto plazo", "calc": True, "ancho": 100}]}]
    NOTA = ("16_GB DES-DPMO: DPMO = defectos / (unidades × oportunidades) × 1,000,000; seis sigma = 3.4 DPMO. DES-Z-VALUE: sigma de largo plazo con "
            "la normal estándar inversa del DPO; corto plazo = largo + 1.5. PL12 SIGMA-CALC convierte entre rendimiento, DPMO, % defectuoso y sigma. "
            "Verificado con DES-EJEMPLO-INTEGRAL (DPMO 13,986 da 2.20 y 3.70) y la tabla de referencia (66,807 = 3.0; 6,210 = 4.0; 3.4 = 6.0). "
            "El proceso completo suma defectos y oportunidades de todos los pasos con las unidades del primero.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        cc, kk, av, filas = [], [], [], []
        for f in d["tablas"]["pasos"]:
            c, k = {}, {}; u, o, de = N(f.get("unidades")), N(f.get("oportunidades")), N(f.get("defectos"))
            for x in ("unidades", "oportunidades", "defectos"):
                if f.get(x) and (N(f[x]) is None or N(f[x]) < 0): k[x] = "mal"
            if u and o and de is not None and u > 0 and o > 0:
                if de > u * o: k["defectos"] = "mal"; av.append(f"«{f.get('paso') or 'paso'}»: hay más defectos que oportunidades.")
                else:
                    dpo = de / (u * o); dpmo = dpo * 1e6; lp, cp = sigma_de_dpmo(dpmo) if 0 < dpo < 1 else (None, None)
                    c.update(dpo=num(dpo, 5), dpmo=f"{dpmo:,.0f}", sigma_lp=num(lp, 3) if lp is not None else ("∞" if de == 0 else "—"),
                             sigma_cp=num(cp, 3) if cp is not None else ("∞" if de == 0 else "—"))
                    filas.append((f.get("paso") or f"Paso {len(filas) + 1}", u, o, de, dpmo))
            cc.append(c); kk.append(k)
        cab = {}
        if filas:
            u0 = filas[0][1]; tot_o = sum(o for _, _, o, _, _ in filas) * u0; tot_d = sum(de for *_, de, _ in filas)
            if len({u for _, u, *_ in filas}) > 1: av.append("Los pasos tienen distinto número de unidades; el total usa las unidades del primero.")
            dpmo = tot_d / tot_o * 1e6; lp, cp = sigma_de_dpmo(dpmo)
            cab["dpmo_total"] = f"{dpmo:,.0f}"; cab["rendimiento"] = f"{pct(1 - dpmo / 1e6, 2)} de las oportunidades sin defecto (todos los pasos)"
            if lp is not None: cab["sigma_total"] = f"{num(lp, 3)} / {num(cp, 3)}"
            peor = max(filas, key=lambda x: x[4]); cab["prioridad"] = f"{peor[0]} (DPMO {peor[4]:,.0f})"
        dato, val = d["cabecera"].get("conv_dato"), N(d["cabecera"].get("conv_valor"))
        if dato and val is not None:
            try:
                dp = {"dpmo": val, "defectuoso": val * 1e6, "rendimiento": (1 - val) * 1e6, "sigma": dpmo_de_sigma(val) if dato == "sigma" else None}[dato]
                if dp is None or not 0 < dp < 1e6: raise ValueError
                lp, cp = sigma_de_dpmo(dp)
                cab["conv_resultado"] = f"DPMO {dp:,.1f} · defectuoso {pct(dp / 1e6, 4)} · rendimiento {pct(1 - dp / 1e6, 4)} · sigma corto plazo {num(cp, 3)} (largo {num(lp, 3)})"
            except (ValueError, KeyError):
                av.append("Convertidor: el valor no es válido para ese dato (fracciones entre 0 y 1; DPMO entre 0 y 1,000,000).")
        bl = [{"tipo": "grafica", "svg": barras_svg([f[0] for f in filas], [f[4] for f in filas], nombre_linea="DPMO")}] if len(filas) > 1 else []
        return {"cab": cab, "calc": {"pasos": cc}, "clases": {"pasos": kk}, "avisos": av, "bloques": bl}


# ---------------- Checklist de revisión de fase ----------------
LISTAS = {
    "D": ("13_GB DEF-CHECKLIST", ["El proyecto ataca un área de oportunidad importante y tiene el respaldo de la dirección.",
          "El caso de negocio está definido: impacto potencial en el desempeño y alineación con el plan estratégico.",
          "El área de oportunidad está definida por sus síntomas, sin causas ni soluciones.",
          "Los resultados esperados están definidos, con objetivos y fecha límite.",
          "Están definidos los elementos clave de DMAIC: plan preliminar, equipo, roles y responsabilidades, alcance.",
          "La documentación (incluido el project charter) se revisó con el facilitador y la dirección la aprobó.",
          "Se identificaron los clientes y usuarios finales, y sus requisitos críticos (CTQ)."]),
    "M": ("16_GB DES-CHECKLIST", ["El equipo está dispuesto a aprender del problema y se identificó la parte del proceso donde están las respuestas.",
          "Se identificaron los indicadores y la viabilidad de recolectar los datos.", "Hay definiciones operacionales de las características a medir.",
          "Las definiciones se probaron entre el equipo para asegurar un lenguaje común.", "Se confirmó que los datos son nuevos y no existen ya en la organización.",
          "Se definió si se requieren factores de estratificación.", "Las hojas de recolección y el sistema de captura son fáciles de usar y dan los datos necesarios.",
          "Se determinó tipo, tamaño y frecuencia de muestreo para datos representativos.", "Se aprobó y validó el sistema de medición (R&R, estabilidad).",
          "Los datos se usaron para determinar la línea base.", "El equipo confirmó en el project charter que todos los elementos siguen siendo válidos."]),
    "A": ("17_GB CORR-CHECKLIST-ANALIZAR", ["Se examinaron los procesos y se identificaron cuellos de botella, disparidades y redundancias.",
          "Se evaluó el valor agregado y el tiempo de ciclo de cada paso, identificando actividades sin valor agregado.",
          "Se analizaron los datos: desempeño, estratificación, fuentes de variación y posibles causas raíz.",
          "Se evaluó si el proyecto es de mejora de proceso o de diseño o rediseño.", "Mejora de proceso: se desarrollaron hipótesis de causa raíz.",
          "Mejora de proceso: las hipótesis se evaluaron y verificaron, cubriendo todas las causas posibles.",
          "Diseño o rediseño: se identificaron todos los requisitos del proceso."])}
LISTAS["I"] = ("sin lista del curso", [])
LISTAS["C"] = ("sin lista del curso", [])
FASES_CK = [["D", "Definir"], ["M", "Medir"], ["A", "Analizar"], ["I", "Mejorar"], ["C", "Controlar"]]
CONFORME = SI("Conforme", "Con desviaciones", "No revisado")
DECISIONES = SI("Continuar a la siguiente fase", "Continuar con modificaciones", "Permanecer en la fase", "Repetir la fase o parte de ella", "Terminar el proyecto")


@formato
class ChecklistFase(Formato):
    ID, TITULO, REDIBUJAR = "CHECKLIST-FASE", "Checklist de revisión de fase", True
    CABECERA = [F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("fase", "Fase a revisar", tipo="opcion", opciones=FASES_CK, defecto="D"),
                F("fecha", "Fecha de revisión"), F("revisor", "Revisó (facilitador o Champion)"), F("resultado", "Resultado", calc=True),
                F("vs_caso", "Compuerta: comparación con el caso de negocio", tipo="opcion", opciones=CONFORME),
                F("vs_acta", "Compuerta: comparación con el acta (Charter)", tipo="opcion", opciones=CONFORME),
                F("vs_plan", "Compuerta: comparación con el plan (cronograma, costo, riesgos)", tipo="opcion", opciones=CONFORME),
                F("vs_beneficios", "Compuerta: comparación con los beneficios esperados", tipo="opcion", opciones=CONFORME),
                F("decision", "Decisión de la compuerta", tipo="opcion", opciones=DECISIONES), F("decidio", "Decidió (patrocinador o comité)"),
                F("condiciones", "Modificaciones o condiciones de la decisión", tipo="largo")]
    TABLAS = [{"id": "puntos", "titulo": "Puntos de verificación", "filas": 11, "fijas": True, "columnas": [
        {"campo": "punto", "etiqueta": "Punto", "ancho": 520, "lectura": True}, {"campo": "respuesta", "etiqueta": "Respuesta", "tipo": "opcion", "opciones": SI("Sí", "No", "No aplica"), "ancho": 100},
        {"campo": "evidencia", "etiqueta": "Evidencia o pendiente", "ancho": 220}]}]
    NOTA = ("Listas del curso: Definir (13_GB DEF-CHECKLIST), Medir (16_GB DES-CHECKLIST) y Analizar (17_GB CORR-CHECKLIST-ANALIZAR; los puntos 5 y 6 "
            "aplican a mejora de proceso y el 7 a diseño o rediseño). Mejorar y Controlar no tienen lista en la base del curso: para ellas se usa solo "
            "la revisión de compuerta. Revisión de compuerta: PMBOK 6, 1.2.4.3 (al final de la fase se compara el desempeño con el caso de negocio, el "
            "acta, el plan y el plan de beneficios, y se decide continuar, continuar con modificaciones, terminar, permanecer o repetir la fase); "
            "PMBOK 7, 2.3.5 (criterios de salida) y 4.4.3 (revisión de proyecto). Al cambiar de fase, los puntos se reemplazan por los de la fase elegida.")

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["puntos"] = [{"punto": p, "respuesta": "", "evidencia": ""} for p in LISTAS["D"][1]]; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        fase = d["cabecera"].get("fase") or "D"; fuente, puntos = LISTAS.get(fase, LISTAS["D"])
        actuales = d["tablas"]["puntos"]
        if [f.get("punto") for f in actuales] != puntos:                    # cambió la fase: se cargan sus puntos
            d["tablas"]["puntos"] = actuales = [{"punto": p, "respuesta": "", "evidencia": ""} for p in puntos]
        kk, av = [], []
        si = sum(1 for f in actuales if f.get("respuesta") == "Sí"); no = [i + 1 for i, f in enumerate(actuales) if f.get("respuesta") == "No"]
        na = sum(1 for f in actuales if f.get("respuesta") == "No aplica"); sin = [i + 1 for i, f in enumerate(actuales) if not f.get("respuesta")]
        for f in actuales:
            k = {"respuesta": {"Sí": "ok", "No": "no", "No aplica": ""}.get(f.get("respuesta"), "falta")}
            if f.get("respuesta") == "No" and not f.get("evidencia"): k["evidencia"] = "falta"
            kk.append(k)
        aplican = len(actuales) - na
        cab = {"resultado": (f"{si} de {aplican} cumplidos" + (" · lista para pasar de fase" if aplican and si == aplican else "")) if actuales else "Sin lista del curso: solo revisión de compuerta"}
        if no: av.append("Puntos no cumplidos: " + ", ".join(map(str, no)) + ". Anota el pendiente y su responsable antes de pasar de fase.")
        c = d["cabecera"]; dec = c.get("decision") or ""
        desv = [n for k, n in (("vs_caso", "caso de negocio"), ("vs_acta", "acta"), ("vs_plan", "plan"), ("vs_beneficios", "beneficios")) if c.get(k) == "Con desviaciones"]
        if dec == "Continuar a la siguiente fase" and (no or desv):
            av.append("Se decidió continuar sin modificaciones, pero hay " + ("puntos no cumplidos" if no else "") + (" y " if no and desv else "") +
                      ("desviaciones contra " + ", ".join(desv) if desv else "") + ": considera «Continuar con modificaciones».")
        if dec and not c.get("decidio"): av.append("Registra quién tomó la decisión de la compuerta.")
        if dec == "Continuar con modificaciones" and not c.get("condiciones"): av.append("Anota qué modificaciones condicionan la continuación.")
        if dec and any(not c.get(k) for k in ("vs_caso", "vs_acta", "vs_plan", "vs_beneficios")): av.append("Falta comparar contra algún documento antes de decidir (PMBOK 6, 1.2.4.3).")
        if sin and len(sin) < len(actuales): av.append("Sin responder: " + ", ".join(map(str, sin)) + ".")
        return {"cab": cab, "calc": {}, "clases": {"puntos": kk}, "avisos": av}


# ---------------- Gestión visual (Andon) ----------------
@formato
class Visual(Formato):
    ID, TITULO = "VISUAL", "Gestión visual y Andon"
    CABECERA = [F("area", "Área", fijo="cliente_area"), F("paso1", "1. Forma simple y visual de mostrar lo aprendido en el área", tipo="largo"),
                F("paso2", "2. Cómo se muestra el estado de la producción", tipo="largo"), F("paso3", "3. Prueba y retroalimentación en el Gemba", tipo="largo"),
                F("resumen", "Señales definidas", calc=True)]
    TABLAS = [{"id": "senales", "titulo": "Señales Andon", "filas": 8, "columnas": [
        {"campo": "anomalia", "etiqueta": "Anomalía que se alerta", "ancho": 220}, {"campo": "senal", "etiqueta": "Señal", "tipo": "opcion", "opciones": SI("Visual", "Sonora", "Visual y sonora"), "ancho": 120},
        {"campo": "color", "etiqueta": "Color o sonido", "ancho": 120}, {"campo": "quien", "etiqueta": "Quién responde", "ancho": 140},
        {"campo": "respuesta", "etiqueta": "Tiempo de respuesta (min)", "tipo": "numero", "ancho": 120}, {"campo": "accion", "etiqueta": "Acción inmediata", "ancho": 200}]}]
    NOTA = ("04_HERRAMIENTAS_LEAN LEAN-VISUAL: el Andon es una señal visual o sonora que alerta de inmediato una anomalía y muestra el estado del proceso. "
            "Diseño en 3 pasos: forma simple de mostrar lo aprendido, mostrar el estado de la producción y probar con retroalimentación del Gemba. "
            "Las columnas de quién responde y en cuánto tiempo son de uso general (no detalladas en la base).")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = [f for f in d["tablas"]["senales"] if f.get("anomalia")]; av = []; kk = []
        for f in d["tablas"]["senales"]:
            k = {}
            if f.get("anomalia"):
                if not f.get("senal"): k["senal"] = "falta"
                if not f.get("quien"): k["quien"] = "falta"
            if f.get("respuesta") and (N(f["respuesta"]) is None or N(f["respuesta"]) < 0): k["respuesta"] = "mal"
            kk.append(k)
        if filas and any(not (f.get("quien") and f.get("accion")) for f in filas): av.append("Cada señal necesita quién responde y la acción inmediata; si nadie responde, el Andon pierde valor.")
        if filas and not d["cabecera"].get("paso3"): av.append("Falta el paso 3: probar el método y recoger retroalimentación en el Gemba.")
        return {"cab": {"resumen": f"{len(filas)} señales"} if filas else {}, "calc": {}, "clases": {"senales": kk}, "avisos": av}


# ---------------- Flujo continuo ----------------
@formato
class Flujo(Formato):
    ID, TITULO = "FLUJO", "Flujo continuo: viabilidad por paso"
    CABECERA = [F("linea", "Línea o celda"), F("takt", "Takt time (s), opcional", tipo="numero"), F("dispersion", "Diferencia entre el paso más lento y el más rápido", calc=True),
                F("propuesta", "Propuesta", calc=True)]
    TABLAS = [{"id": "pasos", "titulo": "Pasos", "filas": 8, "columnas": [
        {"campo": "paso", "etiqueta": "Paso", "ancho": 200}, {"campo": "tc", "etiqueta": "Tiempo de ciclo (s)", "tipo": "numero", "ancho": 110},
        {"campo": "confiable", "etiqueta": "¿Proceso confiable? (sin paros ni defectos frecuentes)", "tipo": "opcion", "opciones": SI("Sí", "No"), "ancho": 160},
        {"campo": "vs_takt", "etiqueta": "Contra el takt", "calc": True, "ancho": 100}, {"campo": "conexion", "etiqueta": "Conexión con el siguiente", "calc": True, "ancho": 160}]}]
    NOTA = ("04_HERRAMIENTAS_LEAN LEAN-FLUJO: flujo continuo (una pieza a la vez o lotes pequeños sin esperas) donde los tiempos de ciclo son parecidos y el "
            "proceso es confiable; donde no es posible, supermercado con Kanban. Qué tan «parecidos» deben ser no lo fija la base: el formato muestra la "
            "diferencia y propone supermercado solo cuando el paso no es confiable o la diferencia supera el umbral que tú indiques [criterio de uso, no de la base].")
    CABECERA.insert(2, F("umbral", "Diferencia máxima aceptable entre pasos (%)", tipo="numero", defecto="20"))

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        takt, um = N(d["cabecera"].get("takt")), N(d["cabecera"].get("umbral")) or 20
        filas = d["tablas"]["pasos"]; cc, kk, av, tcs = [], [], [], []
        for f in filas:
            c, k = {}, {}; t = N(f.get("tc"))
            if f.get("tc") and (t is None or t <= 0): k["tc"] = "mal"; t = None
            if t and takt: c["vs_takt"] = pct(t / takt, 0) + " del takt"; k["vs_takt"] = "no" if t > takt else "ok"
            tcs.append(t); cc.append(c); kk.append(k)
        idx = [i for i, t in enumerate(tcs) if t]
        for a, b in zip(idx, idx[1:]):
            t1, t2 = tcs[a], tcs[b]; dif = abs(t1 - t2) / max(t1, t2) * 100
            noconf = filas[a].get("confiable") == "No" or filas[b].get("confiable") == "No"
            cc[a]["conexion"] = "Supermercado con Kanban" if noconf or dif > um else "Flujo continuo"
            kk[a]["conexion"] = "advertencia" if noconf or dif > um else "ok"
        cab = {}
        if len(idx) > 1:
            mx, mn = max(tcs[i] for i in idx), min(tcs[i] for i in idx); cab["dispersion"] = f"{num(mx - mn, 4)} s ({pct((mx - mn) / mx, 0)} del más lento)"
            sup = sum(1 for i in idx[:-1] if cc[i].get("conexion") == "Supermercado con Kanban")
            cab["propuesta"] = "Flujo continuo en toda la línea" if not sup else f"{sup} conexiones con supermercado y Kanban; el resto en flujo continuo"
            if takt and any(tcs[i] > takt for i in idx): av.append("Hay pasos más lentos que el takt: no pueden ir en flujo continuo hasta balancearlos (ver Balance).")
        return {"cab": cab, "calc": {"pasos": cc}, "clases": {"pasos": kk}, "avisos": av}
