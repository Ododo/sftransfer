import socket
import ssl
import miniupnpc

from classes import FileTransfer


DEFAULT_CHUNK_SIZE=1024
DEFAULT_PORT=6666
KEY_FILE = ""
CERT_FILE = ""

class TcpTransfer(FileTransfer):


    def __init__(self, port=DEFAULT_PORT, chunk_size=DEFAULT_CHUNK_SIZE):
        self._chunk_size=chunk_size
        self._port = port

    def getSocket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def serve_file(self, path):
        s = self.getSocket()
        s.bind(('', self._port))
        s.listen(1)

        while True:
            conn, addr = s.accept()
            try:
                with open(path, "rb") as f:
                    while True:
                        chunk = f.read(self._chunk_size)
                        if chunk:
                            conn.send(chunk)
                        else:
                            break
                    break

            finally:
                conn.close()


    def get_file(self, host, path):
        s = self.getSocket()
        s.connect(host)

        with open(path, "wb") as f:
            while True:
                data = s.recv(self._chunk_size)
                if data:
                    f.write(data)
                else:
                    break
            s.close()


class TcpWithUPnP(TcpTransfer):
    
    def serve_file(self, path):
        u = miniupnpc.UPnP()
        
        if u.discover():
            print("UPnP IGD service found at " + u.selectigd())
            print("Adding TCP port redirection...")
            u.addportmapping(self._port, 'TCP', u.lanaddr, self._port, 'FileTransfer', '')
        else:
            print("UPnP IGD service not found !")
            return
        try:
            super(__class__, self).serve_file(path)
        finally:
            print("Removing redirection ...")
            u.deleteportmapping(self._port, 'TCP')


class TLSTUP(TcpWithUPnP):
    
    def getSocket(self):
        sock = super().getSocket()
        sock = ssl.wrap_socket(sock, keyfile=KEY_FILE, certfile=CERT_FILE)
        
        return sock
            
            
