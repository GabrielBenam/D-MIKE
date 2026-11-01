"""G5 (Revisar la calidad de los datos) y G6 (Duración entre dos fechas), 0.30.0. Datos SINTÉTICOS construidos a mano, con el resultado calculado a mano en cada caso.
Ambos módulos solo leen la hoja, nunca muestran el contenido de las celdas y no entran al paquete de avance."""
import json
from app.api import Api

# 8 filas (SINTÉTICO). Columnas: folio, apertura, cierre, unidad, intento, captura.
TABLA = [
    ("ZZ-f1", "01/03/2026", "05/03/2026", "ZZ-u1", "1", "2026-03-01 08:00:00"),
    ("ZZ-f2", "02/03/2026", "01/03/2026", "ZZ-u2", "1", "2026-03-01 08:00:00"),      # cierre anterior a la apertura
    ("ZZ-f1", "03/03/2026", "03/03/2026", "ZZ-u3", "1", "2026-03-01 08:00:00"),      # folio repetido; cierre igual a la apertura: no es retroactiva
    ("ZZ-f3", "04/03/2026", "10/03/2026", "ZZ-u1", "2", "2026-03-01 09:00:00"),
    ("ZZ-f4", "05/03/2026", "04/03/2026", "ZZ-u4", "2", "2026-03-01 09:00:00"),      # retroactiva; la unidad u4 solo tiene el intento 2
    ("ZZ-f2", "06/03/2026", "09/03/2026", "ZZ-u5", "1", "2026-03-02 10:00:00"),      # folio repetido
    ("ZZ-f5", "07/03/2026", "", "ZZ-u6", "", "2026-03-02 10:30:00"),                # sin cierre y sin intento: u6 no tiene primer evento identificable
    ("ZZ-f6", "", "08/03/2026", "ZZ-u7", "1", ""),
]


def api_con(tabla, cab):
    a = Api(); a.pegar(-1, 0, "\n".join(["\t".join(cab)] + ["\t".join(f) for f in tabla])); return a


def g5(**p):
    a = api_con(TABLA, ["folio", "apertura", "cierre", "unidad", "intento", "captura"])
    cols = {"claves": [0], "apertura": 1, "cierre": 2, "unidad": 3, "intento": 4, "captura": 5, "lote_min": "3"}
    antes = [list(c.celdas) for c in a.hoja.columnas]
    r = a.ejecutar_modulo("CALIDAD-DATOS", {**cols, **p}); assert r["error"] is None, r["sesion"][-1]["texto"]
    assert [list(c.celdas) for c in a.hoja.columnas] == antes                         # solo lectura: la hoja no cambió
    return a, r["resultado"], {x["id"]: x for x in r["resultado"]["datos"]["revisiones"]}


# ---------- G5, a mano ----------
def test_duplicados_2_de_8_en_2_grupos_con_sus_filas():
    _, _, r = g5(); d = r["duplicados"]
    assert d["estado"] == "no_cumple" and "2 de 8 (25.0 %)" in d["detalle"] and "en 2 grupos" in d["detalle"] and "Filas involucradas: 1, 2, 3, 6." in d["detalle"]


def test_fechas_retroactivas_2_de_6_y_la_igualdad_no_cuenta():
    _, _, r = g5(); d = r["retroactivas"]
    assert d["estado"] == "no_cumple" and "2 de 6 (33.3 %)" in d["detalle"] and "Filas: 2, 5." in d["detalle"] and "2 filas excluidas" in d["detalle"]


def test_primer_evento_ausente_2_de_7_con_motivos_sin_contenido():
    _, _, r = g5(); d = r["primer_evento"]
    assert d["estado"] == "no_cumple" and "2 de 7 (28.6 %)" in d["detalle"] and "falta el evento con intento 1: 1" in d["detalle"] and "sin número de intento ni fecha: 1" in d["detalle"]
    assert "Filas involucradas: 5, 7." in d["detalle"]


def test_lotes_segun_el_tamano_minimo_que_fija_el_usuario():
    _, _, r3 = g5(lote_min="3"); assert r3["lotes"]["estado"] == "no_cumple" and "1 lotes de 3 o más" in r3["lotes"]["detalle"] and "3 de 7 (42.9 %)" in r3["lotes"]["detalle"] and "Filas: 1, 2, 3." in r3["lotes"]["detalle"]
    _, _, r2 = g5(lote_min="2"); assert "2 lotes de 2 o más" in r2["lotes"]["detalle"] and "5 de 7 (71.4 %)" in r2["lotes"]["detalle"]
    _, _, r4 = g5(lote_min="4"); assert r4["lotes"]["estado"] == "cumple"


def test_el_tamano_minimo_no_tiene_valor_por_defecto_y_se_valida():
    a = api_con(TABLA, ["folio", "apertura", "cierre", "unidad", "intento", "captura"])
    r = a.ejecutar_modulo("CALIDAD-DATOS", {"captura": 5}); assert r["error"] == "entrada" and "Falta el tamaño mínimo del lote" in r["sesion"][-1]["texto"]
    for malo in ("1", "2.5", "x", "0"):
        assert a.ejecutar_modulo("CALIDAD-DATOS", {"captura": 5, "lote_min": malo})["error"] == "entrada", malo
    assert not any(c.get("campo") == "lote_min" and c.get("defecto") for c in a.dialogo_modulo("CALIDAD-DATOS")["dialogo"]["campos"])


def test_sin_las_columnas_de_una_revision_sale_no_evaluable_y_sin_hora_no_hay_lotes():
    a = api_con(TABLA, ["folio", "apertura", "cierre", "unidad", "intento", "captura"])
    r = {x["id"]: x for x in a.ejecutar_modulo("CALIDAD-DATOS", {"claves": [0]})["resultado"]["datos"]["revisiones"]}
    assert r["duplicados"]["estado"] == "no_cumple" and all(r[k]["estado"] == "no_evaluable" for k in ("retroactivas", "primer_evento", "lotes"))
    sin_hora = api_con([(f, a_, c, u, i, "2026-03-01") for f, a_, c, u, i, _ in TABLA], ["folio", "apertura", "cierre", "unidad", "intento", "captura"])
    r = {x["id"]: x for x in sin_hora.ejecutar_modulo("CALIDAD-DATOS", {"captura": 5, "lote_min": "2"})["resultado"]["datos"]["revisiones"]}
    assert r["lotes"]["estado"] == "no_evaluable" and "no trae hora" in r["lotes"]["detalle"]


def test_primer_evento_sin_intento_ni_fecha_pide_declarar_o_elegir():
    a = api_con(TABLA, ["folio", "apertura", "cierre", "unidad", "intento", "captura"])
    d = {x["id"]: x for x in a.ejecutar_modulo("CALIDAD-DATOS", {"unidad": 3})["resultado"]["datos"]["revisiones"]}["primer_evento"]
    assert d["estado"] == "no_evaluable" and "declara que cada fila es la primera" in d["detalle"]


def test_nunca_muestra_el_contenido_de_las_celdas_y_no_entra_al_paquete_de_avance(tmp_path):
    a, res, _ = g5()
    texto = json.dumps([res["bloques"], res["avisos"], res["titulo"]], ensure_ascii=False)       # lo que se muestra (la copia congelada de reproducibilidad no se muestra)
    assert "ZZ-" not in texto and "2026-03" not in texto and "01/03/2026" not in texto
    a.proyecto.formatos["_receta"] = {"id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c44", "json": "{}", "ids": {}}
    ruta = tmp_path / "av.json"; assert a.exportar_avance(str(ruta)).get("error") is None
    t = ruta.read_text(encoding="utf-8"); assert "CALIDAD" not in t and "revisiones" not in t and "duplicados" not in t


def test_sin_datos_no_hay_cifras():
    a = Api(); a.pegar(-1, 0, "folio\tapertura\n\t\n\t")
    r = a.ejecutar_modulo("CALIDAD-DATOS", {"claves": [0]}); assert r["error"] == "entrada" and not a.resultados()


# ---------- G6, a mano ----------
INI_FIN = [("01/03/2026", "03/03/2026 12:00"), ("2026-03-01", "2026-03-02"), ("05/03/2026", "04/03/2026"), ("01/03/2026", "ZZ-raro"), ("", "03/03/2026"),
           ("N/A", "03/03/2026"), ("01/03/2026 06:00", "01/03/2026 18:00"), ("10/03/2026", "20/03/2026"), ("10/03/2026", "14/03/2026")]


def g6(filas, **p):
    a = api_con(filas, ["inicio", "fin"]); r = a.ejecutar_modulo("DURACION", {"inicio": 0, "fin": 1, **p}); assert r["error"] is None, r["sesion"][-1]["texto"]
    res = r["resultado"]; return a, res, {b["titulo"]: b for b in res["bloques"] if b["tipo"] == "tabla"}


def test_duracion_a_mano_con_exclusiones():
    # duraciones válidas (días): 2.5, 1, 0.5, 10, 4 -> ordenadas 0.5, 1, 2.5, 4, 10; media 18/5 = 3.6; mediana 2.5; P90 = máximo (posición 0.9·6 = 5.4 >= n)
    _, res, t = g6(INI_FIN); f = {x[0]: x for x in t["Resumen de la duración"]["filas"]}
    assert f["n (filas revisadas)"][1] == "9" and f["n válidas"][1] == "5" and f["Mínimo"][1] == "0.5" and f["Máximo"][1] == "10" and f["Media"][1] == "3.6"
    assert f["Mediana"][1] == "2.5" and "15_GB" in f["Mediana"][2] and f["P90"][1] == "10" and "P90 no respaldado por el curso" in f["P90"][2]
    e = {x[0]: x for x in t["Filas excluidas"]["filas"]}
    assert e["Sin dato (vacío o «Sin datos»)"][1] == "1" and e["No aplica (N/A)"][1] == "1" and e["Fecha inválida"][1] == "1" and e["Fecha inválida"][2] == "4"
    assert e["Duración negativa (fin anterior al inicio)"][1] == "1" and e["Duración negativa (fin anterior al inicio)"][2] == "3"
    assert any("menos de 9" in a for a in res["avisos"]) and "ZZ-raro" not in json.dumps([res["bloques"], res["avisos"]], ensure_ascii=False)


def test_duracion_p90_interpolado_con_10_valores():
    # duraciones 1..10 días: media 5.5, mediana 5.5, P90: posición 0.9·11 = 9.9 -> 9 + 0.9·(10 − 9) = 9.9
    filas = [("01/01/2026", f"{k + 1:02d}/01/2026") for k in range(1, 11)]
    _, res, t = g6(filas); f = {x[0]: x for x in t["Resumen de la duración"]["filas"]}
    assert f["Media"][1] == "5.5" and f["Mediana"][1] == "5.5" and f["P90"][1] == "9.9" and not any("menos de 9" in a for a in res["avisos"])
    txt = " ".join(b.get("texto", "") for b in res["bloques"]); assert "días con fracción" in txt and "posición p(n+1)" in txt and "sin días hábiles ni feriados" in txt and "metas" in txt


def test_duracion_no_modifica_la_hoja_ni_inventa_metas_y_sin_validas_no_hay_cifras():
    a, _, _ = g6(INI_FIN)
    solo_malas = [("05/03/2026", "04/03/2026"), ("01/03/2026", "ZZ-raro")]
    b, res, t = g6(solo_malas)
    assert "Resumen de la duración" not in t and "No hay duraciones válidas" in res["bloques"][0]["texto"] and not any(x["tipo"] == "grafica" for x in res["bloques"])
    c = Api(); c.pegar(-1, 0, "inicio\tfin\n\t\n\t"); assert c.ejecutar_modulo("DURACION", {"inicio": 0, "fin": 1})["error"] == "entrada"
    assert a.ejecutar_modulo("DURACION", {"inicio": 0, "fin": 0})["error"] == "entrada"


def test_duracion_grafica_opcional_usa_el_sistema_interactivo():
    filas = [("01/01/2026", f"{k + 1:02d}/01/2026") for k in range(1, 11)]
    _, res, _ = g6(filas); assert not any(b["tipo"] == "grafica" for b in res["bloques"])
    _, res, _ = g6(filas, grafica=True); g = next(b for b in res["bloques"] if b["tipo"] == "grafica")
    assert g["svg"].startswith("<svg") and g["inter"]["g"] == "histograma" and len(g["inter"]["x"]) == 10


# ---------- menús, catálogo e interfaz ----------
def test_ubicacion_en_los_menus_y_en_el_catalogo():
    from app.nucleo.menus import MENUS
    from app import modulos
    from app.api import VERSION
    m = dict(MENUS)
    assert ("Revisar la calidad de los datos…", "mod:CALIDAD-DATOS") in m["Datos"] and ("Duración entre dos fechas (lead time)…", "mod:DURACION") in m["Estadística"]
    assert VERSION == "0.30.0" and {"CALIDAD-DATOS", "DURACION"} <= set(modulos.cargar())


def test_interfaz_abre_los_dos_dialogos(pagina):
    from playwright.sync_api import expect
    a = pagina.api; a.pegar(-1, 0, "inicio\tfin\n01/01/2026\t05/01/2026\n02/01/2026\t06/01/2026")
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']"); pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.evaluate("abrirModulo('CALIDAD-DATOS')"); expect(pagina.locator(".dialogo")).to_contain_text("tamaño mínimo de un lote")
    pagina.keyboard.press("Escape")
    pagina.evaluate("abrirModulo('DURACION')"); expect(pagina.locator(".dialogo")).to_contain_text("Columna de inicio")
