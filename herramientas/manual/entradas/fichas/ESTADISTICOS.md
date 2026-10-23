---
id: ESTADISTICOS
tipo: analisis
titulo: Estadísticos de columna
---

## 1. Propósito
Resume una columna numérica: dónde se centra y cuánto varía. Responde «¿cómo se distribuyen mis datos?».

## 2. Cuándo usarla y cuándo no
Primer vistazo a una variable antes de graficar o comparar. No sirve para concluir estabilidad ni capacidad: con pocos datos no hay base para eso.

## 3. Fase DMAIC y relaciones
Medir (M). Después suelen ir Gráfica de corrida, Diagrama de caja y Distribuciones y normalidad.

## 4. Ubicación en D-MIKE
Calc › Probabilidad y resumen › Estadísticos de columna. Atajo: no declarado (pendiente de validación).

## 5. Entradas
«Variable» (columna numérica, obligatoria) y «Por grupo (opcional)» (columna de texto).

## 6. Preparación y validación
Las celdas vacías o no numéricas quedan fuera y no se cuentan como cero. Con grupo, también se excluye la fila sin grupo. El programa no detecta atípicos aquí; para eso está el Diagrama de caja (bigotes a 1.5 × RIC, 17_GB_ANALIZAR, BOX-PROCEDIMIENTO).

## 7. Fundamento
Media x̄ = Σxᵢ/n; mediana: valor central de los datos ordenados; moda: el valor más frecuente; rango = máximo − mínimo; s = √[Σ(xᵢ−x̄)²/(n−1)]; varianza = s² (15_GB_ESTADISTICA_Y_MUESTREO, EST-CENTRAL y EST-VARIABILIDAD). No respaldados por la base: cuartiles (método de Minitab, posición p(n+1) con interpolación), RIC = Q3 − Q1, error estándar = s/√n, CV = 100·s/x̄, suma, asimetría y curtosis corregidas por sesgo (curtosis como exceso: 0 en una normal).

## 8. Procedimiento en la interfaz
1) Pega o importa los datos en la hoja. 2) Abre la ruta del punto 4. 3) Elige la variable y, si quieres, el grupo. 4) Acepta; el resultado abre en una pestaña.

## 9. Outputs reales esperados
Una tabla «Estadísticos descriptivos», una fila por grupo (o «Todos»), con 19 columnas en este orden: Grupo, N, N faltante, Media, EE de la media, Desv. est., Varianza, CV (%), Suma, Mínimo, Q1, Mediana, Q3, Máximo, Rango, RIC, Asimetría, Curtosis, Moda. Más un texto de fuentes y avisos de exclusión. No genera gráfica (verificado).

## 10. Cómo interpretar cada output
«Moda» muestra hasta 3 valores y «sin moda» si ningún valor se repite. Con n = 1 la desviación, varianza, CV, asimetría y curtosis salen «—»; asimetría exige n ≥ 3 y curtosis n ≥ 4. Una media y una mediana muy distintas sugieren asimetría, no prueban nada por sí solas. El CV no tiene sentido si la media es cercana a 0.

## 11. Ejemplo reproducible
Datos sintéticos 8, 10, 10, 12, 15. D-MIKE entrega: N 5, media 11, EE 1.1832, s 2.6458, varianza 7, CV 24.0523 %, suma 55, mínimo 8, Q1 9, mediana 10, Q3 13.5, máximo 15, rango 7, RIC 4.5, asimetría 0.8099, curtosis 0.6735, moda 10. Sustitución: Σ(xᵢ−11)² = 9+1+1+1+16 = 28; 28/4 = 7; √7 = 2.6458. Contraste con el curso (11 calificaciones, 15_GB EST-CENTRAL y EST-VARIABILIDAD): D-MIKE da media 75.4545, mediana 76, moda 68, rango 26, s 8.9483, varianza 80.0727; el curso reporta 75.5, 76, 68, 26, 8.94 y 80.07. Coinciden salvo el redondeo del curso (8.9483 redondea a 8.95, no a 8.94).

```ejemplo
{"modulo": "ESTADISTICOS", "datos": "tiempo\n8\n10\n10\n12\n15", "parametros": {"y": 0},
 "esperado": {"tabla": "Estadísticos descriptivos", "fila": ["Todos","5","0","11","1.1832","2.6458","7","24.0523","55","8","9","10","13.5","15","7","4.5","0.8099","0.6735","10"]}}
```

```ejemplo
{"modulo": "ESTADISTICOS", "datos": "calif\n64\n88\n66\n82\n68\n68\n70\n78\n76\n80\n90", "parametros": {"y": 0},
 "esperado": {"tabla": "Estadísticos descriptivos", "fila": ["Todos","11","0","75.4545","2.698","8.9483","80.0727","11.8592","830","64","68","76","82","90","26","14","0.3589","-1.1899","68"]}}
```

## 12. Decisiones posteriores
Datos en orden cronológico: Gráfica de corrida (Gráficas › Tiempo y dispersión). Posibles atípicos: Diagrama de caja. Antes de usar pruebas que suponen normalidad: Distribuciones y normalidad (Estadística › Distribución).

## 13. Errores y resolución
Sin datos numéricos válidos: «[columna] no tiene datos numéricos válidos». Celdas excluidas: «N filas con valores faltantes o que no corresponden a su tipo quedaron fuera del cálculo» y «Sin datos: [columna] tiene N celda sin dato (filas …)». Un grupo con un solo dato sale con «—».

## 14. Exportación y trazabilidad
El resultado se guarda en el proyecto (Proyecto › Resultados del proyecto). Según ESTADO se exporta a .xlsx (con hoja de datos plana para Minitab) o .png; pendiente de validación en 0.29.0.

## 15. Fuentes y versión
15_GB_ESTADISTICA_Y_MUESTREO (EST-CENTRAL, EST-VARIABILIDAD); resto marcado «no respaldado». D-MIKE 0.29.0.
