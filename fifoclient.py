import sys
import socket
import json


from classes import RendezVous, Exchange
from tcp_transfer import TLSTUP


class FifoClient(RendezVous):

    def initialization(self, server_ip, server_port):
        self._server_ip = server_ip
        self._server_port = server_port

    def register(self, host_ip, host_port):
        self._send("put", self._token, host_ip, host_port)

    def retreive(self):
        return self._send("get", self._token)

    def _send(self, method, token, ip=None, port=None):
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
