"""ROBOYORK CONTROL SYSTEM (RCS) - programa principal."""
from utilidades import leer_entero
import usuarios, recursos, eventos, reportes

ESTADOS = ["INICIALIZANDO", "OPERATIVA", "ALERTA", "CRÍTICA", "RESUELTA", "FALLIDA"]


def crear_mision(operador):
    """Crea el diccionario que guarda todo el estado de la misión."""
    mision = {
        "operador": operador,
        "recursos": recursos.crear_recursos(),
        "estado": "INICIALIZANDO",
        "puntos": 0,
        "eventos_procesados": 0,
        "decisiones_correctas": 0,
        "decisiones_incorrectas": 0,
        "historial": [],
    }
    reportes.registrar(mision, "Misión creada")
    mision["estado"] = "OPERATIVA"
    return mision


def panel_principal(operador):
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
                mision = crear_mision(operador)
                print("Misión creada.")
            else:
                print(f"Misión retomada. Estado: {mision['estado']}")
        elif opcion == 8:
            return
        elif mision is None:
            print(" Primero crea una misión (opción 1).")
        elif opcion == 2:
            recursos.mostrar_recursos(mision["recursos"])
        elif opcion == 3:
            eventos.procesar_evento(mision)
        elif opcion == 4:
            n = leer_entero("¿Cuántos eventos simular? (1-20): ", 1, 20)
            hechos = eventos.simular(mision, n)
            riesgo, nivel = eventos.algoritmo_propio(mision)
            print(f"Simulados {hechos} eventos. Estado: {mision['estado']} | Riesgo: {riesgo} ({nivel})")
        elif opcion == 5:
            for clave, valor in reportes.calcular_estadisticas(mision).items():
                print(f"{clave}: {valor}")
        elif opcion == 6:
            reportes.mostrar_historial(mision)
        elif opcion == 7:
            reportes.generar_reporte(mision)


def menu_consola():
    """Modo consola (respaldo si tkinter no está disponible)."""
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


def main():
    """Abre directamente la interfaz gráfica; si no hay tkinter, usa la consola."""
    try:
        import gui  # import tardío: gui.py importa crear_mision desde este archivo
    except ImportError:
        print("tkinter no disponible: iniciando modo consola.")
        menu_consola()
        return
    gui.App().mainloop()


if __name__ == "__main__":
    main()