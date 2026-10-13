"""Regenera app/datos/huellas_sinteticas.json: huellas del contenido de las recetas sintéticas que distribuye el repositorio
(refuerzo de E1-R3: se reconocen como demostración aunque su «origen» no lo diga). Uso: python herramientas/huellas_sinteticas.py"""
import glob, json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from app.nucleo import receta as RC  # noqa: E402

FUENTES = ["pruebas/sinteticos/caso_integral_plantilla.xlsx", "pruebas/sinteticos/caso_integral_datos_llenos.xlsx"]


def calcular():
    out = {}
    for rel in FUENTES:
        rc, _ = RC.leer(os.path.join(RAIZ, rel)); out[rel] = RC.huella_sintetica(rc)
    return out


if __name__ == "__main__":
    h = calcular()
    with open(os.path.join(RAIZ, "app", "datos", "huellas_sinteticas.json"), "w", encoding="utf-8") as f:
        json.dump({"nota": "Huellas (huella_sintetica) de las recetas sintéticas del repositorio. Regenerar con herramientas/huellas_sinteticas.py.",
                   "recetas": h, "huellas": sorted(set(h.values()))}, f, ensure_ascii=False, indent=1)
    print(json.dumps(h, indent=1))
