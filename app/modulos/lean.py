"""Cálculos Lean de la base LSS (06_FORMULAS_Y_KPIS). Verificados en pruebas/test_lean.py contra 09_EJEMPLOS_CURSO."""
import math

UMBRALES_OEE = {"disponibilidad": 0.90, "eficiencia": 0.95, "calidad": 0.99, "oee": 0.85}   # PL09, TABLERO-OEE


def oee(total, paro_planeado, muerto, capacidad, produccion, rechazo):
    """[BASE] 06_FORMULAS_Y_KPIS, FORM-OEE-CURSO: disponible = total - paro planeado; operativo = disponible -
    muerto; disponibilidad = operativo / disponible; planeada = operativo x capacidad (pz/min);
    eficiencia = producción / planeada; calidad = (producción - rechazo) / producción; OEE = D x E x C."""
    disp = total - paro_planeado
    oper = disp - muerto
    if disp <= 0 or oper < 0 or produccion <= 0 or capacidad <= 0 or rechazo > produccion:
        raise ValueError("Revisa los tiempos y la producción: el tiempo disponible debe ser mayor a cero, el tiempo muerto no puede "
                         "superarlo y el rechazo no puede ser mayor que la producción.")
    planeada = oper * capacidad
    d = oper / disp
    e = produccion / planeada if planeada else 0.0
    c = (produccion - rechazo) / produccion
    return {"disponible": disp, "operativo": oper, "planeada": planeada, "disponibilidad": d, "eficiencia": e,
            "calidad": c, "oee": d * e * c}


def oee_agregado(filas):
    """OEE del turno o semana a partir de varias horas: se suman tiempos y piezas y se recalculan los factores
    (misma fórmula del curso sobre los totales). La producción planeada es la suma de la de cada hora."""
    disp = sum(f["disponible"] for f in filas); oper = sum(f["operativo"] for f in filas)
    plan = sum(f["planeada"] for f in filas); prod = sum(f["produccion"] for f in filas)
    buenas = sum(f["produccion"] - f["rechazo"] for f in filas)
    d = oper / disp if disp else 0.0; e = prod / plan if plan else 0.0; c = buenas / prod if prod else 0.0
    return {"disponibilidad": d, "eficiencia": e, "calidad": c, "oee": d * e * c}


def takt_simple(tiempo_disponible, demanda):
    """[BASE] FORM-TAKT: takt = tiempo disponible / demanda del cliente (mismas unidades de periodo)."""
    return tiempo_disponible / demanda


def takt_curso(demandas_mensuales, dias_laborales, horas_turno, turnos, descanso_min):
    """[BASE] FORM-TAKT-CURSO: tiempo disponible (s) = horas x 3600 x turnos - descansos (min) x turnos x 60;
    demanda diaria = promedio mensual / días laborales; takt (s) = tiempo disponible / demanda diaria."""
    disp = horas_turno * 3600 * turnos - descanso_min * turnos * 60
    prom = sum(demandas_mensuales) / len(demandas_mensuales)
    diaria = prom / dias_laborales
    return {"tiempo_disponible_s": disp, "demanda_promedio": prom, "demanda_diaria": diaria, "takt_s": disp / diaria}


def kanban(promedio, desv, tiempo_entrega_sem, ubicaciones, capacidad):
    """[BASE] FORM-KANBAN: demanda semanal = promedio mensual x 12 / 52; % variación = s / promedio;
    piezas = demanda semanal x entrega (sem) x ubicaciones x (1 + % variación); contenedores = piezas /
    capacidad, redondeado hacia arriba (la base indica redondear; el libro no lo hace)."""
    sem = promedio * 12 / 52
    var = desv / promedio
    piezas = sem * tiempo_entrega_sem * ubicaciones * (1 + var)
    return {"demanda_semanal": sem, "variacion": var, "piezas": piezas, "contenedores": math.ceil(piezas / capacidad - 1e-9)}


def mantenimiento(horas_operacion, fallas, horas_reparacion, reparaciones):
    """[BASE] FORM-MTBF, FORM-MTTR y FORM-DISP-INH (06_FORMULAS_Y_KPIS)."""
    mtbf = horas_operacion / fallas; mttr = horas_reparacion / reparaciones
    return {"mtbf": mtbf, "mttr": mttr, "disp_inherente": mtbf / (mtbf + mttr)}
