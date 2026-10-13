"""Catálogo de módulos, leído del árbol de diagnóstico (arbol_diagnostico.json)."""
import json
from .rutas import recurso

FASES = [("D", "Definir"), ("M", "Medir"), ("A", "Analizar"), ("I", "Mejorar"), ("C", "Controlar")]

# Catálogo MVP confirmado por el usuario (30/09/2026)
MVP = ["HOJA-DATOS", "CORRIDA", "DISTRIB", "BOXPLOT", "PARETO",
       "ANOVA", "MSA-ATR", "AMEF", "PLAN-CONTROL", "TABLERO"]
# Agregados en v0.10 con autonomía dada por el usuario (01/10/2026)
EXTRA = ["OEE", "TAKT", "KANBAN", "CHARTER", "SIPOC", "ISHIKAWA", "CINCO-PQ", "SMED", "GANTT", "CUATRO-Q", "A3", "KAIZEN", "TARJETAS", "MUDAS", "KATA", "KANO", "QFD", "CTQ-TREE", "VSM", "TIEMPOS", "BALANCE", "TPM", "POKAYOKE", "CINCO-S", "GEMBA", "SCRUM", "LSW", "TRABAJO-EST", "DEF-PROBLEMA", "HOSHIN", "PMAPA", "TOC", "ESPAGUETI", "FINANZAS", "MUESTREO", "DESEMPENO", "CHECKLIST-FASE", "VISUAL", "FLUJO", "INTERESADOS", "RIESGOS", "LECCIONES"]
# Etapa motor estadístico (ETAPA_MOTOR_ESTADISTICO.md, E3, E4 y E6)
ESTADISTICA = ["SPC", "CAPACIDAD", "CORREL", "REGRESION", "RSM", "MSA-VAR"]
# Módulos de D-MIKE que no están en el árbol de diagnóstico (herramientas complementarias). Se muestran en el panel DMAIC para
# poder abrirlos o activarlos. La fase asignada es un criterio de uso de D-MIKE, no del árbol [GENERAL].
COMPLEMENTARIOS = {
    "ESTADISTICOS": ("Estadísticos de columna", "M", "datos"), "PROBABILIDAD": ("Distribuciones de probabilidad", "M", "datos"),
    "DIST-ID": ("Identificación de distribución", "M", "datos"), "BOXCOX": ("Transformación Box-Cox", "M", "datos"),
    "POTENCIA": ("Potencia y tamaño de muestra", "M", "datos"), "HIPOTESIS": ("Pruebas de hipótesis", "A", "datos"),
    "NOPARAM": ("Pruebas no paramétricas", "A", "datos"), "CHI2": ("Tabla cruzada y chi cuadrada", "A", "datos"),
    "ANOVA2": ("ANOVA de dos factores", "A", "datos"), "TUKEY": ("Comparaciones de Tukey", "A", "datos"),
    "AFINIDAD": ("Diagrama de afinidad", "A", "formato"), "COSTO-CALIDAD": ("Costo de calidad", "A", "formato"),
    "DISENO-RSM": ("Crear diseño de experimentos", "I", "datos"), "FACTORIAL": ("Analizar diseño factorial", "I", "datos"),
    "OPTIMIZADOR": ("Optimizador de respuestas", "I", "datos"), "ARBOL-DECISION": ("Árbol de decisión", "I", "formato"),
    "ENFOQUE": ("Enfoque de desarrollo", "D", "formato"), "JUSTIFICACION": ("Justificación de negocio", "D", "formato"),
    "RACI": ("Matriz de responsabilidades (RACI)", "D", "formato"), "EDT": ("EDT y diccionario", "D", "formato"),
    "CRONOGRAMA": ("Cronograma y ruta crítica", "D", "formato"), "MONTECARLO": ("Monte Carlo del cronograma", "D", "formato"),
    "FODA": ("Análisis FODA", "D", "formato"), "BITACORA": ("Bitácora del proyecto", "D", "formato"),
    "VALOR-GANADO": ("Seguimiento por valor ganado", "C", "formato"),
}
CONSTRUIDOS = set(MVP + EXTRA + ESTADISTICA) | set(COMPLEMENTARIOS)


class Catalogo:
    def __init__(self, ruta=None):
        ruta = ruta or recurso("datos", "arbol_diagnostico.json")
        with open(ruta, encoding="utf-8") as f:
            self.arbol = json.load(f)
        self.version = self.arbol["version"]
        self.modulos = {m["id"]: m for m in self.arbol["catalogo"]}
        self.complementarios = {k: {"id": k, "nombre": n, "fases": [f], "tipo": t, "datos_minimos": "", "complementario": True}
                                for k, (n, f, t) in COMPLEMENTARIOS.items() if k not in self.modulos}

    def info(self, mid):
        """Datos de un módulo del árbol o complementario (None si no existe)."""
        return self.modulos.get(mid) or self.complementarios.get(mid)

    def por_fase(self):
        """Módulos disponibles por fase; un módulo aparece en cada fase que le corresponde."""
        salida = {f: [] for f, _ in FASES}
        for m in list(self.arbol["catalogo"]) + list(self.complementarios.values()):
            for f in m["fases"]:
                salida[f].append({"id": m["id"], "nombre": m["nombre"], "tipo": m["tipo"], "construido": m["id"] in CONSTRUIDOS,
                                  "complementario": bool(m.get("complementario"))})
        for f in salida:
            salida[f].sort(key=lambda x: (not x["construido"], x["nombre"]))
        return salida
