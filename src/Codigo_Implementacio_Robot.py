from robodk.robolink import *
from robodk.robomath import *
import time

# 1) Conexión a RoboDK e inicialización
RDK = Robolink()
robot = RDK.ItemUserPick("Selecciona un robot", ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise Exception("No se ha seleccionado un robot válido.")


#Conectar al robot físico
if not robot.Connect():
    raise Exception("No se pudo conectar al robot. Verifica que esté en modo remoto y que la configuración sea correcta.")

# Confirmar conexión
if not robot.ConnectedState():
    raise Exception("El robot no está conectado correctamente. Revisa la conexión.")

print("Robot conectado correctamente.")

# 2) Poses articulares y configuracion de movimiento
robot.setSpeed(50)
robot.setRounding(5)

Home = [0, 0, 0, 0, 0, 0]
aprox = [-88.98, 56.72, 27.52, 4.1, 11.93, 4.62]
PCB = [-88.02, 62.59, 33.77, 3.8, 11.48, 3.8]

# 4) Parámetros de soldadura
z_soldadura = 4
z_aproximacion = -10
tiempo_soldadura = 10
pitch = 2.54
Numero_de_PCB = 1

# 5) Puntos sobre el plano local de la PCB
puntos_soldadura = [
    (3*pitch, 7*pitch), (4*pitch, 8*pitch), (3*pitch, 9*pitch),
    (4*pitch, 9*pitch), (3*pitch, 8*pitch), (4*pitch, 7*pitch)
]

# 6) Rutina de soldadura

# Movimiento al punto de aproximacion
print("Moviendo al punto de aproximacion...")
robot.MoveJ(aprox)
time.sleep(2)

# Guardar la pose de PCB sin mover el robot allí
pose_pcb = robot.SolveFK(PCB)

#inicio de soldadura
print("Iniciando rutina de soldadura...")
robot.setSpeed(10)

for j in range(Numero_de_PCB):
    for i, (x, y) in enumerate(puntos_soldadura, start=1):
        
	#print(f"Soldando punto {i}: X={x}, Y={y}")

        pose_aprox = pose_pcb * transl(x, y, z_aproximacion)
        pose_sold = pose_pcb * transl(x, y, z_soldadura)

        joints_aprox = robot.SolveIK(pose_aprox)
        joints_sold = robot.SolveIK(pose_sold)

        robot.MoveJ(joints_aprox)
        robot.MoveJ(joints_sold)
        time.sleep(tiempo_soldadura)
        robot.MoveJ(joints_aprox)

    print("Volviendo al target de la aproximación...")
    robot.MoveJ(aprox)
    time.sleep(3)

print("Regresando a home...")
robot.MoveJ(Home)

print("PCB's Completadas")
