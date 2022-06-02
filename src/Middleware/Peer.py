##
## @author bltzz
##
## This class holds the logic for the peer
## 
##
import sys
import os
import json
import uuid
#append the src dir to the sys path, to allow importing other classes.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import TCPUnicastSender, TCPUnicastListener, UDPBroadcastListener, UDPBroadcastSender

BROADCAST_PORT = 59073
UNICAST_PORT = 59072
SUBNETMASK = "255.255.255.0"
# Lives in Main Thread
class Peer:
    def __init__(self):
        ## set vars
        self.UUID = uuid.uuid4()
        print("My UUID is: ", str(self.UUID))
        self.unicastSender = TCPUnicastSender.TCPUnicastSender(UNICAST_PORT, self.UUID)
        self.unicastListener = TCPUnicastListener.TCPUnicastListener(UNICAST_PORT, self.UUID)
        self.broadcastSender = UDPBroadcastSender.UDPBroadcastSender(BROADCAST_PORT, SUBNETMASK, self.UUID)
        self.broadcastListener = UDPBroadcastListener.UDPBroadcastListener(BROADCAST_PORT, SUBNETMASK, self.UUID)
        ## start broadcast listener
        self.broadcastListener.start()
        ## start unicast listener
        self.unicastListener.start()

        #self.initialBroadcast()
        self.broadcastSender.broadcast("End")
        ## broadcast
        ## based on responses: Get List of members, set neighbors
        ## Call for voting
        tmp = 1

    def initialBroadcast(self):
        message = {
            "uuid" : str(self.UUID),
            "ip" : self.broadcastSender.ip_address,
            "msg" : "INIT"
        }
        msg_json = json.dumps(message)

        self.broadcastSender.broadcast(msg_json)



##
## testing:
##
if __name__ == '__main__':
    peer = Peer()