import sys
import socket
import ssl
import json


from classes import RendezVous, Exchange
import tcp_transfer
from tcp_transfer import TcpWithFernet
from fifoserv import MSG_SIZE


class FifoClient(RendezVous):

    def initialization(self, server_ip, server_port):
        self._server_ip = server_ip
        self._server_port = server_port

    def register(self, host_ip, host_port):
        return self._send("put", self._token, host_ip, host_port)

    def retreive(self):
        return self._send("get", self._token)

    def _send(self, method, token, ip=None, port=None):
        msg = json.dumps({"method" : method,
                          "token": token,
                          "ip" : ip,
                          "port": port
                          })

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = ssl.wrap_socket(s)
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

    if len(sys.argv) < 4:
        sys.exit(1)

    #token = hashlib.sha224(sys.argv[3].encode()).hexdigest()
    token = sys.argv[3]
    print("Token: " + token)

    rdv = FifoClient(token)
    transfer = TcpWithFernet()

    rdv.initialization(server_ip="", server_port=8021)

    exch = Exchange(rdv, transfer)

    if sys.argv[1] == "send":
        res = exch.register(host_ip="", host_port=tcp_transfer.DEFAULT_PORT)
        res = json.loads(res)
        transfer.initialization(res["msg"])
        print("Waiting for file to be pick up ...")
        exch.serve(sys.argv[2])
        print("Transfer completed.")

    elif sys.argv[1] == "get":
        result = json.loads(exch.retreive())
        if not "msg" in result:
            transfer.initialization(result["key"])
            exch.get((result["ip"], result["port"]), sys.argv[2])
            print("Transfer completed.")
        else:
            print("Failed to get file: " + result["msg"])
