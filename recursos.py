"""Sistema de recursos de la misión."""

RECURSOS_INICIALES = {"Energía": 100, "Agua": 80, "Alimentos": 70, "Comunicación": 90}


def crear_recursos():
    """Devuelve una copia de los recursos iniciales."""
    return dict(RECURSOS_INICIALES)


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