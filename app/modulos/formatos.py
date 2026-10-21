"""Módulos de tipo formato (cabecera + tablas): HOJA-DATOS, AMEF, PLAN-CONTROL y TABLERO.

Cada formato guarda sus datos como texto (lo que el usuario escribe) en proyecto.formatos[ID]; calcular()
interpreta, valida y devuelve columnas calculadas, clases de color y avisos. Los datos fijos del proyecto se
inyectan en la cabecera (campos con «fijo») y no se capturan dos veces.
"""
import math, re
from datetime import date, timedelta
from statistics import median
from . import registrar, estadistica as E
from .base import num
from ..nucleo.hoja import a_numero, a_fecha
from ..nucleo import indicadores as IND

FORMATOS = {}


def formato(cls):
    FORMATOS[cls.ID] = cls; registrar(cls); return cls


class Formato:
    ID = TITULO = ""; VISTA = "formato"; CABECERA = []; TABLAS = []; NOTA = ""

    @classmethod
    def vacio(cls):
        return {"cabecera": {c["campo"]: str(c.get("defecto", "")) for c in cls.CABECERA if not c.get("fijo") and not c.get("calc")},
                "tablas": {t["id"]: [{} for _ in range(t.get("filas", 5))] for t in cls.TABLAS}}

    @classmethod
    def normalizar(cls, d):
        base = cls.vacio()
        for c in cls.CABECERA:
            if c.get("fijo") or c.get("calc"): continue
            base["cabecera"][c["campo"]] = str((d.get("cabecera") or {}).get(c["campo"], base["cabecera"][c["campo"]]) or "").strip()
        for t in cls.TABLAS:
            filas = (d.get("tablas") or {}).get(t["id"])
            if filas is None: continue
            campos = [c["campo"] for c in t["columnas"] if not c.get("calc")]
            base["tablas"][t["id"]] = [{k: str(f.get(k, "") or "").strip() for k in campos} for f in filas]
        return base

    @classmethod
    def espec(cls, hoja):
        return {"id": cls.ID, "titulo": cls.TITULO, "cabecera": cls.CABECERA, "tablas": cls.TABLAS, "nota": cls.NOTA,
                "redibujar": getattr(cls, "REDIBUJAR", False),
                "columnas_hoja": [{"j": j, "nombre": c.nombre or f"C{j + 1}", "tipo": c.tipo} for j, c in enumerate(hoja.columnas) if c.tipo]}

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        return {"cab": {}, "calc": {}, "clases": {}, "avisos": []}


def entero_1_10(t):
    x = a_numero(t) if t else None
    return int(x) if x is not None and float(x).is_integer() and 1 <= x <= 10 else None


def fila_vacia(f): return not any(v for k, v in f.items() if k != "kpi_id")


# ---------------- HOJA-DATOS ----------------
@formato
class HojaDatos(Formato):
    ID, TITULO = "HOJA-DATOS", "Hoja de recolección y plan de muestreo"
    CABECERA = [
        {"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
        {"campo": "responsable", "etiqueta": "Responsable", "fijo": "responsable"},
        {"campo": "area", "etiqueta": "Cliente o área", "fijo": "cliente_area"},
        {"campo": "inicio", "etiqueta": "Inicio de captura (DD/MM/AAAA)"},
        {"campo": "instrumento", "etiqueta": "Instrumento"},
        {"campo": "unidades", "etiqueta": "Qué se cuenta o mide (unidades)"},
        {"campo": "caracteristica", "etiqueta": "Característica de medición"},
        {"campo": "tipo_dato", "etiqueta": "Tipo de dato", "tipo": "opcion", "opciones": [["discreto", "Discreto"], ["continuo", "Continuo"]], "defecto": "continuo"},
        {"campo": "metodo", "etiqueta": "Método de muestreo", "tipo": "opcion",
         "opciones": [["aleatorio", "Aleatorio"], ["sistematico", "Sistemático"], ["estratificado", "Estratificado"]], "defecto": "aleatorio"},
        {"campo": "poblacion", "etiqueta": "Tamaño de la población (N)", "tipo": "numero"},
        {"campo": "p", "etiqueta": "Proporción estimada p (discreto, 0 a 1)", "tipo": "numero"},
        {"campo": "s", "etiqueta": "Desviación estándar estimada s (continuo)", "tipo": "numero"},
        {"campo": "d", "etiqueta": "Precisión ± d", "tipo": "numero"},
        {"campo": "confianza", "etiqueta": "Nivel de confianza", "tipo": "opcion", "opciones": [["90", "90% (z = 1.64)"], ["95", "95% (z = 1.96)"]], "defecto": "95"},
        {"campo": "tiempo", "etiqueta": "Tiempo disponible para muestrear (min)", "tipo": "numero"},
        {"campo": "n_calc", "etiqueta": "Tamaño de muestra n", "calc": True},
        {"campo": "frecuencia_calc", "etiqueta": "Una muestra cada (min)", "calc": True},
    ]
    TABLAS = [{"id": "plan", "titulo": "Registro del plan de muestreo", "filas": 3, "columnas": [
        {"campo": "medicion", "etiqueta": "Medición", "ancho": 150}, {"campo": "estratificacion", "etiqueta": "Factores de estratificación", "ancho": 170},
        {"campo": "definicion", "etiqueta": "Definición operacional", "ancho": 200}, {"campo": "tamano", "etiqueta": "Tamaño de muestra", "ancho": 90},
        {"campo": "fuente", "etiqueta": "Fuente de información", "ancho": 140}, {"campo": "recoleccion", "etiqueta": "Método de recolección", "ancho": 140},
        {"campo": "quien", "etiqueta": "Quién recolecta", "ancho": 110}]}]
    NOTA = ("Tamaño de muestra: discreto n = p(1-p)/(d/z)², continuo n = (zs/d)²; si n/N > 0.05 se ajusta con n/(1+n/N) "
            "(15_GB_ESTADISTICA_Y_MUESTREO, MUE-DISCRETA y MUE-CONTINUA). Frecuencia = tiempo disponible / n. Plan: PL11 y MUE-HOJA-DATOS. "
            "Las columnas de la hoja de recolección son las de la hoja de datos central.")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        c = d["cabecera"]; av = []; cab = {"n_calc": "", "frecuencia_calc": ""}
        z = {"90": 1.64, "95": 1.96}.get(c.get("confianza"), 1.96)
        N, dd, pp, ss, t = (a_numero(c.get(k) or "") for k in ("poblacion", "d", "p", "s", "tiempo"))
        disc = c.get("tipo_dato") == "discreto"
        falta = [e for e, v in (("la precisión d", dd), ("p" if disc else "s", pp if disc else ss)) if v is None]
        if falta:
            av.append("Para calcular el tamaño de muestra falta " + " y ".join(falta) + ".")
        elif dd <= 0 or (disc and not 0 < pp < 1) or (not disc and ss <= 0) or (N is not None and N <= 0):
            av.append("Revisa los valores: d y s deben ser mayores a cero, p entre 0 y 1 y N mayor a cero.")
        else:
            r = E.tamano_muestra("discreto" if disc else "continuo", z, dd, p=pp, s=ss, N=N)
            cab["n_calc"] = f"{r['n']:,}" + (f" (sin ajuste {r['n_sin_ajuste']:,}; n/N = {r['razon']:.2f} > 0.05, ajustado)" if r["ajustado"] else "")
            if N is not None and r["n"] > N: av.append("La muestra resulta mayor que la población.")
            if t is not None and t > 0: cab["frecuencia_calc"] = f"{t / r['n']:.2f}"
        return {"cab": cab, "calc": {}, "clases": {}, "avisos": av}


# ---------------- AMEF ----------------
AYUDA_SEV = "1 menor; 2-3 baja; 4-6 media; 7-8 alta; 9-10 muy alta (cliente molesto, producto inseguro). 10_ESCALAS_AMEF"
AYUDA_OCC = {"ppm": "1 <1 ppm; 2-3 1-250; 4-6 250-12,500; 7-8 12,500-50,000; 9-10 >50,000 ppm. 10_ESCALAS_AMEF",
             "frecuencia": "1 <1/año; 2-3 cada 6-12 meses; 4-6 cada 2-6 meses; 7-8 quincenal a mensual; 9-10 diaria a semanal. 10_ESCALAS_AMEF"}
AYUDA_DET = "1-2 muy alta (siempre se detecta); 3-4 alta; 5-6 moderada; 7-9 baja; 10 nula. 10_ESCALAS_AMEF"


def _escala(bandas):
    """Opciones 1 a 10 con la banda de 10_ESCALAS_AMEF en la etiqueta."""
    ops = [["", ""]]
    for n in range(1, 11):
        b = next(t for (lo, hi), t in bandas if lo <= n <= hi)
        ops.append([str(n), f"{n} · {b}"])
    return ops


OP_SEV = _escala([((1, 1), "menor"), ((2, 3), "baja"), ((4, 6), "media"), ((7, 8), "alta"), ((9, 10), "muy alta")])
OP_OCC = [["", ""]] + [[str(n), str(n)] for n in range(1, 11)]   # la base no nombra los niveles de ocurrencia; ver la ayuda
OP_DET = _escala([((1, 2), "muy alta"), ((3, 4), "alta"), ((5, 6), "moderada"), ((7, 9), "baja"), ((10, 10), "nula")])


@formato
class Amef(Formato):
    ID, TITULO = "AMEF", "AMEF (Análisis de Modo y Efecto de Falla)"
    CABECERA = [
        {"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
        {"campo": "tipo", "etiqueta": "Tipo de AMEF", "tipo": "opcion", "opciones": [["proceso", "Proceso"], ["diseno", "Diseño"]], "defecto": "proceso"},
        {"campo": "escala_occ", "etiqueta": "Escala de ocurrencia", "tipo": "opcion",
         "opciones": [["ppm", "Por ppm"], ["frecuencia", "Por frecuencia"]], "defecto": "ppm"},
        {"campo": "sistema", "etiqueta": "Sistema"}, {"campo": "subsistema", "etiqueta": "Subsistema"},
        {"campo": "componente", "etiqueta": "Componente"}, {"campo": "numero", "etiqueta": "Número de AMEF"},
        {"campo": "articulo", "etiqueta": "Artículo"}, {"campo": "responsable_diseno", "etiqueta": "Responsable de diseño"},
        {"campo": "modelo", "etiqueta": "Modelo"}, {"campo": "fecha", "etiqueta": "Fecha"},
        {"campo": "preparado_por", "etiqueta": "Preparado por", "fijo": "responsable"}, {"campo": "equipo", "etiqueta": "Equipo"},
        {"campo": "creado", "etiqueta": "Creado"}, {"campo": "modificado", "etiqueta": "Modificado"}]
    TABLAS = [{"id": "filas", "titulo": "Modos de falla", "filas": 5, "columnas": [
        {"campo": "operacion", "etiqueta": "Operación / parte y función", "ancho": 150},
        {"campo": "falla", "etiqueta": "Falla potencial", "ancho": 140}, {"campo": "efecto", "etiqueta": "Efecto", "ancho": 140},
        {"campo": "sev", "etiqueta": "SEV", "tipo": "opcion", "opciones": OP_SEV, "ancho": 104, "ayuda": AYUDA_SEV},
        {"campo": "causas", "etiqueta": "Causas potenciales", "ancho": 140},
        {"campo": "occ", "etiqueta": "OCC", "tipo": "opcion", "opciones": OP_OCC, "ancho": 104, "ayuda": AYUDA_OCC["ppm"]},
        {"campo": "controles", "etiqueta": "Controles actuales", "ancho": 140},
        {"campo": "det", "etiqueta": "DET", "tipo": "opcion", "opciones": OP_DET, "ancho": 104, "ayuda": AYUDA_DET},
        {"campo": "rpn", "etiqueta": "RPN", "calc": True, "ancho": 56},
        {"campo": "acciones", "etiqueta": "Acciones recomendadas", "ancho": 150}, {"campo": "responsables", "etiqueta": "Responsables", "ancho": 110},
        {"campo": "tomadas", "etiqueta": "Acciones tomadas", "ancho": 140},
        {"campo": "sev2", "etiqueta": "SEV nuevo", "tipo": "opcion", "opciones": OP_SEV, "ancho": 104}, {"campo": "occ2", "etiqueta": "OCC nuevo", "tipo": "opcion", "opciones": OP_OCC, "ancho": 104},
        {"campo": "det2", "etiqueta": "DET nuevo", "tipo": "opcion", "opciones": OP_DET, "ancho": 104}, {"campo": "rpn2", "etiqueta": "RPN nuevo", "calc": True, "ancho": 56}]}]
    NOTA = ("RPN = SEV x OCC x DET, cada factor de 1 a 10 (06_FORMULAS_Y_KPIS, FORM-RPN; PL04). Escalas: 10_ESCALAS_AMEF; no mezclar "
            "escalas de ocurrencia. El RPN nuevo solo se calcula con los tres factores nuevos. Atender primero severidad 9 a 10 aunque el "
            "RPN sea bajo (AMEF-USO). Marca como estimadas las calificaciones sin datos.")

    @classmethod
    def espec(cls, hoja):
        return super().espec(hoja)

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        filas = d["tablas"]["filas"]; calc, clases, av = [], [], []
        malas, altas, rpns = 0, [], []
        for i, f in enumerate(filas):
            c, k = {"rpn": "", "rpn2": ""}, {}
            if fila_vacia(f): calc.append(c); clases.append(k); continue
            s, o, dt = (entero_1_10(f.get(x)) for x in ("sev", "occ", "det"))
            for x, v in (("sev", s), ("occ", o), ("det", dt)):
                if f.get(x) and v is None: k[x] = "mal"; malas += 1
            if None not in (s, o, dt):
                c["rpn"] = s * o * dt; rpns.append((c["rpn"], i))
            if s is not None and s >= 9: k["sev"] = "alerta"; altas.append(i + 1)
            s2, o2, d2 = (entero_1_10(f.get(x)) for x in ("sev2", "occ2", "det2"))
            for x, v in (("sev2", s2), ("occ2", o2), ("det2", d2)):
                if f.get(x) and v is None: k[x] = "mal"; malas += 1
            if None not in (s2, o2, d2): c["rpn2"] = s2 * o2 * d2
            calc.append(c); clases.append(k)
        for pos, (v, i) in enumerate(sorted(rpns, reverse=True)[:3]):
            clases[i]["rpn"] = "alerta"
        if malas: av.append(f"{malas} calificaciones no son enteros de 1 a 10 y no entran al RPN.")
        if altas: av.append(f"Severidad 9 a 10 en las filas {', '.join(map(str, altas))}: atenderlas aunque su RPN sea bajo.")
        if rpns:
            orden = sorted(rpns, reverse=True)
            av.append("Prioridad por RPN: " + ", ".join(f"fila {i + 1} ({v})" for v, i in orden[:5]) + ".")
            dup = {v for v, _ in rpns if sum(1 for w, _ in rpns if w == v) > 1}
            if dup: av.append(f"RPN repetidos ({', '.join(map(str, sorted(dup, reverse=True)))}): el RPN no distingue combinaciones distintas con el mismo producto.")
        return {"cab": {}, "calc": {"filas": calc}, "clases": {"filas": clases}, "avisos": av,
                "ayuda": {"occ": AYUDA_OCC.get(d["cabecera"].get("escala_occ"), AYUDA_OCC["ppm"])}}


# ---------------- PLAN DE CONTROL ----------------
@formato
class PlanControl(Formato):
    ID, TITULO = "PLAN-CONTROL", "Plan de control"
    CABECERA = [
        {"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
        {"campo": "fecha", "etiqueta": "Fecha"}, {"campo": "revision", "etiqueta": "Revisión"},
        {"campo": "organizacion", "etiqueta": "Organización", "fijo": "cliente_area"},
        {"campo": "producto", "etiqueta": "Producto o servicio"}, {"campo": "proceso", "etiqueta": "Proceso"},
        {"campo": "aprobado_por", "etiqueta": "Aprobado por"}, {"campo": "preparado_por", "etiqueta": "Preparado por", "fijo": "responsable"},
        {"campo": "ultima_revision", "etiqueta": "Fecha de última revisión"}, {"campo": "version", "etiqueta": "Versión"}]
    TABLAS = [{"id": "filas", "titulo": "Puntos de control", "filas": 5, "columnas": [
        {"campo": "paso", "etiqueta": "Paso del proceso", "ancho": 130}, {"campo": "que", "etiqueta": "Qué controlamos", "ancho": 130},
        {"campo": "critico", "etiqueta": "Crítico", "tipo": "opcion", "opciones": [["", ""], ["Sí", "Sí"], ["No", "No"]], "ancho": 60},
        {"campo": "es", "etiqueta": "Entrada / salida", "tipo": "opcion", "opciones": [["", ""], ["Entrada", "Entrada"], ["Salida", "Salida"]], "ancho": 80},
        {"campo": "limites", "etiqueta": "Límites de especificación o requisitos", "ancho": 140},
        {"campo": "metodo_medicion", "etiqueta": "Método de medición", "ancho": 120}, {"campo": "ubicacion", "etiqueta": "Ubicación", "ancho": 110},
        {"campo": "metodo_control", "etiqueta": "Método de control", "ancho": 110}, {"campo": "tamano", "etiqueta": "Tamaño de muestra", "ancho": 80},
        {"campo": "frecuencia", "etiqueta": "Frecuencia", "ancho": 90}, {"campo": "quien", "etiqueta": "Quién o qué mide", "ancho": 110},
        {"campo": "registro", "etiqueta": "Dónde se registra", "ancho": 110}, {"campo": "accion", "etiqueta": "Acción correctiva", "ancho": 170},
        {"campo": "doc", "etiqueta": "Documento núm.", "ancho": 90}]}]
    NOTA = ("Estructura del curso: información general, del proceso, de medición, muestreo, toma de decisiones y aprobación "
            "(19_GB_CONTROLAR, CTRL-FORMATO; PL13, CONTROL-PLAN-GB). Los pasos críticos salen del AMEF (CTRL-FMEA). La acción "
            "correctiva debe incluir responsable, acción, criterio y cómo escalar (CTRL-REGLAS-ACCION).")

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        av, clases = [], []
        sin_accion = []
        for i, f in enumerate(d["tablas"]["filas"]):
            k = {}
            if not fila_vacia(f):
                for campo in ("paso", "que", "metodo_medicion", "tamano", "frecuencia", "quien", "accion"):
                    if not f.get(campo): k[campo] = "falta"
                if f.get("critico") == "Sí" and not f.get("accion"): sin_accion.append(i + 1)
            clases.append(k)
        if sin_accion: av.append(f"Puntos críticos sin acción correctiva: filas {', '.join(map(str, sin_accion))}.")
        if any(not fila_vacia(f) for f in d["tablas"]["filas"]) and not d["cabecera"].get("aprobado_por"):
            av.append("Falta quién aprueba: la aprobación es la parte más importante del plan (CTRL-FORMATO, sección 6).")
        return {"cab": {}, "calc": {}, "clases": {"filas": clases}, "avisos": av}


# ---------------- TABLERO ----------------
SEMANAS = 12


def chispa(valores, ancho=90, alto=22):
    pts = [(i, v) for i, v in enumerate(valores) if v is not None]
    if len(pts) < 2: return ""
    vs = [v for _, v in pts]; lo, hi = min(vs), max(vs); r = (hi - lo) or 1
    n = len(valores) - 1 or 1
    xy = " ".join(f"{2 + (ancho - 4) * i / n:.1f},{alto - 3 - (alto - 6) * (v - lo) / r:.1f}" for i, v in pts)
    return (f'<svg viewBox="0 0 {ancho} {alto}" width="{ancho}" height="{alto}"><polyline points="{xy}" fill="none" '
            f'stroke="#dd5813" stroke-width="1.6" stroke-linejoin="round"/></svg>')


_FRAC = re.compile(r"^\s*([+-]?\d+(?:[.,]\d+)?)\s*(?:/|\bde\b)\s*(\d+(?:[.,]\d+)?)\s*$", re.I)


def valor_semana(texto, unidad=""):
    """A2: valor de una semana capturada a mano. Acepta un número o una fracción «n/d» (o «n de d»), que conserva su base:
    en un indicador en % el valor es 100·n/d. Devuelve (valor, base) con base = (numerador, denominador) o None; con denominador 0
    el valor es None y la base lo declara (resultado «no definido», nunca un cero)."""
    t = (texto or "").strip()
    if not t: return None, None
    x = a_numero(t)
    if x is not None: return x, None
    m = _FRAC.match(t)
    if m:
        n, d = float(m[1].replace(",", ".")), float(m[2].replace(",", "."))
        if d == 0: return None, (n, 0.0)
        return (100 * n / d if unidad == "%" else n / d), (n, d)
    return None, None


def texto_base(base, unidad=""):
    """«28 de 30» para mostrar junto a un porcentaje; «no definido (denominador 0)» si el denominador es cero."""
    if base is None: return ""
    n, d = base
    return "no definido (denominador 0)" if d == 0 else f"{num(n, 3)} de {num(d, 3)}"


def estado_kpi(v, meta, sentido, adv=None):
    """ok / advertencia / no. Meta según 06_FORMULAS_Y_KPIS (la define el proyecto). El límite de advertencia
    (zona amarilla entre la meta y el límite) no está en la base: [GENERAL]."""
    if v is None or meta is None: return None
    menor = (sentido or "<=") == "<="
    if (v <= meta) if menor else (v >= meta): return "ok"
    if adv is not None and ((v <= adv) if menor else (v >= adv)): return "advertencia"
    return "no"


@formato
class Tablero(Formato):
    ID, TITULO, VISTA = "TABLERO", "Tablero de seguimiento semanal", "formato"
    CABECERA = [
        {"campo": "proyecto", "etiqueta": "Proyecto", "fijo": "nombre_proyecto"},
        {"campo": "responsable", "etiqueta": "Responsable", "fijo": "responsable"},
        {"campo": "semanas", "etiqueta": "Semanas a mostrar (1 a 12)", "tipo": "numero", "defecto": "6"},
        {"campo": "inicio", "etiqueta": "Inicio de la semana 1 (DD/MM/AAAA; para llenar desde la hoja)"},
        {"campo": "col_fecha", "etiqueta": "Columna de fecha de la hoja", "tipo": "col", "filtro": "fecha"}]
    TABLAS = [
        {"id": "kpi", "titulo": "Indicadores", "filas": 3, "catalogo": True, "columnas": [
            {"campo": "kpi_id", "etiqueta": "Id", "oculto": True},
            {"campo": "categoria", "etiqueta": "Categoría", "ancho": 110},
            {"campo": "indicador", "etiqueta": "Indicador", "ancho": 170}, {"campo": "unidad", "etiqueta": "Unidad", "ancho": 64},
            {"campo": "sentido", "etiqueta": "Mejor si", "tipo": "opcion", "opciones": [["<=", "≤ menor"], [">=", "≥ mayor"]], "ancho": 84},
            {"campo": "meta", "etiqueta": "Meta", "tipo": "numero", "ancho": 64},
            {"campo": "advertencia", "etiqueta": "Límite de advertencia", "tipo": "numero", "ancho": 84,
             "ayuda": "Opcional. Zona amarilla entre la meta y este límite (no respaldado por la base)."},
            ]
            + [{"campo": f"s{k}", "etiqueta": f"S{k}", "tipo": "numero", "ancho": 58, "semana": k} for k in range(1, SEMANAS + 1)]
            + [{"campo": "tendencia", "etiqueta": "Tendencia", "calc": True, "tipo": "svg", "ancho": 100},
               {"campo": "tarjeta", "etiqueta": "En resumen", "tipo": "opcion", "opciones": [["Sí", "Sí"], ["No", "No"]], "ancho": 64},
               {"campo": "tipo_ind", "etiqueta": "Tipo", "tipo": "opcion", "opciones": [["", ""], ["Adelantado", "Adelantado"], ["Atrasado", "Atrasado"]], "ancho": 100,
                "ayuda": "Adelantado: anticipa tendencias (predice). Atrasado: mide resultados ya ocurridos (PMBOK 7, 2.7.1.1)."},
               {"campo": "explicacion", "etiqueta": "Explicación si no cumple", "ancho": 180,
                "ayuda": "PMBOK 7, 2.7.3.1: texto que explica las medidas fuera de los umbrales."},
               {"campo": "col", "etiqueta": "Desde la hoja: columna (numerador)", "tipo": "col", "filtro": "num", "ancho": 120},
               {"campo": "col_den", "etiqueta": "Desde la hoja: denominador", "tipo": "col", "filtro": "num", "ancho": 120,
                "ayuda": "Solo para el cálculo «Proporción»: suma del numerador / suma de este denominador por semana. Sin columna, el numerador se toma como marcas 0/1 y la base es el número de registros."},
               {"campo": "calculo", "etiqueta": "Cálculo", "tipo": "opcion", "opciones": [["media", "Media"], ["suma", "Suma"], ["conteo", "Conteo"], ["mediana", "Mediana"], ["proporcion", "Proporción (con base)"]], "ancho": 80}]},
        {"id": "wip", "titulo": "Trabajos en proceso", "filas": 3, "columnas": [
            {"campo": "unidad", "etiqueta": "Unidad o trabajo", "ancho": 150}, {"campo": "estado", "etiqueta": "Estado", "ancho": 150},
            {"campo": "responsable", "etiqueta": "Responsable", "ancho": 110}]}]
    NOTA = ("Cada indicador es configurable: agrégalo del catálogo (botón «Agregar del catálogo») o escríbelo. «En resumen: Sí» lo muestra "
            "como tarjeta arriba (nivel ejecutivo). Verde cumple la meta, amarillo está entre la meta y el límite de advertencia, rojo no "
            "cumple. Las metas las define el proyecto (06_FORMULAS_Y_KPIS, KPI-FAMILIAS). Si eliges una columna de la hoja, las semanas se "
            "llenan solas agrupando por semanas de 7 días desde el inicio de la semana 1. Rubros del árbol marcados [COMP]: provisionales. "
            "PMBOK 7: indicadores adelantados y atrasados (2.7.1.1), métricas SMART (2.7.1.2), explicación de lo que sale del umbral (2.7.3.1) "
            "y trampas de medición como el efecto Hawthorne, las métricas de vanidad y confundir correlación con causalidad (2.7.4).")

    @classmethod
    def series(cls, d, hoja):
        """Valores por semana de cada indicador (manuales o calculados desde la hoja) y la base de cada valor (A2: «bases»:
        {semana: (numerador, denominador)} o {semana: (n, None)} para registros). Un faltante no es cero; denominador 0 = no definido.
        Lo usan el tablero y la exportación a Power BI."""
        c = d["cabecera"]; av = []
        ns = a_numero(c.get("semanas") or "") or 6
        ns = int(min(max(ns, 1), SEMANAS))
        inicio = a_fecha(c.get("inicio") or "") if c.get("inicio") else None
        colf = cls._col(hoja, c.get("col_fecha"))
        out = []
        for i, f in enumerate(d["tablas"]["kpi"]):
            if fila_vacia(f): out.append(None); continue
            unidad = f.get("unidad") or ""
            vals, bases = {}, {}
            for s in range(1, ns + 1):
                vals[s], b = valor_semana(f.get(f"s{s}") or "", unidad)
                if b is not None: bases[s] = b
            desde_hoja = False
            colv = cls._col(hoja, f.get("col")); cold = cls._col(hoja, f.get("col_den"))
            if colv is not None:
                if colf is None or inicio is None:
                    av.append(f"Indicador {i + 1}: para llenar desde la hoja faltan la columna de fecha y el inicio de la semana 1.")
                else:
                    desde_hoja = True
                    calculo = f.get("calculo") or "media"
                    grupos, dens = {}, {}
                    for r in range(hoja.n):
                        fe, x = hoja.columnas[colf].valor(r), hoja.columnas[colv].valor(r)
                        y = hoja.columnas[cold].valor(r) if cold is not None else None
                        if fe[1] and fe[2] and x[1] and x[2] is not None and (y is None or (y[1] and y[2] is not None)):
                            sem = (fe[2] - inicio).days // 7 + 1
                            if 1 <= sem <= ns:
                                grupos.setdefault(sem, []).append(x[2])
                                if y is not None: dens.setdefault(sem, []).append(y[2])
                    if calculo == "proporcion":
                        vals, bases = {}, {}
                        for sem in range(1, ns + 1):
                            if sem not in grupos: vals[sem] = None; continue
                            n_ = sum(grupos[sem]); d_ = sum(dens[sem]) if cold is not None else float(len(grupos[sem]))
                            bases[sem] = (n_, d_)
                            vals[sem] = None if d_ == 0 else (100 * n_ / d_ if unidad == "%" else n_ / d_)
                    else:
                        fn = {"media": lambda v: sum(v) / len(v), "suma": sum, "conteo": len, "mediana": median}[calculo]
                        vals = {sem: (fn(grupos[sem]) if sem in grupos else None) for sem in range(1, ns + 1)}
                        bases = {sem: (float(len(grupos[sem])), None) for sem in grupos}
            out.append({"vals": vals, "bases": bases, "desde_hoja": desde_hoja, "meta": a_numero(f.get("meta") or ""),
                        "adv": a_numero(f.get("advertencia") or ""), "sentido": f.get("sentido") or "<="})
        return ns, inicio, out, av

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        ns, inicio, series, av = cls.series(d, hoja)
        calc, clases, tarjetas = [], [], []
        for i, (f, sr) in enumerate(zip(d["tablas"]["kpi"], series)):
            cc, k = {}, {}
            if sr is None: calc.append(cc); clases.append(k); continue
            vals = sr["vals"]
            if sr["desde_hoja"]:
                for s in range(1, ns + 1):
                    b = sr["bases"].get(s)
                    if vals[s] is not None: cc[f"s{s}"] = num(vals[s], 3) + (f" ({texto_base(b)})" if b and b[1] is not None else "")
                    elif b and b[1] == 0: cc[f"s{s}"] = "no definido"
                    else: cc[f"s{s}"] = ""
            for s in range(1, ns + 1):
                b = sr["bases"].get(s)
                if b and b[1] == 0:
                    k[f"s{s}"] = "mal"
                    av.append(f"Indicador {i + 1}, semana {s}: denominador 0, el resultado queda «no definido» (no se toma como 0).")
                elif f.get(f"s{s}") and vals[s] is None and not sr["desde_hoja"]: k[f"s{s}"] = "mal"
                else:
                    e = estado_kpi(vals[s], sr["meta"], sr["sentido"], sr["adv"])
                    if e: k[f"s{s}"] = e
            if sr["adv"] is not None and sr["meta"] is not None and ((sr["adv"] < sr["meta"]) if sr["sentido"] == "<=" else (sr["adv"] > sr["meta"])):
                av.append(f"Indicador {i + 1}: el límite de advertencia debe quedar del lado que no cumple la meta."); k["advertencia"] = "mal"
            serie = [vals[s] for s in range(1, ns + 1)]
            cc["tendencia"] = chispa(serie)
            calc.append(cc); clases.append(k)
            if (f.get("tarjeta") or "Sí") == "Sí":
                hechos = [(s, v) for s, v in enumerate(serie, 1) if v is not None]
                ult = hechos[-1] if hechos else (None, None)
                prev = hechos[-2][1] if len(hechos) > 1 else None
                tarjetas.append({"indicador": f.get("indicador") or f"Indicador {i + 1}", "unidad": f.get("unidad") or "",
                                 "valor": num(ult[1], 3) if ult[1] is not None else "—", "semana": ult[0],
                                 "meta": (("≤ " if sr["sentido"] == "<=" else "≥ ") + num(sr["meta"], 3)) if sr["meta"] is not None else "sin meta",
                                 "estado": estado_kpi(ult[1], sr["meta"], sr["sentido"], sr["adv"]) or "",
                                 "cambio": (num(ult[1] - prev, 3) if ult[1] - prev < 0 else "+" + num(ult[1] - prev, 3)) if prev is not None else "",
                                 "base": texto_base(sr["bases"].get(ult[0]) if sr["bases"].get(ult[0], (0, 0))[1] is not None else None) if ult[0] else "",
                                 "chispa": chispa(serie, 140, 30)})
        if len(tarjetas) > 10: av.append(f"Hay {len(tarjetas)} indicadores en el resumen; un tablero ejecutivo funciona mejor con 6 a 10.")
        for i, (f, sr) in enumerate(zip(d["tablas"]["kpi"], series)):         # A2: tendencias que cruzan revisiones de la definición
            if sr is None or proyecto is None or not f.get("kpi_id"): continue
            revs = IND.revisiones(proyecto, f["kpi_id"])
            nota = IND.nota_cruce(revs, IND.revision_por_semana(revs, inicio, ns), [sr["vals"][s] for s in range(1, ns + 1)], f.get("indicador") or f"Indicador {i + 1}")
            if nota: av.append(nota)
        for i, (f, sr) in enumerate(zip(d["tablas"]["kpi"], series)):
            if sr is None: continue
            ultimos = [v for s, v in sorted(sr["vals"].items()) if v is not None and s <= ns]
            if ultimos and estado_kpi(ultimos[-1], sr["meta"], sr["sentido"], sr["adv"]) == "no" and not (f.get("explicacion") or "").strip():
                av.append(f"«{f.get('indicador') or f'Indicador {i + 1}'}» no cumple la meta: agrega la explicación (PMBOK 7, 2.7.3.1)."); clases[i]["explicacion"] = "falta"
        usados = [f for f, sr in zip(d["tablas"]["kpi"], series) if sr is not None]
        if len(usados) >= 3 and not any(f.get("tipo_ind") == "Adelantado" for f in usados):
            av.append("Ningún indicador está marcado como adelantado: los atrasados solo muestran lo que ya pasó (PMBOK 7, 2.7.1.1).")
        return {"cab": {}, "calc": {"kpi": calc}, "clases": {"kpi": clases}, "avisos": av, "semanas": ns, "tarjetas": tarjetas}

    @staticmethod
    def _col(hoja, nombre):
        if not nombre: return None
        return hoja.indice(nombre)
