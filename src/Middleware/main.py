import socket
from threading import Thread
import time
import sys
import uuid
from json import loads, dumps
import threading
import os

from CommonUtil import encodeMessage, decodeMessage, getBroadcastIP, IP_ADDR



#Global var if this Peer is the leader - set to True after Voting
leader = False
leaderIpAndUUID = (None, None)

#List of Peers Tupel(ip, uuid)
peers = []

UUID = uuid.uuid4()

def sortList():
    sortedList = sorted(peers, key=lambda peers: peers[0])
    #print("Sorted List: ", sortedList)
    #("192.168.172.xxx", str(UUID))
    return sortedList
# needed for heartbeat and voting
def findRightNeighbor(ip_address):
    sortedList = sortList()
    myIndex = sortedList.index((ip_address, str(UUID)))
    return sortedList[(myIndex + 1) % len(sortedList)] # use modulo to implement the list as ring

# needed for heartbeat and voting
def findLeftNeighbor(ip_address):
    sortedList = sortList()
    myIndex = sortedList.index((ip_address, str(UUID)))
    return sortedList[(myIndex - 1) % len(sortedList)] # use modulo to implement the list as ring


class BroadcastListener(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.bcport = 59073
        self.my_host = socket.gethostname()
        self.my_ip = IP_ADDR # from CommonUtil # socket.gethostbyname(self.my_host)
        self.UUID = UUID
        #print("My IP: "+self.my_ip)

        # Create a UDP socket
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the socket to broadcast and enable reusing addresses
        self.listen_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listen_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        self.listen_socket.bind(('', self.bcport))
        #print("Listening to broadcast messages")
        self.running = True

    def run(self):
        while self.running:
            data, addr = self.listen_socket.recvfrom(1024)
            if data:
                #print("Received broadcast message:", decodeMessage(data))
                newUDPThread = UDPBroadcastHandler(data)
                newUDPThread.start()

    def stop(self):
        self.running = False

class UDPBroadcastHandler(Thread):

    def __init__(self, msg):
        Thread.__init__(self)
        self.msg = msg
    
    def run(self):
        MessageInterpreter(self.msg)


class SendMessage():
    def __init__(self, message, command):
        self.bcip = getBroadcastIP()
        self.bcport = 59073
        my_host = socket.gethostname()
        my_ip = IP_ADDR # socket.gethostbyname(my_host)
        self.msg = {
            "cmd": command,
            "uuid": str(UUID),
            "msg": message
        }
        #print(self.msg)

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
        self.bcip = getBroadcastIP()
        self.bcport = 59073
        my_host = socket.gethostname()
        my_ip = IP_ADDR
        self.msg = {
            "cmd": "INIT",
            "uuid": str(UUID),
            "msg": my_ip
        }
        #print(self.msg)

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

    def __init__(self, UUID, recipientIP, msg):
        self.uport = 59072
        #self.UUID = UUID
        self.recipientIP = recipientIP
        self.hostname = socket.gethostname()
        self.ip_address = IP_ADDR
        self.msg = msg
        #print("SEND TCP Message: ", self.msg, self.recipientIP)
        self.sendMessage(self.recipientIP, self.uport, self.msg)

    def sendMessage(self, recipientIP, uport, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #print(recipientIP, uport)
        s.connect_ex((recipientIP, uport))
        s.sendall(encodeMessage(message))
        data = s.recv(1024)
        s.close()
        #print('TCP Received: ', repr(data))

class MessageInterpreter():
    def __init__(self, data):
        self.msg = decodeMessage(data)
        self.command = self.msg['cmd']
        self.ip_addr = self.msg['msg']
        self.id = self.msg['uuid']
        self.my_ip_addr = IP_ADDR
        self.my_id = UUID
        #self.conn = conn

        if(self.command == 'INIT'):
            if(self.ip_addr == self.my_ip_addr ):

                # Wenn Broadcast Nachricht zurück zum Broadcast Sender geht wird keine TCP verschickt
                #print("Es wird keine TCP Nachricht verschickt")
                time.sleep(2)

                # Der neue joiner startet ein Voting
                vote = Voting()
                vote.startVote()

            else:
                peers.append((self.ip_addr, self.id))
                #print(self.my_id)
                res = {
                    "cmd": "INIT_RESPONSE",
                    "uuid": str(self.my_id),
                    "msg": self.my_ip_addr
                }
                TCPUnicastSender(self.my_id, self.ip_addr, res)
            print("Peers: ", peers)
        if(self.command == 'INIT_RESPONSE'):
            self.addPeerToList(self.ip_addr, self.id)
            #conn.close()
        if(self.command == 'SUCCESS'):
            pass
        if(self.command == 'VOTING'):
            voting_instance = Voting()
            voting_instance.respondWithLCRAlgorithmToVote(self.msg)
            pass
        if(self.command == 'AWAKE'):
            pass
        if(self.command == 'HEARTBEAT'):
            pass
        if(self.command == 'LOST_NEIGHBOR'):
            peerToRm = (self.ip_addr, self.id)
            peers.remove(peerToRm)
            #if len(peers) < 3 :
             #   Game.stop()
            # drop from list
            # check if list <=3
            # (stop game, wait for new peer)
            # (else: send updated list via Broadcast)
            pass

    def removePeerFromList(self, ip_addr, id):
        peers.remove((ip_addr, id))
        #print(peers)
            

    def addPeerToList(self, ip_addr, id):
        peers.append((ip_addr, id))
        #print("Peers: ", peers)

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
            #print("New connection added: ", addr)
            newthread = TCPUnicastHandler(conn, addr, self.UUID, self.ip_addr) #missing: execute in a new thread
            newthread.start()

class TCPUnicastHandler(Thread):

    def __init__(self, conn, addr, UUID, ip_addr):
        Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.UUID = UUID
        self.ip_addr = ip_addr

        #print("New connection added: ", self.addr)

    
    def run(self):
        #print("Connection from: ", self.addr)

        while True:
            data = self.conn.recv(1024)
            if not data:
                break
            #msg = decodeMessage(data)
            #print("Unicast Message received: ", data.decode())
            
            msg = {
                "cmd": "SUCCESS",
                "uuid": str(self.UUID),
                "msg": self.ip_addr
            }
            self.conn.sendall(encodeMessage(msg))
            MessageInterpreter(data)
            #conn.sendall(str.encode("Thanks"))
        #print("Peer at ", self.addr ," disconnected...")

class HeartbeatListener(Thread):
    def __init__(self, heartbeat_port, UUID):
        Thread.__init__(self)
        self.heartbeat_port = heartbeat_port
        self.host = socket.gethostname()
        self.ip_addr = IP_ADDR
        self.UUID = UUID

        #print("Heartbeat starting...")

        print("Heartbeat at ", self.ip_addr ," listening on port ", self.heartbeat_port)
        self.running = True
        
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.heartbeat_port))
        s.listen(5)

        while self.running:
            conn, addr = s.accept()
            data = conn.recv(1024)

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

class HeartbeatSender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.running = True
        self.uport = 59071
        self.UUID = UUID
        self.hostname = socket.gethostname()
        self.ip_address = IP_ADDR
        self.counterLeft = 0
        self.counterRight = 0
        self.rightNeighbor = findRightNeighbor(self.ip_address)
        self.leftNeighbor = findLeftNeighbor(self.ip_address)
        #self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.recipientIP = recipientPeer[0]
        #self.recipientUUID = recipientPeer[1]
        self.msg = {
            "cmd": "HEARTBEAT",
            "uuid": str(self.UUID),
            "msg": self.ip_address
        }
        #print("SEND TCP Message: ", self.msg, self.recipientIP)
        #self.sendMessage(self.recipientIP, self.uport, self.msg)

    def run(self):
        self.sendMessage(self.rightNeighbor, self.uport, self.msg, "right")
        time.sleep(2)
        self.sendMessage(self.leftNeighbor, self.uport, self.msg, "left")
        time.sleep(2)
        pass
       

    def sendMessage(self, neighbor, uport, message, direction):
        while self.running:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #print(neighbor[0], uport)
                s.connect_ex((neighbor[0], uport))
                s.sendall(encodeMessage(message))
                data = s.recv(1024)
                time.sleep(1)
                if not data:
                    if direction == "right": 
                        self.counterRight += 1
                    elif direction == "left":
                        self.counterLeft += 1
                    break
                print('TCP Received: ', repr(data))
            except socket.error or Exception:
                if direction == "right": 
                    self.counterRight += 1
                elif direction == "left":
                    self.counterLeft += 1
            finally:
                s.close

            if self.counterLeft > 3 :
                print(neighbor)
                peers.remove(neighbor)
                self.leftNeighbor = findLeftNeighbor(self.ip_address)
                self.sendLostPeerMessage(neighbor)
                pass
            if self.counterRight > 3 :
                print(neighbor)
                peers.remove(neighbor)
                self.rightNeighbor = findRightNeighbor(self.ip_address)
                self.sendLostPeerMessage(neighbor)
        pass

    def sendLostPeerMessage(self, neighbor):
        msgLostPeer = {
                    "cmd": "LOST_NEIGHBOR",
                    "uuid": neighbor[1],
                    "msg": neighbor[0]
                }                
        TCPUnicastSender(self.UUID, self.leftNeighbor[0], msgLostPeer)
        ## if counter > 2 : communicate Lost peer
        #TCPUnicastSender(UUID, leaderIP, {"cmd": "LOST_NEIGHBOR"})
        # Leader: Broadcast -> updated player list

    
class Voting():
    def __init__(self):
        self.ip_address = IP_ADDR
        self.UUID = str(UUID)
        self.isLeaderElected = False
        self.isLeader = False
        self.sortedList = sortList()
        self.rightNeighbor = findRightNeighbor(self.ip_address)
        self.leftNeighbor = findLeftNeighbor(self.ip_address)
        pass



    def startVote(self):
        # needs msg as arg - otherwise we have conflicts! 
        # send message to left neighbor
        msg =  {
            "cmd": "VOTING",
            "uuid": self.UUID,
            "msg": self.ip_address,
            "leaderElected": False
        }
        TCPUnicastSender(self.UUID, self.leftNeighbor[0], msg)
        pass

    def respondWithLCRAlgorithmToVote(self, msg):
        print("Incoming Voting: ", msg)
        receivedUUID = msg["uuid"]
        receivedIP = msg["msg"]
        isLeaderElected = msg["leaderElected"]
        if isLeaderElected:
            if receivedUUID != self.UUID:
                self.isLeaderElected = True
                leader = False
                # TODO: where to put leader ip?
                leaderIpAndUUID = (msg["msg"],msg["uuid"])
                print("My election forward response: ", msg)
                TCPUnicastSender(self.UUID, self.leftNeighbor[0], msg)
        else:
            if self.UUID == receivedUUID:
                leader = True
                response = {
                    "cmd": "VOTING",
                    "uuid": self.UUID,
                    "msg": self.ip_address,
                    "leaderElected" : True
                }
                print("I am Leader: ", msg)
                TCPUnicastSender(self.UUID, self.leftNeighbor[0], response)
            elif self.isOwnUuidIsHigher(self.UUID, receivedUUID):
                # probably ignore this elif
                response = {
                    "cmd": "VOTING",
                    "uuid": self.UUID, 
                    "msg": self.ip_address,
                    "leaderElected" : False
                }
                print("Replacing incoming uuid and ip with my stats, because I am higher", msg)
                TCPUnicastSender(self.UUID, self.leftNeighbor[0], response)
            else:
                print("Forward incoming Voting", msg)
                TCPUnicastSender(self.UUID, self.leftNeighbor[0], msg)
        pass

    def isOwnUuidIsHigher(self, UUID, receivedUUID):
        return (int(uuid.UUID(UUID)) > int(uuid.UUID(receivedUUID)))

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
        pass
        # game code


if __name__ == '__main__':
    try:
        peers.append((IP_ADDR, str(UUID)))
        print(peers)
        # Broadcast Listener
        print("Start TCP Unicast Listener")
        listener = TCPUnicastListener(59072, UUID) #TCP UnicastListener
        listener.start()

        BListener = BroadcastListener()
        BListener.start()

        heartbeat = HeartbeatListener(59071, UUID)
        heartbeat.start()

        time.sleep(5)
        # Broadcast Sender
        BSender = BroadcastSender()

        
        # Voting bevor Gamestart vom Leader (Voting sollte nur von einem Peer gestartet werden)
        # Im voting muss dann das sortieren der uuid passieren

        while len(peers) < 3:
            time.sleep(1)

        time.sleep(3)

        input("Write 'start' to start the game: ")

        #vote = Voting()
        #vote.startVote()

        time.sleep(3)
        if leader:
            print("I AM THE LEADER!!!!!!!!!!!!!!")
        else:
            print("I am only another Peer in the ring!")
        heartbeatSender = HeartbeatSender()
        heartbeatSender.start()

        '''
        #TODO: Loop untill voting.lead_is_elected == True: Then start listening for heartbeats
        while vote.isLeaderElected == True:
            time.sleep(2)
            heartbeatSenderLeft = HeartbeatSender(UUID, vote.leftNeighbor)
            heartbeatSenderRight = HeartbeatSender(UUID, vote.rightNeighbor)


        
        
        # neuer Thread!
        time.sleep(2)
        while True: 
            time.sleep(3)
            heartbeatSender = HeartbeatSender(UUID, vote.leftNeighbor)
            heartbeatSender = HeartbeatSender(UUID, vote.rightNeighbor)
            # wenn ausfällt, dann neues Voting
        # Thread Ende
        # Soll nur beim Leader starten
        if leader == True:
            game = Game()
            game.checkPlayer()
        '''

        # Heartbeat (TCP Unicast)
        #heartbeat = HeartbeatListener(59071, UUID)
        #heartbeat.start()
    except KeyboardInterrupt:
        sys.exit(0)