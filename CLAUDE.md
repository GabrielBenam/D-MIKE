# CLAUDE.md — reglas para trabajar en el repositorio D-MIKE

## Qué es
D-MIKE: suite de calidad Lean Six Sigma para Windows (Python + pywebview, interfaz HTML/JS en `app/ui`). Modo proyecto DMAIC, análisis estadísticos estilo Minitab, formatos de calidad, Lean y gestión, recetas del Diagnóstico en línea. Versión vigente: ver `VERSION` en `app/api.py`.

## Usuario
Ingeniero Aeronáutico en Manufactura y Black Belt LSS, nivel informático básico. Responde en español, sin preámbulos ni emojis, breve. Cuando le pidas algo fuera del código (probar en Windows, descargar el instalador), da pasos numerados con la ruta exacta de cada clic.

## Fuentes y rigor
- `proyecto/ESTADO_D-MIKE.md`: fuente de verdad de lo decidido y lo pendiente. Actualízalo en cada entrega.
- `proyecto/especificaciones/`: requisitos vigentes (`ESPEC_flujo_real_dmaic.md`, `ESPEC_manual_v026.md`).
- Fórmulas y umbrales: solo de la base del curso (citas tipo `16_GB_... CAP-...`, `PL03`). Si no hay fuente, marca «no respaldado» en el código o el resultado; no inventes criterios.
- Solo datos sintéticos marcados como tales. Nunca datos de clientes.
- Formatos Lean (TAKT, TIEMPOS, BALANCE, MUDAS, TRABAJO-EST, VSM): no cambiar cálculos hasta verificarlos contra PL03 con los Excel 3_6_a/3_6_b. MTM, solver de balanceo, simulación y layout: fuera de alcance.

## Cómo trabajar
1. Antes de cambiar código, corre las pruebas: `python -m pytest pruebas -q` (las de interfaz usan Playwright: `python -m playwright install chromium`).
2. Incrementos pequeños; cada cambio con su prueba. No borres pruebas para que pasen: corrige el código o explica por qué la prueba era incorrecta.
3. Vacío no es cero; porcentajes con su base; redondeo solo al mostrar; resultados reproducibles (copia congelada y huella SHA-256). No rompas estas reglas.
4. Compatibilidad: los `.dmike` y recetas de versiones anteriores deben seguir abriendo (agrega pruebas de migración cuando cambies el formato).
5. Al terminar una entrega: sube `VERSION`, regenera `MANIFIESTO.txt` (`python herramientas/generar_manifiesto.py`), regenera el catálogo (`python herramientas/exportar_catalogo.py` crea `proyecto/catalogo/catalogo_dmike_<versión>.json`; borra el de la versión anterior), actualiza `proyecto/ESTADO_D-MIKE.md`, corre la suite completa y reporta: qué cambió, qué probaste, qué no y riesgos.
6. Compilación: GitHub Actions (`.github/workflows/`) arma el instalador en cada push a `main`. Trabaja en ramas y abre PR; el usuario aprueba el merge.

## Formato de reporte por cambio
ID de requisito · comportamiento anterior · comportamiento nuevo · archivos · migración · prueba · resultado · sección del manual · riesgos.
