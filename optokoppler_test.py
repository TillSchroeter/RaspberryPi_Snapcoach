import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT)

# 24 ist rechts (orange)
# 23 ist links (blaue)

print("Test gestartet. Drücke Strg+C zum Beenden.")

# try:
#     while True:
#         print("GPIO 23 ist HIGH -> Optokoppler SCHLIESST")
#         GPIO.output(23, GPIO.HIGH)
#         time.sleep(1)

#         print("GPIO 23 ist LOW  -> Optokoppler TRENNT")
#         GPIO.output(23, GPIO.LOW)
#         time.sleep(5)

# except KeyboardInterrupt:
#     GPIO.cleanup()
#     print("\nGPIOs aufgeräumt.")

GPIO.setmode(GPIO.BCM)
GPIO.setup(24, GPIO.OUT)
try:
    while True:
        print("GPIO 24 ist HIGH -> Optokoppler SCHLIESST")
        GPIO.output(24, GPIO.HIGH)
        time.sleep(1)

        print("GPIO 24 ist LOW  -> Optokoppler TRENNT")
        GPIO.output(24, GPIO.LOW)
        time.sleep(5)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nGPIOs aufgeräumt.")