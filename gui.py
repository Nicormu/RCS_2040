"""ROBOYORK CONTROL SYSTEM - interfaz gráfica (tkinter).
Ejecutar: python gui.py
Reutiliza la lógica de usuarios, recursos, eventos y reportes; la GUI solo
muestra datos y llama a esas funciones (nada de input()/print() aquí).
"""
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import usuarios
import recursos
import eventos
import reportes
from main import crear_mision

FINALES = ("RESUELTA", "FALLIDA")
COLORES_ESTADO = {
    "INICIALIZANDO": "#888888", 
    "OPERATIVA": "#2e7d32", 
    "ALERTA": "#f9a825",
    "CRÍTICA": "#c62828", 
    "RESUELTA": "#1565c0", 
    "FALLIDA": "#4e342e"
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ROBOYORK CONTROL SYSTEM")
        self.geometry("720x520")
        self.minsize(640, 480)
        self.operador = None
        self.mision = None
        self.intentos = 0
        self.contenedor = ttk.Frame(self, padding=14)
        self.contenedor.pack(fill="both", expand=True)
        self.pantalla_login()

    # ---------- utilidades ----------
    def limpiar(self):
        for w in self.contenedor.winfo_children():
            w.destroy()

    # ---------- pantalla de login ----------
    def pantalla_login(self):
        self.limpiar()
        self.intentos = 0
        f = ttk.Frame(self.contenedor)
        f.place(relx=0.5, rely=0.45, anchor="center")
        ttk.Label(f, text="ROBOYORK CONTROL SYSTEM",
                  font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 14))
        ttk.Label(f, text="Usuario:").grid(row=1, column=0, sticky="e", pady=4)
        ttk.Label(f, text="Contraseña:").grid(row=2, column=0, sticky="e", pady=4)
        self.var_user = tk.StringVar()
        self.var_pass = tk.StringVar()
        e_user = ttk.Entry(f, textvariable=self.var_user, width=24)
        e_pass = ttk.Entry(f, textvariable=self.var_pass, width=24, show="•")
        e_user.grid(row=1, column=1, padx=6)
        e_pass.grid(row=2, column=1, padx=6)
        e_user.focus()
        e_pass.bind("<Return>", lambda _e: self.hacer_login())
        ttk.Button(f, text="Iniciar sesión", command=self.hacer_login).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(12, 4))
        ttk.Button(f, text="Crear operador", command=self.hacer_registro).grid(
            row=4, column=0, columnspan=2, sticky="ew")

    def hacer_login(self):
        user = self.var_user.get().strip()
        clave = self.var_pass.get()
        if not user or not clave:
            messagebox.showwarning("Datos incompletos", "Escribe usuario y contraseña.")
            return
        if usuarios.operadores.get(user) == clave:
            self.operador = user
            self.pantalla_panel()
            return
        self.intentos += 1
        restantes = usuarios.MAX_INTENTOS - self.intentos
        if restantes <= 0:
            messagebox.showerror("Acceso bloqueado", "Demasiados intentos fallidos.")
            self.destroy()
        else:
            messagebox.showerror("Error", f"Credenciales incorrectas. Intentos restantes: {restantes}")
            self.var_pass.set("")

    def hacer_registro(self):
        user = self.var_user.get().strip()
        clave = self.var_pass.get()
        if len(user) < 3 or len(clave) < 4:
            messagebox.showwarning("Datos inválidos",
                                   "Usuario mínimo 3 caracteres y contraseña mínimo 4.")
        elif user in usuarios.operadores:
            messagebox.showerror("Error", "Ese operador ya existe.")
        else:
            usuarios.operadores[user] = clave
            messagebox.showinfo("Listo", f"Operador '{user}' creado. Ya puedes iniciar sesión.")

    # ---------- panel principal ----------
    def pantalla_panel(self):
        self.limpiar()
        self.contenedor.columnconfigure(1, weight=1)
        self.contenedor.rowconfigure(0, weight=1)

        menu = ttk.Frame(self.contenedor)
        menu.grid(row=0, column=0, sticky="ns", padx=(0, 14))
        botones = [
            ("1. Crear misión", self.accion_crear),
            ("2. Consultar recursos", self.accion_recursos),
            ("3. Procesar evento", self.accion_evento),
            ("4. Ejecutar simulación", self.accion_simulacion),
            ("5. Estadísticas", self.accion_estadisticas),
            ("6. Ver historial", self.accion_historial),
            ("7. Generar reporte", self.accion_reporte),
            ("8. Cerrar sesión", self.accion_logout),
        ]
        for texto, cmd in botones:
            ttk.Button(menu, text=texto, command=cmd, width=24).pack(pady=3, fill="x")

        self.vista = ttk.LabelFrame(self.contenedor, text=f"Operador: {self.operador}", padding=12)
        self.vista.grid(row=0, column=1, sticky="nsew")
        self.vista.columnconfigure(1, weight=1)

        self.lbl_estado = tk.Label(self.vista, text="SIN MISIÓN", fg="white",
                                   bg="#888888", font=("Segoe UI", 12, "bold"), pady=4)
        self.lbl_estado.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        self.barras = {}
        for i, nombre in enumerate(recursos.RECURSOS_INICIALES, start=1):
            ttk.Label(self.vista, text=nombre, width=13).grid(row=i, column=0, sticky="w", pady=6)
            barra = ttk.Progressbar(self.vista, maximum=100, length=260)
            barra.grid(row=i, column=1, sticky="ew", padx=6)
            lbl = ttk.Label(self.vista, text="--", width=5)
            lbl.grid(row=i, column=2)
            self.barras[nombre] = (barra, lbl)

        self.lbl_puntos = ttk.Label(self.vista, text="Puntos: 0   |   Eventos: 0",
                                    font=("Segoe UI", 11))
        self.lbl_puntos.grid(row=6, column=0, columnspan=3, pady=(14, 4), sticky="w")
        self.lbl_msg = ttk.Label(self.vista, text="Crea una misión para comenzar.",
                                 wraplength=380, justify="left")
        self.lbl_msg.grid(row=7, column=0, columnspan=3, sticky="w")
        self.refrescar()

    def refrescar(self):
        """Actualiza barras, estado y puntos desde self.mision."""
        m = self.mision
        if m is None:
            return
        for nombre, (barra, lbl) in self.barras.items():
            valor = m["recursos"][nombre]
            barra["value"] = valor
            lbl.config(text=f"{valor}%")
        self.lbl_estado.config(text=f"ESTADO: {m['estado']}",
                               bg=COLORES_ESTADO.get(m["estado"], "#888888"))
        self.lbl_puntos.config(text=f"Puntos: {m['puntos']}   |   Eventos: {m['eventos_procesados']}")

    def hay_mision(self):
        if self.mision is None:
            messagebox.showwarning("Sin misión", "Primero crea una misión (opción 1).")
            return False
        return True

    def mision_activa(self):
        if not self.hay_mision():
            return False
        if self.mision["estado"] in FINALES:
            messagebox.showinfo("Misión terminada",
                                f"La misión ya está {self.mision['estado']}. Crea una nueva.")
            return False
        return True

    # ---------- acciones ----------
    def accion_crear(self):
        self.mision = None
        if reportes.existe_progreso(self.operador) and messagebox.askyesno(
                "Progreso guardado",
                "Hay una misión guardada.\n¿Quieres continuarla?\n(No = empezar una nueva)"):
            self.mision = reportes.cargar_progreso(self.operador)
        if self.mision is None:
            self.mision = crear_mision(self.operador)
            self.lbl_msg.config(text="Misión creada. Estado: OPERATIVA.")
        else:
            self.lbl_msg.config(text=f"Misión retomada. Estado: {self.mision['estado']}.")
        self.refrescar()

    def accion_recursos(self):
        if self.hay_mision():
            self.refrescar()
            self.lbl_msg.config(text="Recursos actualizados.")

    def accion_evento(self):
        if not self.mision_activa():
            return
        evento = eventos.generar_evento(self.mision)
        dlg = tk.Toplevel(self)
        dlg.title("Evento")
        dlg.transient(self)
        dlg.grab_set()
        f = ttk.Frame(dlg, padding=16)
        f.pack()
        ttk.Label(f, text=f"⚠ {evento['nombre']}", font=("Segoe UI", 13, "bold")).pack(pady=(0, 10))
        ttk.Label(f, text="¿Qué decisión tomas?").pack(pady=(0, 8))

        def elegir(i):
            op = eventos.aplicar_opcion(self.mision, evento, i)
            dlg.destroy()
            signo = "+" if op["puntos"] >= 0 else ""
            self.lbl_msg.config(text=f"{evento['nombre']}: {op['texto']} ({signo}{op['puntos']} pts)")
            self.refrescar()
            if self.mision["estado"] in FINALES:
                messagebox.showinfo("Fin de misión", f"Estado final: {self.mision['estado']}")

        for i, op in enumerate(evento["opciones"]):
            ttk.Button(f, text=op["texto"], width=40,
                       command=lambda i=i: elegir(i)).pack(pady=3)

    def accion_simulacion(self):
        if not self.mision_activa():
            return
        # Pide N eventos con un diálogo propio (validado por rango del Spinbox).
        dlg = tk.Toplevel(self)
        dlg.title("Simulación")
        dlg.transient(self)
        dlg.grab_set()
        f = ttk.Frame(dlg, padding=16)
        f.pack()
        ttk.Label(f, text="Número de eventos (1-20):").pack()
        var = tk.StringVar(value="5")
        ttk.Spinbox(f, from_=1, to=20, textvariable=var, width=6).pack(pady=8)

        def correr():
            try:
                n = int(var.get())
            except ValueError:
                messagebox.showwarning("Inválido", "Escribe un número entero.", parent=dlg)
                return
            if not 1 <= n <= 20:
                messagebox.showwarning("Fuera de rango", "Debe estar entre 1 y 20.", parent=dlg)
                return
            dlg.destroy()
            for _ in range(n):
                if self.mision["estado"] in FINALES:
                    break
                ev = eventos.generar_evento(self.mision)
                eventos.aplicar_opcion(self.mision, ev, random.randrange(len(ev["opciones"])))
            self.lbl_msg.config(text=f"Simulación completada ({n} eventos solicitados).")
            self.refrescar()

        ttk.Button(f, text="Ejecutar", command=correr).pack()

    def accion_estadisticas(self):
        if not self.hay_mision():
            return
        est = reportes.calcular_estadisticas(self.mision)
        texto = "\n".join(f"{k}: {v}" for k, v in est.items())
        messagebox.showinfo("Estadísticas", texto)

    def accion_historial(self):
        if not self.hay_mision():
            return
        win = tk.Toplevel(self)
        win.title("Historial")
        win.geometry("460x320")
        lista = tk.Listbox(win)
        scroll = ttk.Scrollbar(win, command=lista.yview)
        lista.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        lista.pack(fill="both", expand=True)
        for i, accion in enumerate(self.mision["historial"], start=1):
            lista.insert("end", f"{i}. {accion}")

    def accion_reporte(self):
        if not self.hay_mision():
            return
        texto = reportes.texto_reporte(self.mision)
        win = tk.Toplevel(self)
        win.title("Reporte final")
        win.geometry("480x380")
        caja = tk.Text(win, wrap="word")
        caja.insert("1.0", texto)
        caja.config(state="disabled")
        caja.pack(fill="both", expand=True, padx=8, pady=8)

        def guardar():
            ruta = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Texto", "*.txt")],
                                                initialfile="reporte_rcs.txt", parent=win)
            if ruta:
                with open(ruta, "w", encoding="utf-8") as archivo:
                    archivo.write(texto)
                messagebox.showinfo("Guardado", f"Reporte guardado en:\n{ruta}", parent=win)

        ttk.Button(win, text="Guardar como TXT", command=guardar).pack(pady=(0, 8))

    def accion_logout(self):
        self.operador = None
        self.mision = None
        self.pantalla_login()


if __name__ == "__main__":
    App().mainloop()