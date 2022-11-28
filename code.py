import board
import time
from digitalio import DigitalInOut, Direction, Pull
import analogio
from adafruit_motor import stepper
import busio
import json
import adafruit_datetime 

#-----------------------I2C---------------
slave_bus = busio.I2C(sda=board.GP6, scl=board.GP7)
uart = busio.UART(board.GP0, board.GP1)

# Led
ledBlanco = DigitalInOut(board.GP13)
ledBlanco.direction = Direction.OUTPUT

led = DigitalInOut(board.LED)
led.direction = Direction.OUTPUT
stepper_state = None

def parpadeo(times):
    for _ in range(times):
        ledBlanco.value = False
        time.sleep(0.1)
        ledBlanco.value = True
        time.sleep(0.1)

# Fotointerruptor
interruptor = DigitalInOut(board.GP14)
interruptor.direction = Direction.INPUT
interruptor.pull = Pull.UP

# Joystick
eje_y = analogio.AnalogIn(board.A1)

def obtener_voltaje(pin):
    return (pin.value * 3.3) / 65535  # ADC 12-bits [0 - 3.3]

# Stepper motor setup
DELAY = 0.01  # el más rápido es 0.004, 0.01 sigue siendo muy suave, se vuelve paso a paso después de eso
STEPS = 64  # con 513 pasos da una vuelta completa

coils = (
    DigitalInOut(board.GP21),  # A1
    DigitalInOut(board.GP20),  # A2
    DigitalInOut(board.GP19),  # B1
    DigitalInOut(board.GP18),  # B2
)

for coil in coils:
    coil.direction = Direction.OUTPUT

stepper_motor = stepper.StepperMotor(
    coils[0], coils[1], coils[2], coils[3], microsteps=None
)


def stepper_fwd():
    print("Giro horario")
    for _ in range(STEPS):
        stepper_motor.onestep(direction=stepper.FORWARD)
        time.sleep(DELAY)
    stepper_state = stepper.FORWARD
    stepper_motor.release()


def stepper_back():
    print("Giro antihorario")
    for _ in range(STEPS):
        stepper_motor.onestep(direction=stepper.BACKWARD)
        time.sleep(DELAY)
    stepper_state = stepper.BACKWARD
    stepper_motor.release()

print("====================")
print("==Iniciando Prueba==")
print("====================")

while True:
    ledBlanco.value = False
    y = obtener_voltaje(eje_y)
    #-----------------UART----------------
    s = bytearray(str(y))
    uart.write(s)
    """data = uart.read(32)
    data_string = ''.join([chr(b) for b in data])
    print(data_string, end="")
    """
    s = bytearray(str(stepper_state))
    uart.write(s)
    """data = uart.read(32)
    data_string = ''.join([chr(b) for b in data])
    print(data_string, end="")
    """
    s = bytearray(str(ledBlanco.value))
    uart.write(s)
    """data = uart.read(32)
    data_string = ''.join([chr(b) for b in data])
    print(data_string, end="")
    """
    s = bytearray(str(interruptor.value))
    uart.write(s)
    """data = uart.read(32)
    data_string = ''.join([chr(b) for b in data])
    print(data_string, end="")
    """
    #-----------------UART----------------
    stepper_state = 0
    if y < 0.3:
        stepper_back()
        print("Dirección: Abajo")

    if not interruptor.value:
        if y > 3.0:
            stepper_fwd()
            print("Dirección: Arriba")
    else:
        parpadeo(0.5)
        print("Detención por fin de rango de movimiento")

    #---------------------I2C----------------------
        
    json_data =  {
        "controller_name": "Raspberry Pi Pico",
        "date": adafruit_datetime.datetime.now(),
        "acutators": [
            {
                "type": "steper",
                "current_value": stepper_state
            },
            {
                "type": "led",
                "current_value": ledBlanco.value
            },
        ],
        "sensors": [
            {
                "type": "fotosensor",
                "current_value": interruptor.value
            },
            {
                "type": "Joystick",
                "current_value": y   
            }
        ]
    }

    datos_serializados = json.dumps(json_data)

    with slave_bus.wait(0x11, 0x33, timeout=None) as i2c_request:
        if i2c_request.is_write:
            slave_bus.write(datos_serializados)
        else:
           register = slave_bus.read(1)[0]

    #---------------------I2C----------------------
