"""G7: nota visible sobre no comparar desempeño individual sin normalizar (solo texto; no bloquea el cálculo)."""
from app.api import Api
from app.modulos.base import NOTA_PERSONA, es_columna_persona

DATOS = "defecto\tAnalista\tminutos\n" + "\n".join(f"{['A','B','C'][i % 3]}\t{['Ana','Beto'][i % 2]}\t{10 + i % 7}" for i in range(30))


def textos(r): return [b.get("texto") for b in r["resultado"]["bloques"] if b["tipo"] == "texto"]


def test_pareto_siempre_lleva_la_nota():
    a = Api(); a.pegar(-1, 0, DATOS)
    r = a.ejecutar_modulo("PARETO", {"cat": 0})
    assert r["error"] is None and NOTA_PERSONA in textos(r)


def test_analisis_por_columna_de_personas_lleva_la_nota_y_no_bloquea():
    a = Api(); a.pegar(-1, 0, DATOS)
    r = a.ejecutar_modulo("BOXPLOT", {"y": 2, "grupo": 1})
    assert r["error"] is None and NOTA_PERSONA in textos(r)
    r2 = a.ejecutar_modulo("BOXPLOT", {"y": 2, "grupo": 0})          # grupo = defecto: sin nota
    assert r2["error"] is None and NOTA_PERSONA not in textos(r2)


def test_reproducir_conserva_la_nota():
    a = Api(); a.pegar(-1, 0, DATOS)
    r = a.ejecutar_modulo("PARETO", {"cat": 0})
    rep = a.reproducir_resultado(r["resultado"]["uid"])
    assert NOTA_PERSONA in textos(rep)


def test_deteccion_de_nombres():
    assert es_columna_persona("Analista") and es_columna_persona("Técnico asignado") and es_columna_persona("OPERADOR")
    assert not es_columna_persona("Tipo de defecto") and not es_columna_persona("Línea")
