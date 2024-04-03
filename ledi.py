import board
import digitalio
import time

led = digitalio.DigitalInOut(board.GPIO_P37)  # pin 37
led.direction = digitalio.Direction.OUTPUT

try:
  while True:
    led.value = True
    time.sleep(5)
    led.value = False
    time.sleep(5)
finally:
  led.value = False
  led.close()

  