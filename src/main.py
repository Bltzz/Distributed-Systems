import socket
from threading import Thread
import time
import sys
import uuid
from json import loads, dumps
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

# sort the list of peers according to IPs
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

# Listening for broadcast messages in seperate thread
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
                newUDPThread = UDPBroadcastHandler(data)
                newUDPThread.start()
                if debug: print("Broadcast received: ", decodeMessage(data))

    def stop(self):
        self.running = False

# Handle udp messages in a seperate thread to reduce workload of th broadcastlistener
class UDPBroadcastHandler(Thread):

    def __init__(self, msg):
        Thread.__init__(self)
        self.msg = msg
    
    def run(self):
        MessageInterpreter(self.msg)

# Send a broadcast message
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

# The broadcast sender which starts dynamic dicovery on initialization and is able to send other broadcasts later
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

# Class that is able to send unicasts to a specified sender
class TCPUnicastSender():

    def __init__(self, UUID, recipientIP, msg):
        self.uport = 59072
        self.recipientIP = recipientIP
        self.hostname = socket.gethostname()
        self.ip_address = IP_ADDR
        self.msg = msg
        #if debug: print("SEND TCP Message: ", self.msg, self.recipientIP)
        self.sendMessage(self.recipientIP, self.uport, self.msg)

    def sendMessage(self, recipientIP, uport, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect_ex((recipientIP, uport))
        s.sendall(encodeMessage(message))
        data = s.recv(1024)
        s.close()
        if debug: print('TCP Received: ', repr(data))

# The interpreter class which is called by the unicast and broadcast handlers and knows the actions behind the defined message types
class MessageInterpreter():
    def __init__(self, data):
        self.msg = decodeMessage(data)
        self.command = self.msg['cmd']
        self.content = self.msg['msg'] # Often it is an ip address, except the command is "GAME"
        self.id = self.msg['uuid']
        self.my_ip_addr = IP_ADDR
        self.my_id = UUID
        global leaderIpAndUUID
        global peers
        global leader
        global BSender
        global game

        # Message that tells that a new peer wants to join (dynamic discovery)
        if(self.command == 'INIT'):

            # This way a new peer also identifies itself in the network. An acknowledgement is not needed int his case
            if(self.content  == self.my_ip_addr ):

                time.sleep(0.5)

                # The new joiner always starts a new voting round
                vote = Voting()
                vote.startVote()

            # Send an acknowledgement if a new unkown peer wants to join
            else:
                peers.append((self.content, self.id))
                res = {
                    "cmd": "INIT_RESPONSE",
                    "uuid": str(self.my_id),
                    "msg": self.my_ip_addr
                }
                TCPUnicastSender(self.my_id, self.content, res)
            if debug: print("Peers: ", peers)

        # Add peers that are responding on the inital broadcast
        if(self.command == 'INIT_RESPONSE'):
            self.addPeerToList(self.content, self.id)
        
        # React to an incoming voting message
        if(self.command == 'VOTING'):
            voting_instance = Voting()
            voting_instance.respondWithLCRAlgorithmToVote(self.msg)
            pass
        
        # Information about a lost peer (message sent by leader)
        if(self.command == 'LOST_PEER'):
            if debug: print("The leader informed that one peer is lost")

            # This message could come multiple times, but the lost peer needs to be removed only once
            try:
                peers.remove((self.content, self.id))
                if debug: print("Removed the lost peer from the list")
            except ValueError: # Peer was already removed -> do nothing
                if debug: print("Faild to remove the lost peer from the list. Probably happend already before!")
                pass
            
            # If the game is already running, the peer must check if it has still enough players and maybe reset to the waiting state
            if game.running and len(peers) < players:
                if debug: print("Too less peers: STOP GAME!!!")
                game.changeState({"state": "ResetWaitForStart"})
                pass
            
            # Needed as maybe the peer need to resend its whispered word
            if game.running: 
                game.lostPlayer(self.content)

        # Only the leader can receive this kind of message from apeer that detected a lost neighbor
        # Then the leader has to inform all other peers via broadcast
        if(self.command == 'LOST_NEIGHBOR'):
            
            if debug: print("One of the peers informed that it lost a neighbor -> broadcast this information to the ring")
            msgLostPeer = {
                "cmd": "LOST_PEER",
                "uuid": self.id,
                "msg": self.content
            }

            BSender.broadcast(BSender.bcip, BSender.bcport, msgLostPeer)
        
        # Messages with ths flag are related to the gamelogic and change the game state of the peer
        if(self.command == 'GAME'):
            if debug: print("Received this state changing message:", self.content)
            game.changeState(self.content)
            pass

    # Remove peers from the list of peers
    def removePeerFromList(self, ip_addr, id):
        peers.remove((ip_addr, id))
    
    # Add peers to the list of peers
    def addPeerToList(self, ip_addr, id):
        peers.append((ip_addr, id))
        if debug: print("Peers: ", peers)

# A Listener for TCP messages
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

# Handling the content of the tcp messages in a seperated thread to keep the listener free for other messages
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

# Listener for Heartbeat TCP messages (Fault Tolerance)
class HeartbeatListener(Thread):
    def __init__(self, heartbeat_port, UUID):
        Thread.__init__(self)
        self.heartbeat_port = heartbeat_port
        self.host = socket.gethostname()
        self.ip_addr = IP_ADDR
        self.UUID = UUID

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

            # Acknowledgement to let the hearbeat sender know, that the peer is still alive
            msg = {
                "cmd":"AWAKE",
                "uuid": str(self.UUID),
                "msg": self.ip_addr
            }
            conn.sendall(encodeMessage(msg))
            MessageInterpreter(data)

        conn.close()

# Sending heartbeat messages and waiting for a response -> counting the missing responses and informing the leader about missed peers
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

        self.msg = {
            "cmd": "HEARTBEAT",
            "uuid": str(self.UUID),
            "msg": self.ip_address
        }

    # Send heartbeats in a loop of 1 second
    def run(self):
        while self.running:
            self.sendMessage(findRightNeighbor(self.ip_address), self.uport, self.msg, "right") #Need to search neighbor each time again in case the peers list changed
            time.sleep(0.5)
            self.sendMessage(findLeftNeighbor(self.ip_address), self.uport, self.msg, "left") #Need to search neighbor each time again in case the peers list changed
            time.sleep(0.5)
        pass
       
    # Send the messages and detect failures
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

        # Open the handling of missed neighbors
        if self.counterLeft > 3 :
            if debug: print("Left neighbor lost: ", neighbor)
            self.sendLostPeerMessage(neighbor)
            self.counterLeft = 0
            pass
        if self.counterRight > 3 :
            if debug: print("Right neighbor lost: ", neighbor)
            self.sendLostPeerMessage(neighbor)
            self.counterRight = 0
        pass

    # Handling lost peers
    def sendLostPeerMessage(self, neighbor):
        global leaderIpAndUUID
        global leader
        global BSender

        # Leader got lost. --> Detecting peer takes temporary leader role, broadcasts the lost leader and starts new leader voting
        if neighbor[0] == leaderIpAndUUID[0]:
            
            if debug: print("The leader is lost. This peer will be the temprary leader.")
            
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

        # The detecting peer informs the leader about the lost peer
        else:
            
            if debug: print("Inform the leader that one neighbor is lost")
            msgLostNeighbor = {
                        "cmd": "LOST_NEIGHBOR",
                        "uuid": neighbor[1],
                        "msg": neighbor[0]
                    }

            TCPUnicastSender(self.UUID, leaderIpAndUUID[0], msgLostNeighbor)

# Initalize and start a voting round
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
    
    # Send the own UUID into the ring
    def startVote(self):

        msg =  {
            "cmd": "VOTING",
            "uuid": self.UUID,
            "msg": self.ip_address,
            "leaderElected": False
        }
        TCPUnicastSender(self.UUID, self.leftNeighbor[0], msg)
        pass

    # The LCR Voting algorithm
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
    
    # Funtion to compare two UUIDs
    def isOwnUuidIsHigher(self, UUID, receivedUUID):
        return (int(uuid.UUID(UUID)) > int(uuid.UUID(receivedUUID)))

# Class implementing the Game chinese whisperes
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

    # The game works with states that each peer holds
    def startGame(self):
        print("-"*30)

        # Wait until all peers started
        while (len(peers) < players):
            time.sleep(0.5)
            print(f'🔴 Identified {len(peers)}/{players} players: {", ".join([peer[0] for peer in peers])}', end="\r")
            pass

        # Loop through the states and choose an active one
        while self.running:
            if self.state == "WaitForStart": self.waitForStart()
            elif self.state == "InsertWord": self.insertWord()
            elif self.state == "WaitForWord": self.waitForWord()
            elif self.state == "WaitForResult": self.waitForResult()
            elif self.state == "ProcessResult": self.processResult()
            elif self.state == "ResetWaitForStart": self.state = "WaitForStart"
            else: pass
            time.sleep(.1)

    # Funtion to update the game state (called on message arrival)
    def changeState(self, msg):
        if debug and self.state is not None: print("Changed state from " + self.state)

        self.message = msg
        self.state = self.message['state']

        if debug: print("Changed state to " + self.state)
        pass
    
    # Funtion to wait until the game starts (different behaviour of peers and leader)
    def waitForStart(self):
        if debug: print("I entered waitForStart")
        global BSender
        global leader
        global peers
        
        # If a peer did crash meanwhile, wee neeed to wait until we reach the wanted number of players
        while (len(peers) < players):
            time.sleep(0.5)
            print(f'🔴 Identified {len(peers)}/{players} players: {", ".join([peer[0] for peer in peers])}', end="\r")
            pass
        
        print(f'✅ Identified {len(peers)}/{len(peers)} players: {", ".join([peer[0] for peer in peers])}')
        # The neighbor who will receive your input
        self.receivingIP = findRightNeighbor(self.my_ip)[0]

        # The leader cans tart the gameand send the initial word into the ring
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
            while not start and self.state == "WaitForStart":
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
        
        # Normal peers just have to wait. If the leader crashed, were elected as new leader, they need to switch into the starting class
        elif not leader:
            print("Wait until the leader starts the game ...")
            while self.state == "WaitForStart":
                if leader: # Could be that the leader crashes and a waiting peer receives the leader role in the meantime
                    return
                time.sleep(1)

    # State to whisper a word to the neighbor
    def insertWord(self):
        print("-"*30)
        global leader
        
        # Leader has to choose an initial word
        if leader:
            self.word_understood = None
            while leader and not self.word_understood:
                self.word_understood = input("📣 You are the leader. Please choose a word from the csv file and write it down: ").lower()
            
            # Avoid some failers after a peer crashed
            if not leader:
                CURSOR_UP_ONE = '\x1b[1A' 
                ERASE_LINE = '\x1b[2K' 
                sys.stdout.write(CURSOR_UP_ONE) 
                sys.stdout.write(ERASE_LINE) 
                return
            
            # State could have changed due to a crashed peer
            if self.state != "InsertWord": return
            if debug: print("My Current state: ", self.state)

            msgStateChange = {
                "cmd": "GAME",
                "uuid": str(self.uuid),
                "msg": {"state": "InsertWord", "whisperedWords": [(self.my_ip, self.word_understood)], "resent": False}
            }

            # Switch to the waiting state until all peers finished
            self.state = "ProcessResult"

        # Normal peers se a potentialy moified version of the original word and need to forward it
        elif not leader:
            self.whisperedWords = self.message["whisperedWords"]
            if debug: print(self.word_understood)
            self.word_understood = None
            while not self.word_understood:
                self.word_understood = input(f'PSSSSST 🤫 {self.whisperedWords[-1][0]} whispered the word "{self.tellWordToNeighbour(self.whisperedWords[-1][1])}". Please forward it quietly: ').lower()
            
            # State could have changed due to a crashed peer
            if self.state != "InsertWord": return
            
            # append the new word into the game history and send it to the next neighbor
            self.whisperedWords.append((self.my_ip, self.word_understood))

            msgStateChange = {
                "cmd": "GAME",
                "uuid": str(self.uuid),
                "msg": {"state": "InsertWord", "whisperedWords": self.whisperedWords, "resent": False}
            }

            # Wait until the leader announces the result
            self.state = "WaitForResult"
        
        print("✅ Your neighbor", findRightNeighbor(self.my_ip)[0], "will be informed about your word.")
        TCPUnicastSender(self.uuid, findRightNeighbor(self.my_ip)[0], msgStateChange)

    # Peers are waiting in the que until they are allowed to insert a word
    def waitForWord(self):
        print("-"*30)
        print("Waiting for your neighbor to whisper a word ...")
        while self.state == "WaitForWord":

            # State could have changed due to a crashed peer
            if self.state == "InsertWord" and self.message['resent'] == True: # Your left neighbor crashed and was currently inserting a word. You need to do this now
                return # This if is actually not necessary. Serves only the clearness

            # Leader role could have changed as the leader could have crashed
            if leader: #Could be that a waiting peer becomes leader after old leader crashes. Then it needs to restart the game. (Cant distinguish whether the old leader submitted word already or not)
                self.state = "WaitForStart"
                return
            time.sleep(1)
            
    # State to wait until the result is announced
    def waitForResult(self):
        print("-"*30)
        if not leader: print("Great job! Now wait for the leader to announce the result.")
        global peers

        # Loop until the announcement
        while self.state == "WaitForResult":
            time.sleep(1)

            # State could have changed due to a crashed peer
            if self.state == "InsertWord" and self.message['resent'] == True: # Your left neighbor crahed but was obvously finished already. -> ignore it
                self.state == "WaitForResult"

            # Leader role could have changed as the leader could have crashed
            if leader: # The leader crashed and this peer is the new leader. It needs to switch to the result processing state
                print("The leader crashed. Now you have to take its role.")
                self.state = "ProcessResult"
                return
            
        try: # In  case the result broacast didn't arrive, we need skip to the result announcment to avoid errors
            print('The game is over!')
            print("This is what happend: " + " -> ".join([word[1] for word in self.message["result"]])) # print the chain of whispered words
            print(f'The final word is "{self.message["result"][-1][1]}".')
            print(f'The real word was "{self.message["result"][0][1]}".')

            if self.message["result"][-1][1] == self.message["result"][0][1]:
                print("🏆 Congratulations! The team has won.")
                print("-"*30)
                print("Wait till new round starts")
            else:
                print("❌ Oh no! The team has lost. But you have the chance to try again now.")
                print("-"*30)
                print("Wait till new round starts")
        except KeyError:
            print("The Game started a new round.")
            print("-"*30)
            if len(peers) < players:
                self.state = "WaitForStart"
            return

        # Switch to the state to start again
        self.state = "WaitForStart"

    # State to await the last peer and announce the result via broadcast
    def processResult(self): # Only the leader should be able to come into this state
        print("-"*30)
        print("Now you have to wait until all players finished. Then you can reveal the result.")
        while self.state == "ProcessResult":
            time.sleep(1)

        # State could have changed due to a crashed peer
        if self.state == "WaitForStart": return
        if debug: print(self.message)

        msgStateChange = {
            "cmd": "GAME",
            "uuid": str(self.uuid),
            "msg": {"state": "WaitForStart", "result": self.message["whisperedWords"]}
        }

        self.message = msgStateChange["msg"]

        # Reveal the result to itself before sending the broadcast
        self.waitForResult()           

        BSender.broadcast(BSender.bcip, BSender.bcport, msgStateChange)
    
    # Function to handle a lost peer in the game, as a peer maybe needs to resend its message
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
            with open('../data/Rhymes.csv', mode ='r')as file:
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
            with open('../data/Rhymes.csv', mode ='r')as file:
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

# Main thread to initialize the message listeners, start the dicsovery and the game afterwards
if __name__ == '__main__':
    try:

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

        print("-"*30)
        players = 0
        while players < 3:
            players = input("👥 How many players should join the game? (Min. 3) ")
            try:
                players = int(players)
            except ValueError:
                players = 0

        BSender = BroadcastSender()

        time.sleep(2)

        heartbeatSender = HeartbeatSender()
        heartbeatSender.start()

        game.startGame()

    except KeyboardInterrupt:
        sys.exit(0)