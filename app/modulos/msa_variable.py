"""Gage R&R de variable, diseño cruzado, método ANOVA de dos factores (pieza x evaluador).
Criterio de aceptación: 14_GB_MEDIR, MED-RR-VARIABLE (10% o menos aceptable; entre 10% y 30% marginal; más de 30%
inaceptable). La base trae las calculadoras por promedio-rango y ANOVA (PL16) pero no sus fórmulas ni datos crudos.
[GENERAL, no respaldado por la base]: componentes de varianza por cuadrados medios esperados, el criterio de quitar la
interacción (alfa = 0.25), ndc = 1.41·σpieza/σR&R y %Tolerancia = 6σ/tolerancia. Verificado contra las sumas de cuadrados y
los resultados de Minitab publicados en Industrial Statistics with Minitab (cap. 13, archivo RR_CROSSED)."""
import math
from collections import OrderedDict
from scipy import stats as st
from . import registrar
from .base import (ErrorEntrada, columna, filas_validas, valor, figura, a_svg_png, num, p_igual, p_texto, resultado,
                   b_grafica, b_tabla, b_texto, NARANJA, TINTA, SUAVE, CLARO, PALETA)
from .dialogo import ModuloDialogo
from ..nucleo.seguimiento import ensayo_destructivo


def componentes(ss_p, ss_o, ss_po, ss_e, p, o, r, alfa_inter=0.25):
    """Componentes de varianza del modelo cruzado con efectos aleatorios. p piezas, o evaluadores, r repeticiones."""
    gl_p, gl_o, gl_po = p - 1, o - 1, (p - 1) * (o - 1); gl_e = p * o * (r - 1)
    ms_p, ms_o, ms_po, ms_e = ss_p / gl_p, ss_o / gl_o, ss_po / gl_po, ss_e / gl_e
    f_po = ms_po / ms_e if ms_e > 0 else float("inf"); p_po = float(st.f.sf(f_po, gl_po, gl_e))
    con_inter = p_po < alfa_inter
    if con_inter:
        v_e = ms_e; v_po = max(0.0, (ms_po - ms_e) / r); v_o = max(0.0, (ms_o - ms_po) / (p * r)); v_p = max(0.0, (ms_p - ms_po) / (o * r))
        tabla = [("Pieza", gl_p, ss_p, ms_p, ms_p / ms_po, float(st.f.sf(ms_p / ms_po, gl_p, gl_po))),
                 ("Evaluador", gl_o, ss_o, ms_o, ms_o / ms_po, float(st.f.sf(ms_o / ms_po, gl_o, gl_po))),
                 ("Pieza*Evaluador", gl_po, ss_po, ms_po, f_po, p_po), ("Repetibilidad", gl_e, ss_e, ms_e, None, None)]
    else:
        gl_e2 = gl_po + gl_e; ms_e2 = (ss_po + ss_e) / gl_e2
        v_e = ms_e2; v_po = 0.0; v_o = max(0.0, (ms_o - ms_e2) / (p * r)); v_p = max(0.0, (ms_p - ms_e2) / (o * r))
        tabla = [("Pieza", gl_p, ss_p, ms_p, ms_p / ms_e2, float(st.f.sf(ms_p / ms_e2, gl_p, gl_e2))),
                 ("Evaluador", gl_o, ss_o, ms_o, ms_o / ms_e2, float(st.f.sf(ms_o / ms_e2, gl_o, gl_e2))),
                 ("Repetibilidad", gl_e2, ss_po + ss_e, ms_e2, None, None)]
    v_repro = v_o + v_po; v_grr = v_e + v_repro; v_tot = v_grr + v_p
    return {"con_inter": con_inter, "p_inter": p_po, "tabla": tabla, "v_rep": v_e, "v_o": v_o, "v_po": v_po, "v_repro": v_repro,
            "v_grr": v_grr, "v_p": v_p, "v_tot": v_tot, "p": p, "o": o, "r": r, "ss_total": ss_p + ss_o + ss_po + ss_e}


def resumen(c, tolerancia=None, k=6.0):
    """Tabla de fuentes con desviaciones, variación del estudio (k·σ), %contribución, %variación del estudio y %tolerancia; ndc."""
    filas = []
    for nombre, v in (("R&R total", c["v_grr"]), ("  Repetibilidad", c["v_rep"]), ("  Reproducibilidad", c["v_repro"]),
                      ("    Evaluador", c["v_o"]), ("    Pieza*Evaluador", c["v_po"]), ("Pieza a pieza", c["v_p"]), ("Variación total", c["v_tot"])):
        sd = math.sqrt(v)
        filas.append({"fuente": nombre, "var": v, "sd": sd, "sv": k * sd, "pct_contrib": 100 * v / c["v_tot"] if c["v_tot"] else float("nan"),
                      "pct_sv": 100 * sd / math.sqrt(c["v_tot"]) if c["v_tot"] else float("nan"),
                      "pct_tol": 100 * k * sd / tolerancia if tolerancia else None})
    sd_p, sd_g = math.sqrt(c["v_p"]), math.sqrt(c["v_grr"])
    ndc = int(math.floor(1.41 * sd_p / sd_g)) if sd_g > 0 else None
    return filas, ndc


def clasificar(pct):
    """[BASE] MED-RR-VARIABLE: 10% o menos aceptable; entre 10% y 30% marginal; más de 30% inaceptable."""
    return "aceptable" if pct <= 10 else "marginal" if pct <= 30 else "inaceptable"


def anova_dos_factores(datos):
    """datos: {(pieza, evaluador): [mediciones]} balanceado. Devuelve sumas de cuadrados y tamaños."""
    piezas = sorted({k[0] for k in datos}, key=str); ops = sorted({k[1] for k in datos}, key=str)
    p, o = len(piezas), len(ops); r = len(next(iter(datos.values())))
    todos = [v for g in datos.values() for v in g]; gm = sum(todos) / len(todos)
    mp = {i: sum(v for (a, _), g in datos.items() if a == i for v in g) / (o * r) for i in piezas}
    mo = {j: sum(v for (_, b), g in datos.items() if b == j for v in g) / (p * r) for j in ops}
    mc = {k: sum(g) / r for k, g in datos.items()}
    ss_p = o * r * sum((m - gm) ** 2 for m in mp.values()); ss_o = p * r * sum((m - gm) ** 2 for m in mo.values())
    ss_po = r * sum((mc[(i, j)] - mp[i] - mo[j] + gm) ** 2 for i in piezas for j in ops)
    ss_e = sum((v - mc[k]) ** 2 for k, g in datos.items() for v in g)
    return {"ss_p": ss_p, "ss_o": ss_o, "ss_po": ss_po, "ss_e": ss_e, "p": p, "o": o, "r": r, "piezas": piezas, "ops": ops, "medias_celda": mc,
            "media_pieza": mp, "media_op": mo, "gran_media": gm}


AVISO_DESTRUCTIVO = ("Ensayo destructivo: la variable «{variable}» está declarada como ensayo destructivo. Las probetas no son equivalentes a mediciones "
                     "repetidas de la misma pieza, por lo que el diseño cruzado de este Gage R&R no aplica y su resultado no debe leerse como evaluación del "
                     "sistema de medición. El estudio necesita otro diseño (anidado); el Gage R&R anidado está diferido y no respaldado por la base "
                     "(no hay fuente del curso verificada en el repositorio). Este aviso no bloquea el cálculo.")


@registrar
class GageRR(ModuloDialogo):
    ID, TITULO = "MSA-VAR", "Gage R&R de variable (cruzado)"
    CAMPOS = [{"campo": "pieza", "etiqueta": "Pieza o muestra", "tipo": "col", "rol": ["factor"]},
              {"campo": "evaluador", "etiqueta": "Evaluador (operador)", "tipo": "col", "rol": ["bloque"]},
              {"campo": "y", "etiqueta": "Medición", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "tol", "etiqueta": "Tolerancia = LSE - LIE (opcional; para %Tolerancia)", "tipo": "numero"},
              {"campo": "k", "etiqueta": "Múltiplo de sigma para la variación del estudio", "tipo": "opcion", "defecto": "6",
               "opciones": [["6", "6 (99.73% de la variación; por omisión)"], ["5.15", "5.15 (99%)"]]},
              {"campo": "alfa", "etiqueta": "Alfa para conservar la interacción pieza*evaluador", "tipo": "opcion", "defecto": "0.25",
               "opciones": [["0.25", "0.25 (por omisión)"], ["0.05", "0.05"], ["1", "Siempre conservarla"]]}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        jp, jo, jy = p.get("pieza"), p.get("evaluador"), p.get("y")
        columna(hoja, jp, "la pieza"); columna(hoja, jo, "el evaluador"); columna(hoja, jy, "la medición", "num")
        if len({jp, jo, jy}) < 3: raise ErrorEntrada("Pieza, evaluador y medición deben ser columnas distintas.")
        tol = cls.numero(p, "tol", "La tolerancia", minimo=0)
        k = float(p.get("k") or 6); alfa = float(p.get("alfa") or 0.25)
        filas, fuera = filas_validas(hoja, [jp, jo, jy])
        datos = OrderedDict()
        for i in filas: datos.setdefault((str(valor(hoja, jp, i)), str(valor(hoja, jo, i))), []).append(valor(hoja, jy, i))
        piezas = {a for a, _ in datos}; ops = {b for _, b in datos}
        if len(piezas) < 2 or len(ops) < 2: raise ErrorEntrada("Se necesitan al menos 2 piezas y 2 evaluadores (el curso usa 10 piezas y 2 o 3 evaluadores).")
        faltan = [f"{a}/{b}" for a in sorted(piezas) for b in sorted(ops) if (a, b) not in datos]
        tam = {len(v) for v in datos.values()}
        if faltan or len(tam) > 1:
            raise ErrorEntrada("El estudio debe estar balanceado: cada pieza medida por cada evaluador el mismo número de veces"
                               + (f" (faltan {', '.join(faltan[:5])})" if faltan else "") + ".")
        if min(tam) < 2: raise ErrorEntrada("Cada evaluador debe medir cada pieza al menos 2 veces para estimar la repetibilidad.")
        a = anova_dos_factores(datos)
        c = componentes(a["ss_p"], a["ss_o"], a["ss_po"], a["ss_e"], a["p"], a["o"], a["r"], alfa)
        filas_r, ndc = resumen(c, tol, k)
        if c["v_tot"] <= 0: raise ErrorEntrada("No hay variación en los datos.")
        nom = hoja.columnas[jy].nombre or f"C{jy + 1}"
        # ---------- tablas ----------
        anova = [[n_, g, num(ss, 7), num(ms, 7), num(f, 4) if f is not None else "", p_texto(pv) if pv is not None else ""] for n_, g, ss, ms, f, pv in c["tabla"]]
        anova.append(["Total", a["p"] * a["o"] * a["r"] - 1, num(c["ss_total"], 7), "", "", ""])
        cab_c = ["Fuente", "Varianza", "% contribución"]
        comp = [[f["fuente"], num(f["var"], 7), f"{f['pct_contrib']:.2f}"] for f in filas_r]
        cab_s = ["Fuente", "Desv. est.", f"Variación del estudio ({k:g}σ)", "% variación del estudio"] + (["% tolerancia"] if tol else [])
        sv = [[f["fuente"], num(f["sd"], 7), num(f["sv"], 7), f"{f['pct_sv']:.2f}"] + ([f"{f['pct_tol']:.2f}"] if tol else []) for f in filas_r]
        # ---------- gráficas ----------
        fig, axs = figura(10.0, 7.2, nrows=2, ncols=3)
        nombres = ["R&R", "Repet.", "Reprod.", "Pieza"]; sel = [filas_r[0], filas_r[1], filas_r[2], filas_r[5]]
        ancho = 0.27
        for q, (et, clave, col) in enumerate((("% contribución", "pct_contrib", NARANJA), ("% var. estudio", "pct_sv", TINTA)) + ((("% tolerancia", "pct_tol", SUAVE),) if tol else ())):
            axs[0][0].bar([x + (q - 1) * ancho for x in range(4)], [f[clave] for f in sel], ancho, label=et, color=col)
        axs[0][0].set_xticks(range(4)); axs[0][0].set_xticklabels(nombres); axs[0][0].legend(fontsize=6, frameon=False); axs[0][0].set_title("Componentes de variación", fontsize=8)
        ops = a["ops"]; piezas_o = a["piezas"]; colores = {o_: PALETA[i % len(PALETA)] for i, o_ in enumerate(ops)}
        # carta R por evaluador
        for i_o, o_ in enumerate(ops):
            rg = [max(datos[(pz, o_)]) - min(datos[(pz, o_)]) for pz in piezas_o]
            axs[0][1].plot(range(1, len(rg) + 1), rg, marker="o", ms=3, lw=1, color=colores[o_], label=str(o_))
        rb = sum(max(g) - min(g) for g in datos.values()) / len(datos)
        from .spc import D4
        axs[0][1].axhline(rb, color=TINTA, lw=0.8); axs[0][1].axhline(D4[a["r"]] * rb if a["r"] in D4 else rb * 3, color="#b3261e", lw=0.8, ls="--")
        axs[0][1].set_title("Carta R por evaluador", fontsize=8); axs[0][1].legend(fontsize=6, frameon=False)
        for o_ in ops:
            axs[0][2].plot(range(1, len(piezas_o) + 1), [a["medias_celda"][(pz, o_)] for pz in piezas_o], marker="o", ms=3, lw=1, color=colores[o_], label=str(o_))
        mg = a["gran_media"]; sx = c["v_rep"] ** 0.5 / math.sqrt(a["r"])
        axs[0][2].axhline(mg, color=TINTA, lw=0.8); axs[0][2].axhline(mg + 3 * sx, color="#b3261e", lw=0.8, ls="--"); axs[0][2].axhline(mg - 3 * sx, color="#b3261e", lw=0.8, ls="--")
        axs[0][2].set_title("Carta X̄ por evaluador (límites con la repetibilidad)", fontsize=8)
        # mediciones por pieza, por evaluador, interacción
        for q, pz in enumerate(piezas_o): axs[1][0].scatter([q + 1] * len(sum((datos[(pz, o_)] for o_ in ops), [])), sum((datos[(pz, o_)] for o_ in ops), []), s=8, color=NARANJA, alpha=0.6)
        axs[1][0].plot(range(1, len(piezas_o) + 1), [a["media_pieza"][pz] for pz in piezas_o], color=TINTA, lw=1); axs[1][0].set_title("Mediciones por pieza", fontsize=8)
        axs[1][1].boxplot([sum((datos[(pz, o_)] for pz in piezas_o), []) for o_ in ops], patch_artist=True, medianprops={"color": NARANJA},
                          boxprops={"facecolor": CLARO, "edgecolor": NARANJA}); axs[1][1].set_xticklabels([str(o_) for o_ in ops]); axs[1][1].set_title("Mediciones por evaluador", fontsize=8)
        for o_ in ops: axs[1][2].plot(range(1, len(piezas_o) + 1), [a["medias_celda"][(pz, o_)] for pz in piezas_o], marker="o", ms=3, lw=1, color=colores[o_], label=str(o_))
        axs[1][2].legend(fontsize=6, frameon=False); axs[1][2].set_title("Interacción pieza * evaluador", fontsize=8)
        for ax in axs.flat: ax.tick_params(labelsize=6)
        svg, png = a_svg_png(fig)
        # ---------- conclusión (14_GB MED-RR-VARIABLE) ----------
        base_pct = filas_r[0]["pct_tol"] if tol else filas_r[0]["pct_sv"]
        que = "tolerancia" if tol else "variación del estudio"
        concl = (f"El R&R total es {base_pct:.2f}% de la {que}: sistema de medición {clasificar(base_pct)} (14_GB MED-RR-VARIABLE: 10% o menos "
                 f"aceptable; de 10% a 30% marginal; más de 30% inaceptable). Repetibilidad {(filas_r[1]['pct_tol'] if tol else filas_r[1]['pct_sv']):.2f}% y "
                 f"reproducibilidad {(filas_r[2]['pct_tol'] if tol else filas_r[2]['pct_sv']):.2f}%. "
                 + (f"Categorías distintas (ndc) = {ndc}: " + ("el sistema distingue bien las piezas (5 o más)." if ndc >= 5 else "son pocas; se recomienda al menos 5.") if ndc is not None else ""))
        interp = []
        if c["v_rep"] > c["v_repro"] * 1.5: interp.append("La repetibilidad domina: revisa el instrumento (calibración, resolución, desgaste) y el método de medición.")
        elif c["v_repro"] > c["v_rep"] * 1.5: interp.append("La reproducibilidad domina: los evaluadores miden distinto; entrénalos y estandariza el procedimiento.")
        interp.append("La interacción pieza*evaluador " + (f"es significativa ({p_igual(c['p_inter'])}) y se incluye en el modelo: algunos evaluadores miden distinto ciertas piezas."
                      if c["con_inter"] else f"no es significativa ({p_igual(c['p_inter'])}, alfa {alfa:g}); se quitó del modelo y se agregó al error."))
        if not tol: interp.append("Sin tolerancia no se puede calcular el %Tolerancia; el curso lo juzga contra el rango de especificación (indica LSE - LIE).")
        avisos = [f"{fuera} filas incompletas quedaron fuera."] if fuera else []
        if a["p"] < 10: avisos.append(f"Hay {a['p']} piezas; el curso usa 10 que cubran el rango de la especificación (MED-RR-VARIABLE).")
        if a["r"] < 2 or a["o"] < 2: avisos.append("Se recomiendan al menos 2 evaluadores y 2 repeticiones.")
        supuestos = [("Piezas que representan el rango del proceso", "Lo define el muestreo del estudio", "Revísalo: piezas muy parecidas inflan el %R&R"),
                     ("Mediciones independientes y en orden aleatorio", "Procedimiento del estudio", "Mide en orden aleatorio, sin que el evaluador sepa la pieza"),
                     ("Residuos aproximadamente normales", "Gráficas del estudio", "Revisa las mediciones por pieza y por evaluador")]
        destructivo = ensayo_destructivo(proyecto, hoja.columnas[jy].nombre)
        if destructivo is not None:
            avisos.append(AVISO_DESTRUCTIVO.format(variable=destructivo.get("nombre")))
        res = resultado(cls.ID, f"Gage R&R de {nom}", p, [
            b_grafica(svg), b_texto(concl, "conclusion"),
            b_tabla("ANOVA de dos factores" + (" con interacción" if c["con_inter"] else " sin interacción"), ["Fuente", "GL", "SC", "CM", "F", "Valor p"], anova),
            b_tabla("Componentes de varianza", cab_c, comp), b_tabla("Variación del estudio", cab_s, sv),
            b_texto("Método ANOVA. Criterio de aceptación: 14_GB_MEDIR, MED-RR-VARIABLE. No respaldados por la base: componentes de varianza por "
                    "cuadrados medios esperados, alfa de la interacción, ndc = 1.41·σpieza/σR&R, %tolerancia = kσ/tolerancia y las gráficas.")],
            avisos, supuestos=supuestos, interpretacion=interp, datos={"columnas": [jp, jo, jy], "ndc": ndc}, png=png)
        if destructivo is not None:                       # E3-1 (Decisión 4): nunca bloquea; deja el aviso visible y trazable en el resultado
            res["bloques"].append(b_texto(AVISO_DESTRUCTIVO.format(variable=destructivo.get("nombre")), "advertencia"))
            res["datos"]["ensayo_destructivo"] = {"variable": destructivo.get("nombre"), "cruzado_aplica": False}
        return res
