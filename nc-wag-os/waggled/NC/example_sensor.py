#!/usr/bin/env python
import time, serial, sys, datetime, os, random
sys.path.append('../../../')
from waggle_protocol.utilities import packetmaker
sys.path.append('../Communications/')
from internal_communicator import send



def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

def unix_time_millis(dt):
    return long(unix_time(dt) * 1000.0)
    


temperature_file = '/sys/class/thermal/thermal_zone0/temp'


if os.path.isfile(temperature_file): 
    count = 0
    while 1:
        tempC = int(open(temperature_file).read()) / 1e3
        timestamp_utc = datetime.datetime.utcnow()
        timestamp_date = timestamp_utc.date()
        timestamp_epoch =  int(float(timestamp_utc.strftime("%s.%f"))) * 1000
        #old: sendData=['CPU temperature', int(unix_time_millis(datetime.datetime.now())), ['Temperature']  , ['i'], [tempC], ['Celsius'], ['count='+str(count)]]
        # node_id, date, plugin_id, plugin_version, timestamp, sensor_id, data, meta
        #old: sendData=['CPU temperature', int(unix_time_millis(datetime.datetime.now())), ['Temperature']  , ['i'], [tempC], ['Celsius'], ['count='+str(count)]]
        sendData=[str(timestamp_date), 'test_plugin_cpu_temp', '1', 'default', str(timestamp_epoch), ['cpu_temperature'], [str(tempC)], ['meta.txt'] ]
        print 'Sending data: ',sendData
        #packs and sends the data
        packet = packetmaker.make_data_packet(sendData)
        for pack in packet:
            send(pack)
        #send a packet every 10 seconds
        time.sleep(10)
        count = count + 1
        
else:
    count = 0
    while 1:
        rint = random.randint(1, 100)
        # old: sendData=['RandomNumber', int(unix_time_millis(datetime.datetime.now())), ['Random']  , ['i'], [rint], ['NA'], ['count='+str(count)]]
        sendData=[str(timestamp_date), 'test_plugin_random', '1', 'default', str(timestamp_epoch), ['random'], [str(rint)], ['meta.txt'] ]
        print 'Sending data: ',sendData
        #packs and sends the data
        packet = packetmaker.make_data_packet(sendData)
        for pack in packet:
            send(pack)
        #send a packet every 10 seconds
        time.sleep(10)
        count = count + 1


