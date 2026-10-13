"""Herramientas de la hoja con diálogo (E2): ordenar y buscar y reemplazar. No generan resultado; cambian la hoja
y se pueden deshacer (Datos > Deshacer)."""
from . import registrar
from .base import ErrorEntrada, columna
from .dialogo import ModuloDialogo


@registrar
class Ordenar(ModuloDialogo):
    ID, TITULO, SIN_RESULTADO = "ORDENAR", "Ordenar la hoja", True
    CAMPOS = [{"campo": "col", "etiqueta": "Ordenar todas las filas según la columna", "tipo": "col"},
              {"campo": "orden", "etiqueta": "Orden", "tipo": "opcion", "defecto": "asc",
               "opciones": [["asc", "Ascendente (de menor a mayor, A a Z)"], ["desc", "Descendente"]]}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        j = p.get("col"); c = columna(hoja, j, "la columna")
        if c.tipo is None: raise ErrorEntrada("La columna está vacía.")
        con, sin = hoja.ordenar(j, (p.get("orden") or "asc") == "desc")
        return f"Hoja ordenada por {c.nombre or f'C{j + 1}'} ({con} filas" + (f"; {sin} con vacío o inválido al final" if sin else "") + ")."


@registrar
class Reemplazar(ModuloDialogo):
    ID, TITULO, SIN_RESULTADO = "REEMPLAZAR", "Buscar y reemplazar", True
    CAMPOS = [{"campo": "buscar", "etiqueta": "Buscar", "tipo": "texto"},
              {"campo": "nuevo", "etiqueta": "Reemplazar por (vacío = borrar)", "tipo": "texto"},
              {"campo": "col", "etiqueta": "En la columna (vacío = todas)", "tipo": "col", "opcional": True},
              {"campo": "completa", "etiqueta": "Solo celdas completas iguales al texto buscado", "tipo": "bool", "defecto": False},
              {"campo": "mayusculas", "etiqueta": "Distinguir mayúsculas y minúsculas", "tipo": "bool", "defecto": False}]

    @classmethod
    def ejecutar(cls, hoja, p, proyecto=None):
        j = p.get("col"); columna(hoja, j, "la columna", obligatoria=False)
        try:
            n = hoja.reemplazar(p.get("buscar") or "", p.get("nuevo") or "", [j] if j is not None else None,
                                bool(p.get("completa")), bool(p.get("mayusculas")))
        except ValueError as e:
            raise ErrorEntrada(str(e))
        return f"Reemplazos hechos: {n}." if n else "No se encontró el texto."
