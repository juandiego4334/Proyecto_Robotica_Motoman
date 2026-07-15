import tkinter as tk
from tkinter import ttk, messagebox
from robodk.robolink import *
from robodk.robomath import *
import threading
import time


class HMI_RoboDK:
    def __init__(self, ventana):
        # Configuración principal de la ventana
        self.ventana = ventana
        self.ventana.title("HMI Básica - Soldadura PCB con RoboDK")
        self.ventana.state("zoomed")
        self.ventana.configure(bg="#dfe7ef")

        # Variables de RoboDK
        self.RDK = None
        self.robot = None
        self.target_home = None
        self.target_pcb = None

        # Variables de proceso
        self.proceso_pausado = False
        self.proceso_detenido = False
        self.emergencia_activa = False

        # Variables visuales
        self.estado = tk.StringVar(value="IDLE")
        self.alarma = tk.StringVar(value="Sin fallas")
        self.receta = tk.StringVar(value="PCB_1")
        self.pitch = tk.DoubleVar(value=2.54)
        self.tiempo_soldadura = tk.DoubleVar(value=0.4)
        self.puntos_ejecutados = tk.IntVar(value=0)
        self.total_puntos = tk.IntVar(value=0)
        self.menu_control = tk.StringVar(value="Configuración inicial")

        # PCB por defecto
        self.recetas = {
            "PCB_1": [
                {"tipo": "Resistencia", "cantidad": 4, "referencia": "1k", "pines": 2},
                {"tipo": "Capacitor", "cantidad": 2, "referencia": "100nF", "pines": 2},
                {"tipo": "LED", "cantidad": 1, "referencia": "Rojo", "pines": 2},
                {"tipo": "Conector", "cantidad": 1, "referencia": "JST 2P", "pines": 2}
            ],
            "PCB_2": [
                {"tipo": "Resistencia", "cantidad": 6, "referencia": "220 ohm", "pines": 2},
                {"tipo": "Diodo", "cantidad": 2, "referencia": "1N4007", "pines": 2},
                {"tipo": "Transistor", "cantidad": 2, "referencia": "BC547", "pines": 3},
                {"tipo": "Bornera", "cantidad": 1, "referencia": "2 vías", "pines": 2}
            ],
            "PCB_3": [
                {"tipo": "CI DIP-8", "cantidad": 1, "referencia": "NE555", "pines": 8},
                {"tipo": "Resistencia", "cantidad": 3, "referencia": "10k", "pines": 2},
                {"tipo": "Capacitor", "cantidad": 2, "referencia": "1uF", "pines": 2},
                {"tipo": "Conector", "cantidad": 1, "referencia": "Header 3P", "pines": 3}
            ],
            "PCB_Manual": []
        }

        # Tabla básica de pines por componente
        self.pines_componentes = {
            "Resistencia": 2,
            "Capacitor": 2,
            "Diodo": 2,
            "LED": 2,
            "Transistor": 3,
            "Bornera": 2,
            "Conector": 2,
            "CI DIP-8": 8,
            "CI DIP-14": 14
        }

        # Crear interfaz
        self.crear_interfaz()

        # Actualizar datos iniciales
        self.actualizar_receta()

    def crear_interfaz(self):
        titulo = tk.Label(
            self.ventana,
            text="HMI - Estación 3 de Soldadura",
            font=("123Marker", 18, "bold"),
            bg="#dfe7ef",
            fg="#1f3b5b"
        )
        titulo.pack(pady=10)

        # Marco principal
        marco_principal = tk.Frame(self.ventana, bg="#dfe7ef")
        marco_principal.pack(fill="both", expand=True, padx=10, pady=10)

        # Panel izquierdo
        self.panel_izquierdo = tk.LabelFrame(
            marco_principal,
            text="PCB's y Resumen",
            font=("123Marker", 11, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        self.panel_izquierdo.pack(side="left", fill="y", padx=8)

        # Panel central
        self.panel_central = tk.LabelFrame(
            marco_principal,
            text="Control",
            font=("123Marker", 11, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        self.panel_central.pack(side="left", fill="both", expand=True, padx=8)

        # Panel derecho
        self.panel_derecho = tk.LabelFrame(
            marco_principal,
            text="Estado",
            font=("123Marker", 11, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        self.panel_derecho.pack(side="right", fill="y", padx=8)

        # Construcción de secciones
        self.construir_panel_recetas()
        self.construir_panel_control()
        self.construir_panel_estado()
        self.construir_log()

    def construir_panel_recetas(self):
        # Selector de receta
        tk.Label(
            self.panel_izquierdo,
            text="Selecciona una configuración de PCB",
            bg="white",
            font="123Marker"
        ).pack(anchor="w")

        combo_receta = ttk.Combobox(
            self.panel_izquierdo,
            textvariable=self.receta,
            values=list(self.recetas.keys()),
            state="readonly"
        )
        combo_receta.pack(fill="x", pady=5)
        combo_receta.bind("<<ComboboxSelected>>", self.actualizar_receta)

        # Botón para agregar componente manual
        self.boton_manual = tk.Button(
            self.panel_izquierdo,
            text="Agregar componente a PCB manual",
            bg="#d9e8fb",
            font="123Marker",
            command=self.abrir_ventana_componente
        )

        # Tabla de componentes de la PCB
        tk.Label(
            self.panel_izquierdo,
            text="Componentes de la PCB:",
            bg="white",
            font="123Marker"
        ).pack(anchor="w", pady=(10, 0))

        estilo_tabla = ttk.Style()
        estilo_tabla.theme_use("clam")
        estilo_tabla.configure(
            "Treeview",
            background="white",
            foreground="black",
            rowheight=28,
            fieldbackground="white",
            font=("123Marker", 10)
        )
        estilo_tabla.configure(
            "Treeview.Heading",
            background="#b8d8f8",
            foreground="#1f3b5b",
            font=("123Marker", 10, "bold")
        )

        marco_tabla = tk.Frame(self.panel_izquierdo, bg="white")
        marco_tabla.pack(fill="both", pady=5)

        columnas = ("componente", "cantidad", "referencia", "pines")
        self.tabla_componentes = ttk.Treeview(
            marco_tabla,
            columns=columnas,
            show="headings",
            height=4
        )

        self.tabla_componentes.heading("componente", text="Componente")
        self.tabla_componentes.heading("cantidad", text="Cantidad")
        self.tabla_componentes.heading("referencia", text="Referencia")
        self.tabla_componentes.heading("pines", text="Pines")

        self.tabla_componentes.column("componente", width=130, anchor="center")
        self.tabla_componentes.column("cantidad", width=70, anchor="center")
        self.tabla_componentes.column("referencia", width=110, anchor="center")
        self.tabla_componentes.column("pines", width=60, anchor="center")

        scroll_tabla = ttk.Scrollbar(
            marco_tabla,
            orient="vertical",
            command=self.tabla_componentes.yview
        )
        self.tabla_componentes.configure(yscrollcommand=scroll_tabla.set)

        self.tabla_componentes.pack(side="left", fill="both", expand=True)
        scroll_tabla.pack(side="right", fill="y")

        # Resumen general
        tk.Label(
            self.panel_izquierdo,
            text="Distancia entre puntos [mm]:",
            bg="white",
            font="123Marker"
        ).pack(anchor="w")
        tk.Entry(self.panel_izquierdo, textvariable=self.pitch).pack(fill="x", pady=5)

        tk.Label(
            self.panel_izquierdo,
            text="Tiempo de soldadura [s]:",
            bg="white",
            font="123Marker"
        ).pack(anchor="w")
        tk.Entry(self.panel_izquierdo, textvariable=self.tiempo_soldadura).pack(fill="x", pady=5)

        tk.Label(
            self.panel_izquierdo,
            text="Puntos de soldadura totales:",
            bg="white",
            font="123Marker"
        ).pack(anchor="w")
        tk.Entry(self.panel_izquierdo, textvariable=self.total_puntos, state="readonly").pack(fill="x", pady=5)

    def construir_panel_control(self):
        # Menú desplegable para cambiar entre paneles
        tk.Label(
            self.panel_central,
            text="Selecciona el menú de control:",
            bg="white",
            font="123Marker"
        ).pack(anchor="w")

        combo_control = ttk.Combobox(
            self.panel_central,
            textvariable=self.menu_control,
            values=["Configuración inicial", "Configuraciones de operación"],
            state="readonly"
        )
        combo_control.pack(fill="x", pady=5)
        combo_control.bind("<<ComboboxSelected>>", self.cambiar_panel_control)

        # Marco dinámico
        self.marco_dinamico = tk.Frame(self.panel_central, bg="white")
        self.marco_dinamico.pack(fill="both", expand=True, pady=10)

        # Mostrar panel inicial
        self.mostrar_configuracion_inicial()

    def actualizar_visibilidad_boton_manual(self):
        if self.receta.get() == "PCB_Manual":
            if not self.boton_manual.winfo_ismapped():
                self.boton_manual.pack(fill="x", pady=5)
        else:
            self.boton_manual.pack_forget()

    def limpiar_marco_dinamico(self):
        # Limpiar widgets del panel dinámico
        for widget in self.marco_dinamico.winfo_children():
            widget.destroy()

    def cambiar_panel_control(self, event=None):
        # Cambiar entre panel inicial y panel de operación
        if self.menu_control.get() == "Configuración inicial":
            self.mostrar_configuracion_inicial()
        else:
            self.mostrar_configuracion_operacion()

    def mostrar_configuracion_inicial(self):
        # Mostrar botones de configuración inicial
        self.limpiar_marco_dinamico()

        tk.Button(self.marco_dinamico, text="Conexión con RoboDK", font="123Marker", bg="#b8d8f8", command=self.conectar_robodk).pack(fill="x", pady=5)
        tk.Button(self.marco_dinamico, text="Cargar Robot", font="123Marker", bg="#b8d8f8", command=self.cargar_robot).pack(fill="x", pady=5)
        tk.Button(self.marco_dinamico, text="Ir a Home", font="123Marker", bg="#c9f7c1", command=self.ir_home).pack(fill="x", pady=5)
        tk.Button(self.marco_dinamico, text="Ir a Target PCB", font="123Marker", bg="#c9f7c1", command=self.ir_pcb).pack(fill="x", pady=5)

    def mostrar_configuracion_operacion(self):
        # Mostrar botones de operación
        self.limpiar_marco_dinamico()

        tk.Button(self.marco_dinamico, text="Iniciar soldadura", font="123Marker", bg="#ffe6a7", command=self.iniciar_hilo_soldadura).pack(fill="x", pady=5)
        tk.Button(self.marco_dinamico, text="Pausar / Reanudar", font="123Marker", bg="#fff2b2", command=self.pausar_proceso).pack(fill="x", pady=5)
        tk.Button(self.marco_dinamico, text="Reset", font="123Marker", bg="#f3d1ff", command=self.reset_hmi).pack(fill="x", pady=5)
        tk.Button(self.marco_dinamico, text="Detener proceso", font="123Marker", bg="#f8c1c1", command=self.detener_proceso).pack(fill="x", pady=5)
        tk.Button(self.marco_dinamico, text="Parada de emergencia", font="123Marker", bg="#ff6b6b", fg="white", command=self.parada_emergencia).pack(fill="x", pady=5)

    def construir_panel_estado(self):
        # Mostrar estado actual
        tk.Label(self.panel_derecho, text="Estado actual:", bg="white", font=("123Marker", 10, "bold")).pack(anchor="w")
        tk.Label(self.panel_derecho, textvariable=self.estado, bg="white", fg="blue", font=("123Marker", 12)).pack(anchor="w", pady=5)

        # Mostrar puntos ejecutados
        tk.Label(self.panel_derecho, text="Puntos ejecutados:", bg="white", font=("123Marker", 10, "bold")).pack(anchor="w")
        tk.Label(self.panel_derecho, textvariable=self.puntos_ejecutados, bg="white", fg="green", font=("123Marker", 12)).pack(anchor="w", pady=5)

        # Mostrar alarma
        tk.Label(self.panel_derecho, text="Alarma:", bg="white", font=("123Marker", 10, "bold")).pack(anchor="w")
        tk.Label(
            self.panel_derecho,
            textvariable=self.alarma,
            bg="white",
            fg="red",
            wraplength=220,
            justify="left"
        ).pack(anchor="w", pady=5)

    def construir_log(self):
        # Crear área de log
        marco_log = tk.LabelFrame(
            self.ventana,
            text="Log del proceso",
            font=("123Marker", 11, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        marco_log.pack(fill="both", expand=True, padx=10, pady=10)

        self.texto_log = tk.Text(marco_log, height=10)
        self.texto_log.pack(fill="both", expand=True)

    def escribir_log(self, mensaje):
        # Escribir mensajes en el log
        self.texto_log.insert("end", mensaje + "\n")
        self.texto_log.see("end")

    def actualizar_receta(self, event=None):
        receta_actual = self.receta.get()
        componentes = self.recetas[receta_actual]

        self.actualizar_visibilidad_boton_manual()

        for fila in self.tabla_componentes.get_children():
            self.tabla_componentes.delete(fila)

        if not componentes:
            self.tabla_componentes.insert("", "end", values=("PCB manual vacía", "-", "-", "-"))
        else:
            for i, comp in enumerate(componentes):
                tag = "par" if i % 2 == 0 else "impar"
                self.tabla_componentes.insert(
                    "",
                    "end",
                    values=(
                        comp["tipo"],
                        comp["cantidad"],
                        comp["referencia"],
                        comp["pines"]
                    ),
                    tags=(tag,)
                )

        self.tabla_componentes.tag_configure("par", background="#f4f8fc")
        self.tabla_componentes.tag_configure("impar", background="white")

        self.calcular_puntos_totales()
        self.escribir_log(f"Receta seleccionada: {receta_actual}")

    def calcular_puntos_totales(self):
        # Calcular puntos de soldadura según los componentes
        receta_actual = self.receta.get()
        total = 0

        for comp in self.recetas[receta_actual]:
            total += comp["cantidad"] * comp["pines"]

        self.total_puntos.set(total)

    def abrir_ventana_componente(self):
        # Abrir ventana para agregar componentes a la receta manual
        if self.receta.get() != "PCB_Manual":
            messagebox.showinfo("Información", "Selecciona primero la opcion de PCB'Manual' para agregar componentes.")
            return

        ventana_comp = tk.Toplevel(self.ventana)
        ventana_comp.title("Agregar componente")
        ventana_comp.geometry("400x320")
        ventana_comp.configure(bg="white")

        tipo_var = tk.StringVar(value="Resistencia")
        cantidad_var = tk.IntVar(value=1)
        referencia_var = tk.StringVar(value="")

        tk.Label(ventana_comp, text="Tipo de componente:", font="123Marker", bg="white").pack(anchor="w", padx=10, pady=5)
        ttk.Combobox(
            ventana_comp,
            textvariable=tipo_var,
            values=list(self.pines_componentes.keys()),
            state="readonly"
        ).pack(fill="x", padx=10, pady=5)

        tk.Label(ventana_comp, text="Cantidad:", font="123Marker", bg="white").pack(anchor="w", padx=10, pady=5)
        tk.Entry(ventana_comp, textvariable=cantidad_var).pack(fill="x", padx=10, pady=5)

        tk.Label(ventana_comp, text="Referencia:", font="123Marker", bg="white").pack(anchor="w", padx=10, pady=5)
        tk.Entry(ventana_comp, textvariable=referencia_var).pack(fill="x", padx=10, pady=5)

        def guardar_componente():
            tipo = tipo_var.get()
            cantidad = cantidad_var.get()
            referencia = referencia_var.get().strip()
            pines = self.pines_componentes[tipo]

            if cantidad <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor que cero.")
                return

            if referencia == "":
                referencia = "Sin referencia"

            nuevo = {
                "tipo": tipo,
                "cantidad": cantidad,
                "referencia": referencia,
                "pines": pines
            }

            self.recetas["PCB_Manual"].append(nuevo)
            self.actualizar_receta()
            self.escribir_log(f"Componente agregado a la PCB manual: {tipo}, cantidad {cantidad}")
            ventana_comp.destroy()

        tk.Button(
            ventana_comp,
            text="Guardar componente",
            bg="#c9f7c1",
            font="123Marker",
            command=guardar_componente
        ).pack(fill="x", padx=10, pady=15)

    def generar_puntos(self):
        # Generar puntos automáticamente según total calculado
        puntos = []
        pitch = self.pitch.get()
        cantidad = self.total_puntos.get()

        columnas = 10
        filas = (cantidad + columnas - 1) // columnas

        for fila in range(filas):
            for columna in range(columnas):
                if len(puntos) < cantidad:
                    x = columna * pitch
                    y = fila * pitch
                    puntos.append((x, y))

        return puntos

    def conectar_robodk(self):
        # Conectar con RoboDK
        try:
            self.RDK = Robolink()
            self.estado.set("READY")
            self.alarma.set("Sin fallas")
            self.escribir_log("Conexión con RoboDK establecida.")
        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))
            self.escribir_log(f"Error al conectar con RoboDK: {e}")

    def cargar_robot(self):
        # Cargar robot y targets
        try:
            self.robot = self.RDK.ItemUserPick("Selecciona un robot", ITEM_TYPE_ROBOT)
            self.target_home = self.RDK.Item("Target_Casa", ITEM_TYPE_TARGET)
            self.target_pcb = self.RDK.Item("Target_PCB", ITEM_TYPE_TARGET)

            if not self.robot.Valid():
                raise Exception("No se seleccionó un robot válido.")
            if not self.target_home.Valid():
                raise Exception('No existe el target "Target_Casa".')
            if not self.target_pcb.Valid():
                raise Exception('No existe el target "Target_PCB".')

            self.robot.setPoseTool(self.robot.PoseTool())
            self.robot.setSpeed(20)
            self.robot.setRounding(1)

            self.estado.set("READY")
            self.alarma.set("Sin fallas")
            self.escribir_log("Robot y targets cargados correctamente.")
        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))
            self.escribir_log(f"Error al cargar robot: {e}")

    def ir_home(self):
        # Mover robot a home
        try:
            self.robot.MoveJ(self.target_home)
            self.estado.set("READY")
            self.escribir_log("Robot movido a Home.")
        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))
            self.escribir_log(f"Error al mover a Home: {e}")

    def ir_pcb(self):
        # Mover robot a target PCB
        try:
            self.robot.MoveJ(self.target_pcb)
            self.estado.set("READY")
            self.escribir_log("Robot movido al target PCB.")
        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))
            self.escribir_log(f"Error al mover a PCB: {e}")

    def rutina_soldadura(self):
        # Ejecutar rutina de soldadura
        try:
            self.estado.set("RUN")
            self.alarma.set("Sin fallas")
            self.proceso_pausado = False
            self.proceso_detenido = False
            self.emergencia_activa = False
            self.puntos_ejecutados.set(0)

            pose_pcb = self.target_pcb.Pose()
            puntos = self.generar_puntos()
            z_aproximacion = 5
            z_soldadura = 0

            self.robot.MoveJ(self.target_home)
            self.robot.MoveJ(self.target_pcb)
            self.escribir_log("Inicio de rutina de soldadura.")

            for i, (x, y) in enumerate(puntos, start=1):
                if self.emergencia_activa:
                    raise Exception("Parada de emergencia activada.")

                if self.proceso_detenido:
                    self.estado.set("STOP")
                    self.escribir_log("Proceso detenido por operador.")
                    return

                while self.proceso_pausado:
                    self.estado.set("PAUSE")
                    time.sleep(0.2)

                self.estado.set("RUN")
                self.robot.MoveJ(pose_pcb * transl(x, y, z_aproximacion))
                self.robot.MoveJ(pose_pcb * transl(x, y, z_soldadura))
                time.sleep(self.tiempo_soldadura.get())
                self.robot.MoveJ(pose_pcb * transl(x, y, z_aproximacion))

                self.puntos_ejecutados.set(i)
                self.escribir_log(f"Punto {i} soldado en X={x:.2f} mm, Y={y:.2f} mm")

            self.robot.MoveJ(self.target_pcb)
            self.robot.MoveJ(self.target_home)
            self.estado.set("DONE")
            self.escribir_log("Rutina completada. Robot regresó a Home.")

        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))
            self.escribir_log(f"Error en la rutina: {e}")

    def iniciar_hilo_soldadura(self):
        # Iniciar rutina en un hilo
        hilo = threading.Thread(target=self.rutina_soldadura, daemon=True)
        hilo.start()

    def pausar_proceso(self):
        # Pausar o reanudar el proceso
        self.proceso_pausado = not self.proceso_pausado
        if self.proceso_pausado:
            self.estado.set("PAUSE")
            self.escribir_log("Proceso pausado.")
        else:
            self.estado.set("RUN")
            self.escribir_log("Proceso reanudado.")

    def detener_proceso(self):
        # Detener proceso sin desenergizar
        self.proceso_detenido = True
        self.estado.set("STOP")
        self.alarma.set("Proceso detenido por operador.")
        self.escribir_log("Detener proceso activado.")

    def parada_emergencia(self):
        # Activar parada de emergencia
        self.emergencia_activa = True
        self.proceso_detenido = True
        self.estado.set("EMERGENCY")
        self.alarma.set("Parada de emergencia activada.")
        self.escribir_log("Parada de emergencia activada.")

        try:
            if self.robot:
                self.robot.Stop()
        except Exception:
            pass

    def reset_hmi(self):
        # Reiniciar HMI
        self.proceso_pausado = False
        self.proceso_detenido = False
        self.emergencia_activa = False
        self.estado.set("IDLE")
        self.alarma.set("Sin fallas")
        self.puntos_ejecutados.set(0)
        self.escribir_log("Sistema reiniciado.")


if __name__ == "__main__":
    ventana = tk.Tk()
    app = HMI_RoboDK(ventana)
    ventana.mainloop()