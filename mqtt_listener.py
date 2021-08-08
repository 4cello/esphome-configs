from paho.mqtt import client as mqtt_client
import random
import datetime

broker = "192.168.144.2"
port = 1883
username = "mqtt"
password = "jY2gnm5G"

client_id = f'python-mqtt-{random.randint(0, 1000)}'
topic = "esphome/hydroponics/debug"

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"[{datetime.datetime.now()}]" + msg.payload.decode())
    client.subscribe(topic)
    client.on_message = on_message


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
        else:
            print(f"Failed to connect, return code {rc}")
    
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

if __name__ == "__main__":
    run()