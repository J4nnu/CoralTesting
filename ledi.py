import board
import digitalio
import time

led = digitalio.DigitalInOut(board.GPIO_P37)  # pin 37
led.direction = digitalio.Direction.OUTPUT



try:
  while True:
    led.value = True
    
    time.sleep(2)
    led.value = True
finally:
  led.value = False
  led.deinit()
  