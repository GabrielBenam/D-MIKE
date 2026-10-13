# Generador del manual de D-MIKE

Genera el Manual de uso en PDF a partir de `gen.py` (fichas de los módulos tomadas del código), `textos.json` (secciones 1 a 5) y tres archivos de entrada que viven fuera del código.

## Comando

Desde la raíz del repositorio (también funciona desde cualquier otra carpeta):

    python herramientas/manual/gen.py

El PDF queda en `herramientas/manual/salida/D-MIKE_Manual_de_uso_v<versión>.pdf` (por ejemplo `..._v026.pdf`). Junto a él queda `manual.html`, que sirve para depurar. La carpeta `salida/` se crea sola y no se versiona.

Opciones: `--salida CARPETA` (otra carpeta de salida), `--entradas CARPETA` (otra carpeta de entradas), `--permitir-faltantes` (ver abajo). También se leen las variables de entorno `DMIKE_MANUAL_SALIDA` y `DMIKE_MANUAL_ENTRADAS`.

## Entradas que NO están en el repositorio

Van en `herramientas/manual/entradas/` (o en la carpeta de `--entradas`):

| Archivo | Para qué | Sin él |
|---|---|---|
| `D-MIKE_caso_integral_paso_a_paso.md` | Sección 6, caso maestro | sin sección 6 |
| `svgs.json` | Figuras del caso (formato `{MÓDULO: [{"svg": [...], "huella": "..."}]}`) | sin figuras |
| `08_GLOSARIO.md` | Apéndice B, glosario de la base del curso | sin glosario |

Si falta alguno, el generador se detiene y lo dice. Con `--permitir-faltantes` genera un PDF **parcial**: las secciones afectadas salen marcadas «Sección no generada» y el generador lista lo que faltó. Un PDF parcial no es el manual completo.

## Dependencias

- Python: `markdown` y `playwright` (ambos en `requirements-dev.txt`), más las de `requirements.txt`. Chromium de Playwright: `python -m playwright install chromium`.
- Sistema: `pdfinfo` y `pdftotext` (paquete poppler-utils). Sirven para numerar el índice en una segunda pasada.
- Archivos del repositorio que usa: `app/datos/comandos.json`, `app/ui/logo10_oscuro.svg`, `app/ui/fuentes/Montserrat.woff2`.
