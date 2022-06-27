import socket
import threading
import uuid

class TCPUnicastListener(threading.Thread):

    def __init__(self, listeningPort, uuid):
        threading.Thread.__init__(self)
        self.UUID = uuid
        self.listeningPort = listeningPort
        self.host = socket.gethostname()
        self.ip_addr = socket.gethostbyname(self.host)
        print('TCP Unicast at server %s listening on port %s' %(self.ip_addr, self.listeningPort))

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.ip_addr, self.listeningPort))
        s.listen()
        conn, addr = s.accept()
        cond = True
        while cond:
            data = conn.recv(1024)
            if not data:
                break
            print(data.decode())
            conn.sendall(str.encode("Thanks"))
            
        conn.close()        


if __name__ == '__main__':
    print("Start TCP Unicast Listener")
    listener = TCPUnicastListener(59072, uuid.uuid4())
    listener.start()
    listener.join()
    print("End TCP Unicast Listener")
