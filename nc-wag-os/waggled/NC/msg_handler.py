#!/usr/bin/env python3
import sys
import logging
from waggle.protocol.PacketHandler import *
from waggle.protocol.utils import packetmaker
sys.path.append('../Communications/')
from NC_configuration import conf
sys.path.append('../DataCache/')
from send2dc import send


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def msg_handler(msg, DEVICE_DICT):
    """
    Unpacks and acts on messages sent to the node.
    :param string msg: The packed message sent to the node.
    """
    try:
        #unpacks the header
        header = get_header(msg)
    except:
        logger.error('Message is corrupt: %s' % (msg)) #TODO should this send some kind of error response?

    #get the major header type
    major = chr(header['msg_mj_type'])
    minor = chr(header['msg_mi_type'])

    #large file transfer
    if major == 'F':
        #TODO pass to packet reassembler
        pass

    #small file transfer
    elif major == 'f':
        #TODO do something with this file
        pass

    #ping
    elif major == 'p':
        #ping request.
        if minor == 'r':
            #send a ping response
            packet = packetmaker.make_ping_packet()
            for pack_ in packet:
                send(pack_)
        #ping answer
        else:
            #unpack the message
            ping = unpack(msg)
            #print out the body of the message
            logger.debug('Node received: %s'% (ping[1]))
    #time
    elif major == 't':
        #time request
        if minor == 'r':
            #send time
            packet = packetmaker.make_time_packet()
            for pack_ in packet:
                send(pack_)
        #time answer
        else:
            #unpack the message
            time = unpack(msg)
            #print out the body of the message
            logger.debug('Node received time: %s' % (time[1]))
    #sensor data
    elif major == 's':
        #TODO do stuff here
        pass

    #registration
    elif major =='r':
        sender_int = header['s_uniqid']
        sender = nodeid_int2hexstr(sender_int)
        if minor == 'r': #registration request
            if sender_int == 0:
                #message is from cloud
                #unpack the message
                reg = unpack(msg)
                logger.debug('NC received registration: %s' % (reg[1]))
            else:
                #guest node registration
                #sender = str(sender) #convert from int to string
                with open('/etc/waggle/devices', 'r') as _file:
                    lines = _file.readlines()
                #check if device is already registered
                devices = []
                #the first line of the file contains a list of already registered nodes
                #deconstruct string into list
                while not lines[0].find(',')== -1:
                    device, lines[0] = lines[0].split(',',1)
                    devices.append(device)
                try:
                    devices.index(sender) #if this works, the device is already registered
                    #nothing else to be done
                except:
                    #if it fails, the device is not yet registered. Add to list of devices
                    logger.debug('Adding device %s to devices file.' % (sender))
                    devices.append(sender)

                    #Need to find available priorities to assign it
                    #the second line of the file contains a list of available priorities
                    priorities = []
                    while not lines[1].find(',')== -1:
                        priority, lines[1] = lines[1].split(',',1)
                        priorities.append(priority)
                    device_p = priorities.pop()

                    if not device_p == '': #make sure it isn't empty
                        #assign the device to its priority
                        #the third line of the file contains a mapping of device to its priority.
                        #This is what is used to construct the device_dict
                        lines[2] = sender + ':' + device_p + ',' + lines[2]

                        #put the list back together to be written back into the file
                        for priority in priorities:
                            lines[1] = priority + ',' + lines[1]


                        #send GN registration to cloud
                        header_dict = {
                            "msg_mj_type" : ord('r'),
                            "msg_mi_type" : ord('r'),
                            "s_uniqid"    : sender_int
                            }
                        msg = str(conf['QUEUENAME'])
                        try:
                            packet = pack(header_dict, message_data = msg)
                            logger.info('Registration made for node ID %s' % (sender))
                            for pack_ in packet:
                                send(pack_)
                        except Exception as e:
                            logger.error(e)
                    else:
                        logger.error( 'Cannot register any more guestnodes. Maximum of four guestnodes can be registered at one time. Please remove any unused guestnode IDs from the devices file.')

                #put the list back together to be written back into the file
                for device in devices:
                    lines[0] = device + ',' + lines[0]
                #write the lines back into the file
                with open('/etc/waggle/devices', 'w') as _file:
                    _file.writelines(lines)

        elif minor == 'd': #de-registration request from guest node
            #sender = str(sender) #convert from int to string
            logger.info('Received de-registration message from node %s' % (sender))
            with open('/etc/waggle/devices', 'r') as _file:
                lines = _file.readlines()
            #check if device is already registered and remove from devices list
            devices = []
            #the first line of the file contains a list of already registered nodes
            #deconstruct string into list
            while not lines[0].find(',')== -1:
                device, lines[0] = lines[0].split(',',1)
                devices.append(device)

            #now, need to get the priorities list
            priorities = []
            while not lines[1].find(',')== -1:
                priority, lines[1] = lines[1].split(',',1)
                priorities.append(priority)

            #need to remove the device mapping
            mapping = []
            while not lines[2].find(',')== -1:
                device_map, lines[2] = lines[2].split(',',1)
                mapping.append(device_map)

            #try to remove the device from the devices list
            devices.remove(sender)

            #get the device's priority/location from dictionary
            device_p = DEVICE_DICT[sender]

            #add the device's priority/location back to the list
            priorities.append(str(device_p))

            dev_map = sender + ':' + str(device_p)

            #remove device mapping from file
            mapping.remove(dev_map)

            #put everything back together to be written back onto the file
            for priority in priorities:
                lines[1] = priority + ',' + lines[1]

            for device in devices:
                lines[0] = device + ',' + lines[0]

            for maps in mapping:
                lines[2] = maps + ',' + lines[2]

            #write the lines back into the file
            with open('/etc/waggle/devices', 'w') as _file:
                _file.writelines(lines)


    #message type unrecognized
    else:
        logger.error('Message major type "%s" unrecognized.' % (major))
