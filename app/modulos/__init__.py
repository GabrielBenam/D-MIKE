"""Módulos del MVP. Cada uno define: entrada (parámetros sobre columnas de la hoja o formulario), validación,
cálculo o gráfico, plantilla propia (resultado) y exportación."""
REGISTRO = {}


def registrar(cls):
    REGISTRO[cls.ID] = cls
    return cls


def autoprueba():
    """Llamada por main --prueba: corre cada módulo con datos sintéticos mínimos (verifica matplotlib, scipy y la fuente)."""
    from ..api import Api
    a = Api()
    a.pegar(-1, 0, "y\tg\tb\tcat\tx\n" + "\n".join(f"{10 + (i * 7) % 5 + (i % 2) * 3}\t{'AB'[i % 2]}\t{'XY'[(i // 2) % 2]}\t{'PQR'[i % 3]}\t{i + (i * 3) % 4}"
                                                  for i in range(24)))
    for mid, p in (("ESTADISTICOS", {"y": 0}), ("CORRIDA", {"y": 0}), ("BOXPLOT", {"y": 0, "grupo": 1}),
                   ("ANOVA", {"y": 0, "factor": 1, "bloque": 2, "alfa": "0.05"}), ("PARETO", {"cat": 3, "otros": "95"}),
                   ("DISTRIB", {"y": 0, "lie": "8", "lse": "20"}), ("SPC", {"tipo": "xr", "y": 0, "tam": "4", "pruebas": ["1"]}),
                   ("CAPACIDAD", {"y": 0, "tam": "4", "lie": "8", "lse": "20"}), ("CORREL", {"vars": [0, 4]}), ("REGRESION", {"y": 0, "xs": [4]})):
        r = a.ejecutar_modulo(mid, p)
        if r["error"]: raise RuntimeError(f"{mid}: {r['sesion'][0]['texto']}")
    d = a.ejecutar_modulo("DISENO-RSM", {"tipo": "ccd", "nombres": "A, B", "bajos": "1, 10", "altos": "3, 20", "semilla": "1"})
    if d["error"]: raise RuntimeError("DISENO-RSM: " + d["sesion"][0]["texto"])
    info = d["resultado"]["datos"]["diseno"]          # nombres reales (pueden cambiar si ya existían columnas iguales)
    yj = a.hoja.indice(info["respuesta"]); ja, jb = (a.hoja.indice(f["nombre"]) for f in info["factores"])
    for i in range(a.hoja.n):
        va, vb = a.hoja.columnas[ja].valor(i)[2], a.hoja.columnas[jb].valor(i)[2]
        if va is not None: a.hoja.editar(i, yj, str(round(50 - (va - 2) ** 2 - 0.01 * (vb - 15) ** 2 + 0.1 * (i % 3), 4)))
    r = a.ejecutar_modulo("RSM", {"y": yj, "xs": [ja, jb], "modelo": "cuadratico"})
    if r["error"]: raise RuntimeError("RSM: " + r["sesion"][0]["texto"])
    o = a.ejecutar_modulo("OPTIMIZADOR", {"r1": r["resultado"]["uid"], "meta1": "max", "inf1": "40", "obj1": "50"})
    if o["error"]: raise RuntimeError("OPTIMIZADOR: " + o["sesion"][0]["texto"])
    from .formatos import FORMATOS
    for fid in FORMATOS:
        a.guardar_formato(fid, a.abrir_formato(fid)["datos"])


def cargar():
    """Importa los módulos para que se registren."""
    from . import graficas_basicas, analisis, formatos, formatos2, formatos3, formatos4, formatos5, formatos6, formatos7, calidad, relaciones, superficies, datos_hoja, calc_hoja, msa_variable, inferencia, probabilidad, factorial, formatos8  # noqa: F401
    return REGISTRO
