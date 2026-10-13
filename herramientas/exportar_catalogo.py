"""Exporta el catálogo de módulos de D-MIKE a JSON: python herramientas/exportar_catalogo.py [--salida CARPETA]

Fuente: registro de módulos (analisis + formatos) y menús de la cinta. No ejecuta ningún cálculo.
Por módulo: id, título, ruta de la cinta, fases, tipo, parámetros con sus opciones (análisis)
o campos de cabecera y tablas (formatos). Se regenera en cada versión (ver CLAUDE.md)."""
import argparse, json, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _opciones(c):
    return [{"valor": o[0], "etiqueta": o[1]} if isinstance(o, (list, tuple)) else {"valor": o, "etiqueta": str(o)}
            for o in c.get("opciones") or []]


def _campo(c):
    d = {"campo": c.get("campo"), "etiqueta": c.get("etiqueta") or c.get("campo"), "tipo": c.get("tipo") or "texto"}
    for k in ("filtro", "defecto", "opcional", "calc", "fijo", "lectura", "ayuda"):
        if c.get(k) not in (None, "", False): d[k] = c[k]
    if c.get("opciones"): d["opciones"] = _opciones(c)
    return d


def _tabla(t):
    return {"id": t.get("id"), "titulo": t.get("titulo") or t.get("id"), "filas": t.get("filas"),
            "columnas": [_campo(c) for c in t.get("columnas", [])]}


def construir():
    from app.api import Api, VERSION
    from app.modulos import cargar
    from app.modulos.formatos import FORMATOS
    registro = cargar()
    info = Api().info_modulos()
    modulos = []
    for mid in sorted(registro):
        cls, i = registro[mid], info.get(mid, {})
        m = {"id": mid, "titulo": i.get("titulo") or getattr(cls, "TITULO", mid), "ruta": i.get("ruta", ""),
             "fases": i.get("fases", []), "tipo": "formato" if mid in FORMATOS else "analisis"}
        if mid in FORMATOS:
            m["cabecera"] = [_campo(c) for c in getattr(cls, "CABECERA", [])]
            m["tablas"] = [_tabla(t) for t in getattr(cls, "TABLAS", [])]
        else:
            m["parametros"] = [_campo(c) for c in getattr(cls, "CAMPOS", None) or []]
        modulos.append(m)
    return {"version": VERSION, "total_modulos": len(modulos), "modulos": modulos}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", default=str(RAIZ / "proyecto" / "catalogo"), help="carpeta de salida")
    a = ap.parse_args(argv)
    cat = construir()
    destino = Path(a.salida); destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / f"catalogo_dmike_{cat['version']}.json"
    ruta.write_text(json.dumps(cat, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{ruta}: {cat['total_modulos']} módulos")
    return ruta


if __name__ == "__main__":
    main()
