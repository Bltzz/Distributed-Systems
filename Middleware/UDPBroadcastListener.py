
import socket
import threading

class UDPBroadcastListener(threading.Thread):
    def __init__(self, broadcastPort):
        threading.Thread.__init__(self)
        self.broadcastPort = broadcastPort
        self.host = socket.gethostname()
        self.ip_addr = socket.gethostbyname(self.host)

    def run(self):
        print("Start run")
        # Create a UDP socket
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the socket to broadcast and enable reusing addresses
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        listen_socket.bind((self.ip_addr, self.broadcastPort))
        print("Listening to broadcast messages")

        cond = True
        while cond:
            data, addr = listen_socket.recvfrom(1024)
            if data:
                ## TODO: Based on Message: Do something
                print("Received broadcast message:", data.decode())
                if data.decode() == "End":
                    print("In End")
                    cond = False
        print("Ending Thread")


##
## testing:
##
if __name__ == '__main__':
    # Listening port
    BROADCAST_PORT = 59073

    listener = UDPBroadcastListener(BROADCAST_PORT)
    listener.start()