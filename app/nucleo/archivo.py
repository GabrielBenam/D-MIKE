"""Archivo de proyecto .dmike (SQLite) y exportación de datos limpios para Minitab.

.dmike: tablas meta, columnas, celdas y proyecto. Se escribe en un archivo temporal y luego se reemplaza,
para que un corte de luz no deje el proyecto a medias.

Exportación (decisiones de este incremento, ver ESTADO):
- .xlsx: una hoja "Datos"; números como número, fechas como fecha de Excel con formato DD/MM/AAAA.
- .csv: UTF-8 con BOM, separador coma, punto decimal, fechas AAAA-MM-DD (no depende de la configuración regional).
- Celdas que no corresponden al tipo de su columna: se exportan vacías (dato faltante).
- Nombres de columna: reglas de Minitab (máximo 31 caracteres, sin ' ni #, sin * al inicio, sin espacios
  al inicio o al final). NO RESPALDADO POR LOS DOCUMENTOS: conocimiento general de Minitab.
"""
import csv, json, os, sqlite3, tempfile
from datetime import datetime

FORMATO, VERSION_FORMATO = "dmike", 1
MAX_NOMBRE = 31


class ArchivoInvalido(Exception):
    pass


# ---------------- .dmike ----------------
def guardar(ruta, hoja, proyecto, version_programa):
    carpeta = os.path.dirname(os.path.abspath(ruta))
    fd, tmp = tempfile.mkstemp(suffix=".dmike", dir=carpeta); os.close(fd)
    try:
        con = sqlite3.connect(tmp)
        with con:
            con.executescript("""
                CREATE TABLE meta (clave TEXT PRIMARY KEY, valor TEXT);
                CREATE TABLE columnas (orden INTEGER PRIMARY KEY, nombre TEXT, tipo TEXT, rol TEXT, descr TEXT);
                CREATE TABLE celdas (col INTEGER, fila INTEGER, texto TEXT, PRIMARY KEY (col, fila));
                CREATE TABLE proyecto (clave TEXT PRIMARY KEY, json TEXT);""")
            con.executemany("INSERT INTO meta VALUES (?, ?)", [
                ("formato", FORMATO), ("version_formato", str(VERSION_FORMATO)), ("programa", version_programa),
                ("guardado_en", datetime.now().isoformat(timespec="seconds")), ("filas", str(hoja.n))])
            for j, c in enumerate(hoja.columnas):
                con.execute("INSERT INTO columnas VALUES (?, ?, ?, ?, ?)", (j, c.nombre, c.tipo, c.rol, c.desc))
                con.executemany("INSERT INTO celdas VALUES (?, ?, ?)",
                                [(j, i, t) for i, t in enumerate(c.celdas) if t is not None])
            con.execute("INSERT INTO proyecto VALUES ('estado', ?)", (json.dumps(proyecto.a_dict(), ensure_ascii=False),))
        con.close()
        os.replace(tmp, ruta)
    except Exception:
        if os.path.exists(tmp): os.remove(tmp)
        raise


def abrir(ruta):
    """Devuelve (hoja_dict, proyecto_dict). No modifica nada del programa; lanza ArchivoInvalido."""
    if not os.path.isfile(ruta): raise ArchivoInvalido("el archivo no existe")
    try:
        # URI con ruta codificada: funciona con letras de unidad, espacios, acentos o # en la ruta de Windows
        from pathlib import Path
        con = sqlite3.connect(Path(ruta).resolve().as_uri() + "?mode=ro", uri=True)
        meta = dict(con.execute("SELECT clave, valor FROM meta"))
        if meta.get("formato") != FORMATO: raise ArchivoInvalido("no es un proyecto de D-MIKE")
        if int(meta.get("version_formato", 0)) > VERSION_FORMATO:
            raise ArchivoInvalido("fue guardado con una versión más nueva de D-MIKE")
        n = int(meta["filas"])
        cols = [{"nombre": r[1] or "", "tipo": r[2], "rol": r[3], "desc": r[4] or "", "celdas": [None] * n}
                for r in con.execute("SELECT orden, nombre, tipo, rol, descr FROM columnas ORDER BY orden")]
        for j, i, t in con.execute("SELECT col, fila, texto FROM celdas"):
            cols[j]["celdas"][i] = t
        (pj,) = con.execute("SELECT json FROM proyecto WHERE clave = 'estado'").fetchone()
        con.close()
        return {"n": n, "columnas": cols}, json.loads(pj), meta
    except ArchivoInvalido:
        raise
    except (sqlite3.DatabaseError, KeyError, ValueError, TypeError, IndexError) as e:
        raise ArchivoInvalido(f"el archivo está dañado o no es un proyecto de D-MIKE ({e})")


# ---------------- exportación para Minitab ----------------
def nombre_minitab(nombre, j, usados):
    """Ajusta un nombre a las reglas de Minitab. Devuelve (nombre, cambiado)."""
    orig = nombre
    n = (nombre or f"C{j + 1}").replace("'", "").replace("#", "").strip().lstrip("*").strip()
    n = n or f"C{j + 1}"
    n = n[:MAX_NOMBRE].strip()
    base, k = n, 2
    while n.lower() in usados:
        suf = f"_{k}"; n = base[:MAX_NOMBRE - len(suf)] + suf; k += 1
    usados.add(n.lower())
    return n, bool(orig) and n != orig


def tabla_limpia(hoja, columnas=None):
    """Columnas con al menos nombre o datos; valores interpretados, inválidos como None."""
    idx = columnas if columnas is not None else [
        j for j, c in enumerate(hoja.columnas) if c.nombre or any(v not in (None, "") for v in c.celdas)]
    usados, cambios, cols = set(), [], []
    for j in idx:
        c = hoja.columnas[j]
        nom, cambiado = nombre_minitab(c.nombre, j, usados)
        if cambiado: cambios.append(f"«{c.nombre}» → «{nom}»")
        vals = []
        for i in range(hoja.n):
            _, ok, v = c.valor(i)
            vals.append(v if ok else None)
        cols.append({"nombre": nom, "tipo": c.tipo, "valores": vals})
    faltantes = sum(1 for j in idx for i in range(hoja.n) if not hoja.columnas[j].valor(i)[1])
    return cols, cambios, faltantes


def id_proyecto_de(ruta):
    """id_proyecto guardado en «_receta» de un .dmike, leyendo solo el JSON del proyecto (sin cargar la hoja). None si no hay o no se puede leer."""
    try:
        from pathlib import Path
        con = sqlite3.connect(Path(ruta).resolve().as_uri() + "?mode=ro", uri=True)
        try: fila = con.execute("SELECT json FROM proyecto WHERE clave = 'estado'").fetchone()
        finally: con.close()
        rec = (json.loads(fila[0]).get("formatos") or {}).get("_receta") if fila else None
        return rec.get("id_proyecto") if isinstance(rec, dict) else None
    except (sqlite3.DatabaseError, ValueError, TypeError, AttributeError, OSError):
        return None


def exportar_xlsx(ruta, cols, n, etiqueta=None):
    """etiqueta: marca de proyecto de demostración. Va en una hoja «AVISO» (la hoja «Datos» sigue limpia para Minitab) y en las propiedades del libro."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook(); ws = wb.active; ws.title = "Datos"
    for j, c in enumerate(cols, start=1):
        ws.cell(1, j, c["nombre"]).font = Font(bold=True)
        for i, v in enumerate(c["valores"], start=2):
            if v is None: continue
            cel = ws.cell(i, j, v)
            if c["tipo"] == "fecha": cel.number_format = "DD/MM/YYYY"
    if etiqueta:
        wa = wb.create_sheet("AVISO"); wa.cell(1, 1, etiqueta).font = Font(bold=True, color="C00000")
        wa.cell(2, 1, "Los datos de la hoja «Datos» son sintéticos y no pertenecen a ninguna empresa.")
        wb.properties.subject = etiqueta
    wb.save(ruta)


def exportar_csv(ruta, cols, n, etiqueta=None):
    """etiqueta: el CSV debe quedar limpio para Minitab, así que la marca va en un archivo vecino «<nombre>_AVISO.txt»."""
    if etiqueta:
        with open(os.path.splitext(ruta)[0] + "_AVISO.txt", "w", encoding="utf-8") as f:
            f.write(f"{etiqueta}\nLos datos de {os.path.basename(ruta)} son sintéticos y no pertenecen a ninguna empresa.\n")
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([c["nombre"] for c in cols])
        for i in range(n):
            fila = []
            for c in cols:
                v = c["valores"][i]
                if v is None: fila.append("")
                elif c["tipo"] == "fecha": fila.append(v.isoformat())
                elif c["tipo"] == "num": fila.append(repr(v) if not float(v).is_integer() else str(int(v)))
                else: fila.append(v)
            w.writerow(fila)
