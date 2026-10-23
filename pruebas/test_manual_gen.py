"""Generador del manual (herramientas/manual): sin rutas absolutas ajenas al repositorio y mismo PDF desde cualquier directorio."""
import re, shutil, subprocess, sys
from pathlib import Path
import pytest

RAIZ = Path(__file__).resolve().parent.parent
MANUAL = RAIZ / "herramientas" / "manual"
ENTORNO_AJENO = "/home/" + "claude"            # partido para que esta prueba no se encuentre a sí misma
ABS = re.compile(re.escape(ENTORNO_AJENO) + r"|/mnt/(?:user-data|project)|(?<![\w:.])/tmp/|[A-Za-z]:\\\\")


def test_manual_sin_rutas_absolutas():
    archivos = [f for f in MANUAL.rglob("*") if f.is_file() and f.suffix in (".py", ".json", ".md", ".txt", ".html") and "salida" not in f.parts]
    assert {f.name for f in archivos} >= {"gen.py", "textos.json", "README.md"}
    malos = [f"{f.relative_to(RAIZ)}:{n}: {l.strip()[:90]}" for f in archivos for n, l in enumerate(f.read_text(encoding="utf-8").splitlines(), 1) if ABS.search(l)]
    assert malos == []
    assert subprocess.run(["git", "grep", "-l", ENTORNO_AJENO], cwd=RAIZ, capture_output=True, text=True).stdout == ""      # en todo el repositorio


def _generar(cwd, salida):
    return subprocess.run([sys.executable, str(MANUAL / "gen.py"), "--salida", str(salida)], cwd=cwd, capture_output=True, text=True, timeout=600)


@pytest.mark.interfaz
def test_manual_mismo_pdf_desde_distintos_directorios(tmp_path):
    pytest.importorskip("markdown", reason="falta el paquete markdown (requirements-dev.txt)")
    if not (shutil.which("pdfinfo") and shutil.which("pdftotext")): pytest.skip("falta poppler-utils (pdfinfo, pdftotext)")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p: p.chromium.launch().close()
    except Exception as e: pytest.skip(f"sin navegador de Playwright ({str(e).splitlines()[0][:60]})")
    textos = []
    for nombre, cwd in (("a", RAIZ), ("b", MANUAL)):
        r = _generar(cwd, tmp_path / nombre)
        assert r.returncode == 0, r.stderr[-600:]
        pdf = next((tmp_path / nombre).glob("D-MIKE_Manual_de_uso_v*.pdf"))
        assert pdf.stat().st_size > 100_000 and not (tmp_path / nombre / "_pasada1.pdf").exists()
        n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
        textos.append((n, subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout))
    assert textos[0] == textos[1] and textos[0][0] > 50
    assert "Sección no generada" not in textos[0][1] and textos[0][0] > 120      # manual completo, no parcial


def test_manual_sin_entradas_se_detiene_con_mensaje(tmp_path):
    r = subprocess.run([sys.executable, str(MANUAL / "gen.py"), "--entradas", str(tmp_path), "--salida", str(tmp_path / "s")], capture_output=True, text=True, timeout=120)
    if "No module named" in r.stderr: pytest.skip("faltan dependencias del generador")
    assert r.returncode != 0 and "Faltan entradas" in r.stderr and "paso_a_paso.md" in r.stderr and "--permitir-faltantes" in r.stderr


def test_generar_svgs_produce_las_figuras_que_usa_el_manual(tmp_path):
    """svgs.json trae las 10 figuras que gen.py inserta en la sección 6 (módulo, k-ésimo resultado, j-ésima gráfica) y es reproducible."""
    import json
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    for destino in (a, b):
        r = subprocess.run([sys.executable, str(MANUAL / "generar_svgs.py"), "--salida", str(destino)], capture_output=True, text=True, timeout=300)
        if "No module named" in r.stderr: pytest.skip("faltan dependencias del programa")
        assert r.returncode == 0, r.stderr[-500:]
    assert a.read_bytes() == b.read_bytes()
    sv = json.loads(a.read_text(encoding="utf-8"))
    usadas = [("MSA-VAR", 0, 0), ("SPC", 0, 0), ("CAPACIDAD", 0, 0), ("PARETO", 0, 0), ("ANOVA", 0, 0), ("FACTORIAL", 0, 0), ("RSM", 0, 1), ("RSM", 1, 1), ("OPTIMIZADOR", 0, 0), ("CAPACIDAD", 1, 0)]
    for mod, k, j in usadas:
        assert sv[mod][k]["svg"][j].lstrip().startswith("<svg") and len(sv[mod][k]["huella"]) == 64, (mod, k, j)
    assert "dc:date" not in a.read_text(encoding="utf-8")


@pytest.mark.interfaz
def test_manual_completo_sin_permitir_faltantes(tmp_path):
    pytest.importorskip("markdown", reason="falta el paquete markdown (requirements-dev.txt)")
    if not (shutil.which("pdfinfo") and shutil.which("pdftotext")): pytest.skip("falta poppler-utils")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p: p.chromium.launch().close()
    except Exception as e: pytest.skip(f"sin navegador de Playwright ({str(e).splitlines()[0][:60]})")
    ent = tmp_path / "entradas"; ent.mkdir()
    shutil.copy(MANUAL / "entradas" / "D-MIKE_caso_integral_paso_a_paso.md", ent)           # el glosario sale de la raíz y svgs.json se genera solo
    r = subprocess.run([sys.executable, str(MANUAL / "gen.py"), "--entradas", str(ent), "--salida", str(tmp_path / "s")], capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-600:]
    assert "ADVERTENCIA" not in r.stdout and (ent / "svgs.json").is_file()
    pdf = next((tmp_path / "s").glob("*.pdf"))
    texto = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    assert "Sección no generada" not in texto and "6.10 Notas de rigor" in texto and "A3: formato de una hoja" in texto
    assert (tmp_path / "s" / "manual.html").read_text(encoding="utf-8").count("<figure>") == 10


# ---------- concordancia documental (Entrega 5): lo que el manual dice debe existir en el programa ----------
def _rutas_del_manual():
    import json, html
    t = json.load(open(MANUAL / "textos.json", encoding="utf-8"))
    for k, v in t.items():
        for m in re.finditer(r'<span class="ruta">(.*?)</span>', v):
            yield k, html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
    for f in _fichas().values():                                                      # «Ubicación en D-MIKE» (punto 4) de las fichas escritas
        for r in _rutas_en_texto(f["puntos"][4][1]): yield f["id"], r


def test_las_rutas_del_manual_existen_en_el_menu():
    """Cada ruta «Pestaña › … › Botón…» del manual debe existir en el menú real (app/nucleo/menus.py), que es lo que ve el usuario."""
    sys.path.insert(0, str(RAIZ))
    from app.nucleo.menus import MENUS
    por_menu = {m: {re.sub(r"\s*\((?:Ctrl|Alt|F\d)[^)]*\)$", "", n).strip().rstrip("…").strip() for n, _ in items if not n.startswith("§")} for m, items in MENUS}
    # botones dentro de diálogos o ventanas: no son entradas del menú
    DIALOGO = {"Declarar límites seguros", "Auditar diseño", "Omitir cribado, DCC o DOE", "Terminar la mejora sin DOE", "Plan de confirmación", "Comparar", "Historial de cambios", "Segundo DOE desde"}
    fallos = []
    for k, ruta in _rutas_del_manual():
        partes = [p.strip() for p in ruta.split("›")]
        if len(partes) < 2 or partes[0] not in por_menu: continue                       # solo se comprueban las rutas que empiezan en un menú conocido
        ultimo = partes[-1].rstrip("…").strip()
        if ultimo not in por_menu[partes[0]] and ultimo not in DIALOGO: fallos.append((k, ruta))
    assert not fallos, fallos


def test_el_manual_trae_la_guia_del_proyecto_real_y_las_novedades_de_la_0_29():
    import json
    t = json.load(open(MANUAL / "textos.json", encoding="utf-8"))
    s5 = t["s5"]
    for frag in ("5.8 Guía del proyecto real", "Límites seguros", "RunId", "registrar una versión nueva", "atómica", "Auditar diseño", "Plan de confirmación", "no respaldado", "región no declarada"):
        assert frag in s5, frag
    assert "20 tipos" in t["s3"] and "design_id" in s5 and "5.8" in (MANUAL / "gen.py").read_text(encoding="utf-8")


# ---------- Lote 0: fichas de 15 puntos, tipos, ejemplos, capturas e índices ----------
import json
sys.path.insert(0, str(MANUAL))
ENT = MANUAL / "entradas"


def _catalogo():
    from app.api import VERSION
    return json.loads((RAIZ / "proyecto" / "catalogo" / f"catalogo_dmike_{VERSION}.json").read_text(encoding="utf-8"))


def _fichas():
    import fichas
    return fichas.cargar_fichas(ENT / "fichas")


def _menus():
    sys.path.insert(0, str(RAIZ))
    from app.nucleo.menus import MENUS
    return MENUS


def _rutas_en_texto(texto):
    """Rutas «Pestaña › [Grupo ›] Botón» que aparecen en un texto de ficha (cada elemento termina en punto, punto y coma, dos puntos, flecha o fin)."""
    pestanas = "|".join(re.escape(m) for m, _ in _menus())
    elem = r"[^›.;:\n()]+?(?:\([^)]*\))?"
    for m in re.finditer(rf"(?<![\wÁ-ú])((?:{pestanas})(?: › {elem})+?)(?=\s*(?:[.;:,)]|\n|$))", texto):
        yield re.sub(r"\s*\((?:Ctrl|Alt|F\d)[^)]*\)\s*$", "", m.group(1)).strip().rstrip("…").strip()


def test_tipos_ficha_cubre_todo_el_catalogo():
    """R-T2: tipos_ficha.json trae exactamente los módulos del catálogo y cada tipo es uno de los cuatro; sigue las reglas de R-T1."""
    import fichas
    cat = _catalogo()["modulos"]; tipos = fichas.cargar_tipos(ENT / "tipos_ficha.json")
    assert set(tipos) == {m["id"] for m in cat} and len(tipos) == 92
    assert set(tipos.values()) <= {"interfaz", "analisis", "formato", "gestion"}
    from app.modulos import cargar
    R = cargar()
    for m in cat:
        t = tipos[m["id"]]
        if m["ruta"].startswith("Gestión"): assert t == "gestion", m["id"]
        elif getattr(R.get(m["id"]), "SIN_RESULTADO", False): assert t == "interfaz", m["id"]       # operaciones de datos que no abren resultado
        elif m["tipo"] == "formato": assert t == "formato", m["id"]
        else: assert t == "analisis", m["id"]
    assert {i for i, t in tipos.items() if t == "interfaz"} == {"ALEATORIOS", "APILAR", "CALCULADORA", "DUPLICADOS", "ORDENAR", "PATRON", "RECODIFICAR", "REEMPLAZAR"}


def test_fichas_piloto_tienen_15_puntos_y_su_tipo():
    import fichas
    F = _fichas(); tipos = fichas.cargar_tipos(ENT / "tipos_ficha.json")
    assert set(F) >= {"ESTADISTICOS", "REEMPLAZAR", "CHARTER"}
    for k, f in F.items():
        assert k in tipos and f["tipo"] == tipos[k], k
        assert sorted(f["puntos"]) == list(range(1, 16)) and f["ejemplos"], k
        assert fichas.pendientes_de_redaccion(f) == [], k             # las tres piloto están completas


def test_parser_de_fichas_rechaza_lo_incompleto(tmp_path):
    import fichas
    (tmp_path / "X.md").write_text("---\nid: X\ntipo: analisis\n---\n\n## 1. Propósito\ntexto\n", encoding="utf-8")
    with pytest.raises(fichas.FichaInvalida, match="1 a 15"): fichas.leer_ficha(tmp_path / "X.md")
    (tmp_path / "Y.md").write_text("---\nid: Z\ntipo: analisis\n---\n", encoding="utf-8")
    with pytest.raises(fichas.FichaInvalida, match="no coincide"): fichas.leer_ficha(tmp_path / "Y.md")
    (tmp_path / "W.md").write_text("---\nid: W\ntipo: raro\n---\n", encoding="utf-8")
    with pytest.raises(fichas.FichaInvalida, match="fuera de"): fichas.leer_ficha(tmp_path / "W.md")


def test_ejemplos_de_las_fichas_coinciden_con_lo_que_ejecuta_el_programa():
    """R-F3: cada bloque «ejemplo» se ejecuta con la API real (APPDATA temporal) y coincide con «esperado»."""
    import fichas
    n = 0
    for f in _fichas().values():
        for i, v in enumerate(fichas.verificar_ficha(f), 1):
            assert v["ok"], (f["id"], i, v["diferencias"]); n += 1
    assert n >= 5


def test_un_ejemplo_alterado_no_coincide(tmp_path):
    """R-F3 (--estricto): si se altera un valor esperado, el verificador lo detecta, en análisis, en operación de hoja y en formato."""
    import fichas, copy
    F = _fichas()
    e = copy.deepcopy(F["ESTADISTICOS"]["ejemplos"][0]); e["esperado"]["fila"][3] = "12"
    v = fichas.verificar_ejemplo(e); assert not v["ok"] and "fila esperada" in v["diferencias"][0]
    e = copy.deepcopy(F["REEMPLAZAR"]["ejemplos"][0]); e["pasos"][0]["esperado_mensaje"] = "Reemplazos hechos: 99."
    assert not fichas.verificar_ejemplo(e)["ok"]
    e = copy.deepcopy(F["REEMPLAZAR"]["ejemplos"][0]); e["esperado_hoja"]["1"][0] = "12,5"
    assert not fichas.verificar_ejemplo(e)["ok"]
    e = copy.deepcopy(F["CHARTER"]["ejemplos"][0]); e["esperado_texto"] = "Ahorro total esperado: 1"
    assert not fichas.verificar_ejemplo(e)["ok"]
    e = copy.deepcopy(F["ESTADISTICOS"]["ejemplos"][0]); e["modulo"] = "NO-EXISTE"
    assert not fichas.verificar_ejemplo(e)["ok"]                                   # un ejemplo roto se reporta, no revienta


def test_ejemplos_no_tocan_los_datos_del_usuario(tmp_path, monkeypatch):
    import fichas, os
    monkeypatch.setenv("APPDATA", str(tmp_path / "usuario"))
    fichas.verificar_ficha(_fichas()["REEMPLAZAR"])
    assert os.environ["APPDATA"] == str(tmp_path / "usuario") and not (tmp_path / "usuario").exists()


def test_outputs_reales_y_su_comparacion_con_el_punto_9():
    """R-F4: lista tablas y columnas ejecutadas y avisa si el punto 9 escrito a mano difiere."""
    import fichas, copy
    f = _fichas()["ESTADISTICOS"]; real = fichas.outputs_reales(f, fichas.verificar_ficha(f))
    t = next(b for b in real["bloques"] if b["tipo"] == "tabla")
    assert t["titulo"] == "Estadísticos descriptivos" and len(t["columnas"]) == 19 and t["columnas"][0] == "Grupo" and t["columnas"][-1] == "Moda"
    assert not any(b["tipo"] == "grafica" for b in real["bloques"])
    assert fichas.comparar_punto9(f, real) == []
    g = copy.deepcopy(f); g["puntos"][9] = ("Outputs", g["puntos"][9][1].replace("Rango, RIC", "RIC, Rango"))
    assert any("fuera de orden" in a for a in fichas.comparar_punto9(g, real))
    g["puntos"][9] = ("Outputs", "Una tabla «Otra cosa».")
    assert any("no aparece en el punto 9" in a for a in fichas.comparar_punto9(g, real))
    r = _fichas()["REEMPLAZAR"]; assert fichas.outputs_reales(r, fichas.verificar_ficha(r))["mensajes"] == ["Reemplazos hechos: 3."]


def test_rutas_de_las_fichas_existen_en_el_menu_con_su_grupo():
    """Cada «Pestaña › Grupo › Botón» de cualquier punto de las fichas escritas existe tal cual en app/nucleo/menus.py."""
    grupos, entradas = {}, {}
    for tab, ops in _menus():
        g = ""
        for n, a in ops:
            if n.startswith("§"): g = n[1:]; grupos.setdefault(tab, set()).add(g); continue
            nombre = re.sub(r"\s*\((?:Ctrl|Alt|F\d)[^)]*\)$", "", n).strip().rstrip("…").strip()
            entradas.setdefault(tab, {})[nombre] = g
    vistas = 0
    for f in _fichas().values():
        for n, (_, texto) in f["puntos"].items():
            for ruta in _rutas_en_texto(texto):
                p = [x.strip() for x in ruta.split(" › ")]; tab = p[0]; vistas += 1
                if len(p) == 3: assert entradas[tab].get(p[2]) == p[1], (f["id"], n, ruta)
                else: assert p[1] in grupos[tab] or p[1] in entradas[tab], (f["id"], n, ruta)
    assert vistas >= 6


def test_indice_por_pregunta_esquema_y_rutas_validas():
    """R-I2: esquema de indice_preguntas.json; cada ID de «ruta» existe en el catálogo; las 3 entradas son EJEMPLO DE ESQUEMA."""
    import fichas
    d = json.loads((ENT / "indice_preguntas.json").read_text(encoding="utf-8")); ids = {m["id"] for m in _catalogo()["modulos"]}
    assert fichas.validar_indice_preguntas(d, ids) == [] and len(d["preguntas"]) == 3
    assert all(p["rotulo"] == "EJEMPLO DE ESQUEMA" and 2 <= len(p["ruta"]) <= 4 for p in d["preguntas"])
    malo = {"preguntas": [{**d["preguntas"][0], "ruta": ["ESTADISTICOS", "NO-EXISTE"]}, {**d["preguntas"][1], "ruta": ["SPC"]}, {k: v for k, v in d["preguntas"][2].items() if k != "nivel"}]}
    probs = fichas.validar_indice_preguntas(malo, ids)
    assert len(probs) == 3 and any("NO-EXISTE" in p for p in probs) and any("2 a 4" in p for p in probs) and any("nivel" in p for p in probs)


@pytest.mark.interfaz
def test_capturas_guardas_de_modo_y_selectores(tmp_path):
    """R-C2 y R-C3: un selector inexistente se reporta (no se salta); en modo real nunca se cargan datos sintéticos."""
    pytest.importorskip("playwright")
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("capturas_manual", MANUAL / "capturas.py")      # por ruta: pruebas/capturas.py ya existe y taparía este módulo
    capturas = importlib.util.module_from_spec(spec); spec.loader.exec_module(capturas)
    from playwright.sync_api import sync_playwright
    os.environ["APPDATA"] = str(tmp_path / "ap")
    srv, url = capturas.servidor(RAIZ / "app" / "ui")
    try:
        with sync_playwright() as p:
            try: e = capturas.Escena(p, url, "X", tmp_path)
            except Exception as ex: pytest.skip(f"sin navegador de Playwright ({str(ex).splitlines()[0][:60]})")
            try:
                with pytest.raises(capturas.FalloCaptura, match="no existe"): e.captura(1, "t", "d", 8, [("#no-existe-xyz", "x")])
                e.pegar("a\n1\n2"); e.captura(1, "t", "d", 8, [("#hoja-tabla th.nombre[data-c='0']", "columna")])
                e.captura(2, "t", "d", 8)
                a = e.caps
                assert [c["n"] for c in a] == [1, 2] and all(c["sintetico"] for c in a)
                assert a[0]["sha256"] != a[1]["sha256"]                                    # las anotaciones cambian la imagen; la huella cambia con la pantalla
                assert a[0]["sha256"] == __import__("hashlib").sha256((tmp_path / "X_1.png").read_bytes()).hexdigest()
            finally: e.cerrar()
            real = capturas.Escena(p, url, "R", tmp_path, modo="real")
            try:
                with pytest.raises(capturas.FalloCaptura, match="modo real"): real.pegar("a\n1")
                real.captura(1, "t", "d", 8)
                assert real.caps[0]["sintetico"] is False                                  # sin etiqueta y sin datos sintéticos
            finally: real.cerrar()
    finally: srv.shutdown()


# ---------- manual completo generado una sola vez para las pruebas de índice, hipervínculos y capturas ----------
def _hay_navegador():
    if not (shutil.which("pdfinfo") and shutil.which("pdftotext")): return "falta poppler-utils"
    try:
        pytest.importorskip("markdown")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p: p.chromium.launch().close()
    except pytest.skip.Exception as e: return str(e)
    except Exception as e: return f"sin navegador de Playwright ({str(e).splitlines()[0][:60]})"
    return None


@pytest.fixture(scope="module")
def manual(tmp_path_factory):
    motivo = _hay_navegador()
    if motivo: pytest.skip(motivo)
    d = tmp_path_factory.mktemp("manual")
    r = subprocess.run([sys.executable, str(MANUAL / "gen.py"), "--salida", str(d), "--estricto"], capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, (r.stdout[-800:], r.stderr[-800:])
    pdf = next(d.glob("D-MIKE_Manual_de_uso_v*.pdf"))
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    textos = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", str(pdf), "-"], capture_output=True, text=True).stdout for i in range(1, n + 1)]
    return {"dir": d, "pdf": pdf, "textos": textos, "html": (d / "manual.html").read_text(encoding="utf-8"), "stdout": r.stdout}


@pytest.mark.interfaz
def test_indice_con_pagina_real_de_cada_encabezado(manual):
    """R-I3: en el índice los apéndices ya no salen en la página 3; cada entrada apunta a la página que contiene su encabezado, después del índice."""
    t = manual["textos"]
    fin_ind = next(i for i, x in enumerate(t, 1) if re.search(r"^\s*Índice por pregunta\s*$", x, re.M) and i > 2)        # primera página después del índice
    entradas = []
    for i in range(2, fin_ind):
        for l in t[i - 1].splitlines():
            m = re.match(r"^\s*(.+?)\s{2,}(\d+)\s*$", l)
            if m: entradas.append((m.group(1).strip(), int(m.group(2))))
    assert len(entradas) >= 120 and all(p >= fin_ind for _, p in entradas)
    por = dict(entradas)
    assert por["8 Apéndice A · Comandos y atajos"] > 100 and por["9 Apéndice B · Glosario"] > por["8 Apéndice A · Comandos y atajos"]
    assert por["8 Apéndice A · Comandos y atajos"] != 3 and por["9 Apéndice B · Glosario"] != 3
    previa = 0
    for etiqueta, p in entradas:                                    # el encabezado real está en la página indicada y el orden es el del documento
        base = re.sub(r"\s+[A-Z0-9-]{3,}$", "", etiqueta)           # quita el ID de módulo que el índice agrega al final de las fichas
        assert re.sub(r"\s+", " ", base[:30]) in re.sub(r"\s+", " ", t[p - 1]), (etiqueta, p)
        assert p >= previa, (etiqueta, p, previa); previa = p
    for tit in ("8 Apéndice A · Comandos y atajos", "9 Apéndice B · Glosario"):
        assert re.search(r"^\s*" + re.escape(tit) + r"\s*$", t[por[tit] - 1], re.M)        # encabezado completo en su página, no una línea de índice (sin número de página)


@pytest.mark.interfaz
def test_hipervinculos_internos_tienen_destino(manual):
    """R-I1: cada href="#x" del manual tiene un elemento con id x; el PDF conserva los vínculos y trae marcadores (outline)."""
    h = manual["html"]
    ids = set(re.findall(r"""\bid=['"]([^'"]+)['"]""", h)); hrefs = re.findall(r"""href=['"]#([^'"]+)['"]""", h)
    assert len(hrefs) >= 130 and not [x for x in set(hrefs) if x not in ids]
    assert {"f-ESTADISTICOS", "f-REEMPLAZAR", "f-CHARTER", "s5.8", "s8", "s9", "sq"} <= ids
    pypdf = pytest.importorskip("pypdf", reason="pypdf no es dependencia del proyecto: no se comprueban vínculos ni marcadores del PDF")
    r = pypdf.PdfReader(str(manual["pdf"]))
    enlaces = sum(1 for pg in r.pages for a in (pg.get("/Annots") or []) if a.get_object().get("/Subtype") == "/Link")
    assert enlaces >= 130 and len(r.outline) >= 10


@pytest.mark.interfaz
def test_fichas_piloto_en_el_manual(manual):
    h, t = manual["html"], "\n".join(manual["textos"])
    assert h.count("class='ficha larga'") == 3 and h.count("Ficha automática, sin revisión pedagógica.") == 89         # las demás siguen apareciendo, con su leyenda
    assert h.count("<p class='verif ok'>Ejemplo verificado con D-MIKE 0.29.0") == 3 and "class='verif mal'" not in h and t.count("Ejemplo verificado con D-MIKE 0.29.0") == 3
    assert h.count("<p class='pend'>") == 35                          # solo los 35 del esqueleto del capítulo 7: las fichas piloto no tienen puntos pendientes
    for k in ("ESTADISTICOS", "REEMPLAZAR", "CHARTER"):
        assert all(f"id='p-{k}-{n}'" in h for n in range(1, 16)), k
    assert "Salida ejecutada" in h and "Referencia técnica automática" in h
    rep = json.loads((manual["dir"] / "fichas_reporte.json").read_text(encoding="utf-8"))
    assert rep["no_coinciden"] == [] and rep["avisos"] == [] and rep["sin_ficha_escrita"] == 89


@pytest.mark.interfaz
def test_capturas_del_manual(manual):
    """R-C1 a R-C4: cada captura citada existe, tiene título, descripción, leyenda y huella; las de demostración llevan la etiqueta; sin rutas absolutas."""
    cj = manual["dir"] / "capturas" / "capturas.json"; txt = cj.read_text(encoding="utf-8")
    d = json.loads(txt); caps = d["capturas"]
    assert len(caps) == 10 and not ABS.search(txt) and "/home/" not in txt and "file://" not in txt
    import hashlib
    for c in caps:
        f = manual["dir"] / "capturas" / c["archivo"]
        assert re.fullmatch(r"[A-Z0-9-]+_\d+\.png", c["archivo"]) and f.is_file() and f.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        assert c["titulo"].strip() and c["descripcion"].strip() and c["sintetico"] is True and 1 <= c["punto"] <= 15
        assert c["sha256"] == hashlib.sha256(f.read_bytes()).hexdigest()
        assert [x["n"] for x in c["leyenda"]] == list(range(1, len(c["leyenda"]) + 1))
        assert f"id='cap-{c['id']}-{c['n']}'" in manual["html"] and c["descripcion"] in manual["html"].replace("&#x27;", "'")
    assert d["etiqueta"] == "SINTÉTICO / NO EMPRESARIAL" and manual["html"].count("<figure class='captura'") == 10
    assert any(p["id"] == "ESTADISTICOS" for p in d["pendientes"])                      # diálogos nativos de Windows: pendientes de validación


@pytest.mark.interfaz
def test_capitulos_6_y_7_y_apendices_renumerados(manual):
    h = manual["html"]
    assert "<h1 id=\"s6\">6 Caso maestro demostrativo (sintético)</h1>" in h and "SINTÉTICO / NO EMPRESARIAL, reproducible con la receta del caso integral" in h
    assert "<h1 id=\"s7\">7 Proyecto real guiado</h1>" in h and "<h1 id=\"s8\">8 Apéndice A" in h and "<h1 id=\"s9\">9 Apéndice B" in h
    cap7 = h.split('<h1 id="s7">')[1].split('<h1 id="s8">')[0]
    assert re.findall(r"<h2 id='s7\.\d'>(7\.\d [^<]+)</h2>", cap7) == ["7.1 Definir (D)", "7.2 Medir (M)", "7.3 Analizar (A)", "7.4 Mejorar (I)", "7.5 Controlar (C)"]
    assert cap7.count("[REDACCIÓN PENDIENTE]") == 35 and "href='#s5.8'" in cap7
    for tit in ("Qué sabemos", "Qué falta", "Por qué este método", "Qué produjo", "Qué significa", "Qué decisión sigue", "Qué hacemos si el resultado es inesperado"): assert cap7.count(f">{tit}</h4>") == 5
    assert "caso_integral" not in cap7 and "129.42" not in cap7 and "108.63" not in cap7                       # sin datos ni resultados sintéticos en el esqueleto
    assert "EJEMPLO DE ESQUEMA" in h


@pytest.mark.interfaz
def test_estricto_falla_si_un_ejemplo_no_coincide(manual, tmp_path):
    """R-F3: --estricto sale con error cuando se altera un valor esperado; sin --estricto solo avisa."""
    ent = tmp_path / "entradas"; (ent / "fichas").mkdir(parents=True)
    shutil.copy(ENT / "D-MIKE_caso_integral_paso_a_paso.md", ent)
    for f in (ENT / "fichas").glob("*.md"): shutil.copy(f, ent / "fichas")
    p = ent / "fichas" / "ESTADISTICOS.md"; p.write_text(p.read_text(encoding="utf-8").replace('"Todos","5","0","11"', '"Todos","5","0","12"'), encoding="utf-8")
    cmd = [sys.executable, str(MANUAL / "gen.py"), "--entradas", str(ent), "--salida", str(tmp_path / "s"), "--capturas", str(manual["dir"] / "capturas")]
    r = subprocess.run(cmd + ["--estricto"], capture_output=True, text=True, timeout=900)
    assert r.returncode != 0 and "EJEMPLO NO COINCIDE: ESTADISTICOS ejemplo 1" in r.stdout and "--estricto" in r.stderr
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    assert r.returncode == 0 and "EJEMPLO NO COINCIDE" in r.stdout
    assert "Ejemplo NO coincide con D-MIKE" in subprocess.run(["pdftotext", "-layout", str(next((tmp_path / "s").glob("*.pdf"))), "-"], capture_output=True, text=True).stdout
