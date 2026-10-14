# Caso integral D-MIKE, paso a paso

**Resistencia de uniones adhesivas en paneles de compuesto**
Versión del programa: D-MIKE 0.21.1 · Documento de trabajo para reproducir el caso y armar un proyecto propio.

> **Sobre los datos.** Todo el caso usa **datos hipotéticos (sintéticos)**. No vienen de ninguna empresa, cliente ni prueba real. Cada conjunto de datos se generó con un modelo matemático conocido y una semilla fija, que se describen en la sección 2. Los textos de los formatos (nombres, montos, fechas) también son hipotéticos y se indica de dónde sale cada uno. Las fórmulas y criterios estadísticos citan el archivo y la sección de la base del curso.

---

## Contenido

1. Cómo leer este documento
2. El caso y el origen de cada dato
3. Preparar el proyecto en D-MIKE
4. Definir
5. Medir
6. Analizar
7. Mejorar (cribado, superficie de respuesta y optimización)
8. Controlar
9. Resumen de decisiones y resultados
10. Cómo armar tu propio proyecto con este método
11. Notas de rigor: lo que el caso hace bien y lo que debes corregir en uno real

---

## 1. Cómo leer este documento

**Rutas de menú.** Se escriben así: `Estadística › ANOVA de un factor…`. Con la cinta fija, «Estadística» es una pestaña de la cinta y «ANOVA de un factor» es un botón dentro de ella. Con la cinta contraída, son el menú y su opción. También puedes escribir el nombre en la paleta de comandos (Ctrl+K) y presionar Enter.

**Campos de diálogo.** Se escriben como «Nombre del campo» = valor. Los nombres son exactamente los que muestra el programa.

**Columnas.** Se citan por su nombre (por ejemplo `resistencia_base`). En los diálogos aparecen como «C7 resistencia_base», con el número que tengan en tu hoja.

**Archivos.** Todos están en la carpeta `D-MIKE_caso_integral`:

| Archivo | Contenido |
|---|---|
| `caso_integral_uniones_adhesivas.dmike` | El proyecto terminado (para comparar con el tuyo) |
| `datos/01_linea_base.csv` | 100 mediciones de la situación actual |
| `datos/02_defectos.csv` | 86 defectos clasificados |
| `datos/03_gage_rr.csv` | Estudio del sistema de medición |
| `datos/04_cribado_fraccionado.csv` | Respuestas del experimento de cribado |
| `datos/05_diseno_central_compuesto.csv` | Respuestas del experimento de optimización |
| `datos/06_despues.csv` | 60 mediciones con el proceso mejorado |

**Dos formas de seguirlo.**
- *Solo revisar:* abre el `.dmike` y usa `Proyecto › Resultados del proyecto…` para abrir cada análisis.
- *Reproducirlo desde cero (recomendado):* sigue las secciones 3 a 8 en un proyecto nuevo. Al final, tus resultados deben coincidir con los de la sección 9.

---

## 2. El caso y el origen de cada dato

### 2.1 Situación (hipotética)

Una línea de ensamble une paneles de material compuesto con adhesivo epóxico curado en horno. El cliente exige una **resistencia al cortante de la unión de al menos 30 MPa** (límite inferior de especificación, LIE). Muchos paneles no la alcanzan y se retrabajan o se desechan.

El equipo sospecha del ciclo de curado (temperatura y tiempo), que se copió de otro adhesivo, y de la calidad de los lotes de adhesivo.

### 2.2 Origen de cada conjunto de datos

Todos los datos se generaron con el programa `herramientas/generar_caso_integral.py` (incluido en el código de D-MIKE), con la semilla aleatoria 2026. La tabla dice qué modelo produjo cada dato y cómo obtendrías ese dato en un caso real.

| Conjunto | Modelo que lo generó (hipotético) | En un caso real lo obtendrías… |
|---|---|---|
| **01 Línea base** (100 filas) | Temperatura real ~ Normal(118 °C, 3); tiempo real ~ Normal(75 min, 6). Resistencia = 31.4 + 0.18·(T − 118) + 0.03·(t − 75) − 1.9 si el lote es L3 − 0.6 si el turno es C + ruido Normal(0; 1.1). Porosidad = máx(0.4; 2.6 − 0.12·(Resistencia − 31) + ruido Normal(0; 0.2)). Cuatro probetas por día, del 1 al 25 de agosto; lotes L1 a L4 y turnos A, B y C rotando. | Con la hoja de recolección (sección 5.1): probetas de cortante cortadas de paneles reales, el registro del horno y el número de lote del adhesivo. |
| **02 Defectos** (86 filas) | Conteos fijos: porosidad alta 31, despegue en borde 22, adhesivo insuficiente 14, contaminación de superficie 9, espesor fuera 6, otro 4; en orden aleatorio. | El registro de rechazos de inspección del mismo periodo. |
| **03 Gage R&R** (60 filas) | 10 probetas, 3 operadores (Ana, Beto, Carla), 2 réplicas. Medición = 31 + (número de pieza − 5.5)·0.55 + sesgo del operador (Ana 0, Beto +0.12, Carla −0.08) + ruido Normal(0; 0.12). | Un estudio cruzado: cada operador mide cada probeta dos veces sin saber cuál es. En pruebas destructivas se usan probetas «gemelas» del mismo panel. |
| **04 Cribado** (11 corridas) | En unidades codificadas (−1 a +1): Resistencia = 33.0 + 1.6·A + 1.0·B + 0.03·C + 0.02·D − 0.5·A·B − 1.2 en los puntos centrales + ruido Normal(0; 0.3). A = temperatura, B = tiempo, C = presión, D = nivel de limpieza. | Corriendo los 11 experimentos en el orden que da D-MIKE y probando una probeta de cada uno. |
| **05 Diseño central compuesto** (13 corridas) | Con T = (temperatura − 125)/10 y S = (tiempo − 100)/20: Resistencia = 36.2 + 1.1·T + 0.7·S − 1.4·T² − 0.9·S² − 0.5·T·S + ruido Normal(0; 0.35). Porosidad = 1.8 − 0.35·T − 0.25·S + 0.30·T² + 0.20·S² + ruido Normal(0; 0.07). | Igual que el cribado, midiendo la resistencia y la porosidad (por ultrasonido o por corte metalográfico) en cada corrida. |
| **06 Después** (60 filas) | Resistencia ~ Normal(35.8; 1.1), cinco probetas por día durante 12 días de octubre. | Las mediciones de rutina del plan de control con el ciclo nuevo. |

> **Por qué conviene conocer el modelo.** Como sabes qué efectos «verdaderos» puse en los datos, puedes comprobar si cada análisis los encuentra. Por ejemplo, el ANOVA debe señalar el lote L3, el cribado debe señalar temperatura, tiempo y su interacción, y la superficie debe tener un máximo. Es la mejor forma de aprender a confiar en (y desconfiar de) un análisis.

---

## 3. Preparar el proyecto en D-MIKE

### 3.1 Crear el proyecto y sus datos fijos

1. Abre D-MIKE. En la pantalla de inicio haz clic en «Nuevo proyecto».
2. Abre `Proyecto › Datos fijos del proyecto…`.
3. Captura estos valores (hipotéticos):
   - «Proyecto» = `Resistencia de uniones adhesivas en paneles de compuesto`.
   - «Cliente o área» = `Ensamble de compuestos, línea 1`.
   - «Responsable» = tu nombre.
4. Haz clic en «Aceptar».
5. Guarda de inmediato con `Archivo › Guardar como…` (Ctrl+Mayús+S). Después guarda con Ctrl+S cada vez que termines un análisis.

**Por qué:** los datos fijos se copian solos al encabezado de todos los formatos y reportes. Captúralos una vez.

### 3.2 Activar los módulos de cada fase

El caso se armó con un perfil del diagnóstico. Si no tienes uno, actívalos a mano:

1. En el riel DMAIC de la izquierda, haz clic en la letra de la fase (por ejemplo **D**).
2. Abre el grupo «Inactivos».
3. Haz clic en «+» junto a cada módulo de la lista siguiente.

| Fase | Módulos activados en el caso |
|---|---|
| D | Acta del proyecto, SIPOC, Definición del problema, Kano, QFD, Árbol CTQ, Registro de interesados, RACI, EDT, Cronograma, Monte Carlo, Riesgos, Justificación de negocio, Enfoque, Bitácora |
| M | Hoja de recolección, Gage R&R de variable, Distribuciones y normalidad, Capacidad, Desempeño (DPMO) |
| A | Pareto, Ishikawa, 5 Porqués, ANOVA, Correlación, Regresión, Pruebas de hipótesis |
| I | Crear diseño de experimentos, Analizar diseño factorial, Superficie de respuesta, Optimizador, AMEF, Poka Yoke |
| C | Cartas de control, Plan de control, Tablero semanal, Valor ganado, Costo de calidad, Checklist de fase, A3, Cierre y lecciones |

**Por qué:** activar no es obligatorio para usar un módulo, pero hace visible la ruta del proyecto. El avance de cada módulo (pendiente, en curso o hecho) alimenta la pantalla de inicio, el tablero y la ruta DMAIC.

### 3.3 Cargar los datos observacionales (Medir y Controlar)

Los experimentos (archivos 04 y 05) no se importan: los genera D-MIKE en la sección 7. Primero carga los otros cuatro archivos.

1. `Archivo › Importar archivo (CSV, TXT, Excel)…`
2. Elige `datos/01_linea_base.csv`. Se agregan 7 columnas: `fecha`, `turno`, `lote_adhesivo`, `temp_real_C`, `tiempo_real_min`, `resistencia_MPa` y `porosidad_pct`.
3. Repite con `02_defectos.csv`, `03_gage_rr.csv` y `06_despues.csv`. Cada importación agrega sus columnas a la derecha de las anteriores.
4. Renombra las columnas repetidas para que no se confundan. Haz doble clic en el nombre (F2) y escribe el nuevo. Por ejemplo:
   - la `resistencia_MPa` de la línea base → `resistencia_base`;
   - la de «después» → `resistencia_despues`;
   - las del Gage R&R → `parte_rr`, `operador_rr` y `medicion_rr`.

**Por qué renombrar:** los diálogos muestran las columnas por nombre. Nombres únicos y claros evitan elegir la columna equivocada, el error más común en un análisis.

---

## 4. Definir

En Definir no hay cálculos estadísticos: se fija qué problema se resuelve, para quién y con qué recursos. Todos los textos de esta sección son **hipotéticos**, redactados para el caso.

### 4.1 Definición del problema

**Comando:** `Herramientas de calidad › Definición del problema`

| Campo | Valor | Origen |
|---|---|---|
| Sujeto | las uniones adhesivas de la línea 1 | Planteamiento del caso |
| Predicado | no alcanzan la resistencia al cortante requerida | Planteamiento del caso |
| Dónde | Horno de curado 2 | Hipotético |
| Cuándo | Desde junio de 2026, todos los turnos, más en el lote L3 | Hipotético; el ANOVA lo confirma después (6.3) |
| Magnitud | 26 % de las probetas bajo 30 MPa | **De los datos**: 26 de 100 valores de `resistencia_base` < 30 |
| Estándar | ≥ 30 MPa, Cpk ≥ 1.33 | Requisito del cliente y criterio de 16_GB CAP-INTERPRETACION |

**Por qué este formato primero:** separa el síntoma (baja resistencia) de las causas supuestas. Así el equipo no empieza el proyecto con la solución decidida (03_SOLUCION_PROBLEMAS, PS-3PASOS).

> En el proyecto entregado, la magnitud dice «18 %», un valor inicial hipotético. Al medir resultó 26 %: en tu proyecto usa siempre el valor medido (ver sección 11).

### 4.2 Acta del proyecto (Charter)

**Comando:** `Herramientas de calidad › Acta del proyecto (Charter)`

Valores capturados (hipotéticos salvo donde se indica):
- «Caso de negocio»: rechazos por baja resistencia que cuestan retrabajo y pruebas.
- «Alcance»: línea 1, unión adhesiva; no incluye laminado ni pintura.
- «Requisitos de alto nivel»: resistencia ≥ 30 MPa con Cpk ≥ 1.33.
- Propósito, tabla de CTQ: «Resistencia al cortante (MPa)», base 30.8 (media medida en 5.3), objetivo 36.
- «Recursos financieros preaprobados»: 250 000.
- Patrocinador y su autoridad, criterios de aprobación y de salida, hitos (línea base 15/08, diseño de experimentos 12/09, cierre 16/10).

**Por qué:** el acta autoriza el proyecto y fija qué es éxito antes de ver los datos (PMBOK 6, 4.1.3.1). Si falta el patrocinador, los criterios de salida o los hitos, el formato lo avisa. El objetivo de 36 MPa se fijó con el margen que pide el Cpk. Con una desviación de alrededor de 1.1 MPa, Cpk = (media − 30)/(3 × 1.1) ≥ 1.33 exige una media ≥ 34.4 MPa; se redondeó a 36 para tener holgura.

### 4.3 SIPOC

**Comando:** `Herramientas de calidad › Diagrama SIPOC`

Proceso: limpiar superficie → aplicar adhesivo → curar en horno → probar cortante. Entradas y proveedores: adhesivo (almacén), paneles (laminado) y horno calibrado (mantenimiento).

**Por qué:** delimita el proceso y muestra que el adhesivo y el horno vienen de fuera del alcance. Esto anticipa dos frentes de causa: material y método.

### 4.4 Kano, QFD y árbol CTQ

**Comandos:**
- `Herramientas de calidad › Modelo de Kano`
- `Herramientas de calidad › QFD`
- `Herramientas de calidad › Árbol CTQ`

**Kano** (respuestas hipotéticas de una entrevista al cliente):
- «Unión que no se despega» resultó **básico**: el cliente lo espera y le disgusta si falta.
- «Certificado de prueba por lote» resultó **de deleite**.

**QFD.** Se capturó en este orden:

1. **Requisitos técnicos (cómos):**

   | Requisito técnico | Dirección de mejora | Valor objetivo |
   |---|---|---|
   | Temperatura de curado | ◇ objetivo | 125 °C |
   | Tiempo de curado | ◇ objetivo | 100 min |
   | Porosidad | ▼ minimizar | ≤ 1.5 % |
   | Limpieza de superficie | ▲ maximizar | nivel 3 |

   Agrega su dificultad y la evaluación técnica (nuestra y de dos proveedores competidores). Todo es hipotético.

2. **Requisitos del cliente (qués):** unión resistente (importancia 5), sin burbujas visibles (4), entrega a tiempo (3) y trazabilidad por lote (2). Para cada uno: la evaluación propia y de competidores (1 a 5), la meta y el punto de venta.
3. **Relaciones (9, 3, 1):** se eligen en la tabla, o con clic en las celdas de la casa de la calidad.
4. **Techo de correlaciones:** temperatura y tiempo positiva (+); temperatura y porosidad negativa (−); tiempo y limpieza positiva (+).

**Cómo verlo completo:** botón «Casa completa a la derecha».

**Qué decide:** el Pareto de la importancia técnica dentro del resultado del QFD señala los requisitos técnicos que suman 80 % de la importancia. En este caso son **temperatura y tiempo de curado**, que pasan a ser los factores a investigar.

**Por qué el QFD aquí:** traduce lo que pide el cliente (qués) en variables del proceso (cómos) (13_GB DEF-QFD; PL10 QFD). La importancia técnica se calcula como Σ (peso relativo del qué en % × relación). La razón de mejora y el punto de venta vienen de la plantilla de casa de la calidad de uso común y están marcados en el formato como no respaldados por la base.

**Árbol CTQ:** necesidad «panel que no falle en servicio». Dos ramas:
- Resistencia: cortante ≥ 30 MPa.
- Calidad de la unión: porosidad ≤ 1.5 %.

Así la necesidad del cliente queda convertida en métricas medibles con meta (13_GB, árbol CTQ).

### 4.5 Gestión del proyecto (PMBOK)

| Comando | Qué se capturó | Por qué |
|---|---|---|
| `Gestión › Registro de interesados` | Gerente (poder alto, interés alto: de apoyo → líder), supervisor del horno (bajo, alto: neutral → de apoyo), calidad del cliente (alto, bajo: neutral → de apoyo), cada uno con su acción | La brecha entre compromiso actual y deseado define la comunicación (PMBOK 6, 13.2.2.5) |
| `Gestión › Matriz de responsabilidades (RACI)` | Diseño de experimentos, cambio del ciclo y plan de control, con una sola «A» por actividad | Regla de una sola persona que rinde cuentas (PMBOK 6, 9.1.2.2) |
| `Gestión › EDT y diccionario` | En «Cargar plantilla en una EDT vacía» se eligió «Fases DMAIC como segundo nivel» | Desglosa el trabajo por fases con las actividades del curso (13_GB DEF-GANTT-DMAIC) |
| `Gestión › Cronograma y ruta crítica` | Plantilla DMAIC con inicio 03/08/2026; duración optimista = 0.8 × probable y pesimista = 1.5 × probable (supuesto hipotético de incertidumbre) | Fechas, ruta crítica y la entrada para la simulación |
| `Gestión › Monte Carlo del cronograma` | Sin captura: toma el cronograma | Da P50, P80 y P90 y la probabilidad de cumplir la fecha (PMBOK 6, 11.4.2.5) |
| `Gestión › Registro de riesgos` | Amenaza: el lote L3 sigue fuera (probabilidad media, impacto alto, mitigar). Oportunidad: ciclo más corto (explotar). Reserva de contingencia 30 000 | Prioridad por probabilidad × impacto (PMBOK 6, figura 11-5) |
| `Gestión › Justificación de negocio` | Inversión 250 000; tasa 12 %; tres años de beneficio 180 000 y costo 15 000 (hipotéticos) | VPN, TIR, recuperación y ROI (PMBOK 7, 4.4.1) |
| `Gestión › Enfoque de desarrollo` | «Predictivo» | Alcance claro y estable: el método DMAIC encaja con un enfoque predictivo |
| `Gestión › Bitácora: supuestos, incidentes y cambios` | Supuesto (horno ±2 °C, validado), incidente (termopar descalibrado, cerrado), cambio aprobado (ciclo nuevo) | Deja rastro de las decisiones (PMBOK 6, 4.1.3.2, 4.3.3.3 y 4.6.3.3) |

---

## 5. Medir

**Regla de la fase:** antes de calcular capacidad, demuestra que el sistema de medición sirve y revisa si el proceso es estable.

### 5.1 Plan de recolección

**Comando:** `Herramientas de calidad › Hoja de recolección`

Se planeó medir la resistencia en cuatro probetas por día, estratificando por turno y lote de adhesivo, con la máquina universal de pruebas.

**Por qué estratificar:** si no registras el lote y el turno, después no podrás saber si son causa. En este caso el lote resultó ser la causa principal.

### 5.2 Gage R&R del sistema de medición (primero)

**Comando:** `Estadística › Gage R&R de variable…`

| Campo | Valor |
|---|---|
| Pieza o muestra | `parte_rr` |
| Evaluador (operador) | `operador_rr` |
| Medición | `medicion_rr` |
| Tolerancia = LSE − LIE | `12` (hipotético: rango contractual de 30 a 42 MPa) |
| Múltiplo de sigma | 6 (por omisión) |
| Alfa para la interacción | 0.25 (por omisión) |

**Resultado:**
- R&R total = **7.46 % de la tolerancia**: repetibilidad 5.49 % y reproducibilidad 5.05 %.
- Categorías distintas (ndc) = **15**.
- La interacción pieza × evaluador sale en cero.

**Decisión:** el sistema es **aceptable**, así que se puede confiar en las mediciones.
- Criterio: 10 % o menos es aceptable; de 10 % a 30 %, marginal; más de 30 %, inaceptable (14_GB MED-RR-VARIABLE).
- Con ndc de 5 o más, el sistema distingue bien las piezas.

**Por qué va antes que todo:** si la medición tuviera 40 % de R&R, cualquier capacidad o experimento posterior estaría contaminado por el error del instrumento.

### 5.3 Normalidad de la línea base

**Comando:** `Estadística › Distribuciones y normalidad…`

Campos: «Variable» = `resistencia_base`; «Límite inferior de especificación» = `30`.

**Resultado:**
- Media 30.77 MPa, desviación 1.80, mínimo 25.15 y máximo 34.23.
- Anderson-Darling: AD = 0.929, **p = 0.018**.

**Decisión:** se rechaza la normalidad, pero **no se transforma**. La causa probable es física: la mezcla de lotes con medias distintas (L3 es casi 3 MPa menor; ver 6.3) produce una distribución con cola izquierda. El curso pide buscar primero la explicación física antes de transformar (25_BB_DISTRIBUCIONES, DIST-TRANSFORMACION).

### 5.4 Estabilidad: carta X̄-R de la línea base

**Comando:** `Estadística › Cartas de control…`

Campos:
- «Tipo de carta» = «X̄-R (subgrupos de 2 a 10)».
- «Datos» = `resistencia_base`.
- «Tamaño de subgrupo» = `4`: las cuatro probetas de cada día forman un subgrupo racional.
- «Pruebas de causas especiales»: todas marcadas.

**Resultado:** **5 puntos con señal de causa especial**. El proceso no está en control estadístico.

**Decisión:** el proceso es inestable y hay causas especiales que buscar. Esto orienta el análisis hacia lo que cambia de un día a otro: el lote de adhesivo, que rota (19_GB SPC-ELEMENTOS y SPC-PATRONES).

### 5.5 Capacidad inicial (solo como referencia)

**Comando:** `Estadística › Capacidad de proceso…`

Campos: «Datos» = `resistencia_base`; «Tamaño de subgrupo» = `4`; «LIE» = `30`; LSE vacío; «Incluir resumen gráfico» marcado.

**Resultado:** **Cpk = 0.134 y Ppk = 0.142**: incapaz.

**Decisión:** el número se reporta solo como referencia de la situación actual.
- Con el proceso inestable (5.4) y no normal (5.3), el Cpk no predice el desempeño futuro, pero sí cuantifica la brecha: el objetivo es Cpk ≥ 1.33 (16_GB CAP-INTERPRETACION).
- Solo hay LIE porque la resistencia es una característica de «mayor es mejor»; por eso solo se calculan CPL y PPL.

### 5.6 Desempeño en DPMO

**Comando:** `Herramientas de calidad › Desempeño: DPMO y nivel sigma`

Capturado: 400 unidades (hipotético: paneles del periodo), 2 oportunidades por unidad (resistencia y porosidad) y 86 defectos (del archivo 02).

DPMO = 86 / (400 × 2) × 1 000 000 = 107 500. El formato da el nivel sigma correspondiente (16_GB DES-DPMO).

**Por qué:** expresa el problema en una escala comparable entre procesos, útil para el tablero y el reporte a la dirección.

---

## 6. Analizar

**Pregunta de la fase:** ¿qué causa la baja resistencia y cuánto pesa cada causa?

### 6.1 Pareto de defectos

**Comando:** `Gráficas › Diagrama de Pareto…`

Campos: «Categoría» = `tipo_defecto`; frecuencia vacía (cada fila cuenta 1); «Agrupar en Otros» = 95.

**Resultado:**
- Porosidad alta 36.0 %, despegue en borde 25.6 %, adhesivo insuficiente 16.3 % y contaminación 10.5 %.
- Las cuatro primeras acumulan 88 %.

**Decisión:** la porosidad es el modo de falla principal. Por eso, en la fase Mejorar, la porosidad se trata como **segunda respuesta a minimizar**, además de la resistencia.

### 6.2 Ishikawa y 5 Porqués

**Comandos:** `Herramientas de calidad › Diagrama de Ishikawa` y `Herramientas de calidad › 5 Porqués`

Causas por categoría:
- **Material:** lote L3.
- **Método:** ciclo de curado corto.
- **Máquina:** termopar descalibrado.
- **Mano de obra:** limpieza inconsistente.
- **Medición:** alineación de probetas.
- **Medio ambiente:** humedad.

Se marcaron como verificadas las que los datos confirmaron más adelante.

Los 5 Porqués llegaron a esta causa raíz: el ciclo de curado se copió de otro adhesivo y nunca se definió con datos.

**Por qué:** el Ishikawa evita quedarse con la primera causa que se le ocurre al equipo. Cada causa candidata debe probarse con datos; eso hacen 6.3 a 6.5 y el cribado de 7.1.

### 6.3 ANOVA por lote de adhesivo

**Comando:** `Estadística › ANOVA de un factor…`

Campos: «Respuesta» = `resistencia_base`; «Factor» = `lote_adhesivo`; «Alfa» = 0.05.

**Resultado:**
- F = 22.37, mayor que F de tablas (0.05; 3, 96) = 2.70, con p < 0.001.
- Medias: L1 31.42, L2 31.49, **L3 28.78**, L4 31.39 MPa.

**Decisión:** el lote L3 es una causa especial confirmada.
- Explica la falta de normalidad (5.3) y parte de las señales de la carta (5.4).
- **Acción de control:** inspección de recibo por lote del adhesivo, registrada en el registro de riesgos.
- Para mayor rigor, desde el resultado se puede abrir «Comparar con Tukey» (botón de la barra contextual) y confirmar que solo L3 difiere.

### 6.4 Correlación

**Comando:** `Estadística › Correlación…`

Campos: «Variables» = `temp_real`, `tiempo_real`, `resistencia_base` y `porosidad_base`.

**Resultado:**
- Temperatura y resistencia: r = 0.313 (p = 0.002).
- Tiempo y resistencia: r = 0.127 (p = 0.208).
- Resistencia y porosidad: r = −0.726 (p < 0.001).

**Decisión:** la porosidad acompaña fuertemente a la baja resistencia, lo que confirma que conviene atacarlas juntas. La temperatura tiene relación moderada; el tiempo, ninguna detectable **en estos datos**.

### 6.5 Regresión

**Comando:** `Estadística › Regresión…`

Campos: «Respuesta (Y)» = `resistencia_base`; «Predictores (X)» = `temp_real` y `tiempo_real`; «Predecir en X» = `125; 100`.

**Resultado:**
- resistencia = 5.89 + 0.199·temp + 0.019·tiempo.
- La temperatura es significativa (p = 0.003) y el tiempo no (p = 0.549).
- **R² = 10.15 %**.

**Decisión clave:** la regresión **no basta** para optimizar el ciclo. Por qué:
1. Los datos observacionales cubren un rango estrecho: la temperatura varía solo ±3 °C alrededor de 118. No pueden mostrar qué pasaría a 125 o 130 °C.
2. Correlación no es causa: en planta, la temperatura y el tiempo se mueven junto con otras variables.
3. Un R² de 10 % significa que la mayor parte de la variación viene de otras fuentes (lote, ruido).

Por eso se decide **experimentar**: mover temperatura y tiempo a propósito, en un rango amplio y con orden aleatorio (18_GB_MEJORAR; 26_BB y 28_BB).

---

## 7. Mejorar

### 7.1 Cribado: diseño factorial fraccionado 2^(4−1)

**Qué se quiere saber:** de las cuatro variables candidatas del Ishikawa y del QFD (temperatura, tiempo, presión de prensado y nivel de limpieza), ¿cuáles importan?

**Por qué un fraccionado:**
- Un factorial completo de 4 factores son 16 corridas; la mitad (2^(4−1)) son 8.
- Su **resolución IV** estima los efectos principales sin confundirlos con interacciones dobles (26_BB FRAC-RESOLUCION).
- Se agregan **3 puntos centrales** para detectar curvatura y estimar el error puro.

**Comando:** `Estadística › Crear diseño de experimentos…`

| Campo | Valor | Justificación |
|---|---|---|
| Tipo de diseño | Factorial fraccionado 2^(k-p) | Cribado económico |
| Factores | `Temperatura, Tiempo, Presion, Limpieza` | Del Ishikawa y del QFD |
| Nivel bajo | `110, 60, 2, 1` | Hipotéticos: límites seguros del horno, de la prensa y del procedimiento de limpieza |
| Nivel alto | `130, 120, 4, 3` | Hipotéticos: amplios a propósito, para que un efecto real se note |
| Fraccionado: p | 1 (mitad) | 8 corridas |
| Fraccionado: fracción | Principal (generador positivo) | D = ABC |
| Puntos centrales | `3` | Curvatura y error puro |
| Nombre de la respuesta | `Resistencia_cribado` | — |
| Aleatorizar | marcado | Protege contra factores ocultos que cambian en el tiempo |
| Semilla | `7` | **Con semilla 7 obtienes el mismo orden que el caso** |

**Lo que hace D-MIKE:** agrega 9 columnas: orden estándar, orden de corrida, tipo de punto, bloque, los 4 factores y la respuesta vacía. El resumen muestra la relación definidora I = ABCD y la resolución IV.

**Capturar las respuestas:**
1. Abre `datos/04_cribado_fraccionado.csv` en Excel.
2. Copia la columna `Resistencia_MPa`, sin el encabezado.
3. En D-MIKE, haz clic en la primera celda de la columna `Resistencia_cribado` y pega (Ctrl+V).
4. Comprueba que coincidan los valores de los factores fila por fila. Con la semilla 7, el orden es el mismo.
5. Si usaste otra semilla, captura cada respuesta buscando la fila con la misma combinación de factores.

**Análisis.** **Comando:** `Estadística › Analizar diseño factorial…`

Campos:
- «Respuesta» = `Resistencia_cribado`.
- «Factores» = `Temperatura`, `Tiempo`, `Presion` y `Limpieza`.
- «Términos del modelo» = Automático (en un fraccionado, hasta interacciones dobles).
- «Objetivo» = Maximizar; «Alfa» = 0.05.

**Resultado:**

| Término | Efecto | Valor p | Alias | Lectura |
|---|---|---|---|---|
| A Temperatura | 3.12 | 0.001 | — | Significativo |
| B Tiempo | 1.68 | 0.004 | — | Significativo |
| AB | −1.23 | 0.007 | CD | Significativo (ver abajo) |
| C Presión | 0.25 | 0.134 | — | No significativo |
| D Limpieza | 0.17 | 0.246 | — | No significativo |
| Curvatura (centros) | coef. −0.94 | 0.011 | — | **Significativa** |

Modelo: S = 0.146 y R² = 99.86 %.

**Decisiones y por qué:**
1. **Presión y limpieza se fijan** en su nivel estándar más barato: su efecto no es significativo en el rango probado. Esto reduce el problema a dos factores.
2. **AB está confundida con CD** (resolución IV). Se atribuye a temperatura × tiempo porque C y D no tienen efecto principal: es el principio de herencia, criterio general no respaldado por la base. Con dos factores en la siguiente etapa ya no hay confusión.
3. **La curvatura es significativa.** El centro no está sobre el plano que forman las esquinas, así que el óptimo puede estar dentro de la región, no en una esquina. Un modelo lineal ya no basta y hace falta una **superficie de respuesta**, que modela términos cuadráticos (28_BB_SUPERFICIES_RESPUESTA).
4. La «mejor combinación» que sugiere el análisis factorial (130 °C y 120 min, la esquina) **no se adopta**: con curvatura significativa, la esquina no es necesariamente el óptimo.

### 7.2 Diseño central compuesto (DCC)

**Por qué un DCC:**
- Agrega puntos axiales («estrella») y centrales al factorial de 2 factores. Así estima los efectos cuadráticos que la curvatura reveló.
- **Rotable** (α = √2 ≈ 1.414 para 2 factores) significa que la precisión de la predicción solo depende de la distancia al centro. Es lo deseable cuando no se sabe hacia dónde está el óptimo (28_BB).

**Por qué esa región:**
- Se centró en 125 °C y 100 min: hacia la zona alta del cribado (donde la resistencia subió), pero sin pegarse a la esquina, porque la curvatura indicó que el máximo podía estar dentro.
- Los puntos axiales llegan a 110.9 y 139.1 °C. Se supone (hipotético) que la hoja técnica del adhesivo permite hasta 140 °C.

**Comando:** `Estadística › Crear diseño de experimentos…`

| Campo | Valor |
|---|---|
| Tipo de diseño | Central compuesto (DCC) |
| Factores | `Temp_curado, Tiempo_curado` |
| Nivel bajo | `115, 80` |
| Nivel alto | `135, 120` |
| DCC: distancia de los puntos axiales | Rotable |
| DCC: bloques | Sin bloques |
| Puntos centrales | `5` (estiman el error puro y dan predicción estable en el centro) |
| Nombre de la respuesta | `Resistencia` |
| Aleatorizar | marcado |
| Semilla | `11` (mismo orden que el caso) |

**Resultado:** 13 corridas: 4 de cubo, 4 axiales y 5 centrales, con α = 1.4142.

**Capturar las dos respuestas:**
1. Pega la columna `Resistencia_MPa` de `datos/05_diseno_central_compuesto.csv` en `Resistencia`.
2. En la primera columna vacía, haz doble clic en el nombre, escribe `Porosidad` y pega ahí la columna `Porosidad_pct`.
3. Comprueba fila por fila que temperatura y tiempo coincidan con el CSV.

### 7.3 Superficie de respuesta de la resistencia (maximizar)

**Comando:** `Estadística › Analizar superficie de respuesta…`

Campos:
- «Respuesta» = `Resistencia`.
- «Factores» = `Temp_curado` y `Tiempo_curado`.
- «Términos del modelo» = Cuadrático completo.
- «Objetivo del proceso» = **Maximizar**; «Alfa» = 0.05.

**Resultado:**
- Ecuación codificada: Resistencia = 36.09 + 1.096·T + 0.820·S − 1.250·T² − 1.028·S² − 0.323·T·S.
- Todos los términos son significativos salvo la interacción (p = 0.341).
- S = 0.631; **R² = 91.89 %**; R² ajustado 86.10 %; **R² de predicción 55.93 %**.
- **Punto estacionario: máximo** en 128.95 °C y 106.74 min, con resistencia predicha de 36.44 MPa. Los valores propios son negativos (−1.33 y −0.94), lo que confirma un máximo (28_BB RSM-PUNTO-ESTACIONARIO).

**Dónde ver la superficie en 3D:** se despliega en el mismo resultado, junto con la gráfica de contorno. El domo naranja muestra el máximo dentro de la región.

**Lectura crítica:**
- El R² de predicción (56 %) es moderado: el modelo describe bien los datos, pero predice con menos precisión puntos nuevos.
- Opción válida: quitar la interacción no significativa. Con «Modificar…», escribe `Temp_curado*Tiempo_curado` en «Quitar términos» (con los nombres de los factores, tal como aparece en la tabla de coeficientes) y compara los R². Aquí se conservó porque no cambia la conclusión y el modelo completo es jerárquico.
- **Lo indispensable es confirmar con corridas reales** (7.6).

### 7.4 Superficie de respuesta de la porosidad (minimizar)

**Comando:** el mismo, con «Respuesta» = `Porosidad` y «Objetivo del proceso» = **Minimizar**.

**Resultado:**
- Porosidad = 1.792 − 0.332·T − 0.269·S + 0.312·T² + 0.223·S² + 0.008·T·S.
- R² = 97.59 %; R² de predicción 87.69 %.
- **Mínimo** en 130.23 °C y 111.89 min, con porosidad predicha de 1.625 %.

**Por qué analizar la porosidad por separado:** el Pareto (6.1) la señaló como el primer modo de falla, y la correlación (6.4) mostró que acompaña a la baja resistencia. Su óptimo está cerca del de la resistencia, pero no es el mismo: hace falta un compromiso.

### 7.5 Optimizador de respuestas (la decisión de maximizar y minimizar a la vez)

**Comando:** `Estadística › Optimizador de respuestas…`

| Campo | Respuesta 1 | Respuesta 2 | Justificación |
|---|---|---|---|
| Modelo analizado | Superficie de respuesta de Resistencia | Superficie de respuesta de Porosidad | Las dos superficies de 7.3 y 7.4 |
| Meta | Maximizar | Minimizar | La decisión del proyecto |
| Inferior | `34` | — | Debajo de 34 MPa la deseabilidad es 0: es el mínimo para tener Cpk ≥ 1.33 con σ ≈ 1.1 (ver 4.2) |
| Objetivo | `37` | `1.4` | 37: un poco arriba del máximo esperado (36.4), para que el optimizador siga empujando. 1.4 %: meta hipotética del cliente |
| Superior | — | `2.2` | Arriba de 2.2 % de porosidad la deseabilidad es 0 (hipotético: límite de aceptación por ultrasonido) |
| Importancia | `3` | `2` | La resistencia es el requisito contractual; la porosidad, el medio para lograrla |

**Resultado:**
- **Temperatura 129.42 °C y tiempo 108.63 min.**
- Resistencia predicha 36.43 MPa (deseabilidad 0.81) y porosidad predicha 1.633 % (deseabilidad 0.71).
- **Deseabilidad compuesta D = 0.768**.

La función de deseabilidad (Derringer y Suich) es el método del optimizador de respuesta de Minitab. El programa la marca como no respaldada por la base.

**Decisión final del ciclo:** **129 °C durante 109 min**.
- Se redondea a valores que el horno puede programar.
- El cambio en la predicción es despreciable: el punto queda en la meseta de las dos superficies.
- La tolerancia de operación de ±2 °C se toma del supuesto validado en la bitácora.

### 7.6 Confirmación y acciones de mejora

1. **Corridas de confirmación** (recomendado en un caso real): corre de 3 a 5 paneles en 129 °C y 109 min. Si la media cae dentro del intervalo de predicción, el modelo se confirma. En el caso, la confirmación son los datos «después» (8.1).
2. **AMEF** (`Herramientas de calidad › AMEF`): se capturaron dos modos de falla.

   | Modo de falla | Severidad | Ocurrencia | Detección | Acciones | Ocurrencia y detección después |
   |---|---|---|---|---|---|
   | Curado incompleto | 8 | 6 | 5 | Ciclo nuevo y verificación diaria del termopar | 2 y 3 |
   | Superficie contaminada | 8 | 4 | 6 | Paños de un solo uso y prueba de gota | 2 y 3 |

   El formato calcula el NPR antes y después.
3. **Poka Yoke** (`Lean › Poka Yoke`): receta del horno bloqueada por número de parte, para que nadie arranque con el ciclo anterior.
4. **Bitácora:** el cambio «ciclo 125 °C y 100 min» quedó aprobado por el gerente. En tu proyecto anota el ciclo final (129 °C y 109 min).

---

## 8. Controlar

### 8.1 Estabilidad con el proceso nuevo

**Comando:** `Estadística › Cartas de control…`, tipo X̄-R, «Datos» = `resistencia_despues`, «Tamaño de subgrupo» = `5` (cinco probetas por día).

**Resultado:** ningún punto activa las pruebas. El proceso se comporta como estable, con solo causas comunes (19_GB SPC-ELEMENTOS).

### 8.2 Capacidad final

**Comando:** `Estadística › Capacidad de proceso…`, «Datos» = `resistencia_despues`, subgrupo `5`, LIE `30`.

**Resultado:**
- **Cpk = 1.754 y Ppk = 1.766**: capaz.
- Nivel sigma de corto plazo de 5.26.

Ahora sí el Cpk es válido como predicción, porque el proceso es estable (8.1).

### 8.3 Prueba de que la mejora es real

**Comando:** `Estadística › Pruebas de hipótesis…`

Campos:
- «Prueba» = t de 2 muestras (medias).
- «Datos (muestra 1)» = `resistencia_base`; «Muestra 2» = `resistencia_despues`.
- «Valor de H0» = `0`; «Hipótesis alterna» = **Menor que**.

**Resultado:**
- Medias 30.77 contra 35.84 MPa; diferencia −5.07; t = −22.07 con 157 gl; p < 0.001.
- El límite superior del IC 95 % de la diferencia es −4.69.

**Por qué una cola:** la pregunta del proyecto es si **subió** la resistencia, no solo si cambió. El IC dice que la mejora es de al menos 4.7 MPa con 95 % de confianza. Eso responde si el efecto importa en la práctica, no solo si es significativo.

### 8.4 Plan de control y tablero

**Plan de control** (`Herramientas de calidad › Plan de control`):

| Paso | Qué se controla | Límite | Método | Frecuencia | Responsable |
|---|---|---|---|---|---|
| Curado | Temperatura de meseta | 127 a 131 °C (ciclo 129 °C ± 2) | Registro del horno | Cada ciclo | Operador |
| Prueba | Resistencia | ≥ 30 MPa | Carta X̄-R (n = 5) | Diaria | Técnico |

En el proyecto entregado dice 123 a 127 °C, porque se capturó con el ciclo de 125 °C: en tu proyecto usa el ciclo final.

**Tablero** (`Herramientas de calidad › Tablero semanal`, luego `Proyecto › Tablero de indicadores`):
- Indicadores: nivel sigma (meta 4) y OEE (meta 85 %), con valores semanales hipotéticos.
- Ambos marcados como «Atrasado»: miden resultados ya ocurridos (PMBOK 7, 2.7.1.1).
- En un caso real conviene sumar un indicador adelantado, como el porcentaje de ciclos con la temperatura en rango.

### 8.5 Cierre

| Comando | Qué se capturó | Por qué |
|---|---|---|
| `Gestión › Seguimiento por valor ganado` | Cuatro cortes de PV, EV y AC (hipotéticos) con presupuesto de 250 000 | SPI y CPI para cerrar dentro de tiempo y costo |
| `Gestión › Costo de calidad` | Prevención 20 000 → 60 000; evaluación 90 000 → 70 000; falla interna 520 000 → 110 000; falla externa 80 000 → 10 000 (hipotéticos) | Muestra que invertir en prevención bajó el costo total (PMBOK 7, 2.6.3.1) |
| `Herramientas de calidad › Checklist de revisión de fase` | Todos los puntos en «Sí»; decisión «Continuar» firmada por el gerente | Revisión de compuerta (PMBOK 6, 1.2.4.3) |
| `Herramientas de calidad › Informe A3` | Resumen del proyecto en siete secciones | Comunicación en una hoja |
| `Gestión › Cierre y lecciones aprendidas` | Objetivo de resistencia media: meta 35 y real 35.8 (cumple); costo: meta 250 000 y real 247 000 (cumple). Lección: «Cribar antes de la superficie de respuesta» | Informe final y transición al dueño del proceso (PMBOK 6, 4.7.3.3) |

Marca el avance de cada módulo con «⋯» en el riel o con clic derecho, eligiendo «Marcar como hecho».

---

## 9. Resumen de decisiones y resultados

| Paso | Resultado | Decisión |
|---|---|---|
| Gage R&R | 7.46 % de la tolerancia; ndc 15 | Medición aceptable: seguir |
| Normalidad | p = 0.018 | No transformar: buscar la causa física (lotes) |
| Carta X̄-R antes | 5 señales | Proceso inestable: buscar causas especiales |
| Capacidad antes | Cpk 0.134 | Brecha cuantificada (referencia) |
| Pareto | Porosidad 36 % | Porosidad como segunda respuesta |
| ANOVA por lote | L3 = 28.78 contra unos 31.4; p < 0.001 | Inspección de recibo del adhesivo |
| Regresión | R² 10 % | No alcanza: experimentar |
| Cribado 2^(4−1) | A, B y AB significativos; curvatura p = 0.011 | Fijar presión y limpieza; pasar a superficie de respuesta |
| Superficie de resistencia | Máximo 36.44 en 128.95 °C y 106.7 min | Maximizar |
| Superficie de porosidad | Mínimo 1.625 en 130.2 °C y 111.9 min | Minimizar |
| Optimizador | 129.42 °C, 108.63 min; D = 0.768 | Ciclo 129 °C y 109 min |
| Carta X̄-R después | Sin señales | Proceso estable |
| Capacidad después | Cpk 1.754 | Meta cumplida (≥ 1.33) |
| Prueba t | +5.07 MPa; p < 0.001 | Mejora real de al menos 4.7 MPa |

---

## 10. Cómo armar tu propio proyecto con este método

**Secuencia mínima que no debes saltarte:**
1. **Definir:** problema con magnitud medida, acta con criterio de éxito y CTQ medibles.
2. **Medir:** primero el Gage R&R, luego la estabilidad (carta) y después la capacidad. Estratifica desde la recolección: turno, lote, máquina y operador.
3. **Analizar:** Pareto para elegir qué atacar. Ishikawa para listar causas. Pruebas (ANOVA, correlación, regresión) para confirmarlas con datos.
4. **Mejorar:** si las causas son variables de proceso ajustables, experimenta.
   - Con 4 o más candidatas, cribado fraccionado con puntos centrales.
   - Con 2 o 3 factores importantes y curvatura, superficie de respuesta.
   - Con varias respuestas, optimizador.
5. **Controlar:** carta del proceso nuevo, capacidad final, prueba antes contra después, plan de control y entrega al dueño del proceso.

**Reglas de decisión que usó el caso (puedes copiarlas):**

| Si… | Entonces… | Fuente |
|---|---|---|
| R&R > 30 % de la tolerancia | Arregla la medición antes de seguir | 14_GB MED-RR-VARIABLE |
| La carta muestra señales | Busca la causa especial; el Cpk es solo referencia | 19_GB SPC-ELEMENTOS |
| La normalidad falla | Busca una causa física (mezcla de poblaciones) antes de transformar | 25_BB DIST-TRANSFORMACION |
| El ANOVA es significativo | Usa Tukey para saber qué nivel difiere | 17_GB_ANALIZAR |
| Los datos observacionales dan R² bajo | Experimenta en lugar de inferir | 18_GB_MEJORAR |
| Hay 4 o más factores candidatos | Fraccionado de resolución IV o mayor | 26_BB FRAC-RESOLUCION |
| La curvatura es significativa en un factorial | Superficie de respuesta | 28_BB_SUPERFICIES_RESPUESTA |
| Hay dos respuestas con óptimos distintos | Optimizador con importancias | Práctica general (Minitab) |

**Cómo practicar con tus propios datos hipotéticos:**
1. Copia `herramientas/generar_caso_integral.py`.
2. Cambia los coeficientes de los modelos de la sección 2.2 y la semilla. Por ejemplo, haz que el tiempo no importe o que el óptimo esté fuera de la región.
3. Corre el caso de nuevo: comprobarás si los análisis encuentran lo que pusiste.

Si prefieres no usar código, captura tú mismo los valores en la hoja inventando un modelo sencillo. Anota siempre de dónde sale cada número.

---

## 11. Notas de rigor: lo que debes corregir en un caso real

1. **Magnitud del problema.** El proyecto entregado dice «18 %» en la definición y en el acta, un valor inicial hipotético. La medición dio **26 %** bajo 30 MPa y una media de 30.77, no de 31.3. En tu proyecto actualiza ambos con los datos medidos.
2. **Ciclo en la bitácora y el plan de control.** Se capturaron con 125 °C y 100 min, el centro del DCC. El ciclo final que recomienda el optimizador es **129 °C y 109 min**: corrígelos.
3. **Capacidad antes con proceso inestable.** Se calculó solo para cuantificar la brecha. Un Cpk de un proceso fuera de control no predice el desempeño (19_GB).
4. **Corridas de confirmación.** El caso usa los datos «después» como confirmación. En un caso real corre primero de 3 a 5 piezas en el óptimo y compáralas con el intervalo de predicción, antes de cambiar el estándar.
5. **R² de predicción de la resistencia (56 %).** Es aceptable para decidir la región, no para prometer un valor exacto. Por eso el objetivo se fijó en 36 MPa y no en 36.4.
6. **Datos hipotéticos.** Ningún número de este caso debe usarse como referencia técnica del adhesivo, del horno ni de un cliente. Sirven solo para aprender el método y el programa.
