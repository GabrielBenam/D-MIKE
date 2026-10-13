"""Modo del proyecto: real o demostración (D-MIKE 0.26, E1-R3 a E1-R7).

El modo vive en proyecto.formatos["_modo"] = {valor, deteccion: "declarado"|"inferido_v1", cambiado}. Un .dmike sin «_modo»
se trata con la regla de inferencia aplicada a su «_receta.origen» (si no hay receta, real). No cambia la tabla del .dmike."""
import json, os, unicodedata

REAL, DEMO = "real", "demostracion"
MODOS = (REAL, DEMO)
ETIQUETA = "SINTÉTICO / NO EMPRESARIAL"
DECLARADO, INFERIDO = "declarado", "inferido_v1"
_HUELLAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos", "huellas_sinteticas.json")


def _plano(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t or "")) if unicodedata.category(c) != "Mn").lower()


def inferir_por_origen(origen):
    """E1-R3: «caso maestro» o «sintétic…» en el origen (sin acentos ni mayúsculas) -> demostración; si no, real."""
    t = _plano(origen)
    return DEMO if ("caso maestro" in t or "sintetic" in t) else REAL


def huellas_conocidas():
    """Huellas SHA-256 de las recetas sintéticas que distribuye el repositorio (refuerzo opcional de E1-R3)."""
    try:
        with open(_HUELLAS, encoding="utf-8") as f: return set(json.load(f).get("huellas", []))
    except (OSError, ValueError): return set()


def detectar(receta, huella=None):
    """(valor, deteccion) de una receta. Declarado solo si trae modo_proyecto; si no, se infiere (v1)."""
    m = receta.get("modo_proyecto")
    if m in MODOS: return m, DECLARADO
    if huella and huella in huellas_conocidas(): return DEMO, INFERIDO
    return inferir_por_origen(receta.get("origen")), INFERIDO


def _origen_de_receta(r):
    if not isinstance(r, dict): return ""
    if r.get("origen"): return r["origen"]
    try: return (json.loads(r.get("json") or "{}") or {}).get("origen", "")
    except (ValueError, TypeError): return ""


def estado(proyecto):
    """Registro de modo vigente del proyecto (lo guardado, o el inferido de «_receta.origen»; sin receta, real)."""
    m = (proyecto.formatos or {}).get("_modo")
    if isinstance(m, dict) and m.get("valor") in MODOS:
        return {"valor": m["valor"], "deteccion": m.get("deteccion") or INFERIDO, "cambiado": bool(m.get("cambiado"))}
    rec = (proyecto.formatos or {}).get("_receta")
    if isinstance(rec, dict) and rec.get("json"):
        try:
            rc = json.loads(rec["json"])
            if rc.get("modo_proyecto") in MODOS: return {"valor": rc["modo_proyecto"], "deteccion": DECLARADO, "cambiado": False}
        except (ValueError, TypeError, AttributeError): pass
    return {"valor": inferir_por_origen(_origen_de_receta(rec)), "deteccion": INFERIDO, "cambiado": False}


def valor(proyecto): return estado(proyecto)["valor"]
def es_demo(proyecto): return valor(proyecto) == DEMO


def etiqueta(proyecto):
    """Texto de la marca si el proyecto es de demostración; None si es real (nunca se marca un proyecto real)."""
    return ETIQUETA if es_demo(proyecto) else None


def fijar(proyecto, valor_, deteccion, cambiado=False):
    proyecto.formatos["_modo"] = {"valor": valor_, "deteccion": deteccion, "cambiado": bool(cambiado)}


def puede_cambiar(proyecto, hoja):
    """E1-R4: un solo cambio, solo si fue inferido y antes de cargar datos. Devuelve (ok, motivo)."""
    e = estado(proyecto)
    if e["deteccion"] != INFERIDO: return False, "El modo fue declarado por la receta y no se puede cambiar."
    if e["cambiado"]: return False, "El modo ya se cambió una vez; no se puede cambiar de nuevo."
    if hoja.n or hoja.columnas or proyecto.resultados or any(not k.startswith("_") for k in proyecto.formatos):
        return False, "El modo no se puede cambiar después de cargar datos."
    return True, ""


def estampar_png(datos, texto=ETIQUETA):
    """Devuelve el PNG con una franja superior que lleva la etiqueta (la marca forma parte de la imagen exportada)."""
    import io
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(io.BytesIO(datos)).convert("RGB")
    alto = max(28, img.height // 14)
    fuente = None
    ttf = os.path.join(os.path.dirname(_HUELLAS), "fuentes", "Montserrat-Bold.ttf")
    for ruta in (ttf, "DejaVuSans-Bold.ttf"):
        try: fuente = ImageFont.truetype(ruta, int(alto * 0.55)); break
        except OSError: continue
    fuente = fuente or ImageFont.load_default()
    lienzo = Image.new("RGB", (img.width, img.height + alto), "white")
    d = ImageDraw.Draw(lienzo); d.rectangle([0, 0, img.width, alto], fill="#B3261E")
    d.text((img.width // 2, alto // 2), texto, fill="white", font=fuente, anchor="mm")
    lienzo.paste(img, (0, alto))
    b = io.BytesIO(); lienzo.save(b, format="PNG")
    return b.getvalue()
