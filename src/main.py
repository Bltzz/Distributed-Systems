import socket
from threading import Thread
import time
import sys
import uuid
from json import loads, dumps
import threading
import os
import random
import csv

from CommonUtil import encodeMessage, decodeMessage, getBroadcastIP, IP_ADDR

debug = False

#Global var if this Peer is the leader - set to True after Voting
global leader
leader = False
global leaderIpAndUUID
leaderIpAndUUID = (None, None)

#List of Peers Tupel(ip, uuid)
peers = []

UUID = uuid.uuid4()

def sortList():
    sortedList = sorted(peers, key=lambda peers: peers[0])
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

        # Create a UDP socket
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the socket to broadcast and enable reusing addresses
        self.listen_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listen_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        self.listen_socket.bind(('', self.bcport))
        self.running = True

    def run(self):
        while self.running:
            data, addr = self.listen_socket.recvfrom(1024)
            if data:
                #print("Received broadcast message:", decodeMessage(data))
                newUDPThread = UDPBroadcastHandler(data)
                newUDPThread.start()
                if debug: print("Broadcast received: ", decodeMessage(data))

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
        self.recipientIP = recipientIP
        self.hostname = socket.gethostname()
        self.ip_address = IP_ADDR
        self.msg = msg
        if debug: print("SEND TCP Message: ", self.msg, self.recipientIP)
        self.sendMessage(self.recipientIP, self.uport, self.msg)

    def sendMessage(self, recipientIP, uport, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect_ex((recipientIP, uport))
        s.sendall(encodeMessage(message))
        data = s.recv(1024)
        s.close()
        if debug: print('TCP Received: ', repr(data))

class MessageInterpreter():
    def __init__(self, data):
        self.msg = decodeMessage(data)
        self.command = self.msg['cmd']
        self.content = self.msg['msg'] # Often it is an ip address
        self.id = self.msg['uuid']
        self.my_ip_addr = IP_ADDR
        self.my_id = UUID
        global leaderIpAndUUID
        global peers
        global leader
        global BSender
        global game

        if(self.command == 'INIT'):
            if(self.content  == self.my_ip_addr ):

                # Wenn Broadcast Nachricht zurück zum Broadcast Sender geht wird keine TCP verschickt
                time.sleep(2)

                # Der neue joiner startet ein Voting
                vote = Voting()
                vote.startVote()

            else:
                peers.append((self.content, self.id))
                res = {
                    "cmd": "INIT_RESPONSE",
                    "uuid": str(self.my_id),
                    "msg": self.my_ip_addr
                }
                TCPUnicastSender(self.my_id, self.content, res)
            if debug: print("Peers: ", peers)
        if(self.command == 'INIT_RESPONSE'):
            self.addPeerToList(self.content, self.id)
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
        if(self.command == 'LOST_PEER'):
            if debug: print("The leader informed that one peer is lost")
            try:
                peers.remove((self.content, self.id))
                if debug: print("Removed the lost peer from the list")
            except ValueError: # Peer was already removed -> do nothing
                if debug: print("Faild to remove the lost peer from the list. Probably happend already before!")
                pass

            if game.running and len(peers) < players:
                if debug: print("Too less peers: STOP GAME!!!")
                game.changeState({"state": "WaitForStart"})
                pass
            
            if game.running: # Maybe the peer need to resend its whispered word
                game.lostPlayer(self.content)

            pass
        if(self.command == 'LOST_NEIGHBOR'):
            # Only the leader can receive this kind of message
            if debug: print("One of the peers informed that it lost a neighbor -> broadcast this information to the ring")
            msgLostPeer = {
                "cmd": "LOST_PEER",
                "uuid": self.id,
                "msg": self.content
            }

            BSender.broadcast(BSender.bcip, BSender.bcport, msgLostPeer)
        
        if(self.command == 'GAME'):
            if debug: print("Received this state changing message:", self.content)
            game.changeState(self.content)


    def removePeerFromList(self, ip_addr, id):
        peers.remove((ip_addr, id))
        
    def addPeerToList(self, ip_addr, id):
        peers.append((ip_addr, id))
        if debug: print("Peers: ", peers)

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
        if debug: print('TCP Unicast at server %s listening on port %s' % (self.ip_addr, self.listeningPort))

        while True:
            s.listen(1)
            conn, addr = s.accept()
            if debug: print("New connection added: ", addr)
            newthread = TCPUnicastHandler(conn, addr, self.UUID, self.ip_addr)
            newthread.start()

class TCPUnicastHandler(Thread):

    def __init__(self, conn, addr, UUID, ip_addr):
        Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.UUID = UUID
        self.ip_addr = ip_addr

        if debug: print("New connection added: ", self.addr)

    
    def run(self):
        if debug: print("Connection from: ", self.addr)

        while True:
            data = self.conn.recv(1024)
            if not data:
                break
            #msg = decodeMessage(data)
            if debug: print("Unicast Message received: ", data.decode())
            
            msg = {
                "cmd": "SUCCESS",
                "uuid": str(self.UUID),
                "msg": self.ip_addr
            }
            self.conn.sendall(encodeMessage(msg))
            MessageInterpreter(data)
            #conn.sendall(str.encode("Thanks"))
        if debug: print("Peer at ", self.addr ," disconnected...")

class HeartbeatListener(Thread):
    def __init__(self, heartbeat_port, UUID):
        Thread.__init__(self)
        self.heartbeat_port = heartbeat_port
        self.host = socket.gethostname()
        self.ip_addr = IP_ADDR
        self.UUID = UUID

        #print("Heartbeat starting...")

        if debug: print("Heartbeat at ", self.ip_addr ," listening on port ", self.heartbeat_port)
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
            #print("Heartbeat Message received: ", data.decode())

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
        #self.rightNeighbor = findRightNeighbor(self.ip_address)
        #self.leftNeighbor = findLeftNeighbor(self.ip_address)
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
        while self.running:
            self.sendMessage(findRightNeighbor(self.ip_address), self.uport, self.msg, "right") #Need to search neighbor each time again in case the peers list changed
            time.sleep(0.5)
            self.sendMessage(findLeftNeighbor(self.ip_address), self.uport, self.msg, "left") #Need to search neighbor each time again in case the peers list changed
            time.sleep(0.5)
        pass
       

    def sendMessage(self, neighbor, uport, message, direction):

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #print(neighbor[0], uport)
            s.connect_ex((neighbor[0], uport))
            s.sendall(encodeMessage(message))
            data = s.recv(1024)
            #time.sleep(1)
            if not data:
                if direction == "right": 
                    self.counterRight += 1
                    if debug: print("Right neighbor counter 'no data' +1")
                elif direction == "left":
                    self.counterLeft += 1
                    if debug: print("Left neighbor counter 'no data' +1")
                return
            #print('TCP Received from', direction,'neighbor: ', repr(data))
        except socket.error or Exception:
            if direction == "right": 
                self.counterRight += 1
                self.failureRight = True
                if debug: print("Right neighbor counter 'socket error' +1")
            elif direction == "left":
                self.counterLeft += 1
                self.failureLeft = True
                if debug: print("Left neighbor counter 'socket error' +1")
        finally:
            s.close

        if self.counterLeft > 3 :
            if debug: print("Left neighbor lost: ", neighbor)
            #peers.remove(neighbor)
            #self.leftNeighbor = findLeftNeighbor(self.ip_address)
            self.sendLostPeerMessage(neighbor)
            self.counterLeft = 0
            pass
        if self.counterRight > 3 :
            if debug: print("Right neighbor lost: ", neighbor)
            #peers.remove(neighbor)
            #self.rightNeighbor = findRightNeighbor(self.ip_address)
            self.sendLostPeerMessage(neighbor) #Broadcast an den leader?
            self.counterRight = 0
        pass

    def sendLostPeerMessage(self, neighbor):
        global leaderIpAndUUID
        global leader
        global BSender
        
        if neighbor[0] == leaderIpAndUUID[0]:
            # Leader got lost. --> Detecting peer takes temporary leader role, broadcasts the lost leader and starts new leader voting

            if debug: print("The leader is lsot. This peer will be the temprary leader.")
            
            leader = True

            msgLostPeer = {
                "cmd": "LOST_PEER",
                "uuid": neighbor[1],
                "msg": neighbor[0]
            }

            BSender.broadcast(BSender.bcip, BSender.bcport, msgLostPeer)

            time.sleep(1)

            vote = Voting()
            vote.startVote()

        else:
            # The detecting peer informs the leader about the lost peer
            if debug: print("Inform the leader that one neighbor iszt lost")
            msgLostNeighbor = {
                        "cmd": "LOST_NEIGHBOR",
                        "uuid": neighbor[1],
                        "msg": neighbor[0]
                    }

            TCPUnicastSender(self.UUID, leaderIpAndUUID[0], msgLostNeighbor)
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
        global leader
        global leaderIpAndUUID
        if debug: print("Incoming Voting: ", msg)
        receivedUUID = msg["uuid"]
        receivedIP = msg["msg"]
        isLeaderElected = msg["leaderElected"]
        if isLeaderElected:
            if receivedUUID != self.UUID:
                self.isLeaderElected = True
                leader = False
                # TODO: where to put leader ip?
                
                if debug: print("My election forward response: ", msg)
                TCPUnicastSender(self.UUID, self.leftNeighbor[0], msg)
            leaderIpAndUUID = (msg["msg"],msg["uuid"])
        else:
            if self.UUID == receivedUUID:
                leader = True
                response = {
                    "cmd": "VOTING",
                    "uuid": self.UUID,
                    "msg": self.ip_address,
                    "leaderElected" : True
                }
                if debug: print("I am Leader: ", msg)
                TCPUnicastSender(self.UUID, self.leftNeighbor[0], response)
            elif self.isOwnUuidIsHigher(self.UUID, receivedUUID):
                # probably ignore this elif
                response = {
                    "cmd": "VOTING",
                    "uuid": self.UUID, 
                    "msg": self.ip_address,
                    "leaderElected" : False
                }
                if debug: print("Replacing incoming uuid and ip with my stats, because I am higher", msg)
                TCPUnicastSender(self.UUID, self.leftNeighbor[0], response)
            else:
                if debug: print("Forward incoming Voting", msg)
                TCPUnicastSender(self.UUID, self.leftNeighbor[0], msg)
        pass

    def isOwnUuidIsHigher(self, UUID, receivedUUID):
        return (int(uuid.UUID(UUID)) > int(uuid.UUID(receivedUUID)))

class Game():
    def __init__(self, uuid, ip):
        self.running = True
        self.check = True
        self.uuid = uuid
        self.my_ip = ip
        self.word_understood = None
        self.POINTS_FOR_CORRECT_ANSWER = 10
        self.PROB_FOR_ONE_WORD_DOWN = 0.33
        self.PROB_FOR_SAME_WORD = 0.66
        self.PROB_FOR_ONE_WORD_UP = 1
        self.state = "WaitForStart"
        self.message = None

    def startGame(self):
        print("-"*30)
        # Solange nicht alle Player da sind, geht es nicht weiter
        while (len(peers) < players):
            time.sleep(0.5)
            print(f'🔴 Identified {len(peers)}/{players} players: {", ".join([peer[0] for peer in peers])}', end="\r")
            pass

        while self.running: # Check the current game state
            if self.state == "WaitForStart": self.waitForStart()
            elif self.state == "InsertWord": self.insertWord()
            elif self.state == "WaitForWord": self.waitForWord()
            elif self.state == "WaitForResult": self.waitForResult()
            elif self.state == "ProcessResult": self.processResult()

    def changeState(self, msg):
        self.message = msg
        self.state = self.message['state']
        if debug: print("Changed state to " + self.state)
        pass

    def waitForStart(self):
        if debug: print("I entered waitForStart")
        global BSender
        global leader
        global peers
        
        # If a peer did meanwhile, wee neeed toc heck if we still have the min number of players
        while (len(peers) < players):
            time.sleep(0.5)
            print(f'🔴 Identified {len(peers)}/3 players: {", ".join([peer[0] for peer in peers])}', end="\r")
            pass

        print(f'✅ Identified {len(peers)}/{len(peers)} players: {", ".join([peer[0] for peer in peers])}')
        # The neighbor who will receive your input
        self.receivingIP = findRightNeighbor(self.my_ip)[0]

        if leader:

            time.sleep(3)

            # Be safe that everyone is in the "WaitForStart" State. Important espeacially when leader has crashed and a restart is necessary.
            msgStateChange = {
                "cmd": "GAME",
                "uuid": str(self.uuid),
                "msg": {"state": "WaitForStart", "ip": self.my_ip}
            }

            BSender.broadcast(BSender.bcip, BSender.bcport, msgStateChange)

            time.sleep(1)

            start = None
            while not start:
                start = input("If you want to start the game write 'startGame' (without spacing): ")

            if (start.lower() == "startgame"):

                msgStateChange = {
                    "cmd": "GAME",
                    "uuid": str(self.uuid),
                    "msg": {"state": "WaitForWord", "ip": self.my_ip}
                }

                BSender.broadcast(BSender.bcip, BSender.bcport, msgStateChange)

                time.sleep(1)

                self.state = "InsertWord"
                
            else:
                pass

        elif not leader:
            print("Wait until the leader starts the game ...")
            while self.state == "WaitForStart":
                if leader: # Could be that the leader crashes and a waiting peer receives the leader role in the meantime
                    return
                time.sleep(1)

    def insertWord(self):
        print("-"*30)
        global leader
        
        if leader:
            self.word_understood = None
            while not self.word_understood:
                self.word_understood = input("📣 You are the leader. Please choose a word from the csv file and write it down: ").lower()

            if self.state != "InsertWord": return

            msgStateChange = {
                "cmd": "GAME",
                "uuid": str(self.uuid),
                "msg": {"state": "InsertWord", "whisperedWords": [(self.my_ip, self.word_understood)], "resent": False}
            }

            self.state = "ProcessResult"

        elif not leader:
            self.whisperedWords = self.message["whisperedWords"]
            if debug: print(self.word_understood)
            self.word_understood = None
            while not self.word_understood:
                self.word_understood = input(f'PSSSSST 🤫 {self.whisperedWords[-1][0]} whispered the word "{self.tellWordToNeighbour(self.whisperedWords[-1][1])}". Please forward it quietly: ').lower()
            
            if self.state != "InsertWord": return
            
            self.whisperedWords.append((self.my_ip, self.word_understood))

            

            msgStateChange = {
                "cmd": "GAME",
                "uuid": str(self.uuid),
                "msg": {"state": "InsertWord", "whisperedWords": self.whisperedWords, "resent": False}
            }

            self.state = "WaitForResult"
        
        print("✅ Your neighbor", findRightNeighbor(self.my_ip)[0], "will be informed about your word.")
        TCPUnicastSender(self.uuid, findRightNeighbor(self.my_ip)[0], msgStateChange)

    def waitForWord(self):
        print("-"*30)
        print("Waiting for your neighbor to whisper a word ...")
        while self.state == "WaitForWord":

            if self.state == "InsertWord" and self.message['resent'] == True: # Your left neighbor crashed and was currently inserting a word. You need to do this now
                return # This if is actually not necessary. Serves only the clearness

            if leader: #Could be that a waiting peer becomes leader after old leader crashes. Then it needs to restart the game. (Cant distinguish whether the old leader submitted word already or not)
                self.state = "WaitForStart"
                return
            time.sleep(1)
            

    def waitForResult(self):
        print("-"*30)
        if not leader: print("Great job! Now wait for the leader to announce the result.")
        global peers

        while self.state == "WaitForResult":
            time.sleep(1)
            if self.state == "InsertWord" and self.message['resent'] == True: # Your left neighbor crahed but was obvously finished already. -> ignore it
                self.state == "WaitForResult"

            if leader: # The leader crashed and this peer is the new leader. It needs to switch to the result processing state
                print("The leader crashed. Now you have to take its role.")
                self.state = "ProcessResult"
                return
            
        try: # In  case the result broacast didn't arrive, we need skip the result reveal to avoid errors
            print('The game is over!')
            print("This is what happend: " + " -> ".join([word[1] for word in self.message["result"]])) # print the chain of whispered words
            print(f'The final word is "{self.message["result"][-1][1]}".')
            print(f'The real word was "{self.message["result"][0][1]}".')

            if self.message["result"][-1][1] == self.message["result"][0][1]:
                print("🏆 Congratulations! The team has won.")
                print("-"*30)
            else:
                print("❌ Oh no! The team has lost. But you have the chance to try again now.")
                print("-"*30)
        except KeyError:
            print("The Game started a new round.")
            print("-"*30)
            if len(peers) < players:
                self.state = "WaitForStart"
            return

        self.state = "WaitForStart"

    def processResult(self): # Only the leader should be able to come into this state
        print("-"*30)
        print("Now you have to wait until all players finished. Then you can reveal the result.")
        while self.state == "ProcessResult":
            time.sleep(1)

        if self.state == "WaitForStart":
            return
        if debug: print(self.message)

        msgStateChange = {
            "cmd": "GAME",
            "uuid": str(self.uuid),
            "msg": {"state": "WaitForStart", "result": self.message["whisperedWords"]}
        }

        self.message = msgStateChange["msg"]

        self.waitForResult()           

        BSender.broadcast(BSender.bcip, BSender.bcport, msgStateChange)

    def lostPlayer(self, crashedIP):
        if self.state == "WaitForResult" or self.state == "ProcessResult":
            if crashedIP == self.receivingIP:

                msgStateChange = {
                    "cmd": "GAME",
                    "uuid": str(self.uuid),
                    "msg": {"state": "InsertWord", "whisperedWords": self.whisperedWords, "resent": True}
                }        

                TCPUnicastSender(self.uuid, findRightNeighbor(self.my_ip)[0], msgStateChange)
    
    def tellWordToNeighbour(self, word_understood):
        prop = random.random()
        #print(prop)
        # find word in list
        line = self.findWordInWordList(word_understood)
        if line == None:
            return None
        index = line.index(word_understood)
        # go up/down/stay
        if prop < self.PROB_FOR_ONE_WORD_DOWN: # go one word up in word list
            return line[(index - 1) % len(line)] # use modulo to implement the list as ring
        elif prop >= self.PROB_FOR_ONE_WORD_DOWN and prop < self.PROB_FOR_SAME_WORD: # stay at same position in word list
            return line[index]
        else: # go one word up in word list
            return line[(index + 1) % len(line)] # use modulo to implement the list as ring
        # pass word to neighbour
        pass

    def findWordInWordList(self, word):
        try:
            with open('../../data/Rhymes.csv', mode ='r')as file:
                csvFile = csv.reader(file)
                lines_with_word = [] # Some words appear in more than one word list. Need to capture all of them
                for lines in csvFile:
                    if (lines.__contains__(word)):
                        lines_with_word.append(lines)
                #print(lines_with_word)
                try:
                    return random.choice(lines_with_word) # Select a random word list that contains the word
                except IndexError:
                    return None
        except:
            with open('./data/Rhymes.csv', mode ='r')as file:
                csvFile = csv.reader(file)
                lines_with_word = [] # Some words appear in more than one word list. Need to capture all of them
                for lines in csvFile:
                    if (lines.__contains__(word)):
                        lines_with_word.append(lines)
                #print(lines_with_word)
                try:
                    return random.choice(lines_with_word) # Select a random word list that contains the word
                except IndexError:
                    return None

if __name__ == '__main__':
    try:

        print("-"*30)
        players = 0
        while players < 3:
            players = input("👥 How many players should join the game? (Min. 3) ")
            try:
                players = int(players)
            except ValueError:
                players = 0

        game = Game(UUID, IP_ADDR)
        peers.append((IP_ADDR, str(UUID)))
        if debug: print(peers)

        if debug: print("Start TCP Unicast Listener")
        listener = TCPUnicastListener(59072, UUID) #TCP UnicastListener
        listener.start()

        BListener = BroadcastListener()
        BListener.start()

        heartbeat = HeartbeatListener(59071, UUID)
        heartbeat.start()

        time.sleep(0.5)

        BSender = BroadcastSender()

        time.sleep(2)

        heartbeatSender = HeartbeatSender()
        heartbeatSender.start()

        game.startGame()

    except KeyboardInterrupt:
        sys.exit(0)