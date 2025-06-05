from time import time_ns, sleep
from lib.umqtt import MQTTClient
import json
import _thread

def print_mqtt(topic, message):
    topic = topic.decode("utf-8")
    message = message.decode("utf-8")
    print(f"{topic}: {message}")
    try:
        f = open("config.json", "r")
        config = json.loads(f.read())
        f.close()
        
        jsonData = json.loads(message)
        key = jsonData["key"]
        value = jsonData["value"]
        
        if not key in list(config.keys()):
            raise Exception("Variable nicht konfigurierbar")
        config[key] = value
        
        f = open("config.json", "w")
        f.write(json.dumps(config))
        f.close()
        
        mqtt_client.publish(f"{topic}/current", json.dumps(config))
    except Exception as e:
        msg = repr(e)
        mqtt_client.publish(f"{topic}/error", msg)


# region MQTT-Config
MQTT_SERVER = "broker.emqx.io"
MQTT_CLIENTID = f"raspberry-sub-{time_ns()}"
mqtt_client = MQTTClient(MQTT_CLIENTID, MQTT_SERVER, 1883)
mqtt_client.set_callback(print_mqtt)
# endregion


def _init_mqtt(WIFI_MAC: str):
    MQTT_TOPIC = f"/LBV/Horchboxen/test/Biotop/{WIFI_MAC}"
    mqtt_client.connect()
    mqtt_client.subscribe(MQTT_TOPIC)
    print(f"MQTT: Connected and subscribed to {MQTT_TOPIC}")
    
    while True:
        try:
            mqtt_client.check_msg()
            sleep(1)
        except:
            mqtt_client.connect()
        
    
def init_mqtt(WIFI_MAC: str):
    _thread.start_new_thread(lambda: _init_mqtt(WIFI_MAC), ())