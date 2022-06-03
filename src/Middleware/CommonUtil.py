#
# this is a common Utilities function, containing the basic setup tasks
#
#

import socket
import json
from json import JSONDecodeError, JSONEncoder
import ipaddress

BROADCAST_PORT = 59073
UNICAST_PORT = 59072
SUBNETMASK = "255.255.255.0"
HOST = socket.gethostname()
IP_ADDR = socket.gethostbyname(HOST)

def getIP():
    return IP_ADDR

def getTCPUnicastListener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP_ADDR, UNICAST_PORT))
    s.listen()
    return s

def getUDPBroadcastListener():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', BROADCAST_PORT))
    return s

def encodeMessage(message):
    try:
        #print("Trying to encode Message")
        return str.encode(json.dumps(message))
    except ValueError:
        print("ValueError during encoding")
        return str.encode(message)

def decodeMessage(message):
    try:
        return json.loads(message)
    except JSONDecodeError:
        return None

def getBroadcastIP():
    networkaddress = ipaddress.IPv4Network(IP_ADDR + '/' + SUBNETMASK, False)
    return networkaddress.broadcast_address.exploded
