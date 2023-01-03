# ipump-control
Python based interfacing to a iDM iPump heating system (via modbus TCP)


!!!!!! Warning !!!!!!!! 
* Use on your own risk, this is no approved accessory!
* Running the heating system with modified parameters could potentially void the device warranty. But there is also a chance of increased wearage of the heating system causing damage and expensive repairs.
!!!!!! Warning !!!!!!!! 


Information is mainly based on the document "Modbus TCP Navigatorregelung 2.0" and multiple other Google hits when searching for keywords like "idm ipump modbus".

* ipump/ipump.py is my generic interface to a iDM IPump 3-11 via Modbus TCP.
* influxdb_cli2 is a boring interfacing for InfluxDB using influxdb-client
* ipump_control.py is some control loop which switches the heating system on/off depending on the current electricity price (e.g. hourly price via Tibber)

