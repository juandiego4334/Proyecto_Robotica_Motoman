import tkinter as tk
from tkinter import ttk, messagebox
from robodk.robolink import *
from robodk.robomath import *
import threading
import time

class HMI_RoboDK:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("HMI Estacion de Soldadura PCB")
        self.ventana.state("zoomed")
        self.ventana.configure(bg="#dfe7ef")

        self.RDK = None
        self.robot = None

        self.home = [0, 0, 0, 0, 0, 0]
        self.aprox = [-88.98, 56.72, 27.52, 4.1, 11.93, 4.62]
        self.pcb = [-88.02, 62.59, 33.77, 3.8, 11.48, 3.8]

        self.proceso_pausado = False
        self.proceso_detenido = False
        self.emergencia = False
        self.hilo_soldadura = None
        self.stop_event = threading.Event()

        self.estado = tk.StringVar(value="Inactivo")
        self.alarma = tk.StringVar(value="Sin fallas")
        self.receta = tk.StringVar(value="PCB_1")
        self.pitch = tk.DoubleVar(value=2.54)
        self.tiempo = tk.DoubleVar(value=0.4)
        self.puntos_ejecutados = tk.IntVar(value=0)
        self.total_puntos = tk.IntVar(value=0)

        self.recetas = {
    "PCB_1": {
        "componentes": [
            ("Resistencia", 5, "1k", 2),
            ("Resistencia", 8, "2.2k", 2),
            ("Resistencia", 3, "100k", 2),
            ("Capacitor", 8, "100nF", 2),
            ("LED", 2, "Rojo", 2),
            ("LED", 2, "Verde", 2),
            ("Diodo", 2, "1N4148", 2),
            ("Conector", 2, "JST 2P", 2)
        ],
        "puntos": [
            (1, 1, "R1", 1), (2, 1, "R1", 2),
            (3, 1, "R2", 1), (4, 1, "R2", 2),
            (5, 1, "R3", 1), (6, 1, "R3", 2),
            (7, 1, "R4", 1), (8, 1, "R4", 2),
            (1, 2, "R5", 1), (2, 2, "R5", 2),
            (3, 2, "R6", 1), (4, 2, "R6", 2),
            (5, 2, "R7", 1), (6, 2, "R7", 2),
            (7, 2, "R8", 1), (8, 2, "R8", 2),
            (1, 3, "R9", 1), (2, 3, "R9", 2),
            (3, 3, "R10", 1), (4, 3, "R10", 2),
            (5, 3, "R11", 1), (6, 3, "R11", 2),
            (7, 3, "R12", 1), (8, 3, "R12", 2),
            (1, 4, "R13", 1), (2, 4, "R13", 2),
            (3, 4, "R14", 1), (4, 4, "R14", 2),
            (5, 4, "R15", 1), (6, 4, "R15", 2),
            (7, 4, "R16", 1), (8, 4, "R16", 2),
            (1, 5, "C1", 1), (2, 5, "C1", 2),
            (3, 5, "C2", 1), (4, 5, "C2", 2),
            (5, 5, "C3", 1), (6, 5, "C3", 2),
            (7, 5, "C4", 1), (8, 5, "C4", 2),
            (1, 6, "C5", 1), (2, 6, "C5", 2),
            (3, 6, "C6", 1), (4, 6, "C6", 2),
            (5, 6, "C7", 1), (6, 6, "C7", 2),
            (7, 6, "C8", 1), (8, 6, "C8", 2),
            (1, 7, "LED1", 1), (2, 7, "LED1", 2),
            (3, 7, "LED2", 1), (4, 7, "LED2", 2),
            (5, 7, "LED3", 1), (6, 7, "LED3", 2),
            (7, 7, "LED4", 1), (8, 7, "LED4", 2),
            (1, 8, "D1", 1), (2, 8, "D1", 2),
            (3, 8, "D2", 1), (4, 8, "D2", 2),
            (5, 8, "J1", 1), (6, 8, "J1", 2),
            (7, 8, "J2", 1), (8, 8, "J2", 2)
        ]
    },

    "PCB_2": {
        "componentes": [
            ("Resistencia", 7, "220 ohm", 2),
            ("Resistencia", 11, "10k", 2),
            ("Capacitor", 6, "10uF", 2),
            ("Diodo", 4, "1N4007", 2),
            ("Transistor", 3, "BC547", 3),
            ("Conector", 2, "Bornera 2P", 2),
            ("CI DIP-8", 2, "LM358", 8)
        ],
        "puntos": [
            (1, 1, "R1", 1), (2, 1, "R1", 2),
            (3, 1, "R2", 1), (4, 1, "R2", 2),
            (5, 1, "R3", 1), (6, 1, "R3", 2),
            (7, 1, "R4", 1), (8, 1, "R4", 2),
            (1, 2, "R5", 1), (2, 2, "R5", 2),
            (3, 2, "R6", 1), (4, 2, "R6", 2),
            (5, 2, "R7", 1), (6, 2, "R7", 2),
            (7, 2, "R8", 1), (8, 2, "R8", 2),
            (1, 3, "R9", 1), (2, 3, "R9", 2),
            (3, 3, "R10", 1), (4, 3, "R10", 2),
            (5, 3, "R11", 1), (6, 3, "R11", 2),
            (7, 3, "R12", 1), (8, 3, "R12", 2),
            (1, 4, "R13", 1), (2, 4, "R13", 2),
            (3, 4, "R14", 1), (4, 4, "R14", 2),
            (5, 4, "R15", 1), (6, 4, "R15", 2),
            (7, 4, "R16", 1), (8, 4, "R16", 2),
            (1, 5, "R17", 1), (2, 5, "R17", 2),
            (3, 5, "R18", 1), (4, 5, "R18", 2),
            (5, 5, "C1", 1), (6, 5, "C1", 2),
            (7, 5, "C2", 1), (8, 5, "C2", 2),
            (1, 6, "C3", 1), (2, 6, "C3", 2),
            (3, 6, "C4", 1), (4, 6, "C4", 2),
            (5, 6, "C5", 1), (6, 6, "C5", 2),
            (7, 6, "C6", 1), (8, 6, "C6", 2),
            (1, 7, "D1", 1), (2, 7, "D1", 2),
            (3, 7, "D2", 1), (4, 7, "D2", 2),
            (5, 7, "D3", 1), (6, 7, "D3", 2),
            (7, 7, "D4", 1), (8, 7, "D4", 2),
            (1, 8, "Q1", 1), (2, 8, "Q1", 2), (3, 8, "Q1", 3),
            (4, 8, "Q2", 1), (5, 8, "Q2", 2), (6, 8, "Q2", 3),
            (1, 9, "Q3", 1), (2, 9, "Q3", 2), (3, 9, "Q3", 3),
            (4, 9, "J1", 1), (5, 9, "J1", 2),
            (6, 9, "J2", 1), (7, 9, "J2", 2),
            (1, 10, "U1", 1), (2, 10, "U1", 2), (3, 10, "U1", 3), (4, 10, "U1", 4),
            (5, 10, "U1", 5), (6, 10, "U1", 6), (7, 10, "U1", 7), (8, 10, "U1", 8),
            (1, 11, "U2", 1), (2, 11, "U2", 2), (3, 11, "U2", 3), (4, 11, "U2", 4),
            (5, 11, "U2", 5), (6, 11, "U2", 6), (7, 11, "U2", 7), (8, 11, "U2", 8)
        ]
    },

    "PCB_Nueva": {
        "componentes": [],
        "puntos": []
    }
}

        self.crear_interfaz()
        self.actualizar_receta()

    def crear_interfaz(self):
        tk.Label(self.ventana, text="HMI - Estación de Soldadura",
                 font=("Arial", 18, "bold"), bg="#dfe7ef", fg="#1f3b5b").pack(pady=10)

        marco = tk.Frame(self.ventana, bg="#dfe7ef")
        marco.pack(fill="both", expand=True, padx=10, pady=10)

        self.izq = tk.LabelFrame(marco, text="Recetas", bg="white", padx=10, pady=10)
        self.izq.pack(side="left", fill="y", padx=8)

        self.centro = tk.LabelFrame(marco, text="Control", bg="white", padx=10, pady=10)
        self.centro.pack(side="left", fill="both", expand=True, padx=8)

        self.der = tk.LabelFrame(marco, text="Estado", bg="white", padx=10, pady=10)
        self.der.pack(side="right", fill="y", padx=8)

        self.panel_recetas()
        self.panel_control()
        self.panel_estado()
        self.panel_log()

    def panel_recetas(self):
        tk.Label(self.izq, text="Selecciona una PCB", bg="white").pack(anchor="w")
        combo = ttk.Combobox(self.izq, textvariable=self.receta,
                             values=list(self.recetas.keys()), state="readonly")
        combo.pack(fill="x", pady=5)
        combo.bind("<<ComboboxSelected>>", self.actualizar_receta)

        self.btn_punto = tk.Button(self.izq, text="Agregar punto manual",
                                   bg="#d9fbd9", command=self.agregar_Componentes)

        tk.Label(self.izq, text="Componentes:", bg="white").pack(anchor="w", pady=(10, 0))
        self.tabla_comp = ttk.Treeview(self.izq, columns=("tipo", "cant", "ref", "pin"),
                                       show="headings", height=5)
        for c, t, w in [("tipo", "Tipo", 120), ("cant", "Cant", 50),
                        ("ref", "Ref", 90), ("pin", "Pines", 50)]:
            self.tabla_comp.heading(c, text=t)
            self.tabla_comp.column(c, width=w, anchor="center")
        self.tabla_comp.pack(fill="x", pady=5)

        tk.Label(self.izq, text="Puntos:", bg="white").pack(anchor="w")
        self.tabla_puntos = ttk.Treeview(self.izq, columns=("x", "y", "ref", "pin"),
                                         show="headings", height=6)
        for c, t, w in [("x", "X", 50), ("y", "Y", 50), ("ref", "Ref", 80), ("pin", "Pin", 50)]:
            self.tabla_puntos.heading(c, text=t)
            self.tabla_puntos.column(c, width=w, anchor="center")
        self.tabla_puntos.pack(fill="x", pady=5)

        tk.Label(self.izq, text="Pitch [mm]:", bg="white").pack(anchor="w")
        tk.Entry(self.izq, textvariable=self.pitch).pack(fill="x", pady=5)

        tk.Label(self.izq, text="Tiempo de soldadura [s]:", bg="white").pack(anchor="w")
        tk.Entry(self.izq, textvariable=self.tiempo).pack(fill="x", pady=5)

        tk.Label(self.izq, text="Total puntos:", bg="white").pack(anchor="w")
        tk.Entry(self.izq, textvariable=self.total_puntos, state="readonly").pack(fill="x", pady=5)

    def panel_control(self):
        botones = [
            ("Conectar RoboDK", self.conectar_robodk, "#b8d8f8"),
            ("Cargar robot", self.cargar_robot, "#b8d8f8"),
            ("Ir a Home", self.ir_home, "#c9f7c1"),
            ("Ir a Aproximación", self.ir_aprox, "#c9f7c1"),
            ("Validar puntos", self.validar_puntos, "#d6ecff"),
            ("Iniciar soldadura", self.iniciar_hilo, "#ffe6a7"),
            ("Pausar / Reanudar", self.pausar, "#fff2b2"),
            ("Detener", self.detener, "#f8c1c1"),
            ("Emergencia", self.parada_emergencia, "#ff6b6b"),
            ("Reset", self.reset, "#f3d1ff")
        ]
        for texto, comando, color in botones:
            tk.Button(self.centro, text=texto, bg=color, command=comando).pack(fill="x", pady=5)

    def panel_estado(self):
        tk.Label(self.der, text="Estado:", bg="white").pack(anchor="w")
        tk.Label(self.der, textvariable=self.estado, bg="white", fg="blue").pack(anchor="w", pady=5)

        tk.Label(self.der, text="Puntos ejecutados:", bg="white").pack(anchor="w")
        tk.Label(self.der, textvariable=self.puntos_ejecutados, bg="white", fg="green").pack(anchor="w", pady=5)

        tk.Label(self.der, text="Alarma:", bg="white").pack(anchor="w")
        tk.Label(self.der, textvariable=self.alarma, bg="white", fg="red",
                 wraplength=220, justify="left").pack(anchor="w", pady=5)

    def panel_log(self):
        marco_log = tk.LabelFrame(self.ventana, text="Log", bg="white", padx=10, pady=10)
        marco_log.pack(fill="both", expand=True, padx=10, pady=10)
        self.log = tk.Text(marco_log, height=10)
        self.log.pack(fill="both", expand=True)

    def escribir_log(self, texto):
        self.log.insert("end", texto + "\n")
        self.log.see("end")

    def actualizar_receta(self, event=None):
        receta = self.recetas[self.receta.get()]

        for i in self.tabla_comp.get_children():
            self.tabla_comp.delete(i)
        for i in self.tabla_puntos.get_children():
            self.tabla_puntos.delete(i)

        for comp in receta["componentes"]:
            self.tabla_comp.insert("", "end", values=comp)

        for x, y, ref, pin in receta["puntos"]:
            self.tabla_puntos.insert("", "end", values=(x, y, ref, pin))

        self.total_puntos.set(len(receta["puntos"]))

        if self.receta.get() == "PCB_Nueva":
            self.btn_punto.pack(fill="x", pady=5)
        else:
            self.btn_punto.pack_forget()

        self.escribir_log(f"Receta seleccionada: {self.receta.get()}")

    def agregar_Componentes(self):
        if self.receta.get() != "PCB_Nueva":
            return

        ventana = tk.Toplevel(self.ventana)
        ventana.title("Agregar Componente")
        ventana.geometry("300x250")

        x_var = tk.DoubleVar(value=0)
        y_var = tk.DoubleVar(value=0)
        ref_var = tk.StringVar(value="P1")
        pin_var = tk.IntVar(value=1)

        for texto, var in [("X:", x_var), ("Y:", y_var), ("Referencia:", ref_var), ("Pin:", pin_var)]:
            tk.Label(ventana, text=texto).pack(anchor="w", padx=10, pady=5)
            tk.Entry(ventana, textvariable=var).pack(fill="x", padx=10)

        def guardar():
            self.recetas["PCB_Nueva"]["puntos"].append(
                (x_var.get(), y_var.get(), ref_var.get(), pin_var.get())
            )
            self.actualizar_receta()
            self.escribir_log(f"Punto agregado: X={x_var.get()}, Y={y_var.get()}")
            ventana.destroy()

        tk.Button(ventana, text="Guardar", bg="#c9f7c1", command=guardar).pack(fill="x", padx=10, pady=15)

    def obtener_puntos_mm(self):
        puntos = []
        for x, y, ref, pin in self.recetas[self.receta.get()]["puntos"]:
            puntos.append((x * self.pitch.get(), y * self.pitch.get(), ref, pin))
        return puntos

    def conectar_robodk(self):
        try:
            self.RDK = Robolink()
            self.estado.set("READY")
            self.alarma.set("Sin fallas")
            self.escribir_log("Conexión con RoboDK establecida.")
        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))

    def cargar_robot(self):
        try:
            self.robot = self.RDK.ItemUserPick("Selecciona un robot", ITEM_TYPE_ROBOT)
            if not self.robot.Valid():
                raise Exception("Robot no válido.")
            
            self.robot.setSpeed(50)
            self.robot.setRounding(5)
            self.estado.set("READY")
            self.escribir_log("Robot cargado correctamente.")

        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))

    def ir_home(self):
        try:
            self.robot.MoveJ(self.home)
            self.escribir_log("Robot en Home.")
        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))

    def ir_aprox(self):
        try:
            self.robot.MoveJ(self.aprox)
            self.escribir_log("Robot en aproximación.")
        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))

    def validar_puntos(self):
        try:
            if not self.robot:
                raise Exception("Primero carga el robot.")
            pose_pcb = self.robot.SolveFK(self.pcb)

            for i, (x, y, ref, pin) in enumerate(self.obtener_puntos_mm(), start=1):
                pose1 = pose_pcb * transl(x, y, -10)
                pose2 = pose_pcb * transl(x, y, 1)
                j1 = self.robot.SolveIK(pose1)
                j2 = self.robot.SolveIK(pose2)
                if j1 is None or j2 is None:
                    raise Exception(f"Error en punto {i}: {ref}")

            self.estado.set("READY")
            self.alarma.set("Puntos válidos")
            self.escribir_log("Todos los puntos fueron validados.")
        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))
            self.escribir_log(f"Validación fallida: {e}")

    def rutina_soldadura(self):
        try:
            puntos = self.obtener_puntos_mm()
            if not puntos:
                raise Exception("No hay puntos para soldar.")
            if not self.robot:
                raise Exception("Primero debes cargar el robot.")

            self.puntos_ejecutados.set(0)
            self.estado.set("RUN")
            self.alarma.set("Sin fallas")

            pose_pcb = self.robot.SolveFK(self.pcb)
            self.robot.MoveJ(self.aprox)
            self.robot.setSpeed(10)
            self.escribir_log("Inicio de soldadura.")

            for i, (x, y, ref, pin) in enumerate(puntos, start=1):
                if self.stop_event.is_set() or self.proceso_detenido:
                    self.estado.set("STOP")
                    self.escribir_log("Rutina detenida por operador/reset.")
                    return

                if self.emergencia:
                    raise Exception("Parada de emergencia activada.")

                while self.proceso_pausado:
                    self.estado.set("PAUSE")
                    if self.stop_event.is_set() or self.proceso_detenido:
                        self.estado.set("STOP")
                        self.escribir_log("Rutina cancelada durante pausa.")
                        return
                    time.sleep(0.2)

                self.estado.set("RUN")

                pose_aprox = pose_pcb * transl(x, y, -10)
                pose_sold = pose_pcb * transl(x, y, 1)

                joints_aprox = self.robot.SolveIK(pose_aprox)
                joints_sold = self.robot.SolveIK(pose_sold)

                self.robot.MoveJ(joints_aprox)
                self.robot.MoveJ(joints_sold)
                time.sleep(self.tiempo.get())
                self.robot.MoveJ(joints_aprox)

                self.puntos_ejecutados.set(i)
                self.escribir_log(f"Punto {i}: {ref} pin {pin} | X={x:.2f}, Y={y:.2f}")

            self.robot.MoveJ(self.aprox)
            self.robot.MoveJ(self.home)
            self.estado.set("DONE")
            self.escribir_log("Proceso terminado correctamente.")

        except Exception as e:
            self.estado.set("FAULT")
            self.alarma.set(str(e))
            self.escribir_log(f"Error en rutina: {e}") 

    def iniciar_hilo(self):
            if self.hilo_soldadura and self.hilo_soldadura.is_alive():
                self.escribir_log("La rutina ya está en ejecución.")
                return

            self.stop_event.clear()
            self.proceso_detenido = False
            self.proceso_pausado = False
            self.emergencia = False

            self.hilo_soldadura = threading.Thread(
                target=self.rutina_soldadura,
                daemon=True
            )
            self.hilo_soldadura.start()
            self.escribir_log("Hilo de soldadura iniciado.")

    def pausar(self):
        self.proceso_pausado = not self.proceso_pausado
        self.escribir_log("Proceso pausado." if self.proceso_pausado else "Proceso reanudado.")

    def detener(self):
        self.proceso_detenido = True
        self.stop_event.set()
        self.estado.set("STOP")
        self.alarma.set("Proceso detenido por operador.")
        self.escribir_log("Proceso detenido.")
        try:
            if self.robot:
                self.robot.Stop()
        except:
            pass
        
    def parada_emergencia(self):
        self.emergencia = True
        self.proceso_detenido = True
        self.stop_event.set()
        self.estado.set("EMERGENCY")
        self.alarma.set("Parada de emergencia activada.")
        self.escribir_log("Emergencia activada.")
        try:
            if self.robot:
                self.robot.Stop()
        except:
            pass
        
    def reset(self):
        self.proceso_pausado = False
        self.proceso_detenido = True
        self.emergencia = False
        self.stop_event.set()

        try:
            if self.robot:
                self.robot.Stop()
        except:
            pass

        self.estado.set("Inactivo")
        self.alarma.set("Sin fallas")
        self.puntos_ejecutados.set(0)
        self.escribir_log("Sistema reiniciado.")


if __name__ == "__main__":
    ventana = tk.Tk()
    pantalla = HMI_RoboDK(ventana)
    ventana.mainloop()
