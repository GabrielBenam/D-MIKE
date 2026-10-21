"""A1: faltante no es cero. Tres estados: valor capturado (el cero es válido), «Sin datos» (queda fuera y avisa) y «N/A» (queda fuera
y no cuenta como faltante). Datos SINTÉTICOS."""
from app.api import Api
from app.nucleo.hoja import Hoja


def api_con(texto):
    a = Api(); a.pegar(-1, 0, texto); return a


def avisos(r): return r["resultado"]["avisos"]


def test_estados_de_celda():
    h = Hoja(); h.pegar(-1, 0, "x\n1\n0\n\nN/A\nsin datos\nabc")
    c = h.columnas[0]
    assert [c.estado(i) for i in range(h.n)] == ["valor", "valor", "sin_datos", "na", "sin_datos", "invalido"]
    assert c.tipo == "num" and c.valor(1)[2] == 0.0                     # el cero tecleado es válido
    assert c.valor(3) == ("N/A", True, None) and c.valor(4) == ("Sin datos", True, None)
    assert h.invalidas() == [(5, 0)]                                    # N/A y Sin datos no se marcan como inválidos


def test_cero_cuenta_y_faltante_no():
    con_cero = api_con("x\n0\n2\n4\n6\n8\n10")
    con_falta = api_con("x\n\n2\n4\n6\n8\n10")
    r0 = con_cero.ejecutar_modulo("ESTADISTICOS", {"y": 0}); r1 = con_falta.ejecutar_modulo("ESTADISTICOS", {"y": 0})
    t0 = dict(zip(r0["resultado"]["bloques"][0]["cabeza"], r0["resultado"]["bloques"][0]["filas"][0]))
    t1 = dict(zip(r1["resultado"]["bloques"][0]["cabeza"], r1["resultado"]["bloques"][0]["filas"][0]))
    assert t0["N"] == "6" and t0["Media"] == "5"                        # 0, 2, 4, 6, 8, 10
    assert t1["N"] == "5" and t1["Media"] == "6"                        # 2, 4, 6, 8, 10: la celda vacía no es cero


def test_faltante_genera_aviso_y_na_no():
    a = api_con("x\ty\n1\t1\n2\t\n3\tN/A\n4\t4\n5\t5\n6\t6")
    r = a.ejecutar_modulo("CORREL", {"vars": [0, 1]})
    assert r["error"] is None
    av = avisos(r)
    assert any("Sin datos" in x and "C2" in x and "fila" in x and "no se cuentan como cero" in x for x in av)
    est = r["resultado"]["datos"]["estados_entrada"]["C2 y"]
    assert est == {"sin_datos": 1, "na": 1}
    assert any("N/A (no aplica)" in b.get("texto", "") for b in r["resultado"]["bloques"] if b["tipo"] == "texto")
    assert not any("N/A" in x for x in av)                              # N/A no es aviso de faltante


def test_na_solo_sin_aviso():
    a = api_con("x\n1\n2\nN/A\n4\n5")
    r = a.ejecutar_modulo("ESTADISTICOS", {"y": 0})
    assert not any("Sin datos" in x for x in avisos(r))


def test_muestras_independientes_de_distinto_tamano_no_avisan():
    a = api_con("a\tb\n1\t5\n2\t6\n3\t7\n4\t\n5\t\n6\t\n7\t")
    from app.modulos.base import auditar_estados
    assert auditar_estados(a.hoja, [0, 1], independientes=True)[0] == []
    assert len(auditar_estados(a.hoja, [0, 1], independientes=False)[0]) == 1      # emparejadas: 4 vacíos en b


def test_na_en_columna_de_texto_y_tipo_de_columna():
    h = Hoja(); h.pegar(-1, 0, "t\nA\nN/A\nB\nN/A")
    assert h.columnas[0].tipo == "texto" and h.columnas[0].estado(1) == "na"
    h2 = Hoja(); h2.pegar(-1, 0, "n\nN/A\nN/A\n3\n4")                  # N/A no cuenta para decidir el tipo
    assert h2.columnas[0].tipo == "num" and h2.invalidas() == []


# ---------- formatos: vacío no es cero ----------
def test_charter_ahorro_muestra_su_base():
    a = Api()
    d = a.abrir_formato("CHARTER")["datos"]
    d["tablas"]["objetivos"] = [{"ctq": "tiempo", "ahorro": "100"}, {"ctq": "errores", "ahorro": ""}, {"ctq": "costo", "ahorro": "0"}]
    r = a.guardar_formato("CHARTER", d)
    c = r.get("calculo") or r
    txt = str(c)
    assert "Ahorro total esperado: 100" in txt and "2 de 3 objetivos" in txt and "sin ahorro capturado" in txt


def test_cinco_s_total_con_su_base():
    a = Api()
    d = a.abrir_formato("CINCO-S")["datos"]
    for f, c in zip(d["tablas"]["s"], ["3", "4", "", "", ""]): f["calif"] = c
    r = a.guardar_formato("CINCO-S", d)
    assert "7 de 8 (88%)" in str(r) and "2 de 5 S calificadas" in str(r)
