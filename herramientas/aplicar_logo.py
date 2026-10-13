"""Aplica uno de los logos de la carpeta logos/ al programa: copia app/ui/logo.svg y regenera app/datos/icono.ico.
Uso (desde la carpeta del proyecto):  python herramientas/aplicar_logo.py 2
Requiere playwright con chromium y pillow (solo para el desarrollo, no para el usuario final)."""
import io, shutil, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def main(n):
    svg = RAIZ / "logos" / f"logo_{n}.svg"
    if not svg.exists(): raise SystemExit(f"No existe {svg}")
    shutil.copy(svg, RAIZ / "app" / "ui" / "logo.svg")
    from playwright.sync_api import sync_playwright
    from PIL import Image
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 256, "height": 256})
        pg.set_content(f'<body style="margin:0;background:transparent">{svg.read_text(encoding="utf-8").replace("<svg ", "<svg width=256 height=256 ", 1)}</body>')
        png = pg.screenshot(omit_background=True); b.close()
    Image.open(io.BytesIO(png)).save(RAIZ / "app" / "datos" / "icono.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Logo {n} aplicado.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
