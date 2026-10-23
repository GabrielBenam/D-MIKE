---
id: REEMPLAZAR
tipo: interfaz
titulo: Buscar y reemplazar
---

## 1. Propósito
Corrige o borra texto en las celdas de la hoja (por ejemplo coma decimal por punto, o unificar «Op1» y «op1»).

## 2. Cuándo usarla y cuándo no
Limpieza de datos importados. No usarla con «En la columna» vacío si buscas números cortos: recorre todas las columnas, también las numéricas.

## 3. Fase DMAIC y relaciones
No aplica; es una operación de la hoja.

## 4. Ubicación en D-MIKE
Editar › Selección y búsqueda › Buscar y reemplazar…; atajo Ctrl+H (catálogo de comandos). El código de la hoja también abre el diálogo con Ctrl+F (pendiente de validación en pantalla).

## 5. Entradas y estado previo
Datos en la hoja. Campos: «Buscar», «Reemplazar por (vacío = borrar)», «En la columna (vacío = todas)», «Solo celdas completas iguales al texto buscado», «Distinguir mayúsculas y minúsculas».

## 6. Preparación y riesgos
El cambio se aplica directo, sin vista previa ni confirmación. No cambia resultados ya guardados (se deduce del código, que solo toca la hoja).

## 7. Lógica
Sin «celdas completas»: sustituye cada coincidencia dentro de la celda. Con «celdas completas»: compara el contenido sin espacios en los extremos y reemplaza toda la celda. Si el resultado queda vacío, la celda queda sin dato, no en cero.

## 8. Procedimiento en la interfaz
1) Selecciona la columna o déjala vacía. 2) Abre la ruta del punto 4. 3) Escribe lo buscado y su reemplazo. 4) Marca las opciones. 5) Acepta.

## 9. Outputs reales esperados
No genera resultado; cambia la hoja y deja un mensaje en la sesión: «Reemplazos hechos: N.» o «No se encontró el texto.».

## 10. Cómo interpretar
N cuenta celdas cambiadas, no ocurrencias: una celda con el texto dos veces cuenta 1. «No se encontró el texto» no indica error.

## 11. Ejemplo reproducible
Hoja sintética con operador = Op1, op1, Op2, «Op1 » y tiempo = 12,5; 14,0; 13,1; vacío. Reemplazar «,» por «.» en tiempo: «Reemplazos hechos: 3.». Reemplazar «Op1» por «Operador 1» en operador (sin distinguir mayúsculas): «Reemplazos hechos: 3.»; queda Operador 1, Operador 1, Op2, «Operador 1 » (el espacio final se conserva).

```ejemplo
{"datos": "operador\ttiempo\nOp1\t12,5\nop1\t14,0\nOp2\t13,1\nOp1 \t\n",
 "pasos": [
   {"modulo": "REEMPLAZAR", "parametros": {"buscar": ",", "nuevo": ".", "col": 1}, "esperado_mensaje": "Reemplazos hechos: 3."},
   {"modulo": "REEMPLAZAR", "parametros": {"buscar": "Op1", "nuevo": "Operador 1", "col": 0}, "esperado_mensaje": "Reemplazos hechos: 3."}],
 "esperado_hoja": {"0": ["Operador 1", "Operador 1", "Op2", "Operador 1 "], "1": ["12.5", "14.0", "13.1", null]}}
```

```ejemplo
{"datos": "operador\tt\nOp1\t1\nOp2\t2\n",
 "pasos": [
   {"modulo": "REEMPLAZAR", "parametros": {"buscar": "Op", "nuevo": "X"}, "esperado_mensaje": "Reemplazos hechos: 2."},
   {"accion": "deshacer"}],
 "esperado_hoja": {"0": ["Op1", "Op2"]}}
```

## 12. Decisiones posteriores
Si cambiaste mal: deshacer. Si quedó correcto: continuar con el análisis.

## 13. Errores y resolución
Sin texto a buscar: «Escribe el texto a buscar.». Deshacer: Editar › Historial › Deshacer (Ctrl+Z, hasta 50 pasos); verificado que restaura la hoja. Si cambias una columna numérica con texto, el efecto sobre su tipo está pendiente de validación en pantalla.

## 14. Exportación y trazabilidad
Sin registro del reemplazo más allá del mensaje de la sesión. No genera archivo.

## 15. Fuentes y versión
Operación de interfaz, sin fuente de curso. D-MIKE 0.29.0.
