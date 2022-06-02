from email import message
import socket

class TCPUnicastSender:

    def __init__(self, sendPort):
        self.hostname = socket.gethostname()
        self.ip_address = socket.gethostbyname(self.hostname)
        self.sendPort = sendPort

    def sendMessage(self, recipientIP, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((recipientIP, self.sendPort))
        s.sendall(message.encode())
        data = s.recv(1024)
        s.close()
        print ('Received', repr(data))



##
## testing:
##
if __name__ == '__main__':
    sender = TCPUnicastSender(50001)
    sender.sendMessage("192.168.178.104", "Hi wassup")
