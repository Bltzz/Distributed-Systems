import socket
from threading import Thread
import time
import sys
import uuid

from CommonUtil import encodeMessage, decodeMessage

leader = True

peers = []

UUID = uuid.uuid4()

# class p2p():

#     peers = []


#     def showPeers():
#         print("Peers: ",p2p.peers)

class BroadcastListener(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.bcport = 59073
        self.my_host = socket.gethostname()
        self.my_ip = socket.gethostbyname(self.my_host)
        print("My IP: "+self.my_ip)

        # Create a UDP socket
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the socket to broadcast and enable reusing addresses
        self.listen_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listen_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        self.listen_socket.bind((self.my_ip, self.bcport))
        print("Listening to broadcast messages")
        self.running = True

    def run(self):
        while self.running:
            data, addr = self.listen_socket.recvfrom(1024)
            if data:
                msg = decodeMessage(data)
                print("Received broadcast message:", msg)
                if msg['msg'] not in peers:
                    peers.append(msg['msg'])
                # peers.append(msg['msg'])
                
                if(msg["cmd"] == "INIT"):
                    #SendMessage(msg["msg"], "Not Leader")
                    if(msg["msg"] == self.my_ip and msg["msg"] == peers[0] or self.my_ip in peers):
                        print("Es wird keine TPC Nachricht verschickt")
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
        my_ip = socket.gethostbyname(my_host)
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


class BroadcastSender(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.bcip = '192.168.178.255'
        self.bcport = 59073
        my_host = socket.gethostname()
        my_ip = socket.gethostbyname(my_host)
        self.msg = {
            "cmd": "INIT",
            "uuid": str(UUID),
            "msg": my_ip
        }
        print(self.msg)

        while True:
            time.sleep(2)
            self.broadcast(self.bcip, self.bcport, self.msg)

    def broadcast(self, ip, port, message):
        # Create a UDP socket
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
        self.ip_address = socket.gethostbyname(self.hostname)
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


class TCPUnicastListener(Thread):

    def __init__(self, listeningPort, UUID):
        Thread.__init__(self)
        self.UUID = UUID
        self.listeningPort = listeningPort
        self.host = socket.gethostname()
        self.ip_addr = socket.gethostbyname(self.host)
        print('TCP Unicast at server %s listening on port %s' %
              (self.ip_addr, self.listeningPort))

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', self.listeningPort))
        s.listen(5)
        #conn, addr = s.accept()
        cond = True
        while cond:
            conn, addr = s.accept() #muss in der schleife sein
            data = conn.recv(1024)
            if not data:
                break
            #msg = decodeMessage(data)
            print("Unicast Message received: ", data.decode())
            
            msg = {
                "cmd": "SUCCESS",
                "uuid": str(self.UUID),
                "msg": self.ip_addr,
                "peers": peers
            }
            conn.sendall(encodeMessage(msg))
            MessageInterpreter(data)
            #conn.sendall(str.encode("Thanks"))

        conn.close()

class MessageInterpreter():
    def __init__(self, data):
        self.msg = decodeMessage(data)
        self.command = self.msg['cmd']
        self.ip_addr = self.msg['msg']
        self.id = self.msg['uuid']
        #self.peer_list = self.msg['peers']
        #self.conn = conn

        if(self.command == 'INIT_RESPONSE'):
            self.addResponsivePeerToList(self.ip_addr)
            #conn.close()
        if(self.command == 'SUCCESS'):
            pass
            #peers.extend(self.peer_list)
            

    def addResponsivePeerToList(self, ip_addr):
        peers.append(ip_addr)
        print(peers)

if __name__ == '__main__':
    try:
        # Broadcast Listener
        print("Start TCP Unicast Listener")
        listener = TCPUnicastListener(59072, UUID)
        listener.start()
        #listener.join()
        #print("End TCP Unicast Listener")
        BListener = BroadcastListener()
        BListener.start()

        time.sleep(5)
        # Broadcast Sender
        if (len(peers) >= 1):
            print("Leader existiert schon")
        else:
            BSender = BroadcastSender()
            BSender.start()
        #if len(peers) != 0:
        #    USender = TCPUnicastSender(59072, uuid.uuid4())
        #    USender.sendMessage(peers[0], "Hi wassup")

    except KeyboardInterrupt:
        sys.exit(0)
