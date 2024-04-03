#Lyhyt esimerkki gpio pinnien kaytosta.
#Alustetaan 2kpl ledeja ja yks painike.
#Ledit kytketaan gnd pinniin ja + jalka 220ohm vastuksen kautta output pinniin.
#Painike 3.3v lahdosta input pinniin ja 4,7kohm pull down vastus input - gnd valiin. 

from periphery import GPIO
import time

led = GPIO("/dev/gpiochip2", 13, "out")  # pin 37 Led
led2 = GPIO("/dev/gpiochip4", 13, "out") # pin 36 Led
button = GPIO("/dev/gpiochip0", 8, "in") # pin 31 Button

i=0

print("start")
while i<=30:
    i= i+1
    print("in while loop, round:",i)
    if button.read()==True:
        print("in if loop")
        led.write(True)
        time.sleep(1)
        led2.write(True)
        time.sleep(1)
        led.write(False)
        time.sleep(1)
        led2.write(False)
        time.sleep(1)
    time.sleep(1)

print("Shutting down")
led.write(False)
led2.write(False)
led.close()
led2.close()
button.close()

# from periphery import GPIO
# led = GPIO("/dev/gpiochip2", 13, "out")  # pin 37 Led
# led2 = GPIO("/dev/gpiochip4", 13, "out")
# led.write(True)
