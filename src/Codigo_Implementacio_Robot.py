from robodk.robolink import *
from robodk.robomath import *
import time

# 1) Conexión a RoboDK e inicialización

RDK = Robolink()

robot = RDK.ItemUserPick("Selecciona un robot", ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise Exception("No se ha seleccionado un robot válido.")

print("Robot seleccionado correctamente.")


# 2) Cargar targets y herramienta
target_home = RDK.Item("Target_Casa", ITEM_TYPE_TARGET)
if not target_home.Valid():
    raise Exception('No se encontró el target "Target_Casa".')

target_pcb = RDK.Item("Target_PCB", ITEM_TYPE_TARGET)
if not target_pcb.Valid():
    raise Exception('No se encontró el target "Target_PCB".')

robot.setPoseTool(robot.PoseTool())
robot.setSpeed(20)
robot.setRounding(1)


# 3) Parámetros de soldadura

z_soldadura = 0
z_aproximacion = 2
tiempo_soldadura = 0.4

# Puntos sobre el plano local de la PCB
pitch = 2.54

puntos_soldadura = [
    (0*pitch, 0*pitch), (1*pitch, 0*pitch), (2*pitch, 0*pitch), (3*pitch, 0*pitch), (4*pitch, 0*pitch),
    (5*pitch, 0*pitch), (6*pitch, 0*pitch), (7*pitch, 0*pitch), (8*pitch, 0*pitch), (9*pitch, 0*pitch),

    (0*pitch, 1*pitch), (1*pitch, 1*pitch), (2*pitch, 1*pitch), (3*pitch, 1*pitch), (4*pitch, 1*pitch),
    (5*pitch, 1*pitch), (6*pitch, 1*pitch), (7*pitch, 1*pitch), (8*pitch, 1*pitch), (9*pitch, 1*pitch),

    (0*pitch, 2*pitch), (1*pitch, 2*pitch), (2*pitch, 2*pitch), (3*pitch, 2*pitch), (4*pitch, 2*pitch),
    (5*pitch, 2*pitch), (6*pitch, 2*pitch), (7*pitch, 2*pitch), (8*pitch, 2*pitch), (9*pitch, 2*pitch),

    (0*pitch, 3*pitch), (1*pitch, 3*pitch), (2*pitch, 3*pitch), (3*pitch, 3*pitch), (4*pitch, 3*pitch),
    (5*pitch, 3*pitch), (6*pitch, 3*pitch), (7*pitch, 3*pitch), (8*pitch, 3*pitch), (9*pitch, 3*pitch),

    (0*pitch, 4*pitch), (1*pitch, 4*pitch), (2*pitch, 4*pitch), (3*pitch, 4*pitch), (4*pitch, 4*pitch),
    (5*pitch, 4*pitch), (6*pitch, 4*pitch), (7*pitch, 4*pitch), (8*pitch, 4*pitch), (9*pitch, 4*pitch)
]

pose_pcb = target_pcb.Pose()


# 4) Inicio en home

print("Moviendo a home...")
robot.MoveJ(target_home)
time.sleep(0.5)


# 5) Ir al target de la PCB

print("Moviendo al target de la PCB...")
robot.MoveJ(target_pcb)
time.sleep(0.5)


# 6) Rutina de soldadura

print("Iniciando rutina de soldadura...")

for i, (x, y) in enumerate(puntos_soldadura):
    print(f"Soldando punto {i+1}: X={x}, Y={y}")

    # Aproximación al punto en el plano local de la PCB
    robot.MoveJ(pose_pcb * transl(x, y, z_aproximacion))

    # Bajada perpendicular al plano de la PCB
    robot.MoveJ(pose_pcb * transl(x, y, z_soldadura))

    # Simulación de soldadura
    time.sleep(tiempo_soldadura)

    # Retiro perpendicular al plano
    robot.MoveJ(pose_pcb * transl(x, y, z_aproximacion))


# 7) Volver al target de la PCB
print("Volviendo al target de la PCB...")
robot.MoveJ(target_pcb)
time.sleep(0.5)

# 8) Regresar a home
print("Regresando a home...")
robot.MoveJ(target_home)

