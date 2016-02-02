#!/usr/bin/python3

import sys
import ssl
import json
import time
from sense_hat import SenseHat
import paho.mqtt.client as mqtt

#####
# This script sends measurements every 2 seconds from the Raspberry PIs sens hat via the MQTT Protocol to AWS IoT and
# further to AWS Lambda.
#
# Author: Arik Guggenheim (arik.guggenheim@arik.sydney)
# Date: 26.01.2016
#####

class Sens_data():
    def __init__(self):
        self.sense = SenseHat()

    def get_temperature(self):
        return "%.2f" % self.sense.get_temperature()

    def get_humidity(self):
        return "%.2f" % self.sense.get_humidity()

    def get_pressure(self):
        return "%.2f" % self.sense.get_pressure()

    def get_timestamp(self):
        return str(int(time.time()))

def init_sens():
    return Sens_data()

#called while client tries to establish connection with the server
def on_connect(mqttc, obj, flags, rc):
    if rc==1:
        print ("Subscriber Connection status code: "+str(rc)+" | Connection status: Connection refused")

#called when a topic is successfully subscribed to
def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos)+"data"+str(obj))

#called when a message is received by a topic
def on_message(mqttc, obj, msg):
    print("Received message from topic: "+msg.topic+" | QoS: "+str(msg.qos)+" | Data Received: "+str(msg.payload))

#creating a client with client-id=mqtt-test
mqttc = mqtt.Client(client_id="mqtt-test")

mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_message = on_message

#Configure network encryption and authentication options. Enables SSL/TLS support.
#adding client-side certificates and enabling tlsv1.2 support as required by aws-iot service
mqttc.tls_set("/home/pi/deviceSDK/certs/rootCA.crt",
	            certfile="/home/pi/cert.pem",
	            keyfile="/home/pi/privateKey.pem",
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None)

#connecting to aws-account-specific-iot-endpoint
mqttc.connect("AWS IoT endpoint", port=8883) #AWS IoT service hostname and portno
mqttc.loop_start()

sens = init_sens()

while True:
    jsonstr = '{{"site": "RPI", "timestamp":{ts}, "temp":{t}, "rH":{h}, "press":{p}}}'.format(t=sens.get_temperature(),
                                                                                              h=sens.get_humidity(),
                                                                                              p=sens.get_pressure(),
                                                                                              ts=sens.get_timestamp())
    mqttc.publish("sensorpi/meteo", json.dumps(json.loads(jsonstr)), qos = 1)
    time.sleep(2)

