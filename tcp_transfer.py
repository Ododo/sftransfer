import socket
import miniupnpc

from cryptography.fernet import Fernet

from classes import FileTransfer


DEFAULT_CHUNK_SIZE=1024
DEFAULT_PORT=6666


class TcpTransfer(FileTransfer):


    def __init__(self, port=DEFAULT_PORT, chunk_size=DEFAULT_CHUNK_SIZE):
        self._chunk_size=chunk_size
        self._port = port

    def _getSocket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _process_in_data(self, chunk):
        return chunk

    def _process_out_data(self, chunk):
        return chunk

    def serve_file(self, path):
        s = self._getSocket()
        s.bind(('', self._port))
        s.listen(1)

        while True:
            conn, addr = s.accept()
            try:
                with open(path, "rb") as f:
                    while True:
                        chunk = f.read(self._chunk_size)
                        if chunk:
                            conn.send(self._process_out_data(chunk))
                        else:
                            break
                    break

            finally:
                conn.close()


    def get_file(self, host, path):
        s = self._getSocket()
        s.connect(host)

        with open(path, "wb") as f:
            while True:
                chunk = s.recv(self._chunk_size)
                if chunk:
                    f.write(self._process_in_data(chunk))
                else:
                    break
            s.close()


class TcpWithUPnP(TcpTransfer):

    def serve_file(self, path):
        u = miniupnpc.UPnP()

        if u.discover():
            print("UPnP IGD service found at " + u.selectigd())
            print("Adding TCP port redirection...")
            u.addportmapping(self._port, 'TCP', u.lanaddr,
                             self._port, 'FileTransfer', '')
        else:
            print("UPnP IGD service not found !")
            return
        try:
            super(__class__, self).serve_file(path)
        finally:
            print("Removing redirection ...")
            u.deleteportmapping(self._port, 'TCP')


class TcpWithFernet(TcpTransfer):

    def initialization(self, key):
        self._cipher = Fernet(key.encode())

    def _process_in_data(self, chunk):
        return self._cipher.decrypt(chunk)

    def _process_out_data(self, chunk):
        return self._cipher.encrypt(chunk)


# class TLSTUP(TcpWithUPnP):
#     import ssl
#     def initialization(self, certfile, keyfile=None):
#         self._keyfile = keyfile
#         self._certfile = certfile
#
#     def getSocket(self):
#         sock = super().getSocket()
#         sock = ssl.wrap_socket(sock, keyfile=self._keyfile,
#                                      certfile=self._certfile)
#
#         return sock
