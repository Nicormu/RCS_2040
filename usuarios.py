"""Módulo de autenticación de operadores."""
from utilidades import leer_texto

MAX_INTENTOS = 3

# Diccionario: usuario -> contraseña  (TODO opcional: rol, hash, archivo)
operadores = {"admin": "1234"}


def crear_operador():
    """TODO: pedir usuario y contraseña, validar que no exista, guardarlo."""
    pass


def iniciar_sesion():
    """TODO: hasta MAX_INTENTOS intentos. Devolver el usuario o None."""
    pass
