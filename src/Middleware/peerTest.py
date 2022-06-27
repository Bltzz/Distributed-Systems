import socket
import json
import sys
import os
import uuid
import threading
import ipaddress
import time

BROADCAST_PORT = 59073
UNICAST_PORT = 59072
SUBNET = '255.255.255.0'
HOST = ''
IP_ADDR = ''
UUID = uuid.uuid4()
listOfNodes = []

def getIP():
    HOST = socket.gethostname()
    print(HOST)
    IP_ADDR = socket.gethostbyname("localhost")
    print(IP_ADDR)
    return IP_ADDR

def getBroadcastIP():
    ip = getIP()
    adr = ip+"/"+'255'
    print(adr)
    netIP = ipaddress.ip_network(getIP(), strict=False)
    return netIP.broadcast_address.exploded

def broadcastListener():
    print("Listen...")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', BROADCAST_PORT))
    print("after")
    data = None
    addr = None
    data = s.recvfrom(1024);
    incName = data[0].decode();
    print("incName: "+incName)

    while True:
        if data:
            print("data")
            try:
                print("Message received: %s", data)
                msg = data
                message(data['message'])
            except json.JSONDecodeError:
                print("NO")
                print(data.decode())
            data = None

def message(ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, UNICAST_PORT))
    msg = {
        "cmd" : "INIT_BROADCAST_RES",
        "uuid": str(UUID),
        "message" : getIP()
    }
    s.sendall(str.encode(json.dumps(msg)))
    data = s.recv(1024)
    print(data.decode())
    s.close()

    print("addTOList")
    listOfNodes.append(ip)
    print(listOfNodes)
    return


def unicastlistener():
    getIP()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP_ADDR, UNICAST_PORT))
    s.listen()
    
    conn, addr = s.accept()

    while True:
        data = conn.recv(1024)
        print(data)

        if data:
            print('Unicast: %s', data.decode())
            msg = {"cmd": "SUCCESS"}
            conn.sendall(str.encode(json.dumps(msg)))
            print("sent")
            conn.close()
            message(msg["message"])
            data = None

def sendBroadcast(message):
    bcs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bcs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    bcs.sendto(message, (getBroadcastIP(), BROADCAST_PORT))


if __name__ == '__main__':
    threading.Thread(target=unicastlistener).start()
    threading.Thread(target=broadcastListener).start()

    msg = {
        "cmd" : "INIT_BROADCAST",
        "uuid": str(UUID),
        "message" : IP_ADDR
    }
    time.sleep(5)
    sendBroadcast(str.encode(json.dumps(msg)))