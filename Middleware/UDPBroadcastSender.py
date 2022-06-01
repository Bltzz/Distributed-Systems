import socket
import ipaddress

# No Threading needed (for now)
# Only Used to send a message at a specific point in time. No listening all the time. 
class UDPBroadcastSender:
    def __init__(self, subnetmask, broadcastPort):
        self.subnetmask = subnetmask
        self.hostname = socket.gethostname()
        self.ip_address = socket.gethostbyname(self.hostname)
        self.broadcastIp = self.getBroadcastIP(self.ip_address, self.subnetmask)
        self.boradcastPort = broadcastPort
        
    def broadcast(self, broadcast_message):
        # Create a UDP socket
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Send message on broadcast address
        broadcast_socket.sendto(str.encode(broadcast_message), (self.broadcastIp, self.boradcastPort))
        broadcast_socket.close()

    def getBroadcastIP(self, IP, SUBNETMASK):
        networkaddress = ipaddress.IPv4Network(IP + '/' + SUBNETMASK, False)
        return networkaddress.broadcast_address.exploded



##
## testing:
##
if __name__ == '__main__':
    

    SUBNETMASK = "255.255.255.0"
    
    # Broadcast address and port
    BROADCAST_PORT = 59073

    sender = UDPBroadcastSender(SUBNETMASK, BROADCAST_PORT)

    # Local host information
    
    print(sender.broadcastIp)

    # Send broadcast message
    #message = sender.ip_address + ' sent a broadcast'
    message = "End"
    sender.broadcast(message)
    print("Sent")

