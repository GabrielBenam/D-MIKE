"""FPY y RTY con regla explícita de primer evento (G4).

FPY de un paso = unidades aprobadas en su PRIMERA inspección / unidades inspeccionadas por primera vez.
RTY = producto de los rendimientos (FPY) de cada paso. El retrabajo cuenta como no correcto a la primera: una unidad que se
rechazó y se corrigió hasta pasar NO cuenta como aprobada a la primera (esa es la diferencia entre el rendimiento final y el FPY,
el «trabajo oculto»). Fuente: 16_GB_HISTOGRAMAS_CAPACIDAD_DESEMPENO (RTY y trabajo oculto), regla definida para D-MIKE.
Si los datos no permiten identificar el primer evento de cada unidad en cada paso, el resultado es «no calculable» con su
motivo, nunca un valor aproximado.
"""
from collections import OrderedDict
from . import registrar
from .base import (ErrorEntrada, columna, nombre_col, figura, a_svg_png, num, resultado, b_grafica, b_tabla, b_texto, _f,
                   NARANJA, TINTA, SUAVE, _sin_acentos)
from .dialogo import ModuloDialogo

FUENTE = "16_GB_HISTOGRAMAS_CAPACIDAD_DESEMPENO, RTY y trabajo oculto"
APROBADO, RECHAZO = "Aprobado, OK, Pasa, Sí", "Rechazado, No, Falla, Defecto, Retrabajo"


def _lista(texto): return {_sin_acentos(x).strip() for x in str(texto or "").split(",") if x.strip()}


def calcular(eventos, aprobados, rechazos, declaro_primera=False):
    """eventos: lista de dicts {unidad, paso, resultado (texto), intento (float|None), fecha (date|None), orden (int)}.
    Devuelve {pasos: [...], rty, motivo_rty, excluidos}. Cada paso: {paso, n, aprobadas, fpy, estado, motivo, base, retrabajo, finales}.
    estado: «ok», «no_definido» (denominador 0) o «no_calculable» (con motivo)."""
    ap, rc = _lista(aprobados), _lista(rechazos)
    if ap & rc: raise ErrorEntrada("Un mismo valor no puede ser aprobado y no aprobado a la vez: " + ", ".join(sorted(ap & rc)) + ".")
    pasos = OrderedDict()
    sin_clasificar = OrderedDict(); na = sin_datos = 0
    for e in eventos:
        pasos.setdefault(e["paso"], OrderedDict()).setdefault(e["unidad"], []).append(e)
    salida, fpys = [], []
    for paso, unidades in pasos.items():
        problemas, n, aprob, retrab = [], 0, 0, 0
        primeras, contadas = {}, []
        for u, evs in unidades.items():
            primero, motivo = _primer_evento(evs, declaro_primera)
            if primero is None: problemas.append((u, motivo)); continue
            primeras[u] = (primero, evs)
        if problemas:
            ej = "; ".join(f"{u}: {m}" for u, m in problemas[:5]) + (f" (y {len(problemas) - 5} unidades más)" if len(problemas) > 5 else "")
            salida.append({"paso": paso, "estado": "no_calculable", "motivo": f"no se puede identificar el primer evento de {len(problemas)} "
                           f"de {len(unidades)} unidades. {ej}", "n": None, "aprobadas": None, "fpy": None, "retrabajo": None, "finales": None})
            fpys.append(None); continue
        for u, (primero, evs) in primeras.items():
            r = _sin_acentos(primero["resultado"]).strip()
            if r in ("n/a",): na += 1; continue
            if r in ("", "sin datos", "s/d"): sin_datos += 1; continue
            if r in ap: n += 1; aprob += 1
            elif r in rc: n += 1
            else: sin_clasificar.setdefault(primero["resultado"], []).append(u); continue
            contadas.append((primero, evs))
            if len(evs) > 1: retrab += 1
        n_fin = _finales_aprobadas(contadas, ap)
        if n == 0:
            salida.append({"paso": paso, "estado": "no_definido", "motivo": "ninguna unidad con resultado clasificado en su primera inspección (denominador 0)",
                           "n": 0, "aprobadas": 0, "fpy": None, "retrabajo": 0, "finales": None}); fpys.append(None); continue
        salida.append({"paso": paso, "estado": "ok", "motivo": "", "n": n, "aprobadas": aprob, "fpy": aprob / n, "retrabajo": retrab, "finales": n_fin})
        fpys.append(aprob / n)
    rty, motivo = None, ""
    if not salida: motivo = "no hay eventos."
    elif any(p["estado"] == "no_calculable" for p in salida):
        motivo = "los pasos " + ", ".join(f"«{p['paso']}»" for p in salida if p["estado"] == "no_calculable") + " no son calculables, y el RTY necesita el FPY de todos los pasos."
    elif any(p["estado"] == "no_definido" for p in salida):
        motivo = "los pasos " + ", ".join(f"«{p['paso']}»" for p in salida if p["estado"] == "no_definido") + " tienen denominador 0, y el RTY necesita el FPY de todos los pasos."
    else:
        rty = 1.0
        for f in fpys: rty *= f
    return {"pasos": salida, "rty": rty, "motivo_rty": motivo, "sin_clasificar": sin_clasificar, "na": na, "sin_datos": sin_datos}


def _primer_evento(evs, declaro_primera):
    """Primer evento de una unidad en un paso, o (None, motivo). Usa el número de intento si existe; si no, la fecha; si no hay
    ninguno, solo si el usuario declaró que cada fila es la primera inspección y hay un único evento."""
    con_intento = [e for e in evs if e["intento"] is not None]
    if any(e["intento"] is not None for e in evs):
        if len(con_intento) != len(evs): return None, "hay eventos sin número de intento"
        unos = [e for e in evs if e["intento"] == 1]
        if not unos: return None, f"no hay un evento con intento 1 (el menor es {num(min(e['intento'] for e in evs))}): falta la primera inspección"
        if len(unos) > 1: return None, "hay más de un evento con intento 1"
        return unos[0], ""
    if any(e["fecha"] is not None for e in evs):
        if any(e["fecha"] is None for e in evs): return None, "hay eventos sin fecha"
        menor = min(e["fecha"] for e in evs)
        empate = [e for e in evs if e["fecha"] == menor]
        if len(empate) > 1 and len({_sin_acentos(e["resultado"]).strip() for e in empate}) > 1:
            return None, f"hay {len(empate)} eventos con resultados distintos el {menor.strftime('%d/%m/%Y')} y no se sabe cuál fue el primero"
        return empate[0], ""
    if declaro_primera:
        if len(evs) > 1: return None, "hay más de una fila y no hay intento ni fecha para saber cuál fue la primera"
        return evs[0], ""
    return None, "sin número de intento ni fecha no se sabe si el resultado es el de la primera inspección o el final"


def _finales_aprobadas(primeras, ap):
    """Unidades cuyo último evento (mayor intento o fecha) es aprobado; informativo (rendimiento final, sin trabajo oculto)."""
    n = 0
    for _, evs in primeras:
        if any(e["intento"] is not None for e in evs): ult = max(evs, key=lambda e: e["intento"])
        elif any(e["fecha"] is not None for e in evs): ult = max(evs, key=lambda e: (e["fecha"], e["orden"]))
        else: ult = evs[-1]
        if _sin_acentos(ult["resultado"]).strip() in ap: n += 1
    return n


@registrar
class Rendimiento(ModuloDialogo):
    ID, TITULO = "RENDIMIENTO", "FPY y RTY (rendimiento a la primera)"
    CAMPOS = [{"campo": "unidad", "etiqueta": "Unidad (pieza, documento o folio)", "tipo": "col"},
              {"campo": "paso", "etiqueta": "Paso o etapa (vacío = un solo paso)", "tipo": "col", "opcional": True},
              {"campo": "resultado", "etiqueta": "Resultado de la inspección (texto o 1/0)", "tipo": "col"},
              {"campo": "aprobado", "etiqueta": "Valores que cuentan como aprobado (separados por coma)", "tipo": "texto", "defecto": APROBADO},
              {"campo": "rechazo", "etiqueta": "Valores que cuentan como no aprobado (separados por coma)", "tipo": "texto", "defecto": RECHAZO},
              {"campo": "intento", "etiqueta": "Número de intento (1 = primera inspección)", "tipo": "col", "filtro": "num", "opcional": True},
              {"campo": "fecha", "etiqueta": "Fecha del evento (si no hay número de intento)", "tipo": "col", "filtro": "fecha", "opcional": True},
              {"campo": "declaro", "etiqueta": "Declaro que cada fila es la primera inspección de su unidad en ese paso (solo si no hay intento ni fecha)",
               "tipo": "bool", "defecto": False}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        ju = p.get("unidad"); columna(hoja, ju, "la unidad")
        jp = p.get("paso"); columna(hoja, jp, "el paso", obligatoria=False)
        jr = p.get("resultado"); columna(hoja, jr, "el resultado")
        ji = p.get("intento"); columna(hoja, ji, "el número de intento", "num", obligatoria=False)
        jf = p.get("fecha"); columna(hoja, jf, "la fecha", "fecha", obligatoria=False)
        ap, rc = p.get("aprobado", APROBADO) or "", p.get("rechazo", RECHAZO) or ""
        if not _lista(ap): raise ErrorEntrada("Indica qué valores del resultado cuentan como aprobado.")
        act = hoja.filas_activas(); eventos, vacias = [], 0
        for i in range(hoja.n):
            if act is not None and i not in act: continue
            u = hoja.columnas[ju].valor(i)
            if hoja.columnas[ju].estado(i) != "valor": 
                if any(hoja.columnas[j].estado(i) != "sin_datos" for j in (jr, jp, ji, jf) if j is not None): vacias += 1
                continue
            paso = (hoja.columnas[jp].valor(i)[0] if jp is not None and hoja.columnas[jp].estado(i) == "valor" else "") or "Único"
            res = hoja.columnas[jr].valor(i)[0] if hoja.columnas[jr].estado(i) != "sin_datos" else ""
            eventos.append({"unidad": u[0], "paso": str(paso), "resultado": res,
                            "intento": hoja.columnas[ji].valor(i)[2] if ji is not None and hoja.columnas[ji].estado(i) == "valor" else None,
                            "fecha": hoja.columnas[jf].valor(i)[2] if jf is not None and hoja.columnas[jf].estado(i) == "valor" else None, "orden": i})
        if not eventos: raise ErrorEntrada("No hay eventos con unidad: revisa las columnas elegidas.")
        r = calcular(eventos, ap, rc, bool(p.get("declaro")))
        pasos = r["pasos"]; avisos = []
        if vacias: avisos.append(f"{vacias} filas sin unidad quedaron fuera del cálculo.")
        if r["sin_datos"]: avisos.append(f"Sin datos: {r['sin_datos']} unidades tienen la primera inspección sin resultado; quedan fuera de la base (no cuentan como aprobadas ni como rechazadas).")
        if r["na"]: avisos.append(f"N/A: {r['na']} primeras inspecciones no aplican y quedan fuera de la base.")
        for val, us in r["sin_clasificar"].items():
            avisos.append(f"El resultado «{val}» ({len(us)} unidades) no está en la lista de aprobados ni de no aprobados: esas unidades quedaron fuera de la base. Agrégalo a una de las listas.")
        nom = nombre_col(hoja, jr)
        # tabla
        filas = []
        for q in pasos:
            if q["estado"] == "ok":
                filas.append([q["paso"], q["n"], q["aprobadas"], q["fpy"] * 100, q["retrabajo"], q["finales"]])
            else:
                filas.append([q["paso"], "no calculable" if q["estado"] == "no_calculable" else (q["n"] or 0), "—", "no calculable" if q["estado"] == "no_calculable" else "no definido", "—", "—"])
        bloques = []
        calculables = [q for q in pasos if q["estado"] == "ok"]
        if calculables:
            fig, ax = figura(max(5.6, 0.9 * (len(pasos) + 1) + 2), 3.4)
            etiquetas = [q["paso"] for q in pasos] + (["RTY"] if r["rty"] is not None else [])
            vals = [(q["fpy"] * 100 if q["estado"] == "ok" else 0) for q in pasos] + ([r["rty"] * 100] if r["rty"] is not None else [])
            colores = [NARANJA if q["estado"] == "ok" else "#cfc8bb" for q in pasos] + ([TINTA] if r["rty"] is not None else [])
            ax.bar(range(len(vals)), vals, color=colores, width=0.7); ax.set_ylim(0, 105)
            ax.set_xticks(range(len(vals))); ax.set_xticklabels(etiquetas, rotation=20 if len(vals) > 5 else 0)
            for x, v in enumerate(vals): ax.text(x, v + 1.5, f"{v:.1f}%" if v else "", ha="center", fontsize=8, color=TINTA)
            ax.set_ylabel("% aprobado a la primera"); ax.set_title(f"FPY por paso y RTY de {nom}")
            svg, png = a_svg_png(fig); bloques.append(b_grafica(svg))
        else: png = None
        if r["rty"] is not None:
            concl = (f"RTY = {r['rty'] * 100:.2f}% (producto de los FPY de {len(pasos)} {'paso' if len(pasos) == 1 else 'pasos'}: "
                     + " × ".join(f"{q['fpy'] * 100:.1f}%" for q in pasos) + "). Cada porcentaje de FPY lleva su base en la tabla.")
        else:
            concl = f"RTY no calculable: {r['motivo_rty']}"
        bloques.append(b_texto(concl, "conclusion"))
        bloques.append(b_tabla("Primer evento por paso (cada % con su base)", ["Paso", "Inspeccionadas por primera vez", "Aprobadas a la primera",
                                                                               "FPY (%)", "Unidades con retrabajo", "Aprobadas al final"], filas,
                               ["i", "d", "d", "d", "d", "d"]))
        for q in pasos:
            if q["estado"] != "ok":
                bloques.append(b_texto(f"Paso «{q['paso']}»: {'NO CALCULABLE' if q['estado'] == 'no_calculable' else 'NO DEFINIDO'}. Motivo: {q['motivo']}.", "advertencia"))
        if calculables:
            bloques.append(b_texto("Trabajo oculto: las unidades «aprobadas al final» incluyen las que pasaron tras retrabajo; el FPY no las cuenta como correctas a la "
                                   "primera. Una diferencia grande entre «aprobadas al final» y «aprobadas a la primera» es retrabajo que el rendimiento final no muestra.", "interpretacion"))
        regla = ("Regla de primer evento: " + ("número de intento (1 = primera inspección)" if ji is not None else "fecha del evento (el más antiguo de cada unidad y paso)" if jf is not None
                 else "declarada por el usuario: cada fila es la primera inspección") + ". FPY = aprobadas en su primera inspección / inspeccionadas por primera vez; RTY = producto de los FPY. "
                 f"Fuente: {FUENTE}. Verificación contra el ejemplo resuelto del curso: pendiente, el archivo 16_GB no está en el repositorio; "
                 "verificado con cálculo a mano en pruebas/test_g4_rendimiento.py. El supuesto de que el registro incluye todas las inspecciones no se puede comprobar con los datos.")
        bloques.append(b_texto(regla, "nota"))
        return resultado(cls.ID, f"FPY y RTY de {nom}", p, bloques, avisos, datos={"columnas": [j for j in (ju, jp, jr, ji, jf) if j is not None],
                         "rty": _f(r["rty"]), "pasos": [{"paso": q["paso"], "estado": q["estado"], "n": q["n"], "aprobadas": q["aprobadas"], "fpy": _f(q["fpy"]), "motivo": q["motivo"]} for q in pasos]},
                         png=png)
