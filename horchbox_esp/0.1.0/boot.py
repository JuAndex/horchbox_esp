from machine import SoftI2C, Pin
from time import sleep
from network import WLAN, STA_IF
import ubinascii
from lib.ds3231 import DS3231, EVERY_MINUTE
from MQTT_Manager import init_mqtt
import json
from lib.micropython_ota import check_for_ota_update

turn_on_pin = Pin(5, Pin.OUT, value=0)
turn_off_pin = Pin(32, Pin.OUT, value=0)


def get_time():
    (year, month, day, hour, minute, second, weekday, yearday) = rtc.get_time()
    date_str = "{:02d}.{:02d}.{:04d} {:02d}:{:02d}:{:02d}".format(
        day, month, year, hour, minute, second
    )

    return date_str


def read_config():
    f = open("config.json", "r")
    config = json.loads(f.read())
    f.close()

    global start, end, interval, duration
    start = config["start"]
    end = config["end"]
    interval = config["interval"]
    duration = config["duration"]

    obj = {
        "start": start,
        "end": end,
        "interval": interval,
        "duration": duration,
    }

    print(json.dumps(obj))


# region WIFI-Config
WIFI_SSID = "Sonos_IT"
WIFI_PW = "IT_Sonos"

print("Starting")
wifi = WLAN(STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PW)
WIFI_MAC = ubinascii.hexlify(wifi.config("mac")).decode().upper()
while not wifi.isconnected():
    pass
# endregion

# region RTC-Config
Pin(15, Pin.OUT, value=1)
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
rtc = DS3231(i2c)
rtc.alarm1.set(EVERY_MINUTE, sec=0)
rtc.alarm1.clear()
# endregion

init_mqtt(WIFI_MAC)

# region time settings
start = 0
end = 1440
interval = 2
duration = 1
# endregion

# region Over-the-Air Config
ota_host = "http://192.168.2.100"
project_name = "horchbox_esp"
filenames = ["boot.py", "main.py", "MQTT_Manager.py"]
# endregion

# Loop-Function
while True:
    if rtc.alarm1():
        rtc.alarm1.clear()

        check_for_ota_update(ota_host, project_name, soft_reset_device=False, timeout=5)

        (year, month, day, hour, minute, second, weekday, yearday) = rtc.get_time()
        totalMinutes = hour * 60 + minute

        read_config()

        if totalMinutes % interval == 0:
            if totalMinutes > start and totalMinutes < end:
                # Turn on raspberry
                print(f"{get_time()}: Turning on for {duration} seconds")
                turn_on_pin.value(1)

                # Wait uptime of raspberry
                sleep(duration)
                print(f"{get_time()}: Turning off")
                turn_off_pin.value(1)

                # Wait till Raspberry is shutdown
                sleep(5)
                print(f"{get_time()}: Shutdown complete")
                turn_on_pin.value(0)
                turn_off_pin.value(0)

    sleep(1)
