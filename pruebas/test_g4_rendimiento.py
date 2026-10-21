"""G4: rendimientos con regla explícita de primer evento. Rendimiento de un paso = aprobadas en su primera inspección / inspeccionadas por primera vez;
FTY = promedio y RTY = producto de los rendimientos de cada paso; tradicional = salen / entran sin retrabajo; el retrabajo cuenta como no correcto a la primera; sin primer evento identificable el resultado es
«no calculable» con su motivo. Verificación: cálculo a mano (16_GB DES-RENDIMIENTO no trae ejemplo numérico de RTY). Datos SINTÉTICOS."""
import math
from app.api import Api


def corre(texto, **p):
    a = Api(); a.pegar(-1, 0, texto)
    cols = {"unidad": 0, "paso": 1, "resultado": 2, "intento": 3}
    r = a.ejecutar_modulo("RENDIMIENTO", {**cols, **p})
    return r


def pasos(r): return {q["paso"]: q for q in r["resultado"]["datos"]["pasos"]}


def eventos_a_mano():
    """Revisión: 10 unidades, 8 pasan a la primera y 2 fallan y pasan en el intento 2 (FPY 0.8, final 100%).
    Liberación: 10 unidades, 9 pasan a la primera y 1 falla y pasa en el intento 2 (FPY 0.9). RTY = 0.8 × 0.9 = 0.72."""
    f = ["unidad\tpaso\tresultado\tintento"]
    for u in range(1, 11):
        if u <= 8: f.append(f"U{u}\tRevisión\tAprobado\t1")
        else: f += [f"U{u}\tRevisión\tRechazado\t1", f"U{u}\tRevisión\tAprobado\t2"]
        if u <= 9: f.append(f"U{u}\tLiberación\tAprobado\t1")
        else: f += [f"U{u}\tLiberación\tRechazado\t1", f"U{u}\tLiberación\tAprobado\t2"]
    return "\n".join(f)


def test_rendimiento_y_rty_a_mano_con_retrabajo_como_no_correcto():
    r = corre(eventos_a_mano())
    assert r["error"] is None
    d = r["resultado"]["datos"]; q = pasos(r)
    assert (q["Revisión"]["n"], q["Revisión"]["aprobadas"]) == (10, 8) and math.isclose(q["Revisión"]["rendimiento"], 0.8)
    assert (q["Liberación"]["n"], q["Liberación"]["aprobadas"]) == (10, 9) and math.isclose(q["Liberación"]["rendimiento"], 0.9)
    assert math.isclose(d["rty"], 0.72)                                  # no 100%: el retrabajo no cuenta como correcto a la primera
    tabla = next(b for b in r["resultado"]["bloques"] if b.get("titulo", "").startswith("Rendimiento de cada paso"))
    assert tabla["filas"][0][:3] == ["Revisión", "10", "8"] and tabla["filas"][0][5] == "10" and tabla["filas"][0][4] == "2"   # 10 aprobadas al final
    assert "RTY 72.00%" in " ".join(b.get("texto", "") for b in r["resultado"]["bloques"])


def test_un_solo_paso_rty_igual_rendimiento():
    r = corre("unidad\tpaso\tresultado\tintento\nA\t\tOK\t1\nB\t\tOK\t1\nC\t\tFalla\t1\nD\t\tOK\t1", paso=None)
    assert r["error"] is None and math.isclose(r["resultado"]["datos"]["rty"], 0.75) and "Único" in pasos(r)


def test_sin_intento_ni_fecha_no_calculable_con_motivo():
    r = corre("unidad\tpaso\tresultado\nA\tP1\tAprobado\nB\tP1\tAprobado\nA\tP1\tAprobado", intento=None)
    d = r["resultado"]["datos"]
    assert d["rty"] is None and d["pasos"][0]["estado"] == "no_calculable" and "primera inspección" in d["pasos"][0]["motivo"]
    assert "RTY no calculable" in " ".join(b.get("texto", "") for b in r["resultado"]["bloques"])
    assert d["pasos"][0]["rendimiento"] is None                                  # nunca un valor aproximado


def test_primer_evento_ausente_o_duplicado_es_no_calculable():
    falta = corre("unidad\tpaso\tresultado\tintento\nA\tP1\tAprobado\t2\nB\tP1\tAprobado\t1")      # A no tiene intento 1
    assert pasos(falta)["P1"]["estado"] == "no_calculable" and "falta la primera inspección" in pasos(falta)["P1"]["motivo"] and "A:" in pasos(falta)["P1"]["motivo"]
    dup = corre("unidad\tpaso\tresultado\tintento\nA\tP1\tAprobado\t1\nA\tP1\tRechazado\t1\nB\tP1\tAprobado\t1")
    assert "más de un evento con intento 1" in pasos(dup)["P1"]["motivo"]
    mezcla = corre("unidad\tpaso\tresultado\tintento\nA\tP1\tAprobado\t1\nB\tP1\tAprobado\t1\nA\tP2\tAprobado\t1\nB\tP2\tAprobado\t3")
    d = mezcla["resultado"]["datos"]                                      # un paso calculable y otro no: no hay RTY
    assert pasos(mezcla)["P1"]["estado"] == "ok" and pasos(mezcla)["P2"]["estado"] == "no_calculable" and d["rty"] is None
    assert "P2" in " ".join(b.get("texto", "") for b in mezcla["resultado"]["bloques"] if b.get("clase") == "conclusion")


def test_orden_por_fecha_y_empate_con_resultados_distintos():
    ok = corre("unidad\tpaso\tresultado\tfecha\nA\tP1\tAprobado\t03/06/2026\nA\tP1\tRechazado\t01/06/2026\nB\tP1\tAprobado\t02/06/2026", intento=None, fecha=3)
    assert math.isclose(pasos(ok)["P1"]["rendimiento"], 0.5)                       # el primer evento de A fue el rechazo del 01/06
    empate = corre("unidad\tpaso\tresultado\tfecha\nA\tP1\tAprobado\t01/06/2026\nA\tP1\tRechazado\t01/06/2026", intento=None, fecha=3)
    assert pasos(empate)["P1"]["estado"] == "no_calculable" and "no se sabe cuál fue el primero" in pasos(empate)["P1"]["motivo"]
    mismo = corre("unidad\tpaso\tresultado\tfecha\nA\tP1\tAprobado\t01/06/2026\nA\tP1\tAprobado\t01/06/2026", intento=None, fecha=3)
    assert pasos(mismo)["P1"]["estado"] == "ok"                            # empate con el mismo resultado: no cambia el FPY


def test_declaracion_de_primera_inspeccion():
    t = "unidad\tpaso\tresultado\nA\tP1\tAprobado\nB\tP1\tRechazado"
    assert pasos(corre(t, intento=None, declaro=True))["P1"]["rendimiento"] == 0.5
    assert pasos(corre(t, intento=None, declaro=False))["P1"]["estado"] == "no_calculable"
    dup = "unidad\tpaso\tresultado\nA\tP1\tAprobado\nA\tP1\tRechazado"
    assert pasos(corre(dup, intento=None, declaro=True))["P1"]["estado"] == "no_calculable"        # la declaración no tapa duplicados


def test_denominador_cero_y_estados_de_datos():
    r = corre("unidad\tpaso\tresultado\tintento\nA\tP1\tN/A\t1\nB\tP1\tN/A\t1")
    assert pasos(r)["P1"]["estado"] == "no_definido" and r["resultado"]["datos"]["rty"] is None
    r = corre("unidad\tpaso\tresultado\tintento\nA\tP1\tAprobado\t1\nB\tP1\t\t1\nC\tP1\tN/A\t1\nD\tP1\tRechazado\t1\nE\tP1\tpendiente\t1")
    q = pasos(r)["P1"]
    assert (q["n"], q["aprobadas"]) == (2, 1)                              # solo A y D: el vacío, N/A y el texto sin clasificar quedan fuera
    av = " ".join(r["resultado"]["avisos"])
    assert "Sin datos" in av and "N/A" in av and "«pendiente»" in av


def test_listas_en_conflicto_y_columna_faltante():
    a = Api(); a.pegar(-1, 0, "unidad\tpaso\tresultado\tintento\nA\tP\tOK\t1\nB\tP\tOK\t1")
    assert a.ejecutar_modulo("RENDIMIENTO", {"unidad": 0, "resultado": 2, "intento": 3, "aprobado": "OK", "rechazo": "ok"})["error"] == "entrada"
    assert a.ejecutar_modulo("RENDIMIENTO", {"unidad": 0, "intento": 3})["error"] == "entrada"


def test_reproduce_con_la_misma_cifra():
    a = Api(); a.pegar(-1, 0, eventos_a_mano())
    r = a.ejecutar_modulo("RENDIMIENTO", {"unidad": 0, "paso": 1, "resultado": 2, "intento": 3})["resultado"]
    a.hoja.editar(1, 2, "Rechazado")
    rep = a.reproducir_resultado(r["uid"])["resultado"]
    assert math.isclose(rep["datos"]["rty"], 0.72) and a.estado_resultado(r["uid"])["estado"] == "desactualizado"


# ---------- los tres rendimientos de 16_GB DES-RENDIMIENTO ----------
def test_tres_rendimientos_a_mano():
    r = corre(eventos_a_mano())["resultado"]; d = r["datos"]
    # pasos 0.8 y 0.9: FTY = promedio = 0.85; RTY = producto = 0.72; tradicional = 10 salen de 10 que entran (el retrabajo no se ve)
    assert math.isclose(d["fty"], 0.85) and math.isclose(d["rty"], 0.72)
    assert d["tradicional"]["entran"] == 10 and d["tradicional"]["salen"] == 10 and math.isclose(d["tradicional"]["valor"], 1.0)
    tabla = next(b for b in r["bloques"] if b.get("titulo") == "Rendimientos del proceso")
    assert [f[0].split(" (")[0] for f in tabla["filas"]] == ["Rendimiento tradicional", "FTY", "RTY"] and [f[1] for f in tabla["filas"]] == ["100.00%", "85.00%", "72.00%"]
    assert tabla["filas"][0][2] == "10 salen de «Liberación» entre 10 que entran a «Revisión»"


def test_tradicional_cuenta_una_vez_cada_unidad_y_pierde_las_que_no_salen():
    # A pasa; B se rechaza y pasa al intento 2; C se rechaza y no sale; D pasa -> rendimiento del paso 2/4, salen 3 de 4
    t = "unidad\tpaso\tresultado\tintento\nA\tP\tOK\t1\nB\tP\tFalla\t1\nB\tP\tOK\t2\nC\tP\tFalla\t1\nD\tP\tOK\t1"
    d = corre(t)["resultado"]["datos"]
    assert math.isclose(d["pasos"][0]["rendimiento"], 0.5) and math.isclose(d["tradicional"]["valor"], 0.75)
    assert math.isclose(d["fty"], 0.5) and math.isclose(d["rty"], 0.5)                     # un solo paso: FTY = RTY = rendimiento del paso


def test_no_calculable_arrastra_a_fty_rty_y_tradicional_con_motivo():
    r = corre("unidad\tpaso\tresultado\nA\tP1\tOK\nB\tP1\tOK", intento=None)["resultado"]
    d = r["datos"]
    assert d["fty"] is None and d["rty"] is None and d["tradicional"] is None
    tabla = next(b for b in r["bloques"] if b.get("titulo") == "Rendimientos del proceso")
    assert [f[1] for f in tabla["filas"]] == ["no calculable"] * 3 and all("primera inspección" in f[2] or "necesita" in f[2] for f in tabla["filas"])


def test_nota_del_modulo_declara_que_no_hay_ejemplo_del_curso():
    r = corre(eventos_a_mano())["resultado"]
    nota = " ".join(b["texto"] for b in r["bloques"] if b["tipo"] == "texto" and b["clase"] == "nota")
    assert "DES-RENDIMIENTO" in nota and "Sin ejemplo del curso; verificado con cálculo a mano" in nota
    assert r["titulo"].startswith("Rendimientos de") and "FPY" not in " ".join(str(b) for b in r["bloques"])


# ---------- «salen» cuenta las unidades que terminan el proceso, también después del retrabajo ----------
def test_salen_incluye_las_unidades_que_terminan_tras_el_retrabajo():
    base = eventos_a_mano()
    d = corre(base)["resultado"]["datos"]["tradicional"]
    assert (d["entran"], d["salen"]) == (10, 10)          # U9 y U10 se retrabajaron en Revisión y U10 también en Liberación: aun así salen
    # si U10 nunca logra pasar Liberación (se queda en el rechazo del intento 1), ya no sale: 9 de 10; el RTY no cambia
    sin = "\n".join(l for l in base.splitlines() if l != "U10\tLiberación\tAprobado\t2")
    r = corre(sin)["resultado"]["datos"]
    assert (r["tradicional"]["entran"], r["tradicional"]["salen"]) == (10, 9) and math.isclose(r["tradicional"]["valor"], 0.9)
    assert math.isclose(r["rty"], 0.72)


def test_una_unidad_que_no_entro_no_cuenta_como_salida():
    t = "unidad\tpaso\tresultado\tintento\nA\tP1\tOK\t1\nB\tP1\tOK\t1\nA\tP2\tOK\t1\nB\tP2\tOK\t1\nZ\tP2\tOK\t1"        # Z solo aparece en P2
    r = corre(t)["resultado"]
    assert r["datos"]["tradicional"]["salen"] == 2 and r["datos"]["tradicional"]["entran"] == 2 and r["datos"]["tradicional"]["valor"] == 1.0
    assert any("no cuentan como salidas" in a for a in r["avisos"])


def test_la_nota_dice_que_el_orden_de_los_pasos_es_decision_de_d_mike():
    r = corre(eventos_a_mano())["resultado"]
    nota = " ".join(b["texto"] for b in r["bloques"] if b["tipo"] == "texto" and b["clase"] == "nota")
    assert "Orden de los pasos: el de la hoja; esa regla es una decisión de D-MIKE, no del curso (no respaldado)" in nota
