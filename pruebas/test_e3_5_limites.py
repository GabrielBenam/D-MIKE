"""E3-5 (Decisión 5 de ESPEC_receta_v2, sección 8, parte A): límites seguros al crear el diseño. La región autorizada es distinta de los niveles bajo y alto:
todo punto fuera de ella se rechaza, axiales incluidos, antes de escribir nada en la hoja. Obligatorios en modo real; opcionales en demostración.
Alternativa solo con α = 1, no nombrada por el curso. Datos SINTÉTICOS."""
import json
from app.api import Api
from app.nucleo import modo as MD, receta as RC

BASE = {"nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "respuesta": "Resistencia", "semilla": "7"}
LINEA_57 = "no nombrado por el curso (el ejemplo de 28_BB, línea 57, es consistente con cubo y axiales en el mismo rango)"


def crea(demo=False, **p):
    a = Api()
    if demo: MD.fijar(a.proyecto, MD.DEMO, MD.DECLARADO)
    return a, a.ejecutar_modulo("DISENO-RSM", {**BASE, **p})


def sin_nada(a): return a.hoja.n == 0 and not a.proyecto.formatos.get("_disenos") and not a.resultados()


def texto(r): return r["sesion"][-1]["texto"]


# ---------- obligatorios en real, opcionales en demostración ----------
def test_real_exige_los_limites_y_no_escribe_nada():
    a, r = crea(tipo="fact")
    assert r["error"] == "entrada" and "En un proyecto real declara los límites seguros" in texto(r) and "no son los niveles bajo y alto" in texto(r) and sin_nada(a)


def test_demostracion_los_deja_opcionales_y_marca_la_region_no_declarada():
    a, r = crea(demo=True, tipo="fact"); assert r["error"] is None
    d = a.disenos()[0]; assert d["region"] == "no_declarada" and d["limites_seguros"] is None
    tabla = next(b for b in r["resultado"]["bloques"] if b.get("titulo") == "Resumen del diseño")
    assert ["Región segura (límites por factor)", "No declarada (opcional en demostración)"] in tabla["filas"]


def test_real_con_limites_guarda_la_region_y_verifica_todos_los_puntos():
    a, r = crea(tipo="ccd", alfa="caras", limites="90, 130; 5, 40"); assert r["error"] is None, texto(r)
    d = a.disenos()[0]; assert d["region"] == "declarada" and d["limites_seguros"] == {"Temp": {"min": 90.0, "max": 130.0}, "Tiempo": {"min": 5.0, "max": 40.0}}
    filas = dict(next(b for b in r["resultado"]["bloques"] if b.get("titulo") == "Resumen del diseño")["filas"])
    assert filas["Región segura (límites por factor)"] == "Temp: 90 a 130; Tiempo: 5 a 40" and "ninguno" in filas["Puntos fuera de la región"]
    assert a.proyecto.formatos["_disenos"]["Resistencia"]["alternativa_axial_en_limites"] is False


def test_un_punto_exactamente_en_el_limite_es_valido():
    a, r = crea(tipo="fact", limites="100, 120; 10, 30"); assert r["error"] is None            # el cubo cae justo en los límites


# ---------- rechazo de todo punto fuera de la región ----------
def test_cubo_fuera_de_la_region_se_rechaza_con_el_punto_y_el_factor():
    a, r = crea(tipo="fact", limites="105, 130; 5, 40")
    assert r["error"] == "entrada" and sin_nada(a)
    t = texto(r)
    assert "sale de la región segura" in t and "punto del cubo" in t and "Temp = 100 fuera de [105, 130]" in t and "No se escribió nada en la hoja" in t
    assert "Ajusta los niveles bajo y alto" in t and "línea 57" not in t                    # la alternativa solo se ofrece al central compuesto


def test_axial_fuera_de_la_region_se_rechaza_aunque_el_cubo_quede_dentro_y_ofrece_la_alternativa():
    a, r = crea(tipo="ccd", alfa="rotable", limites="100, 120; 10, 30")                     # el cubo cabe justo; los axiales rotables (±1.414) no
    t = texto(r); assert r["error"] == "entrada" and sin_nada(a)
    assert "punto axial" in t and "fuera de [100, 120]" in t
    assert LINEA_57 in t and "solo con α = 1" in t and "Rotable, otros valores de α y cualquier otra alternativa no están respaldados por la base" in t


def test_dcc_en_las_caras_con_el_cubo_dentro_es_valido_y_sus_axiales_caen_en_las_caras():
    a, r = crea(tipo="ccd", alfa="caras", limites="100, 120; 10, 30"); assert r["error"] is None, texto(r)
    ts = [a.hoja.columnas[a.hoja.indice("Temp")].valor(i)[2] for i in range(a.hoja.n)]
    assert min(ts) == 100 and max(ts) == 120                                                 # los axiales coinciden con las caras del cubo


def test_box_behnken_y_fraccionado_tambien_se_verifican():
    a, r = crea(tipo="bb", nombres="A, B, C", bajos="1, 1, 1", altos="2, 2, 2", limites="1, 3; 1, 3; 1.5, 3")
    assert r["error"] == "entrada" and "punto de arista (Box-Behnken)" in texto(r) and "C = 1 fuera de [1.5, 3]" in texto(r) and sin_nada(a)
    a, r = crea(tipo="frac", nombres="A, B, C", bajos="1, 1, 1", altos="2, 2, 2", limites="0, 3; 0, 3; 0, 3", fraccion="1")
    assert r["error"] is None


def test_muchos_puntos_fuera_se_resumen():
    a, r = crea(tipo="ccd", alfa="rotable", centros="0", limites="115, 116; 5, 40")
    t = texto(r); assert t.count("fuera de [115, 116]") + t.count("fuera de [5, 40]") == 6 and "(y " in t and "más)" in t       # lista hasta 6 y resume el resto
    assert "en 12 puntos" in t or "en 11 puntos" in t or "en 10 puntos" in t or "en 9 puntos" in t or "en 8 puntos" in t or "en 7 puntos" in t


# ---------- límites inválidos ----------
def test_limites_invalidos():
    for lim, frag in (("90, 130", "se esperaban 4 valores"), ("90, 130; x, 40", "números"), ("130, 90; 5, 40", "mínimo debe ser menor que su máximo"),
                      ("90, 90; 5, 40", "mínimo debe ser menor que su máximo")):
        a, r = crea(tipo="fact", limites=lim); assert r["error"] == "entrada" and frag in texto(r) and sin_nada(a), (lim, texto(r))


# ---------- alternativa de puntos axiales (solo α = 1) ----------
def test_alternativa_usa_los_limites_como_niveles_y_axiales_en_las_caras():
    a, r = crea(tipo="ccd", alfa="rotable", limites="95, 125; 8, 35", limites_como_axiales=True); assert r["error"] is None, texto(r)
    d = a.disenos()[0]; info = a.proyecto.formatos["_disenos"]["Resistencia"]
    assert info["alfa"] == 1.0 and info["alternativa_axial_en_limites"] is True and d["region"] == "declarada"
    assert [(f["bajo"], f["alto"]) for f in info["factores"]] == [(95.0, 125.0), (8.0, 35.0)]      # los límites son los niveles bajo y alto
    ts = [a.hoja.columnas[a.hoja.indice("Temp")].valor(i)[2] for i in range(a.hoja.n)]; assert min(ts) == 95 and max(ts) == 125
    av = " ".join(r["resultado"]["avisos"]); assert LINEA_57 in av
    tabla = next(b for b in r["resultado"]["bloques"] if b.get("titulo") == "Resumen del diseño")["filas"]
    assert any(f[0] == "Alternativa de puntos axiales" and LINEA_57 in f[1] for f in tabla)
    assert "mejor" not in av.lower() and "óptim" not in av.lower() and "rotab" not in av.lower()        # no afirma propiedades que la base no trae


def test_alternativa_solo_aplica_al_dcc_y_exige_los_limites():
    a, r = crea(tipo="fact", limites="90, 130; 5, 40", limites_como_axiales=True)
    assert r["error"] == "entrada" and "solo aplica al diseño central compuesto" in texto(r) and sin_nada(a)
    a, r = crea(demo=True, tipo="ccd", limites_como_axiales=True)
    assert r["error"] == "entrada" and "hay que declararlos" in texto(r) and sin_nada(a)


# ---------- recetas ----------
def receta(tmp, dmike_minimo="0.28", limites=None, modo="real", nombres="Temp, Tiempo"):
    d = {"id": "d1", "modulo": "DISENO-RSM", "hoja": "Corridas", "respuestas": ["Resistencia"],
         "parametros": {**BASE, "tipo": "fact", "nombres": nombres, "centros": "2"}}
    if limites is not None: d["limites_seguros"] = limites
    rc = {"tipo": "dmike-receta", "receta_version": 2, "dmike_minimo": dmike_minimo, "modo_proyecto": modo, "id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c14",
          "datos_fijos": {}, "hojas": [{"hoja": "Corridas", "origen_datos": "vacia", "columnas": []}], "disenos": [d]}
    rc["huella"] = RC.huella_receta({k: v for k, v in rc.items() if k != "huella"})
    ruta = tmp / "r.json"; ruta.write_text(json.dumps(rc), encoding="utf-8"); return str(ruta)


def test_receta_con_limites_seguros_por_factor_los_aplica_en_modo_real(tmp_path):
    a = Api(); r = a.ejecutar_receta(receta(tmp_path, limites={"Temp": {"min": 90, "max": 130}, "Tiempo": {"min": 5, "max": 40}}))
    assert r["error"] is None, texto(r); d = a.disenos()[0]
    assert d["region"] == "declarada" and d["limites_seguros"]["Temp"] == {"min": 90.0, "max": 130.0}


def test_receta_con_limites_que_no_contienen_el_diseno_no_lo_crea(tmp_path):
    a = Api(); r = a.ejecutar_receta(receta(tmp_path, limites={"Temp": {"min": 105, "max": 130}, "Tiempo": {"min": 5, "max": 40}}))
    assert not a.proyecto.formatos.get("_disenos") and any("sale de la región segura" in m["texto"] for m in r["sesion"])


def test_receta_anterior_sin_limites_crea_el_diseno_marcado_region_no_declarada(tmp_path):
    a = Api(); r = a.ejecutar_receta(receta(tmp_path, dmike_minimo="0.26")); assert r["error"] is None, texto(r)
    d = a.disenos()[0]; assert d["region"] == "no_declarada" and d["limites_seguros"] is None and a.hoja.n == 6


def test_receta_con_limites_incompletos_se_rechaza_con_un_mensaje_claro(tmp_path):
    # parte A los ignoraba (el diseño quedaba sin región); desde la parte B `validar` revisa la estructura de limites_seguros y un factor sin su par se rechaza
    a = Api(); r = a.ejecutar_receta(receta(tmp_path, limites={"Temp": {"min": 90, "max": 130}}))
    assert r["error"] == "receta" and "falta un {min, max} numérico para el factor «Tiempo»" in r["sesion"][-1]["texto"] and not a.proyecto.formatos.get("_disenos")


# ---------- interfaz ----------
def test_interfaz_el_dialogo_trae_los_limites_y_la_alternativa(pagina):
    from playwright.sync_api import expect
    pagina.evaluate("document.getElementById('inicio') && document.getElementById('inicio').remove()")
    pagina.click(".menu > button:text-is('Estadística')"); pagina.click("text=Crear diseño de experimentos…")
    expect(pagina.locator(".dialogo input[name='limites']")).to_be_visible(); expect(pagina.locator(".dialogo")).to_contain_text("Límites seguros")
    expect(pagina.locator(".dialogo input[name='limites_como_axiales']")).to_be_visible(); expect(pagina.locator(".dialogo")).to_contain_text("No nombrado por el curso")
    pagina.fill(".dialogo input[name='nombres']", "Temp, Tiempo"); pagina.fill(".dialogo input[name='bajos']", "100, 10"); pagina.fill(".dialogo input[name='altos']", "120, 30")
    pagina.click(".dialogo .primario")                                                      # sin límites en un proyecto real
    expect(pagina.locator(".error-dialogo")).to_contain_text("declara los límites seguros")
