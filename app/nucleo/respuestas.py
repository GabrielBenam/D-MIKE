"""Respuestas de un diseño por run_id (Entrega 3, E3-3; ESPEC_flujo_real_dmaic sección 5, reglas para DOE).

Formato del archivo de respuestas (CSV, TXT o Excel; primera fila = encabezados):
  RunId            obligatoria. Identifica la corrida (design_id + OrdenEst); nunca se empareja por el número de fila.
  version_diseno   obligatoria. La versión del diseño con la que se corrió; debe ser la vigente.
  <respuesta>      obligatoria. La columna con el nombre de la respuesta del diseño (o «Respuesta» / «Response»).
  <factores>       opcional. Una columna por factor con su nombre. Si viene, sus niveles se verifican contra los del diseño; si no viene, la
                   identidad se verifica solo con RunId y versión y se avisa. Las demás columnas (fecha, operador, lote…) se ignoran con aviso.
La importación es atómica: si hay un solo desajuste no se escribe nada y se informa cada error, para corregir el archivo y volver a importar.
Rechaza: columnas obligatorias ausentes, corrida repetida, RunId que no pertenece al diseño, RunId de más de un diseño, versión distinta de la
vigente, niveles que no coinciden con los del diseño (respuesta asociada al factor equivocado), respuesta no numérica, filas con respuesta y sin RunId,
definición del diseño cambiada sin registrar, respuestas existentes de otra versión y respuestas existentes distintas (salvo sobrescribir=True).
"""
import hashlib, re
from datetime import datetime
from . import disenos as DIS
from .hoja import a_numero, es_na, es_sin_datos_explicito, TEXTO_NA, TEXTO_SIN_DATOS

MAX_DETALLE = 8


def _clave(t):
    import unicodedata
    base = "".join(c for c in unicodedata.normalize("NFD", str(t or "").lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", base)


RUNID, VERSION, RESPUESTAS_GENERICAS = {"runid"}, {"versiondiseno", "versiondeldiseno", "version"}, {"respuesta", "response"}
COLUMNAS_DEL_ARCHIVO_DE_CORRIDAS = {"ordencorrida", "ordenest", "tipopunto", "bloque", "marca"}     # las trae el archivo que exporta E3-4: se ignoran sin aviso
PATRON_RUNID = re.compile(r"^(DIS-.+)-R\d+$")


def _lista(items, titulo):
    """Un solo error con el detalle de los primeros casos."""
    extra = f" (y {len(items) - MAX_DETALLE} más)" if len(items) > MAX_DETALLE else ""
    return f"{titulo}: " + "; ".join(items[:MAX_DETALLE]) + extra + "."


def huella_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""): h.update(bloque)
    return h.hexdigest()


def _diseno_de(proyecto, hoja, design_id, run_ids_archivo):
    """(clave, info, descriptor) del diseño destino o (None, None, mensaje de error)."""
    ds = DIS.descriptores(proyecto, hoja)
    if not ds: return None, None, "Este proyecto no tiene diseños de experimentos: crea uno primero (Estadística > Diseño de experimentos)."
    if design_id is None:
        pref = {m[1] for r in run_ids_archivo if (m := PATRON_RUNID.match(r))}
        if len(pref) > 1: return None, None, "El archivo trae corridas de más de un diseño (" + ", ".join(sorted(pref)) + "): importa un archivo por diseño."
        if len(pref) == 1: design_id = pref.pop()
        elif len(ds) == 1: design_id = ds[0]["design_id"]
        else: return None, None, "No se pudo saber a qué diseño pertenece el archivo: ningún RunId tiene el formato DIS-…-R### y el proyecto tiene varios diseños."
    d = next((x for x in ds if x["design_id"] == design_id), None)
    if d is None: return None, None, f"El diseño {design_id} no existe en este proyecto (existen: {', '.join(x['design_id'] for x in ds)})."
    return d["clave"], proyecto.formatos["_disenos"][d["clave"]], d


def analizar(proyecto, hoja, filas, design_id=None, sobrescribir=False, extra=None):
    """Valida el archivo contra el diseño sin escribir nada. filas: lista de listas de texto, la primera con encabezados.
    extra: nombre de una SEGUNDA respuesta medida en las mismas corridas del diseño (por ejemplo «Costo»); se importa por RunId igual que la principal y queda
    registrada en el diseño (respuestas_extra), que es lo que la liga al diseño y a su región. Nunca por posición de fila.
    Devuelve {ok, errores, avisos, design_id, version, escrituras: [(fila_hoja, texto)], escritas, iguales, sobrescritas, sin_dato, extra}."""
    plan = {"ok": False, "errores": [], "avisos": [], "design_id": design_id, "version": None, "escrituras": [], "escritas": 0, "iguales": 0,
            "sobrescritas": 0, "sin_dato": 0, "extra": (str(extra).strip() or None) if extra else None}
    E, A = plan["errores"], plan["avisos"]
    if not filas or len(filas) < 2: E.append("El archivo no tiene filas de respuestas."); return plan
    enc = filas[0]; claves = [_clave(h) for h in enc]
    j_run = next((i for i, c in enumerate(claves) if c in RUNID), None)
    j_ver = next((i for i, c in enumerate(claves) if c in VERSION), None)
    cuerpo = [(k, f) for k, f in enumerate(filas[1:], start=2) if any(c.strip() for c in f)]          # k = número de fila en el archivo (encabezado = 1)
    if j_run is None: E.append("Falta la columna RunId: las respuestas se asignan por run_id, nunca por el número de fila.")
    if j_ver is None: E.append("Falta la columna version_diseno: sin ella no se sabe con qué versión del diseño se corrieron las respuestas.")
    ids = [f[j_run].strip() for _, f in cuerpo if j_run is not None and j_run < len(f) and f[j_run].strip()] if j_run is not None else []
    clave, info, d = _diseno_de(proyecto, hoja, design_id, ids)
    if clave is None: E.append(d); return plan
    plan["design_id"], plan["version"] = d["design_id"], d["version_diseno"]
    cols = DIS.columnas(hoja, info)
    if cols["respuesta"] is None: E.append("No se encuentra en la hoja la columna de respuestas del diseño."); return plan
    nombre_resp = plan["extra"] or info.get("respuesta")
    if plan["extra"]:
        reservados = {_clave(f["nombre"]) for f in info.get("factores", [])} | {_clave(info.get(k)) for k in ("respuesta", "orden_est", "orden_corrida", "tipo_punto", "bloque", "col_runid") if info.get(k)}
        if _clave(plan["extra"]) in reservados or _clave(plan["extra"]) in RUNID | VERSION | RESPUESTAS_GENERICAS:
            E.append(f"«{plan['extra']}» no puede ser una segunda respuesta: es una columna del diseño o un nombre reservado."); return plan
        cols = dict(cols, respuesta=hoja.indice(plan["extra"]))                       # None si la columna aún no existe: se crea al aplicar
    j_resp = next((i for i, c in enumerate(claves) if c == _clave(nombre_resp)), None)
    if j_resp is None and not plan["extra"]: j_resp = next((i for i, c in enumerate(claves) if c in RESPUESTAS_GENERICAS), None)
    if j_resp is None: E.append(f"Falta la columna de la respuesta «{nombre_resp}»" + ("" if plan["extra"] else " (o «Respuesta»)") + ".")
    if j_run is None or j_ver is None or j_resp is None: return plan
    # estado del diseño
    legado = not info.get("huella_diseno")
    est = DIS.estado_definicion(hoja, info)
    if est == "cambiada": E.append(f"La definición de {d['design_id']} cambió y no está registrada: registra la versión nueva del diseño antes de importar respuestas.")
    if est == "no_verificable": E.append(f"Faltan en la hoja columnas de {d['design_id']} (OrdenEst o factores): no se puede verificar el diseño.")
    if plan["extra"]:
        n_resp = sum(1 for t in hoja.columnas[cols["respuesta"]].celdas if t not in (None, "") and str(t).strip() != "") if cols["respuesta"] is not None else 0
        v_resp = ((info.get("respuestas_extra") or {}).get(plan["extra"]) or {}).get("version") if n_resp else None
    else: n_resp, v_resp = DIS.estado_respuestas(hoja, info)
    if n_resp and v_resp is not None and v_resp != plan["version"]:
        E.append(f"La hoja ya tiene respuestas de la versión {v_resp} y el diseño está en la versión {plan['version']}: no se mezclan. "
                 "Bórralas o confirma que corresponden a la versión vigente (Diseños del proyecto).")
    # filas del diseño por run_id
    run_ids, _ = DIS.run_ids(hoja, info, clave)
    fila_de = {}
    for i, r in enumerate(run_ids):
        if r: fila_de.setdefault(r, []).append(i)
    # factores del archivo
    f_cols = {}
    for q, jf in enumerate(cols["factores"]):
        nombre = info["factores"][q]["nombre"]
        j = next((i for i, c in enumerate(claves) if c == _clave(nombre)), None)
        if j is not None and jf is not None: f_cols[nombre] = (j, jf)
    if not f_cols: A.append("El archivo no trae las columnas de los factores: la identidad se verificó solo con RunId y versión, no con los niveles.")
    elif len(f_cols) < len(cols["factores"]):
        A.append("El archivo trae los niveles de " + ", ".join(f_cols) + " pero no de todos los factores: solo esos se verificaron.")
    reconocidas = {j_run, j_ver, j_resp} | {j for j, _ in f_cols.values()}
    ignoradas = [enc[i] for i in range(len(enc)) if i not in reconocidas and enc[i].strip() and _clave(enc[i]) not in COLUMNAS_DEL_ARCHIVO_DE_CORRIDAS]
    if ignoradas: A.append("Columnas que se ignoran: " + ", ".join(ignoradas) + ".")
    # filas
    vistos, repetidos, desconocidos, versiones, niveles, no_num, sin_run, conflictos = {}, [], [], [], [], [], [], []
    ambiguos = set()
    for k, f in cuerpo:
        g = lambda j, f=f: f[j].strip() if j < len(f) else ""
        r, v, y = g(j_run), g(j_ver), g(j_resp)
        if not r:
            if y: sin_run.append(f"fila {k} del archivo")
            continue
        if r in vistos: repetidos.append(r)
        vistos[r] = k
        if r not in fila_de: desconocidos.append(r); continue
        if len(fila_de[r]) > 1: ambiguos.add(r); continue
        vv = a_numero(v) if v else None
        if vv is None or not float(vv).is_integer() or int(vv) != plan["version"]:
            versiones.append(f"{r} trae versión «{v or 'vacía'}»")
        i_h = fila_de[r][0]
        for nombre, (j, jf) in f_cols.items():
            esperado = hoja.columnas[jf].valor(i_h)[2]; recibido = a_numero(g(j)) if g(j) else None
            if esperado is None or recibido is None or abs(recibido - esperado) > 1e-6 * max(1.0, abs(esperado)):
                niveles.append(f"{r}: {nombre} del archivo {g(j) or 'vacío'} contra {DIS_texto(esperado)} del diseño")
        if not y: plan["sin_dato"] += 1; continue
        if es_na(y) or es_sin_datos_explicito(y): texto = TEXTO_NA if es_na(y) else TEXTO_SIN_DATOS
        else:
            x = a_numero(y)
            if x is None: no_num.append(f"{r}: «{y}»"); continue
            texto = y
        actual = (hoja.columnas[cols["respuesta"]].celdas[i_h] if i_h < len(hoja.columnas[cols["respuesta"]].celdas) else None) if cols["respuesta"] is not None else None
        if actual not in (None, ""):
            ya = a_numero(actual) if not (es_na(actual) or es_sin_datos_explicito(actual)) else None
            nuevo = a_numero(texto) if texto not in (TEXTO_NA, TEXTO_SIN_DATOS) else None
            if (ya is not None and nuevo is not None and abs(ya - nuevo) <= 1e-9 * max(1.0, abs(ya))) or (ya is None and nuevo is None and actual.strip().lower() == texto.lower()):
                plan["iguales"] += 1; continue
            if not sobrescribir: conflictos.append(f"{r}: ya tiene «{actual}» y el archivo trae «{texto}»"); continue
            plan["sobrescritas"] += 1
        plan["escrituras"].append((i_h, texto))
    if ambiguos: E.append(_lista(sorted(ambiguos), "La hoja tiene más de una fila con el mismo RunId (OrdenEst repetido); corrígelo en la hoja"))
    if sin_run: E.append(_lista(sin_run, "Filas con respuesta y sin RunId (no se asignan por posición)"))
    if repetidos: E.append(_lista(sorted(set(repetidos)), "Corridas repetidas en el archivo"))
    if desconocidos: E.append(_lista(desconocidos, f"RunId que no pertenecen a {d['design_id']}"))
    if versiones: E.append(_lista(versiones, f"Versión de diseño incompatible (la vigente es la {plan['version']})"))
    if niveles: E.append(_lista(niveles, "Los niveles no coinciden con los del diseño (respuesta asociada al factor equivocado o al RunId equivocado)"))
    if no_num: E.append(_lista(no_num, "Respuestas que no son números"))
    if conflictos: E.append(_lista(conflictos, "Ya hay respuestas distintas en la hoja (usa sobrescribir si es intencional)"))
    if not cuerpo: E.append("El archivo no tiene filas de respuestas.")
    if plan["sin_dato"]: A.append(f"Sin datos: {plan['sin_dato']} corridas del archivo no traen respuesta; quedan sin dato, no se toman como cero.")
    plan["escritas"] = len(plan["escrituras"])
    plan["ok"] = not E
    if plan["ok"] and legado: A.append("El diseño es anterior a 0.29: se toma el estado actual de la hoja como su línea base (versión 1).")
    return plan


def DIS_texto(v):
    return "vacío" if v is None else (str(int(v)) if float(v).is_integer() else f"{v:.6g}")


def aplicar(proyecto, hoja, plan, nombre_archivo, huella, ahora=None):
    """Escribe el plan validado (solo si plan['ok']) y deja la trazabilidad en el diseño. Devuelve el número de celdas escritas."""
    if not plan["ok"]: raise ValueError("El plan tiene errores; no se aplica.")
    clave = next(d["clave"] for d in DIS.descriptores(proyecto, hoja) if d["design_id"] == plan["design_id"])
    info = proyecto.formatos["_disenos"][clave]
    DIS.asegurar_identidad(proyecto, hoja)                       # diseño anterior a 0.29: línea base en este momento
    cols = DIS.columnas(hoja, info)
    if plan.get("extra"):                                          # segunda respuesta: columna propia, registrada en el diseño con su versión
        j = hoja.indice(plan["extra"])
        if j is None:
            hoja.pegar(-1, len(hoja.columnas), plan["extra"]); j = hoja.indice(plan["extra"]); hoja.cambiar_tipo(j, "num")
        col = hoja.columnas[j]
        if plan["escrituras"] or plan["iguales"]: info.setdefault("respuestas_extra", {})[plan["extra"]] = {"version": plan["version"]}
    else:
        col = hoja.columnas[cols["respuesta"]]
        if plan["escrituras"] or plan["iguales"]: info["respuestas_version"] = plan["version"]
    if len(col.celdas) < hoja.n: col.celdas.extend([None] * (hoja.n - len(col.celdas)))
    for i, texto in plan["escrituras"]: col.celdas[i] = texto
    info.setdefault("importaciones", []).append({"archivo": nombre_archivo, "huella": huella, "version": plan["version"], "escritas": plan["escritas"],
                                                 "sobrescritas": plan["sobrescritas"], "iguales": plan["iguales"], "sin_dato": plan["sin_dato"], "respuesta": plan.get("extra") or info.get("respuesta"),
                                                 "fecha": (ahora or datetime.now()).isoformat(timespec="seconds")})
    return plan["escritas"]
