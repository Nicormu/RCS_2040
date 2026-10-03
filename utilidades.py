"""Funciones de validación de entradas (reutilizables en todos los módulos)."""


def leer_texto(mensaje, minimo=1):
    """Pide un texto y repite hasta que no esté vacío."""
    while True:
        valor = input(mensaje).strip()
        if len(valor) >= minimo:
            return valor
        print(f"  ⚠ Entrada inválida: mínimo {minimo} carácter(es).")


def leer_entero(mensaje, minimo, maximo):
    """Pide un entero dentro de [minimo, maximo]."""
    while True:
        valor = input(mensaje)
        try:
            numero = int(valor)
        except ValueError:
            print(" Debes escribir un número entero.")
            continue
        if minimo <= numero <= maximo:
            break
        print(f" Fuera de rango ({minimo}-{maximo}).")

    return numero