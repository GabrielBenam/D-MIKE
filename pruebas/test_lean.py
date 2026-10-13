"""Verificación de los cálculos Lean contra 09_EJEMPLOS_CURSO."""
import math
from app.modulos import lean as L


def test_oee_curso_pdf():
    # EJ-OEE-CURSO: 480 min, paro 30, muerto 60, 2 pz/min, 650 piezas, 600 buenas -> 87%, 83%, 92%, 66.7%
    r = L.oee(480, 30, 60, 2, 650, 50)
    assert (r["disponible"], r["operativo"]) == (450, 390)
    assert round(r["disponibilidad"] * 100) == 87 and round(r["eficiencia"] * 100) == 83 and round(r["calidad"] * 100) == 92
    assert round(r["oee"] * 100, 1) == 66.7 and math.isclose(r["oee"], 300 / 450)


def test_oee_tablero_por_hora():
    # EJ-TABLERO-OEE: 77.2%, 39.7% y 87.4%; disponibilidad 80%, 41.7% y 91.7%
    horas = [(60, 10, 10, 5, 195, 2), (60, 0, 35, 5, 120, 1), (60, 0, 5, 7, 370, 3)]
    r = [L.oee(*h) for h in horas]
    assert [round(x["oee"] * 100, 1) for x in r] == [77.2, 39.7, 87.4]
    assert [round(x["disponibilidad"] * 100, 1) for x in r] == [80.0, 41.7, 91.7]


def test_takt():
    assert L.takt_simple(720, 45) == 16                       # EJ-TAKT
    r = L.takt_curso([1000] * 12, 20, 8, 2, 30)               # sintético: 57,600 - 3,600 = 54,000 s / 50 por día
    assert r["tiempo_disponible_s"] == 54000 and r["takt_s"] == 1080


def test_kanban_did():
    # EJ-KANBAN-DID: promedio 1,054, s 121, 2 semanas, 1 ubicación, contenedor 50 -> 243 por semana, 11 contenedores.
    # La base escribe 543 piezas «aproximadamente»; el cálculo sin redondeos intermedios da 542.3.
    r = L.kanban(1054, 121, 2, 1, 50)
    assert round(r["demanda_semanal"]) == 243 and round(r["variacion"] * 100, 1) == 11.5
    assert abs(r["piezas"] - 543) < 1.5 and r["contenedores"] == 11


def test_mantenimiento_did():
    r = L.mantenimiento(1000, 5, 10, 5)                       # EJ-MTBF-DID: 200 h, 2 h, 99.0%
    assert r["mtbf"] == 200 and r["mttr"] == 2 and round(r["disp_inherente"] * 100, 1) == 99.0
