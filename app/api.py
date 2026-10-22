"""Puente entre la interfaz (JavaScript) y el motor (Python)."""
from .nucleo.catalogo import Catalogo, FASES
from .nucleo.sesion import Sesion
from .nucleo.hoja import Hoja
from .nucleo import menus
from .nucleo.perfil import validar, PerfilInvalido
from .nucleo.proyecto import Proyecto, FusionRechazada
from .nucleo import archivo
from .nucleo import modo as MD
from .nucleo import seguimiento as SG
from . import modulos
from .nucleo import indicadores as IND, disenos as DIS, corridas as CORR, auditoria as AUD, confirmacion as CONF
from .modulos.base import ErrorEntrada, agregar_nota_persona, agregar_estados_entrada
import json, os
from datetime import datetime

VERSION = "0.28.0"
NOMBRE_TIPO = {"num": "numérico", "texto": "texto", "fecha": "fecha"}


def filtro_archivo(t):
    """pywebview solo acepta filtros «Descripción (*.ext;*.ext)» con letras, números y espacios en la descripción
    (webview.util.parse_file_type). Un guion, como en «D-MIKE», hacía fallar el diálogo de Abrir y Guardar."""
    import re
    m = re.match(r"^(.*?)\s*\((\*.*)\)$", t.strip())
    if not m: return "Todos los archivos (*.*)"
    desc = re.sub(r"[^\w ]+", " ", m.group(1)); desc = re.sub(r"\s+", " ", desc).strip() or "Archivos"
    return f"{desc} ({m.group(2)})"


def _nombre_seguro(n):
    import re
    return re.sub(r'[\\/:*?"<>|]+', " ", n or "").strip()


FASES_N = [("D", "Definir"), ("M", "Medir"), ("A", "Analizar"), ("I", "Mejorar"), ("C", "Controlar")]


class Api:
    def __init__(self):
        self.catalogo = Catalogo()
        self.sesion = Sesion()
        self.hoja = Hoja()
        self.proyecto = Proyecto()
        self._ventana = None
        self.ruta = None
        self._deshacer, self._rehacer = [], []
        self.registro = modulos.cargar()
        self._sucio = False
        self._docs, self._sig_doc, self._activo = [], 1, None
        self._nuevo_doc()
        self.sesion.registrar(f"D-MIKE {VERSION} iniciado. Catálogo del árbol v{self.catalogo.version}: "
                              f"{len(self.catalogo.modulos)} módulos.")

    def estado_inicial(self):
        return {"version": VERSION, "fases": [{"id": f, "nombre": n} for f, n in FASES],
                "catalogo": self.catalogo.por_fase(), "menus": menus.como_datos(),
                "hoja": self.hoja.estado(), "sesion": self.sesion.entradas, "proyecto": self.proyecto.estado(self.catalogo),
                "archivo": self._archivo(), "comandos": self._comandos(), "recientes": self.recientes(),
                "modulos_info": self.info_modulos()}

    def _comandos(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), "datos", "comandos.json"), encoding="utf-8") as f: return json.load(f)
        except (OSError, ValueError): return []

    # ---------- proyectos recientes (archivo de usuario: así sobreviven aunque la ventana no guarde preferencias) ----------
    def _ruta_recientes(self):
        base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
        return os.path.join(base, "D-MIKE", "recientes.json")

    def recientes(self):
        try:
            with open(self._ruta_recientes(), encoding="utf-8") as f: lista = json.load(f)
        except (OSError, ValueError): return []
        return [r for r in lista if isinstance(r, dict) and os.path.exists(r.get("ruta", ""))][:12]

    def _anotar_reciente(self):
        if not self.ruta: return
        try:
            lista = [r for r in self.recientes() if r.get("ruta") != self.ruta]
            fase = (self.proyecto.estado(self.catalogo) or {}).get("fase_actual") if self.proyecto else None
            nombre = (self.proyecto.fijos.get("nombre_proyecto") or {}).get("valor") or os.path.basename(self.ruta)
            lista.insert(0, {"ruta": self.ruta, "nombre": nombre, "fase": fase, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                             "avance": sum(1 for m in self.proyecto.modulos.values() if m.get("avance") != "pendiente")})
            os.makedirs(os.path.dirname(self._ruta_recientes()), exist_ok=True)
            with open(self._ruta_recientes(), "w", encoding="utf-8") as f: json.dump(lista[:12], f, ensure_ascii=False)
        except OSError: pass

    def quitar_reciente(self, ruta):
        try:
            lista = [r for r in self.recientes() if r.get("ruta") != ruta]
            with open(self._ruta_recientes(), "w", encoding="utf-8") as f: json.dump(lista, f, ensure_ascii=False)
        except OSError: pass
        return {"recientes": self.recientes()}

    def ayuda_datos(self):
        """Todo lo que necesita la ayuda interna (F1): menús, comandos, catálogo por fase, módulos y versión."""
        return {"version": VERSION, "menus": menus.como_datos(), "comandos": self._comandos(), "catalogo": self.catalogo.por_fase(),
                "fases": [{"id": f, "nombre": n} for f, n in FASES], "modulos": self.info_modulos()}

    def info_modulos(self):
        """Por módulo: título, descripción breve (del catálogo de comandos), ruta en la cinta, fases y la nota con sus fuentes."""
        from .modulos.formatos import FORMATOS
        import unicodedata
        norm = lambda t: unicodedata.normalize("NFD", (t or "").lower()).encode("ascii", "ignore").decode().replace("…", "").strip(" .")
        desc = {norm(c["n"]): c["d"] for c in self._comandos()}
        out = {}
        for t, ops in menus.MENUS:
            g = ""
            for x, a in ops:
                if x.startswith("§"): g = x[1:]; continue
                if not a or not a.startswith("mod:") or a[4:] in out: continue
                mid = a[4:]; c = self.registro.get(mid); info = self.catalogo.info(mid) or {}
                titulo = getattr(c, "TITULO", x.replace("…", "")) if c else x.replace("…", "")
                out[mid] = {"titulo": titulo, "ruta": f"{t} › {g} › {x.replace('…', '')}", "fases": info.get("fases", []),
                            "desc": desc.get(norm(x)) or desc.get(norm(titulo)) or info.get("datos_minimos") or "",
                            "nota": getattr(FORMATOS.get(mid), "NOTA", "") if mid in FORMATOS else ""}
        return out

    def modificado(self):
        return self._sucio

    def _archivo(self):
        return {"nombre": os.path.basename(self.ruta) if self.ruta else None, "modificado": self.modificado()}

    def _resp(self, texto=None, tipo="info", error=None, mensajes=(), proyecto=False, hoja=True):
        """Respuesta estándar a la interfaz. mensajes: [(texto, tipo)] adicionales para la sesión."""
        ses = [self.sesion.registrar(texto, tipo)] if texto else []
        ses += [self.sesion.registrar(t, k) for t, k in mensajes]
        r = {"error": error, "sesion": ses, "archivo": self._archivo()}
        if hoja:
            DIS.sincronizar(self.proyecto, self.hoja)                  # E3-2: RunId es de solo lectura (se reescribe de OrdenEst); E3-3: versión de las respuestas
            r["hoja"] = self.hoja.estado()
        if proyecto: r["proyecto"] = self.proyecto.estado(self.catalogo)
        return r

    # --- archivos: diálogo nativo de Windows (las pruebas lo sustituyen) ---
    def _elegir(self, modo, tipos, nombre=""):
        if self._ventana is None: return None
        import webview
        fd = getattr(webview, "FileDialog", None)
        if fd is not None: clase = {"abrir": fd.OPEN, "guardar": fd.SAVE, "carpeta": fd.FOLDER}[modo]
        else: clase = {"abrir": webview.OPEN_DIALOG, "guardar": webview.SAVE_DIALOG, "carpeta": webview.FOLDER_DIALOG}[modo]
        if modo == "carpeta": r = self._ventana.create_file_dialog(clase)
        else: r = self._ventana.create_file_dialog(clase, file_types=tuple(filtro_archivo(t) for t in tipos), save_filename=_nombre_seguro(nombre))
        if not r: return None
        return r if isinstance(r, str) else r[0]

    # --- perfil del proyecto (incrementos 3 y 4) ---
    def abrir_perfil(self, ruta=None):
        ruta = ruta or self._elegir("abrir", ["Perfil del proyecto (*.json)", "Todos los archivos (*.*)"])
        if not ruta: return self._resp("Apertura del perfil cancelada.")
        try:
            with open(ruta, encoding="utf-8-sig") as f: texto = f.read()
        except (OSError, UnicodeDecodeError) as e:
            return self._resp(f"No se pudo leer el archivo: {e}", "aviso", error="lectura")
        try:
            perfil, avisos = validar(texto, self.catalogo)
        except PerfilInvalido as e:
            lista = e.errores[:8] + ([f"y {len(e.errores) - 8} errores más"] if len(e.errores) > 8 else [])
            return self._resp("El perfil no se cargó porque no es válido: " + "; ".join(lista) +
                              ". No se cambió nada.", "aviso", error="perfil")
        previa = self.proyecto.version
        try:
            msgs = self.proyecto.aplicar_perfil(perfil, self.hoja)
        except FusionRechazada as e:
            return self._resp(str(e), "aviso", error="version")
        if previa:
            cab = f"Perfil v{perfil['version']} fusionado con el proyecto (antes v{previa}); no se borró ningún dato."
        else:
            cab = (f"Perfil v{perfil['version']} cargado: {sum(1 for m in self.proyecto.modulos.values() if m['estado'] == 'activo')}"
                   f" módulos activos, fase actual {perfil['diagnostico'].get('fase_actual') or 'sin indicar'}.")
        extra = [(a, "aviso") for a in avisos] + msgs
        extra += [(f"Advertencia del diagnóstico: {w}", "aviso") for w in perfil["advertencias"]]
        extra += [(f"Nota del diagnóstico: {w}", "info") for w in perfil["notas"]]
        for pd in perfil["pendientes_datos"]:
            extra.append((f"Datos pendientes para {pd['modulo']}: {pd.get('minimos', '')}", "info"))
        if perfil["siguiente_paso"]:
            nom = self.catalogo.modulos.get(perfil["siguiente_paso"], {}).get("nombre", perfil["siguiente_paso"])
            extra.append((f"Siguiente paso sugerido: {nom}.", "info"))
        return self._resp(cab, mensajes=extra, proyecto=True)

    def fijar_datos(self, valores):
        cambios = 0
        for k, v in valores.items():
            antes = self.proyecto.fijos.get(k, {}).get("valor")
            self.proyecto.fijar_dato(k, v)
            cambios += antes != self.proyecto.fijos[k]["valor"]
        return self._resp(f"Datos fijos actualizados ({cambios} cambios)." if cambios else None, proyecto=True, hoja=False)

    def activar_modulo(self, mid, fase):
        try: self.proyecto.activar_modulo(mid, fase, self.catalogo)
        except ValueError as e: return self._resp(str(e), "aviso", error="modulo", hoja=False)
        return self._resp(f"{self.catalogo.info(mid)['nombre']}: activado en la fase {dict(FASES_N)[fase]}.", proyecto=True, hoja=False)

    def desactivar_modulo(self, mid):
        try: self.proyecto.desactivar_modulo(mid)
        except ValueError as e: return self._resp(str(e), "aviso", error="modulo", hoja=False)
        return self._resp(f"{(self.catalogo.info(mid) or {}).get('nombre', mid)}: pasó a inactivos. Sus capturas se conservan.", proyecto=True, hoja=False)

    def marcar_avance(self, mid, avance):
        self.proyecto.marcar_avance(mid, avance)
        return self._resp(f"{mid}: avance «{avance.replace('_', ' ')}».", proyecto=True, hoja=False)

    # --- hoja de datos ---
    def _solo_lectura(self, c0, c1=None):
        """E3-2: respuesta de error si el rango toca una columna RunId (solo lectura); None si se puede editar."""
        c1 = c0 if c1 is None else c1
        if any(c0 <= j <= c1 for j in DIS.columnas_protegidas(self.proyecto, self.hoja)):
            return self._resp("RunId es de solo lectura: se genera con design_id y OrdenEst del diseño y no se edita.", "aviso", error="solo_lectura")
        return None

    def editar(self, fila, col, texto):
        if (b := self._solo_lectura(col)): return b
        n0, nc0 = self.hoja.n, len(self.hoja.columnas)
        antes = self.hoja.columnas[col].tipo if col < nc0 else None
        self.hoja.editar(fila, col, texto)
        runid_cambio = DIS.sincronizar(self.proyecto, self.hoja)       # editar OrdenEst cambia el RunId de esa fila: se envía la hoja completa
        c = self.hoja.columnas[col] if col < len(self.hoja.columnas) else None
        malo = bool(c and fila < self.hoja.n and not c.valor(fila)[1])
        if malo:
            msg, tipo = (f"C{col + 1}, fila {fila + 1}: «{texto}» no es {NOMBRE_TIPO[c.tipo]}; queda marcado y no entra en los cálculos.", "aviso")
        elif c and antes is None and c.tipo:
            msg, tipo = f"C{col + 1} queda como columna de tipo {NOMBRE_TIPO[c.tipo]}.", "info"
        else:
            msg, tipo = None, "info"
        if self.hoja.n != n0 or len(self.hoja.columnas) != nc0 or (c and c.tipo != antes) or self.hoja.filtro or runid_cambio:
            return self._resp(msg, tipo)                               # cambió la estructura: se envía la hoja completa
        r = self._resp(msg, tipo, hoja=False)
        if c is not None and fila < self.hoja.n:
            t = c.valor(fila)
            r["delta"] = {"f": fila, "c": col, "texto": t[0], "valida": t[1], "etiqueta": r["archivo"] and None}
            r["delta"].pop("etiqueta")
        return r

    def pegar(self, fila, col, texto):
        if not texto or not texto.strip(): return self._resp()
        if (b := self._solo_lectura(col, col + max(l.count("\t") for l in texto.split("\n")))): return b
        nf, nc = self.hoja.pegar(fila, col, texto)
        malas = len(self.hoja.invalidas())
        msg = f"Pegados {nf} filas por {nc} columnas desde C{col + 1}" + (" con nombres." if fila == -1 else ".")
        if malas: msg += (" Hay 1 celda que no corresponde" if malas == 1 else f" Hay {malas} celdas que no corresponden") + " al tipo de su columna."
        return self._resp(msg, "aviso" if malas else "info")

    def renombrar(self, col, nombre):
        if (b := self._solo_lectura(col)): return b
        try:
            self.hoja.renombrar(col, nombre)
        except ValueError as e:
            return self._resp(str(e), "aviso", error=str(e))
        return self._resp()

    def cambiar_tipo(self, col, tipo):
        if (b := self._solo_lectura(col)): return b
        malas = self.hoja.cambiar_tipo(col, tipo)
        extra = f" {malas} celdas no corresponden y quedan marcadas." if malas else ""
        return self._resp(f"C{col + 1} cambiada a tipo {NOMBRE_TIPO[tipo]}.{extra}", "aviso" if malas else "info")

    def insertar_columna(self, col):
        self.hoja.insertar_columna(col); return self._resp(f"Columna insertada en C{col + 1}.")

    def eliminar_columna(self, col):
        self.hoja.eliminar_columna(col); return self._resp(f"Columna C{col + 1} eliminada.")

    def insertar_fila(self, fila):
        self.hoja.insertar_fila(fila); return self._resp(f"Fila insertada en la posición {fila + 1}.")

    def eliminar_fila(self, fila):
        self.hoja.eliminar_fila(fila); return self._resp(f"Fila {fila + 1} eliminada.")

    def borrar_rango(self, f0, c0, f1, c1, filas=None):
        if (b := self._solo_lectura(min(c0, c1), max(c0, c1))): return b
        n = self.hoja.borrar_rango(f0, c0, f1, c1, filas)
        return self._resp(f"Borrado el contenido de {n} celdas." if n else None)

    def rellenar(self, f0, c0, f1, c1, direccion="abajo"):
        if (b := self._solo_lectura(min(c0, c1), max(c0, c1))): return b
        n = self.hoja.rellenar(f0, c0, f1, c1, direccion)
        return self._resp(f"Rellenadas {n} celdas hacia {'abajo' if direccion == 'abajo' else 'la derecha'}." if n else None)

    def llenar_con(self, f0, c0, f1, c1, texto, filas=None):
        if (b := self._solo_lectura(min(c0, c1), max(c0, c1))): return b
        n = self.hoja.llenar_con(f0, c0, f1, c1, texto, filas)
        return self._resp(f"Escrito el mismo valor en {n} celdas.")

    def texto_rango(self, f0, c0, f1, c1):
        return self.hoja.texto_rango(f0, c0, f1, c1)

    def insertar_filas(self, fila, k=1):
        self.hoja.insertar_filas(fila, k); return self._resp(f"{k} filas insertadas desde la posición {fila + 1}.")

    def eliminar_filas(self, f0, f1):
        self.hoja.eliminar_filas(f0, f1); return self._resp(f"Eliminadas las filas {f0 + 1} a {f1 + 1}." if f1 > f0 else f"Fila {f0 + 1} eliminada.")

    def eliminar_columnas(self, c0, c1):
        self.hoja.eliminar_columnas(c0, c1); return self._resp(f"Eliminadas las columnas C{c0 + 1} a C{c1 + 1}." if c1 > c0 else f"Columna C{c0 + 1} eliminada.")

    def filtrar(self, condiciones):
        try:
            n = self.hoja.aplicar_filtro(condiciones or [])
        except ValueError as e:
            return self._resp(f"Filtro no aplicado: {e}", "aviso", error="filtro")
        if not condiciones: return self._resp("Filtro quitado: se muestran todas las filas.")
        return self._resp(f"Filtro activo: se muestran {n} de {self.hoja.n} filas. Las filas ocultas no entran a los análisis.")

    def info_filtro(self):
        return {"cols": [{"j": j, "nombre": c.nombre or f"C{j + 1}", "tipo": c.tipo} for j, c in enumerate(self.hoja.columnas) if c.tipo],
                "ops": [[k, v] for k, v in Hoja.OPS.items()], "filtro": self.hoja.filtro}

    # --- archivo de proyecto y exportación (incremento 5) ---
    # ---------- varios proyectos abiertos a la vez (como los dibujos de AutoCAD) ----------
    def _campos_doc(self): return ("hoja", "proyecto", "ruta", "_deshacer", "_rehacer", "_sucio")

    def _guardar_doc(self):
        d = next((x for x in self._docs if x["id"] == self._activo), None)
        if d is not None:
            for k in self._campos_doc(): d[k] = getattr(self, k)

    def _cargar_doc(self, d):
        for k in self._campos_doc(): setattr(self, k, d[k])
        self._activo = d["id"]

    def _nuevo_doc(self):
        self._guardar_doc()
        d = {"id": self._sig_doc, "hoja": Hoja(), "proyecto": Proyecto(), "ruta": None, "_deshacer": [], "_rehacer": [], "_sucio": False}
        self._sig_doc += 1; self._docs.append(d); self._cargar_doc(d)
        return d

    def _virgen(self):
        """El proyecto activo está vacío y sin tocar: se puede reutilizar al abrir otro."""
        p = self.proyecto
        return (self.ruta is None and not self._sucio and self.hoja.n == 0 and not p.modulos and not p.resultados
                and not [k for k in p.formatos if not k.startswith("_")] and not any(v["valor"] for v in p.fijos.values()))

    def _nombre_doc(self, d):
        p = d["proyecto"]; n = (p.fijos.get("nombre_proyecto") or {}).get("valor")
        return n or (os.path.basename(d["ruta"]) if d["ruta"] else f"Proyecto {d['id']}")

    def proyectos(self):
        self._guardar_doc()
        return {"proyectos": [{"id": d["id"], "nombre": self._nombre_doc(d), "ruta": d["ruta"], "modificado": bool(d["_sucio"]),
                               "activo": d["id"] == self._activo, "sintetico": MD.es_demo(d["proyecto"]),
                               "etiqueta": MD.etiqueta(d["proyecto"])} for d in self._docs]}

    # ---------- modo del proyecto: real o demostración (0.26) ----------
    def modo_proyecto(self):
        e = MD.estado(self.proyecto); ok, motivo = MD.puede_cambiar(self.proyecto, self.hoja)
        return {**e, "etiqueta": MD.etiqueta(self.proyecto), "puede_cambiar": ok, "motivo": motivo}

    def cambiar_modo(self, valor):
        """Cambia el modo UNA vez, solo si fue inferido y antes de cargar datos (E1-R4)."""
        if valor not in MD.MODOS: return self._resp("El modo debe ser «real» o «demostracion».", "aviso", error="modo", hoja=False)
        ok, motivo = MD.puede_cambiar(self.proyecto, self.hoja)
        if not ok: return self._resp(motivo, "aviso", error="modo", hoja=False)
        if valor == MD.valor(self.proyecto): return self._resp(f"El proyecto ya está en modo {valor}; no se consumió el cambio.", hoja=False)
        MD.fijar(self.proyecto, valor, MD.INFERIDO, cambiado=True); self._sucio = True
        return self._resp(f"Modo del proyecto: {valor}. Ya no se puede cambiar.", proyecto=True, hoja=False)

    def _con_marca(self, res):
        """Copia del resultado con la etiqueta «SINTÉTICO / NO EMPRESARIAL» si el proyecto es de demostración (nunca en un proyecto real)."""
        et = MD.etiqueta(self.proyecto)
        return {**res, "etiqueta": et} if (res is not None and et) else res

    def _doc_con_id(self, idp, excluir=None):
        self._guardar_doc()
        return next((d for d in self._docs if d["id"] != excluir and (d["proyecto"].formatos.get("_receta") or {}).get("id_proyecto") == idp), None)

    def _reciente_con_id(self, idp):
        """Proyecto reciente (guardado, no abierto) que ya tiene ese id_proyecto: lee solo el JSON del proyecto, sin cargar la hoja."""
        abiertas = {os.path.abspath(d["ruta"]) for d in self._docs if d["ruta"]}
        for r in self.recientes():
            if os.path.abspath(r["ruta"]) in abiertas: continue
            if archivo.id_proyecto_de(r["ruta"]) == idp: return r
        return None

    def cambiar_proyecto(self, id_doc):
        d = next((x for x in self._docs if x["id"] == id_doc), None)
        if d is None: return self._resp("Ese proyecto ya no está abierto.", "aviso", error="proyecto")
        if d["id"] != self._activo: self._guardar_doc(); self._cargar_doc(d)
        return self._resp(proyecto=True)

    def cerrar_proyecto(self, id_doc, forzar=False):
        self._guardar_doc()
        d = next((x for x in self._docs if x["id"] == id_doc), None)
        if d is None: return self._resp(hoja=False)
        if d["_sucio"] and not forzar:
            r = self._resp(hoja=False); r["confirmar"] = self._nombre_doc(d); return r
        self._docs.remove(d)
        if d["id"] == self._activo:
            self._activo = None
            if self._docs: self._cargar_doc(self._docs[-1])
            else: self._nuevo_doc()
        return self._resp(f"Proyecto cerrado: {self._nombre_doc(d)}.", proyecto=True)

    def nuevo_proyecto(self):
        if not self._virgen(): self._nuevo_doc()
        else: self.hoja, self.proyecto, self.ruta, self._deshacer, self._rehacer, self._sucio = Hoja(), Proyecto(), None, [], [], False
        return self._resp("Proyecto nuevo, hoja vacía.", proyecto=True)

    def guardar(self, como=False):
        ruta = self.ruta
        if como or not ruta:
            nombre = (self.proyecto.fijos["nombre_proyecto"]["valor"] or "proyecto") + ".dmike"
            ruta = self._elegir("guardar", ["Proyecto D-MIKE (*.dmike)"], nombre)
            if not ruta: return self._resp("Guardado cancelado.")
            if not ruta.lower().endswith(".dmike"): ruta += ".dmike"
        try:
            archivo.guardar(ruta, self.hoja, self.proyecto, VERSION)
        except (OSError, Exception) as e:
            return self._resp(f"No se pudo guardar: {e}. El proyecto sigue abierto sin cambios.", "aviso", error="guardar")
        self.ruta, self._sucio = ruta, False
        self._anotar_reciente()
        return self._resp(f"Proyecto guardado en {ruta}.")

    def abrir_proyecto(self, ruta=None):
        ruta = ruta or self._elegir("abrir", ["Proyecto D-MIKE (*.dmike)", "Receta del diagnóstico (*.xlsx;*.json)"])
        if not ruta: return self._resp("Apertura cancelada.")
        if ruta.lower().endswith((".xlsx", ".json")): return self.abrir_receta(ruta)
        self._guardar_doc()
        ya = next((d for d in self._docs if d["ruta"] and os.path.abspath(d["ruta"]) == os.path.abspath(ruta)), None)
        if ya is not None:
            self._cargar_doc(ya); return self._resp(f"{os.path.basename(ruta)} ya estaba abierto: se muestra su pestaña.", proyecto=True)
        try:
            hd, pd, meta = archivo.abrir(ruta)
            hoja, proy = Hoja.de_dict(hd), Proyecto.de_dict(pd)
        except archivo.ArchivoInvalido as e:
            return self._resp(f"No se abrió el proyecto: {e}. No se cambió nada.", "aviso", error="abrir")
        if not self._virgen(): self._nuevo_doc()
        self.hoja, self.proyecto, self.ruta = hoja, proy, ruta
        self._anotar_reciente()
        self._deshacer, self._rehacer = [], []
        self._sucio = False
        return self._resp(f"Proyecto abierto: {os.path.basename(ruta)} ({hoja.n} filas, {len(hoja.columnas)} columnas"
                          f"{', perfil v' + str(proy.version) if proy.version else ''}).", proyecto=True)

    # ---------- recetas del diagnóstico en línea ----------
    def abrir_receta(self, ruta=None):
        """Lee y valida una receta; no cambia nada. La interfaz pregunta si se ejecuta."""
        from .nucleo import receta as RC
        ruta = ruta or self._elegir("abrir", ["Receta del diagnóstico (*.xlsx;*.json)"])
        if not ruta: return self._resp("Apertura cancelada.")
        try: rc, datos = RC.leer(ruta)
        except Exception as e: return self._resp(f"No se pudo leer la receta: {e}", "aviso", error="receta")
        modo, det = MD.detectar(rc, RC.huella_sintetica(rc))
        # un modo inferido todavía puede cambiarse en el diálogo: la prueba de datos sintéticos se repite al ejecutar
        errores = RC.validar(rc, modulos.cargar(), VERSION, modo=modo if det == MD.DECLARADO else MD.DEMO)
        if errores: return self._resp("La receta no se puede ejecutar: " + "; ".join(errores[:6]) + ".", "aviso", error="receta")
        msgs = [("Esta receta trae un folio. Es la llave de una sesión web, no una referencia del proyecto: D-MIKE lo ignora y no lo guarda. No lo compartas.", "aviso")] if rc.get("folio") else []
        r = self._resp(f"Receta leída: {os.path.basename(ruta)}. Elige cómo abrirla.", mensajes=msgs)
        r["receta"] = RC.resumen(rc, datos); r["receta"]["ruta"] = ruta
        r["receta"].update(modo=modo, deteccion=det, puede_cambiar_modo=(det == MD.INFERIDO), trae_folio=bool(rc.get("folio")),
                           id_proyecto=rc.get("id_proyecto"), etiqueta=MD.ETIQUETA,
                           sintetico_en_receta=bool(RC.errores_modo(rc, MD.REAL)),
                           revision={"recibida": RC.entero(rc.get("revision")), "base": rc.get("revision_base")},
                           variables=len(rc.get("variables") or []), tareas=len(rc.get("tareas") or []))
        self._guardar_doc()
        r["receta"]["abiertos"] = [{"id": d["id"], "nombre": self._nombre_doc(d)} for d in self._docs]
        idp = rc.get("id_proyecto")
        if idp:
            d = self._doc_con_id(idp)
            if d:
                r["receta"]["actualizable"] = {"id": d["id"], "nombre": self._nombre_doc(d)}
                r["receta"]["estado_revision"] = SG.decidir_revision(d["proyecto"], d["hoja"], rc, datos)
            elif (rec := self._reciente_con_id(idp)): r["receta"]["conflicto_id"] = {"nombre": rec.get("nombre") or os.path.basename(rec["ruta"]), "ruta": rec["ruta"]}
        return r

    def ejecutar_receta(self, ruta, modo="nuevo", id_doc=None, modo_proyecto=None, sin_id=False, resolucion=None, forzar=False):
        """modo «nuevo» (proyecto nuevo), «actualizar» (agrega lo nuevo al proyecto id_doc, que el usuario confirma) o «datos» (solo las hojas).
        modo_proyecto: el modo que elige el usuario; solo se acepta si el de la receta fue inferido (v1), y una vez.
        sin_id: crea el proyecto nuevo sin id_proyecto cuando ese id ya pertenece a otro proyecto.
        Al actualizar se controla la revisión (12.5): «ya aplicada» y «más antigua» (salvo forzar=True) no se aplican; un conflicto exige resolucion
        «solo_nuevo» (aplicar solo lo nuevo) o «cancelar»; sin ella no se aplica nada y se devuelve el conflicto para que la interfaz pregunte."""
        from .nucleo import receta as RC
        try: rc, datos = RC.leer(ruta)
        except Exception as e: return self._resp(f"No se pudo leer la receta: {e}", "aviso", error="receta")
        det_modo, det = MD.detectar(rc, RC.huella_sintetica(rc))
        efectivo, cambiado = det_modo, False
        objetivo = None
        if modo == "actualizar":
            self._guardar_doc()
            objetivo = next((d for d in self._docs if d["id"] == id_doc), None)
            if objetivo is None: return self._resp("Para actualizar elige uno de los proyectos abiertos.", "aviso", error="proyecto")
            efectivo = MD.valor(objetivo["proyecto"])
            if det_modo != efectivo:
                return self._resp(f"No se actualiza: el proyecto es de modo {efectivo} y la receta es de modo {det_modo}. Un proyecto real no recibe datos sintéticos ni uno de demostración datos reales.", "aviso", error="modo")
        elif modo_proyecto is not None and modo_proyecto != det_modo:
            if modo_proyecto not in MD.MODOS: return self._resp("El modo debe ser «real» o «demostracion».", "aviso", error="modo")
            if det != MD.INFERIDO: return self._resp("El modo de esta receta fue declarado por la receta y no se puede cambiar.", "aviso", error="modo")
            efectivo, cambiado = modo_proyecto, True
        errores = RC.validar(rc, modulos.cargar(), VERSION, modo=efectivo)
        if errores and modo != "datos": return self._resp("La receta no se puede ejecutar: " + "; ".join(errores[:6]) + ".", "aviso", error="receta")
        bloqueo = RC.errores_modo(rc, efectivo)
        if bloqueo: return self._resp("La receta no se puede abrir: " + "; ".join(bloqueo[:6]) + ".", "aviso", error="receta")
        # id_proyecto (E1-R9): nunca se asigna uno que ya pertenezca a otro proyecto abierto o reciente
        idp = rc.get("id_proyecto")
        if modo == "datos": idp = None                  # E1.3-R3: «solo abrir los datos» no compara ni asigna id_proyecto
        if idp:
            otro = self._doc_con_id(idp, excluir=objetivo["id"] if objetivo else None)
            previo = (objetivo["proyecto"].formatos.get("_receta") or {}).get("id_proyecto") if objetivo else None
            if otro and not (sin_id and modo != "actualizar"):
                return self._resp(f"El id_proyecto de la receta ya pertenece al proyecto abierto «{self._nombre_doc(otro)}». Actualízalo o crea uno nuevo sin id_proyecto.", "aviso", error="id_conflicto")
            if modo == "actualizar" and previo and previo != idp:
                return self._resp("El proyecto elegido ya tiene otro id_proyecto: la receta no es de este proyecto. No se cambió nada.", "aviso", error="id_conflicto")
            if not otro and modo != "actualizar" and not sin_id and (rec := self._reciente_con_id(idp)):
                return self._resp(f"El id_proyecto de la receta ya pertenece al proyecto reciente «{rec.get('nombre') or os.path.basename(rec['ruta'])}». Ábrelo y actualízalo, o crea uno nuevo sin id_proyecto.", "aviso", error="id_conflicto")
            if sin_id and modo != "actualizar": idp = None
        if modo == "actualizar":
            dec = SG.decidir_revision(objetivo["proyecto"], objetivo["hoja"], rc, datos, forzar=bool(forzar))
            if dec["accion"] == "ya_aplicada":
                r = self._resp("Receta ya aplicada al proyecto «" + self._nombre_doc(objetivo) + "» (misma huella): no se cambió nada.", "aviso", error="ya_aplicada"); r["revision"] = dec; return r
            if dec["accion"] == "mas_antigua":
                r = self._resp(dec["motivo"] + " Puedes forzarla si de verdad quieres volver a esa revisión; la actual pasa al historial.", "aviso", error="revision_antigua"); r["revision"] = dec; return r
            if dec["accion"] == "conflicto":
                if resolucion == "cancelar": return self._resp("Actualización cancelada: no se cambió nada.", error="cancelado")
                if resolucion != "solo_nuevo":
                    r = self._resp(dec["motivo"] + " Elige cancelar o aplicar solo lo nuevo; no se cambió nada.", "aviso", error="conflicto_revision"); r["revision"] = dec; return r
        if modo == "datos":
            self.nuevo_proyecto(); MD.fijar(self.proyecto, efectivo, det, cambiado)
            n = RC.solo_datos(self, rc, datos, idp); self._sucio = True
            return self._resp(f"Datos de la plantilla abiertos: {n} hojas en la hoja de datos. La receta queda guardada en el proyecto.", proyecto=True)
        if modo == "actualizar":
            r0 = self.cambiar_proyecto(id_doc)
            if r0["error"]: return r0
            if "_modo" not in self.proyecto.formatos: e0 = MD.estado(self.proyecto); MD.fijar(self.proyecto, e0["valor"], e0["deteccion"], e0["cambiado"])
        else:
            self.nuevo_proyecto(); MD.fijar(self.proyecto, efectivo, det, cambiado)
        try: out = RC.ejecutar(self, rc, datos, actualizar=(modo == "actualizar"), id_proyecto=idp)
        except Exception as e: return self._resp(f"La receta se detuvo: {e}. Revisa la plantilla.", "aviso", error="receta", proyecto=True)
        self._sucio = True
        msgs = [(t, "info") for t in out["log"]] + [(t, "aviso") for t in out["avisos"]] + [("Pendiente: " + t, "aviso") for t in out["pendientes"]]
        if out.get("tareas_cerradas"): msgs.append((f"Tareas cerradas porque ya se cumplieron: {len(out['tareas_cerradas'])}.", "info"))
        if rc.get("folio"): msgs.append(("La receta traía un folio: se ignoró y no se guardó en el proyecto. Es la llave de una sesión web; no la compartas.", "aviso"))
        r = self._resp(f"Receta ejecutada: {(rc.get('datos_fijos') or {}).get('nombre_proyecto') or 'proyecto'}. Guárdalo con Archivo › Guardar como.", mensajes=msgs, proyecto=True)
        r["receta_resultado"] = out
        return r

    # ---------- seguimiento y paquete de avance (0.27, secciones 12 y 13) ----------
    def seguimiento(self):
        """Vista de solo lectura: variables con su estado, tareas abiertas y estado de cada análisis (calculado contra la hoja y los resultados actuales)."""
        return SG.vista(self.proyecto, self.hoja)

    def exportar_avance(self, ruta=None):
        """Paquete de avance v1 para el diagnóstico en línea: solo estado, con huella. Sin id_proyecto no se exporta."""
        pkg, motivo = SG.paquete_avance(self.proyecto, self.hoja)
        if pkg is None: return self._resp("No se exportó el paquete de avance. " + motivo, "aviso", error="sin_id_proyecto", hoja=False)
        base = ((self.proyecto.fijos["nombre_proyecto"]["valor"] or "proyecto") + "_avance.json")
        ruta = ruta or self._elegir("guardar", ["Paquete de avance (*.json)"], base)
        if not ruta: return self._resp("Exportación cancelada.", hoja=False)
        if not ruta.lower().endswith(".json"): ruta += ".json"
        try:
            with open(ruta, "w", encoding="utf-8") as f: json.dump(pkg, f, ensure_ascii=False, indent=1)
        except OSError as e:
            return self._resp(f"No se pudo exportar el paquete de avance: {e}", "aviso", error="exportar", hoja=False)
        return self._resp(f"Paquete de avance exportado a {ruta}: solo estado (sin datos, valores medidos ni resultados). Revisión aplicada: "
                          f"{pkg['revision_aplicada'] if pkg['revision_aplicada'] is not None else 'ninguna'}.", hoja=False)

    def exportar(self, ruta=None):
        cols, cambios, faltantes = archivo.tabla_limpia(self.hoja)
        if not cols: return self._resp("La hoja está vacía; no hay nada que exportar.", "aviso", error="vacia")
        base = (self.proyecto.fijos["nombre_proyecto"]["valor"] or "datos") + "_minitab.xlsx"
        ruta = ruta or self._elegir("guardar", ["Libro de Excel (*.xlsx)", "CSV UTF-8 (*.csv)"], base)
        if not ruta: return self._resp("Exportación cancelada.")
        ext = os.path.splitext(ruta)[1].lower()
        if ext not in (".xlsx", ".csv"): ruta, ext = ruta + ".xlsx", ".xlsx"
        try:
            (archivo.exportar_xlsx if ext == ".xlsx" else archivo.exportar_csv)(ruta, cols, self.hoja.n, MD.etiqueta(self.proyecto))
        except OSError as e:
            return self._resp(f"No se pudo exportar: {e}", "aviso", error="exportar")
        msgs = []
        if cambios: msgs.append(("Nombres ajustados a las reglas de Minitab: " + ", ".join(cambios) + ".", "aviso"))
        if faltantes: msgs.append((f"{faltantes} celdas que no corresponden a su tipo se exportaron vacías (dato faltante).", "aviso"))
        return self._resp(f"Exportadas {len(cols)} columnas y {self.hoja.n} filas a {ruta}.", mensajes=msgs)

    # --- módulos (incrementos 7 en adelante) ---
    def _auto_avance(self, mid):
        m = self.proyecto.modulos.get(mid)
        if m and m["avance"] == "pendiente":
            m["avance"] = "en_curso"; return True
        return False

    def _modulo(self, mid):
        cls = self.registro.get(mid)
        if cls is None: raise ValueError(f"Módulo desconocido: {mid}")
        return cls

    def _bloqueo_modo(self, mid):
        """E1-R6: Calc › Datos aleatorios genera datos sintéticos; en un proyecto real no se permite."""
        if mid == "ALEATORIOS" and not MD.es_demo(self.proyecto):
            return self._resp("Datos aleatorios genera datos sintéticos y está bloqueado en un proyecto real: nunca se mezclan datos inventados con datos de la empresa. "
                              "Solo se permite en un proyecto de demostración.", "aviso", error="entrada", hoja=False)
        return None

    def dialogo_modulo(self, mid):
        cls = self._modulo(mid)
        if (b := self._bloqueo_modo(mid)): return b
        if not self.hoja.columnas and not getattr(cls, "HOJA_VACIA_OK", False):
            return {"error": "vacia", "sesion": [self.sesion.registrar(
                f"{cls.TITULO}: la hoja de datos está vacía. Captura o pega los datos primero.", "aviso")]}
        return {"error": None, "dialogo": cls.dialogo(self.hoja, self.proyecto)}

    def ejecutar_modulo(self, mid, params):
        cls = self._modulo(mid)
        if (b := self._bloqueo_modo(mid)): return b
        try:
            res = cls.ejecutar(self.hoja, params, self.proyecto)
        except ErrorEntrada as e:
            return self._resp(f"{cls.TITULO}: {e}", "aviso", error="entrada")
        if getattr(cls, "SIN_RESULTADO", False):
            return self._resp(res)
        agregar_nota_persona(res, cls, self.hoja, params)
        agregar_estados_entrada(res, cls, self.hoja, self._cols_de(cls, params))
        res["definicion"] = self._definicion(cls, mid, params)
        res["definicion"]["congelado"] = self._congelar(cls, params)
        self.proyecto.resultados.append(res)
        avance = self._auto_avance(mid)
        r = self._resp(f"{res['titulo']}: listo.", mensajes=[(a, "aviso") for a in res["avisos"]], proyecto=avance,
                       hoja=bool(getattr(cls, "CAMBIA_HOJA", False)))
        r["resultado"] = self._con_marca(res)
        return r

    def _definicion(self, cls, mid, params):
        """Definición reproducible: columnas por NOMBRE (no por posición), parámetros, fecha y tamaño de la hoja."""
        from datetime import datetime
        cols = {}
        for c in getattr(cls, "CAMPOS", []):
            j = params.get(c["campo"])
            nom = lambda k: self.hoja.columnas[k].nombre or f"C{k + 1}"
            if c["tipo"] == "col" and isinstance(j, int) and 0 <= j < len(self.hoja.columnas): cols[c["campo"]] = nom(j)
            elif c["tipo"] == "cols" and isinstance(j, list): cols[c["campo"]] = [nom(k) for k in j if isinstance(k, int) and 0 <= k < len(self.hoja.columnas)]
        return {"analisis": mid, "columnas": cols, "parametros": {k: v for k, v in params.items() if k not in cols},
                "fecha": datetime.now().isoformat(timespec="seconds"), "filas_hoja": self.hoja.n, "version": VERSION}

    # ---------- reproducir contra recalcular (A3) ----------
    def _cols_de(self, cls, params, ncols=None):
        out = []; ncols = len(self.hoja.columnas) if ncols is None else ncols
        for c in getattr(cls, "CAMPOS", []):
            j = params.get(c["campo"])
            if c["tipo"] == "col" and isinstance(j, int) and 0 <= j < ncols: out.append(j)
            elif c["tipo"] == "cols" and isinstance(j, list): out += [k for k in j if isinstance(k, int) and 0 <= k < ncols]
        return sorted(set(out))

    @staticmethod
    def _huella(columnas, filtro=None):
        """SHA-256 de la copia congelada. Sin filtro de filas activo la huella cubre solo las columnas (igual que desde v0.25, así las huellas
        ya guardadas siguen valiendo); con filtro cubre columnas y condiciones (v0.28)."""
        import hashlib
        obj = {"columnas": columnas, "filtro": filtro} if filtro else columnas
        return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    def _cols_congeladas(self, cls, params):
        """Columnas del análisis más las que usa el filtro de filas activo (un filtro oculta filas y cambia el resultado)."""
        cols = set(self._cols_de(cls, params))
        cols |= {f["col"] for f in self.hoja.filtro if isinstance(f.get("col"), int) and 0 <= f["col"] < len(self.hoja.columnas)}
        return sorted(cols)

    def _congelar(self, cls, params):
        """Copia congelada de las entradas: celdas de cada columna usada (texto tal cual, incluidos N/A y «Sin datos»), el filtro de filas
        activo, la versión del motor y la huella SHA-256."""
        cols = {}
        for j in self._cols_congeladas(cls, params):
            c = self.hoja.columnas[j]; cel = list(c.celdas)
            while cel and cel[-1] in (None, ""): cel.pop()
            cols[str(j)] = {"nombre": c.nombre or f"C{j + 1}", "tipo": getattr(c, "tipo", None), "celdas": cel}
        filtro = [dict(f) for f in self.hoja.filtro]
        return {"version": VERSION, "columnas": cols, "filtro": filtro, "huella": self._huella(cols, filtro), "parametros": params}

    def _huella_de_copia(self, cg):
        return self._huella(cg["columnas"], cg.get("filtro"))

    def estado_resultado(self, uid):
        """«vigente» si los datos de la hoja coinciden con la copia congelada; «desactualizado» si cambiaron; «sin_copia» si es anterior a v0.25."""
        res = self.resultado(uid)
        cg = (res or {}).get("definicion", {}).get("congelado")
        if not cg: return {"estado": "sin_copia"}
        actual = {}
        for j, info in cg["columnas"].items():
            k = self.hoja.indice(info["nombre"]) if self.hoja.indice(info["nombre"]) is not None else (int(j) if int(j) < len(self.hoja.columnas) else None)
            if k is None: return {"estado": "desactualizado", "motivo": f"ya no existe la columna {info['nombre']}"}
            cel = list(self.hoja.columnas[k].celdas)
            while cel and cel[-1] in (None, ""): cel.pop()
            actual[j] = {"nombre": info["nombre"], "tipo": info["tipo"], "celdas": cel}
        actual_h = self._huella(actual, [dict(f) for f in self.hoja.filtro] if cg.get("filtro") else None)
        if actual_h == cg["huella"]: return {"estado": "vigente", "huella": cg["huella"][:12], "version": cg["version"]}
        return {"estado": "desactualizado", "motivo": "los datos de la hoja cambiaron desde que se corrió", "huella": cg["huella"][:12], "version": cg["version"]}

    def reproducir_resultado(self, uid):
        """Vuelve a correr el análisis con la copia congelada de sus entradas (no con la hoja actual) y verifica la huella."""
        res = self.resultado(uid)
        cg = (res or {}).get("definicion", {}).get("congelado")
        if not cg: return self._resp("Este resultado es anterior a la copia congelada (v0.25); usa «Repetir con datos actuales».", "aviso", error="sin_copia")
        if self._huella_de_copia(cg) != cg["huella"]: return self._resp("La copia congelada no coincide con su huella: no se reproduce.", "aviso", error="huella")
        from .nucleo.hoja import Hoja
        tmp = Hoja(); n = max([len(v["celdas"]) for v in cg["columnas"].values()] + [1])
        ancho = max(int(j) for j in cg["columnas"]) + 1 if cg["columnas"] else 0
        filas = [[""] * ancho for _ in range(n + 1)]
        for j, info in cg["columnas"].items():
            filas[0][int(j)] = info["nombre"]
            for i, v in enumerate(info["celdas"]): filas[i + 1][int(j)] = "" if v is None else str(v)
        tmp.pegar(-1, 0, "\n".join("\t".join(f) for f in filas))
        for j, info in cg["columnas"].items():
            if info.get("tipo") and int(j) < len(tmp.columnas): tmp.columnas[int(j)].tipo = info["tipo"]       # el tipo que tenía al correr
        if cg.get("filtro"): tmp.filtro = [dict(f) for f in cg["filtro"]]
        cls = self._modulo(res["definicion"]["analisis"])
        try: nuevo = cls.ejecutar(tmp, dict(cg["parametros"]), self.proyecto)
        except ErrorEntrada as e: return self._resp(f"No se pudo reproducir: {e}", "aviso", error="entrada")
        agregar_nota_persona(nuevo, cls, tmp, cg["parametros"])
        agregar_estados_entrada(nuevo, cls, tmp, self._cols_de(cls, cg["parametros"], len(tmp.columnas)))
        nuevo["titulo"] = res["titulo"] + " (reproducción de la versión guardada)"
        nuevo["definicion"] = dict(res["definicion"]); nuevo["definicion"]["reproduccion_de"] = uid
        nuevo["avisos"] = [f"Reproducido con la copia congelada del {res['definicion'].get('fecha', '')[:10]} (motor v{cg['version']}, huella {cg['huella'][:12]}); no usa la hoja actual."] + nuevo["avisos"]
        self.proyecto.resultados.append(nuevo)
        r = self._resp(f"{nuevo['titulo']}: listo."); r["resultado"] = nuevo
        return r

    def repetir_resultado(self, uid):
        """Vuelve a correr un análisis con los datos actuales de la hoja, buscando sus columnas por nombre."""
        res = self.resultado(uid)
        if res is None or "definicion" not in res:
            return self._resp("Este resultado no tiene definición guardada; ábrelo desde el menú para repetirlo.", "aviso", error="sin_definicion")
        d = res["definicion"]; params = dict(d["parametros"]); faltan = []
        def buscar(nombre):
            j = self.hoja.indice(nombre)
            if j is None and nombre[:1] == "C" and nombre[1:].isdigit(): j = int(nombre[1:]) - 1   # columna sin nombre
            if j is None or j >= len(self.hoja.columnas): faltan.append(nombre); return None
            return j
        for campo, nombre in d["columnas"].items():
            params[campo] = [buscar(n) for n in nombre] if isinstance(nombre, list) else buscar(nombre)
        if faltan:
            return self._resp(f"No se puede repetir: faltan las columnas {', '.join(faltan)} en la hoja.", "aviso", error="columnas")
        return self.ejecutar_modulo(d["analisis"], params)

    def texto_resultado(self, uid):
        """Resultado en texto con tabuladores, para copiar y pegar en Excel o en un reporte."""
        res = self.resultado(uid)
        if res is None: return ""
        lineas = [res["titulo"], res["fecha"]] + ([res["etiqueta"]] if res.get("etiqueta") else []) + [""] + [f"Aviso: {a}" for a in res["avisos"]]
        for b in res["bloques"]:
            if b["tipo"] == "texto": lineas += [b["texto"], ""]
            elif b["tipo"] == "tabla":
                lineas += [b["titulo"], "\t".join(b["cabeza"])] + ["\t".join(map(str, f)) for f in b["filas"]] + [""]
        return "\n".join(lineas)

    # ---------- estilos de gráficas (A6): se guardan con el proyecto ----------
    def estilos_graficas(self): return self.proyecto.formatos.get("_graficas") or {}

    def guardar_estilo_grafica(self, clave, estilo):
        g = self.proyecto.formatos.setdefault("_graficas", {})
        if estilo: g[str(clave)] = estilo
        else: g.pop(str(clave), None)
        return {"ok": True}

    def resultados(self):
        return [{"uid": r["uid"], "titulo": r["titulo"], "fecha": r["fecha"], "modulo": r["modulo"], "etiqueta": MD.etiqueta(self.proyecto)} for r in self.proyecto.resultados]

    def resultado(self, uid):
        return self._con_marca(next((r for r in self.proyecto.resultados if r["uid"] == uid), None))

    def borrar_resultado(self, uid):
        antes = len(self.proyecto.resultados)
        self.proyecto.resultados = [r for r in self.proyecto.resultados if r["uid"] != uid]
        return self._resp("Resultado eliminado del proyecto." if len(self.proyecto.resultados) < antes else None, hoja=False)

    def exportar_resultado(self, uid, ruta=None):
        res = self.resultado(uid)
        if res is None: return self._resp("El resultado ya no existe.", "aviso", error="no_existe")
        base = res["titulo"].replace("/", "-").replace(":", "")[:60]
        tipos = ["Reporte de Excel (*.xlsx)"] + (["Imagen PNG (*.png)"] if res.get("png") else [])
        ruta = ruta or self._elegir("guardar", tipos, base + ".xlsx")
        if not ruta: return self._resp("Exportación cancelada.")
        ext = os.path.splitext(ruta)[1].lower()
        if ext not in (".xlsx", ".png"): ruta, ext = ruta + ".xlsx", ".xlsx"
        try:
            if ext == ".png":
                if not res.get("png"): return self._resp("Este resultado no tiene gráfica.", "aviso", error="sin_grafica")
                import base64
                png = base64.b64decode(res["png"])
                if res.get("etiqueta"): png = MD.estampar_png(png, res["etiqueta"])
                with open(ruta, "wb") as f: f.write(png)
            else:
                from .modulos.exportar import reporte_resultado
                cols = [c for c in res.get("datos", {}).get("columnas", []) if c is not None and c < len(self.hoja.columnas)]
                plano = archivo.tabla_limpia(self.hoja, cols)[0] if cols else []
                reporte_resultado(ruta, res, self.proyecto, plano)
        except OSError as e:
            return self._resp(f"No se pudo exportar: {e}", "aviso", error="exportar")
        return self._resp(f"Exportado a {ruta}.")

    def exportar_verificacion(self, uid, ruta=None):
        """Excel con fórmulas vivas de Excel y columna para Minitab, para comparar el análisis."""
        from .modulos import verificacion
        res = self.resultado(uid)
        if res is None or "definicion" not in res: return self._resp("El resultado ya no existe o no tiene definición guardada.", "aviso", error="no_existe", hoja=False)
        ruta = ruta or self._elegir("guardar", ["Libro de Excel (*.xlsx)"], "Verificacion_" + res["titulo"].replace(":", "")[:50] + ".xlsx")
        if not ruta: return self._resp("Exportación cancelada.", hoja=False)
        if not ruta.lower().endswith(".xlsx"): ruta += ".xlsx"
        try:
            k, n = verificacion.construir(ruta, res, self.hoja, self.proyecto)
        except (ValueError, OSError) as e:
            return self._resp(f"No se pudo crear la hoja de verificación: {e}", "aviso", error="verificacion", hoja=False)
        return self._resp(f"Hoja de verificación creada en {ruta}: {k} conceptos sobre {n} filas. Captura los valores de Minitab en la columna D.", hoja=False)

    # --- tablero de indicadores (vista del programa, a partir del formato TABLERO) ---
    def datos_tablero(self):
        from .modulos import kpis
        from .modulos import formatos as formatos_tablero
        from .modulos.formatos import estado_kpi
        cls = self.registro["TABLERO"]; d = cls.normalizar(self.proyecto.formatos.get("TABLERO") or cls.vacio())
        ns, inicio, series, av = cls.series(d, self.hoja); ind = []
        for i, (f, sr) in enumerate(zip(d["tablas"]["kpi"], series)):
            if sr is None: continue
            vals = [sr["vals"].get(s) for s in range(1, ns + 1)]; reales = [v for v in vals if v is not None]
            ult = reales[-1] if reales else None
            sem_ult = max((s for s in range(1, ns + 1) if sr["vals"].get(s) is not None), default=None)
            b_ult = sr["bases"].get(sem_ult) if sem_ult else None
            kid = f.get("kpi_id") or ""; revs = IND.revisiones(self.proyecto, kid) if kid else []
            por_sem = IND.revision_por_semana(revs, inicio, ns)
            ind.append({"i": i, "kpi_id": f.get("kpi_id") or "", "nombre": f.get("indicador") or f"Indicador {i + 1}", "categoria": f.get("categoria") or "Sin categoría",
                        "unidad": f.get("unidad") or "", "sentido": sr["sentido"], "meta": sr["meta"], "adv": sr["adv"], "resumen": (f.get("tarjeta") or "Sí") == "Sí",
                        "vals": vals, "ultimo": ult, "delta": (reales[-1] - reales[-2]) if len(reales) > 1 else None,
                        "estado": estado_kpi(ult, sr["meta"], sr["sentido"], sr["adv"]) if ult is not None else None,
                        "estados": [estado_kpi(v, sr["meta"], sr["sentido"], sr["adv"]) if v is not None else None for v in vals],
                        "tipo": f.get("tipo_ind") or "", "explicacion": f.get("explicacion") or "",
                        # A2: base de cada porcentaje (nunca un % sin su base) y definición versionada
                        "bases": [formatos_tablero.texto_base(sr["bases"].get(s) if (sr["bases"].get(s) or (0, 0))[1] is not None else None) for s in range(1, ns + 1)],
                        "base": formatos_tablero.texto_base(b_ult) if b_ult and b_ult[1] is not None else (
                            "base no registrada" if (f.get("unidad") or "") == "%" and ult is not None else ""),
                        "definicion": {"revision": revs[-1]["revision"] if revs else None, "revisiones": revs, "por_semana": por_sem,
                                       "nota": IND.nota_cruce(revs, por_sem, vals, f.get("indicador") or "")}})
        est = self.proyecto.estado(self.catalogo) if self.proyecto.perfil else None
        fases = []
        if est:
            for fz in "DMAIC":
                act = est["activos"].get(fz, [])
                fases.append({"fase": fz, "total": len(act), "hechos": sum(1 for m in act if m.get("avance") == "hecho"),
                              "en_curso": sum(1 for m in act if m.get("avance") == "en_curso")})
        av = list(av) + [x["definicion"]["nota"] for x in ind if x["definicion"]["nota"]]          # A2: notas de cruce de revisiones
        return {"indicadores": ind, "semanas": ns, "inicio": inicio.isoformat() if inicio else None, "avisos": av, "fases": fases,
                "fase_actual": est["fase_actual"] if est else None,
                "wip": [f for f in d["tablas"]["wip"] if any(f.values())], "catalogo": kpis.catalogo(),
                "proyecto": (self.proyecto.fijos.get("nombre_proyecto") or {}).get("valor") or ""}

    def disenos(self):
        """E3-2: identidad de los diseños del proyecto (design_id, version_diseno, estado de su definición, RunId)."""
        return DIS.descriptores(self.proyecto, self.hoja)

    def importar_respuestas(self, ruta=None, design_id=None, sobrescribir=False):
        """E3-3: importa las respuestas de un diseño por RunId (columnas RunId, version_diseno, la respuesta y, opcional, los factores). Atómica:
        con un solo desajuste no se escribe nada y se informa cada error."""
        from .nucleo import importar as imp, respuestas as RS
        ruta = ruta or self._elegir("abrir", ["Respuestas del diseño (*.csv;*.tsv;*.txt;*.xlsx)", "Todos los archivos (*.*)"])
        if not ruta: return self._resp("Importación cancelada.", hoja=False)
        nombre = os.path.basename(ruta)
        try: filas, fmt = imp.leer(ruta); huella = RS.huella_archivo(ruta)
        except (OSError, ValueError) as e:
            return self._resp(f"No se pudieron leer las respuestas: {e}. No se cambió nada.", "aviso", error="respuestas", hoja=False)
        plan = RS.analizar(self.proyecto, self.hoja, filas, design_id, bool(sobrescribir))
        resumen = {k: plan[k] for k in ("ok", "errores", "avisos", "design_id", "version", "escritas", "iguales", "sobrescritas", "sin_dato")}
        if not plan["ok"]:
            r = self._resp(f"Respuestas no importadas de {nombre}: {len(plan['errores'])} {'problema' if len(plan['errores']) == 1 else 'problemas'}. No se escribió nada.",
                           "aviso", error="respuestas", mensajes=[(e, "aviso") for e in plan["errores"]] + [(a, "info") for a in plan["avisos"]], hoja=False)
            r["importacion"] = resumen; return r
        n = RS.aplicar(self.proyecto, self.hoja, plan, nombre, huella)
        r = self._resp(f"Importadas {n} respuestas de {nombre} ({fmt}) al diseño {plan['design_id']}, versión {plan['version']}"
                       + (f"; {plan['iguales']} ya estaban iguales" if plan["iguales"] else "") + (f"; {plan['sobrescritas']} sobrescritas" if plan["sobrescritas"] else "") + ".",
                       mensajes=[(a, "info") for a in plan["avisos"]])
        r["importacion"] = resumen; return r

    def exportar_corridas(self, design_id=None, ruta=None, con_respuestas=False):
        """E3-4: exporta las corridas del diseño sin respuestas (RunId, versión, orden de corrida, tipo de punto, bloque, factores y la respuesta en blanco),
        en el orden en que se corre, a CSV UTF-8 o Excel. Se vuelve a importar con importar_respuestas."""
        try: cab, filas, meta = CORR.preparar(self.proyecto, self.hoja, design_id, bool(con_respuestas))
        except ValueError as e: return self._resp(str(e), "aviso", error="corridas", hoja=False)
        ruta = ruta or self._elegir("guardar", ["Libro de Excel (*.xlsx)", "CSV UTF-8 (*.csv)"], f"{meta['design_id']}_corridas.xlsx")
        if not ruta: return self._resp("Exportación cancelada.", hoja=False)
        ext = os.path.splitext(ruta)[1].lower()
        if ext not in (".xlsx", ".csv"): ruta, ext = ruta + ".xlsx", ".xlsx"
        try:
            if ext == ".xlsx": CORR.escribir_xlsx(ruta, cab, filas, meta)
            else: CORR.escribir_csv(ruta, cab, filas)
        except OSError as e: return self._resp(f"No se pudo exportar las corridas: {e}", "aviso", error="corridas", hoja=False)
        r = self._resp(f"Exportadas {len(filas)} corridas de {meta['design_id']} (versión {meta['version_diseno']}) a {ruta}, en el orden en que se corren. "
                       + ("Incluye las respuestas que ya hay en la hoja." if con_respuestas else "La respuesta va en blanco: captúrala al correr cada experimento y vuelve con «Importar respuestas del diseño»."), hoja=False)
        r["corridas"] = {"design_id": meta["design_id"], "version_diseno": meta["version_diseno"], "n": len(filas), "ruta": ruta}
        return r

    def auditar_diseno(self, design_id):
        """E3-8: auditoría del diseño (alias, aleatorización, restricciones, curvatura, falta de ajuste, confirmación). Solo en pantalla: no viaja en el paquete de avance."""
        a, motivo = AUD.auditar(self.proyecto, self.hoja, design_id)
        if a is None: return {"error": "auditoria", "mensaje": motivo}
        return {"error": None, "auditoria": a}

    def planes_confirmacion(self, design_id=None):
        """E3-9: planes de confirmación o vigilancia registrados (de un diseño, o todos)."""
        return CONF.planes(self.proyecto, design_id)

    def registrar_plan_confirmacion(self, tipo, n_corridas, criterio, condiciones, origen, design_id=None, predicho=None, resultado_uid=None, x0=None):
        """E3-9: registra un plan de confirmación experimental o de vigilancia posterior. Tamaño de muestra, criterio de éxito y condiciones los define el usuario."""
        estado, r = CONF.registrar_plan(self.proyecto, tipo, n_corridas, criterio, condiciones, origen, design_id or None, predicho, resultado_uid or None, x0)
        if estado == "error": return self._resp(r, "aviso", error="confirmacion", hoja=False)
        out = self._resp(f"Plan {r['id']} registrado ({CONF.TIPOS[r['tipo']]}, {r['n_corridas']} corridas). Valor predicho: {r['predicho']['valor']:.6g}.", hoja=False)
        out["plan"] = r; return out

    def registrar_observados_confirmacion(self, plan_id, valores):
        """E3-9: captura las observaciones de un plan de confirmación (números separados por punto y coma, o por coma si el decimal es punto)."""
        estado, msg = CONF.registrar_observados(self.proyecto, plan_id, valores)
        return self._resp(msg, "aviso" if estado == "error" else "info", error="confirmacion" if estado == "error" else None, hoja=False)

    def comparar_confirmacion(self, plan_id):
        """E3-9: observado menos predicho; el intervalo de predicción solo en regresión simple (27_BB REG-PREDICCION)."""
        c, motivo = CONF.comparar(self.proyecto, plan_id)
        if c is None: return {"error": "confirmacion", "mensaje": motivo}
        return {"error": None, "comparacion": c}

    def omitir_paso_doe(self, que, motivo=""):
        """E3-7: el usuario omite el cribado, el DCC o el DOE completo con un motivo registrado (sin motivo no se omite)."""
        estado, msg = DIS.omitir(self.proyecto, que, motivo)
        r = self._resp(msg, "aviso" if estado == "error" else "info", error="omitir" if estado == "error" else None, hoja=False)
        r["estado"] = estado; r["omisiones"] = DIS.omisiones(self.proyecto); return r

    def omisiones(self):
        """E3-7: omisiones justificadas registradas en el proyecto."""
        return DIS.omisiones(self.proyecto)

    def declarar_limites_diseno(self, design_id, limites):
        """E3-5 parte B: declara (o cambia) la región autorizada de un diseño existente («90, 125; 5, 40»). Todos sus puntos actuales deben caber en ella."""
        estado, msg = DIS.declarar_limites(self.proyecto, self.hoja, design_id, limites)
        r = self._resp(msg, "aviso" if estado == "error" else "info", error="limites" if estado == "error" else None, hoja=False)
        r["estado"] = estado; r["disenos"] = DIS.descriptores(self.proyecto, self.hoja); return r

    def confirmar_respuestas_diseno(self, design_id, motivo=""):
        """E3-3: el usuario declara, con motivo registrado, que las respuestas de la hoja corresponden a la versión vigente del diseño."""
        estado, msg = DIS.confirmar_respuestas(self.proyecto, self.hoja, design_id, motivo)
        r = self._resp(msg, "aviso" if estado == "error" else "info", error="confirmar" if estado == "error" else None, hoja=False)
        r["estado"] = estado; r["disenos"] = DIS.descriptores(self.proyecto, self.hoja); return r

    def registrar_version_diseno(self, design_id, motivo=""):
        """E3-2: el usuario pide registrar una versión nueva del diseño cuando su definición cambió; el número lo asigna D-MIKE."""
        estado, msg = DIS.registrar_version(self.proyecto, self.hoja, design_id, motivo)
        r = self._resp(msg, "aviso" if estado == "error" else "info", error="version" if estado == "error" else None, hoja=False)
        r["estado"] = estado; r["disenos"] = DIS.descriptores(self.proyecto, self.hoja)
        return r

    def definicion_indicador(self, i):
        """A2: definición vigente y revisiones del indicador de la fila i del tablero."""
        cls = self.registro["TABLERO"]; d = cls.normalizar(self.proyecto.formatos.get("TABLERO") or cls.vacio()); filas = d["tablas"]["kpi"]
        if not isinstance(i, int) or not 0 <= i < len(filas): return {"error": "El indicador ya no existe."}
        f = filas[i]; revs = IND.revisiones(self.proyecto, f.get("kpi_id") or "") if f.get("kpi_id") else []
        return {"nombre": f.get("indicador") or "", "unidad": f.get("unidad") or "", "revisiones": revs, "campos": IND.ETIQUETAS,
                "vigente": revs[-1] if revs else None}

    def guardar_definicion_indicador(self, i, campos, vigencia, motivo=""):
        """A2: guarda la definición del indicador. Si cambió, crea una revisión nueva (la anterior queda intacta)."""
        cls = self.registro["TABLERO"]; d = cls.normalizar(self.proyecto.formatos.get("TABLERO") or cls.vacio()); filas = d["tablas"]["kpi"]
        if not isinstance(i, int) or not 0 <= i < len(filas): return self._resp("El indicador ya no existe.", "aviso", error="kpi", hoja=False)
        kid = filas[i].get("kpi_id") or IND.nuevo_id()
        estado, msg = IND.guardar_definicion(self.proyecto, kid, campos, vigencia, motivo)
        if estado == "error": return self._resp(msg, "aviso", error="definicion", hoja=False)
        if estado == "nueva":
            filas[i]["kpi_id"] = kid
            if (campos.get("nombre") or "").strip(): filas[i]["indicador"] = campos["nombre"].strip()
            self.proyecto.formatos["TABLERO"] = cls.normalizar(d)
            self._sucio = True
        r = self._resp(msg, hoja=False); r["tablero"] = self.datos_tablero(); return r

    def tablero_kpi(self, accion, datos=None):
        """Cambios hechos desde la vista del tablero: agregar o quitar un indicador, fijar meta y advertencia, mostrar en el resumen."""
        from .modulos import kpis
        datos = datos or {}; cls = self.registro["TABLERO"]; d = cls.normalizar(self.proyecto.formatos.get("TABLERO") or cls.vacio()); filas = d["tablas"]["kpi"]
        if accion == "agregar":
            k = next((x for x in kpis.catalogo() if x["id"] == datos.get("kpi_id")), None)
            if k is None: return self._resp("Ese indicador no está en el catálogo.", "aviso", error="kpi", hoja=False)
            if any(f.get("kpi_id") == k["id"] for f in filas): return self._resp(f"{k['nombre']} ya está en el tablero.", hoja=False)
            nueva = {"kpi_id": k["id"], "categoria": k["categoria"], "indicador": k["nombre"], "unidad": k["unidad"], "sentido": k["sentido"], "tarjeta": "Sí"}
            vacia = next((j for j, f in enumerate(filas) if not any(v for kk, v in f.items())), None)
            if vacia is None: filas.append(nueva)
            else: filas[vacia] = nueva
            msg = f"{k['nombre']} agregado al tablero."
        elif accion in ("quitar", "meta", "resumen"):
            i = datos.get("i")
            if not isinstance(i, int) or not 0 <= i < len(filas): return self._resp("El indicador ya no existe.", "aviso", error="kpi", hoja=False)
            if accion == "quitar": msg = f"{filas[i].get('indicador') or 'Indicador'} quitado del tablero."; filas.pop(i)
            elif accion == "meta":
                filas[i]["meta"] = str(datos.get("meta") or "").strip(); filas[i]["advertencia"] = str(datos.get("adv") or "").strip()
                if "tipo" in datos: filas[i]["tipo_ind"] = datos["tipo"] if datos["tipo"] in ("", "Adelantado", "Atrasado") else ""
                if "explicacion" in datos: filas[i]["explicacion"] = str(datos["explicacion"] or "").strip()
                msg = "Indicador actualizado."
            else: filas[i]["tarjeta"] = "Sí" if datos.get("valor") else "No"; msg = None
        else:
            return self._resp("Acción no válida.", "aviso", error="kpi", hoja=False)
        self.proyecto.formatos["TABLERO"] = cls.normalizar(d); self._sucio = True
        r = self._resp(msg, hoja=False); r["tablero"] = self.datos_tablero(); return r

    # --- formatos (cabecera + tablas) ---
    def _fijos(self):
        return {k: v["valor"] for k, v in self.proyecto.fijos.items()}

    def abrir_formato(self, fid):
        from .modulos.formatos import FORMATOS
        cls = FORMATOS[fid]
        datos = cls.normalizar(self.proyecto.formatos.get(fid, {}))
        return {"espec": cls.espec(self.hoja), "datos": datos, "calc": self._calc(cls, datos), "fijos": self._fijos()}

    def _calc(self, cls, datos):
        c = cls.calcular(datos, self.hoja, self.proyecto)
        c.pop("png", None)          # la imagen solo se usa al exportar; no viaja a la interfaz
        self._marcar_pendientes(cls, datos, c)
        return c

    @staticmethod
    def _marcar_pendientes(cls, datos, c):
        """A1: un campo numérico vacío en un renglón con datos es «pendiente» (no es cero): se marca y se avisa una vez por tabla."""
        for t in getattr(cls, "TABLAS", []):
            cols = [x["campo"] for x in t["columnas"] if x.get("tipo") == "numero" and not x.get("calc") and not x.get("lectura")]
            if not cols: continue
            filas = (datos.get("tablas") or {}).get(t["id"]) or []
            clases = c.setdefault("clases", {}).setdefault(t["id"], [])
            while len(clases) < len(filas): clases.append({})
            n = 0
            for i, f in enumerate(filas):
                llenos = [k for k, v in f.items() if v not in (None, "")]
                if not llenos: continue
                for k in cols:
                    if f.get(k) in (None, ""):
                        clases[i] = clases[i] or {}
                        clases[i].setdefault(k, "pendiente"); n += 1
            if n: c.setdefault("avisos", []).append(f"{t.get('titulo') or t['id']}: {n} campos numéricos vacíos quedan como «pendiente»; no se cuentan como cero.")

    def guardar_formato(self, fid, datos):
        from .modulos.formatos import FORMATOS
        cls = FORMATOS[fid]
        datos = cls.normalizar(datos)
        nuevo = fid not in self.proyecto.formatos
        self.proyecto.formatos[fid] = datos
        avance = self._auto_avance(fid)
        r = self._resp(f"{cls.TITULO}: formato iniciado en el proyecto." if nuevo else None, proyecto=avance, hoja=False)
        r.update(datos=datos, calc=self._calc(cls, datos))
        return r

    def exportar_formato(self, fid, ruta=None):
        from .modulos.formatos import FORMATOS
        from .modulos.exportar import reporte_formato
        cls = FORMATOS[fid]
        datos = cls.normalizar(self.proyecto.formatos.get(fid, {}))
        ruta = ruta or self._elegir("guardar", ["Libro de Excel (*.xlsx)"], cls.TITULO.split(" (")[0] + ".xlsx")
        if not ruta: return self._resp("Exportación cancelada.")
        if not ruta.lower().endswith(".xlsx"): ruta += ".xlsx"
        try:
            reporte_formato(ruta, cls, datos, cls.calcular(datos, self.hoja, self.proyecto), self.proyecto, self.hoja)
        except OSError as e:
            return self._resp(f"No se pudo exportar: {e}", "aviso", error="exportar")
        return self._resp(f"{cls.TITULO} exportado a {ruta}.")

    def catalogo_kpis(self):
        from .modulos.kpis import catalogo
        return catalogo()

    def exportar_powerbi(self, carpeta=None):
        from .nucleo import powerbi
        carpeta = carpeta or self._elegir("carpeta", [])
        if not carpeta: return self._resp("Exportación para Power BI cancelada.")
        try:
            destino, escritos = powerbi.exportar(carpeta, self)
        except OSError as e:
            return self._resp(f"No se pudo exportar para Power BI: {e}", "aviso", error="exportar")
        return self._resp(f"Datos para Power BI exportados en {destino} ({len(escritos)} tablas, tema y guía LEEME.txt).")

    # --- importar, deshacer y rehacer (E2) ---
    def importar(self, ruta=None):
        """Importa CSV, TSV, TXT o XLSX. Si la hoja tiene datos, las columnas nuevas se agregan a la derecha."""
        from .nucleo import importar as imp
        ruta = ruta or self._elegir("abrir", ["Datos (*.csv;*.tsv;*.txt;*.xlsx)", "Todos los archivos (*.*)"])
        if not ruta: return self._resp("Importación cancelada.")
        try:
            filas, fmt = imp.leer(ruta)
        except (OSError, ValueError) as e:
            return self._resp(f"No se pudo importar: {e}. La hoja no cambió.", "aviso", error="importar")
        col0 = len(self.hoja.columnas)
        self.hoja.pegar(-1, col0, "\n".join("\t".join(f) for f in filas))
        donde = "en una hoja vacía" if col0 == 0 else f"a la derecha de los datos, desde C{col0 + 1}"
        return self._resp(f"Importadas {len(filas) - 1} filas y {len(filas[0])} columnas de {os.path.basename(ruta)} ({fmt}), {donde}.")

    def deshacer(self):
        if not self._deshacer: return self._resp("No hay cambios de la hoja para deshacer.")
        self._rehacer.append(self.hoja.instantanea())
        self.hoja.restaurar(self._deshacer.pop()); self._sucio = True
        return self._resp("Cambio deshecho.")

    def rehacer(self):
        if not self._rehacer: return self._resp("No hay cambios para rehacer.")
        self._deshacer.append(self.hoja.instantanea())
        self.hoja.restaurar(self._rehacer.pop()); self._sucio = True
        return self._resp("Cambio rehecho.")

    # --- otras acciones de menú ---
    def accion(self, nombre):
        if nombre == "acerca_de":
            return self.sesion.registrar(f"D-MIKE {VERSION}. Motor local sin conexión para proyectos DMAIC.")
        if nombre == "salir" and self._ventana:
            self._ventana.destroy()
            return None
        return self.sesion.registrar(f"Acción no disponible todavía: {nombre}", "aviso")


_HOJA = ("editar", "pegar", "renombrar", "cambiar_tipo", "insertar_columna", "eliminar_columna", "insertar_fila", "eliminar_fila",
         "borrar_rango", "llenar_con", "rellenar", "insertar_filas", "eliminar_filas", "eliminar_columnas", "filtrar", "importar", "abrir_perfil",
         "ejecutar_modulo", "importar_respuestas")
_MUTAN = set(_HOJA) | {"reproducir_resultado", "guardar_estilo_grafica", "fijar_datos", "marcar_avance", "activar_modulo", "desactivar_modulo", "guardar_formato", "borrar_resultado", "tablero_kpi", "registrar_version_diseno", "confirmar_respuestas_diseno", "declarar_limites_diseno", "omitir_paso_doe", "registrar_plan_confirmacion", "registrar_observados_confirmacion"}


def _con_deshacer(f, cambia_hoja):
    """Antes de un cambio de la hoja guarda una instantánea (hasta 50 pasos); marca el proyecto como modificado."""
    import functools

    @functools.wraps(f)
    def envoltura(self, *a, **k):
        antes = self.hoja.instantanea() if cambia_hoja else None
        r = f(self, *a, **k)
        if cambia_hoja and self.hoja.instantanea() != antes:
            self._deshacer.append(antes); del self._deshacer[:-50]; self._rehacer.clear(); self._sucio = True
        elif f.__name__ in _MUTAN and not (isinstance(r, dict) and r.get("error")): self._sucio = True
        if isinstance(r, dict) and "archivo" in r: r["archivo"] = self._archivo()          # el indicador debe reflejar el cambio recién hecho
        return r
    return envoltura


for _m in _MUTAN:
    setattr(Api, _m, _con_deshacer(getattr(Api, _m), _m in _HOJA))
