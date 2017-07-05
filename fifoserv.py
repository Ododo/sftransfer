import sys
import hashlib
import socket
import json

from queue import Queue
from collections import OrderedDict


MAX_ITEM = 1000
MSG_SIZE = 512
MAX_TOKEN_LENGTH=20
DEFAULT_PORT = 5555


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
