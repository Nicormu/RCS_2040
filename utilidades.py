"""Funciones para validar lo que escribe el usuario (se usan en varios módulos)."""


def leer_texto(mensaje, minimo=1):
    """Pide un texto y vuelve a preguntar hasta que tenga al menos `minimo` caracteres."""
    while True:
        valor = input(mensaje).strip()
        if len(valor) >= minimo:
            return valor
        print(f"  Entrada inválida: mínimo {minimo} carácter(es).")


def leer_entero(mensaje, minimo, maximo):
    """Pide un número entero entre `minimo` y `maximo` (ambos incluidos)."""
    while True:
        valor = input(mensaje)
        try:
            numero = int(valor)
        except ValueError:
            print("  Debes escribir un número entero.")
            continue
        if minimo <= numero <= maximo:
            return numero
        print(f"  Fuera de rango ({minimo}-{maximo}).")