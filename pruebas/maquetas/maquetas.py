"""Maquetas estáticas de los tipos de vista del MVP (datos sintéticos, sin cálculo verificado).
Se dibujan sobre la ventana real del incremento 1 reemplazando el área central."""
import sys, random, statistics
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(RAIZ))
import http.server, functools, threading
from playwright.sync_api import sync_playwright
from app.api import Api

SAL = Path(__file__).resolve().parent
random.seed(7)
filas = []
for i in range(14):
    cond = "Con" if i % 2 else "Sin"; op = "Op1" if i % 4 < 2 else "Op2"
    tam = random.randint(4, 18)
    t = round(tam * (1.6 if cond == "Sin" else 1.1) + random.uniform(-2, 2), 1)
    err = random.randint(0, 3 if cond == "Sin" else 1)
    filas.append([f"2026-10-{5 + i // 3:02d}", f"U-{i + 1:03d}", cond, op, tam, t, err,
                  random.choice(["Símbolo", "Cota", "Nota"]) if err else ""])
filas[6][5] = "12,5 min"  # celda inválida a propósito

AVISO = '<div style="position:absolute;right:16px;bottom:12px;background:#fbe8dd;color:#9a3d0d;padding:3px 10px;border-radius:5px;font-size:11.5px;font-weight:600;z-index:20">Maqueta, datos sintéticos</div>'
CAMPO = lambda et, v, iny=False: f'<label style="display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:var(--tinta-suave)">{et}<span style="font-size:12.5px;color:var(--tinta);border:1px solid var(--linea);border-radius:5px;padding:5px 8px;min-width:170px;background:{"#f6f3ed" if iny else "#fff"}">{v}</span></label>'


def tabla_hoja(cols, tipos, roles, datos):
    h = '<table><thead><tr class="num"><th class="fila"></th>' + "".join(f"<th>C{j+1}{tipos[j]}</th>" for j in range(len(cols))) + "</tr>"
    h += '<tr class="nom"><th class="fila"></th>' + "".join(f'<th style="color:var(--tinta);font-weight:600">{c}</th>' for c in cols) + "</tr>"
    h += '<tr class="nom"><th class="fila" style="top:46px"></th>' + "".join(f'<th style="top:46px;font-size:11px;color:var(--acento);font-weight:500">{r}</th>' for r in roles) + "</tr></thead><tbody>"
    for i, f in enumerate(datos):
        h += f'<tr><th class="fila">{i+1}</th>'
        for j, v in enumerate(f):
            mal = isinstance(v, str) and tipos[j] == "" and v and not v.replace(".", "").isdigit()
            est = "color:#c0392b;background:#fdecea" if mal else ("text-align:left" if tipos[j] else "")
            h += f'<td style="{est}">{v}</td>'
        h += "</tr>"
    return h + "</tbody></table>"


def vista_hoja():
    cols = ["fecha", "unidad_id", "condicion", "operador", "tamano_unidad", "tiempo", "errores", "tipo_error"]
    tipos = ["-D", "-T", "-T", "-T", "", "", "", "-T"]
    roles = ["id", "id", "factor", "bloque", "covariable", "respuesta", "respuesta", "factor"]
    cab = f'<div style="display:flex;gap:14px;padding:10px 12px;border-bottom:1px solid var(--linea);background:var(--papel)">{CAMPO("Proyecto","Proyecto de prueba",True)}{CAMPO("Responsable","Persona de prueba",True)}{CAMPO("Instrumento","Cronómetro y revisión")}{CAMPO("Inicio de captura","2026-10-05")}</div>'
    return f'<div class="hoja-marco" style="position:relative">{AVISO}<div class="hoja-titulo"><span>Hoja de recolección de datos</span><span class="celda-activa">C6, fila 7: "12,5 min" no es un número y no entra en los cálculos</span></div>{cab}<div class="hoja">{tabla_hoja(cols, tipos, roles, filas)}</div></div>'


def svg_caja():
    g = {"Sin": [f[5] for f in filas if f[2] == "Sin" and isinstance(f[5], float)],
         "Con": [f[5] for f in filas if f[2] == "Con" and isinstance(f[5], float)]}
    y = lambda v: 250 - v * 7
    s = '<svg viewBox="0 0 420 290" width="420" height="290" style="font-family:Montserrat;font-size:11px">'
    for k in range(0, 35, 5):
        s += f'<line x1="50" x2="400" y1="{y(k)}" y2="{y(k)}" stroke="#eee8dd"/><text x="42" y="{y(k)+4}" text-anchor="end" fill="#6f675b">{k}</text>'
    for n, (nom, v) in enumerate(g.items()):
        q1, me, q3 = statistics.quantiles(v, n=4); x = 130 + n * 160
        s += f'<line x1="{x}" x2="{x}" y1="{y(max(v))}" y2="{y(min(v))}" stroke="#2b2620"/>'
        s += f'<rect x="{x-40}" y="{y(q3)}" width="80" height="{y(q1)-y(q3)}" fill="#fbe8dd" stroke="#dd5813" stroke-width="1.5"/>'
        s += f'<line x1="{x-40}" x2="{x+40}" y1="{y(me)}" y2="{y(me)}" stroke="#dd5813" stroke-width="2.5"/>'
        s += f'<text x="{x}" y="272" text-anchor="middle" fill="#2b2620" font-weight="600">{nom}</text>'
    return s + '<text x="14" y="140" transform="rotate(-90 14 140)" text-anchor="middle" fill="#6f675b">tiempo</text></svg>'


def vista_dialogo():
    fondo = vista_hoja().replace(AVISO, "")
    sel = lambda et, v: f'<div style="display:flex;flex-direction:column;gap:4px;font-size:12px;color:var(--tinta-suave)">{et}<div style="border:1px solid var(--linea);border-radius:5px;padding:6px 8px;color:var(--tinta);background:#fff">{v}</div></div>'
    lista = "".join(f'<div style="padding:4px 8px;{"background:#fbe8dd;border-radius:4px" if c=="C6 tiempo" else ""}">{c}</div>' for c in ["C5 tamano_unidad", "C6 tiempo", "C7 errores"])
    dlg = f'''<div style="position:absolute;inset:0;background:rgba(43,38,32,.25);display:grid;place-items:center;z-index:30">
    <div style="width:560px;background:#fff;border-radius:8px;box-shadow:0 12px 40px rgba(43,38,32,.25);padding:18px 20px">
      <div style="font-weight:700;font-size:14px;margin-bottom:14px">Diagrama de caja</div>
      <div style="display:grid;grid-template-columns:180px 1fr;gap:16px">
        <div style="border:1px solid var(--linea);border-radius:5px;padding:6px;font-size:12.5px"><div style="color:var(--tinta-suave);font-size:11.5px;margin-bottom:4px">Columnas numéricas</div>{lista}</div>
        <div style="display:flex;flex-direction:column;gap:12px">{sel("Respuesta","C6 tiempo")}{sel("Agrupar por","C3 condicion")}{sel("Separar por (opcional)","C4 operador")}
        <label style="font-size:12.5px"><input type="checkbox" checked> Mostrar puntos individuales</label></div></div>
      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:18px">
        <button style="font:inherit;padding:6px 14px;border:1px solid var(--linea);background:#fff;border-radius:5px">Cancelar</button>
        <button style="font:inherit;padding:6px 14px;border:0;background:#dd5813;color:#fff;border-radius:5px;font-weight:600">Aceptar</button></div></div></div>'''
    return f'<div style="position:relative;flex:1;display:flex;flex-direction:column">{AVISO}{fondo}{dlg}</div>'


def vista_resultado():
    fila = lambda *c: "<tr>" + "".join(f'<td style="padding:4px 10px;border-bottom:1px solid var(--rejilla);text-align:{"left" if i==0 else "right"}">{x}</td>' for i, x in enumerate(c)) + "</tr>"
    tab = '<table style="border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:12.5px"><tr style="color:var(--tinta-suave);font-weight:600">' + "".join(f'<td style="padding:4px 10px;border-bottom:1px solid var(--linea)">{h}</td>' for h in ["Grupo", "n", "Q1", "Mediana", "Q3"]) + "</tr>"
    tab += fila("Sin", 7, "—", "—", "—") + fila("Con", 6, "—", "—", "—") + "</table>"
    return f'''<div class="hoja-marco" style="position:relative">{AVISO}<div class="hoja-titulo"><span>Diagrama de caja de tiempo por condicion</span><span style="display:flex;gap:8px"><span class="celda-activa">Exportar: PNG, PDF</span></span></div>
    <div style="display:flex;gap:28px;padding:18px 22px;align-items:flex-start">{svg_caja()}<div><div style="font-weight:600;margin-bottom:8px">Estadísticos</div>{tab}
    <p style="max-width:330px;color:var(--tinta-suave);font-size:12px;line-height:1.5">1 valor excluido por no ser numérico (C6, fila 7). Los valores de la tabla se llenan cuando el cálculo esté verificado contra el curso.</p></div></div></div>'''


def vista_amef():
    cols = ["N.º", "Operación o función", "Falla potencial", "Efecto", "SEV", "Causas potenciales", "OCC", "Controles actuales", "DET", "RPN"]
    anch = [40, 150, 140, 140, 48, 150, 48, 140, 48, 56]
    datos = [[1, "Colocar símbolo de revisión", "Símbolo omitido", "Dibujo liberado incompleto", 7, "Paso manual repetitivo", 5, "Revisión por segunda persona", 4],
             [2, "Actualizar cota", "Valor mal transcrito", "Pieza fabricada fuera de dimensión", 8, "Captura manual de valores", 3, "Revisión visual", 6],
             [3, "Agregar nota general", "Nota con redacción antigua", "Confusión en taller", 4, "Plantilla desactualizada", 4, "Ninguno", 8]]
    h = '<table style="border-collapse:collapse;table-layout:fixed;font-size:12.5px"><tr>' + "".join(f'<th style="width:{a}px;background:var(--encabezado);color:var(--tinta-suave);font-weight:600;padding:6px;border:1px solid var(--rejilla);text-align:left;vertical-align:bottom">{c}</th>' for c, a in zip(cols, anch)) + "</tr>"
    for f in datos:
        rpn = f[4] * f[6] * f[8]
        celdas = f + [rpn]
        h += "<tr>" + "".join(f'<td style="padding:6px;border:1px solid var(--rejilla);vertical-align:top;line-height:1.35;{"text-align:right;font-variant-numeric:tabular-nums" if isinstance(v,int) else ""}{";background:#f6f3ed;font-weight:600" if j==9 else ""}">{v}</td>' for j, v in enumerate(celdas)) + "</tr>"
    h += '<tr>' + "".join('<td style="height:30px;border:1px solid var(--rejilla)"></td>' for _ in cols) + "</tr></table>"
    cab = f'<div style="display:flex;gap:14px;padding:10px 12px;border-bottom:1px solid var(--linea);background:var(--papel)">{CAMPO("Proyecto","Proyecto de prueba",True)}{CAMPO("Responsable","Persona de prueba",True)}{CAMPO("Sistema o proceso","Modificación de dibujos")}{CAMPO("Fecha","2026-10-05")}</div>'
    return f'<div class="hoja-marco" style="position:relative">{AVISO}<div class="hoja-titulo"><span>AMEF de proceso</span><span class="celda-activa">RPN calculado, no editable</span></div>{cab}<div style="padding:12px;overflow:auto">{h}</div></div>'


def vista_tablero():
    sem = ["S1", "S2", "S3", "S4", "S5", "S6"]
    ind = [("Tiempo medio por unidad (min)", "≤ 12", [18.2, 17.5, 15.1, 13.9, 12.6, 11.8], True),
           ("Errores por unidad", "≤ 0.2", [0.9, 0.8, 0.5, 0.4, 0.3, 0.2], True),
           ("Unidades completadas", "≥ 25", [21, 24, 22, 26, 27, 25], False)]
    def spark(v):
        a, b = min(v), max(v); pts = " ".join(f"{10+i*22},{34-(x-a)/(b-a or 1)*26}" for i, x in enumerate(v))
        return f'<svg width="130" height="40"><polyline points="{pts}" fill="none" stroke="#dd5813" stroke-width="2"/></svg>'
    h = '<table style="border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums"><tr style="color:var(--tinta-suave);font-weight:600">' + "".join(f'<td style="padding:6px 10px;border-bottom:1px solid var(--linea)">{x}</td>' for x in ["Indicador", "Meta"] + sem + ["Tendencia"]) + "</tr>"
    for n, m, v, menor in ind:
        h += f'<tr><td style="padding:6px 10px;border-bottom:1px solid var(--rejilla)">{n}</td><td style="padding:6px 10px;border-bottom:1px solid var(--rejilla);color:var(--tinta-suave)">{m}</td>'
        h += "".join(f'<td style="padding:6px 10px;border-bottom:1px solid var(--rejilla);text-align:right">{x}</td>' for x in v)
        h += f'<td style="border-bottom:1px solid var(--rejilla)">{spark(v)}</td></tr>'
    h += "</table>"
    wip = "".join(f'<li style="padding:6px 0;border-bottom:1px solid var(--rejilla);display:flex;justify-content:space-between;gap:20px"><span>{a}</span><span style="color:var(--tinta-suave)">{b}</span></li>' for a, b in [("U-015 en revisión", "Op1"), ("U-016 en modificación", "Op2"), ("U-017 en espera de datos", "—")])
    return f'''<div class="hoja-marco" style="position:relative">{AVISO}<div class="hoja-titulo"><span>Tablero semanal</span><span class="celda-activa">Semana 6 de 6</span></div>
    <div style="padding:16px 18px;display:flex;gap:30px;align-items:flex-start;overflow:auto"><div>{h}</div>
    <div style="min-width:240px"><div style="font-weight:600;margin-bottom:6px">Trabajos en proceso</div><ul style="list-style:none;margin:0;padding:0">{wip}</ul></div></div></div>'''


VISTAS = {"mvp_1_hoja_recoleccion": vista_hoja, "mvp_2_dialogo_modulo": vista_dialogo,
          "mvp_3_resultado_modulo": vista_resultado, "mvp_4_formato_tabla_amef": vista_amef,
          "mvp_5_tablero": vista_tablero}

if __name__ == "__main__":
    ui = RAIZ / "app" / "ui"
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ui)); h.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h); threading.Thread(target=srv.serve_forever, daemon=True).start()
    api = Api()
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1366, "height": 768})
        pg.expose_function("__py", lambda n, a: getattr(api, n)(*a))
        pg.add_init_script("window.pywebview={api:new Proxy({},{get:(_,n)=>(...a)=>window.__py(n,a)})};")
        pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/index.html"); pg.wait_for_selector("body[data-listo='1']")
        for nombre, f in VISTAS.items():
            pg.evaluate("h => { const m = document.querySelector('.trabajo').firstElementChild; m.outerHTML = h; }", f())
            pg.screenshot(path=str(SAL / f"{nombre}.png"))
        b.close()
    print("listo")
