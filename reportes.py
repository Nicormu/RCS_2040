"""Historial, estadísticas, reporte final y guardado de progreso (CSV)."""
import csv
import os


def registrar(mision, accion):
    """Agrega una acción al historial."""
    mision["historial"].append(accion)


def calcular_estadisticas(mision):
    """Devuelve un diccionario con las estadísticas de la misión."""
    total = mision["eventos_procesados"]
    buenas = mision["decisiones_correctas"]
    return {
        "Dificultad": mision.get("dificultad", "Normal"),
        "Eventos": total,
        "Decisiones correctas": buenas,
        "Decisiones incorrectas": mision["decisiones_incorrectas"],
        "Recursos (%)": dict(mision["recursos"]),
        "Puntos": mision["puntos"],
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
    """Construye el reporte final como texto."""
    est = calcular_estadisticas(mision)
    lineas = [f"REPORTE RCS - Operador: {mision['operador']}", "-" * 40]
    for clave, valor in est.items():
        lineas.append(f"{clave}: {valor}")
    lineas += ["", "Historial:"]
    lineas += [f"{i}. {a}" for i, a in enumerate(mision["historial"], start=1)]
    return "\n".join(lineas)


def generar_reporte(mision, guardar=True):
    """Imprime el reporte y opcionalmente lo guarda en TXT."""
    texto = texto_reporte(mision)
    print("\n" + texto)
    if guardar:
        with open("reporte_rcs.txt", "w", encoding="utf-8") as archivo:
            archivo.write(texto)
        print("\nReporte guardado en reporte_rcs.txt")


# ---------- Guardado de progreso (CSV) ----------
CONTADORES = ("puntos", "eventos_procesados", "decisiones_correctas", "decisiones_incorrectas")


def ruta_progreso(operador):
    """Archivo de progreso propio de cada operador."""
    seguro = "".join(c for c in operador if c.isalnum() or c in "-_")
    return f"progreso_{seguro}.csv"


def existe_progreso(operador):
    return os.path.exists(ruta_progreso(operador))


def borrar_progreso(operador):
    """Elimina el progreso guardado del operador. Devuelve True si existía."""
    if existe_progreso(operador):
        os.remove(ruta_progreso(operador))
        return True
    return False


def guardar_progreso(mision):
    """Guarda todo el estado de la misión en un CSV (tipo, clave, valor)."""
    with open(ruta_progreso(mision["operador"]), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["tipo", "clave", "valor"])
        w.writerow(["meta", "operador", mision["operador"]])
        w.writerow(["meta", "estado", mision["estado"]])
        w.writerow(["meta", "dificultad", mision.get("dificultad", "Normal")])
        for c in CONTADORES:
            w.writerow(["contador", c, mision[c]])
        for nombre, valor in mision["recursos"].items():
            w.writerow(["recurso", nombre, valor])
        for i, accion in enumerate(mision["historial"], start=1):
            w.writerow(["historial", i, accion])


def cargar_progreso(operador):
    """Reconstruye la misión desde el CSV. Devuelve None si no existe o está dañado."""
    if not existe_progreso(operador):
        return None
    mision = {"operador": operador, "recursos": {}, "estado": "OPERATIVA",
              "dificultad": "Normal", "historial": []}
    try:
        with open(ruta_progreso(operador), newline="", encoding="utf-8-sig") as f:
            for fila in csv.DictReader(f):
                tipo, clave, valor = fila["tipo"], fila["clave"], fila["valor"]
                if tipo == "meta" and clave in ("estado", "dificultad"):
                    mision[clave] = valor
                elif tipo == "contador":
                    mision[clave] = int(valor)
                elif tipo == "recurso":
                    mision["recursos"][clave] = int(valor)
                elif tipo == "historial":
                    mision["historial"].append(valor)
        if not mision["recursos"] or any(c not in mision for c in CONTADORES):
            return None
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return mision