#!/usr/bin/env python3

from ipump.ipump import IPump
from influxdb_cli2.influxdb_cli2 import influxdb_cli2
import paho.mqtt.client as paho

import time
import datetime
import sys
import math


class Room():
    def __init__(self, name, cur_temp, tgt_temp, hum, db_name=None):
        self.name = name
        self.cur_temp = cur_temp
        self.tgt_temp = tgt_temp
        self.hum = hum
        self.db_name = db_name

class ipump_controller:
    def __init__(self, ipump_ipaddr):
        self.ipump = IPump(ipaddr=ipump_ipaddr)

        self.mqtt = None
        self.influxdb = None
        self.influxdb_price_location = None
        self.incluxdb_price_measurement = None

        self.ipump_betriebsart = -1  # ipump_betriebsart = operational mode of IPump
        self.something_changed = False
        self.control_state = -1      # state of the statemachine  
        self.preis_lim_heiz = 0.00
        self.preis_lim_wasser = 0.00

    def config_influxdb(self, influxdb_url, influxdb_token, influxdb_org, influxdb_bucket):
        self.influxdb = influxdb_cli2(influxdb_url, influxdb_token, influxdb_org, influxdb_bucket, debug=False)

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
        client.subscribe(self.mqtt_topic + "/control_state_set", 1)
        client.subscribe(self.mqtt_topic + "/preis_lim_heiz_set", 1)
        client.subscribe(self.mqtt_topic + "/preis_lim_wasser_set", 1)

    # The callback for when a PUBLISH message is received from the server.
    def mqtt_on_message(self, client, userdata, msg):
        print(msg.topic+": {0}".format(float(msg.payload)) )
        if msg.topic == self.mqtt_topic + "/control_state_set":
            if int(msg.payload) >= -1 and int(msg.payload) <= 12:
                print("set Betriebsart because of MQTT msg")
                self.control_state = int(msg.payload)
                self.something_changed = True
        if msg.topic == self.mqtt_topic + "/preis_lim_heiz_set":
            if float(msg.payload) >= 0 and float(msg.payload) <= 1.0:
                print("set preis_lim_heiz because of MQTT msg")
                self.preis_lim_heiz = float(msg.payload)
                self.something_changed = True
        if msg.topic == self.mqtt_topic + "/preis_lim_wasser_set":
            if float(msg.payload) >= 0 and float(msg.payload) <= 1.0:
                print("set preis_lim_wasser because of MQTT msg")
                self.preis_lim_wasser = float(msg.payload)
                self.something_changed = True

    def run_1control_loop(self):
        print("--------------------")
        cur_price = self.get_latest_price()
        print("Current price: {0}".format(cur_price))
        print("Betriebsart (should): {0}".format(self.ipump_betriebsart))
        print("Betriebsart (is): {0}".format(int(self.ipump.read_data("Betriebsart System"))))
        print("Control state: {0}".format(self.control_state))
        print("Preis_lim_Wasser: {0}".format(self.preis_lim_wasser))
        print("Preis_lim_Heiz: {0}".format(self.preis_lim_heiz))

        # Control state inputs:
        # -1 - Do nothing, keep passive

        # Manual control, set mode(ipump_betriebsart) directly:
        # 0 - Standby
        # 1 - Automatic (All on)
        # 2 - Holiday
        # 4 - Only Water
        # 5 - Only Heating
        
        # Price-depdendent operation:
        # 10 - IPump + Lüftung (TODO: Split out Lüftung)
        # 11 - only IPump, ignore Lüftung
        
        # 12 - Stop Ipump as soon battery is empty
        
        
        # First check if IPump is still in the state it should be. 
        # If not, likely somebody changed mode on the display of the ipump, go do state -1
        if int(self.ipump.read_data("Betriebsart System")) != self.ipump_betriebsart:
            print("Found Ipump in unexected state, go to do-nothing-mode")
            self.ipump_betriebsart = int(self.ipump.read_data("Betriebsart System"))
            self.control_state = -1 

        if self.control_state >= 0 and self.control_state <= 5:
            # TODO: Rewrite mode only when changed (also below)
            print("Set static to {0}".format(self.control_state))
            self.ipump_betriebsart = self.control_state
            self.ipump.write_data("Betriebsart System", self.ipump_betriebsart)
            
        elif self.control_state == 10 or self.control_state == 11:
            if cur_price == None:
                print("No price information available, all off")
                self.ipump_betriebsart = 0
                self.ipump.write_data("Betriebsart System", self.ipump_betriebsart)
                if self.control_state == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 0)
            elif cur_price <= self.preis_lim_heiz and cur_price >= self.preis_lim_wasser:
                print("Heizung an")
                self.ipump_betriebsart = 5
                self.ipump.write_data("Betriebsart System", self.ipump_betriebsart)
                if self.control_state == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 1)
            elif cur_price >= self.preis_lim_heiz and cur_price <= self.preis_lim_wasser:
                print("Wasser an")
                self.ipump_betriebsart = 4
                self.ipump.write_data("Betriebsart System", self.ipump_betriebsart)
                if self.control_state == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 1)
            elif cur_price <= self.preis_lim_heiz and cur_price <= self.preis_lim_wasser:
                print("Alles an")
                self.ipump_betriebsart = 1
                self.ipump.write_data("Betriebsart System", self.ipump_betriebsart)
                if self.control_state == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 1)
            else:
                print("Alles aus")
                self.ipump_betriebsart = 0
                self.ipump.write_data("Betriebsart System", self.ipump_betriebsart)
                if self.control_state == 10:
                    self.mqtt.publish(self.mqtt_topic + "/luftstufe_set", 0)

        elif self.control_state == 12:
            if int(self.ipump.read_data("Füllstand Batterie")) <= 16:
                print("Batterie leer, Alles aus, {0}%".format(int(self.ipump.read_data("Füllstand Batterie"))))
                self.ipump_betriebsart = 0
                self.ipump.write_data("Betriebsart System", self.ipump_betriebsart)
            elif int(self.ipump.read_data("Füllstand Batterie")) >= 26:
                print("Batterie ok, Alles an, {0}%".format(int(self.ipump.read_data("Füllstand Batterie"))))
                self.ipump_betriebsart = 1
                self.ipump.write_data("Betriebsart System", self.ipump_betriebsart)
            else:
                print("Batterie ok, Nix aendern, {0}%".format(int(self.ipump.read_data("Füllstand Batterie"))))

        
        # Dump status to MQTT for direct display (but will be also recorded into influxdb by a different entity)
        self.mqtt.publish(self.mqtt_topic + "/betriesart_sys", int(self.ipump.read_data("Betriebsart System")))
        self.mqtt.publish(self.mqtt_topic + "/control_state", int(self.control_state))
        self.mqtt.publish(self.mqtt_topic + "/preis_lim_heiz", float(self.preis_lim_heiz))
        self.mqtt.publish(self.mqtt_topic + "/preis_lim_wasser", float(self.preis_lim_wasser))
 
    def dump_db_ipump_status(self):
        # TODO: Database names hardcoded.
        self.influxdb.write_sensordata("weather", "temperature_heizsensor",
                                       self.ipump.read_data("Aussentemperatur B32"))
        self.influxdb.write_sensordata("weather", "temperature_heizunit",
                                       self.ipump.read_data("Luftansaugtemperatur B37"))
        self.influxdb.write_sensordata("strom", "heizung_cur_power",
                                       self.ipump.read_data("Aktuelle Leistungsaufnahme Wärmepumpe")*1000)
        self.influxdb.write_sensordata("heizung", "waermepumpe_vorlauf",
                                       self.ipump.read_data("Wärmepumpen Vorlauftemperatur B33"))
        self.influxdb.write_sensordata("heizung", "waermepumpe_ruecklauf",
                                       self.ipump.read_data("Wärmepumpen Rücklauftemperatur B34"))
        self.influxdb.write_sensordata("heizung", "wasserspeicher_oben",
                                       self.ipump.read_data("Trinkwasserspeicher oben B48"))
        self.influxdb.write_sensordata("heizung", "wasserspeicher_unten",
                                       self.ipump.read_data("Trinkwasserspeicher unten B41"))
        self.influxdb.write_sensordata("heizung", "betriebsmodus",
                                       self.ipump.read_data("Betriebsart Wärmepumpe"))
        self.influxdb.write_sensordata("heizung", "betriebsart_sys_i",
                                       self.ipump.read_data("Betriebsart System"))
        self.influxdb.write_sensordata("heizung", "heizung_cur_heat",
                                       self.ipump.read_data("Wärmemenge Momentanleistung")*1000)

        if self.ipump.read_data("Aktuelle Leistungsaufnahme Wärmepumpe") > 0:
            efficency = self.ipump.read_data("Wärmemenge Momentanleistung") / self.ipump.read_data("Aktuelle Leistungsaufnahme Wärmepumpe")
            if efficency != 0 and efficency < 10.0:
                self.influxdb.write_sensordata("heizung", "heizung_efficency",abs(efficency))
        # else:
        #     self.influxdb.write_sensordata("heizung", "heizung_efficency",0.0)

    # from https://gist.github.com/sourceperl/45587ea99ff123745428
    def get_dew_point_c(self, t_air_c, rel_humidity):
        """Compute the dew point in degrees Celsius
        :param t_air_c: current ambient temperature in degrees Celsius
        :type t_air_c: float
        :param rel_humidity: relative humidity in %
        :type rel_humidity: float
        :return: the dew point in degrees Celsius
        :rtype: float
        """
        if (t_air_c == 0) or (rel_humidity == 0):
            return None
        A = 17.27
        B = 237.7
        alpha = ((A * t_air_c) / (B + t_air_c)) + math.log(rel_humidity/100.0)
        return (B * alpha) / (A - alpha)    

    def build_room_list(self, room_config):
        rooms = []
        for entry in room_config:
            rooms.append(Room(entry[0], 
                        "Zonemodul {0} Raum {1} akt Temperatur".format(entry[1], entry[2]), 
                        "Zonemodul {0} Raum {1} Solltemperatur".format(entry[1], entry[2]), 
                        "Zonemodul {0} Raum {1} Feuchte".format(entry[1], entry[2]),
                        entry[0]
                        ) )
        return(rooms)

    def dump_db_room_status(self, roomlist):
        for room in roomlist:
            self.influxdb.write_sensordata(room.db_name, "temp", self.ipump.read_data(room.cur_temp))
            self.influxdb.write_sensordata(room.db_name, "tgt_temp", self.ipump.read_data(room.tgt_temp))
            self.influxdb.write_sensordata(room.db_name, "humidity", self.ipump.read_data(room.hum))
            self.influxdb.write_sensordata(room.db_name, "dewpoint",
                                           self.get_dew_point_c(self.ipump.read_data(room.cur_temp),
                                                           self.ipump.read_data(room.hum)))

if __name__ == "__main__":
    from config_data import *

    ipump_control = ipump_controller(ipump_ip)

    ipump_control.config_influxdb(influxdb_url, influxdb_token, influxdb_org, influxdb_bucket)
    ipump_control.config_influxdb_pricedb(influxdb_price_location, influxdb_price_measurement)
    ipump_control.config_mqtt(mqtt_ip, mqtt_port, mqtt_topic)
    
    rooms = ipump_control.build_room_list(room_config)
    
    while True:
        ipump_control.run_1control_loop()

        ipump_control.dump_db_ipump_status()
        ipump_control.dump_db_room_status(rooms)
        
        print("before sleep")
        for i in range(int(120/6)):
            time.sleep(6)
            if ipump_control.something_changed:
                ipump_control.something_changed = False
                break
        print("after sleep")

        

