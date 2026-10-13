"""Revisión completa de la interfaz: cada opción de menú y cada botón de las barras con diálogos de archivo simulados que validan los
filtros igual que pywebview; panel DMAIC jerárquico (raíz, fases, inactivos, activar y desactivar). Datos SINTÉTICOS."""
import os, shutil
import webview
from webview.util import parse_file_type
from playwright.sync_api import expect
from app.api import Api
from test_modulos_interfaz import menu

DATOS = "fecha\tturno\tdefecto\ttiempo\tdiametro\n" + "\n".join(
    f"2026-10-{1 + i // 5:02d}\t{'AB'[i % 2]}\t{'RAYA GOLPE RAYA MANCHA RAYA'.split()[i % 5]}\t{10 + (i * 7) % 5 + (i % 2)}\t{round(25 + ((i * 13) % 7 - 3) * .01, 3)}" for i in range(40))


class VentanaFalsa:
    """Imita create_file_dialog de pywebview: valida cada filtro con webview.util.parse_file_type (lo que fallaba con «D-MIKE»)."""
    def __init__(self, dirtmp, existentes): self.dir, self.ex, self.llamadas = dirtmp, existentes, []

    def create_file_dialog(self, clase, file_types=(), save_filename="", **k):
        for t in file_types: parse_file_type(t)                    # lanza ValueError si el filtro no es válido
        self.llamadas.append((clase, file_types))
        FD = getattr(webview, "FileDialog", None)
        OPEN, FOLDER = (FD.OPEN, FD.FOLDER) if FD else (webview.OPEN_DIALOG, webview.FOLDER_DIALOG)
        if clase == FOLDER: return (str(self.dir),)
        ext = file_types[0].split("(*")[1].split(";")[0].rstrip(")") if file_types else ""
        if clase == OPEN: return (self.ex.get(ext, self.ex.get(".csv")),)
        return str(self.dir / f"salida_{len(self.llamadas)}{ext if ext != '.*' else '.txt'}")


def cerrar_todo(pagina):
    """Cierra diálogos, paleta, ventanas de módulos y la pantalla de inicio que haya abierto una opción de menú."""
    for _ in range(6):
        if not pagina.locator(".velo").count(): break
        b = pagina.locator(".velo .dialogo-botones button:not(.primario)")
        if b.count(): b.last.click()
        else: pagina.keyboard.press("Escape"); pagina.evaluate("document.querySelectorAll('.velo').forEach(v => v.remove())")
        pagina.wait_for_timeout(80)
    pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove(); document.querySelectorAll('.ctx-menu').forEach(m => m.remove())")


def preparar(pagina, tmp_path):
    a = pagina.api; a.pegar(-1, 0, DATOS)
    otro = Api(); otro.pegar(-1, 0, "x\n1\n2"); ruta = tmp_path / "otro.dmike"; otro.guardar_como_ruta = None
    otro._elegir = lambda *x, **k: str(ruta); otro.guardar(True)
    csv = tmp_path / "datos.csv"; csv.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    perfil = tmp_path / "perfil.json"; shutil.copy("pruebas/sinteticos/perfil_prueba_sintetico.json", perfil)
    v = VentanaFalsa(tmp_path, {".dmike": str(ruta), ".csv": str(csv), ".json": str(perfil), ".xlsx": str(csv)})
    a._ventana = v
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    return v


def sin_fallas(pagina, errores):
    assert not errores, errores
    assert "No se pudo completar la acción" not in pagina.locator("#sesion").inner_text()


def test_abrir_y_guardar_con_dialogo_real_de_pywebview(pagina, tmp_path):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    v = preparar(pagina, tmp_path)
    pagina.click("button.ico[title^='Guardar']"); expect(pagina.locator("#archivo")).not_to_contain_text("Sin guardar")
    pagina.click("button.ico[title^='Abrir proyecto']")
    expect(pagina.locator("#hoja-tabla th.nombre[data-c='0']")).to_have_text("x")
    pagina.keyboard.press("Control+o"); pagina.wait_for_timeout(300)
    assert any("dmike" in str(t) for _, t in v.llamadas)
    sin_fallas(pagina, errores)


def test_cada_opcion_de_menu_y_boton_funciona(pagina, tmp_path):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    preparar(pagina, tmp_path)
    menus = pagina.locator(".menu > button"); titulos = [menus.nth(i).inner_text() for i in range(menus.count())]
    hechas = 0
    for t in titulos:
        pagina.click(f".menu > button:text-is('{t}')")
        ops = pagina.locator(".menu.abierto button[role='menuitem']:not([disabled])"); nombres = [ops.nth(i).inner_text() for i in range(ops.count())]
        pagina.keyboard.press("Escape")
        for n in nombres:
            if n in ("Salir",) or n.startswith("Nuevo proyecto") or n.startswith("Abrir proyecto") or n.startswith("Fijar o contraer la cinta"): continue
            pagina.click(f".menu > button:text-is('{t}')"); pagina.click(f".menu.abierto button:text-is('{n}')"); pagina.wait_for_timeout(150)
            cerrar_todo(pagina)
            hechas += 1
    assert hechas > 120
    # barra principal
    for tit in ("Deshacer", "Rehacer", "Copiar", "Ordenar de menor", "Ordenar de mayor", "Importar", "Filtrar", "Calculadora"):
        pagina.click(f"#herramientas button.ico[title^='{tit}']"); pagina.wait_for_timeout(120)
        while pagina.locator(".velo").count(): pagina.locator(".velo .dialogo-botones button:not(.primario)").last.click()
    sin_fallas(pagina, errores)


def test_barra_contextual_cambia_con_la_pestana(pagina, tmp_path):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    preparar(pagina, tmp_path)
    expect(pagina.locator("#herr-contexto")).to_contain_text("Hoja")
    r = pagina.api.ejecutar_modulo("ANOVA", {"y": 3, "factor": 1, "alfa": "0.05"})["resultado"]
    pagina.evaluate("r => abrirPestana('res:' + r.uid, r)", r)
    expect(pagina.locator("#herr-contexto")).to_contain_text("Comparar con Tukey")
    pagina.click("#herr-contexto button:has-text('Modificar…')")
    expect(pagina.locator(".dialogo")).to_contain_text("(modificar)")
    expect(pagina.locator(".dialogo select[name='y']")).to_have_value("3")
    pagina.click(".dialogo .primario"); expect(pagina.locator(".pestana")).to_have_count(3)
    pagina.click("#herr-contexto button:has-text('Exportar…')"); pagina.wait_for_timeout(200)
    menu(pagina, "Gestión", "Acta del proyecto (Charter)")
    expect(pagina.locator("#herr-contexto")).to_contain_text("Formato"); expect(pagina.locator("#herr-contexto")).to_contain_text("Interesados")
    pagina.click("#herr-contexto button:has-text('Interesados')"); expect(pagina.locator(".pestana.activa")).to_contain_text("Interesados")
    pagina.click("#herr-contexto button:has-text('Exportar a Excel…')"); pagina.wait_for_timeout(200)
    sin_fallas(pagina, errores)


def test_panel_dmaic_jerarquico_activar_y_desactivar(pagina, tmp_path):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    preparar(pagina, tmp_path)
    expect(pagina.locator(".dmaic-raiz")).to_have_attribute("aria-expanded", "true")
    pagina.click(".dmaic-raiz"); expect(pagina.locator(".dmaic-fases")).to_be_hidden()
    pagina.click(".dmaic-raiz"); expect(pagina.locator(".dmaic-fases")).to_be_visible()
    pagina.click(".fase[data-fase='D'] .fase-cab")
    lista = pagina.locator(".fase[data-fase='D'] .inactivos-lista")
    expect(lista).to_be_hidden()
    pagina.click(".fase[data-fase='D'] .grupo-in"); expect(lista).to_be_visible()
    pagina.click(".fase[data-fase='D'] .inactivos-lista li[data-id='RACI'] .mod-nombre")
    expect(pagina.locator(".pestana.activa")).to_contain_text("RACI")                      # abrir desde inactivos
    pagina.click(".fase[data-fase='D'] .inactivos-lista li[data-id='RACI'] .mod-activar")
    expect(pagina.locator(".fase[data-fase='D'] .activos li[data-id='RACI']")).to_be_visible()
    expect(pagina.locator(".fase[data-fase='D'] .inactivos-lista li[data-id='RACI']")).to_have_count(0)
    pagina.click(".fase[data-fase='D'] .activos li[data-id='RACI'] .mod-mas")
    pagina.click(".dialogo button:has-text('Pasar a inactivos')")
    expect(pagina.locator(".fase[data-fase='D'] .activos li[data-id='RACI']")).to_have_count(0)
    menu(pagina, "Proyecto", "Abrir perfil del diagnóstico…")
    expect(pagina.locator(".fase[data-fase='M'] .activos li").first).to_be_visible()
    pagina.locator(".fase[data-fase='M'] .activos li").first.click(); pagina.wait_for_timeout(300)
    assert pagina.locator(".pestana.activa").count() == 1 or pagina.locator(".velo").count()
    sin_fallas(pagina, errores)


def test_filtros_de_archivo_validos_para_pywebview():
    import pytest
    from app.api import filtro_archivo
    with pytest.raises(ValueError): parse_file_type("Proyecto D-MIKE (*.dmike)")               # la causa del fallo de «Abrir»
    for t in ("Proyecto D-MIKE (*.dmike)", "CSV UTF-8 (*.csv)", "Datos (*.csv;*.tsv;*.txt;*.xlsx)", "Todos los archivos (*.*)", "Perfil del proyecto (*.json)"):
        d, e = parse_file_type(filtro_archivo(t)); assert d and e.startswith("*")
