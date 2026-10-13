"""Calculadora de columnas y utilidades de datos. Datos SINTÉTICOS."""
import math
import pytest
from app.api import Api


@pytest.fixture
def a():
    x = Api(); x.pegar(-1, 0, "tiempo\tpeso unidad\tgrupo\n10\t2\tA\n20\t4\tB\n30\t6\tA\n40\tabc\tB"); return x


def col(a, nombre): return [a.hoja.columnas[a.hoja.indice(nombre)].valor(i)[0] for i in range(a.hoja.n)]


def test_formulas_basicas(a):
    assert a.ejecutar_modulo("CALCULADORA", {"dest": "r", "expr": "tiempo / 10 + C1 ** 2 / 100"})["error"] is None
    assert col(a, "r") == ["2", "6", "12", "20"]
    a.ejecutar_modulo("CALCULADORA", {"dest": "l", "expr": "LOG10('tiempo') + REDONDEAR(RAIZ(tiempo); 2)"})
    assert col(a, "l")[0] == str(round(1 + 3.16, 12))
    r = a.ejecutar_modulo("CALCULADORA", {"dest": "z", "expr": "'peso unidad' * 2"})
    assert col(a, "z") == ["4", "8", "12", ""] and "1 filas quedaron vacías" in r["sesion"][0]["texto"]


def test_columnas_funciones_y_aggregados(a):
    a.ejecutar_modulo("CALCULADORA", {"dest": "c", "expr": "tiempo - PROMEDIO(tiempo)"})
    assert col(a, "c") == ["-15", "-5", "5", "15"]
    a.ejecutar_modulo("CALCULADORA", {"dest": "e", "expr": "ESTAND(tiempo)"})
    assert math.isclose(float(col(a, "e")[0]), -15 / math.sqrt(500 / 3))
    a.ejecutar_modulo("CALCULADORA", {"dest": "d", "expr": "DIF(tiempo)"}); assert col(a, "d") == ["", "10", "10", "10"]
    a.ejecutar_modulo("CALCULADORA", {"dest": "ac", "expr": "ACUM(tiempo)"}); assert col(a, "ac") == ["10", "30", "60", "100"]
    a.ejecutar_modulo("CALCULADORA", {"dest": "rt", "expr": "RETRASO(tiempo; 2)"}); assert col(a, "rt") == ["", "", "10", "20"]
    a.ejecutar_modulo("CALCULADORA", {"dest": "rg", "expr": "RANGO(tiempo)"}); assert col(a, "rg") == ["1", "2", "3", "4"]
    a.ejecutar_modulo("CALCULADORA", {"dest": "s", "expr": "SI(tiempo > 25; 1; 0)"}); assert col(a, "s") == ["0", "0", "1", "1"]
    a.ejecutar_modulo("CALCULADORA", {"dest": "f", "expr": "FILA()"}); assert col(a, "f") == ["1", "2", "3", "4"]


def test_calculadora_rechaza_codigo_y_errores(a):
    for e in ("__import__('os').system('x')", "tiempo.real", "[1,2]", "open('a')", "tiempo +", "FOO(tiempo)", "'no existe' + 1", "grupo + 1", ""):
        r = a.ejecutar_modulo("CALCULADORA", {"dest": "x", "expr": e})
        assert r["error"] == "entrada", e
    assert a.ejecutar_modulo("CALCULADORA", {"dest": "", "expr": "1+1"})["error"] == "entrada"


def test_patron_aleatorios_recodificar_apilar_duplicados():
    a = Api()
    a.ejecutar_modulo("PATRON", {"dest": "p", "lista": "1:3", "cada": "2", "veces": "2"})
    assert col(a, "p") == ["1", "1", "2", "2", "3", "3", "1", "1", "2", "2", "3", "3"]
    a.ejecutar_modulo("PATRON", {"dest": "g", "lista": "A, B", "cada": "6"}); assert col(a, "g")[:7] == ["A"] * 6 + ["B"]
    a.ejecutar_modulo("ALEATORIOS", {"dest": "n", "n": "12", "dist": "normal", "a": "10", "b": "2", "semilla": "5"})
    v1 = col(a, "n"); b = Api(); b.ejecutar_modulo("PATRON", {"dest": "p", "lista": "1:12"})
    b.ejecutar_modulo("ALEATORIOS", {"dest": "n", "n": "12", "dist": "normal", "a": "10", "b": "2", "semilla": "5"}); assert col(b, "n") == v1
    for d, pa, pb in (("uniforme", "2", "5"), ("enteros", "2", "5"), ("exponencial", "2", "1"), ("weibull", "2", "5"), ("binomial", "10", "0.5"),
                      ("poisson", "3", "1"), ("lognormal", "0", "1")):
        assert a.ejecutar_modulo("ALEATORIOS", {"dest": d, "n": "5", "dist": d, "a": pa, "b": pb, "semilla": "1"})["error"] is None, d
    assert a.ejecutar_modulo("ALEATORIOS", {"dest": "x", "n": "5", "dist": "normal", "a": "0", "b": "-1"})["error"] == "entrada"
    a.ejecutar_modulo("RECODIFICAR", {"col": a.hoja.indice("g"), "mapa": "A=0; b=1"}); assert col(a, "g_rec")[0] == "0" and a.hoja.columnas[a.hoja.indice("g_rec")].tipo == "num"
    a.ejecutar_modulo("APILAR", {"cols": [a.hoja.indice("p"), a.hoja.indice("n")], "dest": "todo", "origen": "de"})
    assert len(col(a, "todo")) >= 24 and col(a, "de")[0] == "p" and col(a, "de")[12] == "n"
    c = Api(); c.pegar(-1, 0, "k\n1\n2\n1\n3\n2"); c.ejecutar_modulo("DUPLICADOS", {"cols": [0]}); assert col(c, "Duplicado") == ["0", "0", "1", "0", "1"]


def test_deshacer_de_calculadora_y_rangos(a):
    a.ejecutar_modulo("CALCULADORA", {"dest": "r", "expr": "tiempo * 2"})
    assert a.hoja.indice("r") is not None
    a.deshacer(); assert a.hoja.indice("r") is None
    a.borrar_rango(0, 0, 1, 1); assert col(a, "tiempo")[:2] == ["", ""] and col(a, "grupo")[0] == "A"
    a.deshacer(); assert col(a, "tiempo")[0] == "10"
    a.rellenar(0, 0, 3, 0, "abajo"); assert col(a, "tiempo") == ["10"] * 4
    a.rellenar(0, 0, 1, 1, "derecha"); assert col(a, "peso unidad")[:2] == ["10", "10"]
    assert a.texto_rango(-1, 0, 1, 1).startswith("tiempo\tpeso unidad\n10\t10")
    a.eliminar_filas(1, 2); assert a.hoja.n == 2
    a.eliminar_columnas(1, 2); assert len(a.hoja.columnas) == 1


def test_filtro_oculta_y_excluye_de_analisis():
    a = Api(); a.pegar(-1, 0, "g\ty\n" + "\n".join(f"{'AB'[i % 2]}\t{i}" for i in range(20)))
    r = a.filtrar([{"col": 0, "op": "=", "valor": "A"}])
    assert r["error"] is None and r["hoja"]["visibles"] == list(range(0, 20, 2)) and "10 de 20" in r["sesion"][0]["texto"]
    res = a.ejecutar_modulo("ESTADISTICOS", {"y": 1})["resultado"]
    assert res["bloques"][0]["filas"][0][1] == "10"                             # N = 10, no 20
    assert a.filtrar([{"col": 1, "op": ">=", "valor": "x"}])["error"] == "filtro"
    a.filtrar([{"col": 0, "op": "=", "valor": "B"}, {"col": 1, "op": ">", "valor": "10"}])
    assert a.hoja.estado()["visibles"] == [11, 13, 15, 17, 19]
    a.deshacer(); assert a.hoja.estado()["visibles"] == list(range(0, 20, 2))     # el filtro también se deshace
    assert a.filtrar([])["hoja"]["visibles"] is None


def test_editar_envia_delta_y_modificado():
    a = Api(); a.pegar(-1, 0, "x\n1\n2"); a._sucio = False
    r = a.editar(0, 0, "7")
    assert "hoja" not in r and r["delta"] == {"f": 0, "c": 0, "texto": "7", "valida": True} and a.modificado()
    r = a.editar(0, 0, "abc"); assert r["delta"]["valida"] is False
    assert "hoja" in a.editar(5, 0, "9")                                          # crece la hoja: estado completo
