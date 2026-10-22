"""Entrega 4: decisiones del proyecto, reglas de decisión e historial de cambios (ESPEC_flujo_real_dmaic, Entrega 4 y criterios 8, 9 y 13).
- Criterio 8: terminar una mejora sin DOE registrando la justificación.
- Criterio 9: recomendar un segundo DOE solo después de revisar la evidencia del primero (respuestas capturadas y un análisis guardado de su respuesta).
- Historial de cambios: lista cronológica de lo que ya queda registrado en el proyecto (versiones de diseño, límites, importaciones, confirmaciones de respuestas,
  omisiones, planes de confirmación y decisiones). Solo lee; no crea registros nuevos.
Una decisión no se borra ni se edita: queda con su motivo y su fecha. D-MIKE no decide por el usuario: registra lo que el usuario declara y comprueba la evidencia."""
from datetime import datetime
from . import disenos as DIS

TIPOS = {"mejora_sin_doe": "Terminar la mejora sin DOE", "segundo_doe": "Recomendar un segundo DOE"}

REGLAS = [
    {"id": "mejora_sin_doe", "titulo": TIPOS["mejora_sin_doe"], "regla": "Se puede terminar una mejora sin DOE. Es obligatorio escribir la justificación; queda registrada con su fecha y no se borra. "
                                                                          "D-MIKE no concluye que la mejora funciona: solo guarda que el usuario decidió no hacer un DOE y por qué.", "fuente": "ESPEC_flujo_real_dmaic, sección 3 y criterio 8"},
    {"id": "segundo_doe", "titulo": TIPOS["segundo_doe"], "regla": "Un segundo DOE solo se recomienda después de revisar la evidencia del primero: el diseño base debe tener respuestas capturadas y un análisis guardado "
                                                                  "de su respuesta. La decisión guarda esa evidencia (análisis, curvatura y falta de ajuste con el nivel de significancia del propio análisis) y el motivo del usuario.", "fuente": "ESPEC_flujo_real_dmaic, criterio 9"},
    {"id": "confirmacion", "titulo": "Confirmación o vigilancia", "regla": "Una confirmación experimental (corridas planeadas antes de implementar) no es lo mismo que la vigilancia posterior a la implementación. "
                                                                         "Cada plan declara su tipo y no se mezclan en la comparación.", "fuente": "ESPEC_flujo_real_dmaic, criterio 13"},
]


def _lista(proyecto): return proyecto.formatos.setdefault("_decisiones", [])


def decisiones(proyecto):
    return [dict(x) for x in (proyecto.formatos.get("_decisiones") or []) if isinstance(x, dict)]


def _ultimo_analisis(proyecto, respuesta):
    for r in reversed(proyecto.resultados or []):
        dg = (r.get("datos") or {}).get("diagnostico")
        if dg and dg.get("respuesta") == respuesta: return r, dg
    return None, None


def registrar_mejora_sin_doe(proyecto, motivo, resultado_uid=None, ahora=None):
    """(estado, mensaje o decisión). «registrada» o «error»."""
    motivo = str(motivo or "").strip()
    if not motivo: return "error", "Escribe la justificación: sin ella no se registra la decisión de terminar la mejora sin DOE."
    ev = None
    if resultado_uid:
        r = next((x for x in proyecto.resultados if x["uid"] == resultado_uid), None)
        if r is None: return "error", "El resultado que citas como evidencia ya no existe en el proyecto."
        ev = {"resultado_uid": resultado_uid, "titulo": r.get("titulo"), "fecha_resultado": r.get("fecha")}
    d = {"id": f"DEC-{len(_lista(proyecto)) + 1:03d}", "tipo": "mejora_sin_doe", "motivo": motivo, "design_id": None, "evidencia": ev,
         "fecha": (ahora or datetime.now()).isoformat(timespec="seconds")}
    _lista(proyecto).append(d)
    return "registrada", d


def recomendar_segundo_doe(proyecto, hoja, design_id, motivo, ahora=None):
    """Registra la recomendación de un segundo DOE solo si el primero tiene respuestas y un análisis guardado. «registrada» o «error»."""
    motivo = str(motivo or "").strip()
    for clave, info in (proyecto.formatos.get("_disenos") or {}).items():
        if DIS.identidad(info, clave)["design_id"] != design_id: continue
        n, _ = DIS.estado_respuestas(hoja, info)
        if n == 0:
            return "error", f"{design_id} no tiene respuestas capturadas: primero corre el diseño e importa sus respuestas. Un segundo DOE se recomienda después de revisar la evidencia del primero."
        r, dg = _ultimo_analisis(proyecto, info.get("respuesta"))
        if r is None:
            return "error", (f"{design_id} tiene respuestas, pero no hay un análisis guardado de «{info.get('respuesta')}». Analízalo (factorial o superficie de respuesta) y revisa la evidencia "
                             "antes de recomendar un segundo DOE.")
        if not motivo: return "error", "Escribe el motivo por el que el primer DOE justifica un segundo: queda registrado junto con la evidencia."
        d = {"id": f"DEC-{len(_lista(proyecto)) + 1:03d}", "tipo": "segundo_doe", "motivo": motivo, "design_id": design_id,
             "evidencia": {"resultado_uid": r["uid"], "titulo": r.get("titulo"), "fecha_resultado": r.get("fecha"), "alfa": dg.get("alfa"),
                           "curvatura_p": dg.get("curvatura_p"), "lof_p": dg.get("lof_p"), "respuestas": n},
             "fecha": (ahora or datetime.now()).isoformat(timespec="seconds")}
        _lista(proyecto).append(d)
        return "registrada", d
    return "error", f"No existe el diseño {design_id}."


def historial(proyecto):
    """Eventos ya registrados en el proyecto, del más reciente al más antiguo: [{fecha, que, detalle, objeto}]. Solo lee."""
    from . import confirmacion as CF
    ev = []

    def add(fecha, que, detalle, objeto=""):
        if fecha: ev.append({"fecha": str(fecha), "que": que, "detalle": detalle, "objeto": objeto})
    for clave, info in (proyecto.formatos.get("_disenos") or {}).items():
        did = DIS.identidad(info, clave)["design_id"]
        for h in info.get("historial_versiones") or []:
            add(h.get("reemplazada_en"), "Versión de diseño", f"Reemplazó la versión {h.get('version')}" + (f". Motivo: {h['motivo']}" if h.get("motivo") else ""), did)
        for h in info.get("historial_limites") or []:
            add(h.get("fecha"), "Límites seguros", "Cambió la región autorizada", did)
        for h in info.get("importaciones") or []:
            add(h.get("fecha") or h.get("importado_en"), "Importación de respuestas", f"{h.get('escritas', '?')} respuestas escritas (versión {h.get('version')})", did)
        for h in info.get("confirmaciones_respuestas") or []:
            add(h.get("fecha"), "Confirmación de respuestas", f"De la versión {h.get('de_version')} a la {h.get('a_version')}. Motivo: {h.get('motivo')}", did)
    for o in DIS.omisiones(proyecto): add(o.get("fecha"), "Paso omitido", f"{o.get('que')}. Motivo: {o.get('motivo')}", o.get("id", ""))
    for p in CF.planes(proyecto): add(p.get("fecha"), "Plan de confirmación", f"{CF.TIPOS[p['tipo']]}, {p['n_corridas']} corridas", p["id"])
    for d in decisiones(proyecto): add(d.get("fecha"), "Decisión", f"{TIPOS.get(d['tipo'], d['tipo'])}. Motivo: {d['motivo']}", d["id"])
    return sorted(ev, key=lambda e: e["fecha"], reverse=True)
