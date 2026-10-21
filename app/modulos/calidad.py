"""Módulos de control y capacidad: SPC (cartas I-MR, X̄-R, X̄-S, p, np, c, u) y CAPACIDAD (normal)."""
import math
from collections import OrderedDict
from . import registrar, spc as S, capacidad as C, estadistica as E
from .analisis import clases_histograma, _prob_normal
from .base import _f
from .base import (ErrorEntrada, columna, nombre_col, filas_validas, valor, figura, a_svg_png, num, p_igual,
                   resultado, b_grafica, b_tabla, b_texto, NARANJA, TINTA, SUAVE, CLARO)
from .dialogo import ModuloDialogo
from scipy import stats as st

ROJO = "#b3261e"
TIPOS = [["imr", "I-MR (individuales, n = 1)"], ["xr", "X̄-R (subgrupos de 2 a 10)"], ["xs", "X̄-S (subgrupos de más de 10)"],
         ["p", "p (unidades defectuosas, n variable)"], ["np", "np (unidades defectuosas, n constante)"],
         ["c", "c (defectos, n constante)"], ["u", "u (defectos, n variable)"]]
# G1 (19_GB_CONTROLAR, SPC-TIPOS-CARTA): el usuario declara qué cuenta. Defectos (errores, Poisson) -> c o u;
# unidades defectuosas (binomial) -> np o p. La declaración debe coincidir con la carta elegida.
CUENTA = [["", "Declarar qué se cuenta (obligatorio en p, np, c y u)"],
          ["defectuosas", "Unidades defectuosas: cada unidad es buena o mala (binomial)"],
          ["defectos", "Defectos o errores: una unidad puede tener varios (Poisson)"]]
CARTAS_CUENTA = {"p": "defectuosas", "np": "defectuosas", "c": "defectos", "u": "defectos"}
CARTA_SUGERIDA = {("defectuosas", True): "np", ("defectuosas", False): "p", ("defectos", True): "c", ("defectos", False): "u"}
OP_PRUEBAS = [[str(k), f"{k}. {t}"] for k, t in S.PRUEBAS.items()]


def subgrupos(hoja, j, tam, sub, etiqueta="los datos"):
    """Divide una columna en subgrupos: por tamaño constante (filas consecutivas) o por una columna de
    identificador (filas consecutivas con el mismo valor). Devuelve (subgrupos, etiquetas, filas excluidas)."""
    cols = [j] + ([sub] if sub is not None else [])
    filas, fuera = filas_validas(hoja, cols)
    if sub is not None:
        g = OrderedDict()
        for i in filas: g.setdefault(str(valor(hoja, sub, i)), []).append(valor(hoja, j, i))
        return list(g.values()), list(g), fuera
    x = [valor(hoja, j, i) for i in filas]
    if tam <= 1: return [[v] for v in x], [str(i + 1) for i in range(len(x))], fuera
    if len(x) % tam:
        raise ErrorEntrada(f"Hay {len(x)} datos, que no forman subgrupos completos de {tam}; revisa {etiqueta} o el tamaño.")
    return [x[i:i + tam] for i in range(0, len(x), tam)], [str(i // tam + 1) for i in range(0, len(x), tam)], fuera


def dibujar_carta(ax, c, etiquetas, viol, k=None, titulo=""):
    pts = c["puntos"]; xs = list(range(1, len(pts) + 1))
    xy = [(x, v) for x, v in zip(xs, pts) if v is not None]
    ax.plot([a for a, _ in xy], [b for _, b in xy], color=NARANJA, lw=1.2, marker="o", ms=3.5, mfc="white", mec=NARANJA, zorder=3)
    paso = "mid" if len(set(c["ucl"])) > 1 else None
    for linea, estilo, et in ((c["cl"], "-", "LC"), (c["ucl"], "--", "LSC"), (c["lcl"], "--", "LIC")):
        if paso: ax.step(xs, linea, where="mid", color=TINTA if et == "LC" else ROJO, lw=0.9, ls=estilo)
        else: ax.plot(xs, linea, color=TINTA if et == "LC" else ROJO, lw=0.9, ls=estilo)
        ax.text(xs[-1] + 0.3, linea[-1], f" {et}={num(linea[-1], 4)}", va="center", fontsize=7, color=TINTA if et == "LC" else ROJO,
                clip_on=False)
    for i, ts in viol.items():
        ax.plot(xs[i], pts[i], marker="o", ms=5.5, color=ROJO, zorder=4)
        ax.text(xs[i], pts[i], " " + ",".join(map(str, ts)), color=ROJO, fontsize=7, va="bottom")
    if k: ax.axvline(k + 0.5, color=SUAVE, lw=0.8, ls=":")
    paso_t = max(1, len(xs) // 15)
    ax.set_xticks(xs[::paso_t]); ax.set_xticklabels(etiquetas[::paso_t], fontsize=7)
    ax.set_title(titulo or c["nombre"]); ax.set_xlim(0.5, len(xs) + 0.5)


@registrar
class Spc(ModuloDialogo):
    ID, TITULO = "SPC", "Cartas de control"
    CAMPOS = [{"campo": "tipo", "etiqueta": "Tipo de carta (19_GB, SPC-TIPOS-CARTA)", "tipo": "opcion", "opciones": TIPOS, "defecto": "imr"},
              {"campo": "cuenta", "etiqueta": "Qué cuentas (solo cartas de atributo)", "tipo": "opcion", "opciones": CUENTA, "defecto": ""},
              {"campo": "y", "etiqueta": "Datos: mediciones, defectuosos o defectos", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "tam", "etiqueta": "Tamaño de subgrupo constante (o tamaño de muestra en p, np y u)", "tipo": "numero", "defecto": "1"},
              {"campo": "sub", "etiqueta": "Identificador de subgrupo (opcional, en lugar del tamaño)", "tipo": "col", "opcional": True},
              {"campo": "ncol", "etiqueta": "Tamaño de muestra por subgrupo (opcional; p y u)", "tipo": "col", "filtro": "num", "opcional": True},
              {"campo": "k", "etiqueta": "Calcular los límites solo con los primeros k subgrupos (opcional)", "tipo": "numero"},
              {"campo": "pruebas", "etiqueta": "Pruebas de causas especiales (19_GB, SPC-PATRONES)", "tipo": "multi", "opciones": OP_PRUEBAS,
               "defecto": [o[0] for o in OP_PRUEBAS]}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        tipo = p.get("tipo") or "imr"
        j = p.get("y"); columna(hoja, j, "los datos", "num")
        sub = p.get("sub"); columna(hoja, sub, "el subgrupo", obligatoria=False)
        ncol = p.get("ncol"); columna(hoja, ncol, "el tamaño de muestra", "num", obligatoria=False)
        tam = cls.numero(p, "tam", "El tamaño", minimo=0) or 1
        k = cls.numero(p, "k", "k", minimo=0)
        k = int(k) if k else None
        activas = tuple(int(x) for x in (p.get("pruebas") or []))
        nom = hoja.columnas[j].nombre or nombre_col(hoja, j)
        avisos = []
        cuenta = p.get("cuenta")
        if tipo in CARTAS_CUENTA:
            esperada = CARTAS_CUENTA[tipo]
            if cuenta is None:                     # receta o resultado guardado antes de G1: se deduce de la carta y se avisa
                cuenta = esperada
                avisos.append(f"Resultado anterior a la declaración de lo que se cuenta: se tomó «{dict(CUENTA)[esperada].split(':')[0]}» "
                              f"por la carta {tipo}. Confírmalo al repetir el análisis.")
            elif cuenta == "":
                raise ErrorEntrada("Declara qué cuentas: unidades defectuosas (cartas np o p) o defectos (cartas c o u).")
            elif cuenta != esperada:
                const = tipo in ("np", "c")
                otra = CARTA_SUGERIDA[(cuenta, const)]
                raise ErrorEntrada(f"Declaraste {'unidades defectuosas' if cuenta == 'defectuosas' else 'defectos'}, pero la carta {tipo} cuenta "
                                   f"{'unidades defectuosas' if esperada == 'defectuosas' else 'defectos'}. Con tamaño de muestra "
                                   f"{'constante' if const else 'variable'} usa la carta {otra} (19_GB SPC-TIPOS-CARTA).")
        elif cuenta:
            avisos.append("La declaración de lo que se cuenta no aplica a cartas de variable y se ignoró.")
        try:
            if tipo in ("imr", "xr", "xs"):
                if tipo == "imr" and sub is not None: raise ErrorEntrada("La carta I-MR es para datos individuales; quita el identificador de subgrupo.")
                g, etiquetas, fuera = subgrupos(hoja, j, 1 if tipo == "imr" else int(tam), sub)
                if tipo == "imr": cartas, info = S.carta_imr([v[0] for v in g], k)
                elif tipo == "xr": cartas, info = S.carta_xr(g, k)
                else: cartas, info = S.carta_xs(g, k)
            else:
                cols = [j] + ([ncol] if ncol is not None else [])
                filas, fuera = filas_validas(hoja, cols)
                x = [valor(hoja, j, i) for i in filas]
                ns = [valor(hoja, ncol, i) for i in filas] if ncol is not None else [tam] * len(x)
                etiquetas = [str(q + 1) for q in range(len(x))]
                if tipo in ("p", "np", "u") and ncol is None and tam <= 1 and tipo != "u":
                    raise ErrorEntrada("Indica el tamaño de muestra (constante o en una columna).")
                if tipo == "p": cartas, info = S.carta_p(x, ns, k)
                elif tipo == "np":
                    if ncol is not None and len(set(ns)) > 1: raise ErrorEntrada("La carta np requiere tamaño de muestra constante; usa la carta p.")
                    cartas, info = S.carta_np(x, ns[0], k)
                elif tipo == "c": cartas, info = S.carta_c(x, k)
                else: cartas, info = S.carta_u(x, ns, k)
        except ValueError as e:
            raise ErrorEntrada(str(e))
        if k and k >= len(cartas[0]["puntos"]): raise ErrorEntrada("k debe ser menor que el número de subgrupos.")
        violaciones = [S.pruebas(c, activas) if c["pruebas"] else {} for c in cartas]
        if tipo in ("imr", "xr", "xs"):
            v1 = {i: [1] for i, (v, u, l) in enumerate(zip(cartas[1]["puntos"], cartas[1]["ucl"], cartas[1]["lcl"]))
                  if v is not None and (v > u + 1e-12 or v < l - 1e-12)} if 1 in activas else {}
            violaciones[1] = v1
        fig, axs = figura(9.4, 3.2 * len(cartas), nrows=len(cartas))
        axs = axs if len(cartas) > 1 else [axs]
        nombre_t = dict(TIPOS)[tipo].split(" (")[0]
        for q, (ax, c) in enumerate(zip(axs, cartas)):
            dibujar_carta(ax, c, etiquetas, violaciones[q], k, f"{c['nombre']} de {nom}")
        svg, png = a_svg_png(fig)
        lim = [[c["nombre"], num(c["cl"][0], 5), num(c["ucl"][0], 5) if len(set(c["ucl"])) == 1 else "variable",
                num(c["lcl"][0], 5) if len(set(c["lcl"])) == 1 else "variable"] for c in cartas]
        filas_v = [[c["nombre"], etiquetas[i] if i < len(etiquetas) else str(i + 1), num(c["puntos"][i], 5), ", ".join(map(str, ts)),
                    "; ".join(S.PRUEBAS[t] for t in ts)] for c, vv in zip(cartas, violaciones) for i, ts in sorted(vv.items())]
        n_viol = sum(len(v) for v in violaciones)
        if n_viol:
            concl = (f"Se detectaron {n_viol} puntos con señal de causa especial. El proceso no muestra control estadístico con estas "
                     "pruebas: investiga la causa de cada señal antes de usar los límites para controlar o de calcular capacidad.")
        else:
            concl = ("Ningún punto activa las pruebas elegidas. Con estos datos no hay evidencia de causas especiales: el proceso se "
                     "comporta como estable (solo causas comunes, 19_GB SPC-ELEMENTOS). Esto no garantiza estabilidad futura.")
        if k: avisos.append(f"Límites calculados con los primeros {k} subgrupos y aplicados a todos (límites históricos o de fase).")
        if fuera: avisos.append(f"{fuera} filas con valores faltantes o inválidos quedaron fuera.")
        m = len(cartas[0]["puntos"])
        if tipo in ("xr", "xs") and m < 20: avisos.append(f"Hay {m} subgrupos; el curso recomienda 20 de n=5 o 25 de n=4 (SPC-PROCEDIMIENTO).")
        if tipo == "imr" and m < 20: avisos.append(f"Hay {m} datos; con menos de 20 los límites son poco estables.")
        frac = sum(1 for c, vv in zip(cartas, violaciones) for i in vv if 1 in vv[i]) / m
        supuestos = [("Subgrupos racionales y homogéneos", "Lo define el muestreo (SPC-PROCEDIMIENTO)", "Revísalo con el plan de muestreo"),
                     ("Independencia entre puntos", "Gráfica contra el orden", "Rachas o tendencias largas sugieren autocorrelación")]
        if tipo in ("imr",):
            ad = E.anderson_darling([v for v in cartas[0]["puntos"]]) if m >= 8 else None
            supuestos.insert(0, ("Datos individuales aproximadamente normales", "Anderson-Darling",
                                 (f"{p_igual(ad['p'], .005)}: " + ("no se rechaza la normalidad" if ad["p"] > 0.05 else
                                  "se rechaza la normalidad; las pruebas 2 a 7 pueden dar falsas alarmas")) if ad else "pocos datos"))
        info_t = [[k_, num(v, 5)] for k_, v in info.items()]
        return resultado(cls.ID, f"Carta {nombre_t} de {nom}", p, [
            b_grafica(svg, {"g": "carta", "titulo": f"Carta {nombre_t} de {nom}", "etiq": list(etiquetas), "cartas": [{"nombre": c["nombre"], "puntos": [_f(v) for v in c["puntos"]],
                "cl": [_f(v) for v in c["cl"]], "ucl": [_f(v) for v in c["ucl"]], "lcl": [_f(v) for v in c["lcl"]], "senales": sorted(int(i) for i in violaciones[q])} for q, c in enumerate(cartas)]}),
            b_texto(concl, "conclusion"),
            b_tabla("Límites de control (voz del proceso; no son límites de especificación)", ["Carta", "LC", "LSC", "LIC"], lim),
            b_tabla("Puntos con señal de causa especial", ["Carta", "Subgrupo", "Valor", "Pruebas", "Descripción"], filas_v,
                    ["i", "i", "d", "i", "i"]) if filas_v else b_texto("Sin señales en las pruebas elegidas.", "nota"),
            b_tabla("Parámetros estimados", ["Parámetro", "Valor"], info_t),
            *([b_texto(f"Se cuentan {'unidades defectuosas (modelo binomial)' if cuenta == 'defectuosas' else 'defectos (modelo Poisson)'}; "
                       f"tamaño de muestra {'constante' if tipo in ('np', 'c') else 'variable'}: carta {tipo} (19_GB SPC-TIPOS-CARTA). "
                       "Verificación: fórmulas de límites verificadas con datos sintéticos construidos a partir de los resúmenes de 19_GB; sin datos crudos del curso.")]
              if tipo in CARTAS_CUENTA else []),
            b_texto("Fórmulas y constantes: 19_GB_CONTROLAR, SPC-CONSTANTES y SPC-CARTAS-*; pruebas: SPC-PATRONES (zonas A, B y C). "
                    "Para recalcular límites tras un cambio, deben cumplirse las 4 condiciones de SPC-RECALCULO. Constantes de X̄-S y d2: "
                    "no respaldadas por la base.")],
            avisos, supuestos=supuestos, datos={"columnas": [c for c in (j, sub, ncol) if c is not None]}, png=png)


@registrar
class Capacidad(ModuloDialogo):
    ID, TITULO = "CAPACIDAD", "Capacidad de proceso (normal)"
    CAMPOS = [{"campo": "y", "etiqueta": "Datos", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "tam", "etiqueta": "Tamaño de subgrupo (1 = individuales)", "tipo": "numero", "defecto": "1"},
              {"campo": "sub", "etiqueta": "Identificador de subgrupo (opcional)", "tipo": "col", "opcional": True},
              {"campo": "lie", "etiqueta": "Límite inferior de especificación (LIE)", "tipo": "numero"},
              {"campo": "lse", "etiqueta": "Límite superior de especificación (LSE)", "tipo": "numero"},
              {"campo": "objetivo", "etiqueta": "Objetivo (opcional)", "tipo": "numero"},
              {"campo": "metodo", "etiqueta": "Sigma interna (subgrupos de 2 o más)", "tipo": "opcion", "defecto": "combinada",
               "opciones": [["combinada", "Desviación combinada insesgada (por omisión)"], ["rbarra", "R̄ / d2 (como la carta X̄-R del curso)"]]},
              {"campo": "resumen", "etiqueta": "Incluir resumen gráfico (carta, probabilidad e histograma)", "tipo": "bool", "defecto": True}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        j = p.get("y"); columna(hoja, j, "los datos", "num")
        sub = p.get("sub"); columna(hoja, sub, "el subgrupo", obligatoria=False)
        tam = int(cls.numero(p, "tam", "El tamaño", minimo=0) or 1)
        lie, lse, obj = cls.numero(p, "lie", "El LIE"), cls.numero(p, "lse", "El LSE"), cls.numero(p, "objetivo", "El objetivo")
        g, etiquetas, fuera = subgrupos(hoja, j, tam, sub)
        x = [v for s in g for v in s]
        if len(x) < 10: raise ErrorEntrada("La capacidad necesita al menos 10 datos; el curso usa 20 subgrupos de 5 (CAP-LARGO-CORTO-PLAZO).")
        nom = hoja.columnas[j].nombre or nombre_col(hoja, j)
        try:
            if all(len(s) == 1 for s in g):
                cartas, info = S.carta_imr(x); s_in = info["mr_barra"] / S.D2[2]; metodo = "R̄s / d2 (rango móvil de 2)"
            else:
                n = S._tam_constante(g)
                if (p.get("metodo") or "combinada") == "rbarra":
                    if not 2 <= n <= 25: raise ValueError("R̄/d2 requiere subgrupos de 2 a 25.")
                    rb = sum(max(s) - min(s) for s in g) / len(g); s_in = rb / S.D2[n]; metodo = f"R̄ / d2 (n = {n})"
                else:
                    s_in = C.sigma_combinada(g); metodo = "desviación combinada con c4"
                cartas, info = S.carta_xr(g) if n <= 10 else S.carta_xs(g)
            d = E.descriptivos(x)
            r = C.indices(d["media"], s_in, d["desv"], lie, lse)
        except ValueError as e:
            raise ErrorEntrada(str(e))
        obs = C.ppm_observado(x, lie, lse)
        ad = E.anderson_darling(x)
        viol = S.pruebas(cartas[0])
        fig, ax = figura(7.4, 3.8)
        bordes, unidad, w = clases_histograma(x)
        ax.hist(x, bins=bordes, color=CLARO, edgecolor=NARANJA)
        lo = min([bordes[0]] + [v for v in (lie, lse) if v is not None]); hi = max([bordes[-1]] + [v for v in (lie, lse) if v is not None])
        xs = [lo + (hi - lo) * t / 200 for t in range(201)]
        ax.plot(xs, [len(x) * w * st.norm.pdf(v, d["media"], s_in) for v in xs], color=NARANJA, lw=1.4, label="Dentro de subgrupos")
        ax.plot(xs, [len(x) * w * st.norm.pdf(v, d["media"], d["desv"]) for v in xs], color=TINTA, lw=1.2, ls="--", label="Global")
        for lim, et, col in ((lie, "LIE", ROJO), (lse, "LSE", ROJO), (obj, "Objetivo", SUAVE)):
            if lim is not None:
                ax.axvline(lim, color=col, lw=1.4, ls="-." if et == "Objetivo" else "-")
                ax.text(lim, ax.get_ylim()[1] * 0.97, f" {et}", color=col, fontsize=8, va="top")
        ax.legend(fontsize=7, frameon=False); ax.set_title(f"Capacidad de {nom}"); ax.set_ylabel("Frecuencia")
        svg, png = a_svg_png(fig)
        bloques = [b_grafica(svg, {"g": "capacidad", "titulo": f"Capacidad de {nom}", "x": [_f(v) for v in x], "media": _f(d["media"]), "s_dentro": _f(s_in), "s_global": _f(d["desv"]),
                                   "lie": _f(lie), "lse": _f(lse), "obj": _f(obj), "bordes": [_f(b) for b in bordes],
                                   "indices": {k2: _f(v) for k2, v in r.items() if isinstance(v, (int, float))}})]
        f = lambda v: num(v, 3) if v is not None else "—"
        cpk_txt = f"Cpk = {f(r['Cpk'])} ({C.clasificar(r['Cpk'])}) y Ppk = {f(r['Ppk'])} ({C.clasificar(r['Ppk'])})"
        concl = (f"{cpk_txt}, según 16_GB CAP-INTERPRETACION (< 1 incapaz; 1 a 1.33 apenas capaz; > 1.33 capaz). "
                 + (f"Cp ({f(r['Cp'])}) mayor que Cpk: el proceso no está centrado entre las especificaciones. " if r["Cp"] and r["Cp"] - r["Cpk"] > 0.05 else "")
                 + f"Nivel sigma de corto plazo = Cpk x 3 = {num(r['sigma_cp'], 2)}; de largo plazo = Ppk x 3 = {num(r['sigma_lp'], 2)} (CAP-NIVEL-SIGMA).")
        bloques.append(b_texto(concl, "conclusion"))
        bloques.append(b_tabla("Índices de capacidad", ["Índice", "Corto plazo (dentro)", "Largo plazo (global)"], [
            ["Cp / Pp", f(r["Cp"]), f(r["Pp"])], ["CPU / PPU", f(r["Cpu"]), f(r["Ppu"])], ["CPL / PPL", f(r["Cpl"]), f(r["Ppl"])],
            ["Cpk / Ppk", f(r["Cpk"]), f(r["Ppk"])], ["Desviación estándar", num(s_in, 5), num(d["desv"], 5)]]
            + ([["Cpm (con objetivo)", "", f(C.cpm(x, lie, lse, obj))]] if C.cpm(x, lie, lse, obj) is not None else [])))
        bloques.append(b_tabla("Partes por millón fuera de especificación", ["Concepto", "Observado", "Esperado dentro", "Esperado global"], [
            [n_, num(obs[k_], 1), num(r["ppm_C"][k_], 1), num(r["ppm_P"][k_], 1)] for n_, k_ in
            (("Debajo del LIE", "inf"), ("Arriba del LSE", "sup"), ("Total", "total"))]))
        bloques.append(b_tabla("Datos del proceso", ["Concepto", "Valor"], [
            ["N", d["n"]], ["Media", num(d["media"], 5)], ["LIE", f(lie)], ["LSE", f(lse)], ["Objetivo", f(obj)],
            ["Sigma interna", f"{num(s_in, 5)} ({metodo})"], ["Sigma global", num(d["desv"], 5)]]))
        if p.get("resumen", True):
            fig, axs = figura(9.6, 6.4, nrows=2, ncols=2)
            et = etiquetas if len(cartas[0]["puntos"]) == len(etiquetas) else [str(i + 1) for i in range(len(cartas[0]["puntos"]))]
            dibujar_carta(axs[0][0], cartas[0], et, viol, titulo=cartas[0]["nombre"])
            dibujar_carta(axs[1][0], cartas[1], et, {}, titulo=cartas[1]["nombre"])
            _prob_normal(axs[0][1], x, "Probabilidad normal")
            axs[0][1].text(0.02, 0.97, f"AD = {ad['a2']:.3f}\n{p_igual(ad['p'], .005)}", transform=axs[0][1].transAxes, va="top", fontsize=7)
            ult = x[-min(25, len(x)):]
            axs[1][1].plot(range(1, len(ult) + 1), ult, color=NARANJA, marker="o", ms=3, lw=0.8)
            for lim in (lie, lse):
                if lim is not None: axs[1][1].axhline(lim, color=ROJO, lw=1)
            axs[1][1].set_title(f"Últimas {len(ult)} observaciones")
            svg2, _ = a_svg_png(fig)
            bloques.insert(2, b_grafica(svg2))
        bloques.append(b_texto("Fórmulas: 16_GB CAP-CP, CAP-CPK, CAP-LARGO-CORTO-PLAZO y CAP-NIVEL-SIGMA. No respaldados por la base: "
                               "el método de la sigma interna (combinada insesgada, como describe el libro de Minitab, o R̄/d2), Cpm, el cálculo de PPM "
                               "con la normal y las curvas de la gráfica."))
        avisos = [f"{fuera} filas con valores faltantes o inválidos quedaron fuera."] if fuera else []
        supuestos = [
            ("Proceso estable (en control)", "Pruebas de 19_GB SPC-PATRONES sobre la carta",
             "sin señales de causa especial" if not viol else f"{len(viol)} puntos con señal: la capacidad calculada no es confiable hasta resolverlas"),
            ("Datos normales", "Anderson-Darling", f"{p_igual(ad['p'], .005)}: " + ("no se rechaza la normalidad" if ad["p"] > 0.05 else
             "se rechaza la normalidad; los índices y PPM normales pueden engañar (ver 25_BB, transformación)")),
            ("Especificaciones del cliente", "LIE y LSE capturados", "Son voz del cliente; no se mezclan con los límites de control")]
        return resultado(cls.ID, f"Capacidad de {nom}", p, bloques, avisos, supuestos=supuestos,
                         datos={"columnas": [c for c in (j, sub) if c is not None]}, png=png)
