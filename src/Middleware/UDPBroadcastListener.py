
from multiprocessing.pool import INIT
import socket
import ipaddress
import threading
import uuid
import json
from json import JSONDecodeError
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import TCPUnicastSender

class UDPBroadcastListener(threading.Thread):
    
    def __init__(self, broadcastPort, subnetmask, uuid):
        threading.Thread.__init__(self)
        self.UUID = uuid
        self.broadcastPort = broadcastPort
        self.host = socket.gethostname()
        self.ip_addr = socket.gethostbyname(self.host)
        self.boradcastIP = self.getBroadcastIP(self.ip_addr, subnetmask)
        self.sender = TCPUnicastSender.TCPUnicastSender(59072, self.UUID)

    def getBroadcastIP(self, IP, SUBNETMASK):
        networkaddress = ipaddress.IPv4Network(IP + '/' + SUBNETMASK, False)
        return networkaddress.broadcast_address.exploded

    def run(self):
        print("Start run")
        # Create a UDP socket
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the socket to broadcast and enable reusing addresses
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        listen_socket.bind(('', self.broadcastPort))
        print("Listening to broadcast messages")

        cond = True
        while cond:
            data, addr = listen_socket.recvfrom(1024)
            if data:
                try:
                    ## TODO: Based on Message: Do something
                    dictmsg = json.loads(data)
                    if dictmsg["msg"] == "INIT":
                        print("Init request")
                        reply = {
                            "uuid" : str(self.UUID),
                            "ip" : self.ip_addr,
                            "msg" : "INIT_REPLY"
                        }
                        self.sender.sendMessage(dictmsg["ip"], json.dumps(reply))
                    print("UDP Received broadcast message:", data.decode())
                    if data.decode() == "End":
                        print("In End")
                        cond = False
                except JSONDecodeError:
                    print("No Json :) ")
                    print(data.decode())

        print("Ending Thread")


##
## testing:
##
if __name__ == '__main__':
    # Listening port
    BROADCAST_PORT = 59073
    SUBNETMASK = "255.255.255.0"
    listener = UDPBroadcastListener(BROADCAST_PORT, SUBNETMASK, uuid.uuid4())
    listener.start()