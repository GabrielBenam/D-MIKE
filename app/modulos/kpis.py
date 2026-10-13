"""Catálogo de indicadores para el tablero. Cada indicador es un objeto configurable (no una pieza de interfaz):
el tablero muestra los que el usuario elige y el resto queda en el catálogo.

fuente «BASE ...» = fórmula de la base LSS (archivo, bloque). fuente «GENERAL» = rubro del catálogo ampliado de
manufactura (sugerido por el usuario a partir de una consulta externa); su fórmula y meta las define el proyecto
(06_FORMULAS_Y_KPIS, KPI-FAMILIAS: «las metas de cada KPI las define el proyecto»)."""

B = "BASE 06_FORMULAS_Y_KPIS"
_BASE = [
    ("OEE", "OEE", "Equipo", "%", ">=", "Disponibilidad x Eficiencia x Calidad; umbral mínimo del tablero del curso 85%", f"{B}, FORM-OEE-CURSO; PL09"),
    ("DISPONIBILIDAD", "Disponibilidad", "Equipo", "%", ">=", "Tiempo operativo / tiempo disponible; umbral 90%", f"{B}, FORM-OEE-CURSO"),
    ("EFICIENCIA", "Eficiencia (desempeño)", "Equipo", "%", ">=", "Producción total / producción planeada; umbral 95%", f"{B}, FORM-OEE-CURSO"),
    ("CALIDAD-OEE", "Calidad (factor del OEE)", "Equipo", "%", ">=", "Producción aprobada / producción total; umbral 99%", f"{B}, FORM-OEE-CURSO"),
    ("MTBF", "MTBF", "Equipo", "h", ">=", "Tiempo total de operación / número de fallas", f"{B}, FORM-MTBF"),
    ("MTTR", "MTTR", "Equipo", "h", "<=", "Tiempo total de reparación / número de reparaciones", f"{B}, FORM-MTTR"),
    ("DISP-INH", "Disponibilidad inherente", "Equipo", "%", ">=", "MTBF / (MTBF + MTTR)", f"{B}, FORM-DISP-INH"),
    ("PRODUCTIVIDAD", "Productividad", "Velocidad", "salidas/entradas", ">=", "Salidas / entradas", f"{B}, FORM-PRODUCTIVIDAD"),
    ("TAKT", "Takt time", "Velocidad", "s/pieza", "<=", "Tiempo disponible / demanda del cliente", f"{B}, FORM-TAKT"),
    ("CICLO", "Tiempo de ciclo", "Velocidad", "s/unidad", "<=", "Tiempo real para completar una unidad; se compara con el takt", f"{B}, FORM-CICLO"),
    ("LEADTIME", "Lead time", "Velocidad", "días", "<=", "WIP / tasa de salida (ley de Little)", f"{B}, FORM-LEADTIME"),
    ("PCE", "Eficiencia del ciclo del proceso (PCE)", "Velocidad", "%", ">=", "Tiempo de valor agregado / lead time", f"{B}, FORM-PCE"),
    ("WIP", "Trabajo en proceso (WIP)", "Velocidad", "unidades", "<=", "Unidades en proceso", f"{B}, FORM-LEADTIME"),
    ("ROTACION-INV", "Vueltas de inventario", "Velocidad", "vueltas/año", ">=", "Días laborables al año / tiempo de puerta a puerta", f"{B}, FORM-RESULTADOS"),
    ("ENTREGAS-TIEMPO", "Entregas a tiempo", "Cliente", "%", ">=", "Entregas a tiempo / entregas totales", "BASE 06_FORMULAS_Y_KPIS, KPI-FAMILIAS (fórmula general)"),
    ("NIVEL-SIGMA", "Nivel sigma", "Calidad", "sigma", ">=", "Z de largo plazo + 1.5", "BASE 25_BB_DISTRIBUCIONES, DIST-IDENTIFICAR; 16_GB CAP-NIVEL-SIGMA"),
    ("DPMO", "DPMO", "Calidad", "defectos por millón", "<=", "Defectos / (unidades x oportunidades) x 1,000,000", "BASE 16_GB_HISTOGRAMAS_CAPACIDAD_DESEMPENO, DES-DPMO"),
    ("COPQ", "Costo de pobre calidad", "Calidad", "$", "<=", "Suma de costos de fallas internas y externas, evaluación y prevención", "BASE 06_FORMULAS_Y_KPIS, KPI-FAMILIAS"),
    ("ROI", "ROI", "Financieros", "%", ">=", "Beneficio / inversión", "BASE 06_FORMULAS_Y_KPIS, KPI-FAMILIAS; 23_BB_EVALUACION_FINANCIERA"),
    ("RONA", "RONA", "Financieros", "%", ">=", "Utilidad neta / activos netos", "BASE 06_FORMULAS_Y_KPIS, KPI-FAMILIAS"),
    ("COSTO-CONV", "Costo de conversión", "Financieros", "$", "<=", "Costo de transformar materia prima en producto", "BASE 06_FORMULAS_Y_KPIS, KPI-FAMILIAS"),
    ("UTILIDAD", "Utilidad por unidad", "Financieros", "$/unidad", ">=", "Precio - costo", f"{B}, FORM-UTILIDAD"),
    ("NPS", "NPS (Net Promoter Score)", "Cliente", "%", ">=", "% promotores - % detractores", "BASE 06_FORMULAS_Y_KPIS, KPI-FAMILIAS"),
    ("RPN-MAX", "RPN máximo del AMEF", "Calidad", "RPN", "<=", "Severidad x ocurrencia x detección", f"{B}, FORM-RPN"),
    ("SEGURIDAD", "Incidentes de seguridad", "Personas y entorno", "eventos", "<=", "Conteo por periodo", "BASE 06_FORMULAS_Y_KPIS, KPI-FAMILIAS"),
]

_GENERAL = {
    "Producción": ["Unidades producidas:unidades:>=", "Unidades buenas producidas:unidades:>=", "Cumplimiento del plan de producción:%:>=",
                   "Producción por hora:unidades/h:>=", "Producción por turno:unidades:>=", "Producción por operador:unidades:>=",
                   "Tiempo medio por unidad:min:<=", "Desviación del tiempo de ciclo:%:<=", "Throughput:unidades/h:>=",
                   "Tiempo de espera:min:<=", "Tiempo de setup:min:<=", "Órdenes terminadas:órdenes:>=", "Órdenes atrasadas:órdenes:<=",
                   "Utilización de capacidad:%:>=", "Horas improductivas:h:<="],
    "Equipo": ["Tiempo muerto:min:<=", "Paros no planificados:min:<=", "Número de paros:paros:<=", "Duración media del paro:min:<=",
               "Microparos:paros:<="],
    "Calidad": ["Defectos por unidad:defectos/unidad:<=", "Tasa de defectos:%:<=", "PPM:ppm:<=", "First Pass Yield (FPY):%:>=",
                "Rolled Throughput Yield (RTY):%:>=", "Scrap:%:<=", "Retrabajos:%:<=", "Tasa de rechazo:%:<=",
                "No conformidades abiertas:NC:<=", "Tiempo medio de cierre de NC:días:<=", "CAPA abiertas:CAPA:<=", "CAPA vencidas:CAPA:<=",
                "Quejas del cliente:quejas:<=", "Devoluciones:%:<="],
    "Control estadístico": ["Cp:índice:>=", "Cpk:índice:>=", "Pp:índice:>=", "Ppk:índice:>=", "Puntos fuera de control:puntos:<=",
                            "Porcentaje fuera de especificación:%:<="],
    "Mantenimiento": ["Cumplimiento del mantenimiento preventivo:%:>=", "Backlog de mantenimiento:órdenes:<=",
                      "Órdenes de mantenimiento vencidas:órdenes:<=", "Costo de mantenimiento:$:<=", "Fallas repetitivas:fallas:<="],
    "Entrega y logística": ["OTIF:%:>=", "Pedidos atrasados:pedidos:<=", "Días promedio de atraso:días:<=", "Exactitud de picking:%:>=",
                            "Costo logístico por unidad:$/unidad:<="],
    "Inventario": ["Días de inventario:días:<=", "Exactitud de inventario:%:>=", "Faltantes de material:eventos:<=", "Material obsoleto:$:<=",
                   "Merma:%:<="],
    "Proveedores": ["Entregas a tiempo del proveedor:%:>=", "PPM del proveedor:ppm:<=", "SCAR abiertas:SCAR:<=", "Lead time del proveedor:días:<="],
    "Personas y entorno": ["Horas extra:h:<=", "Ausentismo:%:<=", "Rotación de personal:%:<=", "Cumplimiento de capacitación:%:>=",
                           "Días sin accidentes:días:>=", "Near misses reportados:eventos:>=", "Consumo eléctrico por unidad:kWh/unidad:<=",
                           "Residuos por unidad:kg/unidad:<="],
    "Financieros": ["Costo unitario:$/unidad:<=", "Costo de scrap:$:<=", "Costo de retrabajo:$:<=", "Ahorro generado:$:>=",
                    "Horas ahorradas:h:>="],
    "Mejora continua": ["Proyectos de mejora activos:proyectos:>=", "Acciones Kaizen cerradas:acciones:>=", "Acciones vencidas:acciones:<=",
                        "Ideas implementadas:%:>="],
    "Sistema de gestión de calidad": ["Documentos pendientes de aprobación:documentos:<=", "Documentos vencidos:documentos:<=",
                                      "Auditorías completadas:%:>=", "Hallazgos abiertos:hallazgos:<=", "Hallazgos vencidos:hallazgos:<=",
                                      "Riesgos abiertos:riesgos:<=", "Indicadores dentro de meta:%:>=", "Cambios pendientes de aprobación:cambios:<="],
}


def _slug(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return "-".join("".join(ch if ch.isalnum() else " " for ch in t.upper()).split())[:28]


def catalogo():
    lista = [{"id": i, "nombre": n, "categoria": c, "unidad": u, "sentido": s, "formula": f, "fuente": fu} for i, n, c, u, s, f, fu in _BASE]
    vistos = {x["nombre"].lower() for x in lista}
    for cat, items in _GENERAL.items():
        for it in items:
            n, u, s = it.rsplit(":", 2)
            if n.lower() in vistos: continue
            lista.append({"id": _slug(n), "nombre": n, "categoria": cat, "unidad": u, "sentido": s,
                          "formula": "Definida por el proyecto", "fuente": "GENERAL (catálogo ampliado, no respaldado por la base)"})
    return lista
