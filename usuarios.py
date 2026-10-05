"""Login y creación de operadores, con un rol simple (admin u operador).
Los operadores se guardan en usuarios.json para que no se pierdan al cerrar el programa."""
import json
import os

from utilidades import leer_texto

MAX_INTENTOS = 3

# El archivo queda junto a este módulo, sin importar desde dónde se ejecute el programa
ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usuarios.json")

# Roles especiales. Quien no esté aquí es "operador".
ROLES = {
        "admin": "admin",
        "nico": "admin",
        }


def cargar_operadores():
    """Lee usuarios.json y devuelve el diccionario usuario -> contraseña.
    Si el archivo no existe o está dañado, empieza solo con el admin."""
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        datos = {}
    if not isinstance(datos, dict) or not all(isinstance(v, str) for v in datos.values()):
        datos = {}
    datos.setdefault("admin", "1234")  # el admin siempre existe
    return datos


def guardar_operadores():
    """Escribe todos los operadores en usuarios.json."""
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(operadores, f, indent=2, ensure_ascii=False)


# usuario -> contraseña (se carga del archivo al iniciar)
operadores = cargar_operadores()


def registrar(usuario, clave):
    """Agrega un operador nuevo y lo guarda en el archivo."""
    operadores[usuario] = clave
    guardar_operadores()


def rol(usuario):
    """Devuelve 'admin' u 'operador'."""
    return ROLES.get(usuario, "operador")


def es_admin(usuario):
    """Solo el admin puede ver los operadores y borrar su progreso."""
    return rol(usuario) == "admin"


def crear_operador():
    """Pide usuario y contraseña, revisa que no exista y lo guarda. Devuelve True si lo creó."""
    usuario = leer_texto("Nuevo usuario (mín. 3 caracteres): ", 3)
    if usuario in operadores:
        print("  Ese operador ya existe.")
        return False
    clave = leer_texto("Contraseña (mín. 4 caracteres): ", 4)
    registrar(usuario, clave)
    print(f"Operador '{usuario}' creado.")
    return True


def iniciar_sesion():
    """Da hasta MAX_INTENTOS oportunidades. Devuelve el usuario o None si se bloquea."""
    for intento in range(1, MAX_INTENTOS + 1):
        usuario = leer_texto("Usuario: ")
        clave = leer_texto("Contraseña: ")
        if operadores.get(usuario) == clave:
            print(f"Bienvenido, {usuario}.")
            return usuario
        print(f"  Credenciales incorrectas ({intento}/{MAX_INTENTOS}).")
    print("Acceso bloqueado por demasiados intentos.")
    return None