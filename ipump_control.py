#!/usr/bin/env python3

from ipump.ipump import IPump
from influxdb_cli2.influxdb_cli2 import influxdb_cli2
import paho.mqtt.client as paho

import time
import datetime
import sys

class ipump_controller:
    def __init__(self, ipump_ipaddr):
        self.ipump = IPump(ipaddr=ipump_ipaddr)

        self.mqtt = None
        self.influxdb = None
        self.influxdb_price_location = None
        self.incluxdb_price_measurement = None

        self.betriebsart = -1
        self.preis_lim_heiz = 0.00
        self.preis_lim_wasser = 0.00

    def config_influxdb(self, influxdb_url, influxdb_token, influxdb_org, influxdb_bucket):
        self.influxdb = influxdb_cli2(influxdb_url, influxdb_token, influxdb_org, influxdb_bucket)

    def config_influxdb_pricedb(self, location, measurement):
        self.influxdb_price_location = location
        self.influxdb_price_measurement = measurement
        
    def get_latest_price(self):
        if self.influxdb and self.influxdb_price_location and self.influxdb_price_measurement:
            results = self.influxdb.query_data(self.influxdb_price_location, self.influxdb_price_measurement, datetime.datetime.utcnow()+datetime.timedelta(hours=-1), datetime.datetime.utcnow())
            if results:
                return results[0][3]
            else:
                return None
        else:
            return None

    def config_mqtt(self, mqtt_ip, mqtt_port, mqtt_topic):
        self.mqtt_topic = mqtt_topic
        
        self.mqtt= paho.Client()

        self.mqtt.on_publish = self.mqtt_on_publish
        self.mqtt.on_connect = self.mqtt_on_connect
        self.mqtt.on_message = self.mqtt_on_message

        self.mqtt.connect(mqtt_ip, mqtt_port)
        self.mqtt.loop_start()
        
    def mqtt_on_publish(self, client,userdata,result):
        # print("on_publish - result {0}".format(result))
        pass
        
    def mqtt_on_connect(self, client, userdata, flags, rc):
        # print("Connection returned result: " + str(rc))
        client.subscribe(self.mqtt_topic + "/betriebsart_set", 1)
        client.subscribe(self.mqtt_topic + "/preis_lim_heiz_set", 1)
        client.subscribe(self.mqtt_topic + "/preis_lim_wasser_set", 1)

    # The callback for when a PUBLISH message is received from the server.
    def mqtt_on_message(self, client, userdata, msg):
        print(msg.topic+": {0}".format(float(msg.payload)) )
        if msg.topic == self.mqtt_topic + "/betriebsart_set":
            if int(msg.payload) >= -1 and int(msg.payload) <= 11:
                print("set Betriebsart because of MQTT msg")
                self.betriebsart = int(msg.payload)
        if msg.topic == self.mqtt_topic + "/preis_lim_heiz_set":
            if float(msg.payload) >= 0 and float(msg.payload) <= 1.0:
                print("set preis_lim_heiz because of MQTT msg")
                self.preis_lim_heiz = float(msg.payload)
        if msg.topic == self.mqtt_topic + "/preis_lim_wasser_set":
            if float(msg.payload) >= 0 and float(msg.payload) <= 1.0:
                print("set preis_lim_wasser because of MQTT msg")
                self.preis_lim_wasser = float(msg.payload)

    def run_1control_loop(self):
        print("--------------------")
        cur_price = self.get_latest_price()
        print("Current price: {0}".format(cur_price))
        print("Betriebsart: {0}".format(self.betriebsart))
        print("Preis_lim_Wasser: {0}".format(self.preis_lim_wasser))
        print("Preis_lim_Heiz: {0}".format(self.preis_lim_heiz))

        # Manual control, set mode(betriebsart) directly:
        # 0 - Standby
        # 1 - Automatic (All on)
        # 2 - Holiday
        # 4 - Only Water
        # 5 - Only Heating
        if self.betriebsart >= 0 and self.betriebsart <= 5:
            # TODO: Rewrite mode only when changed (also below)
            self.ipump.write_data("Betriebsart System", betriebsart)
            
        # Price-depdendent operation
        # 10 - IPump + Lüftung (TODO: Split out Lüftung)
        # 11 - only IPump, ignore Lüftung
        if self.betriebsart == 10 or self.betriebsart == 11:
            if cur_price == None:
                print("No price information available, all off")
                self.ipump.write_data("Betriebsart System", 0)
                if self.betriebsart == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 0)
            elif cur_price <= preis_lim_heiz and cur_price >= self.preis_lim_wasser:
                print("Heizung an")
                self.ipump.write_data("Betriebsart System", 5)
                if self.betriebsart == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 1)
            elif cur_price >= self.preis_lim_heiz and cur_price <= self.preis_lim_wasser:
                print("Wasser an")
                self.ipump.write_data("Betriebsart System", 4)
                if self.betriebsart == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 1)
            elif cur_price <= self.preis_lim_heiz and cur_price <= self.preis_lim_wasser:
                print("Alles an")
                self.ipump.write_data("Betriebsart System", 1)
                if self.betriebsart == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 1)
            else:
                print("Alles aus")
                self.ipump.write_data("Betriebsart System", 0)
                if self.betriebsart == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 0)
        
        # Dump status to MQTT (which will be also recorded into influxdb by a different entity)
        self.mqtt.publish(self.mqtt_topic + "/betriesbart_sys_m", int(self.ipump.read_data("Betriebsart System")))
        self.mqtt.publish(self.mqtt_topic + "/betriesbart_sys_s", int(self.betriebsart))
        self.mqtt.publish(self.mqtt_topic + "/preis_lim_heiz", float(self.preis_lim_heiz))
        self.mqtt.publish(self.mqtt_topic + "/preis_lim_wasser", float(self.preis_lim_wasser))
 

if __name__ == "__main__":
    from config_data import *

    ipump_control = ipump_controller(ipump_ip)

    ipump_control.config_influxdb(influxdb_url, influxdb_token, influxdb_org, influxdb_bucket)
    ipump_control.config_influxdb_pricedb(influxdb_price_location, influxdb_price_measurement)
    ipump_control.config_mqtt(mqtt_ip, mqtt_port, mqtt_topic)
    
    while True:
        ipump_control.run_1control_loop()
        
        print("before sleep")
        time.sleep(120)
        print("after sleep")

        

