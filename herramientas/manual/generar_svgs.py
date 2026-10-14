"""Genera herramientas/manual/entradas/svgs.json: las gráficas SVG del caso maestro que el manual inserta en la sección 6.
Corre la receta sintética del caso (pruebas/sinteticos/caso_integral_datos_llenos.xlsx) en D-MIKE y guarda, por módulo,
una lista con un elemento por resultado de ese módulo, en el orden del proyecto:
    {"MÓDULO": [{"svg": [<svg de cada gráfica del resultado>], "huella": "<SHA-256 de su copia congelada>"}, ...]}
gen.py lo lee como SV[módulo][k]["svg"][j] (k = k-ésimo resultado del módulo, j = j-ésima gráfica).
Uso (desde cualquier directorio): python herramientas/manual/generar_svgs.py [--salida RUTA.json]"""
import argparse, json, re, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(RAIZ))
FECHA = re.compile(r"\s*<dc:date>[^<]*</dc:date>")                 # matplotlib sella cada SVG con la hora: se quita para que el archivo sea reproducible
RECETA = RAIZ / "pruebas" / "sinteticos" / "caso_integral_datos_llenos.xlsx"


def generar():
    import matplotlib
    matplotlib.rcParams["svg.hashsalt"] = "dmike-manual"           # ids estables: la misma corrida da el mismo archivo
    from app.api import Api
    a = Api()
    r = a.ejecutar_receta(str(RECETA))
    if r["error"]: sys.exit("No se pudo ejecutar la receta del caso: " + r["sesion"][0]["texto"])
    sv = {}
    for x in a.resultados():
        res = a.resultado(x["uid"])
        svgs = [FECHA.sub("", b["svg"]) for b in res["bloques"] if b.get("tipo") == "grafica" and b.get("svg")]
        sv.setdefault(res["modulo"], []).append({"svg": svgs, "huella": res["definicion"]["congelado"]["huella"]})
    return sv


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", default=str(AQUI / "entradas" / "svgs.json"))
    destino = Path(ap.parse_args().salida); destino.parent.mkdir(parents=True, exist_ok=True)
    sv = generar()
    destino.write_text(json.dumps(sv, ensure_ascii=False), encoding="utf-8")
    print(destino, "|", sum(len(v) for v in sv.values()), "resultados,", sum(len(r["svg"]) for v in sv.values() for r in v), "gráficas,", len(sv), "módulos")
