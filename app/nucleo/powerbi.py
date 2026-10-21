"""Exportación para Power BI: una carpeta con tablas CSV limpias (un tema por archivo, formato largo donde hay
series), el tema visual de D-MIKE y una guía de importación.

Diseño (decidido en v0.10): D-MIKE no usa Power BI como base de datos; escribe tablas planas que Power BI lee con
«Obtener datos > Carpeta» o «Texto/CSV». Separación datos / definición de indicadores / presentación:
  dim_indicador (definición), hecho_indicador (valores por semana), tema_dmike.json (presentación).
La generación por código del modelo (TMDL) y del informe (PBIR) y la publicación por API quedan como pendiente:
no se pueden verificar sin Power BI. Todo lo de Power BI es [GENERAL], no viene de la base LSS.
"""
import csv, json, os
from datetime import timedelta

from .tokens import tema_power_bi
from . import archivo


def _escribir(ruta, cabeza, filas):
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(cabeza)
        for fila in filas: w.writerow(["" if v is None else v for v in fila])


def _n(v):
    """Número con punto decimal y sin separador de miles (Power BI lo lee como número en cualquier región si se
    indica la configuración regional en inglés al importar; ver LEEME)."""
    if v is None or v == "": return ""
    if isinstance(v, float): return repr(v) if not v.is_integer() else str(int(v))    # A4: sin redondeo
    return v


def exportar(carpeta, api):
    from ..modulos.formatos import FORMATOS
    from ..nucleo.hoja import a_numero
    proy, hoja = api.proyecto, api.hoja
    nombre = (proy.fijos["nombre_proyecto"]["valor"] or "proyecto").strip()
    seguro = "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in nombre).strip() or "proyecto"
    destino = os.path.join(carpeta, f"D-MIKE_PowerBI_{seguro}")
    os.makedirs(destino, exist_ok=True)
    escritos = []

    from . import modo as MD
    marca = MD.etiqueta(proy)

    def tabla(archivo_csv, cabeza, filas):
        if marca: cabeza, filas = list(cabeza) + ["marca"], [list(f) + [marca] for f in filas]       # E1-R7: solo proyectos de demostración
        _escribir(os.path.join(destino, archivo_csv), cabeza, filas); escritos.append((archivo_csv, len(filas)))

    fijos = {k: v["valor"] for k, v in proy.fijos.items()}
    emp = (proy.perfil or {}).get("perfil_empresa", {}) if proy.perfil else {}
    tabla("dim_proyecto.csv", ["proyecto", "cliente_area", "responsable", "version_perfil", "fase_actual", "tamano", "giro"],
          [[fijos.get("nombre_proyecto"), fijos.get("cliente_area"), fijos.get("responsable"), proy.version or "",
            proy.fase_actual() or "", emp.get("tamano"), emp.get("giro")]])

    # avance por fase y módulo
    filas = []
    for mid, m in proy.modulos.items():
        filas.append([m["fase"], mid, api.catalogo.modulos.get(mid, {}).get("nombre", mid), m.get("prioridad") or "", m["avance"]])
    tabla("avance_modulos.csv", ["fase", "modulo_id", "modulo", "prioridad", "avance"], filas)

    # hoja de datos (limpia, como para Minitab, con fechas ISO)
    cols, _, _ = archivo.tabla_limpia(hoja)
    if cols:
        filas = []
        for i in range(hoja.n):
            if all(c["valores"][i] is None for c in cols): continue
            filas.append([i + 1] + [(c["valores"][i].isoformat() if c["tipo"] == "fecha" and c["valores"][i] is not None
                                     else _n(c["valores"][i])) for c in cols])
        tabla("datos_hoja.csv", ["fila"] + [c["nombre"] for c in cols], filas)

    # tablero: definición de indicadores y hechos por semana (formato largo)
    if "TABLERO" in proy.formatos:
        T = FORMATOS["TABLERO"]; d = T.normalizar(proy.formatos["TABLERO"])
        ns, inicio, series, _ = T.series(d, hoja)
        dim, hechos, defs = [], [], []
        from ..modulos.formatos import estado_kpi
        from . import indicadores as IND
        for i, (f, sr) in enumerate(zip(d["tablas"]["kpi"], series), 1):
            if sr is None: continue
            kid = f.get("kpi_id") or f"KPI{i}"
            revs = IND.revisiones(proy, kid); por_sem = IND.revision_por_semana(revs, inicio, ns)
            dim.append([kid, f.get("indicador"), f.get("categoria"), f.get("unidad"), "menor_mejor" if sr["sentido"] == "<=" else "mayor_mejor",
                        _n(sr["meta"]), _n(sr["adv"]), (f.get("tarjeta") or "Sí") == "Sí", "hoja" if sr["desde_hoja"] else "manual",
                        revs[-1]["revision"] if revs else ""])
            for r in revs:
                defs.append([kid, r["revision"], r["nombre"], r["numerador"], r["denominador"], r["unidad_conteo"], r["poblacion"],
                             r["evento_inicio"], r["evento_fin"], r["vigencia"], r.get("motivo", "")])
            for s in range(1, ns + 1):
                v = sr["vals"][s]
                b = sr["bases"].get(s)
                if v is None: continue
                hechos.append([kid, s, (inicio + timedelta(days=7 * (s - 1))).isoformat() if inicio else "", _n(v), _n(sr["meta"]),
                               estado_kpi(v, sr["meta"], sr["sentido"], sr["adv"]) or "", por_sem[s - 1] or "",
                               _n(b[0]) if b else "", _n(b[1]) if b and b[1] is not None else ""])
        tabla("dim_indicador.csv", ["indicador_id", "indicador", "categoria", "unidad", "sentido", "meta", "limite_advertencia",
                                    "en_resumen", "origen", "revision_vigente"], dim)
        tabla("definicion_indicador.csv", ["indicador_id", "revision", "nombre", "numerador", "denominador", "unidad_conteo", "poblacion",
                                           "evento_inicio", "evento_fin", "vigencia", "motivo"], defs)
        tabla("hecho_indicador.csv", ["indicador_id", "semana", "inicio_semana", "valor", "meta", "estado", "revision",
                                      "base_numerador", "base_denominador"], hechos)
        wip = [[f.get("unidad"), f.get("estado"), f.get("responsable")] for f in d["tablas"]["wip"] if any(f.values())]
        tabla("trabajos_en_proceso.csv", ["unidad", "estado", "responsable"], wip)

    # formatos con tablas: AMEF, plan de control, OEE (una fila por registro, con columnas calculadas)
    for fid, archivo_csv in (("AMEF", "amef.csv"), ("PLAN-CONTROL", "plan_control.csv"), ("OEE", "oee.csv")):
        if fid not in proy.formatos: continue
        F = FORMATOS[fid]; d = F.normalizar(proy.formatos[fid]); calc = F.calcular(d, hoja, proy)
        t = F.TABLAS[0]; cols_t = [c for c in t["columnas"] if not c.get("oculto")]
        filas = []
        for i, f in enumerate(d["tablas"][t["id"]]):
            cc = calc["calc"].get(t["id"], [{}] * (i + 1))[i] if i < len(calc["calc"].get(t["id"], [])) else {}
            if not any(f.values()): continue
            exacto = {}
            if fid == "OEE":          # fracciones exactas (la vista muestra porcentajes redondeados)
                from ..modulos import lean
                v = [a_numero(f.get(k) or "") for k in ("total", "paro", "muerto", "capacidad", "produccion", "rechazo")]
                if None not in (v[0], v[3], v[4]):
                    try: exacto = lean.oee(v[0], v[1] or 0, v[2] or 0, v[3], v[4], v[5] or 0)
                    except ValueError: exacto = {}
            fila = []
            for c in cols_t:
                if c["campo"] in exacto: fila.append(_n(exacto[c["campo"]])); continue
                v = cc.get(c["campo"], "") if c.get("calc") else f.get(c["campo"], "")
                if isinstance(v, str) and v.endswith("%"): v = _n(float(v[:-1]) / 100)
                elif isinstance(v, str) and c.get("tipo") in ("numero", "entero"):
                    x = a_numero(v); v = _n(x) if x is not None else v
                fila.append(v)
            filas.append(fila)
        tabla(archivo_csv, [c["campo"] for c in cols_t], filas)

    # índice de resultados de módulos (título, módulo y fecha; las gráficas se exportan desde cada resultado)
    tabla("resultados.csv", ["resultado_id", "modulo", "titulo", "fecha"],
          [[r["uid"], r["modulo"], r["titulo"], r["fecha"]] for r in proy.resultados])

    with open(os.path.join(destino, "tema_dmike.json"), "w", encoding="utf-8") as f:
        json.dump(tema_power_bi(), f, ensure_ascii=False, indent=2)
    with open(os.path.join(destino, "LEEME.txt"), "w", encoding="utf-8-sig") as f:
        if marca: f.write(f"{marca}\nLos datos de este proyecto son sintéticos: cada tabla trae la columna «marca».\n\n")
        f.write(LEEME.format(proyecto=nombre, archivos="\n".join(f"  {a}: {n} filas" for a, n in escritos)))
    return destino, escritos


LEEME = """D-MIKE: datos para Power BI
Proyecto: {proyecto}

Archivos:
{archivos}
  tema_dmike.json: colores y tipografía de D-MIKE para el informe

Cómo usarlos en Power BI Desktop
1. Inicio > Obtener datos > Texto/CSV, y elige un archivo (o Obtener datos > Más... > Carpeta para traer todos).
2. En la vista previa, en «Origen del archivo» deja 65001: Unicode (UTF-8) y en «Delimitador» Coma.
3. Si tu Windows usa coma decimal, presiona «Transformar datos» y en cada columna numérica usa
   Cambiar tipo > Usar configuración regional > Número decimal, Inglés (Estados Unidos).
4. Relaciones sugeridas (Modelado > Administrar relaciones):
   hecho_indicador[indicador_id] -> dim_indicador[indicador_id] (muchos a uno);
   definicion_indicador[indicador_id] -> dim_indicador[indicador_id] (muchos a uno). Cada valor semanal trae la revisión de la
   definición que regía esa semana y, en los porcentajes, su base (base_numerador, base_denominador).
5. Tema: Vista > Temas > Examinar temas, y elige tema_dmike.json.

Las columnas de porcentaje vienen como fracción (0.85 = 85%): dales formato de porcentaje en Power BI.
Vuelve a exportar desde D-MIKE y usa Inicio > Actualizar para traer los datos nuevos.
"""
