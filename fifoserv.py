#!/usr/bin/python

import sys
import socket
import ssl
import json
import base64
import os
import argparse

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from queue import Queue
from collections import OrderedDict

from config import *


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

    def _generateKey(self, token, length=48, iterations=100000, salt=None):
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=length,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(token.encode()))
        return key

    def _generateHashmapKey(self, token, integer):
        return self._generateKey(token, length=16,
                                 iterations=integer,
                                 salt=SERVER_KEY)

    def _process_message(self, data):
        try:
            data = json.loads(data)
            token, integer = data["token"].split(",")
            token = self._generateHashmapKey(token, int(integer)).decode()
            if data["method"].lower() == "post":
                key = self._generateKey(token).decode()
                self[token] = (data["ip"], data["port"], data["algo"], key)
                return key
            elif data["method"].lower() == "get":
                return self[token]
        except KeyError:
            return "Invalid token or data incomplete"
        except Exception as e:
            return "Bad data format"

    def listen(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(keyfile=KEY_FILE, certfile=CERT_FILE)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self._ip, self._port))
        s.listen(3)
        while True:
            conn, addr = s.accept()
            try:
                conn = context.wrap_socket(conn, server_side=True)
                while True:
                    msg = conn.recv(MSG_SIZE)
                    if msg:
                        try:
                            result = self._process_message(msg)
                            if type(result) is tuple:
                                ip = result[0] if result[0] \
                                               else conn.getpeername()[0]
                                data = {
                                    "ip" : ip,
                                    "port" : result[1],
                                    "algo" : result[2],
                                    "key" : result[3]
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
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("bind_addr", nargs='?',
                        help="Specify address to listen on, ip:[port]")

    args = parser.parse_args()

    if args.bind_addr:
        host = args.bind_addr.split(":")
        ip = host[0]
        if len(host) == 2:
            port = host[1]
        else:
            port = SERVER_PORT
    else:
        ip = "localhost"
        port = SERVER_PORT

    print("Listening on {}:{}".format(ip, port))
    FifoServer(ip, int(port)).listen()
