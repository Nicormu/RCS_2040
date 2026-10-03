"""Motor de eventos aleatorios, decisiones y reglas de negocio."""
import random

import recursos
import reportes
from utilidades import leer_entero

FINALES = ("RESUELTA", "FALLIDA")
FALLO_PUNTOS = -5  # puntos que se reciben cuando una acción riesgosa falla

# Parámetros por dificultad:
#  meta     = eventos necesarios para resolver la misión
#  desgaste = consumo pasivo (mín, máx) que pierde CADA recurso tras cada evento
#  castigo  = multiplicador de los efectos negativos
#  azar     = variación aleatoria ± aplicada a cada efecto
#  suerte   = ajuste a la probabilidad de éxito de las acciones riesgosas
#  bonus    = puntos extra al resolver la misión
DIFICULTADES = {
    "Fácil":   {"meta": 8,  "desgaste": (0, 1), "castigo": 1.0,  "azar": 2, "suerte": +0.10, "bonus": 10},
    "Normal":  {"meta": 10, "desgaste": (0, 2), "castigo": 1.25, "azar": 3, "suerte": 0.0,   "bonus": 20},
    "Difícil": {"meta": 12, "desgaste": (0, 3), "castigo": 1.4,  "azar": 4, "suerte": -0.10, "bonus": 40},
}

# Peso de cada recurso en el índice de riesgo (suman 1.0)
PESOS = {"Energía": 0.4, "Agua": 0.3, "Alimentos": 0.2, "Comunicación": 0.1}


def op(texto, puntos, prob=1.0, **efectos):
    """Crea una opción de evento. prob < 1 = acción riesgosa (puede fallar)."""
    return {"texto": texto, "efectos": efectos, "puntos": puntos, "prob": prob}


# "recurso" = recurso principal afectado (se usa para ponderar el azar)
EVENTOS = [
    {"nombre": "Falla energética", "recurso": "Energía", "opciones": [
        op("Activar generador de respaldo", 10, Energía=+15, Agua=-5),
        op("Redistribuir la carga entre módulos", 6, Energía=+8, Comunicación=-4),
        op("Reiniciar el reactor principal (riesgoso)", 12, 0.6, Energía=+25, Alimentos=-5),
        op("Ignorar la falla", -10, Energía=-25),
    ]},
    {"nombre": "Contaminación del agua", "recurso": "Agua", "opciones": [
        op("Activar filtros de emergencia", 10, Agua=+10, Energía=-8),
        op("Hervir y racionar el agua", 6, Agua=+6, Energía=-10),
        op("Inyectar purificante químico (riesgoso)", 11, 0.65, Agua=+20, Alimentos=-8),
        op("Usar el agua sin tratar", -10, Agua=-20, Alimentos=-5),
    ]},
    {"nombre": "Pérdida de comunicaciones", "recurso": "Comunicación", "opciones": [
        op("Reorientar la antena satelital", 10, Comunicación=+20, Energía=-5),
        op("Usar el canal de radio de respaldo", 6, Comunicación=+10, Energía=-2),
        op("Reiniciar el módulo de comunicaciones (riesgoso)", 10, 0.6, Comunicación=+25, Energía=-10),
        op("Esperar a que se restablezca", -5, Comunicación=-20),
    ]},
    {"nombre": "Fallo en el transporte de suministros", "recurso": "Alimentos", "opciones": [
        op("Enviar ruta alterna de emergencia", 10, Alimentos=+15, Energía=-10),
        op("Cultivar en el invernadero", 6, Alimentos=+8, Agua=-8),
        op("Racionar las reservas", 3, Alimentos=-5),
        op("No hacer nada", -10, Alimentos=-25),
    ]},
    {"nombre": "Sobreconsumo de recursos", "recurso": "Energía", "opciones": [
        op("Aplicar recorte de consumo", 8, Energía=+10, Comunicación=-5),
        op("Apagar módulos secundarios", 7, Energía=+14, Alimentos=-6),
        op("Mantener el consumo actual", -8, Energía=-15, Agua=-10),
    ]},
    {"nombre": "Tormenta solar", "recurso": "Comunicación", "opciones": [
        op("Activar el blindaje", 10, Energía=-12, Comunicación=+5),
        op("Apagar sistemas no esenciales", 4, Comunicación=-10, Energía=+5),
        op("Desviar energía a los paneles (riesgoso)", 8, 0.6, Energía=+15, Comunicación=-5),
        op("Ignorar la alerta", -12, Comunicación=-25, Energía=-15),
    ]},
    {"nombre": "Fuga en el sistema de refrigeración", "recurso": "Agua", "opciones": [
        op("Sellar el conducto con el robot de mantenimiento", 9, Agua=+8, Energía=-6),
        op("Cerrar la válvula principal", 5, Agua=+4, Alimentos=-8),
        op("Recolectar y reciclar el agua", 8, Agua=+12, Energía=-10),
        op("Dejar que se drene", -10, Agua=-22, Energía=-4),
    ]},
    {"nombre": "Plaga en el cultivo hidropónico", "recurso": "Alimentos", "opciones": [
        op("Aplicar bioprotector", 9, Alimentos=+12, Agua=-6),
        op("Aislar y eliminar la zona infectada", 5, Alimentos=-4),
        op("Tratamiento experimental (riesgoso)", 11, 0.55, Alimentos=+22, Energía=-8),
        op("Ignorar la plaga", -10, Alimentos=-22, Agua=-5),
    ]},
    {"nombre": "Impacto de meteorito en los paneles", "recurso": "Energía", "opciones": [
        op("Reparar los paneles con el dron", 9, Energía=+12, Comunicación=-4),
        op("Reasignar las baterías de emergencia", 6, Energía=+8, Agua=-4),
        op("Salida de reparación manual (riesgoso)", 10, 0.6, Energía=+20, Alimentos=-6),
        op("Posponer la reparación", -9, Energía=-18, Comunicación=-6),
    ]},
    {"nombre": "Interferencia en la red de sensores", "recurso": "Comunicación", "opciones": [
        op("Recalibrar los sensores", 8, Comunicación=+12, Energía=-5),
        op("Instalar un repetidor temporal", 9, Comunicación=+18, Energía=-9),
        op("Operar en modo manual", 4, Comunicación=+5, Energía=+3),
        op("Ignorar las lecturas", -8, Comunicación=-18, Agua=-6),
    ]},
    {"nombre": "Cámara de frío averiada", "recurso": "Alimentos", "opciones": [
        op("Mover los alimentos a otro módulo", 8, Alimentos=+10, Energía=-8),
        op("Consumir primero lo perecedero", 5, Alimentos=+4, Agua=-4),
        op("Reparar la cámara de frío (riesgoso)", 10, 0.65, Alimentos=+18, Energía=-12),
        op("Descartar lo dañado", -4, Alimentos=-18),
    ]},
    {"nombre": "Intrusión informática", "recurso": "Comunicación", "opciones": [
        op("Aislar la red y restaurar copias", 8, Comunicación=-5, Energía=+6),
        op("Contraataque digital (riesgoso)", 10, 0.5, Comunicación=+15, Energía=-10),
        op("Apagar el módulo comprometido", 5, Comunicación=-12, Energía=+8),
        op("Ignorar la intrusión", -10, Comunicación=-20, Energía=-12),
    ]},
    {"nombre": "Cápsula de suministros a la deriva", "recurso": "Alimentos", "opciones": [
        op("Abrirla de inmediato", 8, Alimentos=+15, Agua=+8),
        op("Escanearla antes de abrir", 10, Alimentos=+10, Agua=+5, Energía=-6),
        op("Dejarla sin abrir", -2, Alimentos=-3),
    ]},
]


def config_mision(mision):
    """Parámetros de la dificultad de la misión (Normal si no se reconoce)."""
    return DIFICULTADES.get(mision.get("dificultad"), DIFICULTADES["Normal"])


def generar_evento(mision=None):
    """Elige un evento al azar y baraja el orden de sus opciones.
    Si hay misión, los recursos más bajos hacen más probable el evento que los
    afecta (el azar depende del estado). Devuelve una copia: EVENTOS no cambia."""
    if mision is None:
        base = random.choice(EVENTOS)
    else:
        pesos = [1 + (100 - mision["recursos"][e["recurso"]]) / 25 for e in EVENTOS]
        base = random.choices(EVENTOS, weights=pesos, k=1)[0]
    opciones = list(base["opciones"])
    random.shuffle(opciones)  # el orden de las respuestas cambia cada vez
    return {"nombre": base["nombre"], "recurso": base["recurso"], "opciones": opciones}


def aplicar_opcion(mision, evento, indice):
    """Aplica la opción elegida y devuelve {"texto", "puntos", "exito"}.
    - Las acciones riesgosas (prob < 1) pueden fallar: no dan sus mejoras, pagan
      sus costos y restan FALLO_PUNTOS.
    - Los efectos negativos se multiplican por 'castigo' y todos llevan azar ±.
    - Después de cada evento todos los recursos pierden un desgaste aleatorio."""
    cfg = config_mision(mision)
    opcion = evento["opciones"][indice]
    prob = opcion.get("prob", 1.0)
    exito = prob >= 1 or random.random() < min(1.0, prob + cfg["suerte"])
    puntos = opcion["puntos"] if exito else FALLO_PUNTOS

    for nombre, cambio in opcion["efectos"].items():
        if not exito and cambio > 0:
            continue  # el remedio falló: sin mejora, pero los costos sí se pagan
        if cambio < 0:
            cambio = round(cambio * cfg["castigo"])
        cambio += random.randint(-cfg["azar"], cfg["azar"])
        recursos.modificar_recurso(mision["recursos"], nombre, cambio)
    for nombre in mision["recursos"]:  # desgaste pasivo de cada turno
        recursos.modificar_recurso(mision["recursos"], nombre, -random.randint(*cfg["desgaste"]))

    mision["puntos"] += puntos
    mision["eventos_procesados"] += 1
    if puntos > 0:
        mision["decisiones_correctas"] += 1
    else:
        mision["decisiones_incorrectas"] += 1
    aviso = "" if exito else " ¡FALLÓ!"
    reportes.registrar(mision, f"{evento['nombre']}: {opcion['texto']} ({puntos:+d} pts){aviso}")
    evaluar_reglas(mision)
    reportes.guardar_progreso(mision)  # autoguardado
    return {"texto": opcion["texto"], "puntos": puntos, "exito": exito}


def procesar_evento(mision):
    """Versión consola: muestra evento, lee decisión validada y la aplica."""
    if mision["estado"] in FINALES:
        print(f"  ⚠ La misión ya terminó ({mision['estado']}).")
        return
    evento = generar_evento(mision)
    print(f"\n⚠ EVENTO: {evento['nombre']}")
    for i, o in enumerate(evento["opciones"], start=1):
        print(f"  {i}. {o['texto']}")
    eleccion = leer_entero("Decisión: ", 1, len(evento["opciones"]))
    res = aplicar_opcion(mision, evento, eleccion - 1)
    aviso = "" if res["exito"] else " ¡La acción FALLÓ!"
    print(f"→ {res['texto']} ({res['puntos']:+d} pts).{aviso} Estado: {mision['estado']}")


def simular(mision, n):
    """Ejecuta n eventos automáticos con decisiones al azar. Devuelve cuántos se ejecutaron."""
    ejecutados = 0
    for _ in range(n):
        if mision["estado"] in FINALES:
            break
        evento = generar_evento(mision)
        aplicar_opcion(mision, evento, random.randrange(len(evento["opciones"])))
        ejecutados += 1
    return ejecutados


def evaluar_reglas(mision):
    """Reglas de negocio que actualizan mision['estado'] automáticamente.
    Orden de prioridad: FALLIDA > CRÍTICA > ALERTA > RESUELTA > OPERATIVA.
    Solo se resuelve si, al llegar a la meta, ningún recurso está en alerta."""
    if mision["estado"] in FINALES:
        return
    r = mision["recursos"]
    cfg = config_mision(mision)
    if min(r.values()) == 0:
        mision["estado"] = "FALLIDA"
        reportes.registrar(mision, "MISIÓN FALLIDA: un recurso llegó a 0")
    elif r["Energía"] < 20:
        mision["estado"] = "CRÍTICA"
    elif r["Agua"] < 15 or min(r.values()) < 30:
        mision["estado"] = "ALERTA"
    elif mision["eventos_procesados"] >= cfg["meta"]:
        mision["estado"] = "RESUELTA"
        mision["puntos"] += cfg["bonus"]
        reportes.registrar(mision, f"MISIÓN RESUELTA (+{cfg['bonus']} pts de bonus)")
    else:
        mision["estado"] = "OPERATIVA"


# ---------- ALGORITMO PROPIO: índice de riesgo ponderado ----------
def indice_riesgo(estado_recursos):
    """Índice de riesgo ponderado de la misión.

    Fórmula:  riesgo = Σ peso_i × (100 − valor_i)
    - peso_i  : importancia del recurso (PESOS; Energía 0.4, Agua 0.3,
                Alimentos 0.2, Comunicación 0.1; suman 1.0).
    - 100 − v : cuánto le falta al recurso para estar completo.
    Rango: 0 (todos al 100 %) a 100 (todos en 0). Complejidad O(n), n = recursos.
    Ejemplo: Energía 100, Agua 80, Alimentos 70, Comunicación 90
             → 0.4·0 + 0.3·20 + 0.2·30 + 0.1·10 = 13.0
    """
    return sum(PESOS[n] * (100 - v) for n, v in estado_recursos.items())


def algoritmo_propio(mision):
    """Devuelve (riesgo, nivel): BAJO (<25), MEDIO (25 a <50) o ALTO (≥50)."""
    riesgo = indice_riesgo(mision["recursos"])
    if riesgo < 25:
        nivel = "BAJO"
    elif riesgo < 50:
        nivel = "MEDIO"
    else:
        nivel = "ALTO"
    return round(riesgo, 1), nivel