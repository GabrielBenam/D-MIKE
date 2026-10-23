"""Genera el Manual de uso de D-MIKE en PDF. Ver README.md de esta carpeta (comando, entradas y salida).
Todas las rutas son relativas a este archivo o a la raíz del repositorio: corre igual desde cualquier directorio."""
import sys, os, re, json, inspect, html, shutil, argparse, subprocess, markdown
from pathlib import Path

AQUI = Path(__file__).resolve().parent           # herramientas/manual
RAIZ = AQUI.parent.parent                        # raíz del repositorio
sys.path.insert(0, str(RAIZ))
_ap = argparse.ArgumentParser(description="Genera el Manual de uso de D-MIKE en PDF.")
_ap.add_argument("--salida", default=os.environ.get("DMIKE_MANUAL_SALIDA") or str(AQUI / "salida"), help="carpeta de salida (por omisión herramientas/manual/salida)")
_ap.add_argument("--entradas", default=os.environ.get("DMIKE_MANUAL_ENTRADAS") or str(AQUI / "entradas"), help="carpeta con el paso a paso del caso, svgs.json y el glosario (por omisión herramientas/manual/entradas)")
_ap.add_argument("--permitir-faltantes", action="store_true", help="genera el PDF aunque falten esas entradas; las secciones afectadas quedan marcadas como no generadas")
ARGS = _ap.parse_args()
SAL, ENT = Path(ARGS.salida).resolve(), Path(ARGS.entradas).resolve()
SAL.mkdir(parents=True, exist_ok=True)

ENTRADAS = {"caso": (ENT / "D-MIKE_caso_integral_paso_a_paso.md", "paso a paso del caso maestro (sección 6)"),
            "svgs": (ENT / "svgs.json", "gráficas SVG del caso (figuras de la sección 6)"),
            "glosario": (ENT / "08_GLOSARIO.md" if (ENT / "08_GLOSARIO.md").is_file() else RAIZ / "08_GLOSARIO.md", "glosario de la base del curso (apéndice B)")}   # si no está en entradas/, se usa el de la raíz del repositorio
if not ENTRADAS["svgs"][0].is_file():          # svgs.json se deriva de la receta del caso: si no está, se genera (ver generar_svgs.py)
    sys.path.insert(0, str(AQUI)); import generar_svgs
    ENT.mkdir(parents=True, exist_ok=True)
    ENTRADAS["svgs"][0].write_text(json.dumps(generar_svgs.generar(), ensure_ascii=False), encoding="utf-8")
FALTAN = [f"{ruta}  [{que}]" for ruta, que in ENTRADAS.values() if not ruta.is_file()]
FALTAN += [f"{h}  [herramienta del sistema; instala poppler-utils]" for h in ("pdfinfo", "pdftotext") if not shutil.which(h)]
if FALTAN and not ARGS.permitir_faltantes:
    sys.exit("Faltan entradas para generar el manual completo:\n  " + "\n  ".join(FALTAN) +
             "\nColócalas ahí (o usa --entradas) o corre con --permitir-faltantes para generar un PDF parcial. Ver herramientas/manual/README.md.")
if any("poppler" in f for f in FALTAN): sys.exit("Falta poppler-utils (pdfinfo, pdftotext): sin él no se puede numerar el índice.")


def leer_entrada(clave, defecto):
    ruta = ENTRADAS[clave][0]
    return open(ruta, encoding="utf-8").read() if ruta.is_file() else defecto


def no_generada(clave):
    ruta, que = ENTRADAS[clave]
    return f"<p class='lean'>Sección no generada: falta el archivo {E(ruta.name)} ({E(que)}). Este PDF es parcial.</p>"


from app.api import Api, VERSION
from app.modulos import cargar
from app.modulos.formatos import FORMATOS
from app.nucleo.menus import MENUS
from playwright.sync_api import sync_playwright

R = cargar(); A = Api(); INFO = A.info_modulos(); CMD = json.load(open(RAIZ / "app" / "datos" / "comandos.json", encoding="utf-8"))
CMDN = {c["n"].lower().replace("…", ""): c for c in CMD}
LEAN_PEND = {"TAKT", "TIEMPOS", "BALANCE", "MUDAS", "TRABAJO-EST", "VSM", "BALANCE-FUT", "RESULTADOS-LEAN"}
FASE = {"D": "Definir", "M": "Medir", "A": "Analizar", "I": "Mejorar", "C": "Controlar"}
E = lambda t: html.escape(str(t or ""))
TIPO = {"col": "una columna", "cols": "varias columnas", "num": "número", "numero": "número", "texto": "texto", "opcion": "opción", "bool": "casilla", "largo": "texto largo", None: "texto"}
FILTRO = {"num": "numérica", "texto": "de texto", "fecha": "de fechas"}

def limpia(t): return re.sub(r"\{[^{}]*\}", "…", t).replace("\\n", " ").strip()

def fuentes(src):
    pat = r"\d\d_(?:GB|BB)_[A-ZÁÉÍÓÚÑ0-9_]+(?:,? [A-Z][A-Z0-9-]{2,})?|0\d_[A-Z_]+(?:,? [A-Z][A-Z0-9-]{2,})?|PL\d\d(?: [A-Z][A-Z0-9-]{2,})?|PMBOK \d(?:,? [\d.]+)?"
    return sorted(set(m.strip(" ,") for m in re.findall(pat, src)))

def mensajes(src, patron):
    out = []
    for m in re.findall(patron, src):
        t = limpia(m)
        if len(t) > 12 and t not in out: out.append(t)
    return out

def no_respaldado(src):
    frases = re.findall(r'"([^"]*(?:[Nn]o respaldad|GENERAL)[^"]*)"', src)
    return [limpia(f) for f in dict.fromkeys(frases) if len(f) > 20][:3]

def lista(items, vacio="—"): return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>" if items else f"<p class='mut'>{vacio}</p>"

def ficha_analisis(mid, cls, info, etiqueta):
    src = inspect.getsource(cls)
    campos = []
    for c in getattr(cls, "CAMPOS", []):
        t = TIPO.get(c.get("tipo"), c.get("tipo"))
        if c.get("tipo") in ("col", "cols") and c.get("filtro"): t += " " + FILTRO.get(c["filtro"], "")
        extra = []
        if c.get("opciones"): extra.append("opciones: " + ", ".join(E(o[1] if isinstance(o, (list, tuple)) else o) for o in c["opciones"][:8]) + ("…" if len(c["opciones"]) > 8 else ""))
        if c.get("defecto") not in (None, ""): extra.append(f"por omisión {E(c['defecto'])}")
        if c.get("opcional"): extra.append("opcional")
        campos.append(f"<b>{E(c.get('etiqueta') or c['campo'])}</b> — {E(t)}" + (f" ({'; '.join(extra)})" if extra else ""))
    val = mensajes(src, r'ErrorEntrada\(\s*f?"([^"]+)"')[:7]
    tablas = mensajes(src, r'b_tabla\(\s*f?"([^"]+)"')
    graf = src.count("b_grafica(")
    inter = sorted(set(re.findall(r'"g": "([a-z]+)"', src)))
    entrega = [f"Tabla «{E(t)}»" for t in tablas[:8]]
    if graf: entrega.append(f"{graf} gráfica{'s' if graf > 1 else ''}" + (f" (interactivas en la interfaz: {', '.join(inter)})" if inter else " (imagen fija)"))
    entrega.append("Conclusión en lenguaje llano, avisos sobre los datos excluidos y supuestos del análisis")
    return armar(mid, info, etiqueta, "Análisis", campos, val, entrega, fuentes(src), no_respaldado(src),
                 "Botón «Exportar…» del resultado: libro de Excel con tablas (precisión completa), conclusión y gráfica. «Copiar» lleva las tablas al portapapeles. «Repetir con datos actuales» recalcula; «Reproducir versión guardada» rehace el original con su copia congelada.")

def ficha_formato(mid, cls, info, etiqueta):
    src = inspect.getsource(cls)
    cab = [E(c.get("etiqueta")) for c in cls.CABECERA if not c.get("calc") and not c.get("fijo")]
    calc = [E(c.get("etiqueta")) for c in cls.CABECERA if c.get("calc")]
    tabs = []
    for t in cls.TABLAS:
        cap = [E(c.get("etiqueta")) for c in t["columnas"] if not c.get("calc") and not c.get("lectura")]
        cal = [E(c.get("etiqueta")) for c in t["columnas"] if c.get("calc")]
        tabs.append(f"<b>{E(t.get('titulo') or t['id'])}</b>: captura {', '.join(cap) or '—'}" + (f"; calcula {', '.join(cal)}" if cal else ""))
    campos = ([f"<b>Encabezado</b>: {', '.join(cab)}"] if cab else []) + tabs
    val = mensajes(src, r'av\.append\(\s*f?"([^"]+)"')[:7]
    entrega = ([f"Resultados del encabezado: {', '.join(calc)}"] if calc else []) + [f"{len(getattr(cls, 'TABLAS', []))} tablas con cálculo en vivo y marcas de color (bien, alerta, fuera)",
               "Campos numéricos vacíos marcados «pendiente» (no se cuentan como cero)"]
    if "grafica" in src or "_svg(" in src: entrega.append("Gráfica o diagrama del formato")
    nota = getattr(cls, "NOTA", "") or ""
    return armar(mid, info, etiqueta, "Formato", campos, val, entrega, fuentes(src + nota), no_respaldado(src + '"' + nota + '"'),
                 "«Exportar a Excel…»: libro con el encabezado, las tablas y sus cálculos. «Vista dividida» muestra las gráficas a la derecha.", nota)

def armar(mid, info, etiqueta, tipo, campos, val, entrega, fts, nr, exp, nota=""):
    fases = ", ".join(f"{f} ({FASE.get(f, f)})" for f in info.get("fases", [])) or "Herramienta general"
    aviso = "<div class='lean'>Cálculos aún sin verificar contra el ejemplo del curso (PL03): úsalo con criterio hasta la verificación pendiente.</div>" if mid in LEAN_PEND else ""
    h = f"<section class='ficha'><h4>{E(info.get('titulo') or etiqueta)} <span class='id'>{E(mid)}</span></h4>{aviso}"
    h += f"<p class='meta'><b>Ruta:</b> {E(info.get('ruta', ''))} · <b>Tipo:</b> {tipo} · <b>Fase:</b> {E(fases)}</p>"
    if info.get("desc"): h += f"<p>{E(info['desc'])}.</p>"
    h += "<div class='dos'><div><h5>Qué pide</h5>" + lista(campos) + "</div><div><h5>Qué entrega</h5>" + lista(entrega) + "</div></div>"
    if val: h += "<h5>Qué revisa</h5>" + lista([E(v) for v in val])
    if nota: h += f"<h5>Fórmulas y criterios</h5><p class='nota'>{E(nota)}</p>"
    h += "<h5>Fuentes en la base del curso</h5>" + (f"<p class='nota'>{', '.join(E(x) for x in fts)}</p>" if fts else "<p class='mut'>No cita secciones de la base: revisa la nota del resultado.</p>")
    if nr: h += "<h5>Lo que no está respaldado por la base</h5>" + lista([E(x) for x in nr])
    h += f"<h5>Exportación</h5><p>{exp}</p></section>"
    return h

def comando_simple(texto):
    c = CMDN.get(texto.lower().replace("…", "").split(" (")[0])
    d = c["d"] if c else ""; at = c["a"] if c and c["a"] != "—" else ""
    return f"<li><b>{E(texto.replace('…', ''))}</b>{' — ' + E(d) if d else ''}{f' <span class=at>{E(at)}</span>' if at else ''}</li>"

# ---------- sección 4: módulos por pestaña ----------
mod_html, toc4, vistos = [], [], set()
for n, (tab, ops) in enumerate(MENUS, 1):
    sec = f"4.{n}"; toc4.append((sec, tab)); bloque = f"<h2 id='s{sec}'>{sec} {E(tab)}</h2>"
    grupo, simples = None, []
    def cerrar_simples():
        global bloque
        if simples: bloque += "<ul class='simples'>" + "".join(simples) + "</ul>"; simples.clear()
    for texto, acc in ops:
        if texto.startswith("§"):
            cerrar_simples(); bloque += f"<h3>{E(texto[1:])}</h3>"; continue
        if acc and acc.startswith("mod:"):
            mid = acc[4:]; info = INFO.get(mid, {"titulo": texto, "ruta": f"{tab} › {texto}"})
            if mid in vistos: simples.append(f"<li><b>{E(texto)}</b> — mismo módulo descrito en otra pestaña ({E(mid)}).</li>"); continue
            vistos.add(mid); cerrar_simples()
            cls = R.get(mid) or FORMATOS.get(mid)
            if cls is None: simples.append(comando_simple(texto)); continue
            bloque += ficha_formato(mid, cls, info, texto) if mid in FORMATOS else ficha_analisis(mid, cls, info, texto)
        else: simples.append(comando_simple(texto))
    cerrar_simples(); mod_html.append(bloque)

# ---------- caso maestro (del paso a paso, adaptado a la v0.25) ----------
SV = json.loads(leer_entrada("svgs", "{}"))      # sin svgs.json no hay figuras (fig() devuelve vacío)


def construir_caso(md):
    md = md.split("## 2. El caso y el origen de cada dato", 1)[1]
    md = "## 6.1 El caso y el origen de cada dato" + md
    grupo = {}
    for menu, ops in MENUS:
        g = ""
        for t, acc in ops:
            if t.startswith("§"): g = t[1:]; continue
            grupo[(menu, t)] = g; grupo[(menu, t.replace("…", ""))] = g
    def ruta(m):
        p = [x.strip() for x in m.group(1).split("›")]
        if len(p) == 2 and (p[0], p[1]) in grupo: p = [p[0], grupo[(p[0], p[1])], p[1]]
        elif len(p) != 2 or p[0] not in [x for x, _ in MENUS]: return m.group(0)
        return '<span class="ruta">' + " › ".join(p) + "</span>"
    md = re.sub(r"`([^`]*›[^`]*)`", ruta, md)
    ren = {"## 3. Preparar": "## 6.2 Preparar", "## 4. Definir": "## 6.3 Definir", "## 5. Medir": "## 6.4 Medir", "## 6. Analizar": "## 6.5 Analizar", "## 7. Mejorar": "## 6.6 Mejorar",
           "## 8. Controlar": "## 6.7 Controlar", "## 9. Resumen": "## 6.8 Resumen", "## 10. Cómo armar": "## 6.9 Cómo armar", "## 11. Notas de rigor": "## 6.10 Notas de rigor"}
    for a_, b_ in ren.items(): md = md.replace(a_, b_)
    md = md.replace("D-MIKE 0.21.1", f"D-MIKE {VERSION}").replace("«Repetir»", "«Repetir con datos actuales»")
    md = md.replace("**Dos formas de seguirlo.**", "**Novedades en el caso.** Todos los resultados del caso se recalcularon con la versión " + VERSION + ": cada uno guarda su copia congelada y su huella SHA-256 (indicador «Vigente» junto al título), y sus gráficas son interactivas (Estilo y color, Escala original y pestaña «Gráfico»). La forma más rápida de reproducir el caso es abrir la plantilla llena con «Archivo › Abrir proyecto» y elegir «Ejecutar en un proyecto nuevo».\n\n**Dos formas de seguirlo.**")
    def fig(mod, k=0, j=0, pie=""):
        try: s = SV[mod][k]["svg"][j]; h = SV[mod][k]["huella"]
        except (KeyError, IndexError): return ""
        return f"\n<figure>{s}<figcaption>{E(pie)}{' · huella ' + h if h else ''}</figcaption></figure>\n"
    INS = {"### 5.2": fig("MSA-VAR", 0, 0, "Gage R&R del caso"), "### 5.4": fig("SPC", 0, 0, "Carta X̄-R de la línea base"), "### 5.5": fig("CAPACIDAD", 0, 0, "Capacidad de la línea base"),
           "### 6.1": fig("PARETO", 0, 0, "Pareto de defectos"), "### 6.3": fig("ANOVA", 0, 0, "ANOVA por lote de adhesivo"), "### 7.1": fig("FACTORIAL", 0, 0, "Pareto de efectos estandarizados del cribado"),
           "### 7.3": fig("RSM", 0, 1, "Superficie de respuesta de la resistencia"), "### 7.4": fig("RSM", 1, 1, "Superficie de respuesta de la porosidad"), "### 7.5": fig("OPTIMIZADOR", 0, 0, "Optimizador de respuestas"),
           "### 8.2": fig("CAPACIDAD", 1, 0, "Capacidad con el proceso nuevo")}
    lineas, out, pend = md.split("\n"), [], []
    for l in lineas:
        if l.startswith("#"):
            out += pend; pend = []
            for k, v in INS.items():
                if l.startswith(k): pend.append(v)
        out.append(l.replace("### ", "### 6.").replace("### 6.6.", "### 6.") if False else l)
    out += pend
    out = [re.sub(r"^### (\d+)\.(\d+)", lambda m: f"### 6.{int(m.group(1)) - 1}.{m.group(2)}", l) for l in out]   # 5.2 -> 6.4.2, etc.
    caso_html = markdown.markdown("\n".join(out), extensions=["tables"])
    return re.sub(r"<h2>(6\.\d+[^<]*)</h2>", lambda m: f"<h2 id='c{m.group(1).split()[0]}'>{m.group(1)}</h2>", caso_html)


MD_CASO = leer_entrada("caso", None)
caso_html = construir_caso(MD_CASO) if MD_CASO is not None else no_generada("caso")

# ---------- glosario ----------
glo = leer_entrada("glosario", "").split("\n")
glos = [l for l in glo if ":" in l and not l.startswith("#") and len(l) > 10 and not l.startswith("Glosario")]
glo_html = no_generada("glosario") if not ENTRADAS["glosario"][0].is_file() else "".join(f"<p class='glo'><b>{E(l.split(':', 1)[0])}</b>: {E(l.split(':', 1)[1].strip())}</p>" for l in glos)
CTX = {"G": "Global", "H": "Hoja", "F": "Formatos", "R": "Resultados", "T": "Tablero", "P": "Riel DMAIC"}
cmd_html = "<table class='cmd'><thead><tr><th>Comando</th><th>Atajo</th><th>Funciona en</th><th>Estado</th><th>Qué hace</th></tr></thead><tbody>" + "".join(
    f"<tr{' class=sep' if i == 0 or CMD[i - 1]['cat'] != c['cat'] else ''}><td>{'<span class=cat>' + E(c['cat']) + '</span>' if i == 0 or CMD[i - 1]['cat'] != c['cat'] else ''}{E(c['n'])}</td><td class=at>{'' if c['a'] == '—' else E(c['a'])}</td><td>{', '.join(CTX.get(x, x) for x in c['c'])}</td><td>{'Disponible' if c['e'] == 'D' else 'Propuesto'}</td><td>{E(c['d'])}</td></tr>"
    for i, c in enumerate(CMD)) + "</tbody></table>"

TXT = json.load(open(AQUI / "textos.json", encoding="utf-8"))
L10O = open(RAIZ / "app" / "ui" / "logo10_oscuro.svg", encoding="utf-8").read()
TOC = [("1", "Introducción"), ("2", "Trabajo con proyectos"), ("3", "Resultados, gráficas y reglas de cálculo"), ("4", "Módulos por pestaña de la cinta")] + toc4 + \
      [("5", "Recetas y Diagnóstico en línea"), ("5.8", "Guía del proyecto real: DOE progresivo (versión 0.29)"), ("6", "Caso maestro de principio a fin")] + [(k.split()[0], " ".join(k.split()[1:])) for k in re.findall(r"<h2 id='c[^']*'>([^<]*)</h2>", caso_html)] + [("7", "Apéndice A · Comandos y atajos"), ("8", "Apéndice B · Glosario")]
def doc(paginas):
    toc = "".join(f"<li class='{'sub' if '.' in n else ''}'><span>{E(n)} {E(t)}</span><span class='pun'></span><span>{paginas.get(n, '')}</span></li>" for n, t in TOC)
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><style>
@font-face {{ font-family: M; src: url("{(RAIZ / 'app' / 'ui' / 'fuentes' / 'Montserrat.woff2').as_uri()}"); font-weight: 100 900; }}
body {{ margin: 0; font-family: M, sans-serif; color: #2b2620; font-size: 9.6pt; line-height: 1.5; }}
.portada {{ height: 228mm; box-sizing: border-box; background: #1c1916; color: #f1ece4; padding: 26mm 18mm; border-radius: 8px; display: flex; flex-direction: column; justify-content: space-between; break-after: page; }}
.portada svg {{ width: 115mm; height: auto; }} .portada h1 {{ font-size: 32pt; margin: 12mm 0 3mm; color: #f1ece4; border: 0; break-before: auto; }} .portada p {{ color: #c9c0b2; font-size: 12pt; margin: 0 0 2mm; }}
.bandas {{ display: flex; gap: 6px; }} .bandas i {{ width: 16mm; height: 2.4mm; border-radius: 2mm; }}
h1 {{ font-size: 21pt; margin: 0 0 4mm; color: #b3460d; break-before: page; }} h2 {{ font-size: 14.5pt; margin: 8mm 0 3mm; border-top: 2.5px solid #dd5813; padding-top: 2mm; break-after: avoid; }}
h3 {{ font-size: 11.5pt; margin: 5mm 0 2mm; color: #b3460d; break-after: avoid; }} h4 {{ font-size: 11pt; margin: 0 0 1.5mm; }} h5 {{ font-size: 8.6pt; margin: 2.5mm 0 1mm; text-transform: uppercase; letter-spacing: .06em; color: #5f574c; break-after: avoid; }}
p {{ margin: 0 0 2mm; }} ul {{ margin: 0 0 2mm; padding-left: 5mm; }} li {{ margin-bottom: .8mm; }}
.indice {{ list-style: none; padding: 0; font-size: 10pt; }} .indice li {{ display: flex; gap: 6px; padding: 1.2mm 0; }} .indice li.sub {{ padding-left: 7mm; font-size: 9.2pt; color: #5f574c; }} .indice .pun {{ flex: 1; border-bottom: 1px dotted #9b9284; margin-bottom: 4px; }}
.ficha {{ border: 1px solid #e2dcd0; border-radius: 8px; padding: 3mm 4mm; margin: 0 0 4mm; break-inside: avoid-page; }} .ficha .id {{ font-size: 8pt; color: #9a3e0e; background: #fbe8dd; border-radius: 4px; padding: 0 5px; margin-left: 6px; }}
.meta {{ font-size: 8.6pt; color: #5f574c; }} .dos {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; }} .nota {{ font-size: 8.4pt; color: #3b342d; }} .mut {{ color: #8a8174; font-size: 8.6pt; }}
.lean {{ background: #fdecc8; border-radius: 6px; padding: 2mm 3mm; font-size: 8.6pt; margin: 1mm 0 2mm; }}
.simples {{ list-style: none; padding: 0; }} .simples li {{ border-bottom: 1px solid #efe9df; padding: 1mm 0; }} .at {{ color: #b3460d; white-space: nowrap; font-size: 8.4pt; margin-left: 6px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 8.4pt; margin: 2mm 0 4mm; }} th {{ background: #f1ece2; text-align: left; }} th, td {{ padding: 3px 5px; border-bottom: 1px solid #e2dcd0; vertical-align: top; }} tr {{ break-inside: avoid; }}
tr.sep td {{ border-top: 1.5px solid #dd5813; }} .cat {{ display: block; font-size: 7.5pt; font-weight: 800; color: #b3460d; text-transform: uppercase; }}
.ruta {{ background: #fbe8dd; color: #7a2f08; padding: 0 4px; border-radius: 4px; font-weight: 600; }} blockquote {{ margin: 3mm 0; padding: 2mm 4mm; background: #fbe8dd; border-radius: 6px; }} blockquote p {{ margin: 0; }}
figure {{ margin: 3mm 0 4mm; break-inside: avoid; }} figure svg {{ width: 100%; height: auto; max-height: 95mm; }} figcaption {{ font-size: 8.2pt; color: #5f574c; }}
.glo {{ font-size: 9pt; margin-bottom: 1.5mm; }} code {{ background: #f3efe7; padding: 0 3px; border-radius: 3px; }}
</style></head><body>
<section class="portada"><div class="bandas">{"".join(f'<i style="background:{c}"></i>' for c in ("#6b2d0c", "#9a3e0e", "#dd5813", "#f08a4b", "#fbe8dd"))}</div>
<div>{L10O}<h1>Manual de uso</h1><p>D-MIKE versión {VERSION}</p><p>Módulos, recetas y caso maestro de principio a fin</p></div><p style="color:#f08a4b;font-weight:700">Del dato a la decisión, fase por fase.</p></section>
<h1 style="break-before:auto">Contenido</h1><ol class="indice">{toc}</ol>
<h1 id="s1">1 Introducción</h1>{TXT["s1"]}
<h1 id="s2">2 Trabajo con proyectos</h1>{TXT["s2"]}
<h1 id="s3">3 Resultados, gráficas y reglas de cálculo</h1>{TXT["s3"]}
<h1 id="s4">4 Módulos por pestaña de la cinta</h1>{TXT["s4"]}{"".join(mod_html)}
<h1 id="s5">5 Recetas y Diagnóstico en línea</h1>{TXT["s5"]}
<h1 id="s6">6 Caso maestro de principio a fin</h1>{caso_html}
<h1 id="s7">7 Apéndice A · Comandos y atajos</h1><p>{len(CMD)} comandos; «Propuesto» = aún no construido.</p>{cmd_html}
<h1 id="s8">8 Apéndice B · Glosario</h1><p class="mut">Del glosario de la base del curso (08_GLOSARIO). COMP = complemento de literatura estándar.</p>{glo_html}
</body></html>'''
pie = f'<div style="font-family:M,sans-serif;font-size:7.5pt;color:#6f675b;width:100%;padding:0 16mm;display:flex;justify-content:space-between"><span>D-MIKE {VERSION} · Manual de uso</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'
HTML, PASADA1 = SAL / "manual.html", SAL / "_pasada1.pdf"
PDF = SAL / f"D-MIKE_Manual_de_uso_v{VERSION.rsplit('.', 1)[0].replace('.', '')}.pdf"


def render(html_txt, pdf):
    HTML.write_text(html_txt, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); pg.goto(HTML.as_uri()); pg.wait_for_timeout(1500)
        pg.pdf(path=str(pdf), format="Letter", print_background=True, display_header_footer=True, header_template="<span></span>", footer_template=pie, margin={"top": "16mm", "bottom": "16mm", "left": "16mm", "right": "16mm"})
        b.close()


render(doc({}), PASADA1)
# segunda pasada: números de página del índice
paginas = {}
n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(PASADA1)], capture_output=True, text=True).stdout).group(1))
textos = [subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", str(PASADA1), "-"], capture_output=True, text=True).stdout for i in range(1, n + 1)]
for num, tit in TOC:
    clave = f"{num} {tit}"[:40]
    for i, t in enumerate(textos[2:], 3):
        if re.search(r"(^|\n)\s*" + re.escape(clave), t): paginas[num] = i; break
render(doc(paginas), PDF)
PASADA1.unlink(missing_ok=True)
n2 = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True).stdout).group(1))
print(f"{PDF}\n{n2} páginas;", len(paginas), "de", len(TOC), "entradas del índice con página;", len(vistos), "módulos")
for f in FALTAN: print("ADVERTENCIA, falta:", f)
