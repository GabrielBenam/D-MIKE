"""E3-1 (Decisión 4 de ESPEC_receta_v2, sección 7): Gage R&R de variable (cruzado) avisa cuando la columna de medición corresponde a una variable
declarada como ensayo destructivo. El aviso nunca bloquea; sin variable declarada no avisa. Datos SINTÉTICOS."""
import math
from app.api import Api

# 10 piezas x 2 evaluadores x 2 repeticiones, balanceado
FILAS = ["pieza\tevaluador\tResistencia (MPa)"]
for i in range(1, 11):
    for e, desv in (("A", 0.0), ("B", 0.3)):
        for r in range(2): FILAS.append(f"P{i}\t{e}\t{40 + i * 1.5 + desv + 0.1 * r:.3f}")
DATOS = "\n".join(FILAS)
PARAMS = {"pieza": 0, "evaluador": 1, "y": 2, "tol": "20"}


def api(variables=None):
    a = Api(); a.pegar(-1, 0, DATOS)
    if variables is not None: a.proyecto.formatos["_variables"] = variables
    return a


def var(nombre, destructivo, **k): return {"nombre": nombre, "hoja": "", "unidad": "MPa", "estado_evidencia": "REAL_NO_VALIDADO", "ensayo_destructivo": destructivo, **k}


def correr(a):
    r = a.ejecutar_modulo("MSA-VAR", PARAMS); assert r["error"] is None, r["sesion"][0]["texto"]; return r["resultado"]


def avisa(res): return any("Ensayo destructivo" in x for x in res["avisos"])


def tiene_bloque(res): return any(b["tipo"] == "texto" and b["clase"] == "advertencia" and "Ensayo destructivo" in b["texto"] for b in res["bloques"])


def test_variable_destructiva_avisa_y_no_bloquea():
    res = correr(api([var("Resistencia (MPa)", True)]))
    assert avisa(res) and tiene_bloque(res)
    assert "diseño cruzado" in " ".join(res["avisos"]) and "anidado" in " ".join(res["avisos"]) and "no respaldado por la base" in " ".join(res["avisos"])
    assert res["datos"]["ensayo_destructivo"] == {"variable": "Resistencia (MPa)", "cruzado_aplica": False}
    ancho = {b["titulo"] for b in res["bloques"] if b["tipo"] == "tabla"}
    assert "Componentes de varianza" in ancho                         # el cálculo se hizo completo: el aviso no bloquea


def test_el_calculo_es_identico_con_y_sin_aviso():
    con, sin = correr(api([var("Resistencia (MPa)", True)])), correr(api())
    tabla = lambda r: [b["filas"] for b in r["bloques"] if b["tipo"] == "tabla"]
    assert tabla(con) == tabla(sin)


def test_sin_variable_declarada_no_avisa():
    for variables in (None, [], [var("Otra variable", True)]):
        res = correr(api(variables))
        assert not avisa(res) and not tiene_bloque(res) and "ensayo_destructivo" not in res["datos"]


def test_variable_declarada_no_destructiva_no_avisa():
    assert not avisa(correr(api([var("Resistencia (MPa)", False)])))


def test_emparejamiento_por_nombre_normalizado_y_sin_coincidencias_parciales():
    assert avisa(correr(api([var("  RESISTENCIA   (mpa) ", True)])))                 # mayúsculas, espacios
    assert not avisa(correr(api([var("Resistencia", True)])))                        # parcial: no empareja
    assert not avisa(correr(api([var("Resistencia (MPa) 2", True)])))


def test_con_varias_coincidencias_basta_una_destructiva():
    assert avisa(correr(api([var("Resistencia (MPa)", False), var("resistencia (mpa)", True)])))


def test_reproducir_conserva_el_aviso():
    a = api([var("Resistencia (MPa)", True)]); res = correr(a)
    rep = a.reproducir_resultado(res["uid"])["resultado"]
    assert avisa(rep) and tiene_bloque(rep)


def test_variable_que_viene_de_una_receta_real(tmp_path):
    # el campo ensayo_destructivo viaja en la receta (ESPEC 2.1) y queda en _variables al aplicarla
    from app.nucleo import receta as RC
    a = Api()
    rec = {"tipo": "dmike-receta", "receta_version": 2, "dmike_minimo": "0.26", "modo_proyecto": "real", "id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c10",
           "datos_fijos": {}, "hojas": [], "variables": [{"nombre": "Resistencia (MPa)", "hoja": "", "unidad": "MPa", "unidad_analisis": "probeta",
           "fuente": "ensayo", "responsable": "", "estado_evidencia": "PENDIENTE_RECOLECCION", "ensayo_destructivo": True}]}
    rec["huella"] = RC.huella_receta({k: v for k, v in rec.items() if k != "huella"})
    ruta = tmp_path / "r.json"; ruta.write_text(__import__("json").dumps(rec), encoding="utf-8")
    r = a.ejecutar_receta(str(ruta)); assert r["error"] is None, r["sesion"][0]["texto"]
    assert a.proyecto.formatos["_variables"][0]["ensayo_destructivo"] is True
    a.pegar(-1, 0, DATOS)
    assert avisa(correr(a))
