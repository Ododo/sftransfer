import sys
import hashlib
from time import sleep

import btdht

from classes import Exchange, RendezVous
from tcp_transfer import TcpTransfer


class BtRdv(RendezVous):

    def initialization(self):
        self._dht = btdht.DHT()
        self._dht.start()
        sleep(16)

    def register(self, port):
        print("Sending a get_peers query to enable token")
        self._dht.get_peers(self._token)
        print("Announcing the host to the network ...")
        self._dht.announce_peer(self._token, port)
        print("Waiting for the file to be picked up ...")

    def retreive(self):
        peers = self._dht.get_peers(self._token)
        if peers is not None and len(peers) > 0:
            return peers[0]
        else:
            print("Failed to retreive host")


if __name__ == "__main__":

    if len(sys.argv) < 4:
        sys.exit(1)

    token = hashlib.md5(sys.argv[3].encode()).hexdigest()
    print("Token: " + token)


    rdv = BtRdv(token)
    transfer = TcpTransfer()

    exch = Exchange(rdv, transfer)
    exch.initialization()

    if sys.argv[1] == "send":
        exch.register(port=exch.port)
        exch.serve(sys.argv[2])

    elif sys.argv[1] == "get":
        host = exch.retreive()
        if host:
            exch.get(("127.0.0.1",6666), sys.argv[2])
            print("Done !")
        else:
            print("Failed to get file")
