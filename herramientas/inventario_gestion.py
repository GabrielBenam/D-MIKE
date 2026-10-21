"""Inventario del grupo «Gestión» de la cinta (A5): qué está construido y qué es solo una entrada de menú.

Uso: python herramientas/inventario_gestion.py            (imprime la tabla)
     python herramientas/inventario_gestion.py --escribir  (actualiza proyecto/INVENTARIO_GESTION.md)
Cada entrada del menú «Gestión» se revisa contra el código: módulo registrado, formato con cabecera y tablas, cálculo propio
(calcular distinto del base, que solo guarda texto), pruebas que lo nombran y fuente citada en su nota.
"""
import re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


# Lectura manual del método calcular() de cada formato (21/10/2026). El código solo distingue «calcular propio» del base; esta tabla
# dice qué hace ese cálculo. Si cambia un formato, actualiza su fila (la prueba de sincronía avisa si el .md se desfasa).
TIPO = {
    "CHARTER": "Cálculo: ahorro total con su base; validación de campos obligatorios",
    "JUSTIFICACION": "Cálculo: VPN, TIR, recuperación, ROI del PMBOK y B/C (pendientes si hay periodos vacíos)",
    "ENFOQUE": "Cálculo: promedio de variables y sugerencia de enfoque, con gráfica",
    "INTERESADOS": "Cálculo: prominencia y brecha de compromiso, con cuadrícula poder/interés",
    "RACI": "Validación de reglas (una sola A, falta R, carga por persona); sin cálculo numérico",
    "EDT": "Cálculo: niveles, regla del 100 %, paquetes de trabajo, con dibujo",
    "CRONOGRAMA": "Cálculo: ruta crítica, holguras, tres puntos, desvío contra línea base",
    "RIESGOS": "Cálculo: P×I con zonas, VME y reserva de contingencia, con matriz",
    "MONTECARLO": "Cálculo: simulación con semilla (P50/P80/P90, criticidad, tornado)",
    "ARBOL-DECISION": "Cálculo: valor monetario esperado de las ramas, con dibujo",
    "FODA": "Validación y gráfica: cruza amenazas contra el registro de riesgos; sin cálculo numérico",
    "AFINIDAD": "Organización y gráfica: agrupa ideas; sin cálculo numérico",
    "BITACORA": "Cálculo simple: días abiertos y vencidos; validación de campos",
    "VALOR-GANADO": "Cálculo: SV, CV, SPI, CPI, ETC, EAC, VAC, TCPI y curva S",
    "COSTO-CALIDAD": "Cálculo: totales por categoría, antes y después, y su proporción de ventas",
    "CHECKLIST-FASE": "Validación de reglas de la compuerta y conteo de cumplidos; sin cálculo numérico",
    "LECCIONES": "Cálculo simple: objetivos cumplidos contra meta; validación de campos",
}


def inventario():
    from app.nucleo.menus import MENUS
    from app.nucleo.catalogo import CONSTRUIDOS
    from app.modulos import cargar
    from app.modulos.formatos import Formato
    reg = cargar()
    textos_pruebas = {p.name: p.read_text(encoding="utf-8") for p in (RAIZ / "pruebas").glob("test_*.py")}
    filas, grupo = [], ""
    gestion = next(ops for t, ops in MENUS if t == "Gestión")
    for texto, accion in gestion:
        if accion is None: grupo = texto.lstrip("§"); continue
        mid = accion.split(":", 1)[1] if accion.startswith("mod:") else None
        cls = reg.get(mid) if mid else None
        if cls is None:
            filas.append({"grupo": grupo, "entrada": texto, "id": mid or accion, "estado": "Solo entrada de menú", "detalle": "no hay módulo registrado con ese id",
                          "calculo": "—", "pruebas": [], "fuente": "", "tipo": "—"})
            continue
        es_formato = issubclass(cls, Formato)
        calcula = es_formato and cls.calcular.__func__ is not Formato.calcular.__func__
        pruebas = sorted(n for n, t in textos_pruebas.items() if re.search(rf'["\']{re.escape(mid)}["\']', t))
        nota = getattr(cls, "NOTA", "") or ""
        fuentes = sorted(set(re.findall(r"PMBOK ?\d?[^.;,)]{0,18}|PL\d\d|\d\d_[A-Z]{2}_[A-Z_]+", nota)))[:4]
        estado = ("Construido, con cálculo" if calcula else "Construido, solo captura") if es_formato else "Construido (módulo de análisis)"
        if mid not in CONSTRUIDOS: estado += " [no figura en el catálogo de construidos]"
        det = (f"{len(cls.CABECERA)} campos de cabecera, {len(cls.TABLAS)} tablas" if es_formato else "diálogo sobre la hoja")
        filas.append({"grupo": grupo, "entrada": texto, "id": mid, "estado": estado, "detalle": det,
                      "calculo": "sí" if calcula else "no", "pruebas": pruebas, "fuente": "; ".join(fuentes), "tipo": TIPO.get(mid, "sin clasificar")})
    return filas


def como_markdown(filas):
    n = len(filas); sin = [f for f in filas if f["estado"].startswith("Solo")]
    solo_captura = [f for f in filas if "solo captura" in f["estado"]]
    s = ["# Inventario del grupo «Gestión» de la cinta", "",
         "Generado con `python herramientas/inventario_gestion.py --escribir`. Cada entrada se revisa contra el código.", "",
         f"Entradas: {n}. Solo entrada de menú: {len(sin)}. Construidas con cálculo propio: {sum(f['calculo'] == 'sí' for f in filas)}. "
         f"Construidas solo con captura (guardan y exportan texto, sin cálculo): {len(solo_captura)}. "
         f"Sin cálculo numérico (solo reglas de validación u organización): {sum('sin cálculo numérico' in f['tipo'] for f in filas)}.", "",
         "Nota: «con cálculo propio» significa que el formato define su propio método calcular(); la columna «Qué hace» dice si ese método calcula números "
         "o solo valida reglas. Las pruebas que solo nombran el formato dentro de `test_formatos_v010.py` verifican que se llene, guarde y exporte, no sus cifras.", "",
         "| Grupo | Entrada | Id | Estado | Qué hace | Detalle | Pruebas que lo nombran | Fuente citada en su nota |", "|---|---|---|---|---|---|---|---|"]
    for f in filas:
        s.append(f"| {f['grupo']} | {f['entrada']} | {f['id']} | {f['estado']} | {f['tipo']} | {f['detalle']} | {', '.join(f['pruebas']) or 'ninguna'} | {f['fuente'] or '—'} |")
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    f = inventario(); md = como_markdown(f)
    if "--escribir" in sys.argv: (RAIZ / "proyecto" / "INVENTARIO_GESTION.md").write_text(md, encoding="utf-8"); print("escrito")
    else: print(md)
