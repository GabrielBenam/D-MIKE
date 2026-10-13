"""Módulos de gráficas y estadística básica: ESTADISTICOS (Calc), CORRIDA, BOXPLOT, PARETO."""
from collections import OrderedDict
from . import registrar, estadistica as E
from .base import _f
from .base import (ErrorEntrada, columna, nombre_col, filas_validas, valor, figura, a_svg_png, num, p_texto,
                   resultado, b_grafica, b_tabla, b_texto, NARANJA, TINTA, SUAVE, CLARO, PALETA)
from .dialogo import ModuloDialogo


def _excluidas_msg(fuera, que="fila"):
    return [f"{fuera} {que}s con valores faltantes o que no corresponden a su tipo quedaron fuera del cálculo."] if fuera else []


@registrar
class Estadisticos(ModuloDialogo):
    ID, TITULO = "ESTADISTICOS", "Estadísticos de columna"
    CAMPOS = [{"campo": "y", "etiqueta": "Variable", "tipo": "col", "filtro": "num", "rol": ["respuesta", "covariable"]},
              {"campo": "grupo", "etiqueta": "Por grupo (opcional)", "tipo": "col", "filtro": "texto", "opcional": True}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        j = p.get("y"); columna(hoja, j, "la variable", "num")
        g = p.get("grupo"); gcol = columna(hoja, g, "el grupo", obligatoria=False)
        cols = [j] + ([g] if gcol else [])
        filas, fuera = filas_validas(hoja, cols)
        grupos = OrderedDict()
        for i in filas: grupos.setdefault(str(valor(hoja, g, i)) if gcol else "Todos", []).append(valor(hoja, j, i))
        if not grupos: raise ErrorEntrada(f"{nombre_col(hoja, j)} no tiene datos numéricos válidos.")
        faltan = OrderedDict()
        for i in range(hoja.n):
            vy = hoja.columnas[j].valor(i)
            if vy[1] and vy[2] is not None: continue
            if not vy[0].strip() and not (gcol and hoja.columnas[g].valor(i)[0].strip()): continue
            if not gcol: k = "Todos"
            else: k = str(valor(hoja, g, i)) if hoja.columnas[g].valor(i)[2] is not None else "(sin grupo)"
            faltan[k] = faltan.get(k, 0) + 1
        cab = ["Grupo", "N", "N faltante", "Media", "EE de la media", "Desv. est.", "Varianza", "CV (%)", "Suma", "Mínimo", "Q1",
               "Mediana", "Q3", "Máximo", "Rango", "RIC", "Asimetría", "Curtosis", "Moda"]
        tab = []
        for k, x in grupos.items():
            d = E.descriptivos(x)
            moda = ", ".join(num(m) for m in d["modas"][:3]) + ("…" if len(d["modas"]) > 3 else "") if d["modas"] else "sin moda"
            tab.append([k, d["n"], faltan.get(k, 0), d["media"], d["ee_media"], d["desv"], d["varianza"], d["cv"], d["suma"], d["minimo"],
                        d["q1"], d["mediana"], d["q3"], d["maximo"], d["rango"], d["ric"], d["asimetria"], d["curtosis"], moda])
        titulo = f"Estadísticos de {hoja.columnas[j].nombre or nombre_col(hoja, j)}"
        return resultado(cls.ID, titulo, p, [
            b_tabla("Estadísticos descriptivos", cab, tab),
            b_texto("Media, mediana, moda, rango, desviación estándar y varianza (n-1): 15_GB_ESTADISTICA_Y_MUESTREO, "
                    "EST-CENTRAL y EST-VARIABILIDAD. No respaldados por la base: cuartiles (método de Minitab), error estándar, CV, "
                    "asimetría y curtosis corregidas por sesgo (la curtosis se reporta como exceso: 0 en una normal).")],
            _excluidas_msg(fuera), datos={"columnas": cols})


@registrar
class Corrida(ModuloDialogo):
    ID, TITULO = "CORRIDA", "Gráfica de corrida"
    CAMPOS = [{"campo": "y", "etiqueta": "Variable (en orden cronológico)", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "x", "etiqueta": "Etiquetas del eje (opcional)", "tipo": "col", "opcional": True, "rol": ["id"]}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        j = p.get("y"); columna(hoja, j, "la variable", "num")
        xj = p.get("x"); xc = columna(hoja, xj, "las etiquetas", obligatoria=False)
        filas, fuera = filas_validas(hoja, [j])
        y = [valor(hoja, j, i) for i in filas]
        if len(y) < 3: raise ErrorEntrada("La gráfica de corrida necesita al menos 3 datos válidos.")
        r = E.corridas(y)
        etiquetas = [xc.valor(i)[0] for i in filas] if xc else [str(i + 1) for i in filas]
        fig, ax = figura(7.2, 3.6)
        pos = list(range(1, len(y) + 1))
        ax.plot(pos, y, color=NARANJA, lw=1.4, marker="o", ms=4, mfc="white", mec=NARANJA)
        ax.axhline(r["mediana"], color=TINTA, lw=1, ls="--")
        ax.text(pos[-1], r["mediana"], f"  Mediana {num(r['mediana'])}", va="center", fontsize=8, color=TINTA)
        paso = max(1, len(pos) // 12)
        ax.set_xticks(pos[::paso]); ax.set_xticklabels(etiquetas[::paso], rotation=30 if xc else 0, ha="right" if xc else "center", fontsize=8)
        nom = hoja.columnas[j].nombre or nombre_col(hoja, j)
        ax.set_ylabel(nom); ax.set_title(f"Gráfica de corrida de {nom}")
        svg, png = a_svg_png(fig)
        pruebas = [["Corridas sobre la mediana", r["corridas_mediana"], r.get("esperadas_mediana"),
                    p_texto(r["p_agrupamiento"]) if "p_agrupamiento" in r else "—", p_texto(r["p_mezcla"]) if "p_mezcla" in r else "—"],
                   ["Corridas arriba o abajo", r.get("corridas_arriba_abajo", "—"), r.get("esperadas_arriba_abajo"),
                    p_texto(r["p_tendencia"]) if "p_tendencia" in r else "—", p_texto(r["p_oscilacion"]) if "p_oscilacion" in r else "—"]]
        concl = []
        if r["hay_racha"]: concl.append(f"Hay una racha de {r['racha_max']} puntos seguidos del mismo lado de la mediana (8 o más).")
        if r["hay_tendencia"]: concl.append(f"Hay una tendencia de {r['tendencia_max']} puntos seguidos sin cambio de dirección (6 o más).")
        for clave, txt in (("p_agrupamiento", "agrupamiento"), ("p_mezcla", "mezcla"), ("p_tendencia", "tendencias"), ("p_oscilacion", "oscilación")):
            if clave in r and r[clave] < 0.05: concl.append(f"La prueba de {txt} es significativa (p < 0.05).")
        if not concl: concl.append("No se observan rachas, tendencias ni patrones no aleatorios con estos criterios.")
        return resultado(cls.ID, f"Gráfica de corrida de {nom}", p, [
            b_grafica(svg, {"g": "corrida", "titulo": f"Gráfica de corrida de {nom}", "yl": nom, "y": [_f(v) for v in y], "etiq": etiquetas, "mediana": _f(r["mediana"])}),
            b_texto(" ".join(concl), "conclusion"),
            b_tabla("Patrones (19_GB_CONTROLAR, SPC-PATRONES, aplicados sobre la mediana)", ["Patrón", "Observado", "Criterio"],
                    [["Racha más larga del mismo lado", r["racha_max"], "8 o más"],
                     ["Puntos seguidos sin cambio de dirección", r["tendencia_max"], "6 o más"]]),
            b_tabla("Pruebas de corridas (no respaldadas por la base; aproximación normal de Minitab)",
                    ["Prueba", "Corridas", "Esperadas", "p agrupamiento / tendencia", "p mezcla / oscilación"], pruebas),
            b_texto("La base no trae teoría propia de la gráfica de corrida: los patrones se toman de las reglas de cartas de "
                    "control de 19_GB_CONTROLAR con la mediana como línea central. Los puntos iguales a la mediana no cuentan "
                    "en las corridas sobre la mediana.")], _excluidas_msg(fuera), datos={"columnas": [j] + ([xj] if xc else [])}, png=png)


@registrar
class Caja(ModuloDialogo):
    ID, TITULO = "BOXPLOT", "Diagrama de caja"
    CAMPOS = [{"campo": "y", "etiqueta": "Respuesta", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "grupo", "etiqueta": "Agrupar por (opcional)", "tipo": "col", "filtro": "texto", "opcional": True, "rol": ["factor"]},
              {"campo": "separar", "etiqueta": "Separar por (opcional)", "tipo": "col", "filtro": "texto", "opcional": True, "rol": ["bloque"]},
              {"campo": "puntos", "etiqueta": "Mostrar puntos individuales", "tipo": "bool", "defecto": True}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        j = p.get("y"); columna(hoja, j, "la respuesta", "num")
        g, s = p.get("grupo"), p.get("separar")
        gc = columna(hoja, g, "el grupo", obligatoria=False); sc = columna(hoja, s, "la separación", obligatoria=False)
        if gc and sc and g == s: raise ErrorEntrada("Agrupar y separar deben ser columnas distintas.")
        cols = [j] + ([g] if gc else []) + ([s] if sc else [])
        filas, fuera = filas_validas(hoja, cols)
        grupos = OrderedDict()
        for i in filas:
            k = " / ".join(str(valor(hoja, c, i)) for c in cols[1:]) or (hoja.columnas[j].nombre or "Datos")
            grupos.setdefault(k, []).append(valor(hoja, j, i))
        if not grupos: raise ErrorEntrada(f"{nombre_col(hoja, j)} no tiene datos numéricos válidos.")
        if len(grupos) > 30: raise ErrorEntrada("Hay más de 30 grupos; revisa la columna de agrupación.")
        cortos = [k for k, x in grupos.items() if len(x) < 4]
        stats = {k: E.caja(x) for k, x in grupos.items()}
        fig, ax = figura(max(4.8, 1.1 * len(grupos) + 2.4), 3.8)
        ks = list(grupos)
        bp = ax.boxplot([grupos[k] for k in ks], widths=0.5, patch_artist=True, whis=1.5,
                        medianprops={"color": NARANJA, "lw": 2}, boxprops={"facecolor": CLARO, "edgecolor": NARANJA},
                        whiskerprops={"color": SUAVE}, capprops={"color": SUAVE},
                        flierprops={"marker": "*", "mec": TINTA, "mfc": TINTA, "ms": 7})
        if p.get("puntos", True):
            import random
            rnd = random.Random(0)
            for n, k in enumerate(ks, 1):
                ax.scatter([n + rnd.uniform(-0.08, 0.08) for _ in grupos[k]], grupos[k], s=10, color=TINTA, alpha=0.45, zorder=3)
        ax.set_xticks(range(1, len(ks) + 1)); ax.set_xticklabels(ks, rotation=30 if len(ks) > 6 else 0, ha="right" if len(ks) > 6 else "center")
        nom = hoja.columnas[j].nombre or nombre_col(hoja, j)
        por = " por " + " y ".join(hoja.columnas[c].nombre or f"C{c + 1}" for c in cols[1:]) if len(cols) > 1 else ""
        ax.set_ylabel(nom); ax.set_title(f"Diagrama de caja de {nom}{por}")
        svg, png = a_svg_png(fig)
        tab = [[k, d["n"], d["minimo"], d["q1"], d["mediana"], d["q3"], d["maximo"], d["ric"], len(d["atipicos"])] for k, d in stats.items()]
        avisos = _excluidas_msg(fuera)
        if cortos: avisos.append(f"Grupos con menos de 4 datos ({', '.join(cortos)}): sus cuartiles son poco confiables.")
        at = [f"{k}: {', '.join(num(v) for v in d['atipicos'])}" for k, d in stats.items() if d["atipicos"]]
        return resultado(cls.ID, f"Diagrama de caja de {nom}{por}", p, [
            b_grafica(svg, {"g": "caja", "titulo": f"Diagrama de caja de {nom}{por}", "yl": nom, "grupos": {k: [_f(v) for v in grupos[k]] for k in ks}}),
            b_tabla("Estadísticos por grupo", ["Grupo", "N", "Mínimo", "Q1", "Mediana", "Q3", "Máximo", "RIC", "Atípicos"], tab),
            b_texto(("Valores atípicos (más allá de 1.5 veces el RIC): " + "; ".join(at) + ". Debe analizarse su causa raíz "
                     "(17_GB_ANALIZAR, BOX-INTERPRETACION).") if at else "No hay valores atípicos (más allá de 1.5 veces el RIC).", "conclusion"),
            b_texto("Bigotes hasta el dato más extremo dentro de 1.5 veces el rango intercuartílico: 17_GB_ANALIZAR, "
                    "BOX-PROCEDIMIENTO. Cuartiles con el método de Minitab (la base no fija el método).")],
            avisos, datos={"columnas": cols}, png=png)


@registrar
class Pareto(ModuloDialogo):
    ID, TITULO = "PARETO", "Diagrama de Pareto"
    CAMPOS = [{"campo": "cat", "etiqueta": "Categoría (defecto, causa o tipo)", "tipo": "col", "filtro": "texto", "rol": ["factor"]},
              {"campo": "frec", "etiqueta": "Frecuencia o costo (opcional; si no, cada fila cuenta 1)", "tipo": "col", "filtro": "num", "opcional": True},
              {"campo": "otros", "etiqueta": "Agrupar en «Otros» después de este % acumulado (vacío = no agrupar)", "tipo": "numero", "defecto": 95}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        c = p.get("cat"); columna(hoja, c, "la categoría", "texto")
        f = p.get("frec"); fc = columna(hoja, f, "la frecuencia", "num", obligatoria=False)
        otros = cls.numero(p, "otros", "El porcentaje para «Otros»", minimo=0, maximo=100.0001)
        filas, fuera = filas_validas(hoja, [c] + ([f] if fc else []))
        conteos = OrderedDict()
        neg = 0
        for i in filas:
            k = str(valor(hoja, c, i)); v = valor(hoja, f, i) if fc else 1
            if v < 0: neg += 1; continue
            conteos[k] = conteos.get(k, 0) + v
        if len([v for v in conteos.values() if v > 0]) < 2: raise ErrorEntrada("El Pareto necesita al menos 2 categorías con conteo mayor a cero.")
        r = E.pareto(conteos, otros)
        fl = r["filas"]
        fig, ax = figura(max(5.6, 0.7 * len(fl) + 2.5), 3.8)
        xs = list(range(len(fl)))
        ax.bar(xs, [x["conteo"] for x in fl], color=NARANJA, width=0.75)
        ax.set_xticks(xs); ax.set_xticklabels([x["categoria"] for x in fl], rotation=30 if len(fl) > 5 else 0, ha="right" if len(fl) > 5 else "center")
        ax.set_ylim(0, r["total"]); ax.set_ylabel("Frecuencia" if not fc else (hoja.columnas[f].nombre or "Frecuencia"))
        ax2 = ax.twinx(); ax2.plot(xs, [x["acum"] for x in fl], color=TINTA, marker="o", ms=4, lw=1.2)
        ax2.set_ylim(0, 100); ax2.set_ylabel("% acumulado"); ax2.grid(False); ax2.spines["right"].set_visible(True)
        nom = hoja.columnas[c].nombre or nombre_col(hoja, c)
        ax.set_title(f"Diagrama de Pareto de {nom}")
        svg, png = a_svg_png(fig)
        tab = [[x["categoria"], x["conteo"], x["pct"], x["acum"]] for x in fl]
        vitales = [x["categoria"] for x in fl if x["acum"] - x["pct"] < 80 and x["categoria"] != "Otros"]
        avisos = _excluidas_msg(fuera) + ([f"{neg} filas con frecuencia negativa quedaron fuera."] if neg else [])
        return resultado(cls.ID, f"Diagrama de Pareto de {nom}", p, [
            b_grafica(svg, {"g": "pareto", "titulo": f"Diagrama de Pareto de {nom}", "cat": [x["categoria"] for x in fl], "conteo": [_f(x["conteo"]) for x in fl],
                            "acum": [_f(x["acum"]) for x in fl], "yl": "Frecuencia" if not fc else (hoja.columnas[f].nombre or "Frecuencia")}),
            b_tabla("Tabla de Pareto", ["Categoría", "Conteo", "%", "% acumulado"], tab),
            b_texto(f"Las categorías que acumulan hasta el 80%: {', '.join(vitales)}.", "conclusion"),
            b_texto("La base menciona el Pareto (03_SOLUCION_PROBLEMAS, formato 4 Q's; PL08) pero no su cálculo: el orden, "
                    "los porcentajes, el corte del 80% y el agrupamiento en «Otros» (opción de Minitab) no están respaldados por la base.")],
            avisos, datos={"columnas": [c] + ([f] if fc else [])}, png=png)
