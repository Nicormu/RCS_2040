"""Historial, estadísticas, reporte final y guardado del progreso en CSV."""
import csv
import json
import os
from datetime import datetime


def registrar(mision, accion):
    """Agrega una línea al historial de la misión."""
    mision["historial"].append(accion)


def calcular_estadisticas(mision):
    """Devuelve un diccionario con los números más importantes de la misión."""
    total = mision["eventos_procesados"]
    buenas = mision["decisiones_correctas"]
    return {
        "Dificultad": mision.get("dificultad", "Normal"),
        "Eventos": total,
        "Decisiones correctas": buenas,
        "Decisiones incorrectas": mision["decisiones_incorrectas"],
        "Recursos (%)": dict(mision["recursos"]),
        "Puntos": mision["puntos"],
        # Evitamos dividir entre cero si todavía no hubo eventos
        "Eficiencia (%)": round(100 * buenas / total, 1) if total else 0.0,
        "Estado": mision["estado"],
    }


def mostrar_historial(mision):
    """Imprime el historial numerado."""
    print("\n--- HISTORIAL ---")
    if not mision["historial"]:
        print("(vacío)")
    for i, accion in enumerate(mision["historial"], start=1):
        print(f"{i}. {accion}")


def texto_reporte(mision):
    """Arma el reporte final como un solo texto."""
    est = calcular_estadisticas(mision)
    lineas = [f"REPORTE RCS - Operador: {mision['operador']}", "-" * 40]
    for clave, valor in est.items():
        lineas.append(f"{clave}: {valor}")
    lineas += ["", "Historial:"]
    lineas += [f"{i}. {a}" for i, a in enumerate(mision["historial"], start=1)]
    return "\n".join(lineas)


def generar_reporte(mision, guardar=True):
    """Imprime el reporte y, si guardar=True, lo escribe en reporte_rcs.txt."""
    texto = texto_reporte(mision)
    print("\n" + texto)
    if guardar:
        with open("reporte_rcs.txt", "w", encoding="utf-8") as archivo:
            archivo.write(texto)
        print("\nReporte guardado en reporte_rcs.txt")


# ---------- Guardado de progreso (CSV) ----------

# Números de la misión que se guardan tal cual
CONTADORES = ("puntos", "eventos_procesados", "decisiones_correctas", "decisiones_incorrectas")


def nombre_seguro(operador):
    """Deja solo letras, números, - y _ para poder usar el nombre en un archivo."""
    return "".join(c for c in operador if c.isalnum() or c in "-_")


def ruta_progreso(operador):
    """Nombre del archivo de progreso de un operador."""
    return f"progreso_{nombre_seguro(operador)}.csv"


def ruta_historial(operador):
    """Nombre del archivo JSON con el historial de un operador."""
    return f"historial_{nombre_seguro(operador)}.json"


def nuevo_id():
    """Identificador de una misión: la fecha y hora en que se creó."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- Historial por usuario (JSON) ----------
# Cada operador tiene su propio historial_<usuario>.json. A diferencia del CSV de
# progreso (que solo guarda la misión actual), aquí se acumulan todas sus misiones.

def cargar_historial(operador):
    """Devuelve la lista de misiones guardadas del operador (vacía si no hay o está dañado)."""
    try:
        with open(ruta_historial(operador), encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return []
    misiones = datos.get("misiones") if isinstance(datos, dict) else None
    return misiones if isinstance(misiones, list) else []


def guardar_historial(mision):
    """Guarda la misión en el historial de su operador.
    Si ya estaba guardada (mismo id) se actualiza; si no, se agrega al final."""
    mision.setdefault("id", nuevo_id())
    misiones = cargar_historial(mision["operador"])
    entrada = {"id": mision["id"], "dificultad": mision.get("dificultad", "Normal"),
               "estado": mision["estado"], "puntos": mision["puntos"],
               "acciones": list(mision["historial"])}
    for i, m in enumerate(misiones):
        if isinstance(m, dict) and m.get("id") == entrada["id"]:
            misiones[i] = entrada
            break
    else:
        misiones.append(entrada)
    with open(ruta_historial(mision["operador"]), "w", encoding="utf-8") as f:
        json.dump({"operador": mision["operador"], "misiones": misiones}, f,
                  indent=2, ensure_ascii=False)


def existe_progreso(operador):
    """True si el operador tiene una misión guardada."""
    return os.path.exists(ruta_progreso(operador))


def borrar_progreso(operador):
    """Borra el progreso guardado. Devuelve True si existía."""
    if existe_progreso(operador):
        os.remove(ruta_progreso(operador))
        return True
    return False


def guardar_progreso(mision):
    """Guarda la misión en un CSV (tipo, clave, valor) y actualiza el historial JSON del usuario."""
    with open(ruta_progreso(mision["operador"]), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["tipo", "clave", "valor"])
        w.writerow(["meta", "operador", mision["operador"]])
        w.writerow(["meta", "estado", mision["estado"]])
        w.writerow(["meta", "dificultad", mision.get("dificultad", "Normal")])
        w.writerow(["meta", "id", mision.get("id", "")])
        for c in CONTADORES:
            w.writerow(["contador", c, mision[c]])
        for nombre, valor in mision["recursos"].items():
            w.writerow(["recurso", nombre, valor])
        for i, accion in enumerate(mision["historial"], start=1):
            w.writerow(["historial", i, accion])
    guardar_historial(mision)  # el historial también queda en el JSON del usuario


def cargar_progreso(operador):
    """Lee el CSV y reconstruye la misión. Devuelve None si no existe o está dañado."""
    if not existe_progreso(operador):
        return None
    mision = {"operador": operador, "recursos": {}, "estado": "OPERATIVA",
              "dificultad": "Normal", "historial": []}
    try:
        with open(ruta_progreso(operador), newline="", encoding="utf-8-sig") as f:
            for fila in csv.DictReader(f):
                tipo, clave, valor = fila["tipo"], fila["clave"], fila["valor"]
                if tipo == "meta" and clave in ("estado", "dificultad", "id"):
                    mision[clave] = valor
                elif tipo == "contador":
                    mision[clave] = int(valor)
                elif tipo == "recurso":
                    mision["recursos"][clave] = int(valor)
                elif tipo == "historial":
                    mision["historial"].append(valor)
        # Si faltan datos básicos, el archivo no sirve
        if not mision["recursos"] or any(c not in mision for c in CONTADORES):
            return None
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not mision.get("id"):  # progreso guardado antes de que existieran los ids
        mision["id"] = nuevo_id()
    return mision