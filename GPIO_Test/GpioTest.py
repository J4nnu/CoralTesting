from periphery import GPIO
import time

led = GPIO("/dev/gpiochip2", 13, "out")  # pin 37 Led
led2 = GPIO("/dev/gpiochip4", 13, "out")
i=0
while i<10:
    led.write(True)
    time.sleep(2)
    led2.write(True)
    time.sleep(2)
    led.write(False)
    time.sleep(2)
    led2.write(False)
    time.sleep(2)


# from periphery import GPIO
# led = GPIO("/dev/gpiochip2", 13, "out")  # pin 37 Led
# led2 = GPIO("/dev/gpiochip4", 13, "out")
# led.write(True)
