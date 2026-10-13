"""Recetas del diagnóstico (contrato v1): la receta del caso maestro con sus datos reproduce los 17 resultados; sin datos deja pendientes."""
from pathlib import Path
from app.api import Api
from app.nucleo import receta as RC

S = Path(__file__).parent / "sinteticos"


def test_receta_caso_maestro_reproduce_resultados():
    a = Api()
    r = a.abrir_proyecto(str(S / "caso_integral_datos_llenos.xlsx"))
    assert r["error"] is None and r["receta"]["analisis"] == 15 and r["receta"]["sin_datos"] == []
    r = a.ejecutar_receta(r["receta"]["ruta"])
    o = r["receta_resultado"]
    assert r["error"] is None and o["avisos"] == [] and o["pendientes"] == [] and o["log"][-1] == "Análisis corridos: 15 de 15."
    res = [a.resultado(x["uid"]) for x in a.resultados()]
    assert len(res) == 17 and len([k for k in a.proyecto.formatos if not k.startswith("_")]) == 28
    opt = next(x for x in res if x["definicion"]["analisis"] == "OPTIMIZADOR")
    t = next(b for b in opt["bloques"] if b["tipo"] == "tabla" and b["titulo"] == "Ajuste óptimo de los factores")
    assert [f[1] for f in t["filas"]] == ["129.42323", "108.63155"]


def test_receta_sin_datos_deja_pendientes_y_valida_version():
    a = Api(); r = a.ejecutar_receta(str(S / "caso_integral_plantilla.xlsx"))
    o = r["receta_resultado"]
    assert r["error"] is None and "Análisis corridos: 0 de 15." in o["log"] and len(o["pendientes"]) >= 15
    rc, datos = RC.leer(str(S / "caso_integral_plantilla.xlsx"))
    rc["dmike_minimo"] = "9.0"; assert any("requiere D-MIKE" in e for e in RC.validar(rc, __import__("app.modulos", fromlist=["cargar"]).cargar(), "0.23.0"))
    rc["dmike_minimo"] = "0.23"; rc["analisis"][0]["modulo"] = "NO-EXISTE"; assert any("desconocido" in e for e in RC.validar(rc, __import__("app.modulos", fromlist=["cargar"]).cargar(), "0.23.0"))


def test_interfaz_pregunta_y_ejecuta_la_receta(pagina):
    pagina.api._elegir = lambda *x, **k: str(S / "caso_integral_datos_llenos.xlsx")
    pagina.evaluate("ACCIONES_UI.abrir_proyecto()")
    pagina.wait_for_selector(".dialogo:has-text('¿Ejecutar la receta?')")
    pagina.click(".dialogo .primario")
    pagina.wait_for_function("document.querySelector('#sesion').textContent.includes('Receta ejecutada')", timeout=60000)
    assert len(pagina.api.resultados()) == 17


def _con_folio(origen, destino, folio):
    import json, openpyxl
    wb = openpyxl.load_workbook(origen); ws = wb["_receta"]
    rc = json.loads("".join(str(r[0].value) for r in ws.iter_rows() if r[0].value)); rc["folio"] = folio
    for row in ws.iter_rows(): row[0].value = None
    t = json.dumps(rc, ensure_ascii=False)
    for i in range(0, len(t), 30000): ws.cell(i // 30000 + 1, 1, t[i:i + 30000])
    wb.save(destino)


def test_receta_con_folio_actualiza_el_mismo_proyecto(tmp_path):
    """0.26 (E1-R9): el folio ya NO identifica al proyecto. D-MIKE no propone actualizar por folio; el usuario confirma a mano cuál proyecto abierto."""
    vacia, llena = str(tmp_path / "v.xlsx"), str(tmp_path / "l.xlsx")
    _con_folio(S / "caso_integral_plantilla.xlsx", vacia, "DMK-PRUEBA-0001"); _con_folio(S / "caso_integral_datos_llenos.xlsx", llena, "DMK-PRUEBA-0001")
    a = Api(); a.ejecutar_receta(vacia)
    v = a.abrir_proyecto(llena)
    assert "actualizable" not in v["receta"] and v["receta"]["abiertos"][0]["nombre"].startswith("Resistencia")      # antes: propuesto por folio
    destino = v["receta"]["abiertos"][0]["id"]                                                                         # ahora: confirmación manual
    r = a.ejecutar_receta(llena, "actualizar", destino)
    assert r["receta_resultado"]["log"][-1] == "Análisis corridos: 15 de 15." and len(a.proyectos()["proyectos"]) == 1 and len(a.resultados()) == 17
    r = a.ejecutar_receta(llena, "actualizar", destino)          # no repite lo ya corrido
    assert r["receta_resultado"]["log"][-1] == "Análisis corridos: 0 de 15." and len(a.resultados()) == 17


def test_receta_solo_datos():
    a = Api(); r = a.ejecutar_receta(str(S / "caso_integral_datos_llenos.xlsx"), "datos")
    assert r["error"] is None and len(a.resultados()) == 0 and a.hoja.indice("resistencia_base") is not None and "_receta" in a.proyecto.formatos
