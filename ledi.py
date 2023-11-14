import board
import digitalio

led = digitalio.DigitalInOut(board.GPIO_P37)  # pin 37
led.direction = digitalio.Direction.OUTPUT

button = digitalio.DigitalInOut(board.GPIO_P36)  # pin 36
button.direction = digitalio.Direction.INPUT

try:
  while True:
    led.value = True
    microcontroller.delay_us(500)
    led.value = True
finally:
  led.value = False
  led.deinit()
  button.deinit()