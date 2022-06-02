import socket
import uuid

class TCPUnicastSender:

    def __init__(self, sendPort, uuid):
        self.UUID = uuid
        self.hostname = socket.gethostname()
        self.ip_address = socket.gethostbyname(self.hostname)
        self.sendPort = sendPort

    def sendMessage(self, recipientIP, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((recipientIP, self.sendPort))
        s.sendall(str.encode(message))
        data = s.recv(1024)
        s.close()
        print ('TCP Received', repr(data))



##
## testing:
##
if __name__ == '__main__':
    sender = TCPUnicastSender(59072, uuid.uuid4())
    sender.sendMessage("192.168.178.71", "Hi wassup")
