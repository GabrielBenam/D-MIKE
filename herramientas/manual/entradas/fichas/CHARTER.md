---
id: CHARTER
tipo: formato
titulo: Acta del proyecto (Project Charter)
---

## 1. Propósito
Documentar en un solo formato la definición del proyecto de mejora (13_GB_DEFINIR, DEF-CHARTER).

## 2. Cuándo usarla y cuándo no
Al arrancar el proyecto, antes de medir. Se revisa y actualiza durante el proyecto.

## 3. Fase DMAIC y relaciones
Definir (D). Se alimenta de Enfoque de desarrollo y del registro de Interesados (los dos campos calculados); después sigue la Lista de verificación de fase (DEF-CHECKLIST).

## 4. Ubicación en D-MIKE
Herramientas de calidad › Definir el problema › Acta del proyecto (Charter). Sin atajo.

## 5. Campos
Cabecera: proyecto, cliente o área y «Preparado por» se llenan desde los datos fijos; número de proyecto, iniciador, fechas, documento núm. Secciones: 1 caso de negocio, 2 propósito (CTQ, línea base, objetivo), 3 objetivos (con ahorro), 4 alcance, 5 roles (Champion, Sponsor, Líder, Miembro con nombre, correo y teléfono), 6 recursos, 7 métricas. Además, del PMBOK 6 (4.1.3.1): requisitos de alto nivel, riesgo general, hitos, presupuesto preaprobado, interesados clave, requisitos de aprobación, criterios de salida, autoridad del líder y del patrocinador.

## 6. Preparación y validación
Nada bloquea guardar; solo hay avisos. Fechas de hitos en DD/MM/AAAA. «Ahorro» es numérico y no lleva moneda: indícala en el texto.

## 7. Fundamento
Plantilla del caso de negocio: «Como compañía, el desempeño de nuestro ___ en el área de ___ no está cumpliendo ___» (13_GB_DEFINIR, DEF-CHARTER). El Champion cumple el papel de patrocinador (01_MARCO_Y_ROLES). Ahorro total = suma de los ahorros capturados.

## 8. Procedimiento en la interfaz
Abrir el formato, llenar por sección, guardar; el avance del módulo pasa de pendiente a en curso.

## 9. Outputs reales esperados
Avisos de completitud (siete reglas, ver punto 10), un texto «Ahorro total esperado: …» y la exportación a .xlsx.

## 10. Cómo interpretar
Los siete avisos son: falta caso de negocio o alcance; falta al menos un objetivo con CTQ; falta un líder y un champion o sponsor; falta el patrocinador; faltan requisitos de aprobación; faltan criterios de salida; falta el cronograma de hitos. Que desaparezcan no equivale a «acta completa»: el programa no verifica requisitos de alto nivel, riesgo, métricas, recursos ni firmas.

## 11. Ejemplo diligenciado (sintético)
Acta vacía: los siete avisos. Con caso de negocio y alcance, dos objetivos (uno con ahorro 120000) y un Líder, quedan cinco avisos más dos sobre el ahorro y el texto «Ahorro total esperado: 120,000 (base: 1 de 2 objetivos con ahorro capturado; los demás quedan sin dato, no cuentan como cero)».

```ejemplo
{"modulo": "CHARTER", "tipo": "formato",
 "vacio_esperado_avisos": ["Falta: caso de negocio, alcance.", "Falta al menos un objetivo con su CTQ.", "Define al menos un líder y un champion o sponsor.", "Falta el patrocinador que autoriza el proyecto (PMBOK 6, 4.1.3.1): sin él el acta no autoriza formalmente.", "Falta definir qué es éxito, quién lo decide y quién firma (requisitos de aprobación).", "Faltan los criterios de salida: condiciones para cerrar o cancelar.", "Falta el cronograma resumido de hitos."],
 "cabecera": {"caso_negocio": "Como compañía, el desempeño de la unión adhesiva en el área de ensamble no cumple 30 MPa. (SINTÉTICO)", "alcance": "Proceso de curado de paneles (SINTÉTICO)"},
 "tablas": {"objetivos": [{"ctq": "Resistencia de unión", "base": "30.8 MPa", "objetivo": "35 MPa", "ahorro": "120000"}, {"ctq": "Porosidad", "base": "2.2 %", "objetivo": "1.5 %"}],
            "equipo": [{"rol": "Líder", "nombre": "Persona A (sintética)"}]},
 "esperado_avisos": ["Define al menos un líder y un champion o sponsor.", "Falta el patrocinador que autoriza el proyecto (PMBOK 6, 4.1.3.1): sin él el acta no autoriza formalmente.", "Falta definir qué es éxito, quién lo decide y quién firma (requisitos de aprobación).", "Faltan los criterios de salida: condiciones para cerrar o cancelar.", "Falta el cronograma resumido de hitos.", "1 objetivos sin ahorro capturado: el total solo suma los que lo tienen.", "3. Objetivos del proyecto: 1 campos numéricos vacíos quedan como «pendiente»; no se cuentan como cero."],
 "esperado_texto": "Ahorro total esperado: 120,000 (base: 1 de 2 objetivos con ahorro capturado; los demás quedan sin dato, no cuentan como cero)"}
```

## 12. Decisiones posteriores
Con los avisos resueltos, firmar y pasar a la lista de verificación de Definir (DEF-CHECKLIST, 13_GB_DEFINIR).

## 13. Errores y resolución
Un ahorro vacío en una fila con datos queda «pendiente» y no se cuenta como cero.

## 14. Exportación y trazabilidad
.xlsx con plantilla propia; se guarda en el proyecto (.dmike).

## 15. Fuentes y versión
13_GB_DEFINIR (DEF-CHARTER, DEF-CHARTER-EJEMPLO), PL14, 01_MARCO_Y_ROLES, PMBOK 6 4.1.3.1 (citado por el código; no revisado en el PDF). D-MIKE 0.29.0.
