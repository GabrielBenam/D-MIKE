"""E2: importar CSV/TSV/XLSX, ordenar, buscar y reemplazar, deshacer y rehacer. Datos SINTÉTICOS."""
from datetime import date
from openpyxl import Workbook
from playwright.sync_api import expect
from app.api import Api
from test_modulos_interfaz import menu


def test_importar_csv_coma_y_punto_y_coma(tmp_path):
    a = Api()
    (tmp_path / "a.csv").write_text("lote,peso,fecha\nL1,12.5,2026-10-05\nL2,13.1,2026-10-06\n", encoding="utf-8")
    r = a.importar(str(tmp_path / "a.csv"))
    assert r["error"] is None and "coma" in r["sesion"][0]["texto"]
    cols = r["hoja"]["columnas"]
    assert [c["nombre"] for c in cols] == ["lote", "peso", "fecha"] and [c["tipo"] for c in cols] == ["texto", "num", "fecha"]
    (tmp_path / "b.csv").write_text("operador;tiempo\nAna;12,5\nLuis;13,75\n", encoding="cp1252")
    r = a.importar(str(tmp_path / "b.csv"))
    assert [c["nombre"] for c in r["hoja"]["columnas"]][3:] == ["operador", "tiempo"]
    assert a.hoja.columnas[4].valor(1)[2] == 13.75 and "punto y coma" in r["sesion"][0]["texto"]


def test_importar_tsv_y_excel(tmp_path):
    a = Api()
    (tmp_path / "c.txt").write_text("x\ty\n1\t2\n3\t4\n", encoding="utf-8")
    assert a.importar(str(tmp_path / "c.txt"))["error"] is None and a.hoja.n == 2
    wb = Workbook(); ws = wb.active; ws.append(["maquina", "diametro", "fecha"])
    ws.append(["M1", 10.02, date(2026, 10, 5)]); ws.append(["M2", 9.98, date(2026, 10, 6)]); wb.save(tmp_path / "d.xlsx")
    b = Api(); r = b.importar(str(tmp_path / "d.xlsx"))
    assert r["error"] is None and b.hoja.columnas[1].valor(0)[2] == 10.02 and b.hoja.columnas[2].valor(1)[2] == date(2026, 10, 6)


def test_importar_errores_no_tocan_la_hoja(tmp_path):
    a = Api(); a.pegar(-1, 0, "x\n1"); antes = a.hoja.estado()
    (tmp_path / "v.csv").write_text("", encoding="utf-8")
    assert a.importar(str(tmp_path / "v.csv"))["error"] == "importar" and a.hoja.estado() == antes
    assert a.importar(str(tmp_path / "no.csv"))["error"] == "importar"
    (tmp_path / "x.xls").write_bytes(b"x")
    assert "xlsx" in a.importar(str(tmp_path / "x.xls"))["sesion"][0]["texto"]


def test_ordenar_mueve_filas_completas():
    a = Api(); a.pegar(-1, 0, "id\tvalor\nA\t3\nB\tabc\nC\t1\nD\t2")
    r = a.ejecutar_modulo("ORDENAR", {"col": 1, "orden": "asc"})
    assert r["error"] is None and "resultado" not in r
    assert [a.hoja.columnas[0].valor(i)[0] for i in range(4)] == ["C", "D", "A", "B"]          # inválido al final
    a.ejecutar_modulo("ORDENAR", {"col": 0, "orden": "desc"})
    assert [a.hoja.columnas[1].valor(i)[0] for i in range(4)] == ["2", "1", "abc", "3"]


def test_reemplazar_y_deshacer_rehacer():
    a = Api(); a.pegar(-1, 0, "turno\tdefecto\nMatutino\trayón\nmatutino\tRayón profundo\nNocturno\tgolpe")
    r = a.ejecutar_modulo("REEMPLAZAR", {"buscar": "matutino", "nuevo": "T1", "completa": True})
    assert "2" in r["sesion"][0]["texto"] and a.hoja.columnas[0].valor(1)[0] == "T1"
    a.ejecutar_modulo("REEMPLAZAR", {"buscar": "rayón", "nuevo": "raya", "col": 1})
    assert a.hoja.columnas[1].valor(1)[0] == "raya profundo"
    assert a.ejecutar_modulo("REEMPLAZAR", {"buscar": ""})["error"] == "entrada"
    a.deshacer(); assert a.hoja.columnas[1].valor(1)[0] == "Rayón profundo"
    a.deshacer(); assert a.hoja.columnas[0].valor(0)[0] == "Matutino"
    a.rehacer(); assert a.hoja.columnas[0].valor(0)[0] == "T1"
    a.editar(0, 0, "X"); assert "No hay cambios para rehacer" in a.rehacer()["sesion"][0]["texto"]


def test_deshacer_edicion_y_diseno():
    a = Api(); a.editar(0, 0, "5"); a.editar(1, 0, "6")
    a.deshacer(); assert a.hoja.n == 1 and a.hoja.columnas[0].valor(0)[0] == "5"
    a.ejecutar_modulo("DISENO-RSM", {"nombres": "A, B", "bajos": "0, 0", "altos": "1, 1"})
    assert len(a.hoja.columnas) > 5
    a.deshacer(); assert len(a.hoja.columnas) == 1
    a.ejecutar_modulo("CORRIDA", {"y": 0})                    # un análisis no cambia la hoja: no ocupa un paso
    a.deshacer(); assert a.hoja.n == 0 or a.hoja.columnas[0].valor(0)[0] == ""      # deshace la edición de «5», no el análisis


def test_interfaz_ctrl_z_y_menu(pagina, tmp_path):
    (tmp_path / "m.csv").write_text("pieza,largo\nP1,10\nP2,12\n", encoding="utf-8")
    pagina.api._elegir = lambda *x, **k: str(tmp_path / "m.csv")
    menu(pagina, "Archivo", "Importar archivo (CSV, TXT, Excel)…")
    expect(pagina.locator("#hoja-tabla th.nombre[data-c='1']")).to_have_text("largo")
    pagina.locator("#hoja-tabla [data-f='0'][data-c='1']").click(); pagina.keyboard.type("99"); pagina.keyboard.press("Enter")
    expect(pagina.locator("#hoja-tabla [data-f='0'][data-c='1']")).to_have_text("99")
    pagina.keyboard.press("Control+z")
    expect(pagina.locator("#hoja-tabla [data-f='0'][data-c='1']")).to_have_text("10")
    pagina.keyboard.press("Control+y")
    expect(pagina.locator("#hoja-tabla [data-f='0'][data-c='1']")).to_have_text("99")
    menu(pagina, "Datos", "Ordenar…")
    pagina.select_option(".dialogo select[name='col']", "1"); pagina.select_option(".dialogo select[name='orden']", "desc")
    pagina.click(".dialogo .primario")
    expect(pagina.locator("#hoja-tabla [data-f='0'][data-c='0']")).to_have_text("P1")
    expect(pagina.locator(".pestana.activa")).to_have_text("Hoja de datos")
