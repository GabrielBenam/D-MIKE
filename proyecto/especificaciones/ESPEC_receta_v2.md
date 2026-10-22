# ESPEC_receta_v2 — Contrato de receta v2 de D-MIKE

Versión del documento: 1.2 (14/10/2026; encabezado sincronizado el 21/10/2026). Programa: D-MIKE 0.29.0 (secciones 1 a 15, implementadas hasta 0.27.0; secciones 16 a 19.5, Entrega 3, implementadas en 0.29.0). Base: ENTREGA_0_auditoria_AS-IS.md, ESPEC_flujo_real_dmaic.md (secciones 3 a 5 y 10) y lectura del código publicado del Diagnóstico en línea. Estado de verificación: diseño aprobado por el usuario; las secciones 1 a 15 están implementadas hasta 0.27.0 y verificadas con pruebas (pruebas/test_receta.py, test_receta_e2.py, test_modo_v026.py); lo de la Entrega 3 (secciones 7 y 8, `design_id`, `run_id`, `limites_seguros`, `omitido`) sigue sin implementar. Lo no verificado en código se marca «pendiente de validación».

## 1. Alcance

La receta v2 extiende la v1 sin reemplazarla. Mantiene las claves en español de la v1 (`folio` sale, ver 3). La web pregunta y prepara; D-MIKE diseña, analiza y documenta; la receta evoluciona sin anticipar el futuro: nunca lleva respuestas, corridas, resultados ni cifras no medidas.

## 2. Contrato

```json
{
  "tipo": "dmike-receta",
  "receta_version": 2,
  "dmike_minimo": "0.26",
  "id_proyecto": "uuid-v4-en-minusculas",
  "modo_proyecto": "real",
  "revision": 3,
  "revision_base": 2,
  "huella": "sha256:...",
  "generado_en": "ISO-8601",
  "origen": "Diagnóstico en línea",
  "datos_fijos": {},
  "perfil": {},
  "hojas": [{"hoja": "", "origen_datos": "real|vacia|sintetico", "columnas": []}],
  "variables": [{"nombre": "", "hoja": "", "unidad": "", "unidad_analisis": "", "fuente": "", "responsable": "",
                 "estado_evidencia": "PENDIENTE_RECOLECCION", "ensayo_destructivo": false}],
  "analisis": [{"id": "", "modulo": "", "parametros": {}, "requiere": [], "estado": "pendiente"}],
  "disenos": [{"parametros": {}, "limites_seguros": {"A": {"min": 0, "max": 0}}, "omitido": null}],
  "tareas": [{"id": "", "descripcion": "", "responsable": "", "accion": "", "liga": "", "estado": "abierta"}],
  "decisiones": [{"id": "", "fase": "", "tipo": "omitir_cribado", "motivo": "", "fecha": ""}],
  "formatos": [],
  "avance": {},
  "recomendaciones": []
}
```

### 2.1 Campos

Heredados de v1 sin cambio de significado: `tipo`, `dmike_minimo`, `generado_en`, `origen`, `datos_fijos`, `perfil`, `hojas` (columnas por nombre), `analisis` (con `id` y `modulo`), `formatos`, `avance`, `recomendaciones`, y los campos que ya lee `receta.ejecutar` (`hoja_sugerida`, `complementarios`).

Nuevos, todos opcionales salvo `receta_version`, `modo_proyecto` y `id_proyecto` cuando la receta nace en el Diagnóstico en línea:

- `id_proyecto`: UUID v4 en minúsculas. Lo genera el artefacto al crear la sesión y lo guarda dentro de la sesión cifrada. Identifica al proyecto para actualizar. No es secreto y no da acceso a la sesión.
- `modo_proyecto`: `real` o `demostracion`.
- `revision`: entero desde 1; sube con cada exportación de la web.
- `revision_base`: revisión sobre la que se construyó esta (nulo en la primera).
- `huella`: SHA-256 del JSON canónico (claves ordenadas, sin espacios) sin este campo. Si existe, `validar` la comprueba.
- `hojas[].origen_datos`: `real`, `vacia` o `sintetico`.
- `variables[]`: inventario de evidencia. `estado_evidencia` toma uno de seis valores (ESPEC_flujo 4.2): `REAL_VERIFICADO`, `REAL_NO_VALIDADO`, `PENDIENTE_RECOLECCION`, `DESCONOCIDO`, `NO_APLICA`, `SINTETICO_DEMO`. `unidad_analisis` es panel, probeta, lote, ciclo, documento, tarea, persona-hora, etc. `ensayo_destructivo` dispara el aviso de la sección 7.
- `analisis[].estado`: `pendiente`, `disponible` (hay datos en `requiere`), `analizado`, `aprobado`. `requiere` lista columnas con el prefijo `@`.
- `disenos[]`: lleva los parámetros de DISENO-RSM que ya existen en v1. `limites_seguros` por factor (sección 8). `omitido` registra una omisión justificada (por ejemplo del cribado) con su motivo. `design_id` y `run_id` no viajan en la receta: los asigna D-MIKE al crear el diseño y viven en el `.dmike`.
- `tareas[]`: bandeja de pendientes (qué falta, a quién corresponde, acción sugerida, a qué objeto se liga).
- `decisiones[]`: decisiones propuestas desde la entrevista web (omitir cribado, mejora sin DOE, segundo DOE, etc.). El registro autoritativo con auditoría vive en el `.dmike` (Entrega 4).

### 2.2 Entregas que introducen cada grupo

Entrega 1: `modo_proyecto`, `id_proyecto`, `hojas[].origen_datos`, migración. Entrega 2: `revision`, `revision_base`, `huella`, `variables`, `tareas`, `analisis[].estado` y `requiere`. Entrega 3: `disenos[].limites_seguros`, `omitido`, `design_id`, `run_id` (en el `.dmike`). Entrega 4: `decisiones` completas, bitácora de auditoría, paquete de avance.

## 3. Folio e `id_proyecto`

El folio (`DMK-XXXX-XXXX-XXXX`, alfabeto sin I, O, 0, 1) es la llave de cifrado de la sesión web: el artefacto deriva la llave con PBKDF2 y cifra con AES-GCM el documento `sesiones/<hash del folio>` (hecho verificado por lectura del código publicado, sin ejecutarlo). Por eso el folio es una contraseña y se aplica esto:

1. El folio aparece solo en la pantalla del artefacto y en el TXT de instrucciones.
2. El folio no viaja en la receta v2, ni en la hoja LEEME de la plantilla, ni en el `.dmike`.
3. El `id_proyecto` sustituye al folio para reconocer el proyecto al actualizar.
4. Una receta v1 con folio libre se acepta. D-MIKE ignora ese folio: no lo compara, no lo guarda, y avisa que es la llave de una sesión web y no debe compartirse.
5. Un `.dmike` de la v0.25 que ya traiga el folio dentro de `_receta` se deja intacto. Más adelante se ofrecerá una acción explícita del usuario para quitarlo (pendiente, fuera de la Entrega 1).

## 4. Canales

Se conservan los dos canales ya probados. El `.json` es el contrato canónico. La hoja oculta `_receta` del `.xlsx` (trozos de 30,000 caracteres) es solo el contenedor para que el usuario llene datos en la plantilla. Una revisión sin datos viaja como `.json`, porque los datos viven en el `.dmike`. Con `huella` se detecta una hoja oculta dañada o alterada.

## 5. Actualización de un proyecto

Opciones al abrir una receta (las tres de la v1): ejecutar en un proyecto nuevo, actualizar un proyecto abierto, solo abrir los datos.

Actualizar. Si la receta trae `id_proyecto` y coincide con un proyecto abierto, D-MIKE propone ese proyecto. Si no hay coincidencia, o la receta es v1, D-MIKE pide confirmación manual eligiendo uno de los proyectos abiertos. Nunca actualiza por folio. Solo se buscan proyectos abiertos (comportamiento actual, Entrega 0, 2.2).

Ejecutar en un proyecto nuevo. Si ningún proyecto abierto ni reciente tiene ese `id_proyecto`, el proyecto nuevo lo guarda en `_receta.id_proyecto`. Si ya lo tiene un proyecto abierto o reciente, no se asigna en silencio: D-MIKE avisa y ofrece crear uno nuevo sin `id_proyecto` (queda nulo) y, solo si el coincidente está abierto, también actualizar ese proyecto. Si el coincidente es un reciente cerrado, para actualizarlo hay que abrirlo primero (D-MIKE solo actualiza proyectos abiertos).

Comprobación contra recientes (decisión del usuario, 13/10/2026). Se hace leyendo solo el `id_proyecto` guardado en el JSON de cada `.dmike` reciente, sin abrirlo. Es un aviso y nunca bloquea: un archivo borrado, movido, en unidad de red, ilegible o dañado se ignora y la ejecución continúa. Solo avisa; la decisión es del usuario.

Conflicto de revisión. Si `revision_base` de la receta no coincide con la última revisión aplicada en el `.dmike`, D-MIKE declara el conflicto y pide resolución explícita. No hay fusión automática. Antes de reemplazar `_receta.json`, la receta anterior pasa a `_revisiones` con su huella (Entrega 2). Ningún merge borra datos ni resultados válidos sin confirmación y copia histórica.

## 6. Decisión 1 — Modo de una receta v1 y migración

Una receta v1 sin modo se trata como demostración si su `origen` indica caso maestro o sintético (contiene «caso maestro» o «sintétic», sin distinguir acentos ni mayúsculas); en cualquier otro caso es real. Refuerzo opcional, pendiente de validación: D-MIKE guarda las huellas de las recetas sintéticas que distribuye el repositorio y las marca como demostración aunque el origen no lo diga.

D-MIKE muestra el modo detectado antes de ejecutar la receta y permite cambiarlo una sola vez, solo si fue inferido y antes de cargar datos. Una receta v2 trae el modo declarado y no se cambia. En modo real nunca se cargan datos sintéticos: se rechazan hojas con `origen_datos: sintetico` y variables `SINTETICO_DEMO`, y `Calc › Datos aleatorios` queda bloqueado. En demostración, resultados y exportaciones llevan la etiqueta «SINTÉTICO / NO EMPRESARIAL».

Limitación declarada: la inferencia depende del texto de `origen`. Un caso sintético con origen distinto y sin huella conocida se tomaría como real; por eso se muestra el modo detectado y se permite un cambio.

Migración, sin cambio de tabla (`version_formato` sigue en 1):

1. `VERSION_SOPORTADA` sube a 2. Las recetas v1 se leen sin cambios; una versión mayor se rechaza con mensaje claro. Una receta v2 en un programa 0.25 se rechaza por la versión (por eso `dmike_minimo` es «0.26»).
2. Claves nuevas dentro de `proyecto.formatos`: `_modo` = `{valor, deteccion: "declarado"|"inferido_v1", cambiado}`; después `_corridas`, `_decisiones`, `_revisiones`. Un `.dmike` anterior abre sin ellas; uno nuevo en un programa anterior las ignora.
3. Un `.dmike` sin `_modo` se trata con la regla de la inferencia aplicada a su `_receta.origen`; si no hay receta, es real.
4. Diseños antiguos (Entrega 3): al abrir un proyecto sin `design_id`, se asigna al vuelo a partir de la clave actual (`Y`, `Y_2`) y se deriva `run_id` de `OrdenEst`, sin tocar la hoja. Es determinista y reversible.
5. Línea base protegida: antes de cambiar nada, guardar como referencia los 17 resultados del caso maestro (óptimos 129.42323 y 108.63155). El criterio 11 de ESPEC_flujo se prueba contra ellos.

## 7. Decisión 4 — Gage R&R anidado diferido

El Gage R&R anidado para ensayos destructivos se difiere: es un módulo nuevo y no hay fuente del curso verificada en el repositorio (CLAUDE.md exige citar la base o marcar «no respaldado»). La Entrega 3 solo agrega el aviso de no aplicabilidad: si una variable tiene `ensayo_destructivo: true`, `MSA-VAR` (cruzado, ANOVA) advierte que el diseño cruzado no aplica porque las probetas no son equivalentes a mediciones repetidas de la misma pieza. Cubre E2E-F. Hoy `comandos.json` lo marca «P» (propuesto).

## 8. Decisión 5 — Límites seguros y región autorizada

Al crear el DOE, el usuario declara mínimo y máximo seguros por factor (`limites_seguros`). Esos límites no son los niveles bajo y alto del cubo: son la región autorizada. Obligatorio en modo real; opcional en demostración.

Regla: todo punto del diseño fuera de la región se rechaza, incluidos los axiales del central compuesto, y D-MIKE ofrece una alternativa dentro. El optimizador y el análisis no recomiendan parámetros fuera de la región.

Respaldo en la base (28_BB_SUPERFICIES_RESPUESTA, bloques RSM-DCC y RSM-MINITAB-PROCEDIMIENTO, paso 6): el DCC de segundo orden con puntos cúbicos y axiales, y la opción de que el usuario declare el bajo y alto de cada factor como «Puntos Cúbicos» o como «Puntos Axiales». La base no nombra la variante rotable ni en caras ni da el valor de α: eso es no respaldado, igual que ya consta en ESTADO_D-MIKE.md. Alternativa dentro de la región, respaldada por esa opción: tratar el mínimo y máximo seguros como puntos axiales, de modo que los puntos del cubo queden dentro. Cualquier otra alternativa (reducir α, desplazar el centro) se marca no respaldada.

## 9. Validación (`validar`) en v2

Comprueba, además de lo de v1 (tipo, versión, `dmike_minimo`, módulos y formatos del catálogo): `modo_proyecto` en {`real`, `demostracion`}; `id_proyecto` UUID v4 si existe; `huella` si existe; `SINTETICO_DEMO` y `origen_datos: sintetico` solo con `demostracion`; `estado_evidencia` en los seis valores; estructura de `hojas`, `variables` y `tareas` (v1 no la validaba y fallaba durante la ejecución). `limites_seguros` se exige desde la Entrega 3.

## 10. Pendientes y límites

Pendiente de validación: la lista de huellas de recetas sintéticas, las rutas de código para la etiqueta sintética en exportaciones, y el comportamiento del artefacto una vez cambiado (sus secciones de entrevista, retoma y aislamiento entre folios se auditan en la matriz TO-BE). Fuera de alcance de esta especificación: Gage R&R anidado, quitar el folio de `.dmike` antiguos, paquete de avance. Abierto para decisión del usuario: ruta de menú para crear o pasar a modo demostración un proyecto sin receta (hoy Calc › Datos aleatorios solo se usa abriendo una receta de demostración).

## 11. Trazabilidad con ESPEC_flujo_real_dmaic.md (sección 10)

Criterios 4 y 16: secciones 6 y 9. Criterio 11: sección 6, punto 5. Criterios 1, 2, 3, 12: Entrega 2 con las secciones 2 y 5. Criterios 5 a 10: Entrega 3 con las secciones 2, 7 y 8. Criterios 13 y 14: Entrega 4. Criterio 17: sección 3 (folio) y matriz TO-BE.

## 12. Entrega 2 (D-MIKE 0.27.0) — variables, pendientes, estados y revisiones

Punto de partida verificado en el código de 0.26.0 (app/nucleo/receta.py): `ejecutar(..., actualizar=True)` agrega solo lo nuevo y no sobrescribe columnas con datos; los pendientes salen como texto de la ejecución y no se guardan; `variables` solo se valida (valores de `estado_evidencia`), no se guarda; la receta anterior se reemplaza en `proyecto.formatos["_receta"]` sin copia histórica; no hay control de `revision`.

### 12.1 Dónde se guarda (dentro de `proyecto.formatos`; `version_formato` sigue en 1)

- `_variables`: lista de `{nombre, hoja, unidad, unidad_analisis, fuente, responsable, estado_evidencia, ensayo_destructivo}`.
- `_tareas`: lista de `{id, descripcion, responsable, accion, liga, estado, origen}`; `estado` es `abierta` o `cerrada`; `origen` es `receta` o `auto`.
- `_analisis`: diccionario `{id: {modulo, estado, requiere, motivo, uid}}`; `estado` es `pendiente`, `disponible`, `analizado` o `aprobado` (este último reservado para la Entrega 4).
- `_revisiones`: lista de `{revision, huella, aplicada_en, origen, receta}` (la receta anterior completa como texto JSON), con tope de 20; al excederlo se descarta la más antigua y se avisa.
- `_receta` conserva `ids`, `json`, `origen`, `id_proyecto` y suma `revision` y `huella` de la última receta aplicada.

### 12.2 Variables

Se fusionan por `nombre`. Un estado nuevo reemplaza al previo salvo que el previo sea `REAL_VERIFICADO` y el nuevo no lo sea: bajar de verificado nunca ocurre en silencio y se trata como conflicto (12.5). `SINTETICO_DEMO` solo existe en demostración (ya validado en 0.26.0). Las variables que la receta nueva ya no menciona se conservan. Aun con «aplicar solo lo nuevo», un estado verificado se conserva con aviso.

### 12.3 Tareas

Se fusionan por `id`. Los pendientes que hoy se muestran como texto pasan a tareas `auto` con id estable (`auto:<tipo>:<objeto>`) y se cierran solas cuando se cumple su condición (llegaron los datos, el análisis se corrió). Una tarea cerrada a mano no se reabre automáticamente. Las tareas con `origen: receta` se conservan siempre.

### 12.4 Estado de cada análisis

`pendiente`: falta una columna `@x` o no tiene datos; se guardan `requiere` y un `motivo` legible. `disponible`: hay datos pero aún no se corrió. `analizado`: existe el resultado (`uid`). Un análisis nunca queda `analizado` sin resultado, y no se corre sin los datos mínimos del módulo.

### 12.5 Revisiones y conflictos

El control de revisión rige al actualizar un proyecto existente; al crear un proyecto nuevo no hay destino y no se aplica. Sea `n` la última revisión aplicada al proyecto destino (nula si ninguna) y `r` la `revision` de la receta recibida:

1. Receta sin `revision` (v1 o v2 sin campo): se aplica como hoy y `revision` queda nula.
2. Misma `huella` que una ya aplicada: no se cambia la estructura y se avisa «ya aplicada». Excepción aprobada: si la plantilla trae mediciones que el proyecto aún no tiene, se aplican solo esas columnas (es la forma normal de cargar datos de una plantilla ya llenada); sin datos nuevos es «ya aplicada».
3. `r` mayor que `n` y `revision_base` igual a `n` (ambas nulas cuenta como igual): se aplica.
4. `r` menor o igual que `n`: se avisa «más antigua» y por defecto no se aplica; el usuario puede forzar.
5. `r` mayor que `n` pero `revision_base` distinta de `n`: conflicto. El usuario elige entre cancelar o aplicar solo lo nuevo (la semántica actual de «Actualizar»). No hay fusión automática de campos distintos.
6. Antes de reemplazar `_receta`, la anterior pasa a `_revisiones`. Ningún cambio borra datos ni resultados válidos sin confirmación.

### 12.6 Proyecto real sin mediciones

Una receta v2 real con hojas vacías y variables `PENDIENTE_RECOLECCION` o `DESCONOCIDO` crea el proyecto, deja los análisis en `pendiente` con su motivo, genera las tareas, no carga ningún dato sintético y no inventa cifras.

## 13. Paquete de avance v1 (D-MIKE hacia el diagnóstico)

Archivo `.json` que D-MIKE exporta y el diagnóstico importa. Contiene solo estado: nunca datos de hojas, valores medidos ni resultados numéricos (eso es Entrega 4 y solo opcional).

```json
{
  "tipo": "dmike-avance",
  "avance_version": 1,
  "id_proyecto": "uuid-v4",
  "modo_proyecto": "real",
  "revision_aplicada": 3,
  "generado_en": "ISO-8601",
  "huella": "sha256:...",
  "fase_actual": "M",
  "estado_ruta": "no_determinado",
  "variables": [{"nombre": "", "estado_evidencia": "REAL_VERIFICADO"}],
  "analisis": [{"id": "", "modulo": "", "estado": "pendiente"}],
  "disenos": [{"id": "", "estado": "creado", "corridas": 13, "respuestas_capturadas": 0}],
  "tareas_abiertas": [{"id": "", "descripcion": ""}]
}
```

Reglas: `huella` se calcula igual que la de la receta. Sin `id_proyecto` no se puede exportar y se explica por qué (el proyecto viene de una receta v1 o se creó sin receta). `estado_ruta` toma uno de los valores de ESPEC_flujo 4.5 solo cuando se deduce de la existencia de objetos: `Sin datos` (hoja vacía), `Historicos cargados` (hay columnas con datos), `DOE disenado` (hay un diseño creado), `DOE ejecutado` (un diseño con todas sus respuestas capturadas). El resto de valores (medición evaluada, línea base, causas, mejora validada, control) no se infieren: se devuelve `no_determinado`. `disenos[].estado` es `creado` o `ejecutado` (valores definidos en la Entrega 2). `disenos[].id` es el id de la receta; desde la Entrega 3 cada elemento trae además `design_id` y `version_diseno` (sección 16), claves opcionales: `avance_version` sigue en 1 y no viajan niveles, `RunId`, huellas ni respuestas. `tareas_abiertas[].descripcion` se limita a texto generado por D-MIKE o por la receta, nunca a contenido de celdas.

## 14. Botones de reciprocidad

D-MIKE: `Archivo › Importar receta del diagnóstico…` (mismo flujo de Abrir proyecto con una receta, hoy ya disponible por `abrir_proyecto`) y `Archivo › Exportar paquete de avance…`. El diagnóstico (artefacto, se hace fuera del repositorio): botón «Importar paquete de avance» con selector de archivo y, como respaldo, pegar el texto. La web compara `id_proyecto` y `revision_aplicada` y nunca envía ni recibe datos crudos. Las rutas exactas de menú las propone Claude Code según `app/nucleo/menus.py`.

## 15. Versión y compatibilidad

D-MIKE pasa a 0.27.0. Las recetas que usen campos de la Entrega 2 declaran `dmike_minimo` «0.27»; un 0.26.0 las rechaza con «requiere D-MIKE 0.27». Un `.dmike` de 0.26.0 abre en 0.27.0 sin cambios; uno guardado en 0.27.0 abre en 0.26.0 ignorando las claves nuevas. `limites_seguros`, `design_id` y `run_id` siguen en la Entrega 3.

## 16. Entrega 3 — identidad del diseño (E3-2, implementada en el camino a 0.29.0)

Complementa las secciones 2.1 y 6.4. Todo vive en `proyecto.formatos["_disenos"][respuesta]` (`version_formato` sigue en 1); una versión anterior ignora las claves nuevas y un `.dmike` anterior abre sin cambios.

- `design_id`: «DIS-» y el nombre real de la columna de la respuesta («DIS-Y», «DIS-Y_2»), único en el proyecto. Lo asigna D-MIKE al crear el diseño; nunca la receta ni el usuario. Inmutable.
- `run_id`: `design_id` + «-R» + `OrdenEst` con 3 dígitos. Se deriva siempre del valor de la columna `OrdenEst` de la fila, nunca de su posición, y no se guarda: ordenar o filtrar la hoja no lo cambia. No viaja en la receta.
- `version_diseno`: entero que asigna solo D-MIKE. Nace en 1 al crear el diseño y sube en 1 únicamente cuando el usuario registra una versión nueva, después de que cambió la definición del diseño. La definición es la huella SHA-256 de los niveles reales de cada factor, el tipo de punto y el bloque de cada corrida (identificada por `OrdenEst`) y los nombres de los factores. La respuesta y `OrdenCorrida` no son parte de la definición. Mientras la huella actual difiere de la guardada, el estado de la definición es «cambiada». Cada versión reemplazada queda en `historial_versiones`. Regla de uso (E3-3): no se mezclan respuestas de versiones distintas.
- Proyecto real: el diseño agrega al final la columna `RunId` (rol `run_id`), de solo lectura. Demostración: la hoja no se toca; el `run_id` se deriva igual de `OrdenEst`.
- Diseños anteriores a 0.29 (sección 6.4): `design_id` derivado de su clave, versión 1 y `run_id` derivado de `OrdenEst`, sin escribir nada al abrir ni al consultar. Sin huella guardada su estado es «sin_linea_base»; al registrar una versión se guarda la huella de ese momento como línea base. No se les agrega la columna `RunId`.

## 17. Entrega 3 — respuestas por `run_id` (E3-3, implementada en el camino a 0.29.0)

Complementa la sección 16 y las reglas para DOE de ESPEC_flujo_real_dmaic (sección 5): nunca se empareja por el número de fila.

- Archivo de respuestas (CSV, TXT o Excel, primera fila de encabezados): `RunId` y `version_diseno` obligatorias; la columna de la respuesta con el nombre de la respuesta del diseño (o «Respuesta» o «Response»); una columna por factor, opcional, con su nombre. Si vienen los factores se verifican sus niveles contra los del diseño; si no vienen, la identidad se verifica solo con `RunId` y versión y se avisa. Las demás columnas se ignoran con aviso.
- Importación atómica: con un solo desajuste no se escribe nada y se informa cada error. Se rechaza: columna obligatoria ausente, corrida repetida, `RunId` que no pertenece al diseño o de más de un diseño, versión distinta de la vigente, niveles que no coinciden, respuesta no numérica, fila con respuesta y sin `RunId`, definición cambiada sin registrar, respuestas existentes de otra versión, y respuestas existentes distintas (salvo `sobrescribir`). Un vacío no se escribe ni cuenta como cero; N/A se respeta.
- No se mezclan versiones: `respuestas_version` (la deja D-MIKE) debe coincidir con `version_diseno` para analizar (FACTORIAL y RSM). La resolución manual, auditable y con motivo obligatorio, es declarar que las respuestas corresponden a la versión vigente (`confirmaciones_respuestas`). Cada importación queda en `importaciones` con el SHA-256 del archivo.
- Diseños anteriores a 0.29: no se verifican ni se modifican al abrir; al importar o registrar versión toman su línea base.
- Límite: el canal de la receta empata las respuestas de su plantilla por fila verificando los niveles de todos los factores; como la receta no lleva `run_id` (sección 2.1), no distingue réplicas ni puntos centrales de niveles idénticos.

## 18. Entrega 3 — archivo de corridas (E3-4, implementada en el camino a 0.29.0)

El diseño sale sin respuestas y vuelve con ellas por `run_id` (criterio 5 de ESPEC_flujo_real_dmaic).

- Exportar corridas: CSV UTF-8 con BOM, coma y punto decimal, o Excel (hoja «Corridas» y hoja «Diseño» con `design_id`, `version_diseno`, huella de la definición y niveles). Columnas, en el orden en que se corre: `RunId`, `version_diseno`, `OrdenCorrida`, `TipoPunto`, `Bloque`, los factores con sus niveles reales y la respuesta en blanco. No precarga respuestas aunque la hoja ya las tenga (salvo petición expresa). En demostración agrega la columna «marca» con la etiqueta sintética; en un proyecto real nunca.
- Se vuelve a importar con la sección 17: el archivo trae los factores, así que sus niveles se verifican; las columnas del archivo de corridas (`OrdenCorrida`, `TipoPunto`, `Bloque`, `marca`) se ignoran sin aviso. Un archivo de una versión anterior del diseño se rechaza.
- Con varios diseños en el proyecto se elige uno (`design_id`); se rechaza un diseño inexistente y la hoja con `OrdenEst` repetido.

## 19. Entrega 3 — límites seguros al crear el diseño (E3-5 parte A, implementada en el camino a 0.29.0)

Concreta la sección 8 (Decisión 5).

- Declaración: en «Crear diseño de experimentos», un campo con un par mínimo-máximo por factor, en el orden de los factores (por ejemplo «90, 125; 5, 40»). En la receta, `disenos[].limites_seguros` por factor (`{"A": {"min": 0, "max": 0}}`). Son la región autorizada y no los niveles bajo y alto del diseño. Obligatorios en modo real, opcionales en demostración (donde el diseño queda con región «no_declarada»). La exigencia a las recetas con `dmike_minimo` 0.29 o mayor, la declaración posterior en un diseño existente y la tarea «declarar límites seguros» son la parte B (abajo).
- Regla: todo punto del diseño en unidades reales (cubo, centrales, aristas de Box-Behnken y axiales) debe estar dentro de la región; un punto exactamente en el límite es válido. Si alguno sale, el diseño se rechaza antes de escribir nada en la hoja y el mensaje nombra el tipo de punto, la corrida estándar, el factor, el valor y el intervalo.
- Alternativa, solo para el central compuesto y con α = 1: la casilla «usar los límites seguros como niveles bajo y alto» toma los límites como niveles bajo y alto, de modo que los puntos axiales caen en las caras. Es un uso no nombrado por el curso (el ejemplo de 28_BB, línea 57, es consistente con cubo y axiales en el mismo rango); D-MIKE no le atribuye otras propiedades. La variante rotable, otros valores de α y cualquier otra alternativa (reducir α, desplazar el centro) son no respaldados.
- El diseño guarda `limites_seguros`, `region` («declarada» o «no_declarada») y `alternativa_axial_en_limites`.

### 19.1 Parte B — recetas y diseños existentes

- `validar`: si `disenos[].limites_seguros` viene, debe ser un objeto con un `{min, max}` numérico por cada factor de `parametros.nombres`, con mínimo menor que máximo (en cualquier versión). Se exige a los diseños `DISENO-RSM` de recetas con `dmike_minimo` 0.29 o mayor en modo real; en demostración es opcional y una receta anterior sin límites se acepta: su diseño queda con región «no_declarada».
- Región «no_declarada»: marca de un diseño sin región (anterior a 0.29, de una receta anterior, o de demostración sin límites). No invalida el diseño. En un proyecto real genera la tarea «declarar límites seguros» (`auto:limites:<design_id>`), derivada al consultar el seguimiento y el paquete de avance y nunca guardada; desaparece al declarar la región.
- Declarar después: todos los puntos que el diseño ya tiene deben caber en la región; si no, se rechaza y no se guarda nada (un diseño existente no se mueve). Un cambio de una región ya declarada queda en `historial_limites`.
- Todo diseño nuevo en modo real exige su propia región; no se bloquea crear uno nuevo porque otro diseño tenga la región sin declarar (así las recetas anteriores que crean varios diseños siguen funcionando). Que el análisis y el optimizador no recomienden parámetros fuera de la región, ni sin región en modo real, es E3-6.

## 19.2 Región autorizada en el análisis (E3-6, implementada en el camino a 0.29.0)

- `RSM` guarda en `datos.modelo_rsm.region` el estado de la región de su respuesta (`declarada`, `no_declarada`, `sin_diseno` o `no_aplica`) y los límites por factor en unidades reales. `no_aplica`: demostración o sin proyecto (la región es opcional). `sin_diseno`: la respuesta no viene de un diseño de D-MIKE; no hay a qué declarar la región y el análisis corre como antes con un aviso.
- Punto estacionario: con región declarada y el punto fuera, se reporta con su tipo y «no se recomienda». Con la región no declarada en modo real, se reporta como resultado del modelo y no como recomendación.
- Ruta de ascenso (28_BB RSM-ASCENSO): se muestran los pasos hasta el último que cabe en la región; el aviso nombra el paso que la cruzaría. Con la región no declarada en modo real no se muestra la ruta.
- Optimizador: busca en la intersección de la región elegida con la región autorizada de cada modelo; sin intersección da error. Con la región no declarada en modo real no emite combinación sugerida.
- Los resultados guardados antes de 0.29 no traen `region` y se tratan como antes.

## 19.3 Omisión justificada (E3-7, implementada en el camino a 0.29.0)

- `disenos[].omitido`: `{"que": "cribado" | "dcc" | "doe", "motivo": "texto"}`. El motivo es obligatorio. El paso no crea diseño ni tarea de correrlo, y no necesita `limites_seguros`.
- Registro en el `.dmike`: `_omisiones` (id del paso, qué, motivo, fecha, origen). No se borra. También se registra a mano con `Api.omitir_paso_doe`.
- Paquete de avance: clave opcional `omisiones` con `{id, estado, que}`; el motivo no viaja.

## 19.4 Auditoría del diseño (E3-8, implementada en el camino a 0.29.0)

- `Api.auditar_diseno(design_id)`: seis revisiones (alias, aleatorización, restricciones, curvatura, falta de ajuste, confirmación), cada una con `estado`, `detalle` y `fuente`. Solo en pantalla: no viaja en el paquete de avance.
- Un diseño nuevo guarda `aleatorizado`, `semilla` y `orden_creacion`; `RSM` y `FACTORIAL` guardan `datos.diagnostico` (`respuesta`, `alfa`, `curvatura_p`, `lof_p`). Claves nuevas y opcionales: los diseños y resultados anteriores se auditan como «no evaluable» donde falta el dato.
- Sin respuestas capturadas no se muestra ningún valor p. No hay umbrales propios: la significancia es la del análisis que se lee.

## 19.5 Plan de confirmación (E3-9, implementada en el camino a 0.29.0)

- Plan: `tipo` (`confirmacion` o `vigilancia`), `n_corridas`, `criterio_exito`, `condiciones`, `predicho` (valor, origen, `resultado_uid` opcional, `tipo_modelo`) y `observados`. Todo lo define el usuario; D-MIKE no propone tamaño de muestra ni criterio de éxito. Vive en el `.dmike` como `_confirmaciones`; no viaja en la receta ni en el paquete de avance.
- Comparación: observado menos predicho siempre. Intervalo de predicción individual solo con regresión simple (27_BB REG-PREDICCION); en cualquier otro modelo, «no respaldado» y sin veredicto.

## 19.6 Análisis sin diseño de D-MIKE y planes sin diseño (después del cierre de 0.29.0)

- En modo real, `RSM` solo analiza la respuesta de un diseño de D-MIKE o una segunda respuesta medida en las mismas corridas (se liga por los nombres de los factores). En demostración no se bloquea. El optimizador solo usa modelos `RSM` guardados.
- Un plan de confirmación puede no pertenecer a un diseño (`design_id` nulo): se registra y se compara igual y se ve en la sección «Planes de confirmación» de «Diseños del proyecto».
