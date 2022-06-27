
import socket
from threading import Thread
import time
import sys
import uuid
import argparse
from json import loads, dumps
import threading
import os

from CommonUtil import encodeMessage, decodeMessage, get_lan_ip, IP_ADDR
from Middleware.test import sortList
from sample_code.broadcastsender import MY_IP


#Leader vom SPiel
leader = True

#Liste der Peers (sollte ein Tuple werden wegen der uuid)
peers = []

UUID = uuid.uuid4()


class BroadcastListener(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.bcport = 59073
        self.my_host = socket.gethostname()
        self.my_ip = IP_ADDR # from CommonUtil # socket.gethostbyname(self.my_host)
        print("My IP: "+self.my_ip)

        # Create a UDP socket
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the socket to broadcast and enable reusing addresses
        self.listen_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listen_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        self.listen_socket.bind(('', self.bcport))
        print("Listening to broadcast messages")
        self.running = True

    def run(self):
        while self.running:
            data, addr = self.listen_socket.recvfrom(1024)
            if data:
                msg = decodeMessage(data)
                print("Received broadcast message:", msg)
                peers.append((msg['msg'], msg['uuid']))
                
                if(msg["cmd"] == "INIT"):
                    #SendMessage(msg["msg"], "Not Leader")
                    if(msg["msg"] == self.my_ip ):
                        #Wenn Broadcast Nachricht zurück zum Broadcast Sender geht wird
                        #keine TCP
                        print("Es wird keine TCP Nachricht verschickt")
                        #leader= True #Vorläufiger leader
                        #print("Leader ?: ",leader)
                    else:
                        print(UUID)
                        TCPUnicastSender(UUID, msg['msg'])

                if(msg["cmd"] == "Not Leader"):
                    leader = False
                    print("Peer")
                print("Peers: ", peers)

    def stop(self):
        self.running = False


class SendMessage():
    def __init__(self, message, command):
        self.bcip = '192.168.178.255'
        self.bcport = 59073
        my_host = socket.gethostname()
        my_ip = IP_ADDR # socket.gethostbyname(my_host)
        self.msg = {
            "cmd": command,
            "uuid": str(UUID),
            "msg": message
        }
        print(self.msg)

        self.broadcast(self.bcip, self.bcport, self.msg)

    def broadcast(self, ip, port, message):
        # Create a UDP socket
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send message on broadcast address
        broadcast_socket.sendto(encodeMessage(message), (ip, port))

    def stop(self):
        self.running = False


class BroadcastSender():
    def __init__(self):
        self.bcip = '192.168.178.255'
        self.bcport = 59073
        my_host = socket.gethostname()
        my_ip = IP_ADDR
        self.msg = {
            "cmd": "INIT",
            "uuid": str(UUID),
            "msg": my_ip
        }
        print(self.msg)

        self.broadcast(self.bcip, self.bcport, self.msg)

    def broadcast(self, ip, port, message):
        # Create a UDP socket
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Send message on broadcast address
        broadcast_socket.sendto(encodeMessage(message), (ip, port))

    def stop(self):
        self.running = False


class TCPUnicastSender():

    def __init__(self, UUID, recipientIP):
        self.uport = 59072
        self.UUID = UUID
        self.recipientIP = recipientIP
        self.hostname = socket.gethostname()
        self.ip_address = IP_ADDR
        self.msg = {
            "cmd": "INIT_RESPONSE",
            "uuid": str(self.UUID),
            "msg": self.ip_address
        }
        print("SEND TCP Message: ", self.msg, self.recipientIP)
        self.sendMessage(self.recipientIP, self.uport, self.msg)

    def sendMessage(self, recipientIP, uport, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(recipientIP, uport)
        s.connect_ex((recipientIP, uport))
        s.sendall(encodeMessage(message))
        data = s.recv(1024)
        s.close()
        print('TCP Received: ', repr(data))

class MessageInterpreter():
    def __init__(self, data):
        self.msg = decodeMessage(data)
        self.command = self.msg['cmd']
        self.ip_addr = self.msg['msg']
        self.id = self.msg['uuid']
        #self.conn = conn

        if(self.command == 'INIT_RESPONSE'):
            self.addPeerToList(self.ip_addr, self.id)
            #conn.close()
        if(self.command == 'SUCCESS'):
            pass
        if(self.command == 'VOTING_INIT'):
            pass
        if(self.command == 'VOTING_ELECTED'):
            pass
        if(self.command == 'AWAKE'):
            pass
        if(self.command == 'HEARTBEAT'):
            pass

    def removePeerFromList(self, ip_addr, id):
        peers.remove((ip_addr, id))
        print(peers)
            

    def addPeerToList(self, ip_addr, id):
        peers.append((ip_addr, id))
        print(peers)

class TCPUnicastListener(Thread):
    def __init__(self, listeningPort, UUID):
        Thread.__init__(self)
        self.UUID = UUID
        self.listeningPort = listeningPort
        self.host = socket.gethostname()
        self.ip_addr = IP_ADDR

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.listeningPort))
        print('TCP Unicast at server %s listening on port %s' % (self.ip_addr, self.listeningPort))

        while True:
            ##print("True")
            s.listen(1)
            conn, addr = s.accept()
            print("New connection added: ", addr)
            newthread = TCPUnicastHandler(conn, addr, self.UUID, self.ip_addr)
            newthread.start()

class TCPUnicastHandler(Thread):

    def __init__(self, conn, addr, UUID, ip_addr):
        Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.UUID = UUID
        self.ip_addr = ip_addr

        print("New connection added: ", self.addr)

    
    def run(self):
        print("Connection from: ", self.addr)

        while True:
            data = self.conn.recv(1024)
            if not data:
                break
            #msg = decodeMessage(data)
            print("Unicast Message received: ", data.decode())
            
            msg = {
                "cmd": "SUCCESS",
                "uuid": str(self.UUID),
                "msg": self.ip_addr
            }
            self.conn.sendall(encodeMessage(msg))
            MessageInterpreter(data)
            #conn.sendall(str.encode("Thanks"))
        print("Peer at ", self.addr ," disconnected...")

class HeartbeatListener(Thread):
    def __init__(self, heartbeat_port, UUID):
        Thread.__init__(self)
        self.heartbeat_port = heartbeat_port
        self.host = socket.gethostname()
        self.ip_addr = IP_ADDR
        self.UUID = UUID

        print("Heartbeat starting...")

        print("Heartbeat at ", self.ip_addr ," listening on port ", self.heartbeat_port)
        self.running = True
        
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.heartbeat_port))
        s.listen(5)

        while self.running:
            conn, addr = s.accept()
            data = conn.rcv(1024)

            if not data:
                break
            print("Heartbeat Message received: ", data.decode())

            msg = {
                "cmd":"AWAKE",
                "uuid": str(self.UUID),
                "msg": self.ip_addr
            }
            conn.sendall(encodeMessage(msg))
            MessageInterpreter(data)

        conn.close()

class HeartbeatSender():
    def __init__(self, UUID, recipientIP):
        self.uport = 59071
        self.UUID = UUID
        self.recipientIP = recipientIP
        self.hostname = socket.gethostname()
        self.ip_address = IP_ADDR
        self.msg = {
            "cmd": "HEARTBEAT",
            "uuid": str(self.UUID),
            "msg": self.ip_address
        }
        print("SEND TCP Message: ", self.msg, self.recipientIP)
        self.sendMessage(self.recipientIP, self.uport, self.msg)

    def sendMessage(self, recipientIP, uport, message):
        ## try
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(recipientIP, uport)
        s.connect_ex((recipientIP, uport))
        s.sendall(encodeMessage(message))
        data = s.recv(1024)
        s.close()
        print('TCP Received: ', repr(data))
        ## expect socket.error: 
        ### counter ++

        ## if counter > 2 : communicate Lost peer

    
class Voting():
    def __init__(self):
        self.isLeader = False
        self.isLeaderElected = False
        self.sortedList = self.sortList()
        self.rightNeigbor = self.findRightNeigbor()
        self.leftNeigbor = self.findLeftNeigbor()
        pass

    def sortList(self):
        self.sortedList = sorted(peers, key=lambda peers: peers[0])
        print("Sorted List: ", self.sortedList)

    # also needed for heartbeat
    def findRightNeigbor(self):
        myIndex = self.sortedList.index(MY_IP)
        if myIndex != 0 and self.sortedList[myIndex][1] != UUID:
            return self.sortedList[myIndex - 1]
        elif myIndex == 0:
            return self.sortedList[len(self.sortedList) - 1]
    
    # also needed for heartbeat
    def findLeftNeigbor(self):
        myIndex = self.sortedList.index(MY_IP)
        if myIndex != (len(self.sortedList) - 1) and self.sortedList[myIndex][1] != UUID:
            return self.sortedList[myIndex - 1]
        elif myIndex == (len(self.sortedList) - 1):
            return self.sortedList[0]

    def validateIncomingMessage(self):
        # do the checking and pass the higher UUID. 
        pass  

    def vote(self):
        # needs msg as arg - otherwise we have conflicts! 
        # send message to left neighbor
        #TCPUnicastSender(UUID, self.leftNeigbor[0])

        pass

class Game():
    def __init__(self):
        self.check = True

    def checkPlayer(self):
        
        # Solange es keine 3 Player gibt geht es nicht weiter
        while self.check:
            if(len(peers) >= 3):
                self.check = False
            else:
                pass
        print("If you want to start the game write 'startGame' (without spacing)")
        start= input()

        if (start.lower() == "startgame"):
            time.sleep(5)
            self.startGame()
        else:
            pass

    def startGame(self):
        print("Game start...")
        # game code


if __name__ == '__main__':
    try:
        # Broadcast Listener
        print("Start TCP Unicast Listener")
        listener = TCPUnicastListener(59072, UUID) #TCP UnicastListener
        listener.start()

        BListener = BroadcastListener()
        BListener.start()

        time.sleep(5)
        # Broadcast Sender
        BSender = BroadcastSender()

        # Voting bevor Gamestart vom Leader (Voting sollte nur von einem Peer gestartet werden)
        # Im voting muss dann das sortieren der uuid passieren
        vote = Voting()
        vote.vote()



        # Soll nur beim Leader starten
        if leader == True:
            game = Game()
            game.checkPlayer()


        # Heartbeat (TCP Unicast)
        #heartbeat = HeartbeatListener(59071, UUID)
        #heartbeat.start()




    except KeyboardInterrupt:
        sys.exit(0)