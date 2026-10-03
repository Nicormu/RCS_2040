"""Motor de eventos aleatorios, decisiones y reglas de negocio."""
import random

# Lista de eventos. Cada opción produce consecuencias distintas.
# efectos: {recurso: cambio}, puntos: int
EVENTOS = [
    {
        "nombre": "Falla energética",
        "opciones": [
            {"texto": "Activar generador de respaldo", "efectos": {"Energía": +15, "Agua": -5}, "puntos": 10},
            {"texto": "Ignorar la falla", "efectos": {"Energía": -25}, "puntos": -10},
        ],
    },
    # TODO: agregar al menos 4-5 eventos más (agua, comunicaciones, transporte, sobreconsumo)
]


def generar_evento():
    """Elige un evento al azar; el azar debe afectar la lógica."""
    return random.choice(EVENTOS)


def procesar_evento(mision):
    """TODO: mostrar evento, leer decisión validada, aplicar efectos y puntos,
    registrar en el historial."""
    pass


def evaluar_reglas(mision):
    """TODO: reglas de negocio (energía < 20 -> crítico, agua < 15 -> alerta...)
    y actualizar mision['estado']."""
    pass


def algoritmo_propio(mision):
    """TODO: TU algoritmo (ej. índice de riesgo, prioridad de recursos,
    recomendación de la mejor opción). Documéntalo en el README."""
    pass
