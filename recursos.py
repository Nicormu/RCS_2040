"""Sistema de recursos de la misión."""
import random

NOMBRES = ("Energía", "Agua", "Alimentos", "Comunicación")

# Rango (mínimo, máximo) del valor inicial aleatorio según la dificultad
RANGOS_INICIO = {"Fácil": (70, 100), "Normal": (55, 90), "Difícil": (40, 75)}


def crear_recursos(dificultad="Normal"):
    """Devuelve los recursos con un valor inicial aleatorio según la dificultad."""
    bajo, alto = RANGOS_INICIO.get(dificultad, RANGOS_INICIO["Normal"])
    return {nombre: random.randint(bajo, alto) for nombre in NOMBRES}


def modificar_recurso(recursos, nombre, cambio):
    """Aplica el cambio dejando el recurso siempre entre 0 y 100."""
    recursos[nombre] = max(0, min(100, recursos[nombre] + cambio))


def mostrar_recursos(recursos):
    """Imprime los recursos con barras de '█'."""
    print("\n--- RECURSOS ---")
    for nombre, valor in recursos.items():
        llenos = valor // 5
        barra = "█" * llenos + "░" * (20 - llenos)
        print(f"{nombre:<13} {barra} {valor:>3}%")