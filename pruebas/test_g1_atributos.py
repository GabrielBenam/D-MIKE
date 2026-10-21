"""G1: declaración «defectos» contra «unidades defectuosas» en las cartas de atributo y verificación con los valores
de 19_GB_CONTROLAR (SPC-CARTAS-ATRIBUTO, secciones D a G). El curso da los resúmenes (p̄, np̄, c̄, ū), no los datos
crudos: los datos aquí son SINTÉTICOS y construidos para reproducir exactamente esos resúmenes."""
import pytest
from app.api import Api

TODAS = [str(k) for k in range(1, 8)]


def hoja(encabezado, filas):
    a = Api(); a.pegar(-1, 0, encabezado + "\n" + "\n".join("\t".join(map(str, f)) for f in filas)); return a


def corre(a, p):
    r = a.ejecutar_modulo("SPC", {"pruebas": TODAS, **p})
    return r


def limites(res):
    t = next(b for b in res["bloques"] if b.get("titulo", "").startswith("Límites"))
    return t["filas"][0], [t["filas"][0][0]] + [float(x.replace(",", "")) for x in t["filas"][0][1:]]


def parametros(res):
    t = next(b for b in res["bloques"] if b.get("titulo") == "Parámetros estimados")
    return {f[0]: float(f[1].replace(",", "")) for f in t["filas"]}


def test_np_curso_18_83():
    # np̄ = 18.83 con n = 100, 30 subgrupos (sintético): UCL 30.56, LCL 7.10 (19_GB SPC-CARTAS-ATRIBUTO)
    a = hoja("defectuosas", [[18]] * 5 + [[19]] * 25)
    r = corre(a, {"tipo": "np", "cuenta": "defectuosas", "y": 0, "tam": "100"})
    assert r["error"] is None
    _, c = limites(r["resultado"])
    assert round(c[1], 2) == 18.83 and round(c[2], 2) == 30.56 and round(c[3], 2) == 7.10


def test_p_curso_0_1058():
    # p̄ = 0.1058 (sintético: 20 subgrupos de n = 500 con 1,058 defectuosas)
    a = hoja("def\tn", [[52, 500]] * 2 + [[53, 500]] * 18)
    r = corre(a, {"tipo": "p", "cuenta": "defectuosas", "y": 0, "ncol": 1})
    assert r["error"] is None
    assert round(parametros(r["resultado"])["p_barra"], 4) == 0.1058


def test_c_curso_2_75():
    # c̄ = 2.75: UCL 7.725 y LCL 0 (el curso ajusta el LCL negativo a 0)
    a = hoja("defectos", [[2], [3], [4], [2]])
    r = corre(a, {"tipo": "c", "cuenta": "defectos", "y": 0})
    assert r["error"] is None
    _, c = limites(r["resultado"])
    assert round(c[1], 3) == 2.75 and round(c[2], 3) == 7.725 and c[3] == 0


def test_u_curso_0_4825():
    # ū = 0.4825 (sintético: 20 subgrupos de 20 unidades con 193 defectos)
    a = hoja("defectos\tunidades", [[9, 20]] * 7 + [[10, 20]] * 13)
    r = corre(a, {"tipo": "u", "cuenta": "defectos", "y": 0, "ncol": 1})
    assert r["error"] is None
    assert round(parametros(r["resultado"])["u_barra"], 4) == 0.4825


@pytest.mark.parametrize("tipo,cuenta,sugerida", [("c", "defectuosas", "np"), ("u", "defectuosas", "p"),
                                                  ("np", "defectos", "c"), ("p", "defectos", "u")])
def test_declaracion_incoherente_se_rechaza(tipo, cuenta, sugerida):
    a = hoja("x\tn", [[3, 50], [4, 50], [2, 50], [5, 50]])
    r = corre(a, {"tipo": tipo, "cuenta": cuenta, "y": 0, "ncol": 1, "tam": "50"})
    assert r["error"] == "entrada" and f"usa la carta {sugerida}" in r["sesion"][0]["texto"]


def test_sin_declarar_se_pide():
    a = hoja("x", [[3], [4], [2], [5]])
    r = corre(a, {"tipo": "c", "cuenta": "", "y": 0})
    assert r["error"] == "entrada" and "Declara qué cuentas" in r["sesion"][0]["texto"]


def test_resultado_anterior_a_g1_sigue_abriendo():
    # migración: parámetros guardados sin el campo «cuenta» se deducen de la carta y llevan aviso
    a = hoja("x", [[3], [4], [2], [5]])
    r = corre(a, {"tipo": "c", "y": 0})
    assert r["error"] is None and any("anterior a la declaración" in x for x in r["resultado"]["avisos"])
