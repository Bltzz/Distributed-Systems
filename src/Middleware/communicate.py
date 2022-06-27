from email import message
import socket
import threading
import sys
import time
from base64 import decode, encode
from random import randint
from turtle import update


BROADCAST_IP = "192.168.178.255"
BROADCAST_PORT = 5973

class Server:
    # sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connections = []
    peers = []
    def __init__(self):
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        sck.bind(('0.0.0.0', 10000))
        sck.listen(1)
        print('Server running ...')

        while True:
            b, a = sck.accept()
            bThread = threading.Thread(target=self.handler, args=(b,a))
            bThread.daemon = True
            bThread.start()
            self.connections.append(b)
            self.peers.append(a[0])

            print(self.peers)
            print(a)
            print(str(a[0]) +':'+ str(a[1]), "connected")
            self.sendPeers()

    def handler(self, b, a):
        while True:
            data = b.recv(1024)
            for connection in self.connections:
                connection.send(data)
            if not data:
                print(str(a[0]) + ':' + str(a[1]), "disconnected")
                self.connections.remove(b)
                self.peers.remove(a[0])
                b.close()
                self.sendPeers()
                break

    def broadcastListener(self):
        # Create UDP socket
        ip = p2p.localInformation()
        #Create a UDP socket
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #Set the socket to broadcast and enable reusing addresses
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #Bind socket to address and port
        listen_socket.bind((ip, BROADCAST_PORT))
        
        print('Listening to broadcast messages')
        return listen_socket

    
    def sendPeers(self):
        p = ''
        for peer in self.peers:
            p = p + peer + ','

        for connection in self.connections:
            connection.send(b'\x11'+bytes(p, 'utf-8'))
    # def run(self):
    #     while True:
    #         b, a = self.sck.accept()
    #         bThread = threading.Thread(target=self.handler, args=(b,a))
    #         bThread.daemon = True
    #         bThread.start()
    #         self.connections.append(b)
    #         print(str(a[0]) +':'+ str(a[1]), "connected")

class Client:
    # sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def sendMessage(self, sck):
        #Send Messages to all other peer connections
        while True:
            sck.send(bytes(input(''), 'utf-8'))

    def __init__(self, ip):
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        sck.connect((ip, 10000))

        iThread = threading.Thread(target=self.sendMessage, args=(sck,))
        iThread.daemon = True
        iThread.start()

        

        while True:
            data = sck.recv(1024)
            if not data:
                break
            if data[0:1] == b'\x11':
                self.updatePeers(data[1:])
            else:
                print(str(data, 'utf-8'))

    def updatePeers(self, peerData):
        p2p.peers = str(peerData, 'utf-8').split(',')[:-1]

class Broadcast:

    def handler(self, listen_socket):
        while True:
            data = listen_socket.recv(1024)
            if data:
                print("Received broadcast: ", data.decode())
                if data[0:1] == b'\x11':
                    self.updatePeers(data[1:])

    def updatePeers(self, peerData):
        p2p.peers = str(peerData, 'utf-8').split(',')[:-1]
        print(p2p.peers)

    def __init__(self):
        ip = p2p.localInformation()
        p2p.peers.append(ip)
        print(p2p.peers)
        # Create a UDP socket
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the socket to broadcast and enable reusing addresses
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        listen_socket.bind((ip, BROADCAST_PORT))
        print("Listening to broadcast ...")
        print(0000)
        while True:
            print("while")
            data = None
            addr = None
            data,addr = listen_socket.recvfrom(1024)
            print(data)
            if data:
                try:
                    print("Received broadcast: ", data.decode())
                    self.updatePeers(data[1:])
                except:
                    print("No Json")
                    print(data.decode())
                data = None

class unicast:
    def __init__(self):
        pass

class p2p:
    peers = []
    print("Peers: ",peers)

    def localInformation():
        MY_HOST = socket.gethostname()
        MY_IP = socket.gethostbyname(MY_HOST)
        print("Meine IP: "+MY_IP)

        return MY_IP

while True:
    try:
        print('Trying to connect ...')
        
        print(p2p.peers)
        if len(p2p.peers) == 0:
            broadcast = Broadcast()
        time.sleep(randint(1, 5))
        for peer in p2p.peers:
            try:
                client = Client(peer)
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                pass
            if randint(1, 2) == 1 :

                try:
                    server = Server()
                except KeyboardInterrupt:
                    sys.exit(0)
                except:
                    print("Konnte Server nicht starten ...")
    except KeyboardInterrupt:
        sys.exit(0)