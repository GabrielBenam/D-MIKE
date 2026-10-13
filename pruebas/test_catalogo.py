from app.nucleo.catalogo import Catalogo, MVP, FASES


def test_catalogo_completo():
    c = Catalogo()
    assert c.version == "1.3" and len(c.modulos) == 62


def test_mvp_existe_en_catalogo():
    c = Catalogo()
    assert len(MVP) == 10 and all(m in c.modulos for m in MVP)


def test_por_fase_respeta_fases_del_arbol():
    c = Catalogo(); pf = c.por_fase()
    assert list(pf) == [f for f, _ in FASES]
    for f, mods in pf.items():
        for m in mods:
            assert f in c.info(m["id"])["fases"]          # árbol o complementario (v0.20)
    # un módulo con varias fases aparece en cada una (CORRIDA: M y C)
    assert any(m["id"] == "CORRIDA" for m in pf["M"]) and any(m["id"] == "CORRIDA" for m in pf["C"])
