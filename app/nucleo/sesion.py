"""Ventana de sesión: bitácora de lo que ocurre en el programa."""
from datetime import datetime


class Sesion:
    def __init__(self):
        self.entradas = []

    def registrar(self, texto, tipo="info"):
        e = {"hora": datetime.now().strftime("%H:%M:%S"), "texto": texto, "tipo": tipo}
        self.entradas.append(e)
        return e
