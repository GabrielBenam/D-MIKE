"""E3-5 (parte B): la región autorizada en recetas y en diseños que ya existen. `validar` exige disenos[].limites_seguros a las recetas con
dmike_minimo 0.29 o mayor en modo real; los diseños sin región quedan «región no declarada» con la tarea «declarar límites seguros»; se declaran después
si todos sus puntos caben. Datos SINTÉTICOS."""
import copy, json, gzip, shutil
from pathlib import Path
from app.api import Api
from app.nucleo import modo as MD, receta as RC
from app import modulos

REG = modulos.cargar(); S = Path(__file__).parent / "sinteticos"
DISENO = {"tipo": "fact", "nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "centros": "2", "respuesta": "Resistencia", "semilla": "7"}
LIM = {"Temp": {"min": 90, "max": 130}, "Tiempo": {"min": 5, "max": 40}}


def rec(dmike_minimo="0.29", modo="real", limites="ninguno", **extra):
    d = {"id": "d1", "modulo": "DISENO-RSM", "hoja": "Corridas", "respuestas": ["Resistencia"], "parametros": dict(DISENO)}
    if limites != "ninguno": d["limites_seguros"] = limites
    rc = {"tipo": "dmike-receta", "receta_version": 2, "dmike_minimo": dmike_minimo, "modo_proyecto": modo, "id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c15",
          "datos_fijos": {}, "hojas": [{"hoja": "Corridas", "origen_datos": "vacia", "columnas": []}], "disenos": [d], **extra}
    rc["huella"] = RC.huella_receta({k: v for k, v in rc.items() if k != "huella"}); return rc


def err(rc, version="0.29.0", modo=None): return RC.validar(rc, REG, version, modo=modo)


def archivo(tmp, rc, nombre="r.json"):
    ruta = tmp / nombre; ruta.write_text(json.dumps(rc), encoding="utf-8"); return str(ruta)


def sin_region(a=None, demo=False):
    """Proyecto con un diseño sin región declarada (como el de una receta anterior)."""
    a = a or Api()
    if demo: MD.fijar(a.proyecto, MD.DEMO, MD.DECLARADO)
    r = a.ejecutar_modulo("DISENO-RSM", {**DISENO, "limites_opcionales": True} if not demo else DISENO); assert r["error"] is None, r["sesion"][0]["texto"]
    return a


def ids_tareas(a): return {t["id"] for t in a.seguimiento()["tareas_abiertas"]}


# ---------- validar ----------
def test_receta_029_real_exige_limites_seguros():
    assert any("no trae limites_seguros" in e and "obligatorios desde D-MIKE 0.29" in e for e in err(rec()))
    assert err(rec(limites=LIM)) == []


def test_demostracion_y_recetas_anteriores_no_los_exigen():
    assert err(rec(modo="demostracion")) == []                                  # opcionales en demostración
    for v in ("0.26", "0.27", "0.28"): assert err(rec(dmike_minimo=v), version="0.29.0") == [], v           # compatibilidad: solo desde 0.29
    assert err(rec(), version="0.29.0", modo="demostracion") == []             # el modo con que se ejecutará manda sobre el declarado


def test_estructura_de_los_limites_se_valida_en_cualquier_version():
    for v in ("0.26", "0.29"):
        assert any("debe ser un objeto" in e for e in err(rec(dmike_minimo=v, limites=[1, 2])))
        assert any("falta un {min, max} numérico para el factor «Tiempo»" in e for e in err(rec(dmike_minimo=v, limites={"Temp": LIM["Temp"]})))
        assert any("falta un {min, max} numérico" in e for e in err(rec(dmike_minimo=v, limites={**LIM, "Temp": {"min": "a", "max": 5}})))
        assert any("falta un {min, max} numérico" in e for e in err(rec(dmike_minimo=v, limites={**LIM, "Temp": {"min": True, "max": 5}})))
        assert any("mínimo de «Temp» debe ser menor que su máximo" in e for e in err(rec(dmike_minimo=v, limites={**LIM, "Temp": {"min": 130, "max": 90}})))
    assert err(rec(dmike_minimo="0.28", limites={**LIM, "Otro": {"min": 0, "max": 1}})) == []           # factores de más se toleran (claves desconocidas)


def test_receta_029_se_rechaza_hoy_por_la_version_y_la_exigencia_queda_lista(tmp_path):
    from app.api import VERSION
    a = Api(); r = a.abrir_receta(archivo(tmp_path, rec(limites=LIM)))
    assert VERSION < "0.29" and r["error"] == "receta" and "requiere D-MIKE 0.29 o posterior" in r["sesion"][-1]["texto"]


# ---------- región no declarada y tarea ----------
def test_diseno_sin_region_en_real_lleva_la_tarea_declarar_limites_seguros(tmp_path):
    a = sin_region(); d = a.disenos()[0]
    assert d["region"] == "no_declarada" and d["limites_seguros"] is None
    t = {x["id"]: x for x in a.seguimiento()["tareas_abiertas"]}
    assert "auto:limites:DIS-Resistencia" in t and "Declarar los límites seguros del diseño DIS-Resistencia" in t["auto:limites:DIS-Resistencia"]["descripcion"]
    assert "_tareas" not in a.proyecto.formatos or not [x for x in a.proyecto.formatos["_tareas"] if x["id"].startswith("auto:limites")]     # derivada: no se guarda


def test_demostracion_no_lleva_la_tarea():
    assert not [i for i in ids_tareas(sin_region(demo=True)) if i.startswith("auto:limites")]


def test_la_tarea_viaja_en_el_paquete_de_avance_sin_datos(tmp_path):
    a = Api(); a.ejecutar_receta(archivo(tmp_path, rec(dmike_minimo="0.28")))                      # receta anterior a 0.29: sin límites, región no declarada
    ruta = tmp_path / "av.json"; assert a.exportar_avance(str(ruta))["error"] is None
    pkg = json.loads(ruta.read_text(encoding="utf-8")); t = {x["id"]: x for x in pkg["tareas_abiertas"]}
    assert "auto:limites:DIS-Resistencia" in t and set(t["auto:limites:DIS-Resistencia"]) == {"id", "descripcion"}


def test_abrir_y_consultar_un_proyecto_anterior_no_escribe_nada(tmp_path):
    ruta = tmp_path / "c.dmike"
    with gzip.open(S / "caso_integral_v0.26.0.dmike.gz", "rb") as g, open(ruta, "wb") as f: shutil.copyfileobj(g, f)
    a = Api(); assert a.abrir_proyecto(str(ruta))["error"] is None
    antes = json.dumps(a.proyecto.formatos, sort_keys=True, default=str)
    a.seguimiento(); a.disenos()
    assert json.dumps(a.proyecto.formatos, sort_keys=True, default=str) == antes
    assert all(d["region"] == "no_declarada" for d in a.disenos())                              # marcados, sin invalidar nada
    assert len(a.resultados()) == 17 and all(a.reproducir_resultado(x["uid"])["error"] is None for x in a.resultados())


# ---------- declarar los límites de un diseño existente ----------
def test_declarar_limites_cierra_la_tarea_y_guarda_la_region():
    a = sin_region()
    r = a.declarar_limites_diseno("DIS-Resistencia", "90, 130; 5, 40")
    assert r["error"] is None and r["estado"] == "declarada" and "Región segura de DIS-Resistencia declarada" in r["sesion"][-1]["texto"]
    d = a.disenos()[0]; assert d["region"] == "declarada" and d["limites_seguros"]["Tiempo"] == {"min": 5.0, "max": 40.0}
    assert "auto:limites:DIS-Resistencia" not in ids_tareas(a)
    assert a.declarar_limites_diseno("DIS-Resistencia", "90, 130; 5, 40")["estado"] == "sin_cambios"


def test_declarar_con_puntos_fuera_se_rechaza_y_no_guarda_nada():
    a = sin_region(); antes = json.dumps(a.proyecto.formatos["_disenos"], sort_keys=True)
    r = a.declarar_limites_diseno("DIS-Resistencia", "105, 130; 5, 40")
    assert r["error"] == "limites" and "ya tiene" in r["sesion"][-1]["texto"] and "DIS-Resistencia-R" in r["sesion"][-1]["texto"] and "Temp = 100 fuera de [105, 130]" in r["sesion"][-1]["texto"]
    assert "un diseño existente no se mueve" in r["sesion"][-1]["texto"] and json.dumps(a.proyecto.formatos["_disenos"], sort_keys=True) == antes
    assert a.disenos()[0]["region"] == "no_declarada" and "auto:limites:DIS-Resistencia" in ids_tareas(a)


def test_declarar_valida_el_texto_y_el_diseno():
    a = sin_region()
    for txt, frag in (("90, 130", "se esperaban 4 valores"), ("90, 130; x, 40", "números"), ("130, 90; 5, 40", "mínimo debe ser menor que su máximo")):
        r = a.declarar_limites_diseno("DIS-Resistencia", txt); assert r["error"] == "limites" and frag in r["sesion"][-1]["texto"], txt
    assert a.declarar_limites_diseno("DIS-No-Existe", "0, 1; 0, 1")["error"] == "limites"


def test_cambiar_la_region_queda_en_el_historial():
    a = sin_region(); a.declarar_limites_diseno("DIS-Resistencia", "90, 130; 5, 40")
    assert a.declarar_limites_diseno("DIS-Resistencia", "95, 125; 8, 35")["estado"] == "declarada"
    h = a.proyecto.formatos["_disenos"]["Resistencia"]["historial_limites"]
    assert len(h) == 1 and h[0]["anterior"]["Temp"] == {"min": 90.0, "max": 130.0} and h[0]["nuevo"]["Temp"] == {"min": 95.0, "max": 125.0}
    assert a.declarar_limites_diseno("DIS-Resistencia", "101, 125; 8, 35")["error"] == "limites"       # la nueva región no puede dejar fuera un punto (Temp 100)


def test_diseno_anterior_a_029_declara_su_region_sin_perder_nada(tmp_path):
    ruta = tmp_path / "c.dmike"
    with gzip.open(S / "caso_integral_v0.26.0.dmike.gz", "rb") as g, open(ruta, "wb") as f: shutil.copyfileobj(g, f)
    a = Api(); a.abrir_proyecto(str(ruta)); d = a.disenos()[0]
    info = a.proyecto.formatos["_disenos"][d["clave"]]
    texto = "; ".join(f"{f['bajo'] - 100}, {f['alto'] + 100}" for f in info["factores"])             # una región holgada para el cribado/DCC del caso maestro
    r = a.declarar_limites_diseno(d["design_id"], texto)
    assert r["error"] is None, r["sesion"][-1]["texto"]
    assert a.disenos()[0]["region"] == "declarada" and "design_id" not in a.proyecto.formatos["_disenos"][d["clave"]]       # no se le asigna identidad guardada solo por esto


# ---------- interfaz ----------
def test_interfaz_declarar_limites_desde_diseños_del_proyecto(pagina):
    from playwright.sync_api import expect
    pagina.api.ejecutar_modulo("DISENO-RSM", {**DISENO, "limites_opcionales": True})
    pagina.reload(); pagina.wait_for_selector("body[data-listo='1']"); pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.evaluate("ACCIONES_UI.disenos_dialogo()")
    expect(pagina.locator("#disenos")).to_contain_text("Región segura: no declarada.")
    pagina.click("#disenos button:has-text('Declarar límites seguros')")
    pagina.locator(".dialogo").last.locator("input").fill("105, 130; 5, 40"); pagina.locator(".dialogo").last.locator(".primario").click()
    expect(pagina.locator("#sesion")).to_contain_text("Temp = 100 fuera de [105, 130]")
    pagina.click("#disenos button:has-text('Declarar límites seguros')")                      # el diálogo se reabrió solo tras el rechazo
    pagina.locator(".dialogo").last.locator("input").fill("90, 130; 5, 40"); pagina.locator(".dialogo").last.locator(".primario").click()
    expect(pagina.locator("#disenos")).to_contain_text("Región segura: Temp 90 a 130; Tiempo 5 a 40.")
