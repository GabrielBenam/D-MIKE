"""Perfil del proyecto (perfil_proyecto.json) exportado por el artefacto de diagnóstico.

validar() no toca nada del programa: devuelve el perfil normalizado o la lista de errores.
Esquema tomado de arbol_diagnostico.json (esquema_salida) y de Arbol_Diagnostico.md.
"""
import json

FASES_VALIDAS = ("D", "M", "A", "I", "C")
PRIORIDADES = {"N": "núcleo", "R": "recomendado", "P": "prerrequisito", "O": "opcional", "X": "no recomendado", "U": "activado por ti"}
# Tipos de columna del perfil -> tipos de la hoja. id y cat son etiquetas: se capturan como texto.
TIPO_HOJA = {"fecha": "fecha", "num": "num", "id": "texto", "cat": "texto", "texto": "texto"}
CAMPOS_FIJOS = ("nombre_proyecto", "cliente_area", "responsable", "logo", "notas")
ETIQUETA_FIJO = {"nombre_proyecto": "Proyecto", "cliente_area": "Cliente o área", "responsable": "Responsable",
                 "logo": "Logo", "notas": "Notas"}


class PerfilInvalido(Exception):
    def __init__(self, errores):
        super().__init__("; ".join(errores)); self.errores = errores


def _es_entero(x): return isinstance(x, int) and not isinstance(x, bool)


def _lista_textos(x): return isinstance(x, list) and all(isinstance(t, str) for t in x)


def validar(texto, catalogo):
    """Devuelve (perfil_normalizado, avisos). Lanza PerfilInvalido con todos los errores encontrados."""
    try:
        p = json.loads(texto)
    except (json.JSONDecodeError, TypeError) as e:
        raise PerfilInvalido([f"el archivo no es un JSON legible ({getattr(e, 'msg', e)})"])
    if not isinstance(p, dict):
        raise PerfilInvalido(["el archivo no contiene un perfil (se esperaba un objeto JSON)"])
    err, avisos = [], []

    v = p.get("version_perfil")
    if not _es_entero(v) or v < 1: err.append("falta version_perfil o no es un entero mayor o igual a 1")
    for campo, tipo, nombre in (("modulos", list, "lista"), ("hoja_datos_sugerida", list, "lista"),
                                ("datos_fijos", dict, "objeto")):
        if campo not in p: err.append(f"falta el campo {campo}")
        elif not isinstance(p[campo], tipo): err.append(f"{campo} debe ser {nombre}")

    modulos = []
    for i, m in enumerate(p.get("modulos") if isinstance(p.get("modulos"), list) else []):
        if not isinstance(m, dict) or not isinstance(m.get("id"), str):
            err.append(f"modulos[{i + 1}] no tiene id"); continue
        f = m.get("fase_asignada")
        if f not in FASES_VALIDAS:
            err.append(f"el módulo {m['id']} tiene una fase no válida ({f!r}); se esperaba D, M, A, I o C"); continue
        info = catalogo.info(m["id"])
        if info is None:
            avisos.append(f"El módulo {m['id']} no existe en el catálogo v{catalogo.version}; se ignora."); continue
        if f not in info["fases"]:
            avisos.append(f"El módulo {m['id']} está asignado a la fase {f}, que no le corresponde en el árbol.")
        pr = m.get("prioridad")
        modulos.append({"id": m["id"], "fase": f, "estado": m.get("estado", "activo"),
                        "prioridad": pr if pr in PRIORIDADES else None,
                        "motivos": [x for x in m.get("motivos", []) if isinstance(x, str)],
                        "datos_minimos": m.get("datos_minimos") or "",
                        "verificar": bool(m.get("verificar_fase_anterior"))})

    columnas, vistos = [], set()
    for i, c in enumerate(p.get("hoja_datos_sugerida") if isinstance(p.get("hoja_datos_sugerida"), list) else []):
        if not isinstance(c, dict) or not isinstance(c.get("nombre"), str) or not c["nombre"].strip():
            err.append(f"hoja_datos_sugerida[{i + 1}] no tiene nombre"); continue
        if c.get("tipo") not in TIPO_HOJA:
            err.append(f"la columna sugerida {c['nombre']} tiene un tipo no válido ({c.get('tipo')!r})"); continue
        n = c["nombre"].strip()
        if n.lower() in vistos: avisos.append(f"La columna sugerida {n} está repetida; se toma una vez."); continue
        vistos.add(n.lower())
        columnas.append({"nombre": n, "tipo": TIPO_HOJA[c["tipo"]], "tipo_perfil": c["tipo"],
                         "rol": c.get("rol") if isinstance(c.get("rol"), str) else None, "desc": c.get("desc") or ""})

    fijos = {}
    df = p.get("datos_fijos") if isinstance(p.get("datos_fijos"), dict) else {}
    for k in CAMPOS_FIJOS:
        x = df.get(k)
        if x is not None and not isinstance(x, str): err.append(f"datos_fijos.{k} debe ser texto"); continue
        fijos[k] = x.strip() if isinstance(x, str) and x.strip() else None
    if fijos.get("logo") and not fijos["logo"].startswith("data:image/"):
        avisos.append("El logo del perfil no es una imagen incrustada; se omite."); fijos["logo"] = None

    for campo in ("advertencias", "notas", "ruta_sugerida"):
        if campo in p and not _lista_textos(p[campo]): err.append(f"{campo} debe ser una lista de textos")
    for campo in ("sugeridos", "no_recomendados", "pendientes_datos"):
        if campo in p and not (isinstance(p[campo], list) and all(isinstance(x, dict) for x in p[campo])):
            err.append(f"{campo} debe ser una lista de objetos")
    diag = p.get("diagnostico") if isinstance(p.get("diagnostico"), dict) else {}
    if diag.get("fase_actual") not in (None, *FASES_VALIDAS):
        err.append(f"diagnostico.fase_actual no es válida ({diag.get('fase_actual')!r})")
    if err: raise PerfilInvalido(err)

    av = p.get("arbol_version")
    if av is None: avisos.append("El perfil no indica la versión del árbol con que se generó.")
    elif str(av) != str(catalogo.version):
        avisos.append(f"El perfil se generó con el árbol v{av} y el programa usa v{catalogo.version}.")

    def ids(lista):
        return [x["id"] for x in lista if isinstance(x.get("id"), str) and x["id"] in catalogo.modulos]

    return {
        "version": v, "arbol_version": av, "generado_en": p.get("generado_en"),
        "perfil_empresa": p.get("perfil_empresa") if isinstance(p.get("perfil_empresa"), dict) else {},
        "diagnostico": diag, "modulos": modulos, "columnas": columnas, "datos_fijos": fijos,
        "sugeridos": ids(p.get("sugeridos", [])), "no_recomendados": ids(p.get("no_recomendados", [])),
        "advertencias": p.get("advertencias", []), "notas": p.get("notas", []),
        "pendientes_datos": [x for x in p.get("pendientes_datos", []) if isinstance(x.get("modulo"), str)],
        "ruta_sugerida": p.get("ruta_sugerida", []), "siguiente_paso": p.get("siguiente_paso"),
    }, avisos
