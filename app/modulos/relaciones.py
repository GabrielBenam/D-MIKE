"""Módulos de relación entre variables: CORREL (Pearson, matriz y diagramas) y REGRESION (simple, polinomial y
múltiple con diagnósticos). Motor: regresion.py."""
import math
import numpy as np
from scipy import stats as st
from . import registrar, regresion as R, estadistica as E
from .analisis import _prob_normal
from .base import _f
from .base import (ErrorEntrada, columna, nombre_col, filas_validas, valor, figura, a_svg_png, num, p_igual, p_texto, frase_p,
                   resultado, b_grafica, b_tabla, b_texto, NARANJA, TINTA, SUAVE, CLARO)
from .dialogo import ModuloDialogo

ALFAS = [["0.10", "0.10"], ["0.05", "0.05"], ["0.01", "0.01"]]


def _cols(hoja, lista, etiqueta, minimo):
    lista = [j for j in (lista or []) if j is not None]
    if len(lista) < minimo: raise ErrorEntrada(f"Elige al menos {minimo} {etiqueta}.")
    for j in lista: columna(hoja, j, etiqueta, "num")
    if len(set(lista)) != len(lista): raise ErrorEntrada("Hay columnas repetidas.")
    return lista


def _n(hoja, j): return hoja.columnas[j].nombre or nombre_col(hoja, j)


@registrar
class Correl(ModuloDialogo):
    ID, TITULO = "CORREL", "Correlación"
    CAMPOS = [{"campo": "vars", "etiqueta": "Variables (dos o más columnas numéricas)", "tipo": "cols", "filtro": "num"},
              {"campo": "spearman", "etiqueta": "Agregar correlación de Spearman (por rangos)", "tipo": "bool", "defecto": False}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        vs = _cols(hoja, p.get("vars"), "variables numéricas", 2)
        filas, fuera = filas_validas(hoja, vs)
        if len(filas) < 4: raise ErrorEntrada("Se necesitan al menos 4 filas completas.")
        datos = {j: [valor(hoja, j, i) for i in filas] for j in vs}
        nombres = [_n(hoja, j) for j in vs]
        tab, pares = [], []
        for a in range(len(vs)):
            for b in range(a + 1, len(vs)):
                try:
                    r = R.pearson(datos[vs[a]], datos[vs[b]])
                except ValueError as e:
                    raise ErrorEntrada(str(e))
                fila = [f"{nombres[a]} y {nombres[b]}", r["n"], num(r["r"], 3),
                        f"{num(r['ic'][0], 3)} a {num(r['ic'][1], 3)}" if r["ic"] else "—", f"{r['prueba']} = {num(r['estadistico'], 3)}",
                        p_texto(r["p"]), R.fuerza(r["r"])]
                if p.get("spearman"):
                    rs = st.spearmanr(datos[vs[a]], datos[vs[b]])
                    fila += [num(float(rs.statistic), 3), p_texto(float(rs.pvalue))]
                tab.append(fila); pares.append((a, b, r))
        k = len(vs)
        fig, axs = figura(2.4 * k, 2.2 * k, nrows=k, ncols=k) if k > 2 else figura(5.2, 4.0)
        if k == 2:
            x, y = datos[vs[0]], datos[vs[1]]
            axs.scatter(x, y, s=16, color=NARANJA)
            b1, b0 = np.polyfit(x, y, 1); xs = [min(x), max(x)]
            axs.plot(xs, [b0 + b1 * v for v in xs], color=TINTA, lw=1)
            axs.set_xlabel(nombres[0]); axs.set_ylabel(nombres[1]); axs.set_title(f"{nombres[1]} contra {nombres[0]} (r = {num(pares[0][2]['r'], 3)})")
        else:
            for a in range(k):
                for b in range(k):
                    ax = axs[a][b]
                    if a == b:
                        ax.axis("off"); ax.text(0.5, 0.5, nombres[a], ha="center", va="center", fontsize=9, fontweight="bold", transform=ax.transAxes)
                    else:
                        ax.scatter(datos[vs[b]], datos[vs[a]], s=6, color=NARANJA)
                        ax.tick_params(labelsize=6)
                        rr = next(r for x1, x2, r in pares if {x1, x2} == {a, b})["r"]
                        ax.set_title(f"r = {num(rr, 2)}", fontsize=7)
        svg, png = a_svg_png(fig)
        cab = ["Par", "N", "r de Pearson", "IC 95% de r", "Estadístico", "Valor p", "Fuerza (Western Electric)"] + \
              (["r de Spearman", "Valor p (Spearman)"] if p.get("spearman") else [])
        fuertes = [t[0] for t, (_, _, r) in zip(tab, pares) if abs(r["r"]) >= 0.85 and r["p"] < 0.05]
        interp = [("Pares con correlación lineal fuerte y significativa: " + ", ".join(fuertes) + ". ") if fuertes else
                  "Ningún par muestra correlación lineal fuerte (|r| ≥ 0.85) y significativa. ",
                  "La correlación mide asociación lineal, no causa y efecto: la causalidad se establece con el conocimiento del proceso "
                  "(17_GB CORR-INTERPRETACION y CORR-CAUSALIDAD). Una r significativa pero baja puede no tener utilidad práctica; el "
                  "curso pide al menos 0.8 a 0.9 (REG-PRUEBA-R). Si no hay relación significativa, puede faltar rango en los datos."]
        return resultado(cls.ID, "Correlación de " + ", ".join(nombres), p, [
            b_grafica(svg), b_tabla("Correlaciones", cab, tab),
            b_texto("r = Sxy/raíz(Sxx·Syy); prueba t para n < 50 y z para n ≥ 50 (27_BB REG-CORRELACION y REG-PRUEBA-R); fuerza según "
                    "17_GB CORR-INTERPRETACION. No respaldados por la base: valor p exacto, IC de Fisher y Spearman.")],
            [f"{fuera} filas incompletas quedaron fuera."] if fuera else [], datos={"columnas": vs}, png=png, interpretacion=interp,
            supuestos=[("Relación lineal", "Diagrama de dispersión", "Revisa que la nube no sea curva (r solo mide lo lineal)"),
                       ("Sin atípicos influyentes", "Diagrama de dispersión", "Un punto aislado puede inflar o anular r")])


@registrar
class Regresion(ModuloDialogo):
    ID, TITULO = "REGRESION", "Regresión lineal"
    CAMPOS = [{"campo": "y", "etiqueta": "Respuesta (Y)", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "xs", "etiqueta": "Predictores (X): uno o varios", "tipo": "cols", "filtro": "num"},
              {"campo": "grado", "etiqueta": "Con un solo predictor: grado del modelo", "tipo": "opcion", "defecto": "1",
               "opciones": [["1", "Lineal"], ["2", "Cuadrático"], ["3", "Cúbico"]]},
              {"campo": "x0", "etiqueta": "Predecir en X = (opcional; varios predictores separados por ;)", "tipo": "texto"},
              {"campo": "alfa", "etiqueta": "Nivel de significancia (alfa)", "tipo": "opcion", "opciones": ALFAS, "defecto": "0.05"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        yj = p.get("y"); columna(hoja, yj, "la respuesta", "num")
        xs = _cols(hoja, p.get("xs"), "predictores", 1)
        if yj in xs: raise ErrorEntrada("La respuesta no puede ser también predictor.")
        alfa = float(p.get("alfa") or 0.05); grado = int(p.get("grado") or 1)
        if len(xs) > 1: grado = 1
        filas, fuera = filas_validas(hoja, [yj] + xs)
        y = [valor(hoja, yj, i) for i in filas]
        X0 = [[valor(hoja, j, i) for j in xs] for i in filas]
        nx = [_n(hoja, j) for j in xs]; ny = _n(hoja, yj)
        if grado > 1:
            X = [[r[0] ** g for g in range(1, grado + 1)] for r in X0]
            nombres = [nx[0]] + [f"{nx[0]}^{g}" for g in range(2, grado + 1)]
        else:
            X, nombres = X0, nx
        try:
            m = R.ajustar(X, y, nombres, alfa)
        except ValueError as e:
            raise ErrorEntrada(str(e))
        n = m["n"]
        ec = f"{ny} = {num(m['coef'][0]['coef'], 5)}" + "".join(
            f" {'+' if c['coef'] >= 0 else '-'} {num(abs(c['coef']), 5)} {c['termino']}" for c in m["coef"][1:])
        coef = [[c["termino"], num(c["coef"], 5), num(c["ee"], 5), num(c["t"], 3), p_texto(c["p"]),
                 f"{num(c['ic'][0], 5)} a {num(c['ic'][1], 5)}", num(c["vif"], 2) if c["vif"] is not None else "—"] for c in m["coef"]]
        anova = [["Regresión", m["gl_r"], num(m["scr"], 5), num(m["scr"] / m["gl_r"], 5), num(m["f"], 3), num(m["f_tablas"], 3), p_texto(m["p_f"])],
                 ["Error", m["gl_e"], num(m["sce"], 5), num(m["mce"], 5), "", "", ""], ["Total", n - 1, num(m["sct"], 5), "", "", "", ""]]
        resumen = [[num(m["s"], 5), f"{100 * m['r2']:.2f}%", f"{100 * m['r2_aj']:.2f}%",
                    f"{100 * m['r2_pred']:.2f}%" if m["r2_pred"] == m["r2_pred"] else "—", num(m["press"], 4), num(m["dw"], 3)]]
        # gráfica principal
        if len(xs) == 1:
            fig, ax = figura(6.2, 4.0)
            xv = [r[0] for r in X0]
            ax.scatter(xv, y, s=16, color=NARANJA, zorder=3)
            lo, hi = min(xv), max(xv); grid = [lo + (hi - lo) * t / 100 for t in range(101)]
            pr = [R.predecir(m, [g ** k for k in range(1, grado + 1)]) for g in grid]
            ax.plot(grid, [q["pred"] for q in pr], color=TINTA, lw=1.4)
            ax.plot(grid, [q["ic_media"][0] for q in pr], color=SUAVE, lw=0.8, ls="--"); ax.plot(grid, [q["ic_media"][1] for q in pr], color=SUAVE, lw=0.8, ls="--")
            ax.plot(grid, [q["ip"][0] for q in pr], color=NARANJA, lw=0.8, ls=":"); ax.plot(grid, [q["ip"][1] for q in pr], color=NARANJA, lw=0.8, ls=":")
            ax.set_xlabel(nx[0]); ax.set_ylabel(ny)
            ax.set_title(f"Línea ajustada: S = {num(m['s'], 4)}, R² = {100 * m['r2']:.1f}%, R² ajustado = {100 * m['r2_aj']:.1f}%", fontsize=9)
            ax.text(0.01, 0.01, "-- IC 95% de la media    ·· intervalo de predicción", transform=ax.transAxes, fontsize=7, color=SUAVE)
            svg, png = a_svg_png(fig)
            graf = [b_grafica(svg, {"g": "regresion", "titulo": f"{ny} contra {nx[0]}", "xl": nx[0], "yl": ny, "x": [_f(v) for v in xv], "y": [_f(v) for v in y],
                                    "grid": [_f(v) for v in grid], "pred": [_f(q["pred"]) for q in pr], "ic_lo": [_f(q["ic_media"][0]) for q in pr], "ic_hi": [_f(q["ic_media"][1]) for q in pr],
                                    "ip_lo": [_f(q["ip"][0]) for q in pr], "ip_hi": [_f(q["ip"][1]) for q in pr], "r2": _f(m["r2"]), "s": _f(m["s"])})]
        else:
            png, graf = None, []
        # residuos (27_BB REG-SUPUESTOS a REG-INDEPENDENCIA)
        fig, axs = figura(9.6, 5.6, nrows=2, ncols=2)
        res, aj = m["residuos"], m["ajustados"]
        _prob_normal(axs[0][0], res, "Probabilidad normal de residuos")
        axs[0][1].scatter(aj, res, s=12, color=NARANJA); axs[0][1].axhline(0, color=TINTA, lw=1); axs[0][1].set_title("Residuos contra ajustados")
        axs[1][0].hist(res, bins=min(12, max(5, int(math.sqrt(n)))), color=CLARO, edgecolor=NARANJA); axs[1][0].set_title("Histograma de residuos")
        axs[1][1].plot(range(1, n + 1), res, color=NARANJA, marker="o", ms=3, lw=0.8); axs[1][1].axhline(0, color=TINTA, lw=1)
        axs[1][1].set_title("Residuos contra orden")
        svg_r, png_r = a_svg_png(fig)
        png = png or png_r
        # observaciones inusuales: residuo estandarizado > 2 o Cook > 4/n [GENERAL]
        inus = [[str(filas[i] + 1), num(y[i], 5), num(aj[i], 5), num(m["est_res"][i], 3), num(m["h"][i], 3), num(m["cook"][i], 3),
                 ("residuo grande" if abs(m["est_res"][i]) > 2 else "") + (" influyente" if m["cook"][i] > 4 / n else "")]
                for i in range(n) if m["est_res"][i] == m["est_res"][i] and (abs(m["est_res"][i]) > 2 or m["cook"][i] > 4 / n)]
        bloques = graf + [
            b_texto("Ecuación: " + ec, "conclusion"),
            b_tabla("Coeficientes", ["Término", "Coeficiente", "EE", "t", "Valor p", f"IC {100 * (1 - alfa):.0f}%", "VIF"], coef),
            b_tabla("Resumen del modelo", ["S", "R²", "R² ajustado", "R² de predicción", "PRESS", "Durbin-Watson"], resumen),
            b_tabla("Análisis de varianza", ["Fuente", "GL", "SC", "CM", "F", "F de tablas", "Valor p"], anova)]
        x0 = (p.get("x0") or "").strip()
        if x0:
            try:
                v = [float(t.replace(",", ".")) for t in x0.split(";")]
            except ValueError:
                raise ErrorEntrada("El valor para predecir debe ser numérico (varios separados por ;).")
            if len(v) != len(xs): raise ErrorEntrada(f"Para predecir se necesitan {len(xs)} valores, uno por predictor.")
            vv = [v[0] ** g for g in range(1, grado + 1)] if grado > 1 else v
            q = R.predecir(m, vv)
            fuera_rango = any(not (min(r[k] for r in X0) <= v[k] <= max(r[k] for r in X0)) for k in range(len(v)))
            bloques.append(b_tabla("Predicción", ["X", "Ŷ", f"IC {100 * (1 - alfa):.0f}% de la media", f"Intervalo de predicción {100 * (1 - alfa):.0f}%"],
                                   [["; ".join(num(t) for t in v), num(q["pred"], 5), f"{num(q['ic_media'][0], 5)} a {num(q['ic_media'][1], 5)}",
                                     f"{num(q['ip'][0], 5)} a {num(q['ip'][1], 5)}"]]))
            if fuera_rango: bloques.append(b_texto("El punto está fuera del rango de los datos: es una extrapolación y el modelo puede no valer ahí.", "aviso"))
        bloques += [b_grafica(svg_r)]
        if inus: bloques.append(b_tabla("Observaciones inusuales", ["Fila", "Y", "Ajustado", "Residuo estand.", "Apalancamiento", "Cook", "Motivo"], inus))
        bloques.append(b_texto("Fórmulas: 27_BB_REGRESION (REG-ESTIMACION, REG-SIGNIFICADO, REG-PRUEBAS-PARAMETROS, REG-IC, REG-PREDICCION, "
                               "REG-R2, REG-R2-AJUSTADO, REG-COOK-PRESS-DW, REG-MULTICOLINEALIDAD, REG-MULTIPLE-MATRICIAL, REG-POLINOMIAL). "
                               "No respaldados por la base: los criterios de observación inusual (residuo estandarizado > 2, Cook > 4/n) y el "
                               "umbral de VIF."))
        t_f = frase_p(m["p_f"], alfa, "ningún predictor explica la respuesta", "el modelo explica parte de la variación de " + ny)
        interp = [t_f, f"R² = {100 * m['r2']:.1f}%: proporción de la variación de {ny} que el modelo explica (REG-R2).",
                  "Una relación significativa no prueba causa y efecto (17_GB CORR-CAUSALIDAD)."]
        vif_alto = [c["termino"] for c in m["coef"] if c["vif"] is not None and c["vif"] > 5]
        ad = E.anderson_darling(res) if n >= 8 else None
        supuestos = [
            ("Residuos normales", "Anderson-Darling y gráfica de probabilidad", (f"{p_igual(ad['p'], .005)}: " + ("no se rechaza la normalidad"
             if ad["p"] > 0.05 else "se rechaza la normalidad; revisa atípicos o transformación")) if ad else "pocos datos"),
            ("Varianza constante", "Residuos contra ajustados (REG-VARIANZA-CONSTANTE)", "Revisa que la banda sea pareja, sin forma de embudo"),
            ("Independencia", "Durbin-Watson y residuos contra orden (REG-INDEPENDENCIA)", f"DW = {num(m['dw'], 3)}; cerca de 2 indica sin autocorrelación"),
            ("Sin multicolinealidad", "VIF (REG-MULTICOLINEALIDAD)", ("VIF alto en " + ", ".join(vif_alto)) if vif_alto else "sin VIF mayores a 5")]
        avisos = [f"{fuera} filas incompletas quedaron fuera."] if fuera else []
        if n < 15: avisos.append(f"Hay {n} observaciones; el curso pide al menos 15 para Durbin-Watson (árbol de diagnóstico).")
        return resultado(cls.ID, f"Regresión de {ny} contra {', '.join(nx)}" + (f" (grado {grado})" if grado > 1 else ""), p, bloques, avisos,
                         datos={"columnas": [yj] + xs}, png=png, supuestos=supuestos, interpretacion=interp)
