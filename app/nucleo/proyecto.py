"""Proyecto abierto: perfil vigente, datos fijos, módulos activos con su avance y resultados capturados.

Reglas de fusión (ESTADO_D-MIKE.md, Decisiones): validar sin tocar nada; solo se acepta una versión mayor;
se conservan avance y capturas; los datos fijos del perfil solo llenan vacíos; las columnas sugeridas
se crean si no existen y nunca se borran.
"""
from .perfil import CAMPOS_FIJOS, ETIQUETA_FIJO, PRIORIDADES

AVANCES = ("pendiente", "en_curso", "hecho")


class FusionRechazada(Exception):
    pass


class Proyecto:
    def __init__(self):
        self.perfil = None
        self.version = 0
        self.fijos = {k: {"valor": None, "origen": None} for k in CAMPOS_FIJOS}
        self.modulos = {}          # id -> dict
        self.resultados = []       # capturas de módulos (se guardan en el .dmike)
        self.historial = []        # versiones de perfil incorporadas
        self.formatos = {}         # ID de formato -> datos capturados

    # ---------- perfil ----------
    def aplicar_perfil(self, p, hoja):
        """Incorpora un perfil ya validado. Devuelve mensajes para la sesión. No borra nada."""
        if self.version and p["version"] <= self.version:
            raise FusionRechazada(f"El perfil es la versión {p['version']} y el proyecto ya tiene la versión "
                                  f"{self.version}; solo se incorpora una versión mayor. No se cambió nada.")
        msgs, fusion = [], bool(self.version)

        # datos fijos: solo llenan vacíos
        conservados = 0
        for k in CAMPOS_FIJOS:
            nuevo, actual = p["datos_fijos"].get(k), self.fijos[k]
            if nuevo is None: continue
            if actual["valor"] in (None, ""): self.fijos[k] = {"valor": nuevo, "origen": "perfil"}
            elif actual["valor"] != nuevo: conservados += 1
        if conservados:
            msgs.append((f"Se conservaron {conservados} datos fijos que ya tenían valor; el perfil solo llena los vacíos.", "info"))

        # módulos: los del perfil nuevo, más los que ya tienen avance o capturas
        con_captura = {r["modulo"] for r in self.resultados} | set(self.formatos)
        previos, self.modulos = self.modulos, {}
        for m in p["modulos"]:
            ant = previos.get(m["id"], {})
            self.modulos[m["id"]] = {**m, "avance": ant.get("avance", "pendiente"), "conservado": False}
        kept = []
        for mid, m in previos.items():
            if mid not in self.modulos and (m["avance"] != "pendiente" or mid in con_captura or m.get("origen") == "usuario"):
                self.modulos[mid] = {**m, "conservado": True}; kept.append(mid)
        if kept:
            msgs.append((f"Se conservan {', '.join(kept)} porque ya tienen avance o capturas, aunque la nueva "
                         "versión no los incluye.", "aviso"))
        if fusion:
            nuevos = [i for i in self.modulos if i not in previos]
            quitados = [i for i in previos if i not in self.modulos]
            if nuevos: msgs.append((f"Módulos nuevos en esta versión: {', '.join(nuevos)}.", "info"))
            if quitados: msgs.append((f"Módulos que esta versión ya no incluye (sin avance ni capturas): "
                                      f"{', '.join(quitados)}.", "info"))

        # columnas sugeridas: se crean si no existen; nunca se borran
        creadas = hoja.agregar_sugeridas(p["columnas"])
        if creadas:
            msgs.append((f"Columnas sugeridas creadas en la hoja: {', '.join(creadas)}.", "info"))
        existentes = len(p["columnas"]) - len(creadas)
        if existentes:
            msgs.append((f"{existentes} columnas sugeridas ya existían y no se modificaron.", "info"))

        self.perfil, self.version = p, p["version"]
        self.historial.append({"version": p["version"], "generado_en": p.get("generado_en")})
        return msgs

    def fijar_dato(self, campo, valor):
        if campo not in self.fijos or campo == "logo": raise ValueError("Campo no válido.")
        valor = (valor or "").strip() or None
        self.fijos[campo] = {"valor": valor, "origen": "usuario" if valor else None}

    def activar_modulo(self, mid, fase, catalogo):
        """El usuario activa un módulo inactivo en una fase (queda marcado como elegido por el usuario)."""
        c = catalogo.info(mid)
        if c is None: raise ValueError("Ese módulo no existe.")
        if fase not in "DMAIC" or len(fase) != 1: raise ValueError("Fase no válida.")
        ant = self.modulos.get(mid, {})
        self.modulos[mid] = {"id": mid, "estado": "activo", "fase": fase, "prioridad": "U", "motivos": ["activado por el usuario"],
                             "datos_minimos": c.get("datos_minimos", ""), "verificar": False, "avance": ant.get("avance", "pendiente"),
                             "conservado": False, "origen": "usuario"}

    def desactivar_modulo(self, mid):
        if mid not in self.modulos: raise ValueError("Ese módulo no está activo.")
        del self.modulos[mid]

    def marcar_avance(self, mid, avance):
        if mid not in self.modulos or avance not in AVANCES: raise ValueError("Módulo o avance no válido.")
        self.modulos[mid]["avance"] = avance

    def fase_actual(self):
        return (self.perfil or {}).get("diagnostico", {}).get("fase_actual")

    # ---------- vista ----------
    def estado(self, catalogo):
        p = self.perfil
        if p is None and not any(v["valor"] for v in self.fijos.values()) and not self.modulos: return None
        p = p or {"perfil_empresa": {}, "sugeridos": [], "no_recomendados": [], "siguiente_paso": None}
        activos = {f: [] for f in "DMAIC"}
        for mid, m in self.modulos.items():
            if m["estado"] != "activo" and not m["conservado"]: continue
            c = catalogo.info(mid)
            if c is None: continue
            activos[m["fase"]].append({"id": mid, "nombre": c["nombre"], "prioridad": m["prioridad"],
                                       "prioridad_texto": PRIORIDADES.get(m["prioridad"], ""),
                                       "avance": m["avance"], "motivos": m["motivos"],
                                       "datos_minimos": m["datos_minimos"], "verificar": m["verificar"],
                                       "conservado": m["conservado"]})
        emp = p["perfil_empresa"]
        return {"version": self.version, "fase_actual": self.fase_actual(), "activos": activos,
                "sugeridos": p["sugeridos"], "no_recomendados": p["no_recomendados"],
                "siguiente_paso": p["siguiente_paso"],
                "fijos": [{"campo": k, "etiqueta": ETIQUETA_FIJO[k], "valor": v["valor"], "origen": v["origen"]}
                          for k, v in self.fijos.items()],
                "empresa": {"tamano": emp.get("tamano"), "giro": emp.get("giro")}}

    # ---------- persistencia ----------
    def a_dict(self):
        return {"perfil": self.perfil, "version": self.version, "fijos": self.fijos, "modulos": self.modulos,
                "resultados": self.resultados, "historial": self.historial,
                "formatos": self.formatos}

    @classmethod
    def de_dict(cls, d):
        pr = cls()
        pr.perfil, pr.version = d.get("perfil"), d.get("version", 0)
        pr.fijos.update(d.get("fijos", {}))
        pr.modulos, pr.resultados, pr.historial = d.get("modulos", {}), d.get("resultados", []), d.get("historial", [])
        pr.formatos = d.get("formatos", {})
        return pr
