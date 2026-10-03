"""Sistema de recursos de la misión."""

RECURSOS_INICIALES = {"Energía": 100, "Agua": 80, "Alimentos": 70, "Comunicación": 90}


def crear_recursos():
    """Devuelve una copia de los recursos iniciales (o valores aleatorios)."""
    return dict(RECURSOS_INICIALES)


def modificar_recurso(recursos, nombre, cambio):
    """TODO: aplicar el cambio sin dejar el recurso < 0 ni > 100."""
    pass


def mostrar_recursos(recursos):
    """TODO: imprimir los recursos (puedes usar barras con '█')."""
    pass
