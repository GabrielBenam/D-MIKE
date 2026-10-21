"""Identidad de los diseños de experimentos (Entrega 3, E3-2; ESPEC_receta_v2 secciones 2.1 y 6.4; ESPEC_flujo_real_dmaic sección 5, reglas para DOE).

Cada diseño que crea DISENO-RSM guarda su identidad dentro de proyecto.formatos["_disenos"][respuesta] (sin cambiar version_formato):

  design_id        «DIS-» + el nombre real de la columna de la respuesta (único en el proyecto). Lo asigna D-MIKE al crear el diseño; nunca la
                   receta ni el usuario. Es inmutable. Un diseño anterior a 0.29 lo recibe al vuelo con la misma regla a partir de su clave
                   (Y, Y_2…), sin tocar la hoja: es determinista y reversible (una versión anterior ignora las claves nuevas).
  run_id           «design_id-R» + OrdenEst con 3 dígitos (por ejemplo DIS-Y-R007). Se deriva SIEMPRE del valor de la columna OrdenEst de esa
                   fila y nunca de la posición de la fila: ordenar o filtrar la hoja no lo cambia. No se guarda: se calcula de la hoja.
  version_diseno   Entero que asigna solo D-MIKE (ni la receta ni el usuario lo teclean). Nace en 1 al crear el diseño. Sube en 1 únicamente
                   cuando el usuario registra una nueva versión (registrar_version) después de que la definición del diseño cambió. La
                   definición es la huella de huella_definicion(): niveles reales de cada factor, tipo de punto y bloque de cada corrida
                   (identificada por OrdenEst) y los nombres de los factores. La respuesta, OrdenCorrida (el orden en que se corre) y las
                   demás columnas no son parte de la definición: capturar respuestas o volver a aleatorizar el orden no crea una versión.
                   Mientras la huella actual difiera de la guardada, el diseño está «cambiada» y E3-3 rechaza mezclar respuestas.

En proyectos reales el diseño agrega una columna RunId de solo lectura (rol «run_id»); en demostración no se toca la hoja.
"""
import hashlib, json
from datetime import datetime

PREFIJO = "DIS-"
ROL_RUNID = "run_id"
NOMBRE_RUNID = "RunId"
DESC_RUNID = "Solo lectura: se genera con design_id y OrdenEst; no se edita"


def _disenos(proyecto, crear=False):
    return proyecto.formatos.setdefault("_disenos", {}) if crear else (proyecto.formatos.get("_disenos") or {})


# ---------------- columnas del diseño ----------------
def _indice(hoja, nombre):
    return hoja.indice(nombre) if nombre else None


def columnas(hoja, info):
    """Índices de las columnas del diseño. Usa los nombres guardados; en un diseño anterior a 0.29 deduce OrdenEst y OrdenCorrida por la
    disposición con que DISENO-RSM las crea (OrdenEst, OrdenCorrida, TipoPunto, Bloque, factores, respuesta). Un valor None dice que esa
    columna no se encontró (el usuario la borró o renombró)."""
    tipo = _indice(hoja, info.get("tipo_punto"))
    est = _indice(hoja, info.get("orden_est"))
    cor = _indice(hoja, info.get("orden_corrida"))
    if est is None and tipo is not None and tipo >= 2 and (hoja.columnas[tipo - 2].nombre or "").lower().startswith("ordenest"): est = tipo - 2
    if cor is None and tipo is not None and tipo >= 1 and (hoja.columnas[tipo - 1].nombre or "").lower().startswith("ordencorrida"): cor = tipo - 1
    return {"orden_est": est, "orden_corrida": cor, "tipo_punto": tipo, "bloque": _indice(hoja, info.get("bloque")),
            "factores": [_indice(hoja, f["nombre"]) for f in info.get("factores", [])], "respuesta": _indice(hoja, info.get("respuesta")),
            "runid": _indice(hoja, info.get("col_runid"))}


def _num(hoja, j, i):
    if j is None: return None
    t = hoja.columnas[j].valor(i)
    return t[2] if t[1] and isinstance(t[2], (int, float)) else None


def _texto(hoja, j, i):
    if j is None: return None
    t = hoja.columnas[j].valor(i)
    return t[0] if t[1] and t[0] != "" else None


# ---------------- identidad ----------------
def identidad(info, clave):
    """design_id y version_diseno de un diseño: lo guardado o, si es anterior a 0.29, lo derivado de su clave (versión 1)."""
    return {"design_id": info.get("design_id") or PREFIJO + str(clave), "version_diseno": int(info.get("version_diseno") or 1)}


def _id_unico(proyecto, base):
    usados = {i.get("design_id") for i in _disenos(proyecto).values()}
    if base not in usados: return base
    n = 2
    while f"{base}-{n}" in usados: n += 1
    return f"{base}-{n}"


def run_id(design_id, orden_est):
    """RunId de una corrida: design_id y OrdenEst con 3 dígitos (más dígitos si hace falta)."""
    return f"{design_id}-R{int(orden_est):03d}"


def run_ids(hoja, info, clave):
    """RunId de cada fila de la hoja según su OrdenEst: (lista por fila con RunId o None, problemas). Problemas: filas sin OrdenEst entero,
    OrdenEst repetido (cada uno con sus filas, base 1) y columnas que faltan. Nunca usa la posición de la fila."""
    ident = identidad(info, clave); cols = columnas(hoja, info)
    if cols["orden_est"] is None:
        return [None] * hoja.n, {"sin_columna": True, "sin_orden": [], "repetidos": {}}
    ids, sin, vistos = [], [], {}
    for i in range(hoja.n):
        v = _num(hoja, cols["orden_est"], i)
        if v is None or not float(v).is_integer() or v < 1:
            ids.append(None)
            if any(hoja.columnas[j].valor(i)[0] != "" for j in range(len(hoja.columnas)) if j != cols["runid"]): sin.append(i + 1)
            continue
        r = run_id(ident["design_id"], v); ids.append(r); vistos.setdefault(r, []).append(i + 1)
    return ids, {"sin_columna": False, "sin_orden": sin, "repetidos": {r: f for r, f in vistos.items() if len(f) > 1}}


def huella_definicion(hoja, info):
    """SHA-256 de la definición del diseño (ver el encabezado). None si faltan OrdenEst o los factores en la hoja."""
    cols = columnas(hoja, info)
    if cols["orden_est"] is None or not cols["factores"] or any(j is None for j in cols["factores"]): return None
    corridas = []
    for i in range(hoja.n):
        oe = _num(hoja, cols["orden_est"], i)
        if oe is None: continue
        corridas.append([oe, _texto(hoja, cols["tipo_punto"], i), _texto(hoja, cols["bloque"], i),
                         [None if (v := _num(hoja, j, i)) is None else round(float(v), 9) for j in cols["factores"]]])
    corridas.sort(key=lambda c: (c[0], json.dumps(c, sort_keys=True)))
    cuerpo = {"factores": [f["nombre"].lower() for f in info.get("factores", [])], "corridas": corridas}
    return hashlib.sha256(json.dumps(cuerpo, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def asignar_nuevo(proyecto, hoja, info, clave):
    """Identidad de un diseño recién creado: design_id único, version 1, huella de la definición y nombres de las columnas de la hoja."""
    info["design_id"] = _id_unico(proyecto, PREFIJO + str(clave))
    info["version_diseno"] = 1
    info["huella_diseno"] = huella_definicion(hoja, info)
    info["historial_versiones"] = []
    return info


def asegurar_identidad(proyecto, hoja):
    """Guarda la identidad de los diseños anteriores a 0.29 (6.4 de la especificación): design_id de su clave, versión 1 y la huella de la hoja
    en este momento (su línea base). No toca la hoja. Solo lo llaman las operaciones que necesitan una línea base (registrar una versión y,
    desde E3-3, capturar respuestas por run_id); abrir un proyecto no modifica lo guardado. Devuelve cuántos diseños recibieron identidad."""
    n = 0
    for clave, info in _disenos(proyecto).items():
        if info.get("design_id"): continue
        info["design_id"] = _id_unico(proyecto, PREFIJO + str(clave)); info["version_diseno"] = 1
        info["huella_diseno"] = huella_definicion(hoja, info); info.setdefault("historial_versiones", [])
        cols = columnas(hoja, info)
        if cols["orden_est"] is not None and not info.get("orden_est"): info["orden_est"] = hoja.columnas[cols["orden_est"]].nombre
        if cols["orden_corrida"] is not None and not info.get("orden_corrida"): info["orden_corrida"] = hoja.columnas[cols["orden_corrida"]].nombre
        n += 1
    return n


def estado_definicion(hoja, info):
    """«vigente» (la definición actual coincide con la de la versión), «cambiada» (difiere: hace falta registrar una versión nueva) o
    «no_verificable» (faltan columnas del diseño en la hoja) o «sin_linea_base» (diseño anterior a 0.29 al que aún no se le guardó la huella)."""
    actual = huella_definicion(hoja, info)
    if actual is None: return "no_verificable"
    if not info.get("huella_diseno"): return "sin_linea_base"
    return "vigente" if actual == info.get("huella_diseno") else "cambiada"


# ---------------- respuestas del diseño (E3-3) ----------------
def estado_respuestas(hoja, info):
    """(cuántas respuestas hay en la hoja, versión con la que se capturaron o None). Cuenta las celdas no vacías de la columna de respuestas
    del diseño. La versión la deja D-MIKE: al importar, o al etiquetar las respuestas tecleadas con la versión vigente."""
    j = _indice(hoja, info.get("respuesta"))
    if j is None: return 0, info.get("respuestas_version")
    n = sum(1 for t in hoja.columnas[j].celdas if t not in (None, "") and str(t).strip() != "")
    return n, (info.get("respuestas_version") if n else None)


def etiquetar_respuestas(proyecto, hoja):
    """Las respuestas tecleadas o pegadas a mano se etiquetan con la versión vigente del diseño; sin respuestas, se borra la etiqueta. Solo toca
    diseños con identidad guardada (los anteriores a 0.29 no se modifican al abrir ni al consultar)."""
    for info in _disenos(proyecto).values():
        if not info.get("design_id"): continue
        n, v = estado_respuestas(hoja, info)
        if n == 0 and info.get("respuestas_version") is not None: info["respuestas_version"] = None
        elif n and v is None: info["respuestas_version"] = int(info.get("version_diseno") or 1)


def sincronizar(proyecto, hoja):
    """Mantiene lo derivado de la hoja: la columna RunId de solo lectura y la etiqueta de versión de las respuestas. Devuelve True si cambió RunId."""
    etiquetar_respuestas(proyecto, hoja)
    return sincronizar_runid(proyecto, hoja)


def verificar_para_analisis(proyecto, hoja, nombre_respuesta):
    """Motivo (texto) por el que un análisis no debe correr sobre la columna de respuestas de un diseño, o None si puede. No se mezclan
    respuestas de versiones distintas: se rechaza si la definición cambió sin registrar o si las respuestas son de otra versión.
    Diseños anteriores a 0.29 (sin identidad guardada) y columnas que no son la respuesta de un diseño no se verifican."""
    if proyecto is None: return None
    info = _disenos(proyecto).get(nombre_respuesta)
    if not info or not info.get("design_id"): return None
    n, v = estado_respuestas(hoja, info)
    if n == 0: return None
    ident = identidad(info, nombre_respuesta)
    if estado_definicion(hoja, info) == "cambiada":
        return (f"La definición de {ident['design_id']} cambió desde la versión {ident['version_diseno']} y no está registrada: las respuestas podrían no corresponder "
                "a los niveles actuales. Registra la versión nueva del diseño (Diseños del proyecto) antes de analizar.")
    if v is not None and v != ident["version_diseno"]:
        return (f"Las respuestas de {ident['design_id']} son de la versión {v} y el diseño está en la versión {ident['version_diseno']}: no se mezclan versiones. "
                "Bórralas, impórtalas de nuevo con la versión vigente o confirma que corresponden a ella (Diseños del proyecto).")
    return None


def confirmar_respuestas(proyecto, hoja, design_id, motivo, ahora=None):
    """Resolución manual y auditable: el usuario declara que las respuestas que hay en la hoja corresponden a la versión vigente. Exige un motivo.
    Devuelve (estado, mensaje): «confirmadas», «sin_cambios» o «error»."""
    motivo = str(motivo or "").strip()
    for clave, info in _disenos(proyecto).items():
        if identidad(info, clave)["design_id"] != design_id: continue
        if not info.get("design_id"): asegurar_identidad(proyecto, hoja)
        n, v = estado_respuestas(hoja, info); vig = int(info.get("version_diseno") or 1)
        if n == 0: return "sin_cambios", f"{design_id} no tiene respuestas en la hoja: no hay nada que confirmar."
        if v == vig: return "sin_cambios", f"Las respuestas de {design_id} ya son de la versión vigente ({vig})."
        if not motivo: return "error", "Escribe el motivo: la confirmación queda registrada en el diseño."
        info.setdefault("confirmaciones_respuestas", []).append({"de_version": v, "a_version": vig, "motivo": motivo,
                                                                 "fecha": (ahora or datetime.now()).isoformat(timespec="seconds")})
        info["respuestas_version"] = vig
        return "confirmadas", f"Las respuestas de {design_id} se confirman como de la versión {vig} (antes de la {v}); quedó registrado."
    return "error", f"No existe el diseño {design_id}."


def descriptores(proyecto, hoja):
    """Vista de los diseños del proyecto para la interfaz y el seguimiento. Solo lee: la identidad de un diseño anterior a 0.29 se deriva de su
    clave sin guardarla (determinista y reversible)."""
    out = []
    for clave, info in _disenos(proyecto).items():
        ident = identidad(info, clave); ids, prob = run_ids(hoja, info, clave)
        out.append({"clave": clave, **ident, "respuesta": info.get("respuesta"), "factores": [f["nombre"] for f in info.get("factores", [])],
                    "tipo": info.get("tipo"), "corridas": info.get("corridas"), "estado_definicion": estado_definicion(hoja, info),
                    "col_runid": info.get("col_runid"), "run_ids": sum(1 for r in ids if r), "problemas": prob,
                    "respuestas": dict(zip(("n", "version"), estado_respuestas(hoja, info))), "importaciones": len(info.get("importaciones") or []),
                    "region": info.get("region") or "no_declarada", "limites_seguros": info.get("limites_seguros"),
                    "historial_versiones": list(info.get("historial_versiones") or [])})
    return out


def registrar_version(proyecto, hoja, design_id, motivo="", ahora=None):
    """Registra una versión nueva del diseño (la asigna D-MIKE, a petición del usuario) cuando su definición cambió. Devuelve
    (estado, mensaje): «nueva», «sin_cambios», «linea_base» (diseño anterior a 0.29 sin huella) o «error». La anterior queda en historial_versiones con su huella."""
    for clave, info in _disenos(proyecto).items():
        if identidad(info, clave)["design_id"] != design_id: continue
        if not info.get("huella_diseno"):                  # diseño anterior a 0.29: no hay con qué comparar; el estado de hoy es la línea base (versión 1)
            if huella_definicion(hoja, info) is None: return "error", "No se encuentran en la hoja las columnas del diseño (OrdenEst y factores): no se puede tomar la línea base."
            asegurar_identidad(proyecto, hoja)
            return "linea_base", f"{design_id} no tenía una línea base (es anterior a 0.29): se tomó su estado actual como versión 1. Desde ahora un cambio de su definición se puede registrar como versión nueva."
        actual = huella_definicion(hoja, info)
        if actual is None: return "error", "No se encuentran en la hoja las columnas del diseño (OrdenEst y factores): no se puede registrar una versión."
        if actual == info.get("huella_diseno"): return "sin_cambios", f"La definición de {design_id} no cambió: sigue en la versión {int(info.get('version_diseno') or 1)}."
        previa = int(info.get("version_diseno") or 1)
        info.setdefault("historial_versiones", []).append({"version": previa, "huella": info.get("huella_diseno"), "reemplazada_en": (ahora or datetime.now()).isoformat(timespec="seconds"),
                                                           "motivo": str(motivo or "").strip()})
        info["version_diseno"] = previa + 1; info["huella_diseno"] = actual
        return "nueva", f"{design_id} pasa a la versión {previa + 1}. Las respuestas de la versión {previa} ya no se pueden mezclar con las de esta."
    return "error", f"No existe el diseño {design_id}."


# ---------------- columna RunId (solo proyectos reales) ----------------
def agregar_runid(hoja, info):
    """Agrega la columna RunId (solo lectura) al final de la hoja y la deja registrada en el diseño. Devuelve el índice de la columna."""
    j = len(hoja.columnas)
    hoja.pegar(-1, j, NOMBRE_RUNID)
    real = hoja.columnas[j].nombre
    hoja.columnas[j].rol = ROL_RUNID; hoja.columnas[j].desc = DESC_RUNID
    info["col_runid"] = real
    return j


def columnas_protegidas(proyecto, hoja):
    """Índices de las columnas RunId de solo lectura."""
    return {j for info in _disenos(proyecto).values() if (j := _indice(hoja, info.get("col_runid"))) is not None}


def sincronizar_runid(proyecto, hoja):
    """Reescribe cada columna RunId con los run_id derivados de OrdenEst (así es de solo lectura: cualquier cambio se deshace). Devuelve
    True si cambió alguna celda."""
    cambio = False
    for clave, info in _disenos(proyecto).items():
        j = _indice(hoja, info.get("col_runid"))
        if j is None: continue
        ids, _ = run_ids(hoja, info, clave); col = hoja.columnas[j]
        if len(col.celdas) < hoja.n: col.celdas.extend([None] * (hoja.n - len(col.celdas)))
        for i, r in enumerate(ids):
            nuevo = r if r else None
            if (col.celdas[i] or None) != nuevo: col.celdas[i] = nuevo; cambio = True
        if col.tipo != "texto" and any(ids): col.tipo = "texto"; cambio = True
        if col.rol != ROL_RUNID: col.rol = ROL_RUNID; col.desc = DESC_RUNID; cambio = True
    return cambio
