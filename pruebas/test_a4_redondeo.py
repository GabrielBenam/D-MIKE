"""A4: el redondeo ocurre solo al mostrar. Los valores que un módulo formatea con num() conservan el número exacto
(para exportar y para reproducir); la pantalla muestra el texto redondeado."""
import openpyxl
from app.api import Api
from app.modulos.base import num, b_tabla

SINT = "defectuosos\tn\n" + "\n".join(f"{3 + i % 4}\t{50 + 10 * (i % 3)}" for i in range(20))


def test_num_conserva_el_valor_exacto():
    t = num(0.123456789123, 4)
    assert t == "0.1235" and t.crudo == 0.123456789123
    assert num(7).crudo == 7.0 and num(None) == "—" and num("texto") == "texto"
    b = b_tabla("t", ["a", "b"], [["x", num(2.0 / 3.0, 3)], ["y", 1 / 7]])
    assert b["filas"][0][1] == "0.667" and b["crudas"][0][1] == 2.0 / 3.0 and b["crudas"][1][1] == 1 / 7 and b["crudas"][0][0] is None


def test_exporta_limites_spc_sin_redondeo(tmp_path):
    a = Api(); a.pegar(-1, 0, SINT)
    r = a.ejecutar_modulo("SPC", {"tipo": "p", "cuenta": "defectuosas", "y": 0, "ncol": 1})["resultado"]
    pb = sum(3 + i % 4 for i in range(20)) / sum(50 + 10 * (i % 3) for i in range(20))
    a._elegir = lambda *x, **k: str(tmp_path / "r.xlsx"); a.exportar_resultado(r["uid"])
    valores = [c.value for row in openpyxl.load_workbook(tmp_path / "r.xlsx").active.iter_rows() for c in row if isinstance(c.value, float)]
    assert any(abs(v - pb) < 1e-15 for v in valores)              # p̄ completo, no el texto de 5 decimales
