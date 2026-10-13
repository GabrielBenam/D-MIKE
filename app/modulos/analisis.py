"""Módulos de análisis: ANOVA (un factor, con y sin bloque), DISTRIB (normalidad y especificaciones), MSA-ATR."""
import math
from collections import OrderedDict
from scipy import stats as st
from . import registrar, estadistica as E
from .base import _f
from .base import (ErrorEntrada, columna, nombre_col, filas_validas, valor, figura, a_svg_png, num, p_texto, p_igual, frase_p,
                   resultado, b_grafica, b_tabla, b_texto, NARANJA, TINTA, SUAVE, CLARO)
from .dialogo import ModuloDialogo

ALFAS = [["0.10", "0.10"], ["0.05", "0.05"], ["0.01", "0.01"]]   # 20_GB_TABLA_F


def _fuera(n): return [f"{n} filas con valores faltantes o que no corresponden a su tipo quedaron fuera del cálculo."] if n else []


def _prob_normal(ax, x, titulo):
    """Gráfica de probabilidad normal (residuos o datos). [GENERAL] posiciones de Benard, como Minitab."""
    o = sorted(x); n = len(o)
    q = [st.norm.ppf((i - 0.3) / (n + 0.4)) for i in range(1, n + 1)]
    ax.scatter(o, q, s=12, color=NARANJA, zorder=3)
    m = sum(o) / n; s = math.sqrt(sum((v - m) ** 2 for v in o) / (n - 1)) if n > 1 else 1
    if s > 0:
        lo, hi = min(q), max(q)
        ax.plot([m + lo * s, m + hi * s], [lo, hi], color=TINTA, lw=1)
    pct = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    ax.set_yticks([st.norm.ppf(p / 100) for p in pct]); ax.set_yticklabels([str(p) for p in pct])
    ax.set_ylabel("Porcentaje"); ax.set_title(titulo)


@registrar
class Anova(ModuloDialogo):
    ID, TITULO = "ANOVA", "ANOVA de un factor"
    CAMPOS = [{"campo": "y", "etiqueta": "Respuesta", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "factor", "etiqueta": "Factor", "tipo": "col", "filtro": "texto", "rol": ["factor"]},
              {"campo": "bloque", "etiqueta": "Bloque (opcional)", "tipo": "col", "filtro": "texto", "opcional": True, "rol": ["bloque"]},
              {"campo": "alfa", "etiqueta": "Nivel de significancia (alfa)", "tipo": "opcion", "opciones": ALFAS, "defecto": "0.05"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        j = p.get("y"); columna(hoja, j, "la respuesta", "num")
        fj = p.get("factor"); columna(hoja, fj, "el factor", "texto")
        bj = p.get("bloque"); bc = columna(hoja, bj, "el bloque", "texto", obligatoria=False)
        if fj == bj: raise ErrorEntrada("El factor y el bloque deben ser columnas distintas.")
        alfa = float(p.get("alfa") or 0.05)
        if alfa not in (0.10, 0.05, 0.01): raise ErrorEntrada("Alfa debe ser 0.10, 0.05 o 0.01 (20_GB_TABLA_F).")
        cols = [j, fj] + ([bj] if bc else [])
        filas, fuera = filas_validas(hoja, cols)
        grupos = OrderedDict()
        for i in filas: grupos.setdefault(str(valor(hoja, fj, i)), []).append(valor(hoja, j, i))
        if len(grupos) < 2: raise ErrorEntrada("El factor necesita al menos 2 niveles con datos.")
        if any(len(g) < 2 for g in grupos.values()) and not bc:
            raise ErrorEntrada("Cada nivel necesita al menos 2 réplicas para estimar el error (17_GB_ANALIZAR, ANOVA-ELEMENTOS).")
        nom, fnom = hoja.columnas[j].nombre or nombre_col(hoja, j), hoja.columnas[fj].nombre or nombre_col(hoja, fj)
        bloques = []
        if bc:
            celdas = OrderedDict()
            for i in filas: celdas.setdefault((str(valor(hoja, fj, i)), str(valor(hoja, bj, i))), []).append(valor(hoja, j, i))
            niv = sorted({k[0] for k in celdas}); bls = sorted({k[1] for k in celdas})
            if len(bls) < 2: raise ErrorEntrada("El bloque necesita al menos 2 valores distintos.")
            faltan = [f"{a}/{b}" for a in niv for b in bls if (a, b) not in celdas]
            tam = {len(v) for v in celdas.values()}
            if faltan or len(tam) > 1:
                raise ErrorEntrada("El diseño con bloque debe estar completo y balanceado: cada combinación de nivel y bloque "
                                   "con el mismo número de datos" + (f" (faltan {', '.join(faltan[:6])})" if faltan else "") + ".")
            r = E.anova_bloque(celdas, alfa)
            ajust = {k: r["medias_nivel"][k[0]] + r["medias_bloque"][k[1]] - r["gran_media"] for k in celdas}
            resid = [(v - ajust[k], ajust[k]) for k, vs in celdas.items() for v in vs]
            fuentes = [[fnom, r["tratamientos"]], [hoja.columnas[bj].nombre or "Bloque", r["bloque"]]]
        else:
            r = E.anova_un_factor(grupos, alfa)
            medias = {k: sum(g) / len(g) for k, g in grupos.items()}
            resid = [(valor(hoja, j, i) - medias[str(valor(hoja, fj, i))], medias[str(valor(hoja, fj, i))]) for i in filas]
            fuentes = [[fnom, r["tratamientos"]]]
        tabla = [[n_, f["gl"], f["ss"], f["ms"], f["f"], f["f_tablas"], p_texto(f["p"])] for n_, f in fuentes]
        tabla += [["Error", r["error"]["gl"], r["error"]["ss"], r["error"]["ms"], "", "", ""],
                  ["Total", r["total"]["gl"], r["total"]["ss"], "", "", "", ""]]
        medias_tab = []
        for k, g in grupos.items():
            d = E.descriptivos(g); medias_tab.append([k, d["n"], d["media"], d["desv"]])
        t = r["tratamientos"]
        comp = ">" if t["f"] > t["f_tablas"] else "≤"
        concl = (f"F = {num(t['f'])} {comp} F de tablas ({alfa}; {t['gl']}, {r['error']['gl']}) = {num(t['f_tablas'])}. "
                 + frase_p(t["p"], alfa, f"todas las medias de {fnom} son iguales", f"al menos una media de {fnom} es distinta"))
        bloques_txt = []
        if bc:
            efectivo = r["razon_bloque"] >= 2
            bloques_txt.append(b_texto(
                f"Bloque: MSBL / MSE = {num(r['razon_bloque'], 2)} "
                + ("(al menos 2 a 2.5: el bloqueo fue efectivo). " if efectivo else "(menor a 2: el bloqueo no fue efectivo). ")
                + ("El bloque es significativo; antes de concluir sobre el factor hay que estandarizar o controlar esa fuente "
                   "(17_GB_ANALIZAR, ANOVA-TIPOS y ANOVA-BLOQUEO)." if r["bloque_significativo"] else "El bloque no es significativo."),
                "conclusion"))
        # supuestos: residuos (17_GB_ANALIZAR, ANOVA-SUPUESTOS)
        fig, axs = figura(9.6, 3.0, ncols=3)
        res = [x for x, _ in resid]
        _prob_normal(axs[0], res, "Normalidad de residuos")
        axs[1].scatter([a for _, a in resid], res, s=12, color=NARANJA); axs[1].axhline(0, color=TINTA, lw=1)
        axs[1].set_title("Residuos contra ajustados"); axs[1].set_xlabel("Valor ajustado")
        axs[2].plot(range(1, len(res) + 1), res, color=NARANJA, marker="o", ms=3, lw=1); axs[2].axhline(0, color=TINTA, lw=1)
        axs[2].set_title("Residuos contra orden"); axs[2].set_xlabel("Orden de observación")
        svg_res, _ = a_svg_png(fig)
        fig, ax = figura(max(4.8, 1.0 * len(grupos) + 2.4), 3.4)
        ks = list(grupos)
        ax.boxplot([grupos[k] for k in ks], widths=0.5, patch_artist=True, medianprops={"color": NARANJA, "lw": 2},
                   boxprops={"facecolor": CLARO, "edgecolor": NARANJA})
        ax.plot(range(1, len(ks) + 1), [sum(grupos[k]) / len(grupos[k]) for k in ks], color=TINTA, marker="D", ms=5, lw=1)
        ax.set_xticks(range(1, len(ks) + 1)); ax.set_xticklabels(ks); ax.set_ylabel(nom)
        ax.set_title(f"{nom} por {fnom} (rombos: medias)")
        svg, png = a_svg_png(fig)
        avisos = _fuera(fuera)
        if len(grupos) == 2: avisos.append("Con 2 niveles, el ANOVA equivale a la prueba t de dos muestras.")
        # Supuestos (17_GB_ANALIZAR, ANOVA-SUPUESTOS); las pruebas usadas para revisarlos no están en la base [GENERAL]
        res_vals = [x for x, _ in resid]
        ad_r = E.anderson_darling(res_vals) if len(res_vals) >= 8 else None
        lev = st.levene(*[g for g in grupos.values() if len(g) > 1]) if sum(1 for g in grupos.values() if len(g) > 1) >= 2 else None
        supuestos = [
            ("Residuos con distribución normal", "Anderson-Darling sobre los residuos y gráfica de probabilidad",
             (f"{p_igual(ad_r['p'])}: " + ("no se rechaza la normalidad" if ad_r["p"] > 0.05 else "se rechaza la normalidad; con muestras "
              "balanceadas el ANOVA suele tolerarlo, revisa atípicos")) if ad_r else "muy pocos datos para probarlo"),
            ("Varianza constante entre niveles", "Prueba de Levene (no respaldada por la base) y residuos contra ajustados",
             (f"{p_igual(float(lev.pvalue))}: " + ("no se rechaza la igualdad de varianzas" if lev.pvalue > 0.05 else
              "las varianzas parecen distintas; interpreta F con cautela")) if lev is not None else "no aplica"),
            ("Independencia de las observaciones", "Residuos contra orden de observación", "Revísalo en la gráfica: no debe haber patrón ni tendencia")]
        tipo = "con bloque" if bc else "de un factor"
        return resultado(cls.ID, f"ANOVA {tipo}: {nom} contra {fnom}", p, supuestos=supuestos, bloques=[
            b_texto(concl, "conclusion"), *bloques_txt,
            b_tabla("Tabla ANOVA", ["Fuente", "GL", "SC", "CM", "F", "F de tablas", "Valor p"], tabla),
            b_tabla("Medias por nivel", ["Nivel", "N", "Media", "Desv. est."], medias_tab),
            b_grafica(svg),
            b_grafica(svg_res),
            b_texto("Fórmulas: 17_GB_ANALIZAR, ANOVA-QUE-ES y ANOVA-TIPOS; F de tablas: 20_GB_TABLA_F. SC = suma de "
                    "cuadrados, CM = cuadrado medio, GL = grados de libertad.")],
            avisos=avisos, datos={"columnas": cols}, png=png)


def clases_histograma(x, k=None):
    """[BASE] 16_GB_HISTOGRAMAS_CAPACIDAD_DESEMPENO, HIST-PROCEDIMIENTO: K por tabla (o raíz de N dentro de
    la tabla), W = (R + unidad)/K, primera clase desde el mínimo menos media unidad."""
    n = len(x); o = sorted(x)
    dec = max((len(f"{v:.10f}".rstrip("0").split(".")[1]) for v in o), default=0)
    unidad = 10 ** (-min(dec, 6))
    lo, hi = (5, 7) if n < 50 else (6, 10) if n <= 100 else (7, 12) if n <= 250 else (10, 20)
    k = k or min(max(round(math.sqrt(n)), lo), hi)
    w = (o[-1] - o[0] + unidad) / k
    ini = o[0] - unidad / 2
    return [ini + i * w for i in range(k + 1)], unidad, w


@registrar
class Distrib(ModuloDialogo):
    ID, TITULO = "DISTRIB", "Distribuciones y normalidad"
    CAMPOS = [{"campo": "y", "etiqueta": "Variable", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "lie", "etiqueta": "Límite inferior de especificación (opcional)", "tipo": "numero"},
              {"campo": "lse", "etiqueta": "Límite superior de especificación (opcional)", "tipo": "numero"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        j = p.get("y"); columna(hoja, j, "la variable", "num")
        lie, lse = cls.numero(p, "lie", "El LIE"), cls.numero(p, "lse", "El LSE")
        if lie is not None and lse is not None and lie >= lse: raise ErrorEntrada("El LIE debe ser menor que el LSE.")
        filas, fuera = filas_validas(hoja, [j])
        x = [valor(hoja, j, i) for i in filas]
        if len(x) < 8: raise ErrorEntrada("La prueba de normalidad necesita al menos 8 datos válidos.")
        d = E.descriptivos(x)
        if d["desv"] == 0: raise ErrorEntrada("Todos los datos son iguales; no hay variación que analizar.")
        ad = E.anderson_darling(x)
        normal = ad["p"] > 0.05
        nom = hoja.columnas[j].nombre or nombre_col(hoja, j)
        bordes, unidad, w = clases_histograma(x)
        fig, (a1, a2) = figura(9.6, 3.6, ncols=2)
        a1.hist(x, bins=bordes, color=CLARO, edgecolor=NARANJA)
        xs = [bordes[0] + (bordes[-1] - bordes[0]) * t / 120 for t in range(121)]
        a1.plot(xs, [len(x) * w * st.norm.pdf(v, d["media"], d["desv"]) for v in xs], color=TINTA, lw=1.2)
        for lim, et in ((lie, "LIE"), (lse, "LSE")):
            if lim is not None:
                a1.axvline(lim, color=NARANJA, lw=1.5, ls="--"); a1.text(lim, a1.get_ylim()[1] * 0.95, f" {et}", color=NARANJA, fontsize=8)
        a1.set_title(f"Histograma de {nom}"); a1.set_ylabel("Frecuencia")
        _prob_normal(a2, x, f"Gráfica de probabilidad normal")
        a2.text(0.02, 0.97, f"AD = {ad['a2']:.3f}\n{p_igual(ad['p'], .005)}", transform=a2.transAxes, va="top", fontsize=8, color=TINTA)
        svg, png = a_svg_png(fig)
        bloques = [b_grafica(svg, {"g": "histograma", "titulo": f"Histograma de {nom}", "x": [_f(v) for v in x], "media": _f(d["media"]), "desv": _f(d["desv"]),
                                   "lie": _f(lie), "lse": _f(lse), "bordes": [_f(b) for b in bordes]}),
                   b_texto(f"Prueba de normalidad (Anderson-Darling): {p_igual(ad['p'], .005)}. " + (
                       "Como p > 0.05, los datos no permiten rechazar la normalidad y se trabaja suponiéndola (25_BB_DISTRIBUCIONES, "
                       "DIST-IDENTIFICAR). Esto no demuestra que sean normales: con pocos datos la prueba tiene poca sensibilidad."
                       if normal else "Como p ≤ 0.05, se rechaza la normalidad: los datos no se comportan como una normal. Revisa si "
                       "algún efecto físico lo explica antes de transformar (25_BB_DISTRIBUCIONES, DIST-TRANSFORMACION)."), "conclusion"),
                   b_tabla("Estadísticos", ["N", "Media", "Desv. est.", "Mínimo", "Q1", "Mediana", "Q3", "Máximo", "AD", "Valor p"],
                           [[d["n"], d["media"], d["desv"], d["minimo"], d["q1"], d["mediana"], d["q3"], d["maximo"], ad["a2"], p_texto(ad["p"], .005)]])]
        if lie is not None or lse is not None:
            f = E.fuera_de_especificacion(d["media"], d["desv"], lie, lse)
            filas_e = []
            if lie is not None: filas_e.append(["Por debajo del LIE", num(lie), f["z_inf"], f"{100 * f['p_inf']:.4f}%"])
            if lse is not None: filas_e.append(["Por arriba del LSE", num(lse), f["z_sup"], f"{100 * f['p_sup']:.4f}%"])
            filas_e.append(["Total fuera de especificación", "", "", f"{100 * f['p_total']:.4f}%"])
            bloques.append(b_tabla("Especificaciones (25_BB_DISTRIBUCIONES, DIST-Z)", ["Concepto", "Límite", "Z", "Probabilidad"], filas_e))
            if f["sigma_lp"] is not None:
                bloques.append(b_texto(f"Nivel sigma de largo plazo = {f['sigma_lp']:.2f}; de corto plazo = {f['sigma_cp']:.2f} "
                                       "(largo plazo + 1.5; 25_BB_DISTRIBUCIONES, DIST-IDENTIFICAR, y CAP-NIVEL-SIGMA).", "conclusion"))
            if not normal:
                bloques.append(b_texto("Los datos no son normales: las probabilidades calculadas con la normal no son confiables.", "aviso"))
        bloques.append(b_texto("Criterio p > 0.05: 25_BB_DISTRIBUCIONES, DIST-IDENTIFICAR. La prueba de Anderson-Darling y su "
                               "valor p (D'Agostino y Stephens) no están en la base. Clases del histograma: 16_GB, HIST-PROCEDIMIENTO "
                               f"(K = {len(bordes) - 1}, ancho {num(w)}). La identificación de lognormal y Weibull queda fuera del MVP."))
        avisos = _fuera(fuera)
        if len(x) < 30: avisos.append("Hay menos de 30 datos; los ejemplos del curso usan de 30 a 150.")
        return resultado(cls.ID, f"Normalidad de {nom}", p, bloques, avisos, datos={"columnas": [j]}, png=png)


@registrar
class MsaAtributos(ModuloDialogo):
    ID, TITULO = "MSA-ATR", "MSA de atributos"
    CAMPOS = [{"campo": "ref", "etiqueta": "Valor de referencia conocido (opcional)", "tipo": "col", "opcional": True}] + [
        {"campo": f"e{k}_t{t}", "etiqueta": f"Evaluador {k}, ronda {t}" + ("" if k == 1 else " (opcional)"),
         "tipo": "col", "opcional": k > 1} for k in (1, 2, 3) for t in (1, 2)] + [
        {"campo": "pasa", "etiqueta": "Valor que significa «pasa» (para falsos positivos y negativos)", "tipo": "texto"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        evs = OrderedDict()
        for k in (1, 2, 3):
            a, b = p.get(f"e{k}_t1"), p.get(f"e{k}_t2")
            if a in (None, "") and b in (None, ""):
                if k == 1: raise ErrorEntrada("Falta elegir las dos rondas del evaluador 1.")
                continue
            if a in (None, "") or b in (None, ""): raise ErrorEntrada(f"El evaluador {k} necesita sus dos rondas.")
            columna(hoja, a, f"la ronda 1 del evaluador {k}"); columna(hoja, b, f"la ronda 2 del evaluador {k}")
            nom = (hoja.columnas[a].nombre or f"Evaluador {k}").rsplit("_", 1)[0].strip() or f"Evaluador {k}"
            if nom in evs: nom = f"{nom} ({k})"
            evs[nom] = (a, b)
        usadas = [c for par in evs.values() for c in par]
        if len(set(usadas)) != len(usadas): raise ErrorEntrada("Cada ronda debe estar en una columna distinta.")
        rj = p.get("ref"); rc = columna(hoja, rj, "la referencia", obligatoria=False)
        cols = usadas + ([rj] if rc else [])
        texto = lambda c, i: hoja.columnas[c].valor(i)[0].strip()
        filas = [i for i in range(hoja.n) if all(texto(c, i) for c in cols)]
        incompletas = sum(1 for i in range(hoja.n) if any(texto(c, i) for c in cols)) - len(filas)
        if len(filas) < 5: raise ErrorEntrada("Hay menos de 5 muestras completas; el curso pide de 30 a 50 (14_GB_MEDIR, MED-RR-ATRIBUTO).")
        datos = {nom: [[texto(a, i) for i in filas], [texto(b, i) for i in filas]] for nom, (a, b) in evs.items()}
        ref = [texto(rj, i) for i in filas] if rc else None
        pasa = (p.get("pasa") or "").strip() or None
        valores = {v for r in datos.values() for ronda in r for v in ronda} | set(ref or [])
        avisos = [f"{incompletas} muestras incompletas quedaron fuera."] if incompletas else []
        if pasa and pasa not in valores:
            avisos.append(f"El valor «{pasa}» no aparece en los datos; no se clasifican falsos positivos y negativos."); pasa = None
        r = E.msa_atributos(datos, ref, pasa)
        pct = lambda a: f"{a['k']} de {a['n']} ({a['pct']:.1f}%)"
        ic = lambda a: f"{a['ic_inf']:.1f}% a {a['ic_sup']:.1f}%"
        cab = ["Evaluador", "Consigo mismo", "IC 95%", "Kappa"] + (["Contra la referencia", "IC 95%"] if ref else []) + \
              (["Falso negativo", "Falso positivo", "Mixto"] if ref and pasa else ["Mixto"] if ref else [])
        tab = []
        for nom, e in r["evaluadores"].items():
            fila = [nom, pct(e["consigo"]), ic(e["consigo"]), e["kappa_consigo"] if e["kappa_consigo"] is not None else "—"]
            if ref: fila += [pct(e["vs_ref"]), ic(e["vs_ref"])]
            if ref and pasa: fila += [e["falso_negativo"], e["falso_positivo"], e["mixto"]]
            elif ref: fila += [e["mixto"]]
            tab.append(fila)
        globales = []
        if "entre" in r: globales.append(["Entre evaluadores", pct(r["entre"]), ic(r["entre"]), r["kappa_entre"]])
        if ref: globales.append(["Todos contra la referencia", pct(r["todos_vs_ref"]), ic(r["todos_vs_ref"]), "—"])
        ks = [e["kappa_consigo"] for e in r["evaluadores"].values() if e["kappa_consigo"] is not None]
        if "kappa_entre" in r and r["kappa_entre"] is not None: ks.append(r["kappa_entre"])
        peor = min(ks) if ks else None
        if peor is None: concl = "No se pudo calcular el grado de acuerdo."
        elif peor > 0.90: concl = f"Acuerdo ideal: el menor kappa es {peor:.2f} (mayor a 0.90)."
        elif peor >= 0.75: concl = f"Acuerdo apropiado: el menor kappa es {peor:.2f} (al menos 0.75; ideal mayor a 0.90)."
        else: concl = f"El sistema de medición no es aceptable: el menor kappa es {peor:.2f} (menor a 0.75). Conviene entrenar y repetir el estudio."
        bloques = [b_texto(concl, "conclusion"), b_tabla("Acuerdo por evaluador", cab, tab)]
        if globales: bloques.append(b_tabla("Acuerdo global", ["Comparación", "Acuerdo", "IC 95%", "Kappa"], globales))
        if not ref: bloques.append(b_texto("Sin valor de referencia solo se evalúa el acuerdo entre inspectores, no la exactitud "
                                           "contra el estándar (PL16, revisión de calidad).", "aviso"))
        bloques.append(b_texto("Procedimiento y criterio (al menos 0.75 apropiado, más de 0.90 ideal): 14_GB_MEDIR, MED-RR-ATRIBUTO. "
                               "Acuerdos, IC de Wilson y clasificación de desacuerdos: PL16, MSA-RR-ATRIBUTO-GB (la base nombra los "
                               "conceptos pero no da fórmulas). Kappa de Fleiss, fórmula de Wilson y definiciones de falso negativo "
                               "(rechazó en todas sus rondas una muestra que pasa), falso positivo (aceptó en todas sus rondas una que "
                               "no pasa) y mixto (sus rondas no coinciden): no respaldados por la base."))
        if len(filas) < 30: avisos.append(f"Hay {len(filas)} muestras; el curso pide de 30 a 50.")
        return resultado(cls.ID, "MSA de atributos", p, bloques, avisos, datos={"columnas": cols})
