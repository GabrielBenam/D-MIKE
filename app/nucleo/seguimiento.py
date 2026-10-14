"""Seguimiento del proyecto (D-MIKE 0.27, Entrega 2; ESPEC_receta_v2.md secciones 12 y 13).

Todo vive dentro de proyecto.formatos (version_formato sigue en 1): «_variables», «_tareas», «_analisis», «_revisiones»; «_receta» suma
«revision», «huella» y «aplicada_en». Un .dmike de 0.26 abre sin estas claves; uno de 0.27 abre en 0.26 y las ignora.

Reglas que no se rompen: un estado verificado nunca baja en silencio; una tarea cerrada no se reabre sola; un análisis nunca queda
«analizado» sin resultado; ningún cambio de receta borra la receta anterior (pasa a «_revisiones»); el paquete de avance lleva solo estado."""
import json
from datetime import datetime
from . import receta as RC, modo as MD

TOPE_REVISIONES = 20
VERIFICADO = "REAL_VERIFICADO"
CAMPOS_VARIABLE = ("hoja", "unidad", "unidad_analisis", "fuente", "responsable")
RUTA = ("Sin datos", "Historicos cargados", "DOE disenado", "DOE ejecutado")
NO_DETERMINADO = "no_determinado"


def _ahora(): return datetime.now().isoformat(timespec="seconds")
def _lista(v): return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


# ---------------- columnas de la hoja ----------------
def _nombre_col(x): return str(x)[1:] if str(x).startswith("@") else str(x)


def col_con_datos(hoja, nombre):
    j = hoja.indice(nombre)
    return j is not None and any(hoja.columnas[j].valor(i)[2] is not None for i in range(hoja.n))


def sin_datos(hoja, requiere):
    """(faltan, vacias): columnas «@x» que no existen en la hoja y las que existen sin ningún dato."""
    faltan, vacias = [], []
    for x in requiere or []:
        n = _nombre_col(x)
        if hoja.indice(n) is None: faltan.append(n)
        elif not col_con_datos(hoja, n): vacias.append(n)
    return faltan, vacias


def motivo_columnas(faltan, vacias):
    t = []
    if faltan: t.append(("Falta la columna " if len(faltan) == 1 else "Faltan las columnas ") + ", ".join(faltan))
    if vacias: t.append("Sin datos en " + ", ".join(vacias))
    return "; ".join(t) + "." if t else ""


# ---------------- variables (12.2) ----------------
def conflictos_variables(proyecto, nuevas):
    """Variables que bajarían de REAL_VERIFICADO a otro estado. Nunca ocurre en silencio: se trata como conflicto de revisión (12.5)."""
    previas = {v.get("nombre"): v for v in _lista(proyecto.formatos.get("_variables"))}
    out = []
    for v in _lista(nuevas):
        p = previas.get(v.get("nombre"))
        nuevo = v.get("estado_evidencia")
        if p and p.get("estado_evidencia") == VERIFICADO and nuevo is not None and nuevo != VERIFICADO:
            out.append({"nombre": v["nombre"], "actual": VERIFICADO, "recibido": nuevo})
    return out


def fusionar_variables(proyecto, nuevas):
    """Fusiona por nombre. El estado nuevo reemplaza al previo salvo que el previo sea REAL_VERIFICADO y el nuevo no (se conserva y se avisa).
    El resto de los campos se actualiza cuando la receta los trae; las variables que la receta ya no menciona se conservan."""
    lista = _lista(proyecto.formatos.get("_variables")); por_nombre = {v.get("nombre"): v for v in lista}
    baja = {c["nombre"] for c in conflictos_variables(proyecto, nuevas)}; avisos = []
    for v in _lista(nuevas):
        nom = v.get("nombre")
        if not isinstance(nom, str) or not nom.strip(): continue
        reg = por_nombre.get(nom)
        if reg is None:
            reg = {"nombre": nom, "hoja": "", "unidad": "", "unidad_analisis": "", "fuente": "", "responsable": "", "estado_evidencia": None, "ensayo_destructivo": False}
            lista.append(reg); por_nombre[nom] = reg
        for k in CAMPOS_VARIABLE:
            if v.get(k) not in (None, ""): reg[k] = v[k]
        if isinstance(v.get("ensayo_destructivo"), bool): reg["ensayo_destructivo"] = v["ensayo_destructivo"]
        if v.get("estado_evidencia") is not None:
            if nom in baja: avisos.append(f"Variable «{nom}»: se conservó REAL_VERIFICADO; la receta traía {v['estado_evidencia']} y un estado verificado no baja en silencio.")
            else: reg["estado_evidencia"] = v["estado_evidencia"]
    proyecto.formatos["_variables"] = lista
    return avisos


# ---------------- tareas (12.3) ----------------
def id_auto(tipo, objeto): return f"auto:{tipo}:{objeto}"


def fusionar_tareas_receta(proyecto, tareas):
    """Fusiona por id las tareas de la receta (origen «receta»). Una tarea cerrada no se reabre; las tareas de la receta se conservan siempre."""
    lista = _lista(proyecto.formatos.get("_tareas")); por_id = {t.get("id"): t for t in lista}
    for t in _lista(tareas):
        tid = t.get("id")
        if not isinstance(tid, str) or not tid.strip(): continue
        previa = por_id.get(tid)
        nueva = {"id": tid, "descripcion": t.get("descripcion") or "", "responsable": t.get("responsable") or "", "accion": t.get("accion") or "",
                 "liga": t.get("liga") or "", "estado": t.get("estado") or "abierta", "origen": "receta"}
        if previa is None: lista.append(nueva); por_id[tid] = nueva; continue
        cerrada = previa.get("estado") == "cerrada" or nueva["estado"] == "cerrada"
        previa.update(nueva); previa["estado"] = "cerrada" if cerrada else "abierta"
    proyecto.formatos["_tareas"] = lista


def registrar_pendientes(proyecto, pendientes):
    """Los pendientes que ejecutar() devolvía como texto pasan a tareas «auto» con id estable auto:<tipo>:<objeto> y el mismo texto.
    Una tarea auto ya cerrada no se reabre; una abierta solo refresca su texto."""
    lista = _lista(proyecto.formatos.get("_tareas")); por_id = {t.get("id"): t for t in lista}
    for p in pendientes:
        tid = id_auto(p["tipo"], p["objeto"]); previa = por_id.get(tid)
        if previa is None:
            t = {"id": tid, "descripcion": p["texto"], "responsable": "", "accion": p["accion"], "liga": p["liga"], "estado": "abierta", "origen": "auto"}
            lista.append(t); por_id[tid] = t
        elif previa.get("estado") == "abierta": previa["descripcion"] = p["texto"]
    proyecto.formatos["_tareas"] = lista


def filas_diseno(hoja, d):
    """Filas de la hoja que ocupa un diseño de la receta (las que tienen valor en su primer factor); None si no se puede determinar."""
    nombres = [x.strip() for x in str((d.get("parametros") or {}).get("nombres") or "").replace(";", ",").split(",") if x.strip()]
    j = hoja.indice(nombres[0]) if nombres else None
    if j is None: return None
    return [i for i in range(hoja.n) if hoja.columnas[j].valor(i)[2] is not None]


def respuesta_completa(hoja, filas, resp):
    j = hoja.indice(resp)
    return bool(filas) and j is not None and all(hoja.columnas[j].valor(i)[2] is not None for i in filas)


def _buscar(recetas, clave, ident, campo):
    for rc in recetas:
        for x in _lista((rc or {}).get(clave)):
            if x.get(campo) == ident: return x
    return None


def _cumple(t, hoja, analisis, recetas):
    """¿Ya se cumplió la condición de una tarea auto? hoja: datos en todas sus columnas; diseno/respuesta: respuestas capturadas en todas las corridas;
    analisis: el análisis tiene resultado."""
    try: _, tipo, objeto = t["id"].split(":", 2)
    except (KeyError, ValueError, AttributeError): return False
    if tipo == "hoja":
        h = _buscar(recetas, "hojas", objeto, "hoja")
        cols = [c.get("nombre") for c in _lista((h or {}).get("columnas"))]
        return bool(cols) and all(col_con_datos(hoja, n) for n in cols if n)
    if tipo in ("diseno", "respuesta"):
        did, _, resp = objeto.partition(":") if tipo == "respuesta" else (objeto, "", "")
        d = _buscar(recetas, "disenos", did, "id")
        if d is None: return False
        filas = filas_diseno(hoja, d)
        resps = [resp] if tipo == "respuesta" else [r for r in d.get("respuestas") or [] if isinstance(r, str)]
        return bool(resps) and all(respuesta_completa(hoja, filas, r) for r in resps)
    if tipo == "analisis":
        return (analisis.get(objeto) or {}).get("estado") in ("analizado", "aprobado")
    return False


def cerrar_cumplidas(proyecto, hoja, *recetas):
    """Cierra las tareas auto abiertas cuya condición ya se cumple. Devuelve los ids cerrados. Nunca reabre."""
    analisis = evaluar_analisis(proyecto, hoja); cerradas = []
    for t in _lista(proyecto.formatos.get("_tareas")):
        if t.get("origen") == "auto" and t.get("estado") == "abierta" and _cumple(t, hoja, analisis, recetas):
            t["estado"] = "cerrada"; cerradas.append(t["id"])
    return cerradas


# ---------------- estado de cada análisis (12.4) ----------------
def requiere_de(p):
    """Columnas «@x» que necesita un análisis de la receta: las declaradas en «requiere» más las que cita en sus parámetros."""
    decl = [x for x in (p.get("requiere") or []) if isinstance(x, str)]
    citadas = RC._columnas_citadas(p.get("parametros") or {})
    return list(dict.fromkeys(decl + citadas))


def registrar_analisis(proyecto, aid, modulo, estado, requiere, motivo="", uid=None, bloqueado=False):
    reg = proyecto.formatos.setdefault("_analisis", {})
    e = {"modulo": modulo, "estado": estado, "requiere": list(requiere), "motivo": motivo, "uid": uid}
    if bloqueado: e["bloqueado"] = True       # pendiente por una causa que no son las columnas (falta un resultado previo o el módulo rechazó los datos)
    reg[aid] = e


def evaluar_analisis(proyecto, hoja):
    """Estado vigente de cada análisis, calculado contra la hoja y los resultados actuales (no escribe nada).
    analizado solo si el resultado existe; pendiente si falta una columna @x o no tiene datos; disponible si hay datos y aún no se corrió."""
    uids = {r.get("uid") for r in proyecto.resultados}; out = {}
    for aid, e in (proyecto.formatos.get("_analisis") or {}).items():
        if not isinstance(e, dict): continue
        e = dict(e)
        if e.get("uid") in uids:
            e["estado"] = "aprobado" if e.get("estado") == "aprobado" else "analizado"; e["motivo"] = ""
        else:
            faltan, vacias = sin_datos(hoja, e.get("requiere"))
            if faltan or vacias: e["estado"], e["motivo"] = "pendiente", motivo_columnas(faltan, vacias)
            elif e.get("bloqueado"): e["estado"] = "pendiente"
            else: e["estado"], e["motivo"] = "disponible", "Hay datos; falta correr el análisis."
        out[aid] = e
    return out


# ---------------- revisiones (12.5) ----------------
def aplicada(proyecto):
    """Última revisión aplicada al proyecto: {revision, huella, huellas}. Un .dmike de 0.26 sin esas claves las toma del JSON de «_receta»."""
    rec = proyecto.formatos.get("_receta")
    rec = rec if isinstance(rec, dict) else {}
    rev, h = RC.entero(rec.get("revision")), rec.get("huella")
    if (rev is None or h is None) and rec.get("json"):
        try: rc = json.loads(rec["json"])
        except (ValueError, TypeError): rc = None
        if isinstance(rc, dict):
            if rev is None: rev = RC.entero(rc.get("revision"))
            if h is None: h = RC.huella_efectiva(rc)
    huellas = {h} if h else set()
    huellas |= {e.get("huella") for e in _lista(proyecto.formatos.get("_revisiones")) if e.get("huella")}
    return {"revision": rev, "huella": h, "huellas": huellas}


def datos_nuevos(hoja, receta, datos):
    """¿El archivo trae datos que la hoja del proyecto aún no tiene? (columna con valores en el archivo y ausente o vacía en la hoja)."""
    for h in _lista(receta.get("hojas")):
        filas = (datos or {}).get(h.get("hoja"))
        if not filas or len(filas) < 2: continue
        cab = [str(x).strip() if x is not None else "" for x in filas[0]]
        for c, nombre in enumerate(cab):
            if nombre and any(c < len(f) and f[c] not in (None, "") for f in filas[1:]) and not col_con_datos(hoja, nombre): return True
    return False


def decidir_revision(proyecto, hoja, receta, datos=None, forzar=False):
    """Control de revisión al actualizar un proyecto (12.5). Devuelve {accion, motivo, recibida, aplicada, base, variables} con accion en
    «aplicar», «ya_aplicada», «mas_antigua» o «conflicto». No cambia nada."""
    ap = aplicada(proyecto); n = ap["revision"]; r = RC.entero(receta.get("revision")); base = receta.get("revision_base")
    out = {"accion": "aplicar", "motivo": "", "recibida": r, "aplicada": n, "base": base, "variables": conflictos_variables(proyecto, receta.get("variables"))}
    if RC.huella_efectiva(receta) in ap["huellas"]:
        if not datos_nuevos(hoja, receta, datos):
            return {**out, "accion": "ya_aplicada", "motivo": "La receta ya estaba aplicada (misma huella): no se cambió nada."}
        # la misma receta con mediciones que el proyecto aún no tiene (la forma normal de cargar los datos): se agregan solo esas, sin tocar la revisión
        return {**out, "motivo": "La receta ya estaba aplicada; se agregan solo los datos nuevos del archivo."}
    if r is not None and n is not None and r <= n and not forzar:
        return {**out, "accion": "mas_antigua", "motivo": f"La receta es más antigua: trae la revisión {r} y el proyecto ya tiene aplicada la {n}. No se aplicó."}
    if r is not None and (n is None or r > n) and base != n:
        return {**out, "accion": "conflicto",
                "motivo": f"Conflicto de revisión: la receta (revisión {r}) se construyó sobre la revisión {base if base is not None else 'ninguna'}, "
                          f"pero el proyecto tiene aplicada la revisión {n if n is not None else 'ninguna'}."}
    if out["variables"]:
        nombres = ", ".join(c["nombre"] for c in out["variables"])
        return {**out, "accion": "conflicto", "motivo": f"Conflicto: la receta bajaría de REAL_VERIFICADO a otro estado la evidencia de: {nombres}."}
    return out


def archivar_receta_previa(proyecto, receta_nueva):
    """Antes de reemplazar «_receta», la anterior pasa a «_revisiones» con su huella (tope 20). Devuelve avisos."""
    rec = proyecto.formatos.get("_receta")
    if not isinstance(rec, dict) or not rec.get("json"): return []
    ap = aplicada(proyecto)
    if ap["huella"] is not None and ap["huella"] == RC.huella_efectiva(receta_nueva): return []         # misma receta: nada que archivar
    revs = _lista(proyecto.formatos.get("_revisiones"))
    revs.append({"revision": ap["revision"], "huella": ap["huella"], "aplicada_en": rec.get("aplicada_en"), "origen": rec.get("origen") or "", "receta": rec["json"]})
    avisos = []
    if len(revs) > TOPE_REVISIONES:
        fuera, revs = revs[:len(revs) - TOPE_REVISIONES], revs[len(revs) - TOPE_REVISIONES:]
        avisos.append(f"Historial de revisiones: se descartó {len(fuera)} revisión(es) más antigua(s) (tope de {TOPE_REVISIONES}).")
    proyecto.formatos["_revisiones"] = revs
    return avisos


# ---------------- vista y paquete de avance (13) ----------------
def _receta_guardada(proyecto):
    rec = proyecto.formatos.get("_receta")
    try: rc = json.loads(rec.get("json") or "{}") if isinstance(rec, dict) else {}
    except (ValueError, TypeError): rc = {}
    return rc if isinstance(rc, dict) else {}


def vista(proyecto, hoja):
    """Solo lectura (E2-R9): variables con su estado, tareas abiertas y estado de cada análisis."""
    an = evaluar_analisis(proyecto, hoja); tareas = _lista(proyecto.formatos.get("_tareas")); ap = aplicada(proyecto)
    return {"revision": ap["revision"], "huella": ap["huella"], "revisiones_guardadas": len(_lista(proyecto.formatos.get("_revisiones"))),
            "variables": [{k: v.get(k) for k in ("nombre", "hoja", "unidad", "estado_evidencia", "ensayo_destructivo")} for v in _lista(proyecto.formatos.get("_variables"))],
            "tareas_abiertas": [{k: t.get(k) for k in ("id", "descripcion", "responsable", "accion", "origen")} for t in tareas if t.get("estado") == "abierta"],
            "tareas_cerradas": sum(1 for t in tareas if t.get("estado") == "cerrada"),
            "analisis": [{"id": k, "modulo": e.get("modulo"), "estado": e["estado"], "motivo": e.get("motivo") or ""} for k, e in an.items()]}


def disenos_estado(proyecto, hoja):
    """Diseños de la receta que D-MIKE ya creó: id, estado (creado o ejecutado), corridas y respuestas capturadas completas."""
    ids = (proyecto.formatos.get("_receta") or {}).get("ids") or {}; out = []
    for d in _lista(_receta_guardada(proyecto).get("disenos")):
        if d.get("id") not in ids: continue
        filas = filas_diseno(hoja, d); resps = [r for r in d.get("respuestas") or [] if isinstance(r, str)]
        capt = sum(1 for r in resps if respuesta_completa(hoja, filas, r))
        out.append({"id": d["id"], "estado": "ejecutado" if resps and capt == len(resps) else "creado",
                    "corridas": len(filas) if filas is not None else None, "respuestas_capturadas": capt})
    return out


def estado_ruta(proyecto, hoja, disenos=None):
    """Solo lo que se deduce de la existencia de objetos (13): Sin datos, Historicos cargados, DOE disenado o DOE ejecutado; lo demás, no_determinado."""
    disenos = disenos_estado(proyecto, hoja) if disenos is None else disenos
    if any(d["estado"] == "ejecutado" for d in disenos): return "DOE ejecutado"
    if disenos: return "DOE disenado"
    if any(col_con_datos(hoja, c.nombre) for c in hoja.columnas if c.nombre): return "Historicos cargados"
    if not any(c.celdas and any(v not in (None, "") for v in c.celdas) for c in hoja.columnas): return "Sin datos"
    return NO_DETERMINADO


MOTIVO_SIN_ID = ("El proyecto no tiene id_proyecto. El id_proyecto lo trae una receta v2 del diagnóstico en línea; este proyecto viene de una receta v1 "
                 "o se creó sin receta, y sin ese identificador la web no puede saber a qué proyecto pertenece el avance.")


def _descripcion_exportable(t):
    """Texto de una tarea para el paquete: el de la receta o el generado por D-MIKE a partir de nombres. Las tareas auto de análisis llevan el mensaje
    del módulo, que podría citar datos de celdas: se sustituyen por un texto fijo."""
    if t.get("origen") == "auto" and str(t.get("id", "")).startswith("auto:analisis:"):
        return f"Análisis «{t['id'].split(':', 2)[2]}» pendiente: faltan datos o correrlo."
    return t.get("descripcion") or ""


def paquete_avance(proyecto, hoja):
    """(paquete, None) o (None, motivo). Solo estado: sin datos de hojas, sin valores medidos y sin resultados numéricos."""
    rec = proyecto.formatos.get("_receta")
    idp = rec.get("id_proyecto") if isinstance(rec, dict) else None
    if not idp: return None, MOTIVO_SIN_ID
    an = evaluar_analisis(proyecto, hoja); ap = aplicada(proyecto); dis = disenos_estado(proyecto, hoja)
    pkg = {"tipo": "dmike-avance", "avance_version": 1, "id_proyecto": idp, "modo_proyecto": MD.valor(proyecto), "revision_aplicada": ap["revision"],
           "generado_en": _ahora(), "huella": "", "fase_actual": proyecto.fase_actual(), "estado_ruta": estado_ruta(proyecto, hoja, dis),
           "variables": [{"nombre": v.get("nombre"), "estado_evidencia": v.get("estado_evidencia")} for v in _lista(proyecto.formatos.get("_variables"))],
           "analisis": [{"id": k, "modulo": e.get("modulo"), "estado": e["estado"]} for k, e in an.items()],
           "disenos": dis,
           "tareas_abiertas": [{"id": t["id"], "descripcion": _descripcion_exportable(t)} for t in _lista(proyecto.formatos.get("_tareas")) if t.get("estado") == "abierta"]}
    pkg["huella"] = RC.huella_receta(pkg)
    return pkg, None


def huella_avance_valida(pkg):
    """La huella del paquete se calcula igual que la de la receta (JSON canónico sin el campo «huella»)."""
    return isinstance(pkg, dict) and pkg.get("huella") == RC.huella_receta(pkg)
