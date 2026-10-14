"""Regenera MANIFIESTO.txt a partir de los archivos versionados en git.

Uso: python herramientas/generar_manifiesto.py
El catálogo vigente se deduce de VERSION (app/api.py); no hay números de versión escritos a mano.
"""
import re, subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENCABEZADO = "# Lista de archivos de D-MIKE. La compilación revisa que todos estén en el repositorio."


def version():
    return re.search(r'VERSION = "([^"]+)"', (RAIZ / "app" / "api.py").read_text(encoding="utf-8"))[1]


def archivos():
    out = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    lista = {f for f in out.splitlines() if f and f != "MANIFIESTO.txt" and (RAIZ / f).exists()}
    lista.add(f"proyecto/catalogo/catalogo_dmike_{version()}.json")
    return sorted(lista)


def main():
    (RAIZ / "MANIFIESTO.txt").write_text(ENCABEZADO + "\n" + "\n".join(archivos()) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
