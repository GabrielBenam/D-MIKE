"""Estadística > Analizar diseño factorial (2 niveles, completo o fraccionado). Fuentes: 18_GB_MEJORAR (FACT-NOTACION, FACT-2X2-EJEMPLO,
FACT-EFECTOS-PRINCIPALES, FACT-INTERACCION) y 26_BB_DOE_FRACCIONADOS (FRAC-RESOLUCION, FRAC-CONSTRUCCION, FRAC-EJEMPLO).
Efecto = promedio de la respuesta en el nivel alto menos en el bajo = 2 × coeficiente codificado. Con réplicas o puntos centrales se usa
la prueba t del modelo (27_BB REG-PRUEBAS-PARAMETROS); sin grados de libertad para el error se usa el seudo error de Lenth, como Minitab
[GENERAL]. Los efectos confundidos (fraccionados) se detectan comparando columnas y se reportan como alias."""
import itertools, math
import numpy as np
from scipy import stats as st
from . import registrar, doe as D, regresion as R
from .analisis import _prob_normal
from .base import _f
from .base import (ErrorEntrada, columna, filas_validas, valor, figura, a_svg_png, num, p_texto, p_igual, frase_p, resultado,
                   b_grafica, b_tabla, b_texto, NARANJA, TINTA, SUAVE, CLARO, PALETA)
from .dialogo import ModuloDialogo


def codificar(vals):
    """Devuelve (codificados, bajo, alto, centrales) para una columna de 2 niveles (con puntos centrales opcionales)."""
    if all(isinstance(v, (int, float)) for v in vals): dist = sorted(set(vals))
    else: dist = list(dict.fromkeys(vals))                  # texto: el primer nivel que aparece es el bajo (-1), como en la tabla del diseño
    if len(dist) == 2:
        b, a = dist; return [-1.0 if v == b else 1.0 for v in vals], b, a, [False] * len(vals)
    if len(dist) == 3 and all(isinstance(v, (int, float)) for v in dist) and abs(dist[1] - (dist[0] + dist[2]) / 2) < 1e-9 * max(1, abs(dist[1])):
        b, c, a = dist; return [-1.0 if v == b else 1.0 if v == a else 0.0 for v in vals], b, a, [v == c for v in vals]
    raise ErrorEntrada("Cada factor debe tener 2 niveles (y, si acaso, un punto central numérico justo a la mitad).")


def efectos_factoriales(Xc, y, letras, orden_max):
    """Términos hasta el orden dado; detecta alias (columnas iguales o de signo contrario) y deja el de menor orden."""
    Xc = np.asarray(Xc, float); y = np.asarray(y, float); k = Xc.shape[1]
    terminos, cols, alias = [], [], {}
    for r in range(1, orden_max + 1):
        for comb in itertools.combinations(range(k), r):
            c = np.prod(Xc[:, comb], axis=1); nom = "".join(letras[i] for i in comb)
            dup = next((t for t, cc in zip(terminos, cols) if np.allclose(c, cc) or np.allclose(c, -cc)), None)
            if dup is not None:
                alias.setdefault(dup, []).append(("-" if np.allclose(c, -cols[terminos.index(dup)]) and not np.allclose(c, cols[terminos.index(dup)]) else "") + nom)
                continue
            if np.allclose(c, c[0]):                                         # columna constante (confundida con la media)
                alias.setdefault("Constante", []).append(nom); continue
            terminos.append(nom); cols.append(c)
    return terminos, np.column_stack(cols) if cols else np.empty((len(y), 0)), alias


@registrar
class Factorial(ModuloDialogo):
    ID, TITULO = "FACTORIAL", "Analizar diseño factorial"
    CAMPOS = [{"campo": "y", "etiqueta": "Respuesta", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "xs", "etiqueta": "Factores (2 a 7, cada uno con 2 niveles)", "tipo": "cols"},
              {"campo": "orden", "etiqueta": "Términos del modelo", "tipo": "opcion", "defecto": "auto",
               "opciones": [["auto", "Automático (todas en completos; hasta dobles en fraccionados)"], ["1", "Solo efectos principales"],
                            ["2", "Hasta interacciones dobles"], ["3", "Hasta interacciones triples"], ["todos", "Todas las interacciones"]]},
              {"campo": "meta", "etiqueta": "Objetivo de la respuesta", "tipo": "opcion", "defecto": "max", "opciones": [["max", "Maximizar"], ["min", "Minimizar"]]},
              {"campo": "alfa", "etiqueta": "Nivel de significancia (alfa)", "tipo": "opcion", "defecto": "0.05",
               "opciones": [["0.10", "0.10"], ["0.05", "0.05"], ["0.01", "0.01"]]}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        yj = p.get("y"); columna(hoja, yj, "la respuesta", "num")
        xs = [j for j in (p.get("xs") or []) if j is not None]
        if not 2 <= len(xs) <= 7: raise ErrorEntrada("Elige de 2 a 7 factores.")
        for j in xs: columna(hoja, j, "los factores")
        if yj in xs: raise ErrorEntrada("La respuesta no puede ser también factor.")
        alfa = float(p.get("alfa") or .05)
        filas, fuera = filas_validas(hoja, [yj] + xs)
        y = np.array([valor(hoja, yj, i) for i in filas], float); k = len(xs)
        nombres = [hoja.columnas[j].nombre or f"C{j + 1}" for j in xs]; ny = hoja.columnas[yj].nombre or f"C{yj + 1}"
        letras = D.LETRAS[:k]
        Xc, niveles, centro = [], [], np.zeros(len(y), bool)
        for q, j in enumerate(xs):
            cod, b, a, cen = codificar([valor(hoja, j, i) for i in filas]); Xc.append(cod); niveles.append((b, a)); centro |= np.array(cen)
        Xc = np.array(Xc).T
        niveles = [tuple(num(v) if isinstance(v, (int, float)) else str(v) for v in nv) for nv in niveles]
        es_cen = np.all(Xc == 0, axis=1)
        if np.any(centro & ~es_cen): raise ErrorEntrada("Un punto central debe tener a todos los factores en su nivel medio.")
        Xf, yf = Xc[~es_cen], y[~es_cen]
        combs = {tuple(r) for r in Xf}; completo = len(combs) == 2 ** k
        if p.get("orden") in (None, "", "auto"): orden = k if completo else 2
        elif p.get("orden") == "todos": orden = k
        else: orden = min(int(p["orden"]), k)
        terms, M, aliases = efectos_factoriales(Xf, yf, letras, orden)
        if not terms: raise ErrorEntrada("No hay términos estimables con estos datos.")
        n = len(yf)
        # ¿Hay grados de libertad para el error? (réplicas, puntos centrales o términos omitidos)
        A = np.column_stack([np.ones(n), M])
        gl_e = n - A.shape[1] + int(np.sum(es_cen))
        coef = np.linalg.lstsq(A, yf, rcond=None)[0]; efe = 2 * coef[1:]
        tabla, sig, metodo = [], set(), ""
        if gl_e > 0:
            Mx = np.vstack([M, np.zeros((int(np.sum(es_cen)), M.shape[1]))]) if np.any(es_cen) else M
            yy = np.concatenate([yf, y[es_cen]]) if np.any(es_cen) else yf
            curv = None
            if np.any(es_cen):
                curv = np.concatenate([np.zeros(n), np.ones(int(np.sum(es_cen)))]); Mx = np.column_stack([Mx, curv])
            mod = R.ajustar(Mx, yy, terms + (["Curvatura (puntos centrales)"] if curv is not None else []), alfa)
            tcrit = float(st.t.ppf(1 - alfa / 2, mod["gl_e"])); metodo = f"t con {mod['gl_e']} gl del error"
            for c in mod["coef"][1:]:
                if c["termino"].startswith("Curvatura"):
                    tabla.append([c["termino"], "", num(c["coef"], 5), num(c["ee"], 4), num(c["t"], 3), p_texto(c["p"]), ""]); continue
                if c["p"] < alfa: sig.add(c["termino"])
                tabla.append([c["termino"], num(2 * c["coef"], 5), num(c["coef"], 5), num(c["ee"], 4), num(c["t"], 3), p_texto(c["p"]), ", ".join(aliases.get(c["termino"], []))])
            tstd = {c["termino"]: abs(c["t"]) for c in mod["coef"][1:] if not c["termino"].startswith("Curvatura")}
            resumen = [[num(mod["s"], 5), f"{100 * mod['r2']:.2f}%", f"{100 * mod['r2_aj']:.2f}%", str(mod["gl_e"])]]
            curva = next((c for c in mod["coef"] if c["termino"].startswith("Curvatura")), None)
        else:
            pse, gl = D.lenth(efe); tcrit = float(st.t.ppf(1 - alfa / 2, gl)); metodo = f"seudo error estándar de Lenth = {num(pse, 4)} ({num(gl, 3)} gl)"
            tstd = {}
            for t_, e in zip(terms, efe):
                tv = e / pse if pse > 0 else float("inf"); pv = float(2 * st.t.sf(abs(tv), gl))
                if pv < alfa: sig.add(t_)
                tstd[t_] = abs(tv)
                tabla.append([t_, num(e, 5), num(e / 2, 5), "", num(tv, 3), p_texto(pv), ", ".join(aliases.get(t_, []))])
            resumen, curva = None, None
        # ---------- gráficas ----------
        orden_t = sorted(tstd, key=lambda t: tstd[t])
        fig, ax = figura(6.2, max(2.6, 0.32 * len(orden_t) + 1))
        ax.barh(orden_t, [tstd[t] for t in orden_t], color=[NARANJA if t in sig else CLARO for t in orden_t], edgecolor=NARANJA)
        ax.axvline(tcrit, color="#b3261e", ls="--", lw=1); ax.text(tcrit, len(orden_t) - .4, f" {num(tcrit, 4)}", color="#b3261e", fontsize=8)
        ax.set_xlabel("Efecto estandarizado (valor absoluto)"); ax.set_title(f"Pareto de efectos estandarizados (alfa = {alfa:g})", fontsize=9)
        svg_p, png = a_svg_png(fig)
        fig, ax = figura(5.4, 4.0)
        _prob_normal(ax, list(efe), "Gráfica normal de los efectos" + (f" (significativos: {', '.join(sorted(sig, key=lambda t: (len(t), t)))})" if sig else ""))
        svg_n, _ = a_svg_png(fig)
        fig, axs = figura(min(2.3 * k, 11), 2.6, ncols=k)
        axs = np.atleast_1d(axs)
        for q in range(k):
            m_b, m_a = float(yf[Xf[:, q] < 0].mean()), float(yf[Xf[:, q] > 0].mean())
            axs[q].plot([0, 1], [m_b, m_a], marker="o", color=NARANJA if letras[q] in sig else SUAVE, lw=1.6)
            axs[q].axhline(float(yf.mean()), color=SUAVE, ls=":", lw=.8); axs[q].set_xticks([0, 1]); axs[q].set_xticklabels([str(niveles[q][0])[:8], str(niveles[q][1])[:8]], fontsize=7)
            axs[q].set_title(f"{letras[q]}: {nombres[q][:14]}", fontsize=8); axs[q].set_xlim(-.3, 1.3)
        fig.suptitle(f"Efectos principales para {ny} (medias)", fontsize=9)
        svg_e, _ = a_svg_png(fig)
        pares = [(a, b) for a, b in itertools.combinations(range(k), 2)][:6]
        fig, axs = figura(min(3.0 * len(pares), 12), 2.8, ncols=len(pares))
        axs = np.atleast_1d(axs)
        for q, (a, b) in enumerate(pares):
            for nivel_b, col in ((-1, SUAVE), (1, NARANJA)):
                ms = [float(yf[(Xf[:, a] == la) & (Xf[:, b] == nivel_b)].mean()) if np.any((Xf[:, a] == la) & (Xf[:, b] == nivel_b)) else np.nan for la in (-1, 1)]
                axs[q].plot([0, 1], ms, marker="o", color=col, lw=1.4, label=f"{letras[b]} {niveles[b][0] if nivel_b < 0 else niveles[b][1]}")
            axs[q].set_xticks([0, 1]); axs[q].set_xticklabels([str(niveles[a][0])[:8], str(niveles[a][1])[:8]], fontsize=7)
            axs[q].set_title(f"{letras[a]}{letras[b]}", fontsize=8, color="#b3261e" if f"{letras[a]}{letras[b]}" in sig else TINTA); axs[q].legend(fontsize=6, frameon=False)
        fig.suptitle("Interacciones (líneas paralelas = sin interacción)", fontsize=9)
        svg_i, _ = a_svg_png(fig)
        # ---------- mejor combinación según los términos significativos (y su jerarquía) ----------
        usar = set(sig)
        for t_ in list(sig):
            for c in t_: usar.add(c)
        meta = p.get("meta") or "max"; mejor = None
        for comb in itertools.product([-1, 1], repeat=k):
            yhat = coef[0] + sum(coef[1 + terms.index(t_)] * np.prod([comb[letras.index(c)] for c in t_]) for t_ in usar if t_ in terms)
            if mejor is None or (yhat > mejor[1] if meta == "max" else yhat < mejor[1]): mejor = (comb, yhat)
        indif = [letras[q] for q in range(k) if letras[q] not in {c for t_ in usar for c in t_}]
        combo = ", ".join(f"{nombres[q]} = {niveles[q][0] if mejor[0][q] < 0 else niveles[q][1]}" + (" (indiferente)" if letras[q] in indif else "") for q in range(k))
        # ---------- bloques ----------
        cab = ["Término", "Efecto", "Coeficiente", "EE del coef.", "t", "Valor p", "Alias"]
        bl = [b_texto(f"Términos significativos (α = {alfa:g}): " + (", ".join(sorted(sig, key=lambda t: (len(t), t))) or "ninguno") +
                      f". Mejor combinación para {'maximizar' if meta == 'max' else 'minimizar'}: {combo}; respuesta estimada {num(mejor[1], 5)}.", "conclusion"),
              b_grafica(svg_p, {"g": "pefectos", "titulo": f"Pareto de efectos estandarizados (alfa = {alfa:g})", "terminos": orden_t, "valores": [_f(tstd[t]) for t in orden_t],
                                "sig": sorted(sig), "crit": _f(tcrit)}), b_tabla("Efectos y coeficientes codificados (" + metodo + ")", cab, tabla)]
        if resumen: bl.append(b_tabla("Resumen del modelo", ["S", "R²", "R² ajustado", "GL del error"], resumen))
        _ef = [{"factor": f"{letras[q]}: {nombres[q]}", "niveles": [str(niveles[q][0]), str(niveles[q][1])], "medias": [_f(yf[Xf[:, q] < 0].mean()), _f(yf[Xf[:, q] > 0].mean())]} for q in range(k)]
        _in = [{"par": f"{letras[a]}{letras[b]}", "niveles": [str(niveles[a][0]), str(niveles[a][1])], "series": [{"nombre": f"{letras[b]} {niveles[b][0] if nb < 0 else niveles[b][1]}",
                 "medias": [_f(yf[(Xf[:, a] == la) & (Xf[:, b] == nb)].mean()) if np.any((Xf[:, a] == la) & (Xf[:, b] == nb)) else None for la in (-1, 1)]} for nb in (-1, 1)]} for a, b in pares]
        bl += [b_grafica(svg_n), b_grafica(svg_e, {"g": "efectos", "titulo": f"Efectos principales para {ny}", "media": _f(yf.mean()), "efectos": _ef}),
               b_grafica(svg_i, {"g": "interaccion", "titulo": "Interacciones", "pares": _in})]
        if aliases:
            bl.append(b_tabla("Estructura de alias (efectos confundidos)", ["Término estimado", "Confundido con"],
                              [[t_, ", ".join(v)] for t_, v in aliases.items()]))
        cod = [[f"{letras[q]} = {nombres[q]}", str(niveles[q][0]), str(niveles[q][1])] for q in range(k)]
        bl.append(b_tabla("Codificación de factores", ["Letra y factor", "Nivel bajo (-1)", "Nivel alto (+1)"], cod))
        bl.append(b_texto("18_GB_MEJORAR: efecto = media en el nivel alto - media en el nivel bajo; gráfica de efectos principales (la pendiente más pronunciada "
                          "es el mayor efecto) e interacción (líneas no paralelas o cruzadas). 26_BB_DOE_FRACCIONADOS: en un fraccionado solo se estiman efectos "
                          "principales e interacciones dobles y los efectos confundidos se reportan como alias. No respaldados por la base: el método de Lenth "
                          "para diseños sin réplicas, la gráfica normal de efectos y la búsqueda de la mejor combinación entre las esquinas del diseño."))
        interp = [f"El efecto de cada factor es el cambio promedio en {ny} al pasar de su nivel bajo al alto (FACT-EFECTOS-PRINCIPALES).",
                  "Con interacción significativa, no interpretes por separado los efectos principales de esos factores: revisa la gráfica de interacción (FACT-INTERACCION)."]
        if aliases and any(v for t_, v in aliases.items() if t_ != "Constante"):
            interp.append("Es un diseño fraccionado: cada efecto estimado incluye a sus alias; un efecto doble significativo puede deberse a otra interacción confundida con él.")
        if curva is not None:
            interp.append(("Hay curvatura significativa (" + p_igual(curva["p"]) + "): el óptimo puede estar dentro de la región; continúa con superficie de respuesta.")
                          if curva["p"] < alfa else ("La curvatura no es significativa (" + p_igual(curva["p"]) + "): un modelo lineal con interacciones es razonable."))
        avisos = [f"{fuera} filas incompletas quedaron fuera."] if fuera else []
        if gl_e <= 0: avisos.append("Diseño sin réplicas ni puntos centrales: la significancia se estima con el método de Lenth (no hay error puro).")
        return resultado(cls.ID, f"Diseño factorial: efectos sobre {ny}", p, bl, avisos, interpretacion=interp,
                         datos={"columnas": [yj] + xs}, png=png)
