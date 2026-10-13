"""Rutas a recursos del programa, válidas en desarrollo y en el ejecutable."""
import sys
from pathlib import Path


def base() -> Path:
    # PyInstaller descomprime los recursos en sys._MEIPASS
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "app"
    return Path(__file__).resolve().parent.parent


def recurso(*partes) -> Path:
    return base().joinpath(*partes)
