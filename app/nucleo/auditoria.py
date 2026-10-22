"""E3-8: auditoría de un diseño de experimentos (ESPEC_flujo_real_dmaic, Entrega 3: «revisar alias, aleatorización, restricciones, falta de ajuste y
confirmación»). Solo comprobaciones objetivas sobre lo que hay AHORA en el proyecto; no inventa umbrales (la significancia es la del propio análisis).
Cada revisión: id, titulo, estado («cumple», «no_cumple», «no_evaluable», «no_aplica» o «aviso»), detalle y fuente (de la base o «no respaldado»).
En un proyecto sin respuestas capturadas no se muestra ningún valor p (criterio 12): las revisiones que lo necesitan salen «no evaluable»."""
from . import disenos as DIS
from ..modulos import doe as D

F_ALIAS = ("26_BB_DOE_FRACCIONADOS: FRAC-CONSTRUCCION y FRAC-RESOLUCION respaldan la relación definidora y la resolución; el reparto de alias "
           "(efecto × cada palabra) es un cálculo general y no está respaldado por la base")
F_ALEATORIO = "No respaldado por la base: el curso no fija un criterio de aleatorización; es una comprobación de D-MIKE"
F_REGION = "Regla de D-MIKE (ESPEC_flujo, Entrega 3), no del curso: los límites seguros los declara el usuario"
F_CURVATURA = "28_BB_SUPERFICIES_RESPUESTA: RSM-PUNTOS-CENTRALES"
F_LOF = "27_BB_REGRESION: REG-FALTA-AJUSTE (28_BB RSM-PRUEBAS-2DO-ORDEN)"
F_CONFIRMACION = "ESPEC_flujo_real_dmaic, sección 3 y criterio 13; el plan se registra en E3-9"
CAUTELA = ("Una interacción confundida con otra no se interpreta como causal: el análisis no puede atribuir el efecto a una sola de las dos (cautela de ESPEC_flujo).")


def _rev(id_, titulo, estado, detalle, fuente): return {"id": id_, "titulo": titulo, "estado": estado, "detalle": detalle, "fuente": fuente}


def _alias(info):
    fr = info.get("fraccion")
    if info.get("tipo") != "frac" or not fr:
        return _rev("alias", "Alias (efectos confundidos)", "no_aplica", "No es un diseño fraccionado: no tiene relación definidora ni alias.", F_ALIAS)
    letras = D.LETRAS; nombres = [f["nombre"] for f in info["factores"]]; k = len(nombres)
    pal = fr["palabras"]; res = fr.get("resolucion")
    efectos = [letras[i] for i in range(k)] + [letras[i] + letras[j] for i in range(k) for j in range(i + 1, k)]
    filas = []
    for e in efectos:
        al = [a for a in D.alias(e, pal) if a != e]
        if al: filas.append(f"{e} = " + " = ".join(al))
    fact = ", ".join(f"{letras[i]} = {nombres[i]}" for i in range(k))
    det = (f"Relación definidora: I = {' = '.join(pal)}" + (f"; resolución {res}" if res else "") + f". Letras: {fact}. Términos confundidos: "
           + ("; ".join(filas) if filas else "ninguno entre efectos principales e interacciones dobles") + ". " + CAUTELA)
    return _rev("alias", "Alias (efectos confundidos)", "aviso" if filas else "cumple", det, F_ALIAS)


def _aleatorizacion(hoja, info):
    t = "Aleatorización del orden de corrida"
    if "aleatorizado" not in info:
        return _rev("aleatorizacion", t, "no_evaluable", "El diseño se creó antes de la 0.29 y no guardó si se aleatorizó: no se puede comprobar.", F_ALEATORIO)
    if not info["aleatorizado"]:
        return _rev("aleatorizacion", t, "no_cumple", "El diseño se creó sin aleatorizar: las corridas siguen el orden estándar. Sin aleatorización, una tendencia del proceso "
                    "(desgaste, temperatura ambiente) puede confundirse con un efecto.", F_ALEATORIO)
    cols = DIS.columnas(hoja, info)
    if cols["orden_est"] is None or cols["orden_corrida"] is None:
        return _rev("aleatorizacion", t, "no_evaluable", "Faltan en la hoja las columnas OrdenEst u OrdenCorrida: no se puede comparar el orden actual con el de creación.", F_ALEATORIO)
    pares = []
    for i in range(hoja.n):
        e, c = DIS._num(hoja, cols["orden_est"], i), DIS._num(hoja, cols["orden_corrida"], i)
        if e is not None and c is not None: pares.append((c, int(e)))
    actual = [e for _, e in sorted(pares)]; semilla = info.get("semilla")
    sem = f" (semilla {semilla})" if semilla is not None else " (sin semilla: el orden no se puede repetir)"
    if not info.get("orden_creacion"):
        return _rev("aleatorizacion", t, "no_evaluable", f"El diseño se aleatorizó{sem}, pero no guardó el orden con que se creó.", F_ALEATORIO)
    if actual == info["orden_creacion"]:
        return _rev("aleatorizacion", t, "cumple", f"El diseño se creó aleatorizado{sem} y el orden de corrida de la hoja es el de creación.", F_ALEATORIO)
    return _rev("aleatorizacion", t, "no_cumple", f"El diseño se creó aleatorizado{sem}, pero el orden de corrida de la hoja ya no es el de creación (se reordenó o se editó OrdenCorrida).", F_ALEATORIO)


def _restricciones(hoja, info, clave):
    t = "Restricciones (límites seguros)"
    if info.get("region") != "declarada" or not info.get("limites_seguros"):
        return _rev("restricciones", t, "no_evaluable", "La región autorizada no está declarada: no hay contra qué revisar los puntos. Decláralos en «Diseños del proyecto».", F_REGION)
    cols = DIS.columnas(hoja, info)
    if cols["orden_est"] is None or any(j is None for j in cols["factores"]):
        return _rev("restricciones", t, "no_evaluable", "Faltan en la hoja columnas del diseño (OrdenEst o factores): no se pueden revisar los puntos.", F_REGION)
    ls = info["limites_seguros"]
    try: lim = [(ls[f["nombre"]]["min"], ls[f["nombre"]]["max"]) for f in info["factores"]]
    except (KeyError, TypeError): return _rev("restricciones", t, "no_evaluable", "Los límites guardados no cubren todos los factores.", F_REGION)
    fuera = DIS.puntos_fuera_region(hoja, info, clave, lim)
    if not fuera: return _rev("restricciones", t, "cumple", "Todos los puntos que hay ahora en la hoja están dentro de los límites seguros (incluye las ediciones posteriores a la creación).", F_REGION)
    extra = f" (y {len(fuera) - 6} más)" if len(fuera) > 6 else ""
    return _rev("restricciones", t, "no_cumple", f"{len(fuera)} punto(s) fuera de los límites seguros: " + "; ".join(fuera[:6]) + extra + ". No los corras así.", F_REGION)


def _diagnostico(proyecto, info, n_resp):
    """Curvatura y falta de ajuste del último análisis guardado de la respuesta del diseño."""
    t1, t2 = "Curvatura", "Falta de ajuste"
    if n_resp == 0:
        d = "El diseño no tiene respuestas capturadas: no hay análisis que revisar."
        return [_rev("curvatura", t1, "no_evaluable", d, F_CURVATURA), _rev("falta_ajuste", t2, "no_evaluable", d, F_LOF)]
    diag = None
    for r in reversed(proyecto.resultados or []):
        dg = (r.get("datos") or {}).get("diagnostico")
        if dg and dg.get("respuesta") == info.get("respuesta"): diag = dict(dg, fecha=r.get("fecha"), titulo=r.get("titulo")); break
    if diag is None:
        d = "No hay un análisis (factorial o de superficie de respuesta) guardado para la respuesta de este diseño."
        return [_rev("curvatura", t1, "no_evaluable", d, F_CURVATURA), _rev("falta_ajuste", t2, "no_evaluable", d, F_LOF)]
    a = diag["alfa"]; de = f"«{diag['titulo']}» del {diag['fecha']}, nivel de significancia {a:g}"

    def una(id_, t, p, fuente, sin, ok, mal):
        if p is None: return _rev(id_, t, "no_evaluable", f"En el análisis {de}: {sin}", fuente)
        if p < a: return _rev(id_, t, "no_cumple", f"En el análisis {de}: {mal} (valor p = {p:.4f}).", fuente)
        return _rev(id_, t, "cumple", f"En el análisis {de}: {ok} (valor p = {p:.4f}).", fuente)
    return [una("curvatura", t1, diag.get("curvatura_p"), F_CURVATURA, "no se pudo probar la curvatura (hacen falta puntos centrales y puntos factoriales).",
                "la curvatura no es significativa", "la curvatura es significativa: un modelo de primer orden no basta"),
            una("falta_ajuste", t2, diag.get("lof_p"), F_LOF, "no se pudo probar la falta de ajuste (hacen falta réplicas o puntos centrales que den error puro).",
                "no se detecta falta de ajuste", "hay falta de ajuste: el modelo no describe bien la superficie")]


def _confirmacion(proyecto, info):
    return _rev("confirmacion", "Confirmación", "aviso", "No hay plan de confirmación registrado.", F_CONFIRMACION)


def auditar(proyecto, hoja, design_id):
    """(auditoría, None) o (None, motivo). La auditoría trae design_id, versión, cuántas respuestas hay y la lista de revisiones."""
    for clave, info in (proyecto.formatos.get("_disenos") or {}).items():
        ident = DIS.identidad(info, clave)
        if ident["design_id"] != design_id: continue
        n_resp, _ = DIS.estado_respuestas(hoja, info)
        rev = [_alias(info), _aleatorizacion(hoja, info), _restricciones(hoja, info, clave)] + _diagnostico(proyecto, info, n_resp) + [_confirmacion(proyecto, info)]
        cuenta = {e: sum(1 for r in rev if r["estado"] == e) for e in ("cumple", "no_cumple", "no_evaluable", "no_aplica", "aviso")}
        return {"design_id": design_id, "version_diseno": ident["version_diseno"], "respuestas": n_resp, "revisiones": rev, "resumen": cuenta}, None
    return None, f"No existe el diseño {design_id}."
