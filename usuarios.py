"""Módulo de autenticación de operadores."""
from utilidades import leer_texto

MAX_INTENTOS = 3

# Diccionario: usuario -> contraseña
operadores = {"admin": "1234"}


def crear_operador():
    """Pide usuario y contraseña, valida que no exista y lo guarda."""
    usuario = leer_texto("Nuevo usuario (mín. 3 caracteres): ", 3)
    if usuario in operadores:
        print("  ⚠ Ese operador ya existe.")
        return False
    clave = leer_texto("Contraseña (mín. 4 caracteres): ", 4)
    operadores[usuario] = clave
    print(f"Operador '{usuario}' creado.")
    return True


def iniciar_sesion():
    """Hasta MAX_INTENTOS intentos. Devuelve el usuario o None."""
    for intento in range(1, MAX_INTENTOS + 1):
        usuario = leer_texto("Usuario: ")
        clave = leer_texto("Contraseña: ")
        if operadores.get(usuario) == clave:
            print(f"Bienvenido, {usuario}.")
            return usuario
        print(f"  ⚠ Credenciales incorrectas ({intento}/{MAX_INTENTOS}).")
    print("Acceso bloqueado por demasiados intentos.")
    return None