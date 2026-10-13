"""Calc > Calculadora de columnas y utilidades de datos: serie/patrón, datos aleatorios, recodificar, apilar y duplicados.
Todas cambian la hoja (se pueden deshacer con Ctrl+Z). Las fórmulas de la calculadora usan una lista de funciones
permitidas; no se ejecuta código arbitrario."""
import ast, math, re
import numpy as np
from scipy import stats as st
from . import registrar
from .base import ErrorEntrada, columna
from .dialogo import ModuloDialogo
from ..nucleo.hoja import Columna, a_numero

NAN = float("nan")


# ---------------- utilidades de escritura ----------------
def escribir_columna(hoja, nombre, valores, tipo="num"):
    """Escribe una columna completa. Si el nombre ya existe la reemplaza; si no, la agrega a la derecha."""
    nombre = (nombre or "").strip()
    if not nombre: raise ErrorEntrada("Escribe el nombre de la columna de resultado.")
    j = hoja.indice(nombre)
    n = max(hoja.n, len(valores))
    if j is None:
        j = len(hoja.columnas); hoja._asegurar(max(n - 1, 0), j)
        hoja.columnas[j].nombre = nombre
    else:
        hoja._asegurar(max(n - 1, 0), j)
    c = hoja.columnas[j]; c.tipo = tipo
    c.celdas = [None] * hoja.n
    for i, v in enumerate(valores):
        c.celdas[i] = None if v is None else v if isinstance(v, str) else _fmt(v)
    return j


def _fmt(x):
    if isinstance(x, (float, np.floating)):
        if math.isnan(x) or math.isinf(x): return None
        return str(int(x)) if float(x).is_integer() and abs(x) < 1e15 else repr(round(float(x), 12))
    return str(x)


def _vector(hoja, j):
    """Valores numéricos de una columna como arreglo; vacíos e inválidos son NaN."""
    c = hoja.columnas[j]
    if c.tipo not in ("num", None): raise ErrorEntrada(f"C{j + 1} {c.nombre} no es numérica; las fórmulas solo operan con números.")
    return np.array([c.valor(i)[2] if c.valor(i)[1] and c.valor(i)[2] is not None else NAN for i in range(hoja.n)], float)


# ---------------- calculadora ----------------
def _rango(x):
    out = np.full(len(x), NAN); ok = ~np.isnan(x)
    out[ok] = st.rankdata(x[ok], method="average"); return out


def _estand(x):
    s = np.nanstd(x, ddof=1); return (x - np.nanmean(x)) / s if s > 0 else x * NAN


def _retraso(x, k=1):
    k = int(k); out = np.full(len(x), NAN)
    if k >= 0: out[k:] = x[:len(x) - k] if k else x
    else: out[:k] = x[-k:]
    return out


def _si(c, a, b): return np.where(np.isnan(c), NAN, np.where(c != 0, a, b))


FUNCIONES = {
    "LOG10": np.log10, "LOG": np.log10, "LN": np.log, "EXP": np.exp, "RAIZ": np.sqrt, "SQRT": np.sqrt, "ABS": np.abs,
    "SEN": np.sin, "SIN": np.sin, "COS": np.cos, "TAN": np.tan, "ENTERO": np.trunc, "PISO": np.floor, "TECHO": np.ceil,
    "REDONDEAR": lambda x, d=0: np.round(x, int(d)), "ROUND": lambda x, d=0: np.round(x, int(d)), "SI": _si, "IF": _si,
    "MAXIMO2": np.maximum, "MINIMO2": np.minimum,
}
AGREGADOS = {   # una columna -> un número que se repite en todas las filas
    "SUMA": np.nansum, "PROMEDIO": np.nanmean, "MEDIA": np.nanmean, "MEDIANA": np.nanmedian, "MIN": np.nanmin, "MAX": np.nanmax,
    "DESV": lambda x: np.nanstd(x, ddof=1), "VARIANZA": lambda x: np.nanvar(x, ddof=1), "N": lambda x: float((~np.isnan(x)).sum()),
}
VECTORIALES = {"ACUM": lambda x: np.nancumsum(np.where(np.isnan(x), 0, x)) * np.where(np.isnan(x), NAN, 1), "DIF": lambda x: np.concatenate([[NAN], np.diff(x)]),
               "RETRASO": _retraso, "RANGO": _rango, "ESTAND": _estand}
OPS = {ast.Add: np.add, ast.Sub: np.subtract, ast.Mult: np.multiply, ast.Div: np.divide, ast.Pow: np.power, ast.Mod: np.mod}
CMP = {ast.Gt: np.greater, ast.GtE: np.greater_equal, ast.Lt: np.less, ast.LtE: np.less_equal, ast.Eq: np.equal, ast.NotEq: np.not_equal}


class Evaluador:
    def __init__(self, hoja):
        self.h = hoja; self.n = hoja.n; self.ref = {}

    def preparar(self, texto):
        t = texto.strip().replace("^", "**").replace(",", ".") if "'" not in texto and ";" not in texto else texto.strip().replace("^", "**")
        t = t.replace(";", ",")                         # separador de argumentos en español
        def comilla(m):
            j = self.h.indice(m.group(1))
            if j is None: raise ErrorEntrada(f"No existe la columna «{m.group(1)}».")
            k = f"__c{j}"; self.ref[k] = j; return k
        t = re.sub(r"'([^']+)'", comilla, t)
        t = re.sub(r"\b[Cc](\d+)\b", lambda m: self._c(int(m.group(1)) - 1), t)
        for j, c in enumerate(self.h.columnas):          # nombres de columna sin comillas ni espacios
            if c.nombre and re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúñÑ_][\wÁÉÍÓÚáéíóúñÑ]*", c.nombre) and c.nombre.upper() not in {*FUNCIONES, *AGREGADOS, *VECTORIALES, "PI", "E", "FILA"}:
                t = re.sub(rf"(?<![\w.]){re.escape(c.nombre)}(?![\w(])", self._c(j), t)
        return t

    def _c(self, j):
        if not 0 <= j < len(self.h.columnas): raise ErrorEntrada(f"La columna C{j + 1} no existe.")
        k = f"__c{j}"; self.ref[k] = j; return k

    def evaluar(self, texto):
        try:
            arbol = ast.parse(self.preparar(texto), mode="eval")
        except SyntaxError:
            raise ErrorEntrada("No entiendo la fórmula. Ejemplo: LOG10('tiempo') + C2 / 2")
        v = self._ev(arbol.body)
        v = np.asarray(v, float)
        return np.full(self.n, float(v)) if v.ndim == 0 else v

    def _ev(self, nodo):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)) and not isinstance(nodo.value, bool): return float(nodo.value)
        if isinstance(nodo, ast.Name):
            if nodo.id in self.ref: return _vector(self.h, self.ref[nodo.id])
            if nodo.id.upper() == "PI": return math.pi
            if nodo.id.upper() == "E": return math.e
            raise ErrorEntrada(f"«{nodo.id}» no es una columna ni una función conocida. Usa comillas simples para nombres con espacios: 'mi columna'.")
        if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, (ast.USub, ast.UAdd)):
            v = self._ev(nodo.operand); return -v if isinstance(nodo.op, ast.USub) else v
        if isinstance(nodo, ast.BinOp) and type(nodo.op) in OPS:
            with np.errstate(all="ignore"): return OPS[type(nodo.op)](self._ev(nodo.left), self._ev(nodo.right))
        if isinstance(nodo, ast.Compare) and len(nodo.ops) == 1 and type(nodo.ops[0]) in CMP:
            a, b = np.asarray(self._ev(nodo.left), float), np.asarray(self._ev(nodo.comparators[0]), float)
            return np.where(np.isnan(a) | np.isnan(b), NAN, CMP[type(nodo.ops[0])](a, b).astype(float))
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and not nodo.keywords:
            f = nodo.func.id.upper(); args = [self._ev(a) for a in nodo.args]
            if f == "FILA": return np.arange(1, self.n + 1, dtype=float)
            if f in AGREGADOS:
                if len(args) != 1: raise ErrorEntrada(f"{f} lleva una sola columna.")
                x = np.broadcast_to(np.asarray(args[0], float), (self.n,))
                return float(AGREGADOS[f](x)) if np.any(~np.isnan(x)) else NAN
            if f in VECTORIALES: return VECTORIALES[f](np.asarray(args[0], float), *args[1:])
            if f in FUNCIONES:
                with np.errstate(all="ignore"): return FUNCIONES[f](*args)
            raise ErrorEntrada(f"La función {nodo.func.id} no existe. Disponibles: " + ", ".join(sorted({*FUNCIONES, *AGREGADOS, *VECTORIALES, "FILA"})) + ".")
        raise ErrorEntrada("La fórmula usa algo que no está permitido (solo números, columnas, operadores y las funciones de la lista).")


@registrar
class Calculadora(ModuloDialogo):
    ID, TITULO, SIN_RESULTADO, CAMBIA_HOJA = "CALCULADORA", "Calculadora de columnas", True, True
    CAMPOS = [{"campo": "dest", "etiqueta": "Guardar el resultado en la columna (nombre nuevo o existente)", "tipo": "texto"},
              {"campo": "expr", "etiqueta": "Fórmula (columnas: C1, 'nombre con espacios' o nombre; funciones abajo)", "tipo": "texto"},
              {"campo": "ayuda", "etiqueta": "Funciones: LOG10 LN EXP RAIZ ABS REDONDEAR(x;d) SI(cond;a;b) ENTERO PISO TECHO SEN COS TAN · "
                                             "de una columna: SUMA PROMEDIO MEDIANA DESV VARIANZA MIN MAX N · por fila: ACUM DIF RETRASO(x;k) RANGO ESTAND FILA()",
               "tipo": "nota"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        expr = (p.get("expr") or "").strip()
        if not expr: raise ErrorEntrada("Escribe la fórmula.")
        if not hoja.n: raise ErrorEntrada("La hoja no tiene filas de datos.")
        ev = Evaluador(hoja); v = ev.evaluar(expr)
        existia = hoja.indice((p.get("dest") or "").strip()) is not None
        j = escribir_columna(hoja, p.get("dest"), [None if math.isnan(x) else float(x) for x in v], "num")
        malos = int(np.isnan(v).sum())
        return (f"{'Reemplazada' if existia else 'Creada'} la columna C{j + 1} {hoja.columnas[j].nombre} con {hoja.n - malos} valores"
                + (f"; {malos} filas quedaron vacías (dato faltante, no numérico o resultado no válido)." if malos else "."))


# ---------------- patrón ----------------
def _lista(t):
    t = (t or "").strip()
    m = re.fullmatch(r"(-?[\d.]+)\s*:\s*(-?[\d.]+)(?:\s*:\s*(-?[\d.]+))?", t)
    if m:                                          # inicio:fin  o  inicio:fin:paso
        a, b = float(m[1]), float(m[2]); paso = float(m[3]) if m[3] else (1.0 if b >= a else -1.0)
        if paso == 0 or (b - a) * paso < 0: raise ErrorEntrada("El rango no avanza hacia el fin: revisa inicio, fin y paso.")
        n = int(math.floor((b - a) / paso + 1e-9)) + 1
        if n > 1_000_000: raise ErrorEntrada("El patrón es demasiado grande.")
        return [a + k * paso for k in range(n)]
    partes = [x.strip() for x in t.replace(";", ",").split(",") if x.strip()]
    if not partes: raise ErrorEntrada("Escribe los valores (ej. 1:10, o A, B, C).")
    nums = [a_numero(x) for x in partes]
    return nums if None not in nums else partes


@registrar
class Patron(ModuloDialogo):
    ID, TITULO, SIN_RESULTADO, CAMBIA_HOJA = "PATRON", "Serie y patrón de datos", True, True
    CAMPOS = [{"campo": "dest", "etiqueta": "Columna de resultado", "tipo": "texto"},
              {"campo": "lista", "etiqueta": "Valores: rango (1:10, 0:1:0.1) o lista (A, B, C)", "tipo": "texto"},
              {"campo": "cada", "etiqueta": "Repetir cada valor (veces seguidas)", "tipo": "numero", "defecto": "1"},
              {"campo": "veces", "etiqueta": "Repetir toda la secuencia (veces)", "tipo": "numero", "defecto": "1"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        base = _lista(p.get("lista"))
        cada = int(cls.numero(p, "cada", "Cada", minimo=0) or 1); veces = int(cls.numero(p, "veces", "Veces", minimo=0) or 1)
        vals = [v for v in base for _ in range(cada)] * veces
        if len(vals) > 1_000_000: raise ErrorEntrada("El patrón es demasiado grande.")
        j = escribir_columna(hoja, p.get("dest"), vals, "num" if all(isinstance(v, (int, float)) for v in vals) else "texto")
        return f"Columna C{j + 1} {hoja.columnas[j].nombre} con {len(vals)} valores."


# ---------------- aleatorios ----------------
DISTS = [["normal", "Normal (media, desviación)"], ["uniforme", "Uniforme (mínimo, máximo)"], ["enteros", "Enteros uniformes (mínimo, máximo)"],
         ["exponencial", "Exponencial (media)"], ["weibull", "Weibull (forma, escala)"], ["binomial", "Binomial (n, p)"], ["poisson", "Poisson (media)"],
         ["lognormal", "Lognormal (media del log, desviación del log)"]]


@registrar
class Aleatorios(ModuloDialogo):
    ID, TITULO, SIN_RESULTADO, CAMBIA_HOJA = "ALEATORIOS", "Datos aleatorios (para pruebas y simulación)", True, True
    CAMPOS = [{"campo": "dest", "etiqueta": "Columna de resultado", "tipo": "texto"},
              {"campo": "n", "etiqueta": "Cantidad de valores", "tipo": "numero", "defecto": "30"},
              {"campo": "dist", "etiqueta": "Distribución", "tipo": "opcion", "opciones": DISTS, "defecto": "normal"},
              {"campo": "a", "etiqueta": "Parámetro 1 (media, mínimo, forma, n...)", "tipo": "numero", "defecto": "0"},
              {"campo": "b", "etiqueta": "Parámetro 2 (desviación, máximo, escala, p...)", "tipo": "numero", "defecto": "1"},
              {"campo": "semilla", "etiqueta": "Semilla (opcional; la misma semilla da los mismos datos)", "tipo": "numero"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        n = int(cls.numero(p, "n", "La cantidad", opcional=False, minimo=0)); a = cls.numero(p, "a", "El parámetro 1") or 0.0
        b = cls.numero(p, "b", "El parámetro 2"); b = 1.0 if b is None else b
        if n > 1_000_000: raise ErrorEntrada("Máximo 1,000,000 de valores.")
        sem = cls.numero(p, "semilla", "La semilla"); rng = np.random.default_rng(int(sem) if sem is not None else None)
        d = p.get("dist") or "normal"
        try:
            if d == "normal":
                if b <= 0: raise ValueError("La desviación debe ser mayor que cero.")
                x = rng.normal(a, b, n)
            elif d == "uniforme":
                if b <= a: raise ValueError("El máximo debe ser mayor que el mínimo.")
                x = rng.uniform(a, b, n)
            elif d == "enteros":
                if b < a: raise ValueError("El máximo debe ser mayor o igual que el mínimo.")
                x = rng.integers(int(a), int(b) + 1, n).astype(float)
            elif d == "exponencial":
                if a <= 0: raise ValueError("La media debe ser mayor que cero.")
                x = rng.exponential(a, n)
            elif d == "weibull":
                if a <= 0 or b <= 0: raise ValueError("Forma y escala deben ser mayores que cero.")
                x = b * rng.weibull(a, n)
            elif d == "binomial":
                if a < 1 or not 0 <= b <= 1: raise ValueError("n debe ser al menos 1 y p estar entre 0 y 1.")
                x = rng.binomial(int(a), b, n).astype(float)
            elif d == "poisson":
                if a <= 0: raise ValueError("La media debe ser mayor que cero.")
                x = rng.poisson(a, n).astype(float)
            else:
                if b <= 0: raise ValueError("La desviación debe ser mayor que cero.")
                x = rng.lognormal(a, b, n)
        except ValueError as e:
            raise ErrorEntrada(str(e))
        j = escribir_columna(hoja, p.get("dest"), [float(v) for v in x], "num")
        return f"Columna C{j + 1} {hoja.columnas[j].nombre}: {n} datos {dict(DISTS)[d].split(' (')[0].lower()} generados (datos de simulación, no reales)."


# ---------------- recodificar, apilar, duplicados ----------------
@registrar
class Recodificar(ModuloDialogo):
    ID, TITULO, SIN_RESULTADO, CAMBIA_HOJA = "RECODIFICAR", "Recodificar valores", True, True
    CAMPOS = [{"campo": "col", "etiqueta": "Columna origen", "tipo": "col"},
              {"campo": "dest", "etiqueta": "Columna de resultado (vacío = mismo nombre + _rec)", "tipo": "texto"},
              {"campo": "mapa", "etiqueta": "Cambios (ej. Sin=0; Con=1; los demás valores se conservan)", "tipo": "texto"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        j = p.get("col"); c = columna(hoja, j, "la columna")
        pares = {}
        for t in (p.get("mapa") or "").replace("\n", ";").split(";"):
            if not t.strip(): continue
            if "=" not in t: raise ErrorEntrada(f"«{t.strip()}» no tiene el formato valor=nuevo.")
            a, b = t.split("=", 1); pares[a.strip().lower()] = b.strip()
        if not pares: raise ErrorEntrada("Escribe al menos un cambio, por ejemplo Sin=0.")
        sal, cambios = [], 0
        for i in range(hoja.n):
            t = (c.celdas[i] or "").strip()
            if t.lower() in pares: sal.append(pares[t.lower()]); cambios += 1
            else: sal.append(c.celdas[i])
        dest = (p.get("dest") or "").strip() or f"{c.nombre or f'C{j + 1}'}_rec"
        from ..nucleo.hoja import detectar_tipo
        k = escribir_columna(hoja, dest, sal, detectar_tipo([s for s in sal if s]) or "texto")
        return f"Columna C{k + 1} {hoja.columnas[k].nombre}: {cambios} valores recodificados."


@registrar
class Apilar(ModuloDialogo):
    ID, TITULO, SIN_RESULTADO, CAMBIA_HOJA = "APILAR", "Apilar columnas", True, True
    CAMPOS = [{"campo": "cols", "etiqueta": "Columnas a apilar en una sola (2 o más)", "tipo": "cols"},
              {"campo": "dest", "etiqueta": "Columna de valores", "tipo": "texto", "defecto": "Apilado"},
              {"campo": "origen", "etiqueta": "Columna con el nombre de origen", "tipo": "texto", "defecto": "Origen"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        cols = [j for j in (p.get("cols") or []) if j is not None]
        if len(cols) < 2: raise ErrorEntrada("Elige al menos 2 columnas.")
        for j in cols: columna(hoja, j, "las columnas")
        if len({hoja.columnas[j].tipo for j in cols}) > 1: raise ErrorEntrada("Las columnas deben ser del mismo tipo.")
        vals, orig = [], []
        for j in cols:
            c = hoja.columnas[j]
            for i in range(hoja.n):
                if (c.celdas[i] or "").strip(): vals.append(c.celdas[i]); orig.append(c.nombre or f"C{j + 1}")
        j1 = escribir_columna(hoja, (p.get("dest") or "").strip() or "Apilado", vals, hoja.columnas[cols[0]].tipo or "num")
        j2 = escribir_columna(hoja, (p.get("origen") or "").strip() or "Origen", orig, "texto")
        return f"Apiladas {len(cols)} columnas en C{j1 + 1} ({len(vals)} valores) con el origen en C{j2 + 1}."


@registrar
class Duplicados(ModuloDialogo):
    ID, TITULO, SIN_RESULTADO, CAMBIA_HOJA = "DUPLICADOS", "Detectar duplicados", True, True
    CAMPOS = [{"campo": "cols", "etiqueta": "Columnas que forman la clave (la fila se repite si todas coinciden)", "tipo": "cols"},
              {"campo": "dest", "etiqueta": "Columna de resultado (1 = repetida, 0 = primera aparición)", "tipo": "texto", "defecto": "Duplicado"}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        cols = [j for j in (p.get("cols") or []) if j is not None]
        if not cols: raise ErrorEntrada("Elige al menos una columna.")
        for j in cols: columna(hoja, j, "las columnas")
        vistos, marca = set(), []
        for i in range(hoja.n):
            k = tuple((hoja.columnas[j].celdas[i] or "").strip().lower() for j in cols)
            if all(x == "" for x in k): marca.append(None); continue
            marca.append(1.0 if k in vistos else 0.0); vistos.add(k)
        k = escribir_columna(hoja, (p.get("dest") or "").strip() or "Duplicado", marca, "num")
        return f"Columna C{k + 1}: {int(sum(m for m in marca if m))} filas repetidas de {sum(1 for m in marca if m is not None)}."
