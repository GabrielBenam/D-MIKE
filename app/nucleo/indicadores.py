"""Definiciones versionadas de los indicadores del TABLERO (A2).

Cada indicador guarda su definición como una lista de revisiones en proyecto.formatos["_indicadores"][id]["revisiones"]:
nombre, numerador, denominador, unidad de conteo (texto libre: página, paquete, documento, pieza…), población o filtro, evento de
inicio y de fin (cuando aplique), fecha de vigencia y número de revisión. Si cambia la definición se crea una revisión nueva y la
anterior se conserva sin tocar. Una tendencia que cruza revisiones lleva una nota visible. Es genérico: no trae indicadores ni
estructuras de ningún cliente. Sin cambio de formato de archivo: un .dmike anterior simplemente no tiene la clave «_indicadores».
"""
import uuid
from datetime import date, datetime, timedelta
from .hoja import a_fecha

CLAVE = "_indicadores"
CAMPOS = ["nombre", "numerador", "denominador", "unidad_conteo", "poblacion", "evento_inicio", "evento_fin"]
ETIQUETAS = {"nombre": "Nombre", "numerador": "Numerador", "denominador": "Denominador", "unidad_conteo": "Unidad de conteo",
             "poblacion": "Población o filtro", "evento_inicio": "Evento de inicio", "evento_fin": "Evento de fin"}


def _almacen(proyecto): return proyecto.formatos.setdefault(CLAVE, {})


def revisiones(proyecto, kpi_id):
    """Revisiones de un indicador, de la 1 a la última (lista vacía si no tiene definición)."""
    return list(((proyecto.formatos.get(CLAVE) or {}).get(kpi_id) or {}).get("revisiones") or [])


def nuevo_id():
    return "IND-" + uuid.uuid4().hex[:6].upper()


def _limpio(campos):
    return {k: str((campos or {}).get(k) or "").strip() for k in CAMPOS}


def guardar_definicion(proyecto, kpi_id, campos, vigencia, motivo="", hoy=None):
    """Guarda la definición. Devuelve (estado, mensaje): «nueva» (revisión creada), «sin_cambios» o «error»."""
    nueva = _limpio(campos)
    if not nueva["nombre"]: return "error", "Falta el nombre del indicador."
    if not nueva["numerador"]: return "error", "Falta el numerador: ¿qué se cuenta o se mide?"
    f = a_fecha(str(vigencia or ""))
    if f is None: return "error", "La fecha de vigencia no es válida (usa DD/MM/AAAA o AAAA-MM-DD)."
    previas = revisiones(proyecto, kpi_id)
    if previas:
        ult = previas[-1]
        if all(ult.get(k, "") == nueva[k] for k in CAMPOS):
            return "sin_cambios", "La definición no cambió: no se creó una revisión nueva."
        if f <= a_fecha(ult["vigencia"]):
            return "error", (f"La revisión {len(previas) + 1} debe regir desde una fecha posterior a la de la revisión {ult['revision']} "
                             f"({a_fecha(ult['vigencia']).strftime('%d/%m/%Y')}).")
    rev = {"revision": len(previas) + 1, **nueva, "vigencia": f.isoformat(), "motivo": str(motivo or "").strip(),
           "creada": (hoy or datetime.now()).isoformat(timespec="seconds")}
    _almacen(proyecto).setdefault(kpi_id, {"revisiones": []})["revisiones"].append(rev)
    return "nueva", f"Definición guardada como revisión {rev['revision']} (vigente desde {f.strftime('%d/%m/%Y')})."


def revision_en(revs, fecha):
    """Revisión que rige en una fecha: la última cuya vigencia es anterior o igual; None si la fecha es anterior a la primera."""
    vigente = None
    for r in revs:
        if a_fecha(r["vigencia"]) <= fecha: vigente = r
    return vigente


def revision_por_semana(revs, inicio, ns):
    """Número de revisión de cada semana (rige la del primer día de la semana). None si no hay definición, falta el inicio o la
    semana es anterior a la primera vigencia."""
    if not revs or inicio is None: return [None] * ns
    out = []
    for s in range(ns):
        r = revision_en(revs, inicio + timedelta(days=7 * s))
        out.append(r["revision"] if r else None)
    return out


def nota_cruce(revs, por_semana, vals, nombre=""):
    """Texto visible cuando los valores capturados pertenecen a más de una revisión (o no se puede ubicar la revisión de cada semana)."""
    if len(revs) < 2: return None
    nom = f"«{nombre}»: " if nombre else ""
    if all(r is None for r in por_semana):
        return (f"{nom}tiene {len(revs)} revisiones de definición y no se puede ubicar a cuál pertenece cada semana "
                "(falta el inicio de la semana 1); no asumas que la tendencia es comparable.")
    usadas = sorted({r for r, v in zip(por_semana, vals) if v is not None and r is not None})
    if len(usadas) < 2: return None
    cambio = next(r for r in revs if r["revision"] == usadas[1])
    desde = a_fecha(cambio["vigencia"]).strftime("%d/%m/%Y")
    mot = f" Motivo: {cambio['motivo']}." if cambio.get("motivo") else ""
    return (f"{nom}la tendencia cruza las revisiones {' y '.join(map(str, usadas)) if len(usadas) == 2 else ', '.join(map(str, usadas))} "
            f"de la definición (la {usadas[1]} rige desde {desde}); los valores anteriores y posteriores al cambio no son comparables "
            f"sin revisar qué se modificó.{mot}")


def resumen(proyecto, kpi_id):
    revs = revisiones(proyecto, kpi_id)
    return {"revision": revs[-1]["revision"] if revs else None, "revisiones": revs}
