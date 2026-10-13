"""Hoja de verificación: exporta un análisis a Excel con las fórmulas equivalentes de Excel (vivas, sobre los mismos datos) junto a
los valores de D-MIKE y una columna vacía para que captures lo que dé Minitab. Calcula las diferencias y marca «Coincide» o «Revisar».
Cubre: ESTADISTICOS, CORREL (primeros dos), REGRESION (lineal simple), CAPACIDAD y DISTRIB."""
import math
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import CellIsRule
from . import estadistica as E, capacidad as C, spc as S
from .exportar import T_TITULO, T_CAB, T_NORMAL, T_NOTA, RELLENO, FUENTE
from .base import columna

SOPORTADOS = ("ESTADISTICOS", "CORREL", "REGRESION", "CAPACIDAD", "DISTRIB")
RUTA_MINITAB = {
    "ESTADISTICOS": "Estadísticas > Estadísticas básicas > Mostrar estadísticas descriptivas (Stat > Basic Statistics > Display Descriptive Statistics)",
    "CORREL": "Estadísticas > Estadísticas básicas > Correlación (Stat > Basic Statistics > Correlation)",
    "REGRESION": "Estadísticas > Regresión > Regresión > Ajustar modelo de regresión (Stat > Regression > Regression > Fit Regression Model)",
    "CAPACIDAD": "Estadísticas > Herramientas de calidad > Análisis de capacidad > Normal (Stat > Quality Tools > Capability Analysis > Normal)",
    "DISTRIB": "Estadísticas > Herramientas de calidad > Prueba de normalidad de Anderson-Darling (Stat > Basic Statistics > Normality Test)"}


def _datos(hoja, nombres):
    """Columnas completas por nombre; solo filas donde todas son numéricas válidas (y visibles según el filtro)."""
    idx = []
    for n in nombres:
        j = hoja.indice(n)
        if j is None: raise ValueError(f"La columna «{n}» ya no existe en la hoja.")
        columna(hoja, j, n, "num"); idx.append(j)
    act = hoja.filas_activas(); filas = []
    for i in range(hoja.n):
        if act is not None and i not in act: continue
        v = [hoja.columnas[j].valor(i) for j in idx]
        if all(t[1] and t[2] is not None for t in v): filas.append([t[2] for t in v])
    return filas


def construir(ruta, res, hoja, proyecto):
    d = res["definicion"]; mid = d["analisis"]; col = d["columnas"]; par = d["parametros"]
    if mid not in SOPORTADOS: raise ValueError("Este análisis todavía no tiene hoja de verificación en Excel (disponible para: " + ", ".join(SOPORTADOS) + ").")
    if mid == "CORREL": nombres = col["vars"][:2]
    elif mid == "REGRESION":
        if len(col["xs"]) != 1 or int(par.get("grado") or 1) != 1: raise ValueError("La verificación en Excel cubre la regresión lineal simple (un predictor, grado 1).")
        nombres = [col["xs"][0], col["y"]]
    else: nombres = [col["y"]]
    filas = _datos(hoja, nombres); n = len(filas)
    if n < 3: raise ValueError("Hay muy pocos datos para verificar.")
    wb = Workbook(); wd = wb.active; wd.title = "Datos"
    from ..nucleo import modo as MD
    if MD.etiqueta(proyecto):                 # E1-R7: la hoja «Datos» queda limpia; la marca va en su propia hoja y en las propiedades
        wb.create_sheet("AVISO").cell(1, 1, MD.ETIQUETA).font = Font(name=FUENTE, bold=True, color="B3261E"); wb.properties.subject = MD.ETIQUETA
    for k, nom in enumerate(nombres, 1):
        wd.cell(1, k, nom).font = Font(name=FUENTE, bold=True)
        for i, f in enumerate(filas, 2): wd.cell(i, k, f[k - 1])
    L = lambda k: f"Datos!${chr(64 + k)}$2:${chr(64 + k)}${n + 1}"
    items = []     # (concepto, valor D-MIKE, fórmula Excel)
    x = [f[0] for f in filas]
    if mid in ("ESTADISTICOS", "DISTRIB", "CAPACIDAD"):
        dsc = E.descriptivos(x)
        items = [("N", n, f"=COUNT({L(1)})"), ("Media", dsc["media"], f"=AVERAGE({L(1)})"), ("Desviación estándar (n-1)", dsc["desv"], f"=STDEV({L(1)})"),
                 ("Varianza", dsc["varianza"], f"=VAR({L(1)})"), ("Mínimo", dsc["minimo"], f"=MIN({L(1)})"), ("Mediana", dsc["mediana"], f"=MEDIAN({L(1)})"),
                 ("Máximo", dsc["maximo"], f"=MAX({L(1)})"), ("Q1 (método n+1)", dsc["q1"], f"=_xlfn.QUARTILE.EXC({L(1)},1)"),
                 ("Q3 (método n+1)", dsc["q3"], f"=_xlfn.QUARTILE.EXC({L(1)},3)")]
        if n > 3: items += [("Asimetría", dsc["asimetria"], f"=SKEW({L(1)})"), ("Curtosis (exceso)", dsc["curtosis"], f"=KURT({L(1)})")]
        if mid == "DISTRIB":
            ad = E.anderson_darling(x); items += [("Anderson-Darling A²", ad["a2"], None), ("Valor p de Anderson-Darling", ad["p"], None)]
        if mid == "CAPACIDAD":
            lie = float(par["lie"]) if par.get("lie") not in (None, "") else None; lse = float(par["lse"]) if par.get("lse") not in (None, "") else None
            tam = int(float(par.get("tam") or 1))
            wd.cell(1, 2, "Rango móvil").font = Font(name=FUENTE, bold=True)
            for i in range(3, n + 2): wd.cell(i, 2, f"=ABS(A{i}-A{i - 1})")
            s_in = S.carta_imr(x)[1]["mr_barra"] / S.D2[2]
            r = C.indices(dsc["media"], s_in, dsc["desv"], lie, lse)
            wb.create_sheet("Parámetros").append(["LIE", lie]); ws = wb["Parámetros"]; ws.append(["LSE", lse]); ws.append(["Desviación estándar global", f"=STDEV({L(1)})"])
            ws.append(["Sigma interna (R̄ móvil / 1.128)", f"=AVERAGE(Datos!$B$3:$B${n + 1})/1.128"])
            fl, fu, sg, si = "Parámetros!$B$1", "Parámetros!$B$2", "Parámetros!$B$3", "Parámetros!$B$4"
            mu = f"AVERAGE({L(1)})"
            if lie is not None and lse is not None:
                items += [("Pp", r["Pp"], f"=({fu}-{fl})/(6*{sg})")]
            if lse is not None: items += [("PPU", r["Ppu"], f"=({fu}-{mu})/(3*{sg})")]
            if lie is not None: items += [("PPL", r["Ppl"], f"=({mu}-{fl})/(3*{sg})")]
            items += [("Ppk", r["Ppk"], "=MIN(" + ",".join(f"({fu}-{mu})/(3*{sg})" if k == "u" else f"({mu}-{fl})/(3*{sg})" for k, v in (("u", lse), ("l", lie)) if v is not None) + ")")]
            if tam == 1:
                if lie is not None and lse is not None: items += [("Cp (sigma por rango móvil)", r["Cp"], f"=({fu}-{fl})/(6*{si})")]
                items += [("Cpk (sigma por rango móvil)", r["Cpk"], "=MIN(" + ",".join(f"({fu}-{mu})/(3*{si})" if k == "u" else f"({mu}-{fl})/(3*{si})" for k, v in (("u", lse), ("l", lie)) if v is not None) + ")")]
            else:
                items.append(("Cp y Cpk con subgrupos", None, None))
    elif mid == "CORREL":
        from .regresion import pearson
        y = [f[1] for f in filas]; r = pearson(x, y)
        items = [("N", n, f"=COUNT({L(1)})"), ("r de Pearson", r["r"], f"=CORREL({L(1)},{L(2)})"), ("R²", r["r"] ** 2, f"=RSQ({L(2)},{L(1)})"),
                 ("Estadístico t", r["estadistico"] if r["prueba"] == "t" else None, f"=CORREL({L(1)},{L(2)})*SQRT(({n}-2)/(1-CORREL({L(1)},{L(2)})^2))"),
                 ("Valor p (t, 2 colas)", r["p"] if r["prueba"] == "t" else None, f"=TDIST(ABS(CORREL({L(1)},{L(2)})*SQRT(({n}-2)/(1-CORREL({L(1)},{L(2)})^2))),{n}-2,2)")]
    else:
        from . import regresion as R
        y = [f[1] for f in filas]; m = R.ajustar([[v] for v in x], y, ["x"])
        items = [("N", n, f"=COUNT({L(1)})"), ("Constante (b0)", m["coef"][0]["coef"], f"=INTERCEPT({L(2)},{L(1)})"), ("Pendiente (b1)", m["coef"][1]["coef"], f"=SLOPE({L(2)},{L(1)})"),
                 ("EE de la pendiente", m["coef"][1]["ee"], f"=INDEX(LINEST({L(2)},{L(1)},TRUE,TRUE),2,1)"),
                 ("t de la pendiente", m["coef"][1]["t"], f"=SLOPE({L(2)},{L(1)})/INDEX(LINEST({L(2)},{L(1)},TRUE,TRUE),2,1)"),
                 ("Valor p de la pendiente", m["coef"][1]["p"], f"=TDIST(ABS(SLOPE({L(2)},{L(1)})/INDEX(LINEST({L(2)},{L(1)},TRUE,TRUE),2,1)),{n}-2,2)"),
                 ("R²", m["r2"], f"=RSQ({L(2)},{L(1)})"), ("R² ajustado", m["r2_aj"], f"=1-(1-RSQ({L(2)},{L(1)}))*({n}-1)/({n}-2)"),
                 ("S (error estándar de la estimación)", m["s"], f"=STEYX({L(2)},{L(1)})"), ("F", m["f"], f"=RSQ({L(2)},{L(1)})/(1-RSQ({L(2)},{L(1)}))*({n}-2)"),
                 ("Valor p de F", m["p_f"], f"=FDIST(RSQ({L(2)},{L(1)})/(1-RSQ({L(2)},{L(1)}))*({n}-2),1,{n}-2)")]
    ws = wb.create_sheet("Verificación", 0)
    ws["A1"] = f"Verificación de {res['titulo']}"; ws["A1"].font = T_TITULO
    ws["A2"] = "Ruta en Minitab: " + RUTA_MINITAB[mid]; ws["A2"].font = T_NOTA
    ws["A3"] = "Captura en la columna D lo que da Minitab. Tolerancia relativa para «Coincide»:"; ws["A3"].font = T_NOTA; ws["F3"] = 0.0001; ws["F3"].font = Font(name=FUENTE, bold=True)
    for j, h in enumerate(["Concepto", "D-MIKE", "Excel (fórmula)", "Minitab (captúralo)", "Dif. D-MIKE - Excel", "Dif. D-MIKE - Minitab", "Resultado"], 1):
        c = ws.cell(5, j, h); c.font = T_CAB; c.fill = RELLENO; c.alignment = Alignment(wrap_text=True, vertical="center")
    for r_, (nom, v, f) in enumerate(items, 6):
        ws.cell(r_, 1, nom).font = T_NORMAL
        if v is not None and not (isinstance(v, float) and math.isnan(v)): ws.cell(r_, 2, float(v))
        if f: ws.cell(r_, 3, f)
        ws.cell(r_, 4).fill = PatternFill("solid", fgColor="FFF4D6")
        ws.cell(r_, 5, f'=IF(OR(B{r_}="",C{r_}=""),"",B{r_}-C{r_})'); ws.cell(r_, 6, f'=IF(OR(B{r_}="",D{r_}=""),"",B{r_}-D{r_})')
        ok = lambda c: f'IF({c}{r_}="",TRUE,ABS({c}{r_})<=$F$3*MAX(1,ABS(B{r_})))'
        ws.cell(r_, 7, f'=IF(AND(E{r_}="",F{r_}=""),"sin comparar",IF(AND({ok("E")},{ok("F")}),"Coincide","Revisar"))')
        for j in (2, 3, 4, 5, 6): ws.cell(r_, j).number_format = "0.000000"
    ult = 5 + len(items)
    ws.conditional_formatting.add(f"G6:G{ult}", CellIsRule(operator="equal", formula=['"Coincide"'], fill=PatternFill("solid", bgColor="E3F1E0")))
    ws.conditional_formatting.add(f"G6:G{ult}", CellIsRule(operator="equal", formula=['"Revisar"'], fill=PatternFill("solid", bgColor="FDECEA")))
    for j, w in enumerate((38, 16, 18, 20, 20, 22, 14), 1): ws.column_dimensions[chr(64 + j)].width = w
    ws.cell(ult + 2, 1, "Si «Revisar» aparece en la comparación con Excel, revisa el método (por ejemplo, Excel usa n-1 en STDEV y el método n+1 en QUARTILE.EXC). "
                        "Si aparece contra Minitab, revisa opciones del análisis (método de sigma, alfa, tipo de cuartil) y anótalo en la bitácora.").font = T_NOTA
    wb.save(ruta)
    return len(items), n
