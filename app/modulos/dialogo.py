"""Clase base de los módulos de tipo «diálogo sobre columnas de la hoja + resultado»."""
from .base import ErrorEntrada


class ModuloDialogo:
    ID = ""; TITULO = ""; VISTA = "dialogo"
    CAMPOS = []   # [{campo, etiqueta, tipo: col|numero|opcion|bool|texto, filtro, opcional, rol, defecto, opciones}]

    HOJA_VACIA_OK = False

    @classmethod
    def dialogo(cls, hoja, proyecto=None):
        """Especificación del diálogo con valores por omisión tomados del rol de las columnas."""
        usados, campos = set(), []
        for c in cls.CAMPOS:
            c = dict(c)
            if c["tipo"] == "col" and c.get("rol") and "defecto" not in c:
                for j, col in enumerate(hoja.columnas):
                    if col.rol in c["rol"] and j not in usados and (not c.get("filtro") or col.tipo == c["filtro"]):
                        c["defecto"] = j; usados.add(j); break
            campos.append(c)
        cols = [{"j": j, "etiqueta": f"C{j + 1}", "nombre": c.nombre, "tipo": c.tipo}
                for j, c in enumerate(hoja.columnas) if c.tipo]
        return {"id": cls.ID, "titulo": cls.TITULO, "campos": campos, "columnas": cols}

    @classmethod
    def leer(cls, p, campo, defecto=None):
        v = p.get(campo, defecto)
        return defecto if v in ("", None) else v

    @classmethod
    def numero(cls, p, campo, etiqueta, opcional=True, minimo=None, maximo=None):
        v = p.get(campo)
        if v in (None, ""):
            if opcional: return None
            raise ErrorEntrada(f"Falta {etiqueta}.")
        try:
            x = float(str(v).replace(",", "."))
        except ValueError:
            raise ErrorEntrada(f"{etiqueta} debe ser un número.")
        if minimo is not None and x <= minimo or maximo is not None and x >= maximo:
            raise ErrorEntrada(f"{etiqueta} está fuera del rango permitido.")
        return x
