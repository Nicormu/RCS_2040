"""ROBOYORK CONTROL SYSTEM (RCS) - programa principal."""
from utilidades import leer_entero
import usuarios
import recursos
import eventos
import reportes

ESTADOS = ["INICIALIZANDO", "OPERATIVA", "ALERTA", "CRÍTICA", "RESUELTA", "FALLIDA"]


def crear_mision(operador, dificultad="Normal"):
    """Crea el diccionario que guarda todo el estado de la misión."""
    mision = {
        "id": reportes.nuevo_id(),
        "operador": operador,
        "dificultad": dificultad,
        "recursos": recursos.crear_recursos(dificultad),
        "estado": "INICIALIZANDO",
        "puntos": 0,
        "eventos_procesados": 0,
        "decisiones_correctas": 0,
        "decisiones_incorrectas": 0,
        "historial": [],
    }
    reportes.registrar(mision, f"Misión creada (dificultad {dificultad})")
    mision["estado"] = "OPERATIVA"
    return mision

def main():
    """Abre la interfaz gráfica; si no hay tkinter, usa la consola."""
    try:
        # Se importa aquí porque gui.py importa crear_mision desde este archivo
        import gui
    except ImportError:
        print("tkinter no disponible: iniciando modo consola.")
        menu_consola()
        return
    gui.App().mainloop()


if __name__ == "__main__":
    main()
    

#   MODO CONSOLA

def panel_principal(operador):
    """Menú de la consola con las 8 opciones. Se repite hasta cerrar sesión."""
    mision = None
    while True:
        print("\n=== PANEL PRINCIPAL ===")
        print("1. Crear misión\n2. Consultar recursos\n3. Procesar evento")
        print("4. Ejecutar simulación\n5. Consultar estadísticas")
        print("6. Ver historial\n7. Generar reporte\n8. Cerrar sesión")
        opcion = leer_entero("Opción: ", 1, 8)

        if opcion == 1:
            mision = None
            if reportes.existe_progreso(operador):
                if leer_entero("Hay progreso guardado. 1. Continuar  2. Misión nueva: ", 1, 2) == 1:
                    mision = reportes.cargar_progreso(operador)
                    if mision is None:
                        print("  No se pudo leer el progreso; se creará una misión nueva.")
            if mision is None:
                n = leer_entero("Dificultad: 1. Fácil  2. Normal  3. Difícil: ", 1, 3)
                nivel = list(eventos.DIFICULTADES)[n - 1]
                mision = crear_mision(operador, nivel)
                print(f"Misión creada ({nivel}).")
            else:
                print(f"Misión retomada. Estado: {mision['estado']}")
        elif opcion == 8:
            return
        elif mision is None:
            # Todas las demás opciones necesitan una misión
            print("  Primero crea una misión (opción 1).")
        elif opcion == 2:
            recursos.mostrar_recursos(mision["recursos"])
        elif opcion == 3:
            eventos.procesar_evento(mision)
        elif opcion == 4:
            restantes = eventos.eventos_restantes(mision)
            if mision["estado"] in eventos.FINALES:
                print(f"  La misión ya terminó ({mision['estado']}).")
                continue
            if restantes == 0:
                print("  Ya se llegó a la meta de eventos. Procesa eventos a mano para recuperar los recursos.")
                continue
            n = leer_entero(f"¿Cuántos eventos simular? (1-{restantes}): ", 1, restantes)
            hechos = eventos.simular(mision, n)
            riesgo, nivel = eventos.algoritmo_propio(mision)
            print(f"Simulados {hechos} eventos. Estado: {mision['estado']} | Riesgo: {riesgo} ({nivel})")
        elif opcion == 5:
            for clave, valor in reportes.calcular_estadisticas(mision).items():
                print(f"{clave}: {valor}")
            riesgo, nivel = eventos.algoritmo_propio(mision)
            print(f"Riesgo: {riesgo} ({nivel})")
        elif opcion == 6:
            reportes.mostrar_historial(mision)
        elif opcion == 7:
            reportes.generar_reporte(mision)


def menu_consola():
    """Modo consola: se usa cuando tkinter no está disponible."""
    while True:
        print("\nROBOYORK CONTROL SYSTEM\n1. Iniciar sesión\n2. Crear operador\n3. Salir")
        opcion = leer_entero("Opción: ", 1, 3)
        if opcion == 1:
            print("Iniciar sesión")
            operador = usuarios.iniciar_sesion()
            if operador:
                panel_principal(operador)
        elif opcion == 2:
            usuarios.crear_operador()
        else:
            print("Hasta pronto.")
            break
