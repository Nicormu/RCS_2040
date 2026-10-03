"""Motor de eventos aleatorios, decisiones y reglas de negocio."""
import random

import recursos
import reportes
from utilidades import leer_entero

META_EVENTOS = 10  # eventos necesarios para resolver la misión

# Peso de cada recurso en el índice de riesgo (suman 1.0)
PESOS = {"Energía": 0.4, "Agua": 0.3, "Alimentos": 0.2, "Comunicación": 0.1}

# "recurso" = recurso principal afectado (se usa para ponderar el azar)
EVENTOS = [
    {
        "nombre": "Falla energética", "recurso": "Energía",
        "opciones": [
            {"texto": "Activar generador de respaldo", "efectos": {"Energía": +15, "Agua": -5}, "puntos": 10},
            {"texto": "Ignorar la falla", "efectos": {"Energía": -25}, "puntos": -10},
        ],
    },
    {
        "nombre": "Contaminación del agua", "recurso": "Agua",
        "opciones": [
            {"texto": "Activar filtros de emergencia", "efectos": {"Agua": +10, "Energía": -8}, "puntos": 10},
            {"texto": "Usar el agua sin tratar", "efectos": {"Agua": -20, "Alimentos": -5}, "puntos": -10},
        ],
    },
    {
        "nombre": "Pérdida de comunicaciones", "recurso": "Comunicación",
        "opciones": [
            {"texto": "Reorientar la antena satelital", "efectos": {"Comunicación": +20, "Energía": -5}, "puntos": 10},
            {"texto": "Esperar a que se restablezca", "efectos": {"Comunicación": -20}, "puntos": -5},
        ],
    },
    {
        "nombre": "Fallo en el transporte de suministros", "recurso": "Alimentos",
        "opciones": [
            {"texto": "Enviar ruta alterna de emergencia", "efectos": {"Alimentos": +15, "Energía": -10}, "puntos": 10},
            {"texto": "Racionar las reservas", "efectos": {"Alimentos": -10}, "puntos": 3},
            {"texto": "No hacer nada", "efectos": {"Alimentos": -25}, "puntos": -10},
        ],
    },
    {
        "nombre": "Sobreconsumo de recursos", "recurso": "Energía",
        "opciones": [
            {"texto": "Aplicar recorte de consumo", "efectos": {"Energía": +10, "Comunicación": -5}, "puntos": 8},
            {"texto": "Mantener el consumo actual", "efectos": {"Energía": -15, "Agua": -10}, "puntos": -8},
        ],
    },
    {
        "nombre": "Tormenta solar", "recurso": "Comunicación",
        "opciones": [
            {"texto": "Activar el blindaje", "efectos": {"Energía": -12, "Comunicación": +5}, "puntos": 10},
            {"texto": "Apagar sistemas no esenciales", "efectos": {"Comunicación": -10, "Energía": +5}, "puntos": 4},
            {"texto": "Ignorar la alerta", "efectos": {"Comunicación": -25, "Energía": -15}, "puntos": -12},
        ],
    },
]


def generar_evento(mision=None):
    """Elige un evento al azar. Si hay misión, los recursos más bajos hacen
    más probable el evento que los afecta (el azar depende del estado)."""
    if mision is None:
        return random.choice(EVENTOS)
    pesos = [1 + (100 - mision["recursos"][e["recurso"]]) / 25 for e in EVENTOS]
    return random.choices(EVENTOS, weights=pesos, k=1)[0]


def aplicar_opcion(mision, evento, indice):
    """Aplica la opción elegida: efectos (con variación aleatoria ±3),
    puntos, contadores, historial y reglas. Devuelve la opción."""
    opcion = evento["opciones"][indice]
    for nombre, cambio in opcion["efectos"].items():
        variacion = random.randint(-3, 3)
        recursos.modificar_recurso(mision["recursos"], nombre, cambio + variacion)
    mision["puntos"] += opcion["puntos"]
    mision["eventos_procesados"] += 1
    if opcion["puntos"] > 0:
        mision["decisiones_correctas"] += 1
    else:
        mision["decisiones_incorrectas"] += 1
    reportes.registrar(
        mision, f"{evento['nombre']}: {opcion['texto']} ({opcion['puntos']:+d} pts)")
    evaluar_reglas(mision)
    reportes.guardar_progreso(mision)  # autoguardado
    return opcion


def procesar_evento(mision):
    """Versión consola: muestra evento, lee decisión validada y la aplica."""
    if mision["estado"] in ("RESUELTA", "FALLIDA"):
        print(f"  ⚠ La misión ya terminó ({mision['estado']}).")
        return
    evento = generar_evento(mision)
    print(f"\n⚠ EVENTO: {evento['nombre']}")
    for i, op in enumerate(evento["opciones"], start=1):
        print(f"  {i}. {op['texto']}")
    sugerida = recomendar_opcion(mision, evento) + 1
    print(f"  (Recomendación del sistema: opción {sugerida})")
    eleccion = leer_entero("Decisión: ", 1, len(evento["opciones"]))
    opcion = aplicar_opcion(mision, evento, eleccion - 1)
    print(f"→ {opcion['texto']} ({opcion['puntos']:+d} pts). Estado: {mision['estado']}")


def simular(mision, n):
    """Ejecuta n eventos automáticos con decisiones al azar. Devuelve cuántos se ejecutaron."""
    ejecutados = 0
    for _ in range(n):
        if mision["estado"] in ("RESUELTA", "FALLIDA"):
            break
        evento = generar_evento(mision)
        aplicar_opcion(mision, evento, random.randrange(len(evento["opciones"])))
        ejecutados += 1
    return ejecutados


def evaluar_reglas(mision):
    """Reglas de negocio que actualizan mision['estado'] automáticamente."""
    r = mision["recursos"]
    if mision["estado"] in ("RESUELTA", "FALLIDA"):
        return
    if min(r.values()) == 0:
        mision["estado"] = "FALLIDA"
    elif r["Energía"] < 20:
        mision["estado"] = "CRÍTICA"
    elif r["Agua"] < 15 or min(r.values()) < 30:
        mision["estado"] = "ALERTA"
    elif mision["eventos_procesados"] >= META_EVENTOS:
        mision["estado"] = "RESUELTA"
    else:
        mision["estado"] = "OPERATIVA"


# ---------- ALGORITMO PROPIO: índice de riesgo ponderado ----------
def indice_riesgo(estado_recursos):
    """riesgo = suma(peso_i * (100 - valor_i)). Rango 0 (ideal) a 100 (colapso)."""
    return sum(PESOS[n] * (100 - v) for n, v in estado_recursos.items())


def algoritmo_propio(mision):
    """Devuelve (riesgo, nivel) de la misión actual."""
    riesgo = indice_riesgo(mision["recursos"])
    if riesgo < 25:
        nivel = "BAJO"
    elif riesgo < 50:
        nivel = "MEDIO"
    else:
        nivel = "ALTO"
    return round(riesgo, 1), nivel


def recomendar_opcion(mision, evento):
    """Índice de la opción que deja el menor riesgo tras aplicar sus efectos."""
    mejor, menor = 0, float("inf")
    for i, op in enumerate(evento["opciones"]):
        simulado = dict(mision["recursos"])
        for nombre, cambio in op["efectos"].items():
            recursos.modificar_recurso(simulado, nombre, cambio)
        riesgo = indice_riesgo(simulado)
        if riesgo < menor:
            mejor, menor = i, riesgo
    return mejor