"""Hoja de datos central. Organizada por columnas, como Minitab.

Tipos de columna: None (vacía, se detecta con el primer dato), "num", "texto", "fecha".
Cada celda guarda el texto tal como se capturó; el tipo decide cómo se interpreta.
Una celda que no corresponde al tipo queda marcada como inválida y no entra a los cálculos.
"""
import re
from datetime import date

SUFIJO = {None: "", "num": "", "texto": "-T", "fecha": "-D"}
NUM = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
MILES = re.compile(r"^[+-]?\d{1,3}(,\d{3})+(\.\d+)?$")
ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
DMA = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")   # día/mes/año (México)


def a_numero(t):
    t = t.strip()
    if NUM.match(t): return float(t)
    if MILES.match(t): return float(t.replace(",", ""))
    return None


def a_fecha(t):
    t = t.strip(); m = ISO.match(t)
    try:
        if m: return date(int(m[1]), int(m[2]), int(m[3]))
        m = DMA.match(t)
        if m: return date(int(m[3]), int(m[2]), int(m[1]))
    except ValueError:
        return None
    return None


def detectar_tipo(textos):
    vals = [t for t in textos if t is not None and t.strip() != ""]
    if not vals: return None
    # Regla de diseño D-MIKE: el tipo lo decide la mayoría de los valores; los que no
    # corresponden quedan marcados como inválidos en vez de convertir toda la columna a texto.
    n_num = sum(a_numero(t) is not None for t in vals)
    n_fec = sum(a_fecha(t) is not None for t in vals)
    if n_num * 2 > len(vals): return "num"
    if n_fec * 2 > len(vals): return "fecha"
    return "texto"


def mostrar_numero(x):
    return str(int(x)) if x.is_integer() and abs(x) < 1e15 else repr(x)


class Columna:
    def __init__(self, n):
        self.nombre = ""; self.tipo = None; self.rol = None; self.desc = ""
        self.celdas = [None] * n

    def valor(self, i):
        """(texto_a_mostrar, valido, valor_interpretado)"""
        t = self.celdas[i]
        if t is None or t.strip() == "": return "", True, None
        if self.tipo == "num":
            x = a_numero(t)
            return (mostrar_numero(x), True, x) if x is not None else (t, False, None)
        if self.tipo == "fecha":
            d = a_fecha(t)
            return (d.strftime("%d/%m/%Y"), True, d) if d else (t, False, None)  # se muestra DD/MM/AAAA
        return t, True, t


class Hoja:
    MIN_COLS, MIN_FILAS = 20, 50

    def __init__(self):
        self.n = 0              # filas con datos (longitud de cada columna)
        self.columnas = []
        self.filtro = []        # condiciones activas [{col, op, valor}]; las filas que no cumplen se ocultan y no entran a análisis

    # --- instantáneas rápidas (deshacer) ---
    def instantanea(self):
        return (self.n, [(c.nombre, c.tipo, c.rol, c.desc, list(c.celdas)) for c in self.columnas], [dict(f) for f in self.filtro])

    def restaurar(self, snap):
        self.n = snap[0]; self.columnas = []
        for nom, tipo, rol, desc, cel in snap[1]:
            c = Columna(0); c.nombre, c.tipo, c.rol, c.desc, c.celdas = nom, tipo, rol, desc, list(cel); self.columnas.append(c)
        self.filtro = [dict(f) for f in snap[2]]

    # --- tamaño ---
    def _asegurar(self, fila, col):
        while len(self.columnas) <= col: self.columnas.append(Columna(self.n))
        if fila >= self.n:
            extra = fila + 1 - self.n
            for c in self.columnas: c.celdas.extend([None] * extra)
            self.n = fila + 1

    def _recortar(self):
        """Quita filas y columnas vacías al final para que el tamaño refleje los datos."""
        while self.n and all(c.celdas[self.n - 1] in (None, "") for c in self.columnas):
            for c in self.columnas: c.celdas.pop()
            self.n -= 1
        while self.columnas and not self.columnas[-1].nombre and self.columnas[-1].tipo is None and all(v in (None, "") for v in self.columnas[-1].celdas):
            self.columnas.pop()

    # --- edición ---
    def editar(self, fila, col, texto):
        texto = None if texto is None or texto.strip() == "" else texto
        if texto is None and (col >= len(self.columnas) or fila >= self.n): return
        self._asegurar(fila, col)
        c = self.columnas[col]; c.celdas[fila] = texto
        if c.tipo is None: c.tipo = detectar_tipo([texto] if texto else [])
        self._recortar()

    def pegar(self, fila, col, texto):
        """Pega texto separado por tabuladores (lo que copia Excel). fila = -1 es la fila de nombres."""
        lineas = texto.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n").split("\n")
        tabla = [l.split("\t") for l in lineas]
        ancho = max(len(r) for r in tabla)
        if fila == -1:
            nombres, tabla, fila = tabla[0], tabla[1:], 0
            self._asegurar(0, col + ancho - 1)
            for j, nom in enumerate(nombres):
                self.renombrar(col + j, nom.strip(), forzar_unico=True)
        if tabla:
            self._asegurar(fila + len(tabla) - 1, col + ancho - 1)
            for j in range(ancho):
                c = self.columnas[col + j]
                nuevos = [r[j] if j < len(r) else "" for r in tabla]
                if c.tipo is None and all(v in (None, "") for v in c.celdas):
                    c.tipo = detectar_tipo(nuevos)
                for i, v in enumerate(nuevos):
                    c.celdas[fila + i] = v if v.strip() else None
        self._recortar()
        return len(tabla), ancho

    def renombrar(self, col, nombre, forzar_unico=False):
        nombre = nombre.strip()
        if nombre:
            usados = {c.nombre.lower() for k, c in enumerate(self.columnas) if k != col and c.nombre}
            if nombre.lower() in usados:
                if not forzar_unico: raise ValueError(f"Ya existe una columna llamada «{nombre}».")
                base, k = nombre, 2
                while f"{base}_{k}".lower() in usados: k += 1
                nombre = f"{base}_{k}"
        if not nombre and col >= len(self.columnas): return
        self._asegurar(max(self.n - 1, 0), col)
        self.columnas[col].nombre = nombre
        self._recortar()

    def cambiar_tipo(self, col, tipo):
        if tipo not in ("num", "texto", "fecha"): raise ValueError("Tipo no válido.")
        self._asegurar(max(self.n - 1, 0), col)
        self.columnas[col].tipo = tipo
        self._recortar()
        return sum(1 for i in range(self.n) if not self.columnas[col].valor(i)[1])

    def insertar_columna(self, col):
        if col < len(self.columnas): self.columnas.insert(col, Columna(self.n))

    def eliminar_columna(self, col):
        if col < len(self.columnas): self.columnas.pop(col); self._recortar()

    def insertar_fila(self, fila):
        if fila < self.n:
            for c in self.columnas: c.celdas.insert(fila, None)
            self.n += 1

    def eliminar_fila(self, fila):
        if fila < self.n:
            for c in self.columnas: c.celdas.pop(fila)
            self.n -= 1; self._recortar()

    def agregar_sugeridas(self, columnas):
        """Crea al final las columnas sugeridas por el perfil que no existan (por nombre, sin distinguir
        mayúsculas). Nunca borra ni cambia el tipo de una columna existente; solo le asigna rol si no tenía."""
        existentes = {c.nombre.lower(): c for c in self.columnas if c.nombre}
        creadas = []
        for s in columnas:
            c = existentes.get(s["nombre"].lower())
            if c is not None:
                if c.rol is None: c.rol = s.get("rol")
                if not getattr(c, "desc", ""): c.desc = s.get("desc", "")
                continue
            nueva = Columna(self.n); nueva.nombre, nueva.tipo, nueva.rol = s["nombre"], s["tipo"], s.get("rol")
            nueva.desc = s.get("desc", "")
            self.columnas.append(nueva); existentes[nueva.nombre.lower()] = nueva; creadas.append(nueva.nombre)
        return creadas

    # --- rangos (selección tipo hoja de cálculo) ---
    def borrar_rango(self, f0, c0, f1, c1, filas=None):
        """Vacía el contenido de un rango (o solo de las filas dadas, cuando hay un filtro). Con f0 = -1 incluye los nombres."""
        n = 0
        rows = list(filas) if filas is not None else range(max(f0, 0), min(f1, self.n - 1) + 1)
        for j in range(c0, min(c1, len(self.columnas) - 1) + 1):
            c = self.columnas[j]
            if f0 < 0 and c.nombre: c.nombre = ""; n += 1
            for i in rows:
                if 0 <= i < self.n and c.celdas[i] not in (None, ""): c.celdas[i] = None; n += 1
        self._recortar(); return n

    def llenar_con(self, f0, c0, f1, c1, texto, filas=None):
        """Pone el mismo texto en todas las celdas del rango (pegar un valor sobre varias celdas seleccionadas)."""
        texto = None if texto is None or texto.strip() == "" else texto.strip()
        self._asegurar(f1, c1)
        rows = list(filas) if filas is not None else range(f0, f1 + 1)
        for j in range(c0, c1 + 1):
            c = self.columnas[j]
            if c.tipo is None and texto is not None: c.tipo = detectar_tipo([texto])
            for i in rows: c.celdas[i] = texto
        self._recortar(); return len(rows) * (c1 - c0 + 1)

    def rellenar(self, f0, c0, f1, c1, direccion="abajo"):
        """Rellena el rango con la primera fila (abajo) o la primera columna (derecha) del rango, como Ctrl+D y Ctrl+R."""
        self._asegurar(f1, c1)
        if direccion == "abajo":
            if f1 <= f0: return 0
            for j in range(c0, c1 + 1):
                v = self.columnas[j].celdas[f0]
                for i in range(f0 + 1, f1 + 1): self.columnas[j].celdas[i] = v
            return (f1 - f0) * (c1 - c0 + 1)
        if c1 <= c0: return 0
        for i in range(f0, f1 + 1):
            v = self.columnas[c0].celdas[i]
            for j in range(c0 + 1, c1 + 1): self.columnas[j].celdas[i] = v
            if self.columnas[c0].tipo and self.columnas[c0].tipo != "texto":
                for j in range(c0 + 1, c1 + 1):
                    if self.columnas[j].tipo is None: self.columnas[j].tipo = self.columnas[c0].tipo
        return (c1 - c0) * (f1 - f0 + 1)

    def insertar_filas(self, fila, k=1):
        for _ in range(k): self.insertar_fila(fila)

    def eliminar_filas(self, f0, f1):
        for i in range(min(f1, self.n - 1), f0 - 1, -1): self.eliminar_fila(i)

    def eliminar_columnas(self, c0, c1):
        for j in range(min(c1, len(self.columnas) - 1), c0 - 1, -1): self.columnas.pop(j)
        self._recortar()

    def texto_rango(self, f0, c0, f1, c1):
        """Texto con tabuladores (lo que se copia al portapapeles). f0 = -1 incluye la fila de nombres."""
        filas = []
        if f0 < 0: filas.append("\t".join(self.columnas[j].nombre if j < len(self.columnas) else "" for j in range(c0, c1 + 1)))
        for i in range(max(f0, 0), f1 + 1):
            filas.append("\t".join((self.columnas[j].celdas[i] or "") if j < len(self.columnas) and i < self.n else "" for j in range(c0, c1 + 1)))
        return "\n".join(filas)

    # --- filtro de filas (Minitab: activar y desactivar filas) ---
    OPS = {"=": "es igual a", "!=": "es distinto de", ">": "mayor que", ">=": "mayor o igual que", "<": "menor que", "<=": "menor o igual que",
           "contiene": "contiene", "vacio": "está vacía", "no_vacio": "no está vacía"}

    def _cumple(self, i, cond):
        c = self.columnas[cond["col"]]; op = cond["op"]; v = cond.get("valor", "")
        txt = (c.celdas[i] or "").strip()
        if op == "vacio": return txt == ""
        if op == "no_vacio": return txt != ""
        if op == "contiene": return v.lower() in txt.lower()
        a, b = c.valor(i)[2], None
        if c.tipo == "num": b = a_numero(v)
        elif c.tipo == "fecha": b = a_fecha(v)
        else: a, b = txt.lower(), v.strip().lower()
        if a is None or b is None: return op == "!="
        return {"=": a == b, "!=": a != b, ">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[op]

    def filas_activas(self):
        """Conjunto de filas visibles, o None si no hay filtro."""
        if not self.filtro: return None
        return {i for i in range(self.n) if all(self._cumple(i, f) for f in self.filtro)}

    def aplicar_filtro(self, condiciones):
        for f in condiciones:
            if not 0 <= f["col"] < len(self.columnas): raise ValueError("La columna del filtro ya no existe.")
            if f["op"] not in self.OPS: raise ValueError("Operador de filtro no válido.")
            if f["op"] not in ("vacio", "no_vacio") and not str(f.get("valor", "")).strip(): raise ValueError("Escribe el valor del filtro.")
            c = self.columnas[f["col"]]
            if f["op"] in (">", ">=", "<", "<=") and c.tipo == "texto": pass
            if c.tipo == "num" and f["op"] not in ("contiene", "vacio", "no_vacio") and a_numero(str(f["valor"])) is None:
                raise ValueError(f"«{f['valor']}» no es un número, y la columna es numérica.")
        self.filtro = [dict(f) for f in condiciones]
        return len(self.filas_activas() or ())

    # --- ordenar y reemplazar (E2) ---
    def ordenar(self, col, descendente=False):
        """Ordena todas las filas según una columna (las filas se mueven completas). Vacíos e inválidos van al final;
        el orden es estable (empates conservan su orden)."""
        c = self.columnas[col]
        usadas = [i for i in range(self.n) if any(x.celdas[i] not in (None, "") for x in self.columnas)]
        con = [i for i in usadas if c.valor(i)[1] and c.valor(i)[2] is not None]
        sin = [i for i in usadas if i not in set(con)]
        clave = (lambda i: c.valor(i)[2]) if c.tipo != "texto" else (lambda i: str(c.valor(i)[2]).lower())
        orden = sorted(con, key=clave, reverse=descendente) + sin
        for x in self.columnas:
            nuevas = [x.celdas[i] for i in orden]
            x.celdas[:len(nuevas)] = nuevas
            for i in range(len(nuevas), self.n): x.celdas[i] = None
        self._recortar()
        return len(con), len(sin)

    def reemplazar(self, buscar, nuevo, cols=None, completa=False, mayusculas=False):
        """Reemplaza texto en las celdas. completa: solo celdas cuyo contenido es exactamente «buscar»."""
        if not buscar: raise ValueError("Escribe el texto a buscar.")
        n = 0
        for j in (cols if cols is not None else range(len(self.columnas))):
            c = self.columnas[j]
            for i, t in enumerate(c.celdas):
                if t is None: continue
                a, b = (t, buscar) if mayusculas else (t.lower(), buscar.lower())
                if completa:
                    if a.strip() == b.strip(): c.celdas[i] = nuevo if nuevo.strip() else None; n += 1
                elif b in a:
                    if mayusculas: r = t.replace(buscar, nuevo)
                    else: r = re.sub(re.escape(buscar), lambda _: nuevo, t, flags=re.IGNORECASE)
                    c.celdas[i] = r if r.strip() else None; n += 1
        self._recortar()
        return n

    # --- persistencia ---
    def a_dict(self):
        return {"n": self.n, "filtro": self.filtro, "columnas": [{"nombre": c.nombre, "tipo": c.tipo, "rol": c.rol, "desc": c.desc,
                                                                  "celdas": c.celdas} for c in self.columnas]}

    @classmethod
    def de_dict(cls, d):
        h = cls(); h.n = d["n"]; h.filtro = d.get("filtro", [])
        for x in d["columnas"]:
            c = Columna(h.n); c.nombre, c.tipo, c.rol, c.desc = x["nombre"], x["tipo"], x.get("rol"), x.get("desc", "")
            c.celdas = list(x["celdas"]) + [None] * (h.n - len(x["celdas"]))
            h.columnas.append(c)
        return h

    # --- lectura ---
    def indice(self, nombre):
        for j, c in enumerate(self.columnas):
            if c.nombre.lower() == nombre.lower(): return j
        return None

    def valores(self, col):
        """Valores válidos interpretados de una columna, con su número de fila: [(fila, valor)]."""
        c = self.columnas[col]
        return [(i, v[2]) for i in range(self.n) for v in [c.valor(i)] if v[1] and v[2] is not None]

    def invalidas(self):
        return [(i, j) for j, c in enumerate(self.columnas) for i in range(self.n) if not c.valor(i)[1]]

    def estado(self):
        cols = []
        for j, c in enumerate(self.columnas):
            vals = [c.valor(i) for i in range(self.n)]
            cols.append({"etiqueta": f"C{j + 1}{SUFIJO[c.tipo]}", "nombre": c.nombre, "tipo": c.tipo, "rol": c.rol, "desc": c.desc,
                         "texto": [v[0] for v in vals], "invalida": [i for i, v in enumerate(vals) if not v[1]]})
        act = self.filas_activas()
        return {"filas": self.n, "columnas": cols, "visibles": sorted(act) if act is not None else None, "filtro": self.filtro,
                "vista_filas": max(self.MIN_FILAS, self.n + 20), "vista_columnas": max(self.MIN_COLS, len(self.columnas) + 5)}
