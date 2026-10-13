# D-MIKE 0.25.0 — Auditoría crítica y especificación para rediseñar el manual de uso

> **Destinatario:** Claude, responsable de revisar el manual, el código y la documentación de D-MIKE.
> **Documento base:** `D-MIKE_Manual_de_uso_v025.pdf` (138 páginas).
> **Carácter:** diagnóstico editorial y requisitos de mejora. Las propuestas no deben confundirse con funciones ya implementadas.

## 1. Objetivo de este encargo

Reestructurar el manual de D-MIKE para que deje de funcionar principalmente como un catálogo de comandos y se convierta en una guía de aprendizaje, consulta y ejecución de proyectos Lean Six Sigma DMAIC. La documentación debe permitir que cualquier usuario comprenda **para qué sirve cada comando, qué datos requiere, cómo calcula sus resultados, qué salidas concretas produce, cómo interpretarlas y qué hacer después**.

**Regla de trabajo:** inspecciona el manual completo y, si están disponibles, el código, las pantallas y las salidas reales del programa. Conserva toda la información técnica correcta. No inventes funcionalidades, rutas, fórmulas, outputs o resultados. Si no puedes verificar una función, indícalo como pendiente de validación.

## 2. Diagnóstico general

El manual actual es útil como referencia funcional, pero presenta las características de documentación generada a partir de fichas técnicas más que de una guía orientada al usuario:

1. Organiza la mayor parte del contenido por pestañas de la cinta y por nombres de comandos, no por problemas que necesita resolver una persona.
2. Define las fichas de módulos mediante los campos «Ruta», «Qué pide», «Qué entrega», «Qué revisa», «Fuentes» y «Exportación» (sección 1.2). Esta estructura no es suficiente para enseñar el fundamento, la ejecución, la interpretación y la decisión posterior.
3. Describe resultados con expresiones genéricas, en ocasiones reiteradas, en lugar de explicar las tablas, gráficas y parámetros concretos de cada análisis.
4. No desarrolla sistemáticamente la cadena entre datos, fórmulas, supuestos, cálculos y salidas.
5. Ofrece pocos microejemplos completos dentro del catálogo; el caso maestro aparece al final, después de una sección extensa de funcionalidades.
6. Mezcla elementos de uso cotidiano, operaciones de edición, análisis estadísticos y herramientas DMAIC bajo plantillas narrativas similares, aunque demandan explicaciones distintas.
7. Emplea referencias internas a bloques del curso como si fueran explicaciones autosuficientes.
8. Presenta el caso maestro con datos sintéticos prediseñados, lo cual sirve para demostración, pero no enseña por sí solo a ejecutar proyectos reales cuando los resultados aún son desconocidos.
9. Contiene errores o inconsistencias editoriales que deben auditarse, entre ellos la paginación de los apéndices en el índice.

**Problema central:** falta una secuencia consistente de **problema → datos → método → fórmulas → procedimiento → output → interpretación → decisión**.

## 3. Hallazgos localizados en el manual

### 3.1 Estructura de navegación

- El capítulo 4 («Módulos por pestaña de la cinta») comienza en la página 9 y recorre Archivo, Editar, Datos, Calc, Estadística, Gráficas, Herramientas de calidad, Lean, Gestión, Proyecto, Ver y Ayuda hasta la página 105 aproximadamente.
- El capítulo 5 («Recetas y Diagnóstico en línea») inicia en la página 106.
- El capítulo 6 («Caso maestro de principio a fin») inicia en la página 107.
- El índice muestra referencias poco útiles para los apéndices A y B (aparecen asociados a la página 3); verificar y corregir la navegación real y los hipervínculos.

**Crítica:** la estructura es práctica si el usuario ya sabe qué botón busca, pero no cuando parte de una pregunta como «¿mi proceso es estable?», «¿qué factores afectan la resistencia?» o «¿dónde está el cuello de botella?».

**Requisito:** mantener un índice funcional por pestaña y añadir índices por necesidad, tipo de dato, resultado esperado, fase DMAIC y nivel de experiencia.

### 3.2 Fichas de comandos

El formato existente (ruta/entradas/salidas/validaciones/fuentes/exportación) debe conservarse como núcleo de referencia técnica, pero complementarse con explicaciones pedagógicas. Ejemplos a inspeccionar en detalle:

- **Buscar y reemplazar (p. 10):** revisar si hay texto genérico sobre conclusiones analíticas, avisos de supuestos o exportación estadística que no corresponda a una operación de edición. Documentar únicamente outputs realmente implementados, tales como conteos o registros de sustitución, si existen.
- **Estadísticos de columna (aprox. p. 18):** explicar con fórmulas y ejemplos la media, mediana, moda, dispersión y demás estadísticos que el programa efectivamente entregue; aclarar datos faltantes, agrupación y tratamiento de atípicos.
- **Distribuciones y normalidad (aprox. p. 19):** explicar el propósito, la prueba efectivamente implementada, hipótesis, supuestos, interpretación del valor p, salidas y decisiones posteriores; no inventar pruebas o umbrales.
- **Regresión, ANOVA, DOE, cartas de control y capacidad:** desarrollar las tablas de resultados **reales** del software parámetro por parámetro, con unidades, hipótesis, limitaciones y ejemplos numéricos verificables.

### 3.3 Documentación de outputs

La expresión genérica «conclusión en lenguaje llano, avisos sobre los datos excluidos y supuestos del análisis» no equivale a documentar una salida. En cada comando se debe describir:

- Nombre exacto del output visible en la interfaz.
- Forma de presentación: tabla, gráfica, indicador, texto, advertencia o archivo.
- Variable o estadístico que representa.
- Fórmula o algoritmo, si corresponde.
- Unidades y rango o escala cuando exista.
- Qué resultado se considera informativo, anómalo o insuficiente, fundamentándolo.
- Cómo leerlo sin concluir más de lo que permiten los datos.
- Decisión o análisis siguiente que puede justificar.

Adjuntar capturas reales y anotadas si están disponibles. No copiar una lista genérica de salidas de Minitab: verificar las salidas de **D-MIKE**.

### 3.4 Fórmulas y rigor técnico

Para cada comando cuantitativo, documentar:

1. Ecuación legible en notación matemática.
2. Definición de símbolos y unidades.
3. Tipo y estructura de datos.
4. Supuestos y requisitos previos.
5. Tratamiento de datos faltantes, atípicos y filtros.
6. Ejemplo con valores pequeños y sustitución paso a paso.
7. Resultado numérico contrastado con D-MIKE.
8. Interpretación válida y limitaciones.
9. Referencia bibliográfica y, cuando corresponda, referencia a la base del curso.

Distinguir **límites de especificación** de **límites de control**; significancia estadística de relevancia práctica; correlación de causalidad; y capacidad de proceso de estabilidad. No trasladar automáticamente fórmulas de manufactura a documentación técnica sin examinar unidades y condiciones.

### 3.5 Caso maestro y datos sintéticos

El capítulo 6 presenta un caso sobre la resistencia de uniones adhesivas en paneles compuestos. El propio manual establece que los datos son sintéticos, no resultados empresariales reales.

El ejemplo incluye línea base, defectos, estudio de medición, cribado experimental, un diseño central compuesto y datos posteriores a la mejora. Este formato demuestra varios módulos, pero anticipa datasets que un proyecto real solo podría producir conforme avance.

**Requisito editorial y metodológico:** conservar el caso sintético, correctamente rotulado como demostración reproducible, y añadir un recorrido **Proyecto real guiado**. En él, la receta inicial solo debe pedir información disponible, planificación de medición y definición provisional; los DOE se diseñan y ejecutan dentro de D-MIKE cuando haya evidencia y autorización; las respuestas experimentales y datos posteriores no deben generarse por defecto.

La narrativa de cada etapa debe contestar: «qué sabemos», «qué falta», «por qué este método», «qué produjo», «qué significa», «qué decisión sigue» y «qué hacemos si el resultado es inesperado».

## 4. Nuevo índice editorial recomendado

I. **Orientación y mapa del software.** Propósito de D-MIKE, estructura, conceptos esenciales y convenciones.

II. **Primeros pasos.** Crear proyecto, importar datos, configurar variables, guardar, consultar y exportar resultados.

III. **Guía de selección metodológica.** Árboles de decisión por síntoma, tipo de dato, objetivo estadístico y fase DMAIC.

IV. **Herramientas explicadas.** Fichas pedagógicas completas y ejemplos breves de los comandos, sin perder la referencia a la cinta.

V. **Rutas prácticas.** Secuencias cortas de 2 a 4 herramientas para problemas comunes: retrasos, defectos, variabilidad, recursos compartidos, auditorías, etc.

VI. **Caso maestro demostrativo.** Caso sintético reproducible con datos y respuestas verificables; distinguirlo claramente de una intervención real.

VII. **Caso maestro real guiado.** Datos progresivos, decisiones, recetas iterativas, mediciones, experimentos y plan de control.

VIII. **Referencia rápida de comandos.** Nombre, ruta, atajo, prerequisitos, entradas, outputs y estado de implementación.

IX. **Fundamentos matemáticos y criterios.** Fórmulas, definiciones, algoritmos, supuestos, límites y bibliografía.

X. **Errores frecuentes y solución de problemas.** Mensajes de D-MIKE, causas posibles y medidas correctivas.

Puede adaptarse esta estructura a las restricciones del proyecto siempre que se mantenga la separación entre tutorial, referencia operativa y fundamento matemático.

## 5. Plantilla obligatoria para documentar cada módulo

Aplicar solo las secciones pertinentes al tipo de módulo; evitar inventar fórmulas para herramientas cualitativas.

1. **Nombre y propósito.** ¿Qué problema ayuda a resolver?
2. **Cuándo utilizarlo y cuándo no.** Condiciones y preguntas típicas.
3. **Fase DMAIC y relaciones.** Pasos previos y siguientes, si corresponden.
4. **Ubicación en D-MIKE.** Ruta exacta, atajos y estado de disponibilidad.
5. **Entradas.** Columnas, campos, tipos, unidades y ejemplo de estructura.
6. **Preparación y validación.** Calidad de datos y requisitos.
7. **Fundamento o lógica.** Fórmulas, criterios o metodología paso a paso.
8. **Procedimiento en la interfaz.** Secuencia verificable de acciones y opciones.
9. **Outputs reales esperados.** Inventario completo de tablas, gráficas, números, archivos y avisos.
10. **Cómo interpretar cada output.** Qué significa, qué no significa, qué signos ameritan investigar.
11. **Ejemplo reproducible.** Dataset breve, ejecución y resultados contrastados.
12. **Decisiones posteriores.** Qué hacer según distintos resultados posibles.
13. **Errores y resolución.** Entradas inválidas, supuestos fallidos, mensajes, ausencias.
14. **Exportación y trazabilidad.** Formatos, nombres, reproducibilidad.
15. **Fuentes y versión.** Bibliografía, IDs de curso y versión de D-MIKE.

### 5.1 Tipos de ficha

- **Operación de interfaz / edición:** prioridad en acciones, estados previos, confirmación del cambio, riesgos de pérdida de datos y reversión.
- **Análisis estadístico:** prioridad en hipótesis, supuestos, cálculo, outputs e interpretación.
- **Formato Lean/calidad:** prioridad en objetivo, responsables, campos, criterio de completitud y ejemplo diligenciado.
- **Gestión de proyectos:** prioridad en flujo, roles, dependencias, estados, entregables y seguimiento.

No forzar todos los comandos dentro de la misma prosa genérica.

## 6. Ejemplo de cómo debe verse una ficha: Estadísticos de columna

> **Nota:** el contenido siguiente es una muestra del estilo deseado. Claude debe verificar qué métricas genera realmente D-MIKE, así como la ruta exacta del comando.

**Pregunta:** ¿Cómo se distribuyen los tiempos de ejecución de una tarea?

**Datos ilustrativos:** 8, 10, 10, 12 y 15 minutos.

**Media:** `x̄ = (8+10+10+12+15)/5 = 11 minutos`.

**Mediana:** 10 minutos.

**Moda:** 10 minutos.

**Desviación estándar muestral:** `s = sqrt[Σ(xᵢ−x̄)²/(n−1)] = sqrt(28/4) ≈ 2.65 minutos`.

**Interpretación:** el promedio observado es 11 minutos y la dispersión muestral estimada es de alrededor de 2.65 minutos. Con solo cinco observaciones no puede asumirse estabilidad ni capacidad del proceso; se necesitaría un plan de medición adecuado.

**Outputs a comprobar:** tabla de estadísticos que entregue realmente D-MIKE, indicadores gráficos si existen, cantidad de datos válidos y advertencias. Añadir capturas con anotaciones y una explicación de cada valor.

**Siguiente paso:** si interesa estudiar cambios durante el tiempo, investigar herramientas temporales apropiadas; si interesa comparar equipos o tipos de trabajo, revisar la segmentación y análisis comparativos.

## 7. Método de auditoría y reconstrucción para Claude

### Fase 1 — Inventario

1. Extraer índice, secciones, fichas, comandos, fórmulas, ejemplos, outputs, imágenes, referencias y enlaces.
2. Construir una tabla de cobertura con cada comando y sus secciones pedagógicas presentes o ausentes.
3. Identificar incoherencias de nomenclatura, duplicados, texto de plantilla repetido y paginación incorrecta.
4. Separar comandos operativos de funcionalidades propuestas, en desarrollo o no verificadas.

### Fase 2 — Verificación funcional

1. Inspeccionar el código fuente o ejecutar el software si está disponible.
2. Identificar entradas, validaciones, métodos, resultados y exportaciones por comando.
3. Comparar el output real con lo declarado por el manual.
4. Marcar discrepancias como **documentación incorrecta**, **error de software**, **diferencia de versión** o **pendiente de confirmación**.
5. No alterar fórmulas ni algoritmos exclusivamente para que coincidan con el texto del manual; investigar cuál es correcto.

### Fase 3 — Reconstrucción editorial

1. Diseñar el índice dual: por rutas de software y por preguntas del usuario.
2. Desarrollar plantillas diferenciadas según categoría de comando.
3. Reescribir cada ficha a partir de las funciones verificadas.
4. Añadir microejemplos y referencias cruzadas con comandos relacionados.
5. Crear un glosario usable y una sección matemática bien organizada.
6. Corregir índices, numeración, nomenclatura y enlaces internos.

### Fase 4 — Reconstrucción pedagógica del caso maestro

1. Mantener una edición demostrativa sintética, completamente reproducible.
2. Crear una edición real guiada con datos adquiridos progresivamente.
3. Mostrar explícitamente las decisiones tomadas después de cada resultado.
4. No exigir desde la receta inicial datos posteriores a la mejora ni respuestas de diseños experimentales todavía no ejecutados.
5. Documentar rutas alternativas cuando fallen supuestos, falten observaciones o no aparezcan los efectos previstos.
6. Vincular el caso con las fichas de comandos y el diagnóstico web.

### Fase 5 — Validación editorial y técnica

1. Revisar que cada ejemplo reproduce el cálculo prometido.
2. Revisar que cada output coincide con el programa y la versión declarada.
3. Probar los enlaces y los índices.
4. Comprobar la lectura de tablas, ecuaciones, pies de figura y capturas.
5. Pedir revisión de un usuario principiante y de uno técnicamente avanzado, si están disponibles.

## 8. Entregables solicitados a Claude

1. **Informe de auditoría** del manual actual con hallazgos, evidencia (página/sección), gravedad y solución recomendada.
2. **Matriz de trazabilidad de comandos**: comando → ruta → entradas → cálculos → outputs reales → ejemplo → documentación actual → acciones faltantes.
3. **Nuevo índice y arquitectura editorial**, con relación entre capítulos.
4. **Plantilla(s) de fichas** para estadística, operaciones, Lean y gestión.
5. **Manual revisado completo**, conservando la información vigente y corrigiendo inconsistencias identificadas.
6. **Ejercicios breves verificables** por herramienta, donde resulte útil.
7. **Caso maestro sintético corregido** y **caso de proyecto real guiado**, diferenciados.
8. **Bitácora de cambios** que explique qué se modificó, por qué y contra qué evidencia se verificó.
9. **Lista de brechas del software** descubiertas al documentarlo, sin atribuir implementaciones que no se hayan hecho.
10. **Lista de pendientes de validación** cuando no haya acceso a la aplicación, fuente o datos necesarios.

## 9. Criterios de aceptación

El rediseño solo debe considerarse listo cuando:

- [ ] Cada comando existente puede encontrarse por nombre, pestaña y problema que ayuda a resolver.
- [ ] Cada comando explica entradas, pasos y outputs con suficiente especificidad.
- [ ] Cada cálculo estadístico documentado tiene fórmula, símbolos, supuestos y ejemplo contrastable.
- [ ] Cada gráfica y tabla de resultados está interpretada, no solo enumerada.
- [ ] Las conclusiones no exceden la evidencia estadística.
- [ ] Los módulos no estadísticos tienen documentación acorde a su función, sin texto analítico de plantilla irrelevante.
- [ ] Los ejemplos sintéticos están claramente marcados y no se presentan como datos de empresas.
- [ ] El caso real guiado no presupone respuestas experimentales ni mejoras futuras.
- [ ] La documentación distingue capacidades existentes, propuestas y pendientes de comprobación.
- [ ] Índice, paginación, referencias cruzadas y enlaces son correctos.
- [ ] Las entradas, algoritmos y salidas coinciden con el software real, o están marcadas las discrepancias pendientes.
- [ ] Existe trazabilidad entre manual, módulos de D-MIKE, diagnóstico web y etapas DMAIC.

## 10. Instrucción final para Claude

**No te limites a corregir redacción, acortar párrafos o embellecer el PDF.** El objetivo es mejorar sustancialmente la capacidad del usuario para comprender y ejecutar cada análisis.

Trabaja a partir del manual y del software real, audita cada comando, conserva el rigor matemático y distingue las correcciones documentales de los cambios funcionales. Mantén como eje editorial:

> **Problema → Datos → Método → Fórmulas → Ejecución → Outputs → Interpretación → Decisión.**

El resultado debe servir como manual de aprendizaje, guía operativa y referencia técnica confiable; además, debe acompañar el nuevo flujo de recetas iterativas y proyectos reales de D-MIKE.
