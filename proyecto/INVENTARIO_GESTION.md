# Inventario del grupo «Gestión» de la cinta

Generado con `python herramientas/inventario_gestion.py --escribir`. Cada entrada se revisa contra el código.

Entradas: 17. Solo entrada de menú: 0. Construidas con cálculo propio: 17. Construidas solo con captura (guardan y exportan texto, sin cálculo): 0. Sin cálculo numérico (solo reglas de validación u organización): 4.

Nota: «con cálculo propio» significa que el formato define su propio método calcular(); la columna «Qué hace» dice si ese método calcula números o solo valida reglas. Las pruebas que solo nombran el formato dentro de `test_formatos_v010.py` verifican que se llene, guarde y exporte, no sus cifras.

| Grupo | Entrada | Id | Estado | Qué hace | Detalle | Pruebas que lo nombran | Fuente citada en su nota |
|---|---|---|---|---|---|---|---|
| Inicio del proyecto | Acta del proyecto (Charter) | CHARTER | Construido, con cálculo | Cálculo: ahorro total con su base; validación de campos obligatorios | 27 campos de cabecera, 5 tablas | test_a1_estados.py, test_formatos_v010.py | PL14; PMBOK 6; PMBOK 7 |
| Inicio del proyecto | Justificación de negocio | JUSTIFICACION | Construido, con cálculo | Cálculo: VPN, TIR, recuperación, ROI del PMBOK y B/C (pendientes si hay periodos vacíos) | 9 campos de cabecera, 1 tablas | test_formatos_v010.py | PL18; PMBOK 7 |
| Inicio del proyecto | Enfoque de desarrollo | ENFOQUE | Construido, con cálculo | Cálculo: promedio de variables y sugerencia de enfoque, con gráfica | 4 campos de cabecera, 1 tablas | test_formatos_v010.py | PMBOK 6; PMBOK 7 |
| Inicio del proyecto | Registro de interesados | INTERESADOS | Construido, con cálculo | Cálculo: prominencia y brecha de compromiso, con cuadrícula poder/interés | 3 campos de cabecera, 2 tablas | test_capturas_manual.py, test_formatos_v010.py | PMBOK 6: registro de inte; PMBOK 7: dominio de inter |
| Inicio del proyecto | Matriz de responsabilidades (RACI) | RACI | Construido, con cálculo | Validación de reglas (una sola A, falta R, carga por persona); sin cálculo numérico | 7 campos de cabecera, 1 tablas | test_formatos_v010.py, test_ui_completa.py | PMBOK 6; PMBOK 7 |
| Alcance y tiempo | EDT y diccionario | EDT | Construido, con cálculo | Cálculo: niveles, regla del 100 %, paquetes de trabajo, con dibujo | 5 campos de cabecera, 1 tablas | test_capturas_manual.py, test_formatos_v010.py, test_gestion_interfaz.py | PMBOK 6; PMBOK 7 |
| Alcance y tiempo | Cronograma y ruta crítica | CRONOGRAMA | Construido, con cálculo | Cálculo: ruta crítica, holguras, tres puntos, desvío contra línea base | 11 campos de cabecera, 1 tablas | test_capturas_manual.py, test_formatos_v010.py, test_gestion_interfaz.py | PMBOK 6: actividades e hi; PMBOK 7; PMBOK de iniciar el día  |
| Riesgo y decisión | Registro de riesgos | RIESGOS | Construido, con cálculo | Cálculo: P×I con zonas, VME y reserva de contingencia, con matriz | 6 campos de cabecera, 1 tablas | test_capturas_manual.py, test_formatos_v010.py | PMBOK 6: registro de ries; PMBOK 7: dominio de incer |
| Riesgo y decisión | Monte Carlo del cronograma | MONTECARLO | Construido, con cálculo | Cálculo: simulación con semilla (P50/P80/P90, criticidad, tornado) | 9 campos de cabecera, 0 tablas | test_capturas_manual.py, test_formatos_v010.py | PMBOK 6; PMBOK 7 |
| Riesgo y decisión | Árbol de decisión | ARBOL-DECISION | Construido, con cálculo | Cálculo: valor monetario esperado de las ramas, con dibujo | 3 campos de cabecera, 1 tablas | test_formatos_v010.py | PMBOK 6; PMBOK 7 |
| Riesgo y decisión | Análisis FODA | FODA | Construido, con cálculo | Validación y gráfica: cruza amenazas contra el registro de riesgos; sin cálculo numérico | 2 campos de cabecera, 4 tablas | test_formatos_v010.py | PMBOK 6; PMBOK 7 |
| Riesgo y decisión | Diagrama de afinidad | AFINIDAD | Construido, con cálculo | Organización y gráfica: agrupa ideas; sin cálculo numérico | 2 campos de cabecera, 1 tablas | test_formatos_v010.py | PMBOK 6; PMBOK 7 |
| Seguimiento | Bitácora: supuestos, incidentes y cambios | BITACORA | Construido, con cálculo | Cálculo simple: días abiertos y vencidos; validación de campos | 2 campos de cabecera, 3 tablas | test_formatos_v010.py | PMBOK 6: bitácora de supu; PMBOK 7: 4 |
| Seguimiento | Seguimiento por valor ganado | VALOR-GANADO | Construido, con cálculo | Cálculo: SV, CV, SPI, CPI, ETC, EAC, VAC, TCPI y curva S | 7 campos de cabecera, 1 tablas | test_capturas_manual.py, test_formatos_v010.py | PMBOK 6; PMBOK 7 |
| Seguimiento | Costo de calidad | COSTO-CALIDAD | Construido, con cálculo | Cálculo: totales por categoría, antes y después, y su proporción de ventas | 6 campos de cabecera, 1 tablas | test_formatos_v010.py | PMBOK 7 |
| Seguimiento | Revisión de compuerta de fase | CHECKLIST-FASE | Construido, con cálculo | Validación de reglas de la compuerta y conteo de cumplidos; sin cálculo numérico | 12 campos de cabecera, 1 tablas | test_formatos_v010.py | PMBOK 6; PMBOK 7 |
| Cierre | Cierre y lecciones aprendidas | LECCIONES | Construido, con cálculo | Cálculo simple: objetivos cumplidos contra meta; validación de campos | 8 campos de cabecera, 2 tablas | test_formatos_v010.py | PMBOK 6: informe final 4; PMBOK 7: aprendizaje 2 |
