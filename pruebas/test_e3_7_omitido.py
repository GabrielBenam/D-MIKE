"""E3-7 (ESPEC_flujo_real_dmaic sección 3, criterio 7): omitir cribado, DCC o DOE completo solo con un motivo registrado. Receta: disenos[].omitido =
{que, motivo}; manual: Api.omitir_paso_doe. Una omisión no crea diseño ni tarea de correrlo. Datos SINTÉTICOS."""
import json
from app.api import Api
from app.nucleo import receta as RC
from app import modulos

REG = modulos.cargar()
DISENO = {"tipo": "fact", "nombres": "Temp, Tiempo", "bajos": "100, 10", "altos": "120, 30", "centros": "2", "respuesta": "Resistencia", "semilla": "7",
          "limites": "90, 130; 5, 40"}


def rec(omitido="ninguno", con_diseno=True, minimo="0.28"):
    pasos = []
    if omitido != "ninguno": pasos.append({"id": "crib", "modulo": "DISENO-RSM", "hoja": "Cribado", "respuestas": ["Y"], "parametros": {}, "omitido": omitido})
    if con_diseno: pasos.append({"id": "d1", "modulo": "DISENO-RSM", "hoja": "Corridas", "respuestas": ["Resistencia"], "parametros": dict(DISENO)})
    rc = {"tipo": "dmike-receta", "receta_version": 2, "dmike_minimo": minimo, "modo_proyecto": "real", "id_proyecto": "6f1c2a9e-1b0d-4c7e-9a3a-5d2e8f4b7c19",
          "datos_fijos": {}, "hojas": [{"hoja": "Corridas", "origen_datos": "vacia", "columnas": []}], "disenos": pasos}
    rc["huella"] = RC.huella_receta({k: v for k, v in rc.items() if k != "huella"}); return rc


def archivo(tmp, rc):
    ruta = tmp / "r.json"; ruta.write_text(json.dumps(rc), encoding="utf-8"); return str(ruta)


def avance(a, tmp):
    ruta = tmp / "av.json"; assert a.exportar_avance(str(ruta))["error"] is None
    return json.loads(ruta.read_text(encoding="utf-8"))


OK = {"que": "cribado", "motivo": "Hay 3 factores conocidos por 12 años de historial; se va directo al DCC."}


# ---------- validar ----------
def test_omitido_sin_motivo_o_con_que_invalido_se_rechaza():
    for o, frag in (({"que": "cribado", "motivo": ""}, "falta el motivo"), ({"que": "cribado", "motivo": "   "}, "falta el motivo"), ({"que": "cribado"}, "falta el motivo"),
                    ({"que": "otro", "motivo": "x"}, "«que» debe ser uno de"), ("texto", "debe ser un objeto")):
        e = RC.validar(rec(o), REG, "0.29.0"); assert any(frag in x for x in e), (o, e)


def test_omitido_valido_no_exige_limites_ni_parametros():
    assert RC.validar(rec(OK, con_diseno=False, minimo="0.29"), REG, "0.29.0") == []          # el paso omitido no crea diseño: no lleva región


# ---------- receta ----------
def test_la_receta_registra_la_omision_y_no_crea_diseno_ni_tarea(tmp_path):
    a = Api(); r = a.ejecutar_receta(archivo(tmp_path, rec(OK, con_diseno=False))); assert r["error"] is None, r
    om = a.omisiones(); assert len(om) == 1 and om[0]["id"] == "crib" and om[0]["que"] == "cribado" and om[0]["motivo"] == OK["motivo"] and om[0]["origen"] == "receta"
    assert not a.proyecto.formatos.get("_disenos") and a.hoja.n == 0
    assert not any("crib" in str(t.get("id")) for t in a.proyecto.formatos.get("_tareas") or [])


def test_omitir_el_cribado_y_crear_el_diseno_siguiente(tmp_path):
    a = Api(); assert a.ejecutar_receta(archivo(tmp_path, rec(OK)))["error"] is None
    assert len(a.omisiones()) == 1 and a.disenos()[0]["design_id"] == "DIS-Resistencia"


def test_aplicar_la_receta_otra_vez_no_duplica_la_omision(tmp_path):
    a = Api(); ruta = archivo(tmp_path, rec(OK, con_diseno=False)); a.ejecutar_receta(ruta)
    a.ejecutar_receta(ruta, modo="actualizar"); assert len(a.omisiones()) == 1


# ---------- manual ----------
def test_omitir_manual_exige_motivo_y_queda_registrado():
    a = Api()
    r = a.omitir_paso_doe("cribado", "  "); assert r["error"] == "omitir" and "escribe el motivo" in r["sesion"][-1]["texto"] and a.omisiones() == []
    assert a.omitir_paso_doe("rsm", "x")["error"] == "omitir"
    r = a.omitir_paso_doe("dcc", "El proceso ya está en su óptimo conocido"); assert r["error"] is None and r["estado"] == "omitido"
    assert a.omisiones()[0]["que"] == "dcc" and a.omisiones()[0]["origen"] == "usuario" and a._sucio
    assert a.omitir_paso_doe("dcc", "El proceso ya está en su óptimo conocido")["estado"] == "sin_cambios" and len(a.omisiones()) == 1


def test_la_omision_se_guarda_y_se_abre_con_el_proyecto(tmp_path):
    a = Api(); a.omitir_paso_doe("doe", "Mejora directa sin DOE: cambio de proveedor documentado")
    from app.nucleo import archivo as AR
    ruta = str(tmp_path / "p.dmike"); AR.guardar(ruta, a.hoja, a.proyecto, "0.28.0")
    b = Api(); assert b.abrir_proyecto(ruta)["error"] is None and b.omisiones()[0]["motivo"].startswith("Mejora directa")


# ---------- paquete de avance ----------
def test_el_paquete_lleva_que_se_omitio_pero_no_el_motivo(tmp_path):
    a = Api(); a.ejecutar_receta(archivo(tmp_path, rec(OK)))
    pkg = avance(a, tmp_path)
    assert pkg["omisiones"] == [{"id": "crib", "estado": "omitido", "que": "cribado"}] and OK["motivo"] not in json.dumps(pkg, ensure_ascii=False)
    assert [d["id"] for d in pkg["disenos"]] == ["d1"] and pkg["estado_ruta"] == "DOE disenado"           # el paso omitido no cuenta como diseño
    assert RC.huella_receta({k: v for k, v in pkg.items() if k != "huella"}) == pkg["huella"]


def test_sin_omisiones_el_paquete_no_trae_la_clave(tmp_path):
    a = Api(); a.ejecutar_receta(archivo(tmp_path, rec(con_diseno=True)))
    assert "omisiones" not in avance(a, tmp_path)
