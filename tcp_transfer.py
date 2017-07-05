import socket
import base64
import os

import miniupnpc

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

from classes import FileTransfer
from config import *


class TcpTransfer(FileTransfer):

    def __init__(self, port=TCP_PORT, chunk_size=TCP_CHUNK_SIZE):
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
                            conn.send(self._process_out_data(None))
                            break
                    break

            finally:
                conn.close()

    def get_file(self, host, path):
        s = self._getSocket()
        s.connect(host)

        with open(path, "wb") as f:
            cnt = 0
            while True:
                chunk = s.recv(self._chunk_size)
                if chunk:
                    f.write(self._process_in_data(chunk))
                else:
                    f.write(self._process_in_data(None))
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
        self._cipher = Fernet(key[:32].encode())
        print(self._cipher)

    def _process_in_data(self, chunk):
        return self._cipher.decrypt(chunk)

    def _process_out_data(self, chunk):
        return self._cipher.encrypt(chunk)

class TcpWithAES(TcpTransfer):

    def initialization(self, key):
        key = base64.urlsafe_b64decode(key)
        k = key[:32]
        iv = key[32:]
        cipher = Cipher(algorithms.AES(k), modes.CBC(iv),
                        backend=default_backend())
        self._decryptor = cipher.decryptor()
        self._encryptor = cipher.encryptor()
        self._padder = padding.PKCS7(algorithms.AES.block_size).padder()
        self._unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

    def _process_in_data(self, chunk):
        if chunk is None:
            return self._unpadder.update(self._decryptor.finalize()) + \
                   self._unpadder.finalize()
        chunk = self._decryptor.update(chunk)
        return self._unpadder.update(chunk)

    def _process_out_data(self, chunk):
        if chunk is None:
            return self._encryptor.update(self._padder.finalize()) + \
                   self._encryptor.finalize()
        chunk = self._padder.update(chunk)
        return self._encryptor.update(chunk)


class TcpWithUPnPWithFernet(TcpWithFernet, TcpWithUPnP):
    pass

class TcpWithUPnPWithAES(TcpWithAES, TcpWithUPnP):
    pass

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
