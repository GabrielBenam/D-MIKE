# Entrega 0 — Auditoría AS-IS, matriz AS-IS/TO-BE, dependencias y migración

Base: código del repositorio en la versión 0.25.0 (rama `main` tras el PR 1), contra `proyecto/especificaciones/ESPEC_flujo_real_dmaic.md`. Solo informe: no se cambió código, datos ni pruebas. Fecha: 13/10/2026.

## 1. Qué se pudo y qué no se pudo auditar

Cada afirmación de este informe es verificable en el archivo citado. Donde no hubo código, se dice.

| Pieza | Estado de acceso |
|---|---|
| Artefacto web «Diagnóstico de proyecto D-MIKE» (cinco secciones, Preparar la receta) | **El código fuente de la interfaz no está en el repositorio.** Solo están su motor de reglas y su catálogo: `herramientas_arbol/engine.js`, `herramientas_arbol/simular_arbol.py`, `herramientas_arbol/verificar_arbol.py` y `app/datos/arbol_diagnostico.json`. `proyecto/artefactos/` contiene guía, visor y tablero, no el diagnóstico. Las cinco secciones, el cuestionario completo, el guardado por folio y la exportación a Excel/TXT **no se pueden auditar**. |
| Contrato de receta y su ejecución | Completo: `app/nucleo/receta.py` (248 líneas), `app/api.py` líneas 364–424, interfaz en `app/ui/inicio.js` 160–182. |
| Aplicación y módulos DOE | Completo: `app/modulos/doe.py`, `superficies.py`, `factorial.py`. |
| Manual v0.25 (PDF, 138 páginas) y su generador | **No están en el repositorio.** Solo hay `ESPEC_manual_v026.md`, la ayuda interna (`app/ui/ayuda.js`) y `app/datos/comandos.json`. Las afirmaciones del manual (capítulos 5 y 6, páginas 106–127) no se pudieron contrastar con el texto. |
| Pruebas | Completo. Corrida de la suite: 391 pasan, 1 falla (`test_capturas_manual.py::test_captura_incremento_3`, anterior a esta tarea). |

## 2. Hallazgos AS-IS

### 2.1 Contrato de receta (v1)

Es un JSON declarativo con `tipo: "dmike-receta"` y `receta_version: 1`. La versión soportada es 1 (`VERSION_SOPORTADA`). Viaja como `.json` (sin datos) o dentro de un `.xlsx` en la hoja oculta `_receta`, partida en trozos de 30,000 caracteres; las demás hojas del libro son los datos. Campos que lee `ejecutar`: `folio` (opcional), `datos_fijos`, `perfil`, `hoja_sugerida`, `complementarios`, `hojas`, `disenos`, `formatos`, `analisis`, `avance`, `dmike_minimo`, `origen`, `recomendaciones`.

La validación (`validar`) comprueba solo cuatro cosas: el tipo, que la versión no sea mayor, que `dmike_minimo` no exceda al programa, y que existan los módulos de diseños y análisis y los formatos. **No valida** la estructura de `hojas`, columnas, `avance` ni folio; un campo mal formado falla durante la ejecución, que se detiene con el mensaje «La receta se detuvo».

No existen en el contrato: modo de proyecto (real o demostración), `recipe_revision`, `base_revision`, estados de evidencia, procedencia de datos, decisiones, bitácora de auditoría ni huella de los datos de entrada. Una búsqueda en `app/` de `project_mode`, `run_id`, `design_id`, `checksum` y «demostración» no encontró nada.

### 2.2 Ejecución y actualización por folio

`ejecutar(actualizar=True)` ya es la base de las recetas incrementales (hecho verificado en código y en `test_receta.py::test_receta_con_folio_actualiza_el_mismo_proyecto`). Comportamiento real:

- Datos fijos: solo llena los vacíos.
- Columnas de hojas: si ya tienen datos, no se sobrescriben y se avisa; si están vacías y la plantilla trae datos, se llenan.
- Formatos: llena cabecera y tablas solo donde están vacías; si hay contenido distinto, lo conserva y avisa.
- Análisis: no repite los que ya figuran en `_receta.ids` por su `id`. **No detecta que los datos cambiaron** después de correrlo: un análisis hecho con datos parciales no se reevalúa.
- Análisis sin datos en sus columnas: quedan como «Pendiente» con explicación legible (cumple el principio de pendientes).
- Avance: solo sube (pendiente → en_curso → hecho).
- El perfil **no se vuelve a aplicar** si el proyecto ya tiene módulos (`receta.py` línea 119): una receta nueva no puede incorporar un perfil más nuevo.
- Al terminar, `_receta.json` **reemplaza** a la receta anterior (línea 247). No hay historia de revisiones.
- El proyecto «actualizable» se busca solo entre los proyectos **abiertos** (`api.py` línea 399). Un `.dmike` cerrado con el mismo folio no se encuentra.
- El folio es texto libre opcional; no se valida su formato ni su unicidad.

### 2.3 DOE (DISENO-RSM y módulos de análisis)

Lo que ya cumple la especificación:

- El diseño se crea **sin respuestas**: la columna de respuesta nace vacía y numérica. Cumple «el DOE se diseña antes de recolectar».
- Tipos: central compuesto (rotable o en caras, 1 o 2 bloques), Box-Behnken, factorial 2^k con centros y fraccionado 2^(k−p) con generadores, resolución y relación definidora; réplicas, aleatorización opcional con semilla (con semilla, el orden se reproduce; sin semilla cambia en cada ejecución, verificado).
- Escribe `OrdenEst` (orden estándar), `OrdenCorrida`, `TipoPunto`, `Bloque`, factores en unidades reales y la respuesta. Avisa si los puntos axiales salen de los niveles bajo y alto.
- Los análisis (RSM, FACTORIAL, OPTIMIZADOR) leen la información del diseño desde `proyecto.formatos["_disenos"]`.

Lo que no cumple:

- No hay `run_id` inmutable, `design_id` ni versión de diseño. El diseño se identifica por el **nombre de la columna de respuesta** (`_disenos["Y"]`; un segundo diseño con la misma respuesta se guarda como `Y_2`, verificado).
- No se guarda la semilla ni los metadatos de generación dentro del diseño; quedan solo en la definición del resultado. `info` guarda tipo, factores, alfa, nombres de columnas y número de corridas.
- No hay límites de seguridad por factor ni rechazo de extrapolación (los niveles bajo y alto son solo el cubo). El optimizador acota por la región del diseño, pero no existe el concepto «región autorizada».
- No hay captura de operador, lote, fecha, estado ni observaciones por corrida.
- No hay hoja de ejecución con eventos, ni bloqueo que impida analizar con respuestas insuficientes más allá de los errores propios del análisis.
- El segundo diseño no está condicionado a evidencia del primero; tampoco hay omisión justificada del cribado, ni «mejora sin DOE» registrada.

### 2.4 Emparejamiento de respuestas (riesgo de mayor importancia)

Al ejecutar una receta con diseños, `receta.py` líneas 141–171 empareja las filas de la hoja de la plantilla con las filas del diseño **por posición** (fila k con fila k), comprobando que los niveles de cada factor coincidan con tolerancia 1e-6. Consecuencias verificadas por lectura:

1. No existe identificador de corrida. Las corridas con niveles idénticos (puntos centrales y réplicas) son **intercambiables sin que se detecte**: si dos filas centrales se cruzan, el emparejamiento sigue siendo «válido».
2. Si la hoja no trae la columna de un factor, esa columna se omite en la comprobación (`if n in cab`), y la hoja se acepta solo por tener el mismo número de filas.
3. Si el número de filas difiere, se descarta **todo** el diseño con el aviso «las corridas de la plantilla no coinciden»; no hay resolución por corrida.
4. No hay detección de corridas duplicadas, de versión de diseño incompatible ni de respuesta asociada al factor equivocado salvo por los niveles.
5. Con `actualizar`, si la columna de respuesta ya tiene algún dato, se omite completa (`_tiene_datos`): no se completan corridas faltantes de una captura parcial.

Los criterios de aceptación 5 y 6 (conservar `run_id`, detectar duplicada, factor equivocado y versión incompatible) **no se cumplen hoy**.

### 2.5 Separación real / demostración

No existe. El generador del caso (`herramientas/generar_caso_integral.py`, semilla 2026) y `herramientas/receta_caso_integral.py` son **herramientas de desarrollo fuera de `app/`**, así que la aplicación no los ejecuta. El riesgo está en otro lugar: `Calc › Datos aleatorios` (`ALEATORIOS`, `app/modulos/calc_hoja.py` línea 207) escribe valores aleatorios en cualquier proyecto sin marcarlos como sintéticos, y la plantilla `caso_integral_datos_llenos.xlsx` (en `pruebas/sinteticos/`) se abre igual que una receta real, sin etiqueta «SINTÉTICO». Los datos fijos no incluyen un campo de modo. Los resultados exportados tampoco llevan marca.

La receta del caso maestro (`herramientas/receta_caso_integral.py`) es, además, el único ejemplo del contrato: define seis hojas (`linea_base`, `defectos`, `gage_rr`, `cribado`, `dcc`, `despues`), dos diseños (semillas 7 y 11), 15 análisis y 28 formatos. Su estructura obliga a la ruta cribado → DCC; no existe receta con una sola etapa, ni sin DOE.

### 2.6 Archivo `.dmike` y compatibilidad

SQLite con tablas `meta`, `columnas`, `celdas` y `proyecto`; `version_formato = 1`; un archivo con versión mayor se rechaza. **No hay código de migración** (ninguna búsqueda de «migr» en `app/`). La receta y los diseños viven dentro de `proyecto.formatos` con claves que empiezan con guion bajo (`_receta`, `_disenos`), de modo que agregar claves nuevas ahí no rompe la lectura de archivos anteriores. Hay una huella SHA-256 de columnas (`api.py` línea 502) usada para la reproducibilidad de resultados; no es una huella de la fuente de datos importada.

### 2.7 Medición con ensayo destructivo

`MSA-VAR` es Gage R&R **cruzado** por ANOVA (`msa_variable.py`). En `comandos.json` figura «Gage R&R anidado — Pruebas destructivas» marcado «P» (propuesto: próxima versión, según `app/ui/ui2.js` línea 254), es decir, no implementado. Para el caso de la especificación (probetas que se destruyen) no hay hoy un estudio de medición con diseño coherente; el programa tampoco advierte que el cruzado no aplica.

### 2.8 Pruebas

Existentes y relevantes: `test_receta.py` (5 pruebas: reproducción de 17 resultados con óptimo 129.42323 y 108.63155, receta vacía con pendientes, versión y módulo desconocido, actualización por folio idempotente, solo datos), `test_doe.py` (9, estadística), `test_superficies.py` (8), `test_archivo.py` (10, guardar, abrir, exportar), `test_perfil.py`, `test_revision_integral.py`. Estas pruebas son la **línea base del criterio 11** (demostración reproducible) y no deben tocarse.

No existen pruebas de: modo real/demostración, `run_id`, corridas duplicadas, versión de diseño, migración de receta o de `.dmike` entre versiones, conflictos web/escritorio, omisión de cribado, ni fuga entre folios. La compilación en GitHub ejecuta `-m "not interfaz"` y excluye `*capturas*`: la prueba de interfaz de recetas no corre en CI.

## 3. Matriz AS-IS / TO-BE

Estados: **Implementado**, **Parcial**, **A desarrollar**, **No auditable** (falta código).

| ID | Funcionalidad | AS-IS | TO-BE | Estado | Entrega |
|---|---|---|---|---|---|
| R1 | Receta declarativa validada contra catálogo | Contrato v1, `validar` | Mantener y extender | Implementado | — |
| R2 | Receta parcial (pendientes) | Análisis sin datos quedan pendientes con texto | Añadir tareas con responsable y acción | Parcial | 2 |
| R3 | Actualización por folio sin pérdida | `actualizar=True`, solo agrega | Añadir revisión, historia y detección de datos cambiados | Parcial | 2 |
| R4 | `recipe_revision`, `base_revision` | No existe | Campos nuevos opcionales | A desarrollar | 2 |
| R5 | `project_mode` real/demostración | No existe | Campo en receta, proyecto y datos; bloqueo de sintéticos en real | A desarrollar | 1 |
| R6 | Estados de evidencia por variable | No existe | Los seis estados de la sección 4.2 | A desarrollar | 2 |
| R7 | Bitácora de decisiones y auditoría | No existe (hay formato BITACORA del PMBOK, `formatos6.py`) | Reutilizar el formato o un registro propio | A desarrollar | 4 |
| D1 | Diseño de DOE sin respuestas | Cumple | Conservar | Implementado | — |
| D2 | `design_id`, `run_id`, versión de diseño | No existe | Identificadores inmutables | A desarrollar | 3 |
| D3 | Semilla y metadatos del diseño guardados | Solo en la definición del resultado | Guardar en el diseño | Parcial | 3 |
| D4 | Emparejamiento por identidad | Por posición con niveles | Por `run_id` más niveles | A desarrollar | 3 |
| D5 | Detección de duplicadas, versión y factor erróneo | No | Rechazo o resolución auditable | A desarrollar | 3 |
| D6 | Límites de seguridad y rechazo de extrapolación | Solo aviso de axiales | Región autorizada por factor | A desarrollar | 3 |
| D7 | Captura por corrida (fecha, operador, lote, estado) | No | Columnas y estado por `run_id` | A desarrollar | 3 |
| D8 | DOE secuencial optativo y omisión justificada | No hay lógica | Decisión registrada | A desarrollar | 3 |
| D9 | Alias y confundimiento en el análisis | Resolución y alias en el fraccionado | Advertencia explícita (AB = CD) en la conclusión | Parcial | 3 |
| D10 | Confirmación independiente | No existe como flujo | Plan, comparación observado-predicho | A desarrollar | 3–4 |
| M1 | Gage R&R cruzado | Implementado | Conservar | Implementado | — |
| M2 | Estudio para ensayo destructivo | «P» (propuesto, no implementado) | Anidado o aviso de no aplicabilidad | A desarrollar | 3 |
| W1 | Entrevista adaptativa y cinco secciones | Código no disponible | Rediseño | No auditable | 2 |
| W2 | Árbol de reglas (62 módulos, 78 reglas, 17 síntomas) | Implementado | Conservar | Implementado | — |
| W3 | Retoma por estado y paquete de avance | No auditable | Nuevo formato de paquete | No auditable | 4 |
| W4 | Aislamiento entre folios | No auditable | Verificar en el artefacto | No auditable | 4 |
| C1 | Caso sintético reproducible | `pruebas/sinteticos`, `herramientas/` | Conservar y etiquetar | Implementado | 1 |
| C2 | Caso real guiado sin respuestas | No existe | Nueva receta vacía y guía | A desarrollar | 5 |
| X1 | Manual v0.25 con capítulo 5 y 6 | PDF fuera del repositorio | Actualizar tras implementar | No auditable | 5 |
| X2 | Marca «sintético» en resultados y exportaciones | No existe | Etiqueta visible | A desarrollar | 1 |
| A1 | Migración `.dmike` v1 y recetas v1 | Sin migración, formato abierto | Claves nuevas opcionales con valores por omisión | A desarrollar | 1–2 |

Los criterios de aceptación 1–18 se mapean así: 1, 2, 3, 12 → Entrega 2; 4 y 16 → migración (sección 5); 5–10 → Entrega 3; 11 → Entrega 1; 13 → Entrega 4; 14 → Entregas 2–4; 15 y 18 → Entrega 5; 17 → web (no auditable).

## 4. Mapa de dependencias

Receta y proyecto: `app/nucleo/receta.py` depende de `app/api.py` (`fijar_datos`, `pegar`, `ejecutar_modulo`, `abrir_formato`, `guardar_formato`), de `app/nucleo/perfil.py` (validación del perfil), de `app/nucleo/hoja.py` y de `app/modulos/formatos.py` (registro de formatos). El estado de la receta se guarda en `proyecto.formatos["_receta"]`, que `app/nucleo/archivo.py` escribe en la tabla `proyecto`.

DOE: `DISENO-RSM` (`superficies.py`) usa `doe.py` y escribe `proyecto.formatos["_disenos"]`. Lo leen `Rsm`, `Optimizador` y `factorial.py`. Cambiar la clave del diseño (de nombre de respuesta a `design_id`) afecta a estos tres módulos, a `receta.py` (línea 132–133, que reconstruye `info`), a `herramientas/receta_caso_integral.py` y a las pruebas `test_superficies.py` y `test_receta.py`.

Interfaz: `inicio.js` (`preguntarReceta`) y `ui2.js` consumen el resumen de `abrir_receta`; agregar campos al resumen es compatible, quitarlos no.

Herramientas fuera de `app/`: `generar_ejemplos.py` → `generar_caso_integral.py` → `receta_caso_integral.py` → `pruebas/sinteticos/*.xlsx`. Cualquier cambio de contrato obliga a regenerar las plantillas de prueba y a documentar que son la línea base de la demostración.

Compilación: `main.yml` revisa `MANIFIESTO.txt`; cada archivo nuevo debe agregarse ahí.

Web (sin código aquí): el catálogo `app/datos/arbol_diagnostico.json` y `engine.js` se comparten; la receta que exporta la web debe seguir cumpliendo `validar`.

## 5. Propuesta de migración y compatibilidad

1. **Receta v2 como extensión, no reemplazo.** Mantener `receta_version: 1` legible. Agregar campos opcionales: `project_mode`, `recipe_revision`, `base_revision`, `variables[].estado_evidencia`, `disenos[].design_id`. Si faltan, se asumen: `project_mode = "demostracion"` solo para recetas v1 que traigan marca de origen sintético, y `"real"` en los demás casos (decisión pendiente, ver pregunta 1). `VERSION_SOPORTADA` sube a 2 y las recetas v1 se leen sin cambios.
2. **`.dmike` sin cambio de tabla.** Las claves nuevas (`_modo`, `_corridas`, `_decisiones`, `_revisiones`) se guardan en `proyecto.formatos`, igual que `_receta` y `_disenos`. Un `.dmike` anterior abre sin ellas; uno nuevo en un programa anterior las ignora como ya ignora claves desconocidas. Prueba de migración obligatoria en la Entrega 1: abrir los `.dmike` generados por la v0.25.0 y verificar que resultados, huellas y diseños quedan iguales.
3. **Diseños antiguos.** Al abrir un proyecto sin `design_id`, asignarlo al vuelo a partir de la clave actual (`Y`, `Y_2`) y derivar `run_id` de `OrdenEst`, sin tocar la hoja. Es determinista y reversible.
4. **Historia de recetas.** Antes de reemplazar `_receta.json`, mover la anterior a `_revisiones` (con huella). Esto cumple «ningún merge borra sin copia histórica».
5. **Línea base protegida.** Antes de cualquier cambio, guardar como referencia los 17 resultados del caso maestro; el criterio 11 se prueba contra ellos.

## 6. Orden de las entregas siguientes y riesgos

Orden propuesto (el de la especificación): 1 modo real/demostración con migración y marca; 2 receta v2 y tareas pendientes; 3 DOE con `run_id`; 4 continuidad, auditoría y paquete de avance; 5 manual y caso real.

Riesgos principales: (a) el código del artefacto web no está disponible, así que las Entregas 2 y 4 dependen de que se proporcione; (b) cambiar la clave de `_disenos` toca tres módulos y varias pruebas; (c) sin el PDF del manual no se puede verificar la concordancia documental de la Entrega 5; (d) el Gage R&R anidado es un módulo nuevo, no un ajuste, y no hay fuente del curso verificada en este repositorio (CLAUDE.md exige citar la base del curso o marcar «no respaldado»).

## 7. Decisiones que requieren al usuario (se preguntan una a la vez)

1. ¿Cómo debe tratarse una receta v1 sin campo de modo? (pregunta abierta en el chat)
2. Dónde está el código fuente del artefacto web y cómo se me entrega.
3. Si el PDF del manual v0.25 y su generador se agregan al repositorio.
4. Si el Gage R&R anidado entra en la Entrega 3 o se difiere.
5. Qué criterio de «región autorizada» usar para rechazar extrapolación.
