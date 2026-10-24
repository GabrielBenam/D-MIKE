"""Interfaz v0.21 (cinta, riel, inicio, paleta, clic derecho, vista dividida, ventana de módulos, ayuda F1, tema, sesión plegable)
y QFD interactivo. Datos SINTÉTICOS."""
import os
from pathlib import Path
from playwright.sync_api import expect

NUEVA = "try { sessionStorage.setItem('dmike_ui_nueva', '1'); ['cinta','riel','inicio','compacto','sesion_abierta'].forEach(k => localStorage.removeItem('dmike_' + k)); } catch (e) {}"


def nueva(pagina, tmp_path, con_reciente=True):
    os.environ["APPDATA"] = str(tmp_path)
    a = pagina.api
    if con_reciente:
        a.pegar(-1, 0, "y\tgrupo\n" + "\n".join(f"{10 + (i % 3) * 2 + (i % 5) * .3}\t{'ABC'[i % 3]}" for i in range(30)))
        a._elegir = lambda *x, **k: str(tmp_path / "proyecto_prueba.dmike"); a.guardar(True)
        a.nuevo_proyecto()
    pagina.add_init_script(NUEVA); pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")


def test_inicio_cinta_riel_y_tema(pagina, tmp_path):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    nueva(pagina, tmp_path)
    expect(pagina.locator("#inicio")).to_be_visible()
    expect(pagina.locator(".inicio-reciente")).to_contain_text("proyecto_prueba")
    pagina.click(".inicio-reciente"); expect(pagina.locator("#inicio")).to_have_count(0)
    expect(pagina.locator("#cinta")).to_be_visible()
    pagina.click("#menus .menu > button:text-is('Estadística')")
    b = pagina.locator("#cinta .cinta-b").filter(has_text="ANOVA").first
    assert ":" in (b.get_attribute("aria-label") or "")                    # cada comando dice qué hace (la tarjeta de ayuda lo muestra)
    b.click(); expect(pagina.locator(".dialogo")).to_be_visible(); pagina.keyboard.press("Escape")
    assert pagina.evaluate("document.body.classList.contains('riel')")
    pagina.click(".fase[data-fase='A'] .fase-cab")
    expect(pagina.locator(".fase[data-fase='A'] .fase-cuerpo")).to_be_visible()
    pagina.click(".fase[data-fase='A'] .pop-botones button:has-text('Módulos del proyecto')")
    expect(pagina.locator(".ventana-mod .vm-paso")).to_have_count(5); expect(pagina.locator(".ventana-mod .vm-col")).to_have_count(1)   # abre en la fase A
    pagina.click(".vm-paso[data-f='A']"); expect(pagina.locator(".ventana-mod .vm-col")).to_have_count(5)
    pagina.click(".ventana-mod .boton:has-text('Cerrar')")
    pagina.click(".interruptor"); expect(pagina.locator("html")).to_have_attribute("data-tema", "oscuro")
    pagina.click(".interruptor"); expect(pagina.locator("html")).not_to_have_attribute("data-tema", "oscuro")
    assert not pagina.evaluate("document.body.classList.contains('sesion-abierta')")
    pagina.click(".sesion-titulo"); assert pagina.evaluate("document.body.classList.contains('sesion-abierta')")
    assert not errores, errores


def test_paleta_clic_derecho_division_y_ayuda(pagina, tmp_path):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    nueva(pagina, tmp_path, con_reciente=False)
    pagina.api.pegar(-1, 0, "y\tgrupo\n" + "\n".join(f"{10 + (i % 3) * 2 + (i % 5) * .3}\t{'ABC'[i % 3]}" for i in range(30)))
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']")
    pagina.keyboard.press("Control+k"); expect(pagina.locator(".paleta")).to_be_visible()
    pagina.fill(".pal-in", "anova de un"); pagina.keyboard.press("Enter")
    expect(pagina.locator(".dialogo")).to_be_visible()
    pagina.select_option(".dialogo select[name='y']", "0"); pagina.select_option(".dialogo select[name='factor']", "1"); pagina.click(".dialogo .primario")
    expect(pagina.locator(".pestana.activa")).to_contain_text("ANOVA")
    pagina.click(".pestana.activa", button="right"); expect(pagina.locator(".ctx-menu")).to_contain_text("Abrir a la derecha")
    pagina.click(".ctx-menu button:has-text('Abrir a la derecha')")
    expect(pagina.locator("#derecha")).to_be_visible(); expect(pagina.locator("#marco-hoja")).to_be_visible()
    pagina.click(".derecha-cab .boton"); expect(pagina.locator("#derecha")).to_be_hidden()
    pagina.keyboard.press("F1"); expect(pagina.locator(".ayuda .ay-nav")).to_be_visible()
    pagina.fill(".ay-buscar", "pareto"); expect(pagina.locator(".ay-cuerpo")).to_contain_text("Pareto")
    pagina.click(".ay-item:has-text('Todos')"); expect(pagina.locator(".ay-cuerpo tbody tr")).to_have_count(len(__import__("json").load(open(Path(__file__).parent.parent / "app" / "datos" / "comandos.json", encoding="utf-8"))))
    pagina.locator(".fase[data-fase='A'] .fase-cab").click(button="right"); expect(pagina.locator(".ctx-menu")).to_contain_text("Ruta DMAIC")
    assert not errores, errores


def test_qfd_interactivo_y_casa_completa(pagina, tmp_path):
    errores = []; pagina.on("pageerror", lambda e: errores.append(str(e)))
    a = pagina.api; d = a.abrir_formato("QFD")["datos"]
    for k, n in enumerate(["Tiempo de respuesta", "Capacitación", "Encuesta"]): d["tablas"]["tecnicos"][k].update(nombre=n, direccion="max")
    d["tablas"]["requisitos_cliente"] = [{"requisito": "Rapidez", "importancia": "5", "rel_1": "9"}, {"requisito": "Trato", "importancia": "3", "rel_2": "9"}]
    a.guardar_formato("QFD", d)
    nueva(pagina, tmp_path, con_reciente=False)
    pagina.evaluate("abrirModulo('QFD')"); expect(pagina.locator(".qfd-casa svg")).to_be_visible()
    pagina.locator(".qfd-casa [data-rel='1:1']").dispatch_event("click")
    expect(pagina.locator(".tabla-fmt[data-tabla='requisitos_cliente'] select[name='rel_1'] >> nth=1")).to_have_value("9")
    pagina.locator(".qfd-casa [data-cor='1:2']").dispatch_event("click"); pagina.wait_for_timeout(400); assert a.proyecto.formatos["QFD"]["cabecera"]["techo"] == "1-2 ++"
    expect(pagina.locator(".formato.dividida")).to_be_visible()                 # el QFD abre con la casa completa a la derecha
    pagina.click(".vista-barra button:has-text('Casa completa a la derecha')"); expect(pagina.locator(".formato.dividida")).to_have_count(0)
    assert not errores, errores


def test_el_boton_cinta_oculta_y_muestra_la_cinta_y_libera_el_espacio(pagina, tmp_path):
    """El botón «Cinta» (y Ctrl+F1) debe ocultar la cinta de verdad: antes el atributo hidden perdía contra `.cinta { display: flex }` y la cinta nunca se iba."""
    nueva(pagina, tmp_path, con_reciente=False)
    pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    expect(pagina.locator("#cinta")).to_be_visible()
    alto_con = pagina.evaluate("document.querySelector('.vista:not([hidden]), #hoja-marco, #pestanas').getBoundingClientRect().top")
    pagina.click(".boton-ctrl:text-is('Cinta')")
    expect(pagina.locator("#cinta")).to_be_hidden(); assert not pagina.evaluate("document.body.classList.contains('cinta-fija')")
    assert pagina.evaluate("document.getElementById('cinta').getBoundingClientRect().height") == 0
    alto_sin = pagina.evaluate("document.querySelector('.vista:not([hidden]), #hoja-marco, #pestanas').getBoundingClientRect().top")
    assert alto_sin < alto_con - 40                                                        # el espacio de trabajo sube: la cinta ya no lo ocupa
    pagina.click("#menus .menu > button:text-is('Estadística')")                          # sin cinta fija, la pestaña abre su menú desplegable
    expect(pagina.locator("#menus .menu.abierto")).to_have_count(1); expect(pagina.locator("#cinta")).to_be_hidden()
    pagina.keyboard.press("Escape"); pagina.mouse.click(600, 500)
    pagina.keyboard.press("Control+F1"); expect(pagina.locator("#cinta")).to_be_visible()   # Ctrl+F1 la vuelve a fijar
    pagina.keyboard.press("Control+F1"); expect(pagina.locator("#cinta")).to_be_hidden()
    assert pagina.evaluate("localStorage.getItem('dmike_cinta')") == "0"                   # la preferencia se guarda (esta prueba la borra al recargar, como las demás)
