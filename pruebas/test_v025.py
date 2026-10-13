"""v0.25: A3 reproducir contra recalcular (copia congelada con huella SHA-256), A4 exportación con precisión completa y
especificaciones interactivas de las gráficas de prioridad alta. Datos SINTÉTICOS."""
import openpyxl
from app.api import Api
from playwright.sync_api import expect

DATOS = "y\tg\n" + "\n".join(f"{10 + (i % 3) * 2 + (i % 5) * .37123}\t{'ABC'[i % 3]}" for i in range(30))
texto = lambda r: [b.get("texto") or b.get("filas") for b in r["bloques"] if b["tipo"] in ("texto", "tabla")]


def test_a3_reproducir_y_desactualizado():
    a = Api(); a.pegar(-1, 0, DATOS)
    uid = a.ejecutar_modulo("ANOVA", {"y": 0, "factor": 1, "alfa": "0.05"})["resultado"]["uid"]
    assert a.estado_resultado(uid)["estado"] == "vigente"
    a.hoja.editar(0, 0, "99"); assert a.estado_resultado(uid)["estado"] == "desactualizado"
    r = a.reproducir_resultado(uid); assert r["error"] is None and texto(r["resultado"]) == texto(a.resultado(uid))
    assert texto(a.repetir_resultado(uid)["resultado"]) != texto(a.resultado(uid))


def test_a4_exporta_precision_completa(tmp_path):
    a = Api(); a.pegar(-1, 0, DATOS)
    uid = a.ejecutar_modulo("ANOVA", {"y": 0, "factor": 1, "alfa": "0.05"})["resultado"]["uid"]
    a._elegir = lambda *x, **k: str(tmp_path / "r.xlsx"); a.exportar_resultado(uid)
    vals = [c.value for row in openpyxl.load_workbook(tmp_path / "r.xlsx").active.iter_rows() for c in row if isinstance(c.value, float)]
    assert any(len(repr(v).split(".")[-1]) > 6 for v in vals)          # más decimales de los que se muestran


def test_graficas_emiten_especificacion():
    a = Api(); a.pegar(-1, 0, DATOS)
    r = a.ejecutar_modulo("BOXPLOT", {"y": 0, "grupo": 1})["resultado"]
    assert [b["inter"]["g"] for b in r["bloques"] if b.get("inter")] == ["caja"]
    r = a.ejecutar_modulo("CORRIDA", {"y": 0})["resultado"]; assert r["bloques"][0]["inter"]["g"] == "corrida"


def test_interfaz_grafica_interactiva_y_pestana_grafico(pagina):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    pagina.api.pegar(-1, 0, DATOS); pagina.add_init_script("try { sessionStorage.setItem('dmike_ui_nueva', '1'); localStorage.removeItem('dmike_graficas_int'); } catch (e) {}")
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']"); pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    r = pagina.api.ejecutar_modulo("BOXPLOT", {"y": 0, "grupo": 1})["resultado"]
    pagina.evaluate("r => abrirPestana('res:' + r.uid, r)", r)
    expect(pagina.locator(".g-int .g-plot .main-svg").first).to_be_visible()
    pagina.click(".g-barra button:has-text('Estilo y color')"); expect(pagina.locator(".g-pop")).to_contain_text("Escala original")
    pagina.click(".g-pop button:has-text('Violín')"); pagina.click(".g-pop button:has-text('Editar propiedades')")
    expect(pagina.locator("#tab-grafico")).to_be_visible(); expect(pagina.locator("#cinta")).to_contain_text("Escala original")
    assert pagina.api.estilos_graficas()[f"{r['uid']}:0"]["s"] == 2
    pagina.click(".pestana[data-p='hoja']"); expect(pagina.locator("#tab-grafico")).to_have_count(0)
    pagina.evaluate("ACCIONES_UI.paleta_graficas()"); expect(pagina.locator(".g-paletas .g-pal")).to_have_count(10)
    assert not errores, errores
