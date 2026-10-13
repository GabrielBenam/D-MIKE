# ESPEC_receta_v2 — Contrato de receta v2 de D-MIKE

Versión del documento: 1.0 (13/10/2026). Programa objetivo: D-MIKE 0.26.0. Base: ENTREGA_0_auditoria_AS-IS.md, ESPEC_flujo_real_dmaic.md (secciones 3 a 5 y 10) y lectura del código publicado del Diagnóstico en línea. Estado de verificación: diseño aprobado por el usuario; nada de lo descrito como «nuevo» está implementado todavía. Lo no verificado en código se marca «pendiente de validación».

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

Ejecutar en un proyecto nuevo. Si no hay proyecto abierto con ese `id_proyecto`, el proyecto nuevo lo guarda en `_receta.id_proyecto`. Si ya hay un proyecto abierto con ese `id_proyecto`, no se asigna en silencio ni se rechaza sin salida: D-MIKE ofrece actualizar ese proyecto o crear uno nuevo sin `id_proyecto` (queda nulo). La unicidad se verifica solo contra proyectos abiertos; verificar contra `.dmike` cerrados queda fuera de esta entrega porque no se abren sin elegirlos.

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

Pendiente de validación: la lista de huellas de recetas sintéticas, las rutas de código para la etiqueta sintética en exportaciones, y el comportamiento del artefacto una vez cambiado (sus secciones de entrevista, retoma y aislamiento entre folios se auditan en la matriz TO-BE). Fuera de alcance de esta especificación: Gage R&R anidado, quitar el folio de `.dmike` antiguos, verificar `id_proyecto` contra `.dmike` cerrados, paquete de avance.

## 11. Trazabilidad con ESPEC_flujo_real_dmaic.md (sección 10)

Criterios 4 y 16: secciones 6 y 9. Criterio 11: sección 6, punto 5. Criterios 1, 2, 3, 12: Entrega 2 con las secciones 2 y 5. Criterios 5 a 10: Entrega 3 con las secciones 2, 7 y 8. Criterios 13 y 14: Entrega 4. Criterio 17: sección 3 (folio) y matriz TO-BE.
