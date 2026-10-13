"""QFD completo (v0.21). Reemplaza a la primera versión de formatos4. Fuentes: 13_GB_DEFINIR DEF-QFD (qués contra cómos, cuatro matrices),
PL10 QFD (plantilla del curso: importancia, relaciones 9/3/1, evaluación propia y de competidores, evaluación técnica, valores objetivo,
importancia absoluta y techo con fuerte positiva, positiva, negativa y fuerte negativa). La ponderación de la evaluación competitiva
(razón de mejora = meta / evaluación propia; peso absoluto = importancia × razón × punto de venta) y la dirección de mejora (▲ ◇ ▼) siguen
la plantilla de casa de la calidad que usa el usuario (QFD-Act1) y la práctica común [GENERAL, no en la base].
Importancia técnica = Σ (peso relativo del qué en % × relación), igual que la plantilla del usuario."""
import json
from .formatos import Formato, formato, fila_vacia
from .formatos4 import SI, F, N, _svg, _t
from .base import num

NT, NC = 10, 4                                   # requisitos técnicos y competidores
REL = [["", ""], ["9", "● 9 fuerte"], ["3", "○ 3 media"], ["1", "▽ 1 débil"]]
SIMB = {"9": "●", "3": "○", "1": "▽"}
DIR = [["", ""], ["max", "▲ maximizar"], ["obj", "◇ objetivo"], ["min", "▼ minimizar"]]
DSIMB = {"max": "▲", "obj": "◇", "min": "▼"}
CORR = ["", "++", "+", "-", "--"]
CSIMB = {"++": "◎", "+": "+", "-": "−", "--": "✕"}
COLC = ["#2b6f8f", "#9a3e0e", "#2e7d32", "#7a5a9a"]


def leer_techo(txt):
    """«1-2 ++; 2-5 -» → {(1, 2): '++', (2, 5): '-'}"""
    out = {}
    for parte in (txt or "").replace(",", ";").split(";"):
        p = parte.split()
        if len(p) == 2 and "-" in p[0]:
            try:
                a, b = sorted(int(x) for x in p[0].split("-")[:2])
                if 1 <= a < b <= NT and p[1] in CORR[1:]: out[(a, b)] = p[1]
            except ValueError: pass
    return out


def escribir_techo(d): return "; ".join(f"{a}-{b} {v}" for (a, b), v in sorted(d.items()) if v)


def casa_svg(qs, ts, rel, techo, w_rel, t_abs, t_rel, comp_nombres, rank, orig=None):
    """Casa de la calidad completa e interactiva: data-rel="fila:col" y data-cor="a:b" se cambian con un clic."""
    nt, nq = len(ts), len(qs)
    if not nt or not nq: return None
    cw, rh, izq = 34, 26, 330
    techo_h = cw * nt / 2 + 10; cab_h = 150; top = techo_h + cab_h
    der_w = 210; W = izq + nt * cw + der_w + 20; H = top + nq * rh + 6 * 22 + 30
    s = ""
    x0 = izq
    # techo (rombos entre columnas a y b)
    for a in range(nt):
        for b in range(a + 1, nt):
            cx = x0 + (a + b + 1) * cw / 2; cy = techo_h - (b - a) * cw / 2 + 4
            v = techo.get((ts[a][0], ts[b][0]), "")
            col = {"++": "#2e7d32", "+": "#5b9a5e", "-": "#c2410c", "--": "#b3261e"}.get(v, "#9b9284")
            s += (f'<g data-cor="{ts[a][0]}:{ts[b][0]}" style="cursor:pointer"><path d="M{cx} {cy - cw / 2}l{cw / 2} {cw / 2}-{cw / 2} {cw / 2}-{cw / 2}-{cw / 2}z" '
                  f'fill="#fbf6ef" stroke="#e2dcd0"/><text x="{cx}" y="{cy + 5}" text-anchor="middle" font-size="13" font-weight="700" fill="{col}">{CSIMB.get(v, "")}</text></g>')
    # encabezados técnicos (verticales) con dirección
    for j, (k, nombre, d, *_) in enumerate(ts):
        x = x0 + j * cw
        s += f'<rect x="{x}" y="{techo_h}" width="{cw}" height="{cab_h}" fill="#f1ece2" stroke="#e2dcd0"/>'
        s += f'<text transform="translate({x + cw / 2 + 4} {top - 26}) rotate(-90)" font-size="10.5" fill="#2b2620">{k}. {_t(nombre)[:22]}</text>'
        s += f'<text x="{x + cw / 2}" y="{top - 8}" text-anchor="middle" font-size="12" font-weight="700" fill="#dd5813">{DSIMB.get(d, "")}</text>'
    # qués
    s += f'<text x="8" y="{top - 8}" font-size="10.5" font-weight="700" fill="#5f574c">Requisito del cliente</text><text x="{izq - 74}" y="{top - 8}" font-size="10" fill="#5f574c">Imp.</text><text x="{izq - 40}" y="{top - 8}" font-size="10" fill="#5f574c">Peso %</text>'
    for i, (q, imp) in enumerate(qs):
        y = top + i * rh
        s += f'<rect x="0" y="{y}" width="{izq}" height="{rh}" fill="{"#ffffff" if i % 2 else "#faf8f4"}" stroke="#e2dcd0"/><text x="8" y="{y + 17}" font-size="11" fill="#2b2620">{i + 1}. {_t(q)[:34]}</text>'
        s += f'<text x="{izq - 64}" y="{y + 17}" text-anchor="middle" font-size="11" fill="#2b2620">{num(imp, 3) if imp is not None else ""}</text><text x="{izq - 22}" y="{y + 17}" text-anchor="middle" font-size="11" font-weight="600" fill="#2b2620">{w_rel[i] * 100:.1f}</text>'
        for j, (k, *_) in enumerate(ts):
            x = x0 + j * cw; v = rel.get((i, k), "")
            s += f'<g data-rel="{(orig or list(range(nq)))[i]}:{k}" style="cursor:pointer"><rect x="{x}" y="{y}" width="{cw}" height="{rh}" fill="#ffffff" stroke="#e2dcd0"/><text x="{x + cw / 2}" y="{y + 18}" text-anchor="middle" font-size="14" fill="#2b2620">{SIMB.get(v, "")}</text></g>'
    # evaluación competitiva del cliente (derecha)
    xd = x0 + nt * cw + 14
    s += f'<text x="{xd}" y="{top - 30}" font-size="10.5" font-weight="700" fill="#5f574c">Evaluación del cliente (1 a 5)</text>'
    for n in range(1, 6): s += f'<text x="{xd + (n - 1) * 46 + 4}" y="{top - 10}" font-size="9.5" fill="#5f574c">{n}</text>'
    for i, (q, _) in enumerate(qs):
        y = top + i * rh + 13
        s += f'<line x1="{xd}" x2="{xd + 4 * 46 + 8}" y1="{y}" y2="{y}" stroke="#ede8de"/>'
    for c, (nom, vals) in enumerate(comp_nombres):
        pts = [(xd + (v - 1) * 46 + 6, top + i * rh + 13) for i, v in enumerate(vals) if v is not None]
        if len(pts) > 1: s += f'<polyline fill="none" stroke="{"#dd5813" if c == 0 else COLC[(c - 1) % 4]}" stroke-width="{2.4 if c == 0 else 1.3}" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>'
        for x, y in pts: s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4 if c == 0 else 3}" fill="{"#dd5813" if c == 0 else COLC[(c - 1) % 4]}"/>'
    ley = "".join(f'<rect x="{xd}" y="{top + nq * rh + 12 + c * 14}" width="10" height="10" fill="{"#dd5813" if c == 0 else COLC[(c - 1) % 4]}"/><text x="{xd + 15}" y="{top + nq * rh + 21 + c * 14}" font-size="10" fill="#2b2620">{_t(n)[:22]}</text>' for c, (n, _) in enumerate(comp_nombres))
    s += ley
    # filas inferiores
    yb = top + nq * rh + 6
    filas = [("Importancia técnica", [num(v, 4) for v in t_abs]), ("Importancia relativa %", [f"{v * 100:.1f}" for v in t_rel]), ("Prioridad", [str(r) for r in rank]),
             ("Valor objetivo", [_t(t[3])[:6] for t in ts]), ("Dificultad (1 a 5)", [t[4] for t in ts]), ("Nuestra evaluación (0 a 5)", [t[5] for t in ts])]
    for r, (et, vals) in enumerate(filas):
        y = yb + r * 22
        s += f'<text x="{izq - 8}" y="{y + 15}" text-anchor="end" font-size="10.5" font-weight="{700 if r < 3 else 400}" fill="#2b2620">{et}</text>'
        for j, v in enumerate(vals):
            x = x0 + j * cw; dest = r == 2 and v == "1"
            s += f'<rect x="{x}" y="{y}" width="{cw}" height="22" fill="{"#fbe8dd" if dest else "#ffffff"}" stroke="#e2dcd0"/><text x="{x + cw / 2}" y="{y + 15}" text-anchor="middle" font-size="9.5" fill="#2b2620">{v}</text>'
    s += f'<text x="8" y="{H - 8}" font-size="9.5" fill="#6f675b">Clic en una celda de la matriz o del techo para cambiar su valor · ● 9 ○ 3 ▽ 1 · techo: ◎ ++  + positiva  − negativa  ✕ −−</text>'
    return _svg(W, H, s)


def pareto_svg(nombres, vals):
    orden = sorted(range(len(vals)), key=lambda j: -vals[j]); tot = sum(vals) or 1
    w, h, iz, ab = 720, 250, 50, 70; n = len(orden); bw = (w - iz - 20) / max(n, 1); mx = max(vals) or 1
    s, acum, pts = "", 0, []
    for k, j in enumerate(orden):
        x = iz + k * bw; bh = (h - ab - 20) * vals[j] / mx; acum += vals[j]
        s += f'<rect x="{x + 4:.1f}" y="{h - ab - bh:.1f}" width="{bw - 8:.1f}" height="{bh:.1f}" rx="3" fill="{"#dd5813" if acum / tot <= .8 + 1e-9 or k == 0 else "#f6c9a8"}"/>'
        s += f'<text transform="translate({x + bw / 2 + 3:.1f} {h - ab + 8}) rotate(50)" font-size="9.5" fill="#2b2620">{_t(nombres[j])[:20]}</text>'
        pts.append((x + bw / 2, h - ab - (h - ab - 20) * acum / tot))
    s += '<polyline fill="none" stroke="#2b2620" stroke-width="1.8" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>'
    y80 = h - ab - (h - ab - 20) * .8
    s += f'<line x1="{iz}" x2="{w - 10}" y1="{y80:.1f}" y2="{y80:.1f}" stroke="#b3261e" stroke-dasharray="4 3"/><text x="{w - 12}" y="{y80 - 4:.1f}" text-anchor="end" font-size="9.5" fill="#b3261e">80 %</text>'
    s += f'<text x="4" y="14" font-size="11" font-weight="700" fill="#2b2620">Pareto de la importancia técnica</text>'
    return _svg(w, h, s)


@formato
class Qfd(Formato):
    ID, TITULO, REDIBUJAR = "QFD", "QFD: casa de la calidad", True
    CABECERA = ([F("proyecto", "Proyecto", fijo="nombre_proyecto"), F("producto_servicio", "Producto o servicio"), F("linea_valor", "Línea o flujo de valor"),
                 F("matriz", "Matriz del despliegue", tipo="opcion", opciones=[["1", "1. Producto o servicio (cliente → técnico)"], ["2", "2. Partes"], ["3", "3. Proceso"], ["4", "4. Control"]], defecto="1"),
                 F("nuestro", "Nombre de nuestro producto", defecto="Nuestro producto")]
                + [F(f"comp_nombre_{k}", f"Competidor {k}") for k in range(1, NC + 1)]
                + [F("techo", "Techo de correlaciones (también con clic en la casa)", tipo="largo",
                     ayuda="Formato «1-2 ++; 2-5 -»: pares de requisitos técnicos y su correlación (++ fuerte positiva, + positiva, - negativa, -- fuerte negativa)."),
                   F("prioridades", "Requisitos técnicos prioritarios (80 % del Pareto)", calc=True), F("resumen", "Resumen", calc=True)])
    TABLAS = [{"id": "tecnicos", "titulo": "Requisitos técnicos (cómos)", "filas": NT, "fijas": True, "columnas": [
                  {"campo": "k", "etiqueta": "N.º", "ancho": 46, "lectura": True}, {"campo": "nombre", "etiqueta": "Requisito técnico (cómo)", "ancho": 230},
                  {"campo": "direccion", "etiqueta": "Dirección de mejora", "tipo": "opcion", "opciones": DIR, "ancho": 130}, {"campo": "unidad", "etiqueta": "Unidad", "ancho": 80},
                  {"campo": "objetivo", "etiqueta": "Valor objetivo", "ancho": 110}, {"campo": "dificultad", "etiqueta": "Dificultad (1 a 5)", "tipo": "numero", "ancho": 100},
                  {"campo": "empresa", "etiqueta": "Nuestra evaluación (0 a 5)", "tipo": "numero", "ancho": 120}]
                  + [{"campo": f"comp_{k}", "etiqueta": f"Competidor {k} (0 a 5)", "tipo": "numero", "ancho": 110} for k in range(1, NC + 1)]
                  + [{"campo": "imp_abs", "etiqueta": "Importancia técnica", "calc": True, "ancho": 110}, {"campo": "imp_rel", "etiqueta": "% de la importancia técnica total", "calc": True, "ancho": 120},
                     {"campo": "rango", "etiqueta": "Prioridad", "calc": True, "ancho": 70}]},
              {"id": "requisitos_cliente", "titulo": "Requisitos del cliente (qués), relaciones y evaluación competitiva", "filas": 6, "columnas": [
                  {"campo": "requisito", "etiqueta": "Requisito del cliente", "ancho": 220}, {"campo": "importancia", "etiqueta": "Importancia (1 a 5)", "tipo": "numero", "ancho": 90}]
                  + [{"campo": f"rel_{k}", "etiqueta": f"T{k}", "tipo": "opcion", "opciones": REL, "ancho": 70} for k in range(1, NT + 1)]
                  + [{"campo": "quejas", "etiqueta": "Quejas", "tipo": "numero", "ancho": 70}, {"campo": "empresa", "etiqueta": "Nosotros (1 a 5)", "tipo": "numero", "ancho": 90}]
                  + [{"campo": f"comp_{k}", "etiqueta": f"Comp. {k}", "tipo": "numero", "ancho": 70} for k in range(1, NC + 1)]
                  + [{"campo": "meta", "etiqueta": "Meta (1 a 5)", "tipo": "numero", "ancho": 80},
                     {"campo": "punto_venta", "etiqueta": "Punto de venta", "tipo": "opcion", "opciones": [["", ""], ["1", "1 ninguno"], ["1.2", "1.2 medio"], ["1.5", "1.5 fuerte"]], "ancho": 110},
                     {"campo": "razon", "etiqueta": "Razón de mejora", "calc": True, "ancho": 90}, {"campo": "peso_abs", "etiqueta": "Peso absoluto", "calc": True, "ancho": 90},
                     {"campo": "peso_rel", "etiqueta": "% del peso absoluto total", "calc": True, "ancho": 110}]}]
    NOTA = ("13_GB DEF-QFD: el QFD traduce los requisitos del cliente (qués) en requisitos técnicos (cómos) y se despliega en cuatro matrices encadenadas "
            "(producto, partes, proceso y control). PL10 QFD: importancia del cliente, relaciones 9, 3 y 1, evaluación propia y de competidores, evaluación "
            "técnica, valores objetivo, importancia absoluta y techo de correlaciones. No respaldados por la base: razón de mejora (meta / evaluación propia), "
            "punto de venta y peso absoluto (importancia × razón × punto de venta), dirección de mejora y el Pareto con corte en 80 %, tomados de la plantilla "
            "de casa de la calidad de uso común. Importancia técnica = Σ (peso relativo del qué en % × relación).")

    @classmethod
    def vacio(cls):
        v = super().vacio(); v["tablas"]["tecnicos"] = [{"k": str(k)} for k in range(1, NT + 1)]; return v

    @classmethod
    def calcular(cls, d, hoja, proyecto):
        cab = d["cabecera"]; tec = d["tablas"]["tecnicos"]
        while len(tec) < NT: tec.append({"k": str(len(tec) + 1)})
        for k, f in enumerate(tec, 1): f["k"] = str(k)
        qs = d["tablas"]["requisitos_cliente"]; av = []
        activos = [k for k in range(1, NT + 1) if (tec[k - 1].get("nombre") or "").strip()]
        cc_q, kk_q, filas = [], [], []
        pesos = []
        for i, f in enumerate(qs):
            c, k = {}, {}
            if not (f.get("requisito") or "").strip(): cc_q.append(c); kk_q.append(k); pesos.append(None); continue
            imp = N(f.get("importancia"))
            if imp is None or not 1 <= imp <= 5: k["importancia"] = "falta" if imp is None else "mal"; imp = None
            emp, meta, pv = N(f.get("empresa")), N(f.get("meta")), N(f.get("punto_venta")) or 1.0
            for x in ["empresa", "meta"] + [f"comp_{j}" for j in range(1, NC + 1)]:
                v = N(f.get(x))
                if f.get(x) and (v is None or not 1 <= v <= 5): k[x] = "mal"
            razon = (meta / emp) if (emp and meta) else 1.0
            pa = imp * razon * pv if imp is not None else None
            if emp and meta: c["razon"] = num(razon, 3)
            if pa is not None: c["peso_abs"] = num(pa, 4)
            pesos.append(pa); cc_q.append(c); kk_q.append(k)
            rels = [f.get(f"rel_{j}") for j in activos if f.get(f"rel_{j}")]
            if activos and not rels: av.append(f"«{f['requisito']}» no se relaciona con ningún requisito técnico: falta un cómo que lo atienda.")
            elif rels and "9" not in rels: av.append(f"«{f['requisito']}» no tiene relación fuerte con ningún requisito técnico.")
            for j in range(1, NT + 1):
                if f.get(f"rel_{j}") and j not in activos: k[f"rel_{j}"] = "advertencia"
        tot = sum(p for p in pesos if p) or 0
        w_rel = [(p / tot if (p and tot) else 0.0) for p in pesos]
        for c, p, wr in zip(cc_q, pesos, w_rel):
            if p: c["peso_rel"] = f"{wr * 100:.1f}%"
        t_abs = {j: sum(w_rel[i] * 100 * float(qs[i].get(f"rel_{j}") or 0) for i in range(len(qs)) if pesos[i]) for j in activos}
        tt = sum(t_abs.values()) or 0
        t_rel = {j: (t_abs[j] / tt if tt else 0) for j in activos}
        orden = sorted(activos, key=lambda j: -t_abs[j]); rank = {j: r + 1 for r, j in enumerate(orden)}
        cc_t, kk_t = [], []
        for j in range(1, NT + 1):
            f = tec[j - 1]; c, k = {}, {}
            if j in activos:
                c.update(imp_abs=num(t_abs[j], 4), imp_rel=f"{t_rel[j] * 100:.1f}%", rango=str(rank[j]))
                k["rango"] = "ok" if rank[j] <= 3 else ""
                if not f.get("direccion"): k["direccion"] = "falta"
                if t_abs[j] == 0: av.append(f"T{j} «{f['nombre']}» no se relaciona con ningún requisito del cliente: revisa si sobra.")
                for x in ["empresa"] + [f"comp_{q}" for q in range(1, NC + 1)]:
                    v = N(f.get(x))
                    if f.get(x) and (v is None or not 0 <= v <= 5): k[x] = "mal"
                dif = N(f.get("dificultad"))
                if f.get("dificultad") and (dif is None or not 1 <= dif <= 5): k["dificultad"] = "mal"
            cc_t.append(c); kk_t.append(k)
        techo = leer_techo(cab.get("techo")); cab_out = {}
        if orden and tt:
            acum, prio = 0, []
            for j in orden:
                prio.append(j); acum += t_abs[j]
                if acum / tt >= .8: break
            cab_out["prioridades"] = ", ".join(f"T{j} {tec[j - 1]['nombre']} ({t_rel[j] * 100:.0f}%)" for j in prio)
            for (a, b), v in techo.items():
                if v in ("-", "--") and a in prio and b in prio:
                    av.append(f"Conflicto: T{a} y T{b} son prioritarios y tienen correlación negativa ({v}); define cuál cede o busca una solución que resuelva la contradicción.")
        nq = sum(1 for p in pesos if p is not None)
        llenas = sum(1 for i in range(len(qs)) if pesos[i] is not None for j in activos if qs[i].get(f"rel_{j}"))
        if nq and activos:
            cab_out["resumen"] = f"{nq} requisitos del cliente · {len(activos)} técnicos · {len(techo)} correlaciones en el techo · matriz llena al {100 * llenas / (nq * len(activos)):.0f}%"
            if llenas / (nq * len(activos)) > .6: av.append("La matriz está muy llena: una relación fuerte en casi todas las celdas suele indicar requisitos técnicos poco específicos.")
        # la casa se dibuja siempre: con lo capturado o, si falta, con renglones y columnas de muestra para ver su estructura
        idx = [i for i, p in enumerate(pesos) if p is not None]
        vis_t = activos or list(range(1, 6))
        filas_q = [(qs[i]["requisito"], N(qs[i].get("importancia"))) for i in idx] or [(f"(requisito {n})", None) for n in (1, 2, 3)]
        orig = idx or [0, 1, 2]
        rel = {(r, j): qs[i].get(f"rel_{j}") for r, i in enumerate(idx) for j in vis_t if qs[i].get(f"rel_{j}")}
        ts = [(j, tec[j - 1].get("nombre") or "(sin nombre)", tec[j - 1].get("direccion"), tec[j - 1].get("objetivo") or "", tec[j - 1].get("dificultad") or "",
               tec[j - 1].get("empresa") or "") for j in vis_t]
        comp = [(cab.get("nuevo") or cab.get("nuestro") or "Nuestro producto", [N(qs[i].get("empresa")) for i in idx])] + \
               [(cab.get(f"comp_nombre_{c}") or f"Competidor {c}", [N(qs[i].get(f"comp_{c}")) for i in idx]) for c in range(1, NC + 1)
                if any(qs[i].get(f"comp_{c}") for i in idx)]
        casa = casa_svg(filas_q, ts, rel, techo, [w_rel[i] for i in idx] or [0.0] * len(filas_q), [t_abs.get(j, 0) for j in vis_t],
                        [t_rel.get(j, 0) for j in vis_t], comp, [rank.get(j, "") for j in vis_t], orig=orig)
        bl = [{"tipo": "grafica", "svg": casa, "clase": "qfd-casa"}]
        if nq and activos and tt: bl.append({"tipo": "grafica", "svg": pareto_svg([f"T{j} {tec[j - 1]['nombre']}" for j in activos], [t_abs[j] for j in activos])})
        if not (nq and activos): av.append("La casa muestra su estructura de ejemplo: captura los requisitos técnicos (arriba) y los del cliente (abajo) para llenarla. También puedes hacer clic en las celdas de la casa.")
        return {"cab": cab_out, "calc": {"tecnicos": cc_t, "requisitos_cliente": cc_q}, "clases": {"tecnicos": kk_t, "requisitos_cliente": kk_q}, "avisos": av, "bloques": bl}


def alternar_rel(d, i, k):
    f = d["tablas"]["requisitos_cliente"][i]; ciclo = ["", "9", "3", "1"]
    f[f"rel_{k}"] = ciclo[(ciclo.index(f.get(f"rel_{k}") or "") + 1) % 4]


def alternar_cor(d, a, b):
    t = leer_techo(d["cabecera"].get("techo")); v = t.get((a, b), "")
    t[(a, b)] = CORR[(CORR.index(v) + 1) % len(CORR)]; d["cabecera"]["techo"] = escribir_techo(t)
