import sys
import hashlib
import socket
import json

from queue import Queue
from collections import OrderedDict

from classes import RendezVous, Exchange

import tcp_transfer
from tcp_transfer import *


MAX_ITEM = 1000
MSG_SIZE = 512
MAX_TOKEN_LENGTH=20
SERVER_PORT = 5555


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

    def _process_message(self, data):
        try:
            data = json.loads(data)
            token = data["token"][:MAX_TOKEN_LENGTH]
            if data["method"].lower() == "put":
                self[token] = (data["ip"], data["port"])
            elif data["method"].lower() == "get":
                return self[token]
            return "Success"
        except json.JSONDecodeError:
            return "Bad data format"
        except KeyError:
            return "Invalid token or data incomplete"

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self._ip, self._port))
        s.listen()
        while True:
            conn, addr = s.accept()
            print("CONN")
            try:
                while True:
                    msg = conn.recv(MSG_SIZE)
                    if msg:
                        try:
                            result = self._process_message(msg)
                            if type(result) is tuple:
                                data = json.dumps({"ip" : result[0],
                                                   "port" : result[1]})
                            else:
                                data = json.dumps(({"msg" : result}))

                            conn.sendall(data.encode())
                        except:
                            pass
                        break
                    else:
                        break
            finally:
                conn.close()

class FifoClient(RendezVous):

    def initialization(self, server_ip, server_port):
        self._server_ip = server_ip
        self._server_port = server_port

    def register(self, host_ip, host_port):
        self.send("put", self._token, host_ip, host_port)

    def retreive(self):
        return self.send("get", self._token)

    def send(self, method, token, ip=None, port=None):
        msg = json.dumps({"method" : method,
                          "token": token,
                          "ip" : ip,
                          "port": port})

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._server_ip, self._server_port))
        while True:
            s.sendall(msg.encode())
            data = s.recv(MSG_SIZE)
            if data:
                return data
            else:
                break
        s.close()


if __name__ == "__main__":

    if len(sys.argv) == 2 and sys.argv[1] == "serve":
        print("Listening on port {}".format(SERVER_PORT))
        FifoServer("", SERVER_PORT).listen()

    if len(sys.argv) < 4:
        sys.exit(1)

    #token = hashlib.sha224(sys.argv[3].encode()).hexdigest()
    token = sys.argv[3]
    print("Token: " + token)

    rdv = FifoClient(token)
    transfer = TLSTUP()

    exch = Exchange(rdv, transfer)
    exch.initialization(server_ip="", server_port=SERVER_PORT)

    if sys.argv[1] == "send":
        exch.register(host_ip="", host_port=tcp_transfer.DEFAULT_PORT)
        print("Waiting for file to be pick up ...")
        exch.serve(sys.argv[2])
        print("Transfer completed.")

    elif sys.argv[1] == "get":
        result = json.loads(exch.retreive())
        if not "msg" in result:
            exch.get((result["ip"], result["port"]), sys.argv[2])
            print("Transfer completed.")
        else:
            print("Failed to get file: " + result["msg"])
