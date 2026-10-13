# D-MIKE

Programa de escritorio para Windows que administra proyectos de mejora Lean Six Sigma por fases DMAIC,
con módulos estadísticos y gráficos al estilo Minitab, formatos propios y exportación de datos limpios para Minitab.

## Estructura

- `main.py`: arranque (ventana pywebview con WebView2). `main.py --prueba` revisa el programa sin abrir ventana.
- `app/api.py`: puente entre la interfaz y el motor.
- `app/nucleo/`: hoja de datos, catálogo del árbol, perfil y fusión, archivo .dmike y exportación.
- `app/modulos/`: módulos del MVP (`estadistica.py` tiene las fórmulas con su fuente en la base LSS).
- `app/ui/`: interfaz (HTML, CSS y JavaScript propios; Montserrat con licencia OFL).
- `pruebas/`: pytest y Playwright con el puente real de Python; solo datos sintéticos.
- `.github/workflows/compilar.yml` e `instalador/d-mike.iss`: compilación en GitHub Actions e instalador.

## Pruebas (entorno de desarrollo)

    pip install -r requirements.txt -r requirements-dev.txt
    python -m playwright install chromium
    python -m pytest pruebas -q
