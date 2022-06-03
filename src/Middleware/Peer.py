##
## @author bltzz
##
## This class holds the logic for the peer
## 
##
from base64 import decode, encode
import sys
import os
from json import JSONDecodeError
import json
import threading
import socket
from time import sleep
from typing import List
import uuid

#append the src dir to the sys path, to allow importing other classes.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CommonUtil import UNICAST_PORT, IP_ADDR,BROADCAST_PORT
from CommonUtil import getTCPUnicastListener, getUDPBroadcastListener, encodeMessage, decodeMessage, getBroadcastIP, getIP
        
UUID = uuid.uuid4()
listOfNodes = []

# Default JSON Message looks like this: 
# {
#   "cmd"       : [INIT_BROADCAST, VOTE, START_GAME, TELL_WORD, HEARTBEAT]
#   "uuid"      : $UUID
#   "message"   : [The_Word_to_be_passed] 
# }


def startGame(message):
    return None

def tellWordToNeigbor(message):
    return None

def sendHeartbeat():
    return None

def unicastListener():
    listen_socket = getTCPUnicastListener()
    conn, addr = listen_socket.accept()
    cond = True
    while cond:
        data = None 
        data = conn.recv(1024)
        if data:
            print("Unicast Message received: %s", data.decode())
            msg = {
                "cmd": "SUCCESS"
            }
            conn.sendall(encodeMessage(msg))
            print("answer sent")
            conn.close() 
            interpret_message(data)
            data = None       


def broadcastListener():
    print("Listening for new joiners...")
    listen_socket = getUDPBroadcastListener()
    cond = True
    while cond:
        data = None
        addr = None
        data, addr = listen_socket.recvfrom(1024)
        if data:
            try:
                print("Broadcast Message received: %s", data.decode())
                interpret_message(data)
            except JSONDecodeError:
                print("No Json")
                print(data.decode())
            data = None
    print("Ending Thread")

def interpret_message(data):
    try:
        msg = decodeMessage(data)
    except ValueError:
        #do nothing
        pass
    CMD = {
        'INIT_BROADCAST'        : respondWithOwnIPToBroadcast(msg['message']),
        'INIT_BROADCAST_RES'    : addResponsivePeerToList(msg['message']),
        'VOTE'                  : startVoting(),
        'START_GAME'            : startGame(msg),
        'TELL_WORD'             : tellWordToNeigbor(msg),
        'HEARTBEAT'             : sendHeartbeat(),
        'SUCCESS'               : None
    }
    CMD.get(msg["cmd"])
    return

def sendBroadcast(message):
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Send message on broadcast address
    broadcast_socket.sendto(message, (getBroadcastIP(), BROADCAST_PORT))
    broadcast_socket.close()

def respondWithOwnIPToBroadcast(recipientIP):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((recipientIP, UNICAST_PORT))
    msg = {
        "cmd" : "INIT_BROADCAST_RES",
        "uuid": str(UUID),
        "message" : getIP()
    }
    s.sendall(encodeMessage(msg))
    data = s.recv(1024)
    print(data.decode())
    s.close()
    return

def addResponsivePeerToList(senderIP):
    print("in addToListFunction")
    listOfNodes.append(senderIP)
    print(listOfNodes)
    return

def startVoting():
    return None
##
## testing:
##
if __name__ == '__main__':
    threading.Thread(target=unicastListener).start()
    threading.Thread(target=broadcastListener).start()

    msg = {
        "cmd" : "INIT_BROADCAST",
        "uuid": str(UUID),
        "message" : IP_ADDR
    }
    sleep(5)
    sendBroadcast(encodeMessage(msg))