"""Recursos de la misión: Energía, Agua, Alimentos y Comunicación."""
import random

NOMBRES = ("Energía", "Agua", "Alimentos", "Comunicación")

# Rango del valor inicial aleatorio según la dificultad
RANGOS_INICIO = {"Fácil": (70, 100), "Normal": (55, 90), "Difícil": (40, 75)}


def crear_recursos(dificultad="Normal"):
    """Devuelve un diccionario con cada recurso en un valor inicial al azar."""
    bajo, alto = RANGOS_INICIO.get(dificultad, RANGOS_INICIO["Normal"])
    return {nombre: random.randint(bajo, alto) for nombre in NOMBRES}


def modificar_recurso(recursos, nombre, cambio):
    """Suma `cambio` al recurso sin dejarlo salir del rango 0-100."""
    recursos[nombre] = max(0, min(100, recursos[nombre] + cambio))


def mostrar_recursos(recursos):
    """Imprime cada recurso con una barra hecha de caracteres (cada bloque vale 5%)."""
    print("\n--- RECURSOS ---")
    for nombre, valor in recursos.items():
        llenos = valor // 5
        barra = "█" * llenos + "░" * (20 - llenos)
        print(f"{nombre:<13} {barra} {valor:>3}%")