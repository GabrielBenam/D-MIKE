"""E3-9: plan de confirmación (ESPEC_flujo_real_dmaic sección 3 y criterios 11 y 13). El usuario registra un plan con su tipo (confirmación experimental o vigilancia
posterior a la implementación), el número de corridas, el criterio de éxito y las condiciones, y el valor predicho con su origen. D-MIKE no inventa el tamaño
de muestra ni el criterio de éxito. Después se capturan las observaciones y la comparación muestra siempre observado menos predicho.
El intervalo de predicción solo se añade donde la base lo respalda: regresión simple (27_BB_REGRESION, REG-PREDICCION), para una observación individual.
Para modelos múltiples o de superficie dice «no respaldado» y no da veredicto."""
from datetime import datetime
import numpy as np
from ..modulos import regresion as R

TIPOS = {"confirmacion": "Confirmación experimental", "vigilancia": "Vigilancia posterior a la implementación"}
F_INTERVALO = "27_BB_REGRESION: REG-PREDICCION (regresión simple, observación individual)"
NO_RESPALDADO = ("No respaldado por la base: el intervalo de predicción de 27_BB REG-PREDICCION es de regresión simple y de una observación individual; "
                 "para este tipo de modelo no se calcula y no hay veredicto.")


def _lista(proyecto): return proyecto.formatos.setdefault("_confirmaciones", [])


def planes(proyecto, design_id=None):
    return [dict(x) for x in (proyecto.formatos.get("_confirmaciones") or []) if isinstance(x, dict) and (design_id is None or x.get("design_id") == design_id)]


def _numero(v):
    try:
        x = float(str(v).strip().replace(",", ".")); return x if np.isfinite(x) else None
    except (TypeError, ValueError): return None


def registrar_plan(proyecto, tipo, n_corridas, criterio, condiciones, origen, design_id=None, predicho=None, resultado_uid=None, x0=None, ahora=None):
    """(estado, mensaje o plan). estado «registrado» o «error». Con resultado_uid de una regresión simple, el valor predicho se calcula con ella en x0; en otro caso el
    usuario da el valor predicho a mano y su origen."""
    if tipo not in TIPOS: return "error", f"Tipo de plan: elige uno de {', '.join(TIPOS)}."
    try: n = int(str(n_corridas).strip())
    except (TypeError, ValueError): n = 0
    if n < 1: return "error", "El número de corridas lo defines tú y debe ser un entero de 1 o más: D-MIKE no propone un tamaño de muestra."
    criterio, condiciones, origen = (str(x or "").strip() for x in (criterio, condiciones, origen))
    if not criterio: return "error", "Escribe el criterio de éxito: lo defines tú; D-MIKE no propone uno."
    if not condiciones: return "error", "Escribe las condiciones de la confirmación (proceso, lote, equipo, ajustes)."
    if not origen: return "error", "Escribe de dónde sale el valor predicho (por ejemplo, el análisis o el modelo que lo dio)."
    from . import disenos as DIS
    if design_id is not None and not any(DIS.identidad(i, k)["design_id"] == design_id for k, i in (proyecto.formatos.get("_disenos") or {}).items()):
        return "error", f"No existe el diseño {design_id}."
    modelo = None
    if resultado_uid:
        r = next((x for x in proyecto.resultados if x["uid"] == resultado_uid), None)
        if r is None: return "error", "El resultado del que sale el valor predicho ya no existe en el proyecto."
        modelo = (r.get("datos") or {}).get("modelo_reg")
    if modelo:
        xv = _numero(x0)
        if xv is None: return "error", f"Para predecir con la regresión de {modelo['respuesta']} indica el valor de {modelo['predictor']} de la confirmación."
        q = R.predecir(_reconstruir(modelo), [xv]); pred = q["pred"]; tipo_modelo = "regresion_simple"
        extrap = not (modelo["x_min"] <= xv <= modelo["x_max"])
    else:
        pred = _numero(predicho)
        if pred is None: return "error", "Escribe el valor predicho (un número)."
        tipo_modelo = "otro"; xv = None; extrap = False
    plan = {"id": f"CONF-{len(_lista(proyecto)) + 1:03d}", "tipo": tipo, "design_id": design_id, "n_corridas": n, "criterio_exito": criterio, "condiciones": condiciones,
            "predicho": {"valor": pred, "origen": origen, "resultado_uid": resultado_uid, "tipo_modelo": tipo_modelo, "x0": xv, "extrapolacion": extrap},
            "observados": [], "fecha": (ahora or datetime.now()).isoformat(timespec="seconds")}
    _lista(proyecto).append(plan)
    return "registrado", plan


def registrar_observados(proyecto, plan_id, valores, ahora=None):
    """Agrega observaciones al plan (números). No pasa del número de corridas del plan. Devuelve (estado, mensaje): «registrado» o «error»."""
    plan = next((x for x in _lista(proyecto) if x.get("id") == plan_id), None)
    if plan is None: return "error", f"No existe el plan {plan_id}."
    texto = ";".join(str(v) for v in valores) if isinstance(valores, (list, tuple)) else str(valores or "")
    # separador: «;» o salto de línea (así la coma puede ser decimal: 57,1); si no hay ninguno, la coma separa y el decimal es el punto
    sep = ";" if (";" in texto or "\n" in texto) else ","
    partes = [t for t in texto.replace("\n", ";").split(sep) if t.strip()]
    nuevos = [_numero(t) for t in partes]
    if not nuevos or any(v is None for v in nuevos): return "error", "Escribe las observaciones como números separados por punto y coma (o por coma si usas punto decimal)."
    if len(plan["observados"]) + len(nuevos) > plan["n_corridas"]:
        return "error", f"El plan {plan_id} prevé {plan['n_corridas']} corridas y ya tiene {len(plan['observados'])}: no caben {len(nuevos)} más."
    plan["observados"] += nuevos
    return "registrado", f"Registradas {len(nuevos)} observaciones en {plan_id} ({len(plan['observados'])} de {plan['n_corridas']})."


def _reconstruir(m):
    return {"constante": m["constante"], "b": np.array(m["b"], float), "xtx_inv": np.array(m["xtx_inv"], float), "mce": m["mce"], "tc": m["tc"]}


def comparar(proyecto, plan_id):
    """(comparación, None) o (None, motivo). Muestra siempre observado menos predicho; el intervalo de predicción solo en regresión simple."""
    plan = next((x for x in planes(proyecto) if x["id"] == plan_id), None)
    if plan is None: return None, f"No existe el plan {plan_id}."
    pr = plan["predicho"]; obs = plan["observados"]
    out = {"id": plan["id"], "tipo": TIPOS[plan["tipo"]], "design_id": plan["design_id"], "n_corridas": plan["n_corridas"], "criterio_exito": plan["criterio_exito"],
           "condiciones": plan["condiciones"], "predicho": pr["valor"], "origen": pr["origen"], "observados": obs, "faltan": plan["n_corridas"] - len(obs),
           "diferencias": [v - pr["valor"] for v in obs], "media": float(np.mean(obs)) if obs else None,
           "diferencia_media": (float(np.mean(obs)) - pr["valor"]) if obs else None, "intervalo": None, "fuera_del_intervalo": None, "nota_intervalo": None, "avisos": []}
    if pr["tipo_modelo"] == "regresion_simple":
        r = next((x for x in proyecto.resultados if x["uid"] == pr["resultado_uid"]), None)
        modelo = (r or {}).get("datos", {}).get("modelo_reg")
        if modelo is None: out["nota_intervalo"] = "El resultado de la regresión ya no está en el proyecto: no se puede calcular el intervalo de predicción."
        else:
            q = R.predecir(_reconstruir(modelo), [pr["x0"]]); lo, hi = q["ip"]
            out["intervalo"] = {"inferior": lo, "superior": hi, "nivel": 1 - modelo["alfa"], "fuente": F_INTERVALO}
            out["fuera_del_intervalo"] = [not (lo <= v <= hi) for v in obs]
            out["nota_intervalo"] = (f"Intervalo de predicción individual al {100 * (1 - modelo['alfa']):.0f}% (REG-PREDICCION) para {modelo['predictor']} = {pr['x0']:g}. "
                                     "Es el de una observación individual: con varias observaciones se mira cada una, no su promedio. El criterio de éxito sigue siendo el tuyo.")
            if pr["extrapolacion"]: out["avisos"].append("El valor de la confirmación está fuera del rango de los datos de la regresión: es una extrapolación.")
    else:
        out["nota_intervalo"] = NO_RESPALDADO
    return out, None
