"""G5 (revisión de la calidad de los datos) y G6 (duración entre dos fechas), versión 0.30.0. Solo leen la hoja: no la modifican, no generan datos y no entran al
paquete de avance. Reportan conteos y números de fila (1 = primera fila de la hoja), nunca el contenido de las celdas.

G5, «Revisar la calidad de los datos»: cuatro revisiones, cada una «cumple», «no cumple» o «no evaluable»:
  duplicados (coincidencia EXACTA del texto de las columnas clave), fechas retroactivas (cierre anterior a la apertura, sin umbral), primer evento ausente
  (la misma regla de primer evento de RENDIMIENTO, G4) y capturas por lote (registros con la misma fecha y hora de captura, con el tamaño mínimo que fija el
  usuario, sin valor por defecto). Criterio de diseño de D-MIKE; no respaldado por el curso (la base solo respalda errores de recolección,
  15_GB_ESTADISTICA_Y_MUESTREO).
G6, «Duración entre dos fechas»: lead time entre dos columnas de fecha (02_DIAGNOSTICO), en días con fracción, sin días hábiles ni feriados. Mediana: 15_GB
  (EST-CENTRAL). P90: el método de percentil de D-MIKE que ya usan los cuartiles de Estadísticos (posición p(n+1) con interpolación lineal, como Minitab; 17_GB
  BOX-PROCEDIMIENTO pide cuartiles pero no fija el método); P90 no respaldado por el curso. Sin metas ni acuerdos de nivel de servicio.
"""
import re
from collections import OrderedDict
from datetime import datetime
from . import registrar, estadistica as E
from .analisis import clases_histograma
from .base import ErrorEntrada, columna, figura, a_svg_png, num, resultado, b_grafica, b_tabla, b_texto, _f, NARANJA, TINTA, CLARO
from .dialogo import ModuloDialogo
from .rendimiento import _primer_evento
from ..nucleo.hoja import es_na, es_sin_datos_explicito, a_fecha

NOTA_G5 = "Criterio de diseño de D-MIKE; no respaldado por el curso (la base solo respalda errores de recolección, 15_GB_ESTADISTICA_Y_MUESTREO)."
MAX_FILAS = 30                                                    # números de fila que se listan por revisión; el resto se cuenta

_HORA = r"(?:[T ]+(\d{1,2}):(\d{2})(?::(\d{2}))?)?"
_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})" + _HORA + r"$")
_DMA = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})" + _HORA + r"$")   # día/mes/año, como la hoja


def a_fechahora(texto):
    """(datetime, con_hora) o (None, False). Acepta AAAA-MM-DD o DD/MM/AAAA, con hora opcional (HH:MM o HH:MM:SS, separada por espacio o T).
    Una fecha sin hora es la medianoche de ese día y con_hora = False."""
    t = str(texto or "").strip()
    for patron, orden in ((_ISO, (1, 2, 3)), (_DMA, (3, 2, 1))):
        m = patron.match(t)
        if not m: continue
        try:
            y, mo, d = (int(m[k]) for k in orden)
            hh, mi, ss = (int(m[k]) if m[k] is not None else 0 for k in (4, 5, 6))
            return datetime(y, mo, d, hh, mi, ss), m[4] is not None
        except ValueError:
            return None, False
    return None, False


def _estado_texto(col, i):
    """«valor», «sin_datos» o «na» según el texto crudo de la celda (no depende del tipo de la columna)."""
    t = col.celdas[i] if i < len(col.celdas) else None
    if t is None or str(t).strip() == "" or es_sin_datos_explicito(t): return "sin_datos"
    if es_na(t): return "na"
    return "valor"


def _filas(hoja):
    act = hoja.filas_activas()
    return [i for i in range(hoja.n) if act is None or i in act]


def _lista_filas(filas):
    filas = sorted(set(filas)); vis = ", ".join(str(i + 1) for i in filas[:MAX_FILAS])
    return vis + (f" (y {len(filas) - MAX_FILAS} más)" if len(filas) > MAX_FILAS else "")


def _pct(a, b): return f"{a} de {b} ({100 * a / b:.1f} %)" if b else f"{a} de {b}"


def _rev(id_, titulo, estado, detalle): return {"id": id_, "titulo": titulo, "estado": estado, "detalle": detalle}


ETIQUETA = {"cumple": "Cumple", "no_cumple": "No cumple", "no_evaluable": "No evaluable"}


def _categoria(motivo):
    """Categoría del motivo de RENDIMIENTO sin copiar datos de las celdas (los motivos originales pueden citar fechas o números)."""
    for ini, cat in (("hay eventos sin número de intento", "eventos sin número de intento"), ("no hay un evento con intento 1", "falta el evento con intento 1"),
                     ("hay más de un evento con intento 1", "más de un evento con intento 1"), ("hay eventos sin fecha", "eventos sin fecha"),
                     ("hay más de una fila", "varias filas sin número de intento ni fecha"), ("sin número de intento ni fecha", "sin número de intento ni fecha")):
        if motivo.startswith(ini): return cat
    return "fecha repetida con resultados distintos" if "resultados distintos" in motivo else "otro motivo"


@registrar
class CalidadDatos(ModuloDialogo):
    ID, TITULO = "CALIDAD-DATOS", "Revisar la calidad de los datos"
    CAMPOS = [{"campo": "claves", "etiqueta": "Duplicados: columnas clave (la fila se repite si todas coinciden exactamente)", "tipo": "cols", "opcional": True},
              {"campo": "apertura", "etiqueta": "Fechas: columna de apertura", "tipo": "col", "opcional": True},
              {"campo": "cierre", "etiqueta": "Fechas: columna de cierre (una fecha anterior a la apertura es retroactiva)", "tipo": "col", "opcional": True},
              {"campo": "unidad", "etiqueta": "Primer evento: unidad (pieza, documento o folio)", "tipo": "col", "opcional": True},
              {"campo": "paso", "etiqueta": "Primer evento: paso o etapa (vacío = un solo paso)", "tipo": "col", "opcional": True},
              {"campo": "resultado", "etiqueta": "Primer evento: resultado de la inspección (opcional; desempata fechas iguales como en Rendimientos)", "tipo": "col", "opcional": True},
              {"campo": "intento", "etiqueta": "Primer evento: número de intento (1 = primera inspección)", "tipo": "col", "filtro": "num", "opcional": True},
              {"campo": "fecha", "etiqueta": "Primer evento: fecha del evento (si no hay número de intento)", "tipo": "col", "filtro": "fecha", "opcional": True},
              {"campo": "declaro", "etiqueta": "Declaro que cada fila es la primera inspección de su unidad en ese paso (solo si no hay intento ni fecha)", "tipo": "bool", "defecto": False},
              {"campo": "captura", "etiqueta": "Lotes: columna con la fecha y hora de captura", "tipo": "col", "opcional": True},
              {"campo": "lote_min", "etiqueta": "Lotes: tamaño mínimo de un lote (lo fijas tú; no hay valor por defecto)", "tipo": "numero"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        claves = [j for j in (p.get("claves") or []) if j is not None]
        for j in claves: columna(hoja, j, "las columnas clave")
        ja, jc = p.get("apertura"), p.get("cierre")
        columna(hoja, ja, "la apertura", obligatoria=False); columna(hoja, jc, "el cierre", obligatoria=False)
        ju, jp, jr = p.get("unidad"), p.get("paso"), p.get("resultado")
        columna(hoja, ju, "la unidad", obligatoria=False); columna(hoja, jp, "el paso", obligatoria=False); columna(hoja, jr, "el resultado", obligatoria=False)
        ji = p.get("intento"); columna(hoja, ji, "el número de intento", "num", obligatoria=False)
        jf = p.get("fecha"); columna(hoja, jf, "la fecha del evento", "fecha", obligatoria=False)
        jk = p.get("captura"); columna(hoja, jk, "la captura", obligatoria=False)
        lote_min = None
        if jk is not None:
            lote_min = cls.numero(p, "lote_min", "el tamaño mínimo del lote", opcional=False)
            if lote_min != int(lote_min) or lote_min < 2: raise ErrorEntrada("El tamaño mínimo del lote debe ser un entero de 2 o más: lo fijas tú.")
            lote_min = int(lote_min)
        usadas = set(claves) | {j for j in (ja, jc, ju, jp, jr, ji, jf, jk) if j is not None}
        if not usadas: raise ErrorEntrada("Elige las columnas de al menos una revisión.")
        filas = _filas(hoja)
        if not any(_estado_texto(hoja.columnas[j], i) == "valor" for j in usadas for i in filas):
            raise ErrorEntrada("Las columnas elegidas no tienen datos: no hay nada que revisar.")
        revs = [cls._duplicados(hoja, filas, claves), cls._retroactivas(hoja, filas, ja, jc), cls._primer_evento(hoja, filas, ju, jp, jr, ji, jf, bool(p.get("declaro"))),
                cls._lotes(hoja, filas, jk, lote_min)]
        cuenta = {e: sum(1 for r in revs if r["estado"] == e) for e in ETIQUETA}
        concl = (f"Revisiones: {cuenta['cumple']} cumplen, {cuenta['no_cumple']} no cumplen y {cuenta['no_evaluable']} no son evaluables con las columnas elegidas. "
                 "Los números son filas de la hoja; D-MIKE no muestra el contenido de las celdas.")
        return resultado(cls.ID, "Calidad de los datos", p, [
            b_texto(concl, "conclusion"),
            b_tabla("Revisiones", ["Revisión", "Resultado", "Detalle"], [[r["titulo"], ETIQUETA[r["estado"]], r["detalle"]] for r in revs]),
            b_texto("Notas: " + NOTA_G5 + " Duplicados: coincidencia exacta del texto de las celdas, sin quitar espacios ni distinguir otra cosa que lo escrito; las filas con alguna "
                    "celda clave vacía o «Sin datos» no se comparan. Fecha retroactiva: cierre anterior a la apertura, sin umbral; una fecha sin hora es la medianoche de ese día. "
                    "Primer evento: la misma regla que Rendimientos. Lotes: registros con exactamente la misma fecha y hora de captura; si la columna no trae hora, no es evaluable.")],
            [], datos={"columnas": sorted(usadas), "revisiones": revs})

    @staticmethod
    def _duplicados(hoja, filas, claves):
        t = "Duplicados"
        if not claves: return _rev("duplicados", t, "no_evaluable", "No elegiste columnas clave.")
        grupos = OrderedDict(); excl = 0
        for i in filas:
            if any(_estado_texto(hoja.columnas[j], i) != "valor" for j in claves): excl += 1; continue
            grupos.setdefault(tuple(hoja.columnas[j].celdas[i] for j in claves), []).append(i)
        n = sum(len(v) for v in grupos.values())
        if n == 0: return _rev("duplicados", t, "no_evaluable", f"Ninguna fila trae todas las columnas clave ({excl} filas excluidas por tener alguna vacía, «Sin datos» o N/A).")
        rep = [v for v in grupos.values() if len(v) > 1]
        sobran = sum(len(v) - 1 for v in rep); base = f"{n} filas comparadas" + (f"; {excl} excluidas por tener alguna clave vacía, «Sin datos» o N/A" if excl else "")
        if not rep: return _rev("duplicados", t, "cumple", f"Ninguna fila se repite ({base}).")
        return _rev("duplicados", t, "no_cumple", f"{_pct(sobran, n)} son repeticiones, en {len(rep)} grupos de filas idénticas en las columnas clave ({base}). Filas involucradas: "
                    + _lista_filas([i for v in rep for i in v]) + ".")

    @staticmethod
    def _retroactivas(hoja, filas, ja, jc):
        t = "Fechas retroactivas"
        if ja is None or jc is None: return _rev("retroactivas", t, "no_evaluable", "Faltan la columna de apertura o la de cierre.")
        pares, retro, excl = 0, [], 0
        for i in filas:
            ea, ec = _estado_texto(hoja.columnas[ja], i), _estado_texto(hoja.columnas[jc], i)
            if ea == "sin_datos" and ec == "sin_datos": continue
            a, _ = a_fechahora(hoja.columnas[ja].celdas[i]) if ea == "valor" else (None, False)
            c, _ = a_fechahora(hoja.columnas[jc].celdas[i]) if ec == "valor" else (None, False)
            if a is None or c is None: excl += 1; continue
            pares += 1
            if c < a: retro.append(i)
        ex = f"; {excl} filas excluidas por tener una fecha vacía, N/A o inválida" if excl else ""
        if pares == 0: return _rev("retroactivas", t, "no_evaluable", f"No hay filas con las dos fechas válidas{ex}.")
        if not retro: return _rev("retroactivas", t, "cumple", f"Ningún cierre es anterior a su apertura ({pares} filas revisadas{ex}).")
        return _rev("retroactivas", t, "no_cumple", f"{_pct(len(retro), pares)} tienen el cierre anterior a la apertura{ex}. Filas: {_lista_filas(retro)}.")

    @staticmethod
    def _primer_evento(hoja, filas, ju, jp, jr, ji, jf, declaro):
        t = "Primer evento ausente"
        if ju is None: return _rev("primer_evento", t, "no_evaluable", "No elegiste la columna de unidad.")
        if ji is None and jf is None and not declaro:
            return _rev("primer_evento", t, "no_evaluable", "Sin número de intento ni fecha no se puede identificar el primer evento: elige una de las dos columnas o declara que cada fila es la primera.")
        pasos, sin_unidad = OrderedDict(), 0
        for i in filas:
            if _estado_texto(hoja.columnas[ju], i) != "valor": sin_unidad += 1; continue
            paso = (hoja.columnas[jp].valor(i)[0] if jp is not None and hoja.columnas[jp].estado(i) == "valor" else "") or "Único"
            res = hoja.columnas[jr].valor(i)[0] if jr is not None and hoja.columnas[jr].estado(i) != "sin_datos" else ""
            ev = {"unidad": hoja.columnas[ju].celdas[i], "paso": str(paso), "resultado": res,
                  "intento": hoja.columnas[ji].valor(i)[2] if ji is not None and hoja.columnas[ji].estado(i) == "valor" else None,
                  "fecha": hoja.columnas[jf].valor(i)[2] if jf is not None and hoja.columnas[jf].estado(i) == "valor" else None, "orden": i}
            pasos.setdefault(ev["paso"], OrderedDict()).setdefault(ev["unidad"], []).append(ev)
        n = sum(len(u) for u in pasos.values())
        if n == 0: return _rev("primer_evento", t, "no_evaluable", f"Ninguna fila trae la unidad ({sin_unidad} filas sin unidad).")
        malas, filas_mal, cats = 0, [], {}
        for unidades in pasos.values():
            for evs in unidades.values():
                primero, motivo = _primer_evento(evs, declaro)
                if primero is None:
                    malas += 1; filas_mal += [e["orden"] for e in evs]; c = _categoria(motivo); cats[c] = cats.get(c, 0) + 1
        ex = f"; {sin_unidad} filas sin unidad quedaron fuera" if sin_unidad else ""
        if not malas: return _rev("primer_evento", t, "cumple", f"Las {n} combinaciones de unidad y paso tienen un primer evento identificable{ex}.")
        porq = "; ".join(f"{k}: {v}" for k, v in sorted(cats.items(), key=lambda kv: -kv[1]))
        return _rev("primer_evento", t, "no_cumple", f"{_pct(malas, n)} de las combinaciones de unidad y paso no tienen un primer evento identificable{ex}. Motivos (conteo de unidades): {porq}. "
                    f"Filas involucradas: {_lista_filas(filas_mal)}.")

    @staticmethod
    def _lotes(hoja, filas, jk, minimo):
        t = "Capturas por lote"
        if jk is None: return _rev("lotes", t, "no_evaluable", "No elegiste la columna de fecha y hora de captura.")
        regs, sin_hora, excl = [], 0, 0
        for i in filas:
            e = _estado_texto(hoja.columnas[jk], i)
            if e == "sin_datos": continue
            f, con_hora = a_fechahora(hoja.columnas[jk].celdas[i]) if e == "valor" else (None, False)
            if f is None: excl += 1; continue
            if not con_hora: sin_hora += 1; continue
            regs.append((f, i))
        if not regs:
            return _rev("lotes", t, "no_evaluable", "La columna no trae hora de captura en ningún registro" + (f" ({sin_hora} registros solo con fecha)" if sin_hora else "")
                        + (f"; {excl} celdas vacías, N/A o inválidas" if excl else "") + ": sin hora no se pueden formar lotes.")
        g = OrderedDict()
        for f, i in regs: g.setdefault(f, []).append(i)
        lotes = [v for v in g.values() if len(v) >= minimo]; en_lote = sum(len(v) for v in lotes)
        ex = (f"; {sin_hora} registros sin hora y {excl} vacíos, N/A o inválidos quedaron fuera" if (sin_hora or excl) else "")
        if not lotes: return _rev("lotes", t, "cumple", f"Ninguna fecha y hora de captura reúne {minimo} o más registros ({len(regs)} registros con hora{ex}).")
        return _rev("lotes", t, "no_cumple", f"{len(lotes)} lotes de {minimo} o más registros con la misma fecha y hora de captura: {_pct(en_lote, len(regs))} de los registros con hora{ex}. "
                    f"Filas: {_lista_filas([i for v in lotes for i in v])}.")


@registrar
class Duracion(ModuloDialogo):
    ID, TITULO = "DURACION", "Duración entre dos fechas (lead time)"
    CAMPOS = [{"campo": "inicio", "etiqueta": "Columna de inicio", "tipo": "col"},
              {"campo": "fin", "etiqueta": "Columna de fin", "tipo": "col"},
              {"campo": "grafica", "etiqueta": "Mostrar el histograma de las duraciones", "tipo": "bool", "defecto": False}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        ji, jf = p.get("inicio"), p.get("fin")
        columna(hoja, ji, "el inicio"); columna(hoja, jf, "el fin")
        if ji == jf: raise ErrorEntrada("El inicio y el fin deben ser columnas distintas.")
        ci, cf = hoja.columnas[ji], hoja.columnas[jf]
        revisadas, sin_dato, na, invalidas, negativas, dur, con_hora = 0, 0, 0, [], [], [], False
        for i in _filas(hoja):
            ei, ef = _estado_texto(ci, i), _estado_texto(cf, i)
            if ei == "sin_datos" and ef == "sin_datos" and not (ci.celdas[i] or "").strip() and not (cf.celdas[i] or "").strip(): continue     # fila vacía en las dos
            revisadas += 1
            if "na" in (ei, ef): na += 1; continue
            if "sin_datos" in (ei, ef): sin_dato += 1; continue
            (a, ha), (b, hb) = a_fechahora(ci.celdas[i]), a_fechahora(cf.celdas[i])
            if a is None or b is None: invalidas.append(i); continue
            d = (b - a).total_seconds() / 86400
            if d < 0: negativas.append(i); continue
            dur.append(d); con_hora = con_hora or ha or hb
        if revisadas == 0: raise ErrorEntrada("Las dos columnas no tienen datos: no hay duraciones que calcular.")
        ni, nf = ci.nombre or f"C{ji + 1}", cf.nombre or f"C{jf + 1}"
        excl = [["Sin dato (vacío o «Sin datos»)", sin_dato, ""], ["No aplica (N/A)", na, ""],
                ["Fecha inválida", len(invalidas), _lista_filas(invalidas)], ["Duración negativa (fin anterior al inicio)", len(negativas), _lista_filas(negativas)]]
        notas = ("Duración = fin − inicio en días con fracción (una fecha sin hora es la medianoche de ese día); sin días hábiles ni feriados. Es el tiempo de entrega o lead time "
                 "de 02_DIAGNOSTICO. Se excluyen y se cuentan las celdas sin dato, N/A e inválidas y las duraciones negativas. Mediana: 15_GB_ESTADISTICA_Y_MUESTREO, EST-CENTRAL. "
                 "P90 no respaldado por el curso: se calcula con el método de percentil de D-MIKE que ya usan los cuartiles de Estadísticos (posición p(n+1) con interpolación lineal, como "
                 "Minitab; 17_GB BOX-PROCEDIMIENTO pide cuartiles pero no fija el método). No hay metas ni acuerdos de nivel de servicio: la comparación con una meta la defines tú.")
        if not dur:
            return resultado(cls.ID, f"Duración de {ni} a {nf}", p, [
                b_texto(f"No hay duraciones válidas: de {revisadas} filas revisadas, ninguna tiene las dos fechas válidas y en orden. No se calculan estadísticos.", "conclusion"),
                b_tabla("Filas excluidas", ["Motivo", "Filas", "Números de fila"], excl), b_texto("Notas: " + notas)], [], datos={"columnas": [ji, jf]})
        d = E.descriptivos(dur); p90 = E.cuartil(sorted(dur), 0.90)
        resumen = [["n (filas revisadas)", revisadas, ""], ["n válidas", len(dur), ""], ["Mínimo", num(d["minimo"], 4), "días"], ["Máximo", num(d["maximo"], 4), "días"],
                   ["Media", num(d["media"], 4), "días"], ["Mediana", num(d["mediana"], 4), "días · 15_GB EST-CENTRAL"], ["P90", num(p90, 4), "días · P90 no respaldado por el curso"]]
        avisos = []
        if len(dur) < 9: avisos.append(f"Hay {len(dur)} duraciones válidas: con menos de 9, el P90 de este método coincide con el máximo.")
        if not con_hora: avisos.append("Ninguna celda trae hora: las duraciones son de días completos.")
        concl = (f"Mediana de {num(d['mediana'], 4)} días con {len(dur)} duraciones válidas de {revisadas} filas revisadas. "
                 f"P90 = {num(p90, 4)} días (P90 no respaldado por el curso).")
        bloques = [b_texto(concl, "conclusion"), b_tabla("Resumen de la duración", ["Estadístico", "Valor", "Fuente o unidad"], resumen), b_tabla("Filas excluidas", ["Motivo", "Filas", "Números de fila"], excl)]
        png = None
        if p.get("grafica") and len(dur) >= 2 and d["desv"] > 0:
            bordes, _, w = clases_histograma(dur)
            fig, ax = figura(6.0, 3.6); ax.hist(dur, bins=bordes, color=CLARO, edgecolor=NARANJA)
            ax.axvline(d["mediana"], color=TINTA, lw=1.2); ax.set_xlabel("Días"); ax.set_ylabel("Frecuencia"); ax.set_title(f"Duración de {ni} a {nf} (línea: mediana)", fontsize=9)
            svg, png = a_svg_png(fig)
            bloques.insert(1, b_grafica(svg, {"g": "histograma", "titulo": f"Duración de {ni} a {nf} (días)", "x": [_f(v) for v in dur], "media": _f(d["media"]), "desv": _f(d["desv"]),
                                              "lie": None, "lse": None, "bordes": [_f(b) for b in bordes]}))
            avisos.append("La curva normal del histograma es solo una referencia visual: puedes quitarla en «Estilo y color».")
        bloques.append(b_texto("Notas: " + notas))
        return resultado(cls.ID, f"Duración de {ni} a {nf}", p, bloques, avisos, datos={"columnas": [ji, jf], "n": revisadas, "n_validas": len(dur)}, png=png)
