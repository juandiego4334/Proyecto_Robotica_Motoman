# Proyecto_Robotica_Motoman
Proyecto final robótica semestre 2026-I
## 1. Bitácora del desarrollo

## 2. Diagrama de flujo del proceso global y por estación

## 3.Diseño del gripper y del workobject

## 4. Simulación desde RoboDK

## 5.Código fuente utilizado
Debido a que RoboDK no permite una comunicación en tiempo real de el programa y el robot, la interfaz gráfica no se puede comunicar con el robot en tiempo real. Es por esto que se tienen 2 códigos, uno donde se simula la comunicación real entre la interfaz gráfica y el robot, y el código aplicado en la realidad.
### 5.1 Código con interfaz gráfica
El programa en Python puede consultarse aquí:
[Ver código](src/HMI_Simulacion.py)
### 5.2 Código implementado en el robot real
El programa en Python puede consultarse aquí:
[Ver código](src/Codigo_Implementacio_Robot.py)
## 6. Comparación manual vs automatizado

## 7. Diagrama de flujo de acciones del robot

## 8. Plano de planta de la ubicación de cada uno de los elementos

## 9. Descripción del código implementado para la soldadura

El programa en Python puede consultarse aquí:
[Ver código](src/Codigo_Implementacio_Robot.py)
 
Este programa conecta con el robot físico a través de RoboDK y ejecuta una rutina automática de soldadura sobre una o varias PCB (placas de circuito impreso), calculando cada punto a partir de transformaciones locales respecto a una pose de referencia. A continuación se explican las funciones y parámetros nuevos vistos.
 
### 9.1 Importación de librerías
Además de robolink y robomath (comunicación con RoboDK y funciones matemáticas), se importa la librería time, que permite generar pausas controladas durante la ejecución, por ejemplo mientras el robot se estabiliza en una posición o mientras dura la soldadura.
```python
from robodk.robolink import *
from robodk.robomath import *
import time
```
 
### 9.2 Conexión a RoboDK y al robot físico
Se selecciona el robot desde la estación de RoboDK y se valida que la selección sea correcta con `robot.Valid()`. Después se intenta la conexión con el controlador físico mediante `robot.Connect()` y se confirma el estado con `robot.ConnectedState()` (ambas devuelven `True` o `False`). Si alguna comprobación falla, el programa se detiene lanzando una excepción con un mensaje descriptivo, en lugar de continuar con un robot no disponible.
```python
robot = RDK.ItemUserPick("Selecciona un robot", ITEM_TYPE_ROBOT)
if not robot.Valid():
    raise Exception("No se ha seleccionado un robot válido.")
 
if not robot.Connect():
    raise Exception("No se pudo conectar al robot. Verifica que esté en modo remoto y que la configuración sea correcta.")
 
if not robot.ConnectedState():
    raise Exception("El robot no está conectado correctamente. Revisa la conexión.")
```
 
### 9.3 Parámetros de movimiento y posiciones articulares
Se define la velocidad y la tolerancia (rounding) del movimiento, y se guardan las posiciones clave del robot como arreglos de 6 valores articulares, uno por cada eje: `Home` (posición de reposo), `aprox` (punto de aproximación seguro) y `PCB` (punto de referencia sobre la placa).
```python
robot.setSpeed(50)
robot.setRounding(5)
 
Home  = [0, 0, 0, 0, 0, 0]
aprox = [-88.98, 56.72, 27.52, 4.1, 11.93, 4.62]
PCB   = [-88.02, 62.59, 33.77, 3.8, 11.48, 3.8]
```
 
### 9.4 Parámetros de soldadura
Estas variables configuran la geometría y el tiempo de la rutina: la altura de soldadura, la altura de aproximación (más alta, para evitar colisiones al desplazarse entre puntos), el tiempo que el robot permanece soldando cada punto, el paso entre orificios de la placa (`pitch`, en milímetros) y el número de PCB que se van a procesar en la misma ejecución.
```python
z_soldadura = 4
z_aproximacion = -10
tiempo_soldadura = 10
pitch = 2.54
Numero_de_PCB = 1
```
 
### 9.5 Puntos de soldadura en el plano local de la PCB
Los puntos a soldar se definen como coordenadas (x, y) en el plano local de la placa, expresadas en múltiplos de `pitch`. Esto permite ubicar cada punto según la cuadrícula de orificios de la PCB, sin depender de su posición global dentro de la estación.
```python
puntos_soldadura = [
    (3*pitch, 7*pitch), (4*pitch, 8*pitch), (3*pitch, 9*pitch),
    (4*pitch, 9*pitch), (3*pitch, 8*pitch), (4*pitch, 7*pitch)
]
```
 
### 9.6 Obtención de la pose de referencia (cinemática directa)
El robot se mueve primero al punto de aproximación. Luego, con `SolveFK`, se calcula la pose cartesiana (posición y orientación) correspondiente a las articulaciones de `PCB`, sin necesidad de mover físicamente el robot hasta ese punto. Esta pose (`pose_pcb`) se usa como referencia para ubicar todos los puntos de soldadura.
```python
robot.MoveJ(aprox)
time.sleep(2)
 
pose_pcb = robot.SolveFK(PCB)
```
 
### 9.7 Rutina de soldadura: transformación de puntos y cinemática inversa
Para cada punto de la lista, se calculan dos poses a partir de `pose_pcb` usando `transl(x, y, z)`, que aplica una traslación local sobre esa pose de referencia: una a la altura de aproximación (segura) y otra a la altura de soldadura. Con `SolveIK` se obtienen los valores articulares correspondientes a cada pose, y el robot se desplaza primero al punto de aproximación, desciende al punto de soldadura, espera el tiempo definido en `tiempo_soldadura`, y se retira nuevamente al punto de aproximación antes de continuar con el siguiente punto. Al terminar todos los puntos de una PCB, el robot vuelve al target de aproximación antes de procesar la siguiente placa (si `Numero_de_PCB` > 1).
```python
for j in range(Numero_de_PCB):
    for i, (x, y) in enumerate(puntos_soldadura, start=1):
 
        pose_aprox = pose_pcb * transl(x, y, z_aproximacion)
        pose_sold  = pose_pcb * transl(x, y, z_soldadura)
 
        joints_aprox = robot.SolveIK(pose_aprox)
        joints_sold  = robot.SolveIK(pose_sold)
 
        robot.MoveJ(joints_aprox)
        robot.MoveJ(joints_sold)
        time.sleep(tiempo_soldadura)
        robot.MoveJ(joints_aprox)
 
    robot.MoveJ(aprox)
    time.sleep(3)
```
 
### 9.8 Retorno a posición de home
Una vez completadas todas las PCB configuradas, el robot regresa a la posición de home (todas las articulaciones en 0°) y se imprime un mensaje confirmando que la rutina terminó.
```python
robot.MoveJ(Home)
print("PCB's Completadas")
```

## 10. Vídeos de simulación y de implementación 
