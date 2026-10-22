"""E3-6 (Decisión 5 de ESPEC_receta_v2): la región autorizada en el análisis RSM, el optimizador y la ruta de ascenso. Nada se recomienda fuera de la
región ni, en modo real, mientras la región no esté declarada. Datos SINTÉTICOS."""
import csv
from app.api import Api
from app.nucleo import modo as MD, disenos as DIS

BASE = {"nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "respuesta": "Resistencia", "semilla": "7"}


def col(a, n): return a.hoja.indice(n)


def monta(tmp, tipo="ccd", limites="90, 130; 5, 40", demo=False, f=None, **extra):
    """Diseño con las respuestas SINTÉTICAS y = f(T, t) importadas por RunId."""
    a = Api()
    if demo: MD.fijar(a.proyecto, MD.DEMO, MD.DECLARADO)
    p = {**BASE, "tipo": tipo, "alfa": "caras", **extra}
    if limites: p["limites"] = limites
    else: p["limites_opcionales"] = True
    r = a.ejecutar_modulo("DISENO-RSM", p); assert r["error"] is None, r["sesion"][-1]["texto"]
    info = a.proyecto.formatos["_disenos"]["Resistencia"]; ids, _ = DIS.run_ids(a.hoja, info, "Resistencia")
    f = f or (lambda t, ti: 100 - 0.1 * (t - 125) ** 2 - 0.1 * (ti - 20) ** 2)              # máximo en Temp = 125, fuera del cubo
    filas = [["RunId", "version_diseno", "Temp", "Tiempo", "Resistencia"]]
    for i in range(a.hoja.n):
        t = float(a.hoja.columnas[col(a, "Temp")].valor(i)[0]); ti = float(a.hoja.columnas[col(a, "Tiempo")].valor(i)[0])
        filas.append([ids[i], 1, t, ti, f(t, ti) + 0.01 * (i % 3)])
    ruta = tmp / "r.csv"
    with open(ruta, "w", encoding="utf-8", newline="") as fh: csv.writer(fh).writerows(filas)
    assert a.importar_respuestas(str(ruta)).get("error") in (None, "")
    return a


def rsm(a, **p):
    return a.ejecutar_modulo("RSM", {"y": col(a, "Resistencia"), "xs": [col(a, "Temp"), col(a, "Tiempo")], **p})


def interp(r): return " ".join(b["texto"] for b in r["resultado"]["bloques"] if b.get("clase") == "interpretacion")
def avisos(r): return " ".join(r["resultado"]["avisos"])


# ---------- punto estacionario ----------
def test_estacionario_dentro_de_la_region_no_cambia_el_texto(tmp_path):
    a = monta(tmp_path, f=lambda t, ti: 100 - 0.1 * (t - 112) ** 2 - 0.1 * (ti - 18) ** 2)
    r = rsm(a); assert r["error"] is None, r
    assert "queda dentro de la región experimentada" in interp(r) and "fuera de la región autorizada" not in interp(r)


def test_estacionario_fuera_de_la_region_declarada_no_se_recomienda(tmp_path):
    a = monta(tmp_path, limites="95, 122; 5, 40")             # el estacionario (Temp = 125) cae fuera de la región autorizada
    r = rsm(a); assert r["error"] is None
    assert "queda fuera de la región autorizada" in interp(r) and "no se recomienda" in interp(r)
    assert a.proyecto.resultados[-1]["datos"]["modelo_rsm"]["region"]["estado"] == "declarada"


def test_real_sin_region_corre_pero_no_recomienda(tmp_path):
    a = monta(tmp_path, limites=None)
    r = rsm(a); assert r["error"] is None
    assert "no está declarada" in interp(r) and "no una recomendación" in interp(r)
    assert "no se recomiendan parámetros hasta declarar" in avisos(r)
    assert a.proyecto.resultados[-1]["datos"]["modelo_rsm"]["region"]["estado"] == "no_declarada"


def test_demostracion_sin_region_se_comporta_como_antes(tmp_path):
    a = monta(tmp_path, limites=None, demo=True)
    r = rsm(a); assert r["error"] is None
    assert "no se recomiendan parámetros" not in avisos(r) and "no está declarada" not in interp(r)
    assert a.proyecto.resultados[-1]["datos"]["modelo_rsm"]["region"]["estado"] == "no_aplica"


# ---------- ruta de ascenso ----------
def _lineal(a): return rsm(a, modelo="lineal")


def test_ascenso_se_detiene_en_el_limite_y_avisa(tmp_path):
    f = lambda t, ti: 50 + 2 * (t - 110) + 0.5 * (ti - 20)                                         # lineal: sube con Temp
    a = monta(tmp_path, tipo="fact", limites="100, 125; 10, 30", centros="2", f=f)
    r = _lineal(a); assert r["error"] is None
    tabla = next(b for b in r["resultado"]["bloques"] if "ascenso" in (b.get("titulo") or ""))
    temps = [float(x[1].replace(",", ".")) for x in tabla["filas"]]
    assert max(temps) <= 125 + 1e-9 and len(tabla["filas"]) < 6
    assert "se detiene" in avisos(r) and "límites seguros" in avisos(r)


def test_ascenso_dentro_de_la_region_muestra_los_seis_pasos(tmp_path):
    f = lambda t, ti: 50 + 2 * (t - 110) + 0.5 * (ti - 20)
    a = monta(tmp_path, tipo="fact", limites="0, 500; 0, 500", centros="2", f=f)
    r = _lineal(a); tabla = next(b for b in r["resultado"]["bloques"] if "ascenso" in (b.get("titulo") or ""))
    assert len(tabla["filas"]) == 6 and "se detiene" not in avisos(r)


def test_ascenso_sin_region_en_real_no_muestra_la_ruta(tmp_path):
    f = lambda t, ti: 50 + 2 * (t - 110) + 0.5 * (ti - 20)
    a = monta(tmp_path, tipo="fact", limites=None, centros="2", f=f)
    r = _lineal(a); assert r["error"] is None
    assert not any("ascenso" in (b.get("titulo") or "") for b in r["resultado"]["bloques"]) and "no se muestra la ruta de ascenso" in avisos(r)


# ---------- optimizador ----------
def _opt(a, uid=None, **p):
    uid = uid or next(r["uid"] for r in a.proyecto.resultados if r["modulo"] == "RSM")
    return a.ejecutar_modulo("OPTIMIZADOR", {"r1": uid, "meta1": "max", "inf1": 50, "obj1": 100, "peso1": 1, "imp1": 1, **p})


def test_optimizador_sin_region_en_real_no_recomienda(tmp_path):
    a = monta(tmp_path, limites=None); assert rsm(a)["error"] is None
    r = _opt(a); assert r["error"] is None
    t = " ".join(b.get("texto", "") for b in r["resultado"]["bloques"] if b.get("tipo") == "texto" or "texto" in b)
    assert "No se recomiendan parámetros" in t and not any((b.get("titulo") or "") == "Ajuste óptimo de los factores" for b in r["resultado"]["bloques"])


def test_optimizador_busca_dentro_de_la_region_declarada(tmp_path):
    a = monta(tmp_path, limites="90, 130; 5, 40", alfa="rotable"); assert rsm(a)["error"] is None
    mr = a.proyecto.resultados[-1]["datos"]["modelo_rsm"]
    sin = _opt(a, region="diseno")                                                                   # búsqueda sobre toda la región del diseño
    t_sin = float(next(b for b in sin["resultado"]["bloques"] if b.get("titulo") == "Ajuste óptimo de los factores")["filas"][0][1])
    mr["region"] = {"estado": "declarada", "limites": [[100, 112], [10, 30]]}                      # región autorizada más estrecha (caso forzado)
    con = _opt(a, region="diseno"); assert con["error"] is None
    fila = next(b for b in con["resultado"]["bloques"] if b.get("titulo") == "Ajuste óptimo de los factores")["filas"][0]
    assert float(fila[1]) <= 112 + 1e-6 and t_sin > 112 and fila[3].split(" a ")[1].replace(",", ".").startswith("112")
    assert "región autorizada" in avisos(con)


def test_optimizador_con_regiones_que_no_se_cruzan_da_un_error_claro(tmp_path):
    a = monta(tmp_path); assert rsm(a)["error"] is None
    a.proyecto.resultados[-1]["datos"]["modelo_rsm"]["region"] = {"estado": "declarada", "limites": [[500, 600], [10, 30]]}
    r = _opt(a); assert r["error"] == "entrada" and "no se cruza con la región autorizada" in r["sesion"][-1]["texto"]


def test_resultado_anterior_sin_region_se_sigue_optimizando(tmp_path):
    a = monta(tmp_path); assert rsm(a)["error"] is None
    a.proyecto.resultados[-1]["datos"]["modelo_rsm"].pop("region")                                  # resultado guardado antes de 0.29
    r = _opt(a); assert r["error"] is None and any((b.get("titulo") or "") == "Ajuste óptimo de los factores" for b in r["resultado"]["bloques"])


# ---------- decisión del usuario (22/10/2026): sin diseño de D-MIKE no se analiza la superficie en un proyecto real ----------
def _pegado(demo=False):
    a = Api()
    if demo: MD.fijar(a.proyecto, MD.DEMO, MD.DECLARADO)
    a.pegar(-1, 0, "A\tB\tY\n" + "\n".join(f"{x}\t{z}\t{10 + x - z * 0.5 + 0.01 * (x * z)}" for x in (1, 2, 3) for z in (1, 2, 3)))
    return a


def test_real_sin_diseno_de_dmike_bloquea_el_analisis_de_superficie_con_la_salida():
    a = _pegado(); r = a.ejecutar_modulo("RSM", {"y": 2, "xs": [0, 1], "modelo": "lineal"})
    t = r["sesion"][-1]["texto"]
    assert r["error"] == "entrada" and "solo corre sobre la respuesta de un diseño creado en D-MIKE" in t and "Importar respuestas del diseño" in t and not a.resultados()


def test_el_bloqueo_no_aplica_en_demostracion():
    a = _pegado(demo=True); assert a.ejecutar_modulo("RSM", {"y": 2, "xs": [0, 1], "modelo": "lineal"})["error"] is None


def test_una_segunda_respuesta_en_las_corridas_del_diseno_si_se_analiza(tmp_path):
    a = monta(tmp_path); a.pegar(-1, len(a.hoja.columnas), "Costo\n" + "\n".join(str(20 + i) for i in range(a.hoja.n)))
    r = a.ejecutar_modulo("RSM", {"y": col(a, "Costo"), "xs": [col(a, "Temp"), col(a, "Tiempo")], "modelo": "lineal"}); assert r["error"] is None, r["sesion"][-1]["texto"]
    assert a.proyecto.resultados[-1]["datos"]["modelo_rsm"]["region"]["estado"] == "declarada"                  # hereda la región del diseño por sus factores


def test_el_optimizador_queda_bloqueado_por_consecuencia():
    a = _pegado(); assert a.ejecutar_modulo("OPTIMIZADOR", {"r1": ""})["error"] == "entrada"
