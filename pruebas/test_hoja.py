import pytest
from app.nucleo.hoja import Hoja, a_numero, a_fecha


def test_interpretacion_de_numeros_y_fechas():
    assert a_numero("12.5") == 12.5 and a_numero("-3") == -3 and a_numero("1,234.5") == 1234.5
    assert a_numero("12,5") is None and a_numero("12,5 min") is None and a_numero("1e3") == 1000
    assert a_fecha("2026-10-05").isoformat() == "2026-10-05"
    assert a_fecha("05/10/2026").isoformat() == "2026-10-05"      # día/mes/año
    assert a_fecha("31/02/2026") is None


def test_tipo_se_detecta_con_el_primer_dato_y_se_mantiene():
    h = Hoja(); h.editar(0, 0, "16.2")
    assert h.columnas[0].tipo == "num"
    h.editar(1, 0, "12,5 min")
    e = h.estado()["columnas"][0]
    assert e["texto"] == ["16.2", "12,5 min"] and e["invalida"] == [1] and e["etiqueta"] == "C1"


def test_etiquetas_tipo_minitab():
    h = Hoja(); h.editar(0, 0, "Op1"); h.editar(0, 1, "2026-10-05"); h.editar(0, 2, "3")
    assert [c["etiqueta"] for c in h.estado()["columnas"]] == ["C1-T", "C2-D", "C3"]


def test_pegar_bloque_desde_excel_extiende_la_hoja():
    h = Hoja()
    nf, nc = h.pegar(2, 1, "Sin\t16.2\r\nCon\t2.7\r\nSin\t14.7\r\n")
    assert (nf, nc) == (3, 2) and h.n == 5 and len(h.columnas) == 3
    assert h.columnas[1].tipo == "texto" and h.columnas[2].tipo == "num"
    assert h.columnas[2].celdas[2:] == ["16.2", "2.7", "14.7"]


def test_pegar_en_fila_de_nombres_usa_la_primera_linea_como_nombres():
    h = Hoja(); h.pegar(-1, 0, "condicion\ttiempo\nSin\t16.2\nCon\t2.7")
    assert [c.nombre for c in h.columnas] == ["condicion", "tiempo"] and h.n == 2


def test_pegar_texto_en_columna_numerica_lo_marca():
    h = Hoja(); h.pegar(0, 0, "1\n2"); h.pegar(2, 0, "x\n4")
    assert h.estado()["columnas"][0]["invalida"] == [2]


def test_nombres_unicos():
    h = Hoja(); h.renombrar(0, "tiempo")
    with pytest.raises(ValueError): h.renombrar(1, "Tiempo")
    h.pegar(-1, 1, "tiempo\n5")
    assert h.columnas[1].nombre == "tiempo_2"


def test_cambiar_tipo_revalida():
    h = Hoja(); h.pegar(0, 0, "a\nabc\n3")
    assert h.columnas[0].tipo == "texto"
    assert h.cambiar_tipo(0, "num") == 2
    assert h.estado()["columnas"][0]["invalida"] == [0, 1]


def test_insertar_y_eliminar_desplazan_datos():
    h = Hoja(); h.pegar(0, 0, "a\tb\n1\t2")
    h.insertar_columna(0); assert h.columnas[1].celdas == ["a", "1"]
    h.eliminar_columna(0); h.insertar_fila(0); assert h.columnas[0].celdas == [None, "a", "1"]
    h.eliminar_fila(0); assert h.columnas[0].celdas == ["a", "1"] and h.n == 2


def test_borrar_ultima_fila_reduce_la_hoja():
    h = Hoja(); h.editar(0, 0, "1"); h.editar(1, 0, "2"); h.editar(1, 0, "")
    assert h.n == 1


def test_mil_filas_pegadas():
    h = Hoja(); txt = "\n".join(f"{i}\t{i*0.5}\tA" for i in range(1000))
    h.pegar(0, 0, txt); e = h.estado()
    assert e["filas"] == 1000 and e["columnas"][1]["texto"][3] == "1.5"


def test_tipo_por_mayoria_al_pegar():
    h = Hoja(); h.pegar(0, 0, "16.2\n12,5 min\n14.7")
    assert h.columnas[0].tipo == "num" and h.estado()["columnas"][0]["invalida"] == [1]
    h.pegar(0, 1, "Sin\n3\nCon")
    assert h.columnas[1].tipo == "texto"


def test_fechas_se_muestran_dd_mm_aaaa():
    h = Hoja(); h.pegar(0, 0, "2026-10-05\n05/10/2026\n7/3/2026")
    assert h.estado()["columnas"][0]["texto"] == ["05/10/2026", "05/10/2026", "07/03/2026"]
