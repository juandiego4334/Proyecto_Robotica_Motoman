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

# 2) Poses articulares
#joints = robot.Joints().list()
#print("Posiciones actuales:", joints)
# Los índices debes confirmarlos en tu estación
#joints[6] = 162700       # Eje externo rotativo: 45 grados
#joints[7] = 143700    
#robot.MoveJ(joints)
Home = [0, 0, 0, 0, 0, 0]
aprox = [-88.98,56.72,27.52,4.1,11.93,4.62]
PCB = [-88.02,62.59,33.77,3.8,11.48,3.8]

# 3) Configuración de herramienta y movimiento
#robot.setPoseTool(robot.PoseTool())
robot.setSpeed(50)
robot.setRounding(5)

# 4) Parámetros de soldadura
z_soldadura = 0
z_aproximacion = -5
tiempo_soldadura = 1.5
pitch = 2.54
Numero_de_PCB = 1

# 5) Puntos sobre el plano local de la PCB
puntos_soldadura = [
    (3*pitch, 7*pitch), (3*pitch, 8*pitch), (3*pitch, 9*pitch), (4*pitch, 7*pitch), (4*pitch, 8*pitch), (4*pitch, 9*pitch)]

# 6) Inicio en home
#print("Moviendo a home...")
#robot.MoveJ(Home)
#time.sleep(5)

# 7) Ir a aproximación y PCB
print("Moviendo al target de la aproximacion...")
robot.MoveJ(aprox)
time.sleep(2)


# 7) Ir a aproximación y PCB
robot.MoveJ(PCB)

# Guardar la pose cartesiana actual de la PCB
pose_pcb = robot.Pose()
robot.MoveJ(pose_pcb * transl(1, 1, z_aproximacion))
        
# 8) Rutina de soldadura
print("Iniciando rutina de soldadura...")
robot.setSpeed(10)

for j in range(Numero_de_PCB):
    for i, (x, y) in enumerate(puntos_soldadura, start=1):
        # print(f"Soldando punto {i}: X={x}, Y={y}")
        robot.MoveJ(pose_pcb * transl(x, y, z_aproximacion))
        robot.MoveJ(pose_pcb * transl(x, y, z_soldadura))
        time.sleep(tiempo_soldadura)
        robot.MoveJ(pose_pcb * transl(x, y, z_aproximacion))

#9) Volver a aproximación
    print("Volviendo al target de la aproximacion...")
    robot.MoveJ(aprox)
    time.sleep(3)


# 10) Regresar a home
print("Regresando a home...")
#robot.MoveJ(Home)

print("PCB's Completadas")
