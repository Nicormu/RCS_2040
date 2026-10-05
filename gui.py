"""ROBOYORK CONTROL SYSTEM - interfaz gráfica con tkinter.

Se ejecuta con:  python gui.py   (o python main.py)
Este archivo solo muestra datos y botones; la lógica está en usuarios, eventos y reportes.
"""
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog

import usuarios
import recursos
import eventos
import reportes
from main import crear_mision

# ---------- colores y fuente ----------
F = "Segoe UI"
BG, PANEL, PANEL2 = "#0b1220", "#151f33", "#1f2d47"
TEXTO, MUTED, ACENTO = "#e6edf7", "#8aa0bf", "#38bdf8"
VERDE, AMBAR, ROJO = "#22c55e", "#f59e0b", "#ef4444"
COLORES_ESTADO = {
                "INICIALIZANDO": "#64748b", 
                "OPERATIVA": "#16a34a", 
                "ALERTA": "#d97706",
                "CRÍTICA": "#dc2626", 
                "RESUELTA": "#2563eb", 
                "FALLIDA": "#7c2d12"
                }
ICONOS = {
        "Energía": "⚡", 
        "Agua": "💧", 
        "Alimentos": "🍞", 
        "Comunicación": "📡"
        }
DESC_DIF = {
        "Fácil": "Más recursos y menos castigo",
        "Normal": "Equilibrada",
        "Difícil": "Recursos escasos, desgaste y más riesgo"
        }


def aclarar(color):
    """Devuelve el mismo color un poco más claro (para el efecto al pasar el mouse)."""
    n = int(color[1:], 16)
    rgb = (n >> 16 & 255, n >> 8 & 255, n & 255)
    return "#%02x%02x%02x" % tuple(min(255, x + 28) for x in rgb)


def boton(parent, texto, cmd, bg=PANEL2, fg=TEXTO, **kw):
    """Crea un botón plano que se aclara cuando el mouse pasa por encima."""
    b = tk.Button(parent, text=texto, command=cmd, bg=bg, fg=fg, relief="flat", bd=0,
                  font=(F, 10, "bold"), cursor="hand2", padx=14, pady=8,
                  activebackground=aclarar(bg), activeforeground=fg, **kw)
    b.bind("<Enter>", lambda _e: b.config(bg=aclarar(bg)))
    b.bind("<Leave>", lambda _e: b.config(bg=bg))
    return b


class Barra(tk.Canvas):
    """Barra de progreso que sube o baja poco a poco y cambia de color según el valor."""

    def __init__(self, master):
        super().__init__(master, height=12, bg=PANEL2, highlightthickness=0)
        self.valor, self.objetivo, self._job = 0, 0, None
        self.bind("<Configure>", lambda _e: self._dibujar())

    def poner(self, v):
        """Define el valor al que debe llegar la barra y arranca la animación."""
        self.objetivo = v
        if self._job:
            self.after_cancel(self._job)
        self._animar()

    def _animar(self):
        # Mueve la barra hasta 3 puntos por paso hacia el objetivo
        delta = self.objetivo - self.valor
        if delta:
            self.valor += (1 if delta > 0 else -1) * min(abs(delta), 3)
            self._job = self.after(14, self._animar)
        self._dibujar()

    def _dibujar(self):
        self.delete("all")
        color = VERDE if self.valor >= 60 else AMBAR if self.valor >= 30 else ROJO
        self.create_rectangle(0, 0, self.winfo_width() * self.valor / 100, 12, fill=color, width=0)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ROBOYORK CONTROL SYSTEM")
        self.geometry("1000x700")
        self.minsize(900, 640)
        self.configure(bg=BG)
        self.operador = self.mision = None
        self.intentos = 0
        self.contenedor = tk.Frame(self, bg=BG)
        self.contenedor.pack(fill="both", expand=True)
        self.pantalla_login()

    def limpiar(self, w=None):
        """Borra todo lo que hay dentro de un frame (por defecto el contenedor principal)."""
        for h in (w or self.contenedor).winfo_children():
            h.destroy()

    def etiqueta(self, parent, texto, size=10, color=TEXTO, bold=False, bg=None, **kw):
        """Atajo para crear un Label con la fuente y los colores del tema."""
        return tk.Label(parent, text=texto, fg=color, bg=bg or parent["bg"],
                        font=(F, size, "bold" if bold else "normal"), **kw)

    # ---------- login ----------
    def pantalla_login(self):
        self.limpiar()
        self.intentos = 0
        card = tk.Frame(self.contenedor, bg=PANEL, padx=40, pady=32)
        card.place(relx=0.5, rely=0.5, anchor="center")
        self.etiqueta(card, "🤖", 36).pack()
        self.etiqueta(card, "ROBOYORK", 20, ACENTO, True).pack()
        self.etiqueta(card, "CONTROL SYSTEM", 10, MUTED).pack(pady=(0, 18))
        self.var_user, self.var_pass = tk.StringVar(), tk.StringVar()
        for texto, var, oculto in (("Usuario", self.var_user, ""), ("Contraseña", self.var_pass, "•")):
            self.etiqueta(card, texto, 9, MUTED, anchor="w").pack(fill="x")
            e = tk.Entry(card, textvariable=var, show=oculto, width=28, bg=PANEL2, fg=TEXTO, relief="flat",
                         insertbackground=TEXTO, font=(F, 11), highlightthickness=1,
                         highlightbackground=PANEL2, highlightcolor=ACENTO)
            e.pack(pady=(2, 12), ipady=6)
            if not oculto:
                e.focus()
        # Enter en el campo de contraseña también inicia sesión
        e.bind("<Return>", lambda _e: self.hacer_login())
        boton(card, "Iniciar sesión", self.hacer_login, ACENTO, "#04121f").pack(fill="x")
        boton(card, "Crear operador", self.hacer_registro).pack(fill="x", pady=(8, 0))

    def hacer_login(self):
        user, clave = self.var_user.get().strip(), self.var_pass.get()
        if not user or not clave:
            return messagebox.showwarning("Datos incompletos", "Escribe usuario y contraseña.")
        if usuarios.operadores.get(user) == clave:
            self.operador = user
            return self.pantalla_panel()
        self.intentos += 1
        restantes = usuarios.MAX_INTENTOS - self.intentos
        if restantes <= 0:
            messagebox.showerror("Acceso bloqueado", "Demasiados intentos fallidos.")
            self.destroy()
        else:
            messagebox.showerror("Error", f"Credenciales incorrectas. Intentos restantes: {restantes}")
            self.var_pass.set("")

    def hacer_registro(self):
        user, clave = self.var_user.get().strip(), self.var_pass.get()
        if len(user) < 3 or len(clave) < 4:
            messagebox.showwarning("Datos inválidos", "Usuario mínimo 3 caracteres y contraseña mínimo 4.")
        elif user in usuarios.operadores:
            messagebox.showerror("Error", "Ese operador ya existe.")
        else:
            usuarios.registrar(user, clave)
            messagebox.showinfo("Listo", f"Operador '{user}' creado. Ya puedes iniciar sesión.")

    # ---------- panel principal ----------
    def pantalla_panel(self):
        self.limpiar()
        c = self.contenedor
        c.columnconfigure(1, weight=1)
        c.rowconfigure(0, weight=1)

        # Menú lateral
        lado = tk.Frame(c, bg=PANEL, width=210)
        lado.grid(row=0, column=0, sticky="ns")
        lado.pack_propagate(False)
        self.etiqueta(lado, "🤖 ROBOYORK", 15, ACENTO, True).pack(pady=(22, 2))
        self.etiqueta(lado, f"{self.operador} · {usuarios.rol(self.operador)}", 9, MUTED).pack(pady=(0, 20))
        botones = [("＋  Nueva misión", self.accion_crear, ACENTO, "#04121f"),
                   ("⚠  Procesar evento", self.accion_evento, PANEL2, TEXTO),
                   ("▶  Simular", self.accion_simulacion, PANEL2, TEXTO),
                   ("📄  Reporte", self.accion_reporte, PANEL2, TEXTO)]
        if usuarios.es_admin(self.operador):  # este botón solo lo ve el admin
            botones.append(("👥  Operadores", self.accion_operadores, PANEL2, TEXTO))
        for texto, cmd, bg, fg in botones:
            boton(lado, texto, cmd, bg, fg, anchor="w").pack(fill="x", padx=14, pady=4)
        boton(lado, "⏻  Cerrar sesión", self.accion_logout, "#3b1d24", "#fca5a5",
              anchor="w").pack(side="bottom", fill="x", padx=14, pady=16)

        # Zona principal
        main = tk.Frame(c, bg=BG, padx=22, pady=18)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure((0, 1), weight=1, uniform="a")
        main.rowconfigure(4, weight=1)

        self.titulo = self.etiqueta(main, "Panel de misión", 16, TEXTO, True)
        self.titulo.grid(row=0, column=0, sticky="w")
        self.badge = tk.Label(main, text="SIN MISIÓN", fg="white", bg="#64748b",
                              font=(F, 10, "bold"), padx=14, pady=4)
        self.badge.grid(row=0, column=1, sticky="e")

        # Una tarjeta por recurso (2 columnas)
        self.barras = {}
        for i, nombre in enumerate(recursos.NOMBRES):
            card = tk.Frame(main, bg=PANEL, padx=14, pady=10)
            card.grid(row=1 + i // 2, column=i % 2, sticky="ew", padx=(0, 8) if i % 2 == 0 else (8, 0), pady=6)
            card.columnconfigure(0, weight=1)
            self.etiqueta(card, f"{ICONOS[nombre]}  {nombre}", 10, MUTED).grid(row=0, column=0, sticky="w")
            lbl = self.etiqueta(card, "--", 12, TEXTO, True)
            lbl.grid(row=0, column=1)
            barra = Barra(card)
            barra.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
            self.barras[nombre] = (barra, lbl)

        # Fila de métricas: puntos, eventos, eficiencia y riesgo
        fila = tk.Frame(main, bg=BG)
        fila.grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)
        self.tiles = {}
        for i, t in enumerate(("Puntos", "Eventos", "Eficiencia", "Riesgo")):
            fila.columnconfigure(i, weight=1, uniform="t")
            tile = tk.Frame(fila, bg=PANEL, padx=12, pady=8)
            tile.grid(row=0, column=i, sticky="ew", padx=4)
            self.etiqueta(tile, t.upper(), 8, MUTED).pack(anchor="w")
            self.tiles[t] = self.etiqueta(tile, "--", 14, TEXTO, True)
            self.tiles[t].pack(anchor="w")

        # Abajo: el evento actual (izquierda) y el historial (derecha)
        self.panel_evento = tk.Frame(main, bg=PANEL, padx=16, pady=12)
        self.panel_evento.grid(row=4, column=0, sticky="nsew", padx=(0, 8), pady=(10, 0))
        hist = tk.Frame(main, bg=PANEL, padx=12, pady=12)
        hist.grid(row=4, column=1, sticky="nsew", padx=(8, 0), pady=(10, 0))
        self.etiqueta(hist, "HISTORIAL", 8, MUTED).pack(anchor="w")
        self.log = tk.Text(hist, bg=PANEL, fg=TEXTO, relief="flat", font=(F, 9), wrap="word",
                           state="disabled", height=8, highlightthickness=0, cursor="arrow")
        self.log.pack(fill="both", expand=True, pady=(4, 0))
        self.log.tag_config("pos", foreground=VERDE)
        self.log.tag_config("neg", foreground="#f87171")
        self.mensaje("Crea una misión para comenzar.")
        self.refrescar()

    def refrescar(self):
        """Vuelve a pintar barras, métricas, estado e historial con los datos actuales."""
        m = self.mision
        for nombre, (barra, lbl) in self.barras.items():
            barra.poner(m["recursos"][nombre] if m else 0)
            lbl.config(text=f"{m['recursos'][nombre]}%" if m else "--")
        self.titulo.config(text=f"Panel de misión · {m['dificultad']}" if m else "Panel de misión")
        self.badge.config(text=m["estado"] if m else "SIN MISIÓN",
                          bg=COLORES_ESTADO.get(m["estado"], "#64748b") if m else "#64748b")
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        if m:
            est = reportes.calcular_estadisticas(m)
            riesgo, nivel = eventos.indice_riesgo(m["recursos"])
            self.tiles["Puntos"].config(text=m["puntos"])
            self.tiles["Eventos"].config(text=f"{m['eventos_procesados']}/{eventos.config_mision(m)['meta']}")
            self.tiles["Eficiencia"].config(text=f"{est['Eficiencia (%)']}%")
            self.tiles["Riesgo"].config(text=f"{riesgo} · {nivel}",
                                        fg={"BAJO": VERDE, "MEDIO": AMBAR, "ALTO": ROJO}[nivel])
            # Verde si la línea suma puntos, rojo si resta o es un fallo
            for i, a in enumerate(m["historial"], start=1):
                tag = "pos" if "(+" in a else "neg" if "(-" in a or "FALLIDA" in a else ""
                self.log.insert("end", f"{i}. {a}\n", tag)
            self.log.see("end")
        self.log.config(state="disabled")

    def mensaje(self, titulo, detalle="", color=TEXTO):
        """Escribe un mensaje en el panel del evento (reemplaza lo que hubiera)."""
        self.limpiar(self.panel_evento)
        self.etiqueta(self.panel_evento, titulo, 12, color, True, wraplength=320, justify="left").pack(anchor="w")
        if detalle:
            self.etiqueta(self.panel_evento, detalle, 10, MUTED, wraplength=320,
                          justify="left").pack(anchor="w", pady=4)

    def mision_activa(self):
        """True si hay una misión en curso; si no, avisa al usuario y devuelve False."""
        if self.mision is None:
            messagebox.showwarning("Sin misión", "Primero crea una misión.")
        elif self.mision["estado"] in eventos.FINALES:
            messagebox.showinfo("Misión terminada", f"La misión ya está {self.mision['estado']}. Crea una nueva.")
        else:
            return True
        return False

    def pedir_dificultad(self):
        """Ventana con un botón por dificultad. Devuelve el nombre elegido o None."""
        res = []
        win = tk.Toplevel(self, bg=PANEL, padx=24, pady=20)
        win.title("Dificultad")
        win.transient(self)
        win.grab_set()
        self.etiqueta(win, "Elige la dificultad", 13, TEXTO, True).pack(pady=(0, 10))
        for nombre in eventos.DIFICULTADES:
            boton(win, f"{nombre}  —  {DESC_DIF[nombre]}", lambda n=nombre: (res.append(n), win.destroy()),
                  anchor="w").pack(fill="x", pady=3)
        self.wait_window(win)
        return res[0] if res else None

    # ---------- acciones de los botones ----------
    def accion_crear(self):
        previa, self.mision = self.mision, None
        if reportes.existe_progreso(self.operador) and messagebox.askyesno(
                "Progreso guardado", "Hay una misión guardada.\n¿Quieres continuarla?\n(No = empezar una nueva)"):
            self.mision = reportes.cargar_progreso(self.operador)
        if self.mision is not None:
            self.mensaje("Misión retomada", "Pulsa «Procesar evento» o «Simular».", VERDE)
        else:
            nivel = self.pedir_dificultad()
            if nivel is None:  # canceló: se conserva la misión anterior
                self.mision = previa
                return
            self.mision = crear_mision(self.operador, nivel)
            self.mensaje(f"Misión creada · {nivel}", "Pulsa «Procesar evento» o «Simular».", VERDE)
        self.refrescar()

    def accion_evento(self):
        if not self.mision_activa():
            return
        ev = eventos.generar_evento(self.mision)
        self.mensaje(f"⚠ {ev['nombre']}", "¿Qué decisión tomas?", AMBAR)
        for i, op in enumerate(ev["opciones"]):
            boton(self.panel_evento, op["texto"], lambda i=i: self.elegir(ev, i),
                  anchor="w", wraplength=320, justify="left").pack(fill="x", pady=3)

    def elegir(self, ev, i):
        """Se llama al pulsar una opción: aplica la decisión y muestra el resultado."""
        op = eventos.aplicar_opcion(self.mision, ev, i)
        self.refrescar()
        estado = self.mision["estado"]
        if estado in eventos.FINALES:
            self.mensaje(f"Misión {estado}", "Crea una nueva misión para seguir jugando.",
                         VERDE if estado == "RESUELTA" else ROJO)
        elif not op["exito"]:
            self.mensaje(f"✖ La acción falló ({op['puntos']:+d} pts)", f"{ev['nombre']}: {op['texto']}", ROJO)
        else:
            self.mensaje(f"{op['puntos']:+d} pts", f"{ev['nombre']}: {op['texto']}",
                         VERDE if op["puntos"] > 0 else ROJO)

    def accion_simulacion(self):
        if not self.mision_activa():
            return
        restantes = eventos.eventos_restantes(self.mision)
        if restantes == 0:
            return messagebox.showinfo("Meta alcanzada", "Ya se llegó a la meta de eventos.\n"
                                       "Procesa eventos a mano para recuperar los recursos.")
        n = simpledialog.askinteger("Simulación", f"Número de eventos (1-{restantes}):",
                                    minvalue=1, maxvalue=restantes, initialvalue=min(5, restantes),
                                    parent=self)
        if n:
            hechos = eventos.simular(self.mision, n)
            self.mensaje("Simulación completada", f"{hechos} evento(s) ejecutados.", ACENTO)
            self.refrescar()

    def accion_reporte(self):
        if self.mision is None:
            return messagebox.showwarning("Sin misión", "Primero crea una misión.")
        texto = reportes.texto_reporte(self.mision)
        win = tk.Toplevel(self, bg=BG)
        win.title("Reporte final")
        win.geometry("500x420")
        caja = tk.Text(win, wrap="word", bg=PANEL, fg=TEXTO, relief="flat", font=("Consolas", 10), padx=10, pady=10)
        caja.insert("1.0", texto)
        caja.config(state="disabled")
        caja.pack(fill="both", expand=True, padx=10, pady=10)

        def guardar():
            ruta = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")],
                                                initialfile="reporte_rcs.txt", parent=win)
            if ruta:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(texto)
                messagebox.showinfo("Guardado", f"Reporte guardado en:\n{ruta}", parent=win)

        boton(win, "Guardar como TXT", guardar, ACENTO, "#04121f").pack(pady=(0, 10))

    def accion_operadores(self):
        """Panel del admin: lista los operadores y permite borrar su progreso guardado."""
        if not usuarios.es_admin(self.operador):
            return messagebox.showerror("Sin permiso", "Solo el admin puede gestionar operadores.")
        win = tk.Toplevel(self, bg=BG)
        win.title("Operadores")
        win.geometry("400x320")
        lista = tk.Listbox(win, bg=PANEL, fg=TEXTO, relief="flat", font=(F, 11),
                           selectbackground=ACENTO, selectforeground="#04121f", highlightthickness=0)
        lista.pack(fill="both", expand=True, padx=10, pady=10)

        def cargar():
            lista.delete(0, "end")
            for u in usuarios.operadores:
                guardado = "💾 progreso guardado" if reportes.existe_progreso(u) else "—"
                lista.insert("end", f"{u}  [{usuarios.rol(u)}]   {guardado}")

        def borrar():
            sel = lista.curselection()
            if not sel:
                return messagebox.showwarning("Selecciona", "Elige un operador de la lista.", parent=win)
            u = list(usuarios.operadores)[sel[0]]
            if messagebox.askyesno("Borrar progreso", f"¿Borrar el progreso guardado de '{u}'?", parent=win):
                reportes.borrar_progreso(u)
                cargar()

        cargar()
        boton(win, "Borrar progreso seleccionado", borrar, "#3b1d24", "#fca5a5").pack(pady=(0, 10))

    def accion_logout(self):
        self.operador = self.mision = None
        self.pantalla_login()


if __name__ == "__main__":
    App().mainloop()