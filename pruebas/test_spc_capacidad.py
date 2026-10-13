"""Verificación del motor SPC y de capacidad contra 19_GB_CONTROLAR y 16_GB (ejemplos del curso)."""
import math, random
import pytest
from app.modulos import spc as S, capacidad as C


def test_constantes_reproducen_tabla_del_curso():
    # 19_GB SPC-CONSTANTES: A2 y D4 (y D3 de 7 a 10) para n = 2 a 10
    a2 = {2: 1.881, 3: 1.023, 4: 0.729, 5: 0.577, 6: 0.483, 7: 0.419, 8: 0.373, 9: 0.337, 10: 0.308}
    d4 = {2: 3.27, 3: 2.57, 4: 2.28, 5: 2.11, 6: 2.00, 7: 1.92, 8: 1.86, 9: 1.82, 10: 1.78}
    d3 = {7: 0.08, 8: 0.14, 9: 0.18, 10: 0.22}
    for n in range(2, 11):
        assert S.a2(n) == a2[n] and S.d4(n) == d4[n] and S.d3(n) == d3.get(n, 0.0)
        assert abs(3 / (S.D2[n] * math.sqrt(n)) - a2[n]) <= 0.0015          # d2 [GENERAL] coherente con el A2 del curso
        assert abs(1 + 3 * S.D3T[n] / S.D2[n] - d4[n]) <= 0.006
    assert S.E2_IMR == 2.66 and S.d4(2) == 3.27 and round(3 / S.D2[2], 2) == 2.66


def test_ejemplo_xr_chemical():
    # SPC-CONSTANTES: x̿ = 63.50, R̄ = 2.05, n = 5 -> 64.68, 62.32, 4.32 y 0
    xbb, rb, n = 63.50, 2.05, 5
    assert round(xbb + S.a2(n) * rb, 2) == 64.68 and round(xbb - S.a2(n) * rb, 2) == 62.32
    assert abs(S.d4(n) * rb - 4.32) < 0.006 and S.d3(n) == 0        # 2.11 x 2.05 = 4.3255; el curso escribe 4.32
    # y por el camino completo, con subgrupos sintéticos que dan exactamente esos valores
    sub = [[63.5 - 1.025, 63.5, 63.5, 63.5, 63.5 + 1.025]] * 12
    cartas, info = S.carta_xr(sub)
    assert round(cartas[0]["ucl"][0], 2) == 64.68 and abs(cartas[1]["ucl"][0] - 4.32) < 0.006


def test_ejemplo_np_y_c():
    # SPC-CARTAS-ATRIBUTO: np̄ = 18.83 con n = 100 -> 30.56 y 7.10; c̄ = 2.75 -> 7.725 y 0
    npb, n = 18.83, 100; s = math.sqrt(npb * (1 - npb / n))
    assert round(npb + 3 * s, 2) == 30.56 and round(npb - 3 * s, 2) == 7.10
    cartas, _ = S.carta_c([2, 3, 4, 2])                      # c̄ = 2.75
    assert round(cartas[0]["ucl"][0], 3) == 7.725 and cartas[0]["lcl"][0] == 0


def test_carta_p_limites_variables():
    cartas, info = S.carta_p([5, 10, 3], [50, 100, 25])
    assert math.isclose(info["p_barra"], 18 / 175) and len(set(cartas[0]["ucl"])) == 3


def test_imr_y_pruebas():
    random.seed(1)
    x = [10 + random.gauss(0, 1) for _ in range(30)]                     # sintéticos
    cartas, info = S.carta_imr(x)
    assert math.isclose(cartas[1]["ucl"][0], S.d4(2) * info["mr_barra"])
    x2 = x[:20] + [x[19] + 0.5 * (i + 1) for i in range(7)] + [30]
    v = S.pruebas(S.carta_imr(x2, k=20)[0][0])
    assert 1 in v[len(x2) - 1] and any(5 in t for t in v.values())          # punto fuera y tendencia
    racha = [0.5] * 9
    c = {"puntos": racha, "cl": [0] * 9, "ucl": [3] * 9, "lcl": [-3] * 9, "sigma": [1] * 9}
    assert 4 in S.pruebas(c)[8]
    estr = [0.1, -0.1] * 8
    c = {"puntos": estr, "cl": [0] * 16, "ucl": [3] * 16, "lcl": [-3] * 16, "sigma": [1] * 16}
    assert 6 in S.pruebas(c)[14] and 4 not in S.pruebas(c).get(14, [])
    mezcla = [1.5, -1.5] * 4
    c = {"puntos": mezcla, "cl": [0] * 8, "ucl": [3] * 8, "lcl": [-3] * 8, "sigma": [1] * 8}
    assert 7 in S.pruebas(c)[7]
    zona_a = [0, 2.5, 2.4]
    c = {"puntos": zona_a, "cl": [0] * 3, "ucl": [3] * 3, "lcl": [-3] * 3, "sigma": [1] * 3}
    assert 2 in S.pruebas(c)[2]


def test_capacidad_chelsea():
    # 16_GB CAP-NIVEL-SIGMA: media 165.2, s 5.484, LIE 155, LSE 180 -> Pp 0.76, Ppk 0.62, sigma LP 1.86
    r = C.indices(165.2, 5.484, 5.484, 155, 180)
    assert round(r["Pp"], 2) == 0.76 and round(r["Ppk"], 2) == 0.62 and round(r["sigma_lp"], 2) == 1.86
    assert round(r["sigma_lp"] + 1.5, 2) == 3.36 and C.clasificar(r["Ppk"]) == "incapaz"
    u = C.indices(10, 1, 1, lse=13)
    assert u["Cp"] is None and u["Cpk"] == 1.0 and u["ppm_C"]["inf"] == 0
