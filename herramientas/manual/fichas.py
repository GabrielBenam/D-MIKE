"""Fichas de 15 puntos del manual: lectura, validación y ejecución de sus ejemplos con la API real del programa.
Sin efectos al importar. Todas las rutas son relativas a la raíz del repositorio. Los ejemplos corren siempre con un APPDATA temporal."""
import contextlib, json, os, re, sys, tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
TIPOS_VALIDOS = ("interfaz", "analisis", "formato", "gestion")
ROTULO_TIPO = {"interfaz": "Operación de interfaz", "analisis": "Análisis", "formato": "Formato", "gestion": "Gestión"}
PENDIENTE = "[PENDIENTE DE REDACCIÓN]"
_SECCION = re.compile(r"^## (\d{1,2})\. (.+?)\s*$", re.M)
_EJEMPLO = re.compile(r"^```ejemplo[ \t]*\n(.*?)\n```[ \t]*$", re.M | re.S)


class FichaInvalida(ValueError):
    pass


@contextlib.contextmanager
def entorno_temporal():
    """APPDATA temporal: ejecutar ejemplos nunca toca los datos del usuario."""
    previo = os.environ.get("APPDATA")
    with tempfile.TemporaryDirectory(prefix="dmike_fichas_") as d:
        os.environ["APPDATA"] = d
        try: yield d
        finally:
            if previo is None: os.environ.pop("APPDATA", None)
            else: os.environ["APPDATA"] = previo


# ---------- lectura ----------
def leer_ficha(ruta):
    """Devuelve {id, tipo, titulo, puntos: {n: (titulo, texto)}, ejemplos: [dict], archivo}. Lanza FichaInvalida si el archivo no cumple el formato."""
    ruta = Path(ruta); txt = ruta.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", txt, re.S)
    if not m: raise FichaInvalida(f"{ruta.name}: falta el encabezado (front matter) entre líneas «---».")
    meta = {}
    for l in m.group(1).splitlines():
        if ":" in l: k, v = l.split(":", 1); meta[k.strip()] = v.strip()
    for k in ("id", "tipo"):
        if not meta.get(k): raise FichaInvalida(f"{ruta.name}: el encabezado no trae «{k}».")
    if meta["tipo"] not in TIPOS_VALIDOS: raise FichaInvalida(f"{ruta.name}: tipo «{meta['tipo']}» fuera de {TIPOS_VALIDOS}.")
    if meta["id"] != ruta.stem: raise FichaInvalida(f"{ruta.name}: el id «{meta['id']}» no coincide con el nombre del archivo.")
    cuerpo = txt[m.end():]
    ejemplos = []
    for e in _EJEMPLO.finditer(cuerpo):
        try: ejemplos.append(json.loads(e.group(1)))
        except json.JSONDecodeError as ex: raise FichaInvalida(f"{ruta.name}: bloque «ejemplo» con JSON inválido ({ex}).")
    limpio = _EJEMPLO.sub("", cuerpo)
    marcas = list(_SECCION.finditer(limpio)); puntos = {}
    for i, s in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(limpio)
        n = int(s.group(1))
        if n in puntos: raise FichaInvalida(f"{ruta.name}: el punto {n} aparece dos veces.")
        puntos[n] = (s.group(2), limpio[s.end():fin].strip())
    faltan = [n for n in range(1, 16) if n not in puntos]
    if faltan or len(puntos) != 15: raise FichaInvalida(f"{ruta.name}: la ficha debe tener los puntos 1 a 15 (faltan {faltan}; hay {sorted(puntos)}).")
    return {"id": meta["id"], "tipo": meta["tipo"], "titulo": meta.get("titulo", meta["id"]), "puntos": puntos, "ejemplos": ejemplos, "archivo": ruta.name}


def cargar_fichas(carpeta):
    """{id: ficha} de todos los .md de la carpeta (no entra a borradores/)."""
    carpeta = Path(carpeta)
    return {p.stem: leer_ficha(p) for p in sorted(carpeta.glob("*.md"))} if carpeta.is_dir() else {}


def cargar_tipos(ruta):
    d = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return d["tipos"]


def pendientes_de_redaccion(ficha):
    return [n for n, (_, t) in sorted(ficha["puntos"].items()) if PENDIENTE in t or "[REDACCIÓN PENDIENTE]" in t]


# ---------- ejecución de ejemplos ----------
def _tabla(bloques, titulo):
    return next((b for b in bloques if b.get("tipo") == "tabla" and b.get("titulo") == titulo), None)


def _nuevo_api():
    from app.api import Api
    return Api()


def _verificar_formato(ej):
    """Acta vacía -> avisos; acta llena -> avisos y texto de conclusión. Compara con vacio_esperado_avisos, esperado_avisos y esperado_texto."""
    api = _nuevo_api(); mid = ej["modulo"]; dif = []
    v = api.abrir_formato(mid)
    if "vacio_esperado_avisos" in ej and v["calc"]["avisos"] != ej["vacio_esperado_avisos"]:
        dif.append(f"avisos del formato vacío: esperado {ej['vacio_esperado_avisos']}, obtenido {v['calc']['avisos']}")
    d = v["datos"]
    d["cabecera"].update(ej.get("cabecera", {}))
    for t, filas in ej.get("tablas", {}).items(): d["tablas"][t] = filas
    r = api.guardar_formato(mid, d); c = r["calc"]
    if "esperado_avisos" in ej and c["avisos"] != ej["esperado_avisos"]:
        dif.append(f"avisos: esperado {ej['esperado_avisos']}, obtenido {c['avisos']}")
    textos = [b.get("texto") for b in c.get("bloques", []) if b.get("tipo") == "texto"]
    if "esperado_texto" in ej and ej["esperado_texto"] not in textos:
        dif.append(f"texto: esperado «{ej['esperado_texto']}», obtenido {textos}")
    salida = {"avisos": c["avisos"], "bloques": c.get("bloques", []), "mensajes": [s["texto"] for s in r.get("sesion", [])]}
    return dif, salida


def _verificar_hoja(ej):
    """Ejemplo de operación de la hoja: pega los datos, aplica los pasos y compara mensajes y celdas."""
    api = _nuevo_api(); dif = []; mensajes = []
    api.pegar(-1, 0, ej["datos"])
    for i, p in enumerate(ej.get("pasos", []), 1):
        if p.get("accion"):
            r = getattr(api, p["accion"])()
        else:
            r = api.ejecutar_modulo(p["modulo"], p.get("parametros", {}))
        textos = [s["texto"] for s in r.get("sesion", [])]; mensajes += textos
        if r.get("error"): dif.append(f"paso {i}: el programa devolvió error «{r['error']}» ({textos})")
        if "esperado_mensaje" in p and p["esperado_mensaje"] not in textos:
            dif.append(f"paso {i}: mensaje esperado «{p['esperado_mensaje']}», obtenido {textos}")
    for k, esperado in ej.get("esperado_hoja", {}).items():
        real = list(api.hoja.columnas[int(k)].celdas)
        if real != esperado: dif.append(f"hoja, columna {k}: esperado {esperado}, obtenido {real}")
    return dif, {"mensajes": mensajes}


def _verificar_analisis(ej):
    api = _nuevo_api(); dif = []
    api.pegar(-1, 0, ej["datos"])
    r = api.ejecutar_modulo(ej["modulo"], ej.get("parametros", {}))
    if r.get("error"): return [f"el programa devolvió error «{r['error']}»: {[s['texto'] for s in r['sesion']]}"], {}
    res = r["resultado"]; esp = ej.get("esperado", {})
    if "tabla" in esp:
        t = _tabla(res["bloques"], esp["tabla"])
        if t is None: dif.append(f"no hay tabla «{esp['tabla']}» (hay {[b.get('titulo') for b in res['bloques'] if b.get('tipo') == 'tabla']})")
        elif "fila" in esp and esp["fila"] not in [list(map(str, f)) for f in t["filas"]]:
            dif.append(f"tabla «{esp['tabla']}»: fila esperada {esp['fila']}, obtenida {t['filas']}")
    return dif, {"resultado": res}


def verificar_ejemplo(ej):
    """Ejecuta un ejemplo y devuelve {ok, diferencias, salida}. Usa un Api nuevo y APPDATA temporal."""
    with entorno_temporal():
        try:
            if ej.get("tipo") == "formato": dif, salida = _verificar_formato(ej)
            elif "pasos" in ej: dif, salida = _verificar_hoja(ej)
            else: dif, salida = _verificar_analisis(ej)
        except Exception as e:                                  # un ejemplo roto se reporta, no detiene la generación
            dif, salida = [f"el ejemplo no se pudo ejecutar: {type(e).__name__}: {e}"], {}
    return {"ok": not dif, "diferencias": dif, "salida": salida}


def verificar_ficha(ficha):
    return [verificar_ejemplo(e) for e in ficha["ejemplos"]]


# ---------- outputs reales (R-F4) ----------
def resumen_bloques(bloques):
    """Lista ordenada de lo que el resultado muestra: tablas con sus columnas, gráficas, textos."""
    out = []
    for b in bloques:
        if b.get("tipo") == "tabla": out.append({"tipo": "tabla", "titulo": b["titulo"], "columnas": list(b["cabeza"])})
        elif b.get("tipo") == "grafica": out.append({"tipo": "grafica", "interactiva": (b.get("inter") or {}).get("g")})
        elif b.get("tipo") == "texto": out.append({"tipo": "texto", "clase": b.get("clase", ""), "texto": b["texto"]})
    return out


def outputs_reales(ficha, verificaciones):
    """Outputs del primer ejemplo con salida: {'bloques': [...], 'avisos': [...], 'mensajes': [...]} (vacío si no hay)."""
    for v in verificaciones:
        s = v["salida"]
        if "resultado" in s:
            return {"bloques": resumen_bloques(s["resultado"]["bloques"]), "avisos": list(s["resultado"]["avisos"]), "mensajes": [], "png": bool(s["resultado"].get("png"))}
        if "bloques" in s:
            return {"bloques": resumen_bloques(s["bloques"]), "avisos": list(s.get("avisos", [])), "mensajes": [], "png": False}
        if s.get("mensajes"):
            return {"bloques": [], "avisos": [], "mensajes": list(dict.fromkeys(s["mensajes"])), "png": False}
    return {"bloques": [], "avisos": [], "mensajes": [], "png": False}


def comparar_punto9(ficha, real):
    """Avisos si lo escrito a mano en el punto 9 difiere de lo ejecutado (título de cada tabla y orden de sus columnas)."""
    texto = ficha["puntos"][9][1]; avisos = []
    for b in real["bloques"]:
        if b["tipo"] != "tabla": continue
        if b["titulo"] not in texto: avisos.append(f"{ficha['id']}: la tabla «{b['titulo']}» no aparece en el punto 9.")
        pos = 0
        for c in b["columnas"]:
            i = texto.find(c, pos)
            if i < 0: avisos.append(f"{ficha['id']}: la columna «{c}» de «{b['titulo']}» no aparece (o está fuera de orden) en el punto 9."); break
            pos = i + len(c)
    n_graf = sum(1 for b in real["bloques"] if b["tipo"] == "grafica")
    if n_graf == 0 and re.search(r"genera (?:una )?gr[aá]fica", texto) and "No genera gr" not in texto:
        avisos.append(f"{ficha['id']}: el punto 9 habla de gráfica y la ejecución no produjo ninguna.")
    if n_graf and "No genera gr" in texto: avisos.append(f"{ficha['id']}: el punto 9 dice que no genera gráfica y la ejecución produjo {n_graf}.")
    return avisos


# ---------- índice por pregunta ----------
CAMPOS_PREGUNTA = ("pregunta", "ruta", "fase", "tipo_dato", "resultado_esperado", "nivel", "fuente_base")


def validar_indice_preguntas(datos, ids_validos):
    """Devuelve la lista de problemas del esquema (vacía si es válido)."""
    probs = []
    if not isinstance(datos.get("preguntas"), list): return ["falta la lista «preguntas»."]
    for i, p in enumerate(datos["preguntas"], 1):
        falta = [c for c in CAMPOS_PREGUNTA if c not in p]
        if falta: probs.append(f"pregunta {i}: faltan campos {falta}.")
        ruta = p.get("ruta")
        if not isinstance(ruta, list) or not 2 <= len(ruta) <= 4: probs.append(f"pregunta {i}: «ruta» debe ser una lista de 2 a 4 IDs.")
        else:
            malos = [m for m in ruta if m not in ids_validos]
            if malos: probs.append(f"pregunta {i}: IDs que no existen en el catálogo: {malos}.")
    return probs
