#
# this is a common Utilities function, containing the basic setup tasks
#
#

import socket
import json
from json import JSONDecodeError, JSONEncoder
import ipaddress
import os

# This code is used by smerlin in this stackoverflow question: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
if os.name != "nt":
    import fcntl
    import struct
    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', bytes(ifname[:15], 'utf-8'))
                # Python 2.7: remove the second argument for the bytes call
            )[20:24])

# This code is used by smerlin in this stackoverflow question: https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
# added enp0s3 to the list, because I'm using debian and a bridged, internal network.
def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = ["enp0s3","eth0","eth1","eth2","wlan0","wlan1","wifi0","ath0","ath1","ppp0"]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                if ip.startswith("192.168"):
                    return ip
                break
            except IOError:
                pass
    return ip


BROADCAST_PORT = 59073
UNICAST_PORT = 59072
SUBNETMASK = "255.255.255.0"
HOST = socket.gethostname()
IP_ADDR = ""
if os.name != "nt":
    IP_ADDR = get_lan_ip()
else:
    IP_ADDR = socket.gethostbyname(HOST)


#If host uses a 127. IP -> read the IP from a .txt file containing the correct IP
if "192" not in IP_ADDR[:4]:
    with open('../DS-IP.txt', 'r') as file:
        IP_ADDR = file.read().replace('\n', '')

def getIP():
    return IP_ADDR

def getTCPUnicastListener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP_ADDR, UNICAST_PORT))
    #s.listen() #Musste in while schleife ausgelagert werden
    return s

def getUDPBroadcastListener():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((IP_ADDR, BROADCAST_PORT))
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
        return json.loads(message) #json.loads(str.decode(message))
    except JSONDecodeError:
        return None

def getBroadcastIP():
    networkaddress = ipaddress.IPv4Network(IP_ADDR + '/' + SUBNETMASK, False)
    return networkaddress.broadcast_address.exploded
