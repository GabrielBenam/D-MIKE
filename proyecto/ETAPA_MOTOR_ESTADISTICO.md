# D-MIKE — Etapa «Motor estadístico» (adaptado al estado v0.10.0)

## Alcance
Convertir el módulo estadístico de D-MIKE en una herramienta estadística industrial propia (código, nombres e
interfaz propios; sin copiar implementación, textos ni elementos de Minitab). Solo el motor estadístico y lo que
dependa directamente de él (hoja de datos, gráficas, resultados). Fuera de esta etapa: gestión de proyectos,
tablero ejecutivo, Power BI, formatos Lean.

## Reglas que se mantienen del proyecto
- Fórmulas, umbrales y criterios: de la base LSS, citando archivo y sección. Lo que la base no cubre se marca
  «no respaldado por la base» en el código y en el resultado, antes de usar conocimiento general.
- Cada cálculo se verifica contra un ejemplo resuelto del curso; si la base no trae los datos crudos, se verifica
  lo que sí trae, se contrasta con una implementación independiente (scipy o numpy) y se deja anotado qué falta.
- Solo datos sintéticos, marcados como tales.
- Incrementos pequeños: cada análisis se define con entrada, validación, cálculo/gráfica, plantilla y exportación;
  pruebas pytest + Playwright con el puente real y una captura por entrega; al final, qué se probó y qué no.
- Dependencias: Python 3.12, numpy, scipy, matplotlib, openpyxl (ya en requirements). statsmodels solo si una
  fase lo exige (logística, ARIMA); avisar antes de agregarlo, porque crece el instalador.
- Identidad visual: tokens.py (#dd5813, Montserrat).

## 1. Auditoría (estado real de v0.10.0)

| Funcionalidad | Estado | Archivo | Problemas | Reutilizable | Falta | Prioridad |
|---|---|---|---|---|---|---|
| Hoja de datos (tipos num/texto/fecha, nombres, pegar, insertar/eliminar filas y columnas, renombrar, celdas inválidas fuera de cálculo) | PARCIAL | nucleo/hoja.py, ui/app.js | sin selección de rangos, deshacer, ordenar, filtrar, buscar/reemplazar; sin tipo hora | Sí | importar CSV/TSV/XLSX, ordenar, filtrar, buscar y reemplazar, deshacer | Alta |
| Archivo .dmike y exportación .xlsx/.csv | COMPLETA | nucleo/archivo.py | — | Sí | importar | — |
| Descriptivos (N, media, mediana, moda, rango, s, s², Q1, Q3) | PARCIAL | modulos/estadistica.py `descriptivos` | falta faltantes, suma, EE, CV, IQR, percentiles, asimetría, curtosis | Sí | completar | Alta |
| Normalidad Anderson-Darling + gráfica de probabilidad | PARCIAL | modulos/analisis.py `Distrib` | redacción «se asume normal» debe decir «no se rechaza»; sin Q-Q ni identificación de distribución | Sí | redacción, Shapiro-Wilk, identificación lognormal/Weibull (25_BB), Box-Cox | Alta |
| Z, % fuera, nivel sigma | COMPLETA (verificada) | estadistica `fuera_de_especificacion` | — | Sí | — | — |
| Histograma con clases del curso | COMPLETA (verificada) | analisis `clases_histograma` | solo dentro de DISTRIB | Sí | gráfica independiente | Media |
| Diagrama de caja | COMPLETA | graficas_basicas `Caja` | — | Sí | — | — |
| Gráfica de corrida | COMPLETA | graficas_basicas `Corrida` | la base no trae teoría propia | Sí | — | — |
| Pareto | COMPLETA | graficas_basicas `Pareto` | no respaldado por la base | Sí | — | — |
| ANOVA un factor y con bloque, residuos | COMPLETA | estadistica `anova_un_factor`, `anova_bloque` | sin comparaciones múltiples | Sí | dos factores, Tukey | Alta |
| MSA de atributos (acuerdos, Wilson, kappa) | COMPLETA | estadistica `msa_atributos` | kappa no respaldado | Sí | — | — |
| MSA de variable (Gage R&R) | AUSENTE | — | — | — | cruzado (14_GB MED-RR-VARIABLE, PL16) | Crítica |
| SPC (I-MR, Xbar-R, Xbar-S, P, NP, C, U, reglas) | AUSENTE | — | patrones existen solo dentro de corrida | `corridas`, `max_racha` | motor SPC completo (19_GB) | Crítica |
| Capacidad (Cp, Cpk, Pp, Ppk, PPM) | AUSENTE | — | — | `fuera_de_especificacion` | 16_GB CAP-* | Crítica |
| Correlación | AUSENTE | — | — | — | 17_GB CORR-* | Alta |
| Regresión simple, múltiple, polinomial y diagnósticos | AUSENTE | — | — | — | 27_BB REG-* | Alta |
| Pruebas de hipótesis (t, proporciones, varianzas) | AUSENTE | — | no están en la base | — | general, marcado | Alta |
| DOE factorial, fraccionado, RSM | AUSENTE | — | — | — | 18_GB, 26_BB, 28_BB | Media |
| Multi-Vari | AUSENTE | — | — | `Caja` | 17_GB MV-* | Media |
| Tamaño de muestra | PARCIAL | estadistica `tamano_muestra` | solo estimación de media y proporción | Sí | potencia, factorial (18_GB) | Media |
| Resultado estructurado | PARCIAL | modulos/base.py `resultado()` | dict con bloques; sin supuestos, interpretación ni reejecución; columnas guardadas por índice | Sí | refactor a resultado de análisis | Crítica |
| Sesión e historial | PARCIAL | sesión + Proyecto > Resultados | no se puede copiar, reabrir con datos nuevos ni generar reporte conjunto | Sí | historial reproducible | Alta |
| Duplicados | — | descriptivos se calculan en ESTADISTICOS, DISTRIB, BOXPLOT y ANOVA | — | — | unificar en una sola función | Media |

## 2. Arquitectura (sobre lo que ya existe, sin rehacer)
Hoja (nucleo/hoja.py) → Selección de datos (columnas por NOMBRE, filtros, filas válidas)
→ Motor (modulos/estadistica.py y motores nuevos spc.py, regresion.py, msa.py, doe.py: funciones puras, sin interfaz)
→ Resultado de análisis (amplía el dict actual con: tipo, definición, supuestos con su diagnóstico, estadísticos,
estimaciones, IC, valores p, advertencias, tablas, gráficas e interpretación)
→ Gráficas (modulos/base.py con tokens.py) → Pestaña de resultado, sesión e historial → Exportación (xlsx/png, Minitab).

Definición de análisis guardada en el .dmike: análisis, columnas por nombre, filtros, alfa, opciones y fecha;
botón «Repetir con los datos actuales».

Interpretación: frases correctas («no se rechaza H0» ≠ «son iguales»; asociación ≠ causalidad; significancia
estadística ≠ práctica), con alfa, valor p e IC; los supuestos se advierten, no bloquean.

## 3. Incrementos (en orden; cada uno cierra con pruebas, captura y ESTADO)
- E1 Refactor: resultado de análisis, definición reproducible, columnas por nombre, interpretación con redacción
  correcta (corrige DISTRIB), descriptivos unificados y completos, historial con reabrir/repetir/copiar.
- E2 Hoja: importar CSV/TSV/XLSX, ordenar, filtrar, buscar/reemplazar, deshacer, selección de rangos;
  Calc > Calculadora de columnas (operaciones, log, estandarizar, diferencias, acumulados, rango).
- E3 SPC: I-MR, Xbar-R, Xbar-S, P, NP, C, U con constantes y patrones de 19_GB (SPC-CONSTANTES, SPC-PATRONES,
  SPC-RECALCULO); motor que devuelve violaciones; fases y límites históricos; límites de control separados de
  los de especificación.
- E4 Capacidad normal: Cp, Cpk, CPU, CPL, Pp, Ppk, PPM esperado y observado, sigma dentro y global (16_GB);
  resumen de capacidad propio con histograma, carta, probabilidad y valores.
- E5 MSA de variable: Gage R&R cruzado (ANOVA y, si la base lo trae, método de rangos), %contribución, %VE,
  %tolerancia, ndc, gráficas (14_GB MED-RR-VARIABLE, PL16).
- E6 Correlación (Pearson, matriz, diagrama) y regresión simple, múltiple y polinomial con ANOVA, IC, predicción,
  R², R² ajustado, residuos, Cook, PRESS, Durbin-Watson, VIF y selección de variables (17_GB, 27_BB).
- E7 Pruebas de hipótesis: t de 1 y 2 muestras, pareada, 1 y 2 proporciones, 1 y 2 varianzas (no respaldado por la base).
- E8 ANOVA de dos factores con interacción, Tukey; Multi-Vari (17_GB MV-*).
- E9 DOE: 2^k completo y fraccionado con resolución, aleatorización, réplicas, bloques y puntos centrales; efectos,
  Pareto y normal de efectos, interacciones; superficie de respuesta con DCC, contornos y punto estacionario
  (18_GB, 26_BB, 28_BB).
- E10 Distribuciones: identificación (normal, lognormal, Weibull, exponencial) y Box-Cox (25_BB); capacidad no normal.
- E11 Potencia y tamaño de muestra, intervalos de tolerancia, no paramétricas, tablas cruzadas y chi-cuadrada
  (no respaldado por la base).

Después de E11 (fuera de esta etapa salvo pedido): series de tiempo, multivariado, confiabilidad, bootstrap,
equivalencia, muestreo de aceptación, logística (requiere statsmodels).

## 4. Lo que necesito del usuario (no bloquea; se usa al llegar a cada incremento)
Datos crudos de ejemplos del curso para verificar: tablas de constantes y ejemplo de cartas (19_GB), ejemplo de
capacidad (16_GB), estudio Gage R&R de variable (PL16), ejemplos de regresión (27_BB REG-EJ-*), ejemplo DOE
fraccionado y RSM (26_BB, 28_BB), ANOVA de tornillos, 4_5_d.

## Avance
- v0.11.0: E1, E3, E4 y E6 completos.
- v0.12.0: revisión integral; E9 superficies de respuesta (diseño, análisis, contornos, superficie, punto estacionario, ascenso y optimizador); E2 parte 1 (importar, ordenar, buscar y reemplazar, deshacer y rehacer).
- Siguiente: E2 parte 2 (filtrar, rangos, calculadora), E5 Gage R&R de variable, E7 pruebas de hipótesis, E8, resto de E9 (factorial con efectos), E10, E11.
- v0.13.0: E2 completo (filtrar, rangos, calculadora); E5 Gage R&R de variable cruzado; hoja de verificación contra Excel.
- Siguiente: E7 pruebas de hipótesis, E8 ANOVA de dos factores y Tukey, resto de E9, E10, E11, Gage R&R anidado y por promedio-rango.
