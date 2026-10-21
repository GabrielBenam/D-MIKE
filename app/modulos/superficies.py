"""Superficies de respuesta para optimizar procesos (28_BB_SUPERFICIES_RESPUESTA):
DISENO-RSM crea el diseño en la hoja, RSM lo analiza (modelo en unidades codificadas, ANOVA, falta de ajuste,
contornos, superficie, punto estacionario y ascenso) y OPTIMIZADOR busca la mejor combinación de factores para una
o varias respuestas con la función de deseabilidad. Motor: doe.py."""
import math
import numpy as np
from matplotlib import colors as mcolors
from . import registrar, doe as D, estadistica as E
from .analisis import _prob_normal
from .base import _f
from .base import (ErrorEntrada, columna, filas_validas, valor, figura, a_svg_png, num, p_igual, p_texto, frase_p,
                   resultado, b_grafica, b_tabla, b_texto, NARANJA, TINTA, SUAVE, CLARO)
from .dialogo import ModuloDialogo
from ..nucleo import modo as MD, disenos as DIS

MAPA = mcolors.LinearSegmentedColormap.from_list("dmike", ["#fbf6ef", "#f6c9a8", "#ec8a4f", "#dd5813", "#8a3307"])
TIPOS_DISENO = [["ccd", "Central compuesto (DCC)"], ["bb", "Box-Behnken"], ["fact", "Factorial completo 2^k con puntos centrales"],
                ["frac", "Factorial fraccionado 2^(k-p)"]]


def _lista(t, etiqueta, n=None, numeros=True):
    partes = [x.strip() for x in (t or "").replace(";", ",").split(",") if x.strip()]
    if numeros:
        try: partes = [float(x) for x in partes]
        except ValueError: raise ErrorEntrada(f"{etiqueta}: escribe números separados por comas.")
    if n is not None and len(partes) != n: raise ErrorEntrada(f"{etiqueta}: se esperaban {n} valores y hay {len(partes)}.")
    return partes


# ---------------- crear diseño ----------------
@registrar
class DisenoRsm(ModuloDialogo):
    ID, TITULO, HOJA_VACIA_OK, CAMBIA_HOJA = "DISENO-RSM", "Crear diseño de experimentos", True, True
    CAMPOS = [{"campo": "tipo", "etiqueta": "Tipo de diseño", "tipo": "opcion", "opciones": TIPOS_DISENO, "defecto": "ccd"},
              {"campo": "nombres", "etiqueta": "Factores (nombres separados por comas)", "tipo": "texto", "defecto": "A, B"},
              {"campo": "bajos", "etiqueta": "Nivel bajo de cada factor (unidades reales, separados por comas)", "tipo": "texto", "defecto": "-1, -1"},
              {"campo": "altos", "etiqueta": "Nivel alto de cada factor", "tipo": "texto", "defecto": "1, 1"},
              {"campo": "alfa", "etiqueta": "DCC: distancia de los puntos axiales", "tipo": "opcion", "defecto": "rotable",
               "opciones": [["rotable", "Rotable (2^(k/4))"], ["caras", "Centrado en las caras (α = 1)"]]},
              {"campo": "limites", "etiqueta": "Límites seguros: mínimo y máximo de cada factor, un par por factor en el mismo orden (ej. 90, 125; 5, 40)", "tipo": "texto", "defecto": ""},
              {"campo": "limites_como_axiales", "etiqueta": "DCC con α = 1: usar los límites seguros como niveles bajo y alto (puntos axiales en las caras). No nombrado por el curso", "tipo": "bool", "defecto": False},
              {"campo": "bloques", "etiqueta": "DCC: bloques", "tipo": "opcion", "defecto": "1", "opciones": [["1", "Sin bloques"], ["2", "2 bloques (cubo y estrella)"]]},
              {"campo": "fraccion", "etiqueta": "Fraccionado: p (1 = mitad, 2 = cuarta parte…)", "tipo": "opcion", "defecto": "1",
               "opciones": [["1", "1 (mitad)"], ["2", "2 (cuarta parte)"], ["3", "3 (octava parte)"], ["4", "4"]]},
              {"campo": "signo", "etiqueta": "Fraccionado: fracción", "tipo": "opcion", "defecto": "1",
               "opciones": [["1", "Principal (generador positivo)"], ["-1", "Alterna (generador negativo, ej. D = -ABC)"]]},
              {"campo": "centros", "etiqueta": "Puntos centrales (vacío = por omisión)", "tipo": "numero"},
              {"campo": "replicas", "etiqueta": "Réplicas", "tipo": "numero", "defecto": "1"},
              {"campo": "respuesta", "etiqueta": "Nombre de la respuesta", "tipo": "texto", "defecto": "Respuesta"},
              {"campo": "aleatorio", "etiqueta": "Aleatorizar el orden de las corridas", "tipo": "bool", "defecto": True},
              {"campo": "semilla", "etiqueta": "Semilla para aleatorizar (opcional, para repetir el mismo orden)", "tipo": "numero"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        nombres = _lista(p.get("nombres"), "Factores", numeros=False)
        k = len(nombres)
        if k < 2: raise ErrorEntrada("Se necesitan al menos 2 factores.")
        if len({n.lower() for n in nombres}) != k: raise ErrorEntrada("Los nombres de los factores deben ser distintos.")
        bajos, altos = _lista(p.get("bajos"), "Nivel bajo", k), _lista(p.get("altos"), "Nivel alto", k)
        if any(b >= a for b, a in zip(bajos, altos)): raise ErrorEntrada("Cada nivel bajo debe ser menor que su nivel alto.")
        tipo = p.get("tipo") or "ccd"
        # ---- región autorizada (Entrega 3, Decisión 5) ----
        real = proyecto is not None and not MD.es_demo(proyecto)
        texto_lim = (p.get("limites") or "").strip(); lim = None; alfa_dcc = p.get("alfa") or "rotable"
        if texto_lim:
            v = _lista(texto_lim, "Límites seguros", 2 * k)
            lim = [(v[2 * q], v[2 * q + 1]) for q in range(k)]
            if any(a >= b for a, b in lim): raise ErrorEntrada("Cada límite seguro mínimo debe ser menor que su máximo.")
        elif real and not p.get("limites_opcionales"):
            raise ErrorEntrada("En un proyecto real declara los límites seguros de cada factor (mínimo y máximo): son la región autorizada para experimentar y no son los niveles "
                               "bajo y alto del diseño. Escribe un par por factor, por ejemplo «90, 125; 5, 40».")
        usar_limites = bool(p.get("limites_como_axiales"))
        if usar_limites:
            if tipo != "ccd": raise ErrorEntrada("La alternativa de usar los límites seguros como puntos axiales solo aplica al diseño central compuesto.")
            if lim is None: raise ErrorEntrada("Para usar los límites seguros como puntos axiales hay que declararlos.")
            bajos, altos, alfa_dcc = [a for a, _ in lim], [b for _, b in lim], "caras"          # α = 1: los axiales caen en las caras del cubo, que es la región declarada
        cen = cls.numero(p, "centros", "Los puntos centrales", minimo=-1)
        cen = int(cen) if cen is not None else None
        rep = int(cls.numero(p, "replicas", "Las réplicas", minimo=0) or 1)
        try:
            if tipo == "ccd":
                bl = int(p.get("bloques") or 1)
                filas, alfa = D.diseno_ccd(k, alfa_dcc, bl, centros_cubo=cen, replicas=rep,
                                           centros_estrella=(cen if bl == 2 and cen is not None else None))
            elif tipo == "bb": filas, alfa = D.diseno_box_behnken(k, cen, rep)
            elif tipo == "frac":
                pf = int(p.get("fraccion") or 1)
                if (k, pf) not in D.GENERADORES: raise ValueError(f"No hay fraccionado 2^({k}-{pf}) en la tabla de generadores (k de 3 a 7, p de 1 a 4).")
                filas, alfa = D.diseno_fraccionado(k, pf, int(p.get("signo") or 1), cen or 0, rep)
            else: filas, alfa = D.diseno_factorial(k, cen or 0, rep)
        except ValueError as e:
            raise ErrorEntrada(str(e))
        if lim is not None:                  # todo punto fuera de la región se rechaza (axiales incluidos) antes de escribir nada en la hoja
            fuera = D.puntos_fuera(filas, bajos, altos, lim)
            if fuera:
                det = "; ".join(f"{D.NOMBRE_PUNTO.get(t, 'punto')} (corrida estándar {i}), {nombres[q]} = {num(v, 6)} fuera de [{num(lim[q][0])}, {num(lim[q][1])}]" for i, t, q, v in fuera[:6])
                extra = f" (y {len(fuera) - 6} más)" if len(fuera) > 6 else ""
                alt = (" Alternativa, solo con α = 1: marca «usar los límites seguros como niveles bajo y alto». Es un uso no nombrado por el curso (el ejemplo de 28_BB, línea 57, es "
                       "consistente con cubo y axiales en el mismo rango). Rotable, otros valores de α y cualquier otra alternativa no están respaldados por la base."
                       if tipo == "ccd" else " Ajusta los niveles bajo y alto para que todo punto quede dentro de la región.")
                raise ErrorEntrada(f"El diseño sale de la región segura en {len(fuera)} puntos: {det}{extra}. No se escribió nada en la hoja." + alt)
        n = len(filas)
        semilla = cls.numero(p, "semilla", "La semilla")
        orden = D.aleatorizar(n, int(semilla) if semilla is not None else None) if p.get("aleatorio", True) else list(range(n))
        resp = (p.get("respuesta") or "Respuesta").strip()
        cab = ["OrdenEst", "OrdenCorrida", "TipoPunto", "Bloque"] + nombres + [resp]
        lineas = ["\t".join(cab)]
        for corrida, i in enumerate(orden, 1):
            f = filas[i]; o = D.a_original(f["coded"], bajos, altos)
            lineas.append("\t".join([str(i + 1), str(corrida), str(f["tipo"]), str(f["bloque"])] + [f"{v:.6g}" for v in o] + [""]))
        col0 = len(hoja.columnas)
        hoja.pegar(-1, col0, "\n".join(lineas))
        hoja.cambiar_tipo(col0 + len(cab) - 1, "num")
        reales = [hoja.columnas[col0 + j].nombre for j in range(len(cab))]
        info = {"tipo": tipo, "factores": [{"nombre": reales[4 + j], "bajo": bajos[j], "alto": altos[j]} for j in range(k)],
                "alfa": alfa, "respuesta": reales[-1], "bloque": reales[3], "tipo_punto": reales[2], "corridas": n,
                "orden_est": reales[0], "orden_corrida": reales[1]}
        if lim is not None:
            info["limites_seguros"] = {info["factores"][q]["nombre"]: {"min": lim[q][0], "max": lim[q][1]} for q in range(k)}
            info["region"] = "declarada"; info["alternativa_axial_en_limites"] = usar_limites
        else: info["region"] = "no_declarada"
        columnas_nuevas = list(range(col0, col0 + len(cab)))
        runid = False
        if proyecto is not None:
            # E3-2: identidad del diseño (design_id, version_diseno, huella). En un proyecto real se agrega la columna RunId de solo lectura;
            # en demostración no se toca la hoja (el run_id se deriva igual de OrdenEst).
            DIS.asignar_nuevo(proyecto, hoja, info, info["respuesta"])
            proyecto.formatos.setdefault("_disenos", {})[info["respuesta"]] = info
            if not MD.es_demo(proyecto):
                columnas_nuevas.append(DIS.agregar_runid(hoja, info)); DIS.sincronizar_runid(proyecto, hoja); runid = True
        conteo = {"cubo o esquina": sum(f["tipo"] == 1 for f in filas), "axiales": sum(f["tipo"] == -1 for f in filas),
                  "aristas (Box-Behnken)": sum(f["tipo"] == 2 for f in filas), "centrales": sum(f["tipo"] == 0 for f in filas)}
        frac_info = []
        if tipo == "frac":
            pf = int(p.get("fraccion") or 1); sg = int(p.get("signo") or 1); pal = D.relacion_definidora(k, pf); R = D.resolucion(k, pf)
            gens = D.GENERADORES[(k, pf)]
            letras = {D.LETRAS[i]: nombres[i] for i in range(k)}
            frac_info = [["Generadores", ", ".join(f"{D.LETRAS[k - pf + i]} = {'-' if sg < 0 else ''}{g}" for i, g in enumerate(gens))],
                         ["Relación definidora", "I = " + " = ".join(pal)], ["Resolución", ["", "", "", "III", "IV", "V", "VI", "VII"][R]],
                         ["Letras", ", ".join(f"{a} = {b}" for a, b in letras.items())]]
            info["fraccion"] = {"p": pf, "signo": sg, "palabras": pal, "resolucion": R}
        region = ([["Región segura (límites por factor)", "; ".join(f"{f['nombre']}: {num(lim[q][0])} a {num(lim[q][1])}" for q, f in enumerate(info["factores"]))],
                   ["Puntos fuera de la región", "ninguno (cubo, centrales y axiales verificados)"]] if lim is not None
                  else [["Región segura (límites por factor)", "No declarada (opcional en demostración)"]])
        if usar_limites: region.append(["Alternativa de puntos axiales", "Los límites seguros son los niveles bajo y alto y los axiales caen en las caras (α = 1). Es un uso no nombrado por el curso (el ejemplo de 28_BB, línea 57, es consistente con cubo y axiales en el mismo rango)."])
        identidad = [["Identificador del diseño (design_id)", info.get("design_id", "—")], ["Versión del diseño", info.get("version_diseno", "—")],
                     ["Identificador de cada corrida", "RunId = design_id + OrdenEst" + (" (columna de solo lectura al final de la hoja)" if runid else " (derivado de OrdenEst; la hoja no se modifica en demostración)")]]
        resumen = [["Tipo", dict(TIPOS_DISENO)[tipo] + (f" 2^({k}-{int(p.get('fraccion') or 1)})" if tipo == "frac" else "")], ["Factores", k], ["Corridas", n],
                   ["α (distancia axial, codificada)", num(alfa, 4) if tipo == "ccd" else "—"],
                   ["Bloques", p.get("bloques") if tipo == "ccd" else "1"], ["Réplicas", rep]] + \
                  [[f"Puntos {k_}", v] for k_, v in conteo.items() if v]
        fact = [[f["nombre"], num(f["bajo"]), num(f["alto"]), num(D.a_original([-alfa], [f["bajo"]], [f["alto"]])[0]) if tipo == "ccd" else "—",
                 num(D.a_original([alfa], [f["bajo"]], [f["alto"]])[0]) if tipo == "ccd" else "—"] for f in info["factores"]]
        avisos = []
        if usar_limites:
            avisos.append("Alternativa elegida: los límites seguros son los niveles bajo y alto del diseño y los puntos axiales caen en las caras (α = 1). Es un uso "
                          "no nombrado por el curso (el ejemplo de 28_BB, línea 57, es consistente con cubo y axiales en el mismo rango); D-MIKE no le atribuye otras propiedades.")
        if tipo == "ccd" and alfa > 1:
            avisos.append("Los puntos axiales quedan fuera de los niveles bajo y alto: verifica que el proceso pueda operar en ellos; si no, "
                          "usa el diseño centrado en las caras.")
        return resultado(cls.ID, f"Diseño {dict(TIPOS_DISENO)[tipo].split(' (')[0].lower()} de {k} factores para {resp}", p, [
            b_texto(f"Se agregaron {len(columnas_nuevas)} columnas a la hoja, a partir de C{col0 + 1}. Corre los experimentos en el orden de "
                    f"«OrdenCorrida», captura la respuesta en «{info['respuesta']}» y luego usa Estadística > Superficie de respuesta > Analizar.",
                    "conclusion"),
            b_tabla("Resumen del diseño", ["Concepto", "Valor"], resumen + frac_info + region + identidad),
            b_tabla("Factores (unidades reales)", ["Factor", "Bajo (-1)", "Alto (+1)", "Axial -α", "Axial +α"], fact),
            b_texto("Procedimiento: 28_BB RSM-PROCEDIMIENTO (factorial con puntos centrales, ascenso, DCC). No respaldados por la base: "
                    "α rotable, Box-Behnken, cantidad de puntos centrales por omisión y reparto en bloques.")],
            avisos, datos={"columnas": columnas_nuevas, "diseno": info})


# ---------------- analizar ----------------
def _niveles(hoja, j, nombre, x, diseno):
    if diseno:
        for f in diseno["factores"]:
            if f["nombre"].lower() == nombre.lower(): return f["bajo"], f["alto"]
    dist = sorted(set(round(v, 9) for v in x))
    if len(dist) == 5: return dist[1], dist[3]                 # DCC: -α, -1, 0, 1, α
    return dist[0], dist[-1]


@registrar
class Rsm(ModuloDialogo):
    ID, TITULO = "RSM", "Analizar superficie de respuesta"
    CAMPOS = [{"campo": "y", "etiqueta": "Respuesta", "tipo": "col", "filtro": "num", "rol": ["respuesta"]},
              {"campo": "xs", "etiqueta": "Factores (2 o más)", "tipo": "cols", "filtro": "num"},
              {"campo": "bloque", "etiqueta": "Bloques (opcional)", "tipo": "col", "opcional": True},
              {"campo": "modelo", "etiqueta": "Términos del modelo", "tipo": "opcion", "defecto": "cuadratico",
               "opciones": [[k, v] for k, v in D.MODELOS.items()]},
              {"campo": "excluir", "etiqueta": "Quitar términos: con letras (A*B, A*A; A es el primer factor) o con nombres (Temp*Tiempo); uno a la vez, el menos significativo primero", "tipo": "texto"},
              {"campo": "niveles", "etiqueta": "Niveles bajo y alto por factor (opcional; ej. 2,3; 2,3)", "tipo": "texto"},
              {"campo": "ejes", "etiqueta": "Factores de los ejes del contorno (opcional; ej. A, B)", "tipo": "texto"},
              {"campo": "fijar", "etiqueta": "Los demás factores en", "tipo": "opcion", "defecto": "centro",
               "opciones": [["centro", "Su punto medio"], ["bajo", "Su nivel bajo"], ["alto", "Su nivel alto"]]},
              {"campo": "meta", "etiqueta": "Objetivo del proceso (para la dirección de ascenso)", "tipo": "opcion", "defecto": "max",
               "opciones": [["max", "Maximizar"], ["min", "Minimizar"]]},
              {"campo": "alfa", "etiqueta": "Nivel de significancia (alfa)", "tipo": "opcion", "defecto": "0.05",
               "opciones": [["0.10", "0.10"], ["0.05", "0.05"], ["0.01", "0.01"]]}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        yj = p.get("y"); columna(hoja, yj, "la respuesta", "num")
        xs = [j for j in (p.get("xs") or []) if j is not None]
        if len(xs) < 2: raise ErrorEntrada("Elige al menos 2 factores.")
        for j in xs: columna(hoja, j, "los factores", "num")
        if yj in xs: raise ErrorEntrada("La respuesta no puede ser también factor.")
        bj = p.get("bloque"); bc = columna(hoja, bj, "los bloques", obligatoria=False)
        alfa = float(p.get("alfa") or 0.05)
        filas, fuera = filas_validas(hoja, [yj] + xs + ([bj] if bc else []))
        y = [valor(hoja, yj, i) for i in filas]
        X = [[valor(hoja, j, i) for j in xs] for i in filas]
        nombres = [hoja.columnas[j].nombre or f"C{j + 1}" for j in xs]
        ny = hoja.columnas[yj].nombre or f"C{yj + 1}"
        if (motivo := DIS.verificar_para_analisis(proyecto, hoja, ny)): raise ErrorEntrada(motivo)          # E3-3: no se mezclan versiones del diseño
        disenos = (proyecto.formatos.get("_disenos", {}) if proyecto is not None else {})
        diseno = disenos.get(ny)
        if p.get("niveles"):
            pares = [x.strip() for x in p["niveles"].split(";") if x.strip()]
            if len(pares) != len(xs): raise ErrorEntrada("Niveles: escribe un par «bajo, alto» por factor, separados por punto y coma.")
            niveles = [tuple(_lista(t, "Niveles", 2)) for t in pares]
        else:
            niveles = [_niveles(hoja, j, nombres[q], [r[q] for r in X], diseno) for q, j in enumerate(xs)]
        if any(a <= b for b, a in niveles): raise ErrorEntrada("Cada factor necesita un nivel bajo menor que el alto (revisa que varíe).")
        bajos, altos = [b for b, _ in niveles], [a for _, a in niveles]
        Xc = [D.a_codificado(r, bajos, altos) for r in X]
        modelo = p.get("modelo") or "cuadratico"
        def _letras(t):           # «A*B» o «A*A» también sirven: cada letra es un factor en el orden elegido
            partes = [x.strip() for x in t.split("*")]
            if partes and all(len(x) == 1 and "A" <= x.upper() <= chr(64 + len(nombres)) for x in partes):
                return "*".join(nombres[ord(x.upper()) - 65] for x in partes)
            return t.strip()
        excl = [_letras(t) for t in (p.get("excluir") or "").split(",") if t.strip()]
        ts, retenidos, desconocidos = D.terminos(nombres, modelo, excl)
        es_centro = [all(abs(v) < 1e-9 for v in r) for r in Xc]
        curv = es_centro if (modelo in ("lineal", "lineal_interacciones") and any(es_centro) and not all(es_centro)) else None
        bloques = [str(valor(hoja, bj, i)) for i in filas] if bc else None
        try:
            sup = D.ajustar_superficie(Xc, y, nombres, ts, bloques, curv, alfa)
        except ValueError as e:
            raise ErrorEntrada(str(e) + " Revisa el diseño o quita términos.")
        m = sup["modelo"]; b0, b, B = D.coeficientes_modelo(sup)
        k = len(xs)
        # ---------- tablas ----------
        coef = [[c["termino"], num(c["coef"], 5), num(c["ee"], 4), num(c["t"], 3), p_texto(c["p"]),
                 num(c["vif"], 2) if c["vif"] is not None else "—"] for c in m["coef"]]
        resumen = [[num(m["s"], 6), num(m["press"], 4), f"{100 * m['r2']:.2f}%", f"{100 * m['r2_aj']:.2f}%",
                    f"{100 * m['r2_pred']:.2f}%" if m["r2_pred"] == m["r2_pred"] else "—"]]
        anova = []
        for a in sup["anova"]:
            sangria = "    " if a.get("sub") is True else "        " if a.get("sub") == 2 else ""
            anova.append([sangria + a["fuente"], a["gl"], num(a["ss"], 5), num(a["ms"], 5), num(a["f"], 3), p_texto(a["p"])])
        anova.append(["Error", m["gl_e"], num(m["sce"], 5), num(m["mce"], 5), "", ""])
        lof = sup["lof"]
        if lof:
            anova.append(["    Falta de ajuste", lof["gl"], num(lof["ss"], 5), num(lof["ms"], 5), num(lof["f"], 3), p_texto(lof["p"])])
            anova.append(["    Error puro", lof["pe"]["gl"], num(lof["pe"]["ss"], 5), num(lof["pe"]["ms"], 5), "", ""])
        anova.append(["Total", m["n"] - 1, num(m["sct"], 5), "", "", ""])
        # ecuación en unidades reales: z = D(x - c)
        cen = np.array([(b_ + a_) / 2 for b_, a_ in zip(bajos, altos)]); h = np.array([(a_ - b_) / 2 for b_, a_ in zip(bajos, altos)])
        Dm = np.diag(1 / h); Q = Dm @ B @ Dm; cvec = Dm @ b
        k0 = b0 - cvec @ cen + cen @ Q @ cen; lin = cvec - 2 * Q @ cen
        terminos_reales = [(f"{nombres[i]}", lin[i]) for i in range(k)] + [(f"{nombres[i]}*{nombres[i]}", Q[i, i]) for i in range(k)] + \
                          [(f"{nombres[i]}*{nombres[j]}", 2 * Q[i, j]) for i in range(k) for j in range(i + 1, k)]
        ec_real = f"{ny} = {num(k0, 6)}" + "".join(f" {'+' if v >= 0 else '-'} {num(abs(v), 6)} {t}" for t, v in terminos_reales if abs(v) > 1e-12)
        ec_cod = f"{ny} = {num(b0, 5)}" + "".join(f" {'+' if c['coef'] >= 0 else '-'} {num(abs(c['coef']), 5)} {c['termino']}"
                                                   for c in m["coef"][1:] if not c["termino"].startswith("Bloque") and not c["termino"].startswith("Curvatura"))
        bloques_out = [b_texto(f"Ecuación en unidades codificadas: {ec_cod}", "conclusion"),
                       b_texto(f"Ecuación en unidades reales: {ec_real}", "nota")]
        # ---------- gráficas: contorno y superficie ----------
        ejes = [e.strip().lower() for e in (p.get("ejes") or "").split(",") if e.strip()]
        if ejes:
            try: ia, ib = (nombres_l := [n.lower() for n in nombres]).index(ejes[0]), nombres_l.index(ejes[1])
            except (ValueError, IndexError): raise ErrorEntrada("Ejes: escribe dos nombres de factores del modelo, separados por coma.")
        else:
            peso = [abs(b[i]) + 2 * abs(B[i, i]) + sum(abs(B[i, j]) for j in range(k) if j != i) for i in range(k)]
            ia, ib = sorted(sorted(range(k), key=lambda i: -peso[i])[:2])
        fijo_c = {"centro": 0.0, "bajo": -1.0, "alto": 1.0}[p.get("fijar") or "centro"]
        lim = max(1.0, max(max(abs(v) for v in r) for r in Xc))
        g = np.linspace(-lim, lim, 61)
        Z = np.zeros((len(g), len(g)))
        for r_, vb in enumerate(g):
            for c_, va in enumerate(g):
                xv = np.full(k, fijo_c); xv[ia] = va; xv[ib] = vb
                Z[r_, c_] = D.predecir_codificado((b0, b, B), xv)
        ga = [D.a_original([v], [bajos[ia]], [altos[ia]])[0] for v in g]; gb = [D.a_original([v], [bajos[ib]], [altos[ib]])[0] for v in g]
        fig, ax = figura(5.6, 4.4)
        cs = ax.contourf(ga, gb, Z, levels=12, cmap=MAPA)
        cl = ax.contour(ga, gb, Z, levels=12, colors=TINTA, linewidths=0.4)
        ax.clabel(cl, fontsize=6, fmt=lambda v: num(v, 3))
        pts = [(r[ia], r[ib]) for r in X]
        ax.scatter([a for a, _ in pts], [b_ for _, b_ in pts], s=10, color=TINTA, zorder=3)
        fig.colorbar(cs, ax=ax, label=ny)
        ax.set_xlabel(nombres[ia]); ax.set_ylabel(nombres[ib]); ax.grid(False)
        otros = [nombres[i] for i in range(k) if i not in (ia, ib)]
        ax.set_title(f"Contorno de {ny}" + (f" ({', '.join(otros)} en su {'punto medio' if fijo_c == 0 else 'nivel ' + p.get('fijar')})" if otros else ""), fontsize=9)
        svg_c, png = a_svg_png(fig)
        fig = figura(5.6, 4.4)[0]; ax3 = fig.add_subplot(111, projection="3d")
        GA, GB = np.meshgrid(ga, gb)
        ax3.plot_surface(GA, GB, Z, cmap=MAPA, linewidth=0, antialiased=True, alpha=0.95)
        ax3.set_xlabel(nombres[ia], fontsize=8); ax3.set_ylabel(nombres[ib], fontsize=8); ax3.set_zlabel(ny, fontsize=8)
        ax3.tick_params(labelsize=6); ax3.set_title(f"Superficie de {ny}", fontsize=9)
        svg_s, _ = a_svg_png(fig)
        _sp = {"titulo": f"{ny}", "xl": nombres[ia], "yl": nombres[ib], "zl": ny, "x": [_f(v) for v in ga[::2]], "y": [_f(v) for v in gb[::2]], "z": [[_f(v) for v in fila[::2]] for fila in Z.tolist()[::2]],
               "px": [_f(a) for a, _ in pts], "py": [_f(b_) for _, b_ in pts], "pz": [_f(v) for v in y]}
        bloques_out += [b_grafica(svg_c, dict(_sp, g="contorno")), b_grafica(svg_s, dict(_sp, g="superficie"))]
        bloques_out += [b_tabla("Coeficientes (unidades codificadas)", ["Término", "Coeficiente", "EE", "t", "Valor p", "VIF"], coef),
                        b_tabla("Resumen del modelo", ["S", "PRESS", "R²", "R² ajustado", "R² de predicción"], resumen),
                        b_tabla("Análisis de varianza (SC ajustada)", ["Fuente", "GL", "SC", "CM", "F", "Valor p"], anova)]
        # ---------- punto estacionario o ascenso ----------
        interp = [frase_p(next(a for a in sup["anova"] if a["fuente"] == "Modelo")["p"], alfa, "ningún término explica la respuesta",
                          f"el modelo explica parte de la variación de {ny}")]
        hay_cuad = any(len(t) == 2 and t[0] == t[1] for t in ts)
        ps = D.punto_estacionario(b0, b, B) if hay_cuad else None
        if ps:
            dentro = all(abs(v) <= lim + 1e-9 for v in ps["x"])
            orig = D.a_original(ps["x"], bajos, altos)
            bloques_out.append(b_tabla("Punto estacionario (28_BB RSM-PUNTO-ESTACIONARIO)", ["Factor", "Codificado", "Unidades reales"],
                                       [[nombres[i], num(ps["x"][i], 4), num(orig[i], 5)] for i in range(k)] +
                                       [[f"{ny} predicha", "", num(ps["y"], 5)], ["Tipo", "", ps["tipo"]],
                                        ["Valores propios", "", ", ".join(num(v, 4) for v in ps["valores_propios"])]]))
            interp.append(f"El punto estacionario es un {ps['tipo']}" + (" y queda dentro de la región experimentada." if dentro else
                          ", pero queda fuera de la región experimentada: no lo uses sin confirmarlo; considera moverte hacia él con nuevos experimentos.")
                          + (" Para maximizar o minimizar en un punto silla, usa el optimizador dentro de la región." if ps["tipo"] == "punto silla" else ""))
        elif not hay_cuad:
            i, pasos = D.ascenso(b, 5, (p.get("meta") or "max") == "max")
            if pasos:
                filas_a = [[f"{s} Δ"] + [num(v, 5) for v in D.a_original(q, bajos, altos)] + [num(D.predecir_codificado((b0, b, B), q), 5)]
                           for s, q in enumerate(pasos)]
                bloques_out.append(b_tabla(f"Ruta de {'ascenso' if (p.get('meta') or 'max') == 'max' else 'descenso'} más pronunciado "
                                           f"(28_BB RSM-ASCENSO; paso base en {nombres[i]})", ["Paso"] + nombres + [f"{ny} del modelo"], filas_a))
                interp.append("El modelo es de primer orden: corre experimentos sobre la ruta hasta que la respuesta deje de mejorar y en esa "
                              "vecindad plantea un diseño central compuesto (RSM-VECINDAD y RSM-DCC). Las predicciones fuera de la región son "
                              "solo una guía.")
        if sup["con_curvatura"]:
            cv = next(a for a in sup["anova"] if a["fuente"] == "Curvatura")
            interp.append(("La curvatura es significativa (" + p_igual(cv["p"]) + "): un modelo de primer orden no basta; agrega puntos axiales "
                           "(DCC) para estimar los términos cuadráticos (RSM-PUNTOS-CENTRALES).") if cv["p"] < alfa else
                          ("La curvatura no es significativa (" + p_igual(cv["p"]) + "); el modelo de primer orden es razonable en esta región."))
        if lof:
            interp.append(("Hay falta de ajuste (" + p_igual(lof["p"]) + "): el modelo no describe bien la superficie; revisa términos o transformación "
                           "(27_BB REG-FALTA-AJUSTE).") if lof["p"] < alfa else ("No se detecta falta de ajuste (" + p_igual(lof["p"]) + ")."))
        sig = {c["termino"] for c in m["coef"][1:] if c["p"] < alfa}
        def protegido(nm):   # lineal con cuadrado o interacción significativos: se queda por jerarquía
            return "*" not in nm and any("*" in s_ and nm in s_.split("*") for s_ in sig)
        no_sig = [c["termino"] for c in m["coef"][1:] if c["p"] >= alfa and not c["termino"].startswith(("Bloque", "Curvatura"))
                  and not protegido(c["termino"])]
        if no_sig:
            interp.append("Términos no significativos: " + ", ".join(no_sig) + ". Quítalos uno por uno, empezando por el de mayor valor p y por las "
                          "interacciones; un término lineal se conserva si su cuadrado o una interacción con él es significativa (RSM-PRUEBAS-2DO-ORDEN).")
        # ---------- residuos ----------
        fig, axs = figura(9.6, 5.6, nrows=2, ncols=2)
        res, aj = m["residuos"], m["ajustados"]
        _prob_normal(axs[0][0], res, "Probabilidad normal de residuos")
        axs[0][1].scatter(aj, res, s=12, color=NARANJA); axs[0][1].axhline(0, color=TINTA, lw=1); axs[0][1].set_title("Residuos contra ajustados")
        axs[1][0].hist(res, bins=min(10, max(5, int(math.sqrt(len(res))))), color=CLARO, edgecolor=NARANJA); axs[1][0].set_title("Histograma de residuos")
        axs[1][1].plot(range(1, len(res) + 1), res, color=NARANJA, marker="o", ms=3, lw=0.8); axs[1][1].axhline(0, color=TINTA, lw=1)
        axs[1][1].set_title("Residuos contra orden")
        bloques_out += [b_grafica(a_svg_png(fig)[0])]
        bloques_out.append(b_texto("Método: 28_BB_SUPERFICIES_RESPUESTA y 27_BB_REGRESION (pruebas del modelo, falta de ajuste, sumas extra). "
                                   "Unidades codificadas: -1 en el nivel bajo y +1 en el alto. No respaldados por la base: análisis canónico con "
                                   "valores propios, codificación de bloques por efectos y la gráfica de superficie."))
        ad = E.anderson_darling(res) if len(res) >= 8 else None
        supuestos = [("Residuos normales", "Anderson-Darling y gráfica de probabilidad (RSM-PRUEBAS-2DO-ORDEN)",
                      (f"{p_igual(ad['p'], .005)}: " + ("no se rechaza la normalidad" if ad["p"] > 0.05 else "se rechaza la normalidad")) if ad else "pocos datos"),
                     ("Varianza constante", "Residuos contra ajustados", "Revisa que no haya forma de embudo"),
                     ("Independencia", "Residuos contra orden de corrida", "Corre los experimentos en orden aleatorio y revisa que no haya tendencia")]
        avisos = [f"{fuera} filas incompletas quedaron fuera (corridas sin respuesta)."] if fuera else []
        if retenidos: avisos.append("Se conservaron por jerarquía los términos lineales: " + ", ".join(retenidos) + ".")
        if desconocidos: avisos.append("No se reconocieron estos términos a quitar: " + ", ".join(desconocidos) + ".")
        if not diseno and not p.get("niveles"):
            avisos.append("Niveles bajo y alto inferidos de los datos: " + "; ".join(f"{n} {num(b_)} a {num(a_)}" for n, b_, a_ in zip(nombres, bajos, altos))
                          + ". Si no son los del diseño, indícalos en «Niveles».")
        modelo_guardado = {"respuesta": ny, "factores": nombres, "bajos": bajos, "altos": altos, "b0": b0, "b": b.tolist(), "B": B.tolist(),
                           "limite": lim, "terminos": [D.nombre_termino(t, nombres) for t in ts]}
        return resultado(cls.ID, f"Superficie de respuesta de {ny}", p, bloques_out, avisos, supuestos=supuestos, interpretacion=interp,
                         datos={"columnas": [yj] + xs + ([bj] if bc else []), "modelo_rsm": modelo_guardado}, png=png)


# ---------------- optimizador ----------------
METAS = [["max", "Maximizar"], ["min", "Minimizar"], ["objetivo", "Llegar a un objetivo"]]


@registrar
class Optimizador(ModuloDialogo):
    ID, TITULO, HOJA_VACIA_OK = "OPTIMIZADOR", "Optimizador de respuestas", True
    CAMPOS = []

    @classmethod
    def dialogo(cls, hoja, proyecto=None):
        modelos = [[r["uid"], f"{r['titulo']} ({r['fecha']})"] for r in (proyecto.resultados if proyecto else [])
                   if r["modulo"] == "RSM" and r.get("datos", {}).get("modelo_rsm")]
        ops = [["", "(ninguna)"]] + modelos
        campos = []
        for q in (1, 2, 3):
            campos += [{"campo": f"r{q}", "etiqueta": f"Respuesta {q}: modelo analizado" + ("" if q == 1 else " (opcional)"), "tipo": "opcion",
                        "opciones": ops if q > 1 else modelos or [["", "No hay superficies analizadas en el proyecto"]],
                        "defecto": (modelos[0][0] if q == 1 and modelos else "")},
                       {"campo": f"meta{q}", "etiqueta": "Meta", "tipo": "opcion", "opciones": METAS, "defecto": "max"},
                       {"campo": f"inf{q}", "etiqueta": "Inferior (mínimo aceptable; no se usa al minimizar)", "tipo": "numero"},
                       {"campo": f"obj{q}", "etiqueta": "Objetivo (valor ideal)", "tipo": "numero"},
                       {"campo": f"sup{q}", "etiqueta": "Superior (máximo aceptable; no se usa al maximizar)", "tipo": "numero"},
                       {"campo": f"peso{q}", "etiqueta": "Peso (0.1 a 10; 1 = lineal)", "tipo": "numero", "defecto": "1"},
                       {"campo": f"imp{q}", "etiqueta": "Importancia (0.1 a 10)", "tipo": "numero", "defecto": "1"}]
        campos.append({"campo": "region", "etiqueta": "Buscar dentro de", "tipo": "opcion", "defecto": "cubo",
                       "opciones": [["cubo", "Los niveles bajo y alto (cubo)"], ["diseno", "Toda la región del diseño (incluye puntos axiales)"]]})
        return {"id": cls.ID, "titulo": cls.TITULO, "campos": campos, "columnas": []}

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        res_por_uid = {r["uid"]: r for r in (proyecto.resultados if proyecto else [])}
        resp = []
        for q in (1, 2, 3):
            uid = p.get(f"r{q}")
            if not uid: continue
            r = res_por_uid.get(uid)
            if r is None or not r.get("datos", {}).get("modelo_rsm"): raise ErrorEntrada(f"La respuesta {q} no es una superficie analizada del proyecto.")
            mr = r["datos"]["modelo_rsm"]
            meta = p.get(f"meta{q}") or "max"
            inf, obj, sup = (cls.numero(p, f"{x}{q}", f"{e} de la respuesta {q}") for x, e in (("inf", "El inferior"), ("obj", "El objetivo"), ("sup", "El superior")))
            peso = cls.numero(p, f"peso{q}", "El peso") or 1.0; imp = cls.numero(p, f"imp{q}", "La importancia") or 1.0
            if not (0.1 <= peso <= 10 and 0.1 <= imp <= 10): raise ErrorEntrada("Peso e importancia deben estar entre 0.1 y 10.")
            if meta == "max" and (inf is None or obj is None or inf >= obj): raise ErrorEntrada(f"Respuesta {q}: al maximizar indica inferior < objetivo.")
            if meta == "min" and (sup is None or obj is None or obj >= sup): raise ErrorEntrada(f"Respuesta {q}: al minimizar indica objetivo < superior.")
            if meta == "objetivo" and (None in (inf, obj, sup) or not inf <= obj <= sup or inf == sup):
                raise ErrorEntrada(f"Respuesta {q}: para un objetivo indica inferior ≤ objetivo ≤ superior.")
            resp.append({"mr": mr, "modelo": (mr["b0"], np.array(mr["b"]), np.array(mr["B"])), "meta": meta, "inferior": inf, "objetivo": obj,
                         "superior": sup, "peso": peso, "importancia": imp})
        if not resp: raise ErrorEntrada("Elige al menos una superficie analizada (Estadística > Superficie de respuesta > Analizar).")
        base = resp[0]["mr"]
        for r in resp[1:]:
            if [f.lower() for f in r["mr"]["factores"]] != [f.lower() for f in base["factores"]] or r["mr"]["bajos"] != base["bajos"] or r["mr"]["altos"] != base["altos"]:
                raise ErrorEntrada("Todas las respuestas deben venir de modelos con los mismos factores y niveles.")
        k = len(base["factores"]); lim = 1.0 if (p.get("region") or "cubo") == "cubo" else base["limite"]
        opt = D.optimizar(resp, k, lim)
        orig = D.a_original(opt["x"], base["bajos"], base["altos"])
        fac = [[base["factores"][i], num(orig[i], 5), num(opt["x"][i], 4), f"{num(D.a_original([-lim], [base['bajos'][i]], [base['altos'][i]])[0], 5)} a "
                f"{num(D.a_original([lim], [base['bajos'][i]], [base['altos'][i]])[0], 5)}"] for i in range(k)]
        sal = [[r["mr"]["respuesta"], dict(METAS)[r["meta"]], num(r["inferior"]), num(r["objetivo"]), num(r["superior"]), num(y, 5), num(d, 4)]
               for r, y, d in zip(resp, opt["y"], opt["d"])]
        # gráfica de optimización: cada respuesta contra cada factor, con los demás en el óptimo
        fig, axs = figura(max(4.0, 2.4 * k), 2.0 * len(resp) + 0.6, nrows=len(resp), ncols=k)
        axs = np.array(axs).reshape(len(resp), k)
        g = np.linspace(-lim, lim, 81)
        for a_, r in enumerate(resp):
            for i in range(k):
                ax = axs[a_][i]; vals = []
                for v in g:
                    xv = np.array(opt["x"], float); xv[i] = v; vals.append(D.predecir_codificado(r["modelo"], xv))
                xo = [D.a_original([v], [base["bajos"][i]], [base["altos"][i]])[0] for v in g]
                ax.plot(xo, vals, color=TINTA, lw=1.1); ax.axvline(orig[i], color="#b3261e", lw=1); ax.tick_params(labelsize=6)
                if r["objetivo"] is not None: ax.axhline(r["objetivo"], color=NARANJA, lw=0.8, ls="--")
                if a_ == 0: ax.set_title(f"{base['factores'][i]}\n{num(orig[i], 4)}", fontsize=8)
                if i == 0: ax.set_ylabel(f"{r['mr']['respuesta']}\ny = {num(opt['y'][a_], 4)}", fontsize=7)
        fig.suptitle(f"Deseabilidad compuesta D = {opt['D']:.4f}", fontsize=9, color=TINTA)
        svg, png = a_svg_png(fig)
        concl = (f"Combinación sugerida: " + ", ".join(f"{base['factores'][i]} = {num(orig[i], 5)}" for i in range(k)) +
                 f". Deseabilidad compuesta D = {opt['D']:.4f} (1 = todas las respuestas en su ideal; 0 = alguna fuera de lo aceptable).")
        interp = ["El óptimo es una predicción del modelo: confírmalo con corridas de verificación antes de fijarlo en el proceso "
                  "(28_BB RSM-PUNTO-ESTACIONARIO usa el optimizador y después se confirma).",
                  "La búsqueda se limita a la región elegida; fuera de ella el modelo no está respaldado por datos."]
        if opt["D"] == 0: interp.insert(0, "Ninguna combinación dentro de la región deja todas las respuestas en su rango aceptable: revisa los límites o la región.")
        return resultado(cls.ID, "Optimización de " + ", ".join(r["mr"]["respuesta"] for r in resp), p, [
            b_texto(concl, "conclusion"), b_grafica(svg),
            b_tabla("Ajuste óptimo de los factores", ["Factor", "Valor", "Codificado", "Región de búsqueda"], fac),
            b_tabla("Respuestas", ["Respuesta", "Meta", "Inferior", "Objetivo", "Superior", "Predicción", "Deseabilidad"], sal),
            b_texto("Deseabilidad de Derringer y Suich con peso e importancia (como el optimizador de respuesta de Minitab); búsqueda global por "
                    "evolución diferencial con refinamiento local. No respaldados por la base: la función de deseabilidad y el método de búsqueda.")],
            interpretacion=interp, datos={"columnas": []}, png=png)
