import sys
import socket
import ssl
import json
import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from queue import Queue
from collections import OrderedDict


MAX_ITEM = 1000
MSG_SIZE = 512
MAX_TOKEN_LENGTH=20
DEFAULT_PORT = 5555
CERT_FILE=""
KEY_FILE=""


class FifoServer(Queue):

    class Item:
        def __init__(self, token, host):
            self.token = token
            self.host = host

    def __init__(self, ip, port, maxsize=MAX_ITEM):
        Queue.__init__(self, maxsize)
        self._ip = ip
        self._port = port

    def _init(self, maxsize):
        self.queue = OrderedDict()

    def _put(self, item):
        self.queue[item.token] = item.host

    def _get(self):
        return self.queue.popitem(last=False)

    def __contains__(self, token):
        with self.mutex:
            return token in self.queue

    def __getitem__(self, token):
        return self.queue.pop(token)

    def __setitem__(self, token, host):
        if self.full():
            self.get(block=False)
        self.put(FifoServer.Item(token, host), block=False)

    def _getKey(self, token):
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(token.encode()))
        return key

    def _process_message(self, data):
        try:
            data = json.loads(data)
            token = data["token"][:MAX_TOKEN_LENGTH]
            if data["method"].lower() == "put":
                key = self._getKey(token).decode()
                self[token] = (data["ip"], data["port"], key)
                return key
            elif data["method"].lower() == "get":
                return self[token]
        except json.JSONDecodeError:
            return "Bad data format"
        except KeyError:
            return "Invalid token or data incomplete"

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = ssl.wrap_socket(s, keyfile=KEY_FILE, certfile=CERT_FILE)
        s.bind((self._ip, self._port))
        s.listen()
        while True:
            conn, addr = s.accept()
            try:
                while True:
                    msg = conn.recv(MSG_SIZE)
                    if msg:
                        try:
                            result = self._process_message(msg)
                            if type(result) is tuple:
                                data = {
                                    "ip" : result[0],
                                    "port" : result[1],
                                    "key" : result[2]
                                }
                            else:
                                data = { "msg" : result }
                            data = json.dumps(data).encode()
                            conn.sendall(data)
                        except Exception as e:
                            print(e)
                        break
                    else:
                        break
            finally:
                conn.close()



if __name__ == "__main__":

    if len(sys.argv) == 2:
        arg = sys.argv[1].split(":")
        ip = arg[0]
        if len(arg) == 2:
            port = arg[1]
        else:
            port = DEFAULT_PORT
        print("Listening on {}:{}".format(ip, port))
        FifoServer(ip, int(port)).listen()
