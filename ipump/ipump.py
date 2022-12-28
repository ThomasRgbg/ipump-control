#!/usr/bin/env python3

import time
import argparse

from pyModbusTCP.client import ModbusClient
from pyModbusTCP import utils


class IPump:
    def __init__(self, ipaddr, debug=False):
        self.debug = debug
        self.ipaddr = ipaddr
        self.modbus = ModbusClient(host=ipaddr, port=502, auto_open=True, auto_close=True)
        if self.debug:
            self.modbus.debug = True

        self.registers = {
            "Aussentemperatur B32" : [1000, "float"],
            "Mittl Aussentemperatur / 24h" : [1002, "float"],
            "Akt Störungsnummer" : [1004, "uchar"],
            "Betriebsart System" : [1005, "uint16"],
            "Wärmespeichertemperatur B38" : [1008, "float"],
            # "Kältespeichertemperatur" : [1010, "float"],
            "Trinkwasserspeicher unten B41" : [1012, "float"],
            "Trinkwasserspeicher oben B48" : [1014, "float"],
            #"Warmwasserzapftemperatur" : [1030, "float"],
            "Warmwasser Solltemperatur FW030" : [1032, "uchar"],
            "Warmwasserladung Einschalttemperatur FW027" : [1033, "uchar"],
            "Warmwasserladung Ausschalttemperatur FW028" : [1034, "uchar"],
            #"Aktueller Strompreis" : [1048, "float"],
            "Wärmepumpen Vorlauftemperatur B33" : [1050, "float"],
            "Wärmepumpen Rücklauftemperatur B34" : [1052, "float"],
            #"HGL Vorlauftemperatur" : [1054, "float"],
            #"Wärmequelleneintrittstemperatur" : [1056, "float"],
            #"Wärmequellenaustrittstemperatur" : [1058, "float"],
            "Luftansaugtemperatur B37" : [1060, "float"],
            #"Luftwärmetauschertemperatur" : [1062, "float"],
            #"Luftansaugtemperatur 2" : [1064, "float"],
            "Betriebsart Wärmepumpe" : [1090, "uchar"],
            "Status Verdichter 1" : [1100, "uchar"],
            #"Status Verdichter 2" : [1101, "uchar"],
            #"Status Verdichter 3" : [1102, "uchar"],
            #"Status Verdichter 4" : [1103, "uchar"],
            "Status Ladepumpe M73" : [1104, "word"],
            "Status Zwischenkreispumpe M16" : [1105, "word"],
            "Status Wärmequellen/Grundwasserpumpe M15" : [1106, "word"],
            "Status ISC Kältespeicherpumpe M84" : [1108, "word"],
            "Status ISC Rückkühlpumpe M17" : [1109, "word"],
            "Umschaltventil Heizkreis Heizen/Kühlen M61" : [1110, "word"],
            # "Umschaltventil Speicher Heizen/Kühlen M62" : [1111, "word"],
            "Umschaltventil Heizen/Warmwasser M63" : [1112, "word"],
            #"Umschaltventil Heizen/Kühlen M74" : [1113, "word"],
            "Anzahl laufende Verdichterstufen Heizen" : [1150, "uchar"],
            "Anzahl laufende Verdichterstufen Kühlen" : [1151, "uchar"],
            "Anzahl laufende Verdichterstufen Warmwasser" : [1152, "uchar"],
            #"Heizkreis A Vorlauftemperatur B51" : [1350, "float"],
            #"Heizkreis A Raumtemperatur B61" : [1364, "float"],
            "Heizkreis A Sollvorlauftemperatur" : [1378, "float"],
            "Betriebsart Heizkreis A" : [1393, "uchar"],
            "Raumsolltemperatur Heizen Normal HK A" : [1401, "float"],
            "Raumsolltemperatur Heizen Eco HK A" : [1415, "float"],
            "Heizkurve HK A" : [1429, "float"],
            "Heizgrenze HK A" : [1442, "uchar"],
            "Raumsolltemperatur Kühlen HK A" : [1449, "uchar"],
            "Raumsolltemperatur ECO HK A" : [1471, "uchar"],
            "Kühlgrenze HK A" : [1484, "uchar"],
            "Sollvorlauftemperatur Kühlen HK A" : [1491, "uchar"],
            "Aktive Betriebsart HK A" : [1498, "uchar"],
            "Parallelverschiebung HK A" : [1505, "uchar"],
            "Externe Raumtemperatur HK A" : [1650, "float"],
            "Externe Aussentemperatur" : [1690, "float"],
            "Externe Feuchte" : [1692, "float"],
            "Externe Anforderungstemperatur Heizen" : [1694, "uchar"],
            "Externe Anforderungstemperatur Kühlen" : [1695, "uchar"],
            "Anforderung Heizen" : [1710, "uchar"],
            "Anforderung Kühlen" : [1711, "uchar"],
            "Anforderung Warmwasserladung" : [1712, "uchar"],
           
            "Wärmemenge Heizen" : [1750, "float"],
            "Wärmemenge Kühlen" : [1752, "float"],
            "Wärmemenge Warmwasser" : [1754, "float"],
            "Wärmemenge Abtauung" : [1756, "float"],
            #"Wärmemenge Passive Kühlung" : [1758, "float"],
            "Wärmemenge Elektroheizsatz" : [1762, "float"],
            "Wärmemenge Momentanleistung" : [1790, "float"],

            "Zonemodul 1 Modus Heizen/Kühlen A14" : [2000, "uchar"],
            "Zonemodul 1 Entfeuchtungsausgang A12" : [2001, "uchar"],

            "Zonemodul 1 Raum 1 akt Temperatur" : [2002, "float"],
            "Zonemodul 1 Raum 1 Solltemperatur" : [2004, "float"],
            "Zonemodul 1 Raum 1 Feuchte" : [2006, "uchar"],
            "Zonemodul 1 Raum 1 Betriebsart" : [2007, "uchar"],
            "Zonemodul 1 Raum 1 Status A1" : [2008, "uchar"],

            "Zonemodul 1 Raum 2 akt Temperatur" : [2009, "float"],
            "Zonemodul 1 Raum 2 Solltemperatur" : [2011, "float"],
            "Zonemodul 1 Raum 2 Feuchte" : [2013, "uchar"],
            "Zonemodul 1 Raum 2 Betriebsart" : [2014, "uchar"],
            "Zonemodul 1 Raum 2 Status A2" : [2015, "uchar"],

            "Zonemodul 2 Raum 1 akt Temperatur" : [2067, "float"],
            "Zonemodul 2 Raum 1 Solltemperatur" : [2069, "float"],
            "Zonemodul 2 Raum 1 Feuchte" : [2071, "uchar"],
            "Zonemodul 2 Raum 1 Betriebsart" : [2072, "uchar"],
            "Zonemodul 2 Raum 1 Status A1" : [2073, "uchar"],
            
            "Zonemodul 2 Raum 2 akt Temperatur" : [2074, "float"],
            "Zonemodul 2 Raum 2 Solltemperatur" : [2076, "float"],
            "Zonemodul 2 Raum 2 Feuchte" : [2078, "uchar"],
            "Zonemodul 2 Raum 2 Betriebsart" : [2079, "uchar"],
            "Zonemodul 2 Raum 2 Status A2" : [2080, "uchar"],

            "Zonemodul 2 Raum 3 akt Temperatur" : [2081, "float"],
            "Zonemodul 2 Raum 3 Solltemperatur" : [2083, "float"],
            "Zonemodul 2 Raum 3 Feuchte" : [2085, "uchar"],
            "Zonemodul 2 Raum 3 Betriebsart" : [2086, "uchar"],
            "Zonemodul 2 Raum 3 Status A3" : [2087, "uchar"],
            
            "Zonemodul 3 Raum 1 akt Temperatur" : [2132, "float"],
            "Zonemodul 3 Raum 1 Solltemperatur" : [2134, "float"],
            "Zonemodul 3 Raum 1 Feuchte" : [2136, "uchar"],
            "Zonemodul 3 Raum 1 Betriebsart" : [2137, "uchar"],
            "Zonemodul 3 Raum 1 Status A1" : [2138, "uchar"],

            "Zonemodul 3 Raum 2 akt Temperatur" : [2139, "float"],
            "Zonemodul 3 Raum 2 Solltemperatur" : [2141, "float"],
            "Zonemodul 3 Raum 2 Feuchte" : [2143, "uchar"],
            "Zonemodul 3 Raum 2 Betriebsart" : [2144, "uchar"],
            "Zonemodul 3 Raum 2 Status A2" : [2145, "uchar"],


            "Zonemodul 3 Raum 3 akt Temperatur" : [2146, "float"],
            "Zonemodul 3 Raum 3 Solltemperatur" : [2148, "float"],
            "Zonemodul 3 Raum 3 Feuchte" : [2150, "uchar"],
            "Zonemodul 3 Raum 3 Betriebsart" : [2151, "uchar"],
            "Zonemodul 3 Raum 3 Status A3" : [2152, "uchar"],


            "Zonemodul 3 Raum 4 akt Temperatur" : [2153, "float"],
            "Zonemodul 3 Raum 4 Solltemperatur" : [2155, "float"],
            "Zonemodul 3 Raum 4 Feuchte" : [2157, "uchar"],
            "Zonemodul 3 Raum 4 Betriebsart" : [2158, "uchar"],
            "Zonemodul 3 Raum 4 Status A4" : [2159, "uchar"],
            
            "Aktueller PV-Ueberschuss" : [74, "float"],
            "Leistung E-Heizstab" : [76, "float"],
            "PV-Leistung" : [76, "float"],
            "Hausverbrauch" : [82, "float"],
            "Batterieentladung" : [84, "float"],
            "Füllstand Batterie" : [86, "float"],
            "Aktuelle Leistungsaufnahme Wärmepumpe" : [4122, "float"],
            "Wärmemenge gesamt" : [4128, "float"],

        }
                    
    def read_uchar(self, addr):
        regs = self.modbus.read_holding_registers(addr, 1)
        if regs:
            return int(regs[0])
        else:
            # print("read_uchar() - error")
            return False

    def read_word(self, addr):
        regs = self.modbus.read_holding_registers(addr, 1)
        if regs:
            return int(regs[0])
        else:
            print("read_word() - error")
            return False

    def read_float(self, addr):
        regs = self.modbus.read_holding_registers(addr, 2)
        if not regs:
            # print("read_float() - error")
            return False

        list_32_bits = utils.word_list_to_long(regs, big_endian=False)
        return float(utils.decode_ieee(list_32_bits[0]))

    def read_data(self, parameter):
        [register, datatype] = self.registers[parameter]
        
        if datatype == "float":
            return self.read_float(register)
        elif datatype == "word":
            return self.read_word(register)
        elif datatype == "uchar":
            return self.read_uchar(register)
        else:
            return False

    def write_float(self, addr, value):
        floats_list = [value]
        b32_l = [utils.encode_ieee(f) for f in floats_list] 
        b16_l = utils.long_list_to_word(b32_l, big_endian=False)
        return self.modbus.write_multiple_registers(addr, b16_l)

    def write_uint16(self, addr, value):
        return self.modbus.write_single_register(addr, value)
   
    def write_data(self, parameter, value):
        [register, datatype] = self.registers[parameter]

        if datatype == "float":
            return self.write_float(register, value)
        elif datatype == "uint16":
            return self.write_uint16(register, value)
        else:
            return False

    def print_all(self):
        print("Show all registers:")
        for name, params in self.registers.items():
            value = self.read_data(name)
            print("{0:d}: {1:s} - {2:2.1f}".format(params[0], name, value))
            
    def print_raw(self):
        print("Raw read 0000-100:")
        for i in range(4100,4150,1):
            value = self.read_float(i)
            if value:
                print("{0:d}: {1:2.3f}".format(i, value))
                # print("{0:d}: {1:d}".format(i, value))
            #else:
            #    print("{0:d}: error".format(i))
            time.sleep(1)
        


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-i", "--ipaddr", help="IP Address of Heating system", 
                           default='192.168.0.58', action='store')
    argparser.add_argument("--debug", help="Enable debug output",
                           action='store_true')
    argparser.add_argument("-t", "--test", help="Enable Test functions",
                           action='store_true')
    argparser.add_argument("-d", "--dump", help="Dump Modbus registers",
                           action='store_true')

    args = argparser.parse_args()

    pump = IPump(ipaddr=args.ipaddr, debug=args.debug)
    

    if args.dump:
        pump.print_all()()

    if args.test:
        # print(pump.read_uchar(1005))
        # print(pump.read_float(1000))
        # pump.write_data("Aktueller PV-Ueberschuss", 4.0)
        # PV Leistung
        # pump.write_float(78, 5.0)
        # pump.write_float(84, -3.0)
        # print(pump.read_uchar(1005))
        # pump.write_data("Betriebsart System", 2)
        # pump.write_uint16(1005, 2)

        # print(pump.read_data("Aussentemperatur B32"))
        print(pump.read_data("Aktueller PV-Ueberschuss"))
        

        # pump.print_all()
        # pump.print_raw()
        
    



