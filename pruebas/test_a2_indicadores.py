"""A2: indicadores como definiciones versionadas (numerador, denominador, unidad de conteo, población, eventos, vigencia, revisión),
notas de tendencias que cruzan revisiones, todo porcentaje con su base y denominador cero = «no definido». Datos SINTÉTICOS y genéricos."""
import csv, os
from app.api import Api
from app.nucleo import indicadores as IND

DEF1 = {"nombre": "Entregas completas", "numerador": "Entregas con todos los documentos", "denominador": "Entregas recibidas",
        "unidad_conteo": "entrega", "poblacion": "Entregas del periodo", "evento_inicio": "Recepción", "evento_fin": "Cierre"}


def tablero(a, filas, inicio="01/06/2026", semanas="6", col_fecha=""):
    d = a.abrir_formato("TABLERO")["datos"]
    d["cabecera"].update({"semanas": semanas, "inicio": inicio, "col_fecha": col_fecha})
    d["tablas"]["kpi"] = filas
    return a.guardar_formato("TABLERO", d)


def fila(**k): return {"kpi_id": "IND-X", "indicador": "Entregas completas", "unidad": "%", "sentido": ">=", "meta": "90", "tarjeta": "Sí", **k}


def ind(a, i=0): return a.datos_tablero()["indicadores"][i]


# ---------- revisiones ----------
def test_revisiones_se_crean_solo_si_cambia_la_definicion():
    a = Api(); tablero(a, [fila(s1="80")])
    r = a.guardar_definicion_indicador(0, DEF1, "01/06/2026")
    assert r["error"] is None and ind(a)["definicion"]["revision"] == 1
    r = a.guardar_definicion_indicador(0, DEF1, "15/06/2026")
    assert "no cambió" in r["sesion"][0]["texto"] and ind(a)["definicion"]["revision"] == 1
    cambiada = {**DEF1, "denominador": "Entregas recibidas y vencidas"}
    a.guardar_definicion_indicador(0, cambiada, "15/06/2026", "Se incluyen las vencidas")
    revs = ind(a)["definicion"]["revisiones"]
    assert [r["revision"] for r in revs] == [1, 2] and revs[0]["denominador"] == "Entregas recibidas"       # la 1 queda intacta
    assert revs[1]["vigencia"] == "2026-06-15" and revs[1]["motivo"] == "Se incluyen las vencidas"


def test_validaciones_de_la_definicion():
    a = Api(); tablero(a, [fila()])
    assert a.guardar_definicion_indicador(0, {**DEF1, "nombre": ""}, "01/06/2026")["error"] == "definicion"
    assert a.guardar_definicion_indicador(0, {**DEF1, "numerador": ""}, "01/06/2026")["error"] == "definicion"
    assert a.guardar_definicion_indicador(0, DEF1, "mañana")["error"] == "definicion"
    a.guardar_definicion_indicador(0, DEF1, "10/06/2026")
    r = a.guardar_definicion_indicador(0, {**DEF1, "poblacion": "otra"}, "10/06/2026")                    # misma fecha: no es posterior
    assert r["error"] == "definicion" and "posterior" in r["sesion"][0]["texto"]


def test_indicador_manual_sin_id_recibe_uno():
    a = Api(); tablero(a, [{"indicador": "Mío", "unidad": "días", "s1": "3"}])
    a.guardar_definicion_indicador(0, {**DEF1, "nombre": "Mío"}, "01/06/2026")
    assert ind(a)["kpi_id"].startswith("IND-") and ind(a)["definicion"]["revision"] == 1


def test_revision_vigente_por_fecha_y_por_semana():
    from datetime import date
    a = Api(); tablero(a, [fila(s1="80")])
    a.guardar_definicion_indicador(0, DEF1, "01/06/2026"); a.guardar_definicion_indicador(0, {**DEF1, "poblacion": "x"}, "15/06/2026")
    revs = IND.revisiones(a.proyecto, "IND-X")
    assert IND.revision_en(revs, date(2026, 5, 31)) is None and IND.revision_en(revs, date(2026, 6, 14))["revision"] == 1
    assert IND.revision_por_semana(revs, date(2026, 6, 1), 6) == [1, 1, 2, 2, 2, 2]


def test_tendencia_que_cruza_revisiones_lleva_nota_visible():
    a = Api(); tablero(a, [fila(s1="80", s2="82", s3="85", s4="88")])
    a.guardar_definicion_indicador(0, DEF1, "01/06/2026")
    assert ind(a)["definicion"]["nota"] is None                                   # una sola revisión: sin nota
    a.guardar_definicion_indicador(0, {**DEF1, "denominador": "Todas"}, "15/06/2026", "Cambio de denominador")
    nota = ind(a)["definicion"]["nota"]
    assert "cruza las revisiones 1 y 2" in nota and "15/06/2026" in nota and "Cambio de denominador" in nota
    assert nota in a.datos_tablero()["avisos"]                                    # visible en el tablero
    assert any("cruza las revisiones" in x for x in a.abrir_formato("TABLERO")["calc"]["avisos"])      # y en el formato
    # si los valores capturados caen todos en una revisión, no hay cruce
    tablero(a, [fila(s3="85", s4="88")])
    assert ind(a)["definicion"]["nota"] is None


def test_sin_inicio_no_se_puede_ubicar_la_revision():
    a = Api(); tablero(a, [fila(s1="80")], inicio="")
    a.guardar_definicion_indicador(0, DEF1, "01/06/2026"); a.guardar_definicion_indicador(0, {**DEF1, "poblacion": "x"}, "15/06/2026")
    assert "no se puede ubicar" in ind(a)["definicion"]["nota"]


# ---------- base de los porcentajes y denominador cero ----------
def test_fraccion_conserva_su_base():
    a = Api(); tablero(a, [fila(s1="28/30", s2="45", s3="9 de 10")])
    k = ind(a)
    assert round(k["vals"][0], 6) == round(100 * 28 / 30, 6) and k["bases"][0] == "28 de 30" and k["bases"][2] == "9 de 10"
    assert k["bases"][1] == ""                                                    # 45 se capturó sin base
    assert k["base"] == "9 de 10"                                                 # base del último valor
    tablero(a, [fila(s1="28/30", s2="45")])
    assert ind(a)["base"] == "base no registrada"                                 # % sin base: se dice, no se inventa


def test_denominador_cero_es_no_definido_no_cero():
    a = Api(); r = tablero(a, [fila(s1="0/0", s2="5/0", s3="3/4")])
    k = ind(a)
    assert k["vals"][:2] == [None, None] and k["vals"][2] == 75.0
    assert any("denominador 0" in x for x in r["calc"]["avisos"])
    assert k["bases"][0] == "no definido (denominador 0)"


def test_proporcion_desde_la_hoja_con_base_y_sin_cero_por_faltante():
    a = Api()
    filas = ["fecha\tbuenas\ttotal"] + [f"{d:02d}/06/2026\t{b}\t{t}" for d, b, t in [(1, 8, 10), (3, 9, 10), (4, "", 10), (9, 5, 0), (10, 0, 0), (17, 1, 4)]]
    a.pegar(-1, 0, "\n".join(filas))
    tablero(a, [fila(col="buenas", col_den="total", calculo="proporcion")], semanas="3", col_fecha="fecha")
    k = ind(a)
    # semana 1: filas 1, 3 -> 17/20 (la fila 4 tiene la numerador vacío: sin dato, queda fuera); semana 2: 5/0 + 0/0 -> denominador 0; semana 3: 1/4
    assert round(k["vals"][0], 6) == 85.0 and k["bases"][0] == "17 de 20"
    assert k["vals"][1] is None and k["bases"][1] == "no definido (denominador 0)"
    assert k["vals"][2] == 25.0 and k["bases"][2] == "1 de 4"


# ---------- Power BI y archivo ----------
def test_powerbi_trae_definiciones_revision_y_base(tmp_path):
    a = Api(); tablero(a, [fila(s1="28/30", s3="3/4")])
    a.guardar_definicion_indicador(0, DEF1, "01/06/2026"); a.guardar_definicion_indicador(0, {**DEF1, "poblacion": "x"}, "15/06/2026")
    carpeta, _ = __import__("app.nucleo.powerbi", fromlist=["x"]).exportar(str(tmp_path), a)
    leer = lambda n: list(csv.DictReader(open(os.path.join(carpeta, n), encoding="utf-8-sig")))
    assert [r["revision"] for r in leer("definicion_indicador.csv")] == ["1", "2"] and leer("dim_indicador.csv")[0]["revision_vigente"] == "2"
    h = leer("hecho_indicador.csv")
    assert (h[0]["revision"], h[0]["base_numerador"], h[0]["base_denominador"]) == ("1", "28", "30") and h[1]["revision"] == "2"


def test_definiciones_sobreviven_guardar_y_abrir_y_proyecto_viejo_abre(tmp_path):
    a = Api(); tablero(a, [fila(s1="80")]); a.guardar_definicion_indicador(0, DEF1, "01/06/2026")
    ruta = str(tmp_path / "p.dmike"); a._elegir = lambda *x, **k: ruta; a.guardar()
    b = Api(); b.abrir_proyecto(ruta)
    assert ind(b)["definicion"]["revision"] == 1
    c = Api(); tablero(c, [fila(s1="80")])                                        # proyecto sin «_indicadores» (anterior a esta versión)
    assert "_indicadores" not in c.proyecto.formatos and ind(c)["definicion"] == {"revision": None, "revisiones": [], "por_semana": [None] * 6, "nota": None}


# ---------- interfaz ----------
def test_interfaz_define_indicador_y_muestra_revision_base_y_nota(pagina):
    from playwright.sync_api import expect
    a = pagina.api; tablero(a, [fila(s1="28/30", s2="27/30", s3="24/30", s4="26/30")])
    a.guardar_definicion_indicador(0, DEF1, "01/06/2026")
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    pagina.evaluate("ACCIONES_UI.tablero_vista()")
    expect(pagina.locator(".tb-kpi >> nth=0")).to_contain_text("rev. 1"); expect(pagina.locator(".tb-kpi >> nth=0 >> .tb-base")).to_have_text("base: 26 de 30")
    pagina.click(".tb-kpi >> nth=0")
    expect(pagina.locator(".tb-def")).to_contain_text("Definición vigente · revisión 1")
    pagina.click(".tb-detalle button:has-text('Revisar definición')")
    pagina.locator(".dialogo textarea").nth(1).fill("Todas las entregas, incluidas las vencidas")        # denominador
    pagina.locator(".dialogo input").nth(4).fill("15/06/2026"); pagina.locator(".dialogo input").nth(5).fill("Se agregan las vencidas")
    pagina.click(".dialogo .primario")
    expect(pagina.locator(".tb-kpi >> nth=0")).to_contain_text("rev. 2"); expect(pagina.locator(".tb-cruce")).to_be_visible()
    expect(pagina.locator(".tb-avisos")).to_contain_text("cruza las revisiones 1 y 2")

