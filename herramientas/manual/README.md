# Generador del manual de D-MIKE

Genera el Manual de uso en PDF a partir de `gen.py` (fichas de los módulos tomadas del código), `textos.json` (secciones 1 a 5) y tres archivos de entrada que viven fuera del código.

## Comando

Desde la raíz del repositorio (también funciona desde cualquier otra carpeta):

    python herramientas/manual/gen.py

El PDF queda en `herramientas/manual/salida/D-MIKE_Manual_de_uso_v<versión>.pdf` (por ejemplo `..._v026.pdf`). Junto a él queda `manual.html`, que sirve para depurar. La carpeta `salida/` se crea sola y no se versiona.

Opciones: `--estricto` (falla si un ejemplo de una ficha no coincide con lo que ejecuta el programa), `--capturas CARPETA` (capturas ya generadas; por omisión `<salida>/capturas`, que se genera sola si falta), `--salida CARPETA` (otra carpeta de salida), `--entradas CARPETA` (otra carpeta de entradas), `--permitir-faltantes` (ver abajo). También se leen las variables de entorno `DMIKE_MANUAL_SALIDA` y `DMIKE_MANUAL_ENTRADAS`.

## Entradas

Van en `herramientas/manual/entradas/` (o en la carpeta de `--entradas`):

| Archivo | Para qué | Cómo se obtiene |
|---|---|---|
| `D-MIKE_caso_integral_paso_a_paso.md` | Sección 6, caso maestro | Texto escrito a mano; está versionado en `entradas/` |
| `svgs.json` | Figuras del caso (formato `{MÓDULO: [{"svg": [...], "huella": "..."}]}`) | Se genera solo si falta, con `python herramientas/manual/generar_svgs.py` (corre la receta sintética del caso; no se versiona) |
| `08_GLOSARIO.md` | Apéndice B, glosario de la base del curso | Si no está en `entradas/`, se usa el de la raíz del repositorio |

Si falta alguno, el generador se detiene y lo dice. Con `--permitir-faltantes` genera un PDF **parcial**: las secciones afectadas salen marcadas «Sección no generada» y el generador lista lo que faltó. Un PDF parcial no es el manual completo.

## Dependencias

- Python: `markdown` y `playwright` (ambos en `requirements-dev.txt`), más las de `requirements.txt`. Chromium de Playwright: `python -m playwright install chromium`.
- Sistema: `pdfinfo` y `pdftotext` (paquete poppler-utils). Sirven para numerar el índice en una segunda pasada.
- Archivos del repositorio que usa: `app/datos/comandos.json`, `app/ui/logo10_oscuro.svg`, `app/ui/fuentes/Montserrat.woff2`.

## Fichas de 15 puntos, ejemplos y capturas

- `entradas/tipos_ficha.json`: tipo de ficha (`interfaz`, `analisis`, `formato`, `gestion`) de cada módulo del catálogo.
- `entradas/fichas/<ID>.md`: ficha escrita. Encabezado con `id` y `tipo`; puntos `## 1.` a `## 15.`; los bloques ```` ```ejemplo ```` (JSON) se ejecutan con el programa al generar el manual y se comparan con `esperado`. Formas de ejemplo: `{"modulo", "datos", "parametros", "esperado": {"tabla", "fila"}}` (análisis), `{"datos", "pasos": [...], "esperado_hoja"}` (operación de la hoja) y `{"modulo", "tipo": "formato", "cabecera", "tablas", "esperado_avisos", "esperado_texto"}` (formato). Un módulo sin ficha escrita usa la ficha automática con su leyenda. La carpeta `fichas/` se toma de `--entradas` si existe; si no, de la del repositorio. Los puntos pedagógicos pendientes se marcan `[PENDIENTE DE REDACCIÓN]`.
- `entradas/indice_preguntas.json`: índice por pregunta (campos `pregunta`, `ruta` de 2 a 4 IDs de módulo, `fase`, `tipo_dato`, `resultado_esperado`, `nivel`, `fuente_base`). Cada ID debe existir en el catálogo.
- `capturas.py`: `python herramientas/manual/capturas.py [--salida CARPETA] [--solo ID]` toma las capturas de la interfaz web con datos sintéticos y escribe `capturas.json`. Necesita Playwright y su Chromium. Los diálogos nativos de Windows no se capturan. `gen.py` la corre solo si falta `capturas.json`.
- `salida/fichas_reporte.json`: ejemplos que coinciden, puntos pendientes y avisos de las fichas.
