#!/usr/bin/python

import sys
import os
import socket
import ssl
import json
import argparse
import base64

from classes import RendezVous, Exchange
from tcp_transfer import (
         TCP_FERNET, TCP_ACBC, TCP_AGCM, TCP_UPnP
)
from config import *


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
        context = ssl.create_default_context()
        context.check_hostname = False
        context.load_verify_locations(CERT_FILE)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s = context.wrap_socket(s)
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

    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=["get", "send"],
                        help="Can be either 'send' or 'get'")
    parser.add_argument("path", help="Path to write or read the file")
    parser.add_argument("password", help="""Password used to retreive your peer,
                       you must give a string and a number of your choice, e.g: password,1337""")
    parser.add_argument("-p", "--tcp-port", type=int, default=TCP_PORT,
                        help="Specify the port used for file transfer")
    parser.add_argument("-s", "--server-host",
                        help="Specify the RendezVous server address to use, format: ip:[port]")
    parser.add_argument("-u", "--use-upnp", action="store_true",
                        help="Use UPnP IGD to forward the tcp port to \
                        your machine, may not be allowed by all routers")
    parser.add_argument("-g", "--use-aes-gcm", action="store_true",
                        help="""
                        Use AES GCM instead of Fernet for data encryption,
                        use this option when you have to transfer large files.
                        """)
    parser.add_argument("-c", "--use-aes-cbc", action="store_true",
                        help="""
                        Use AES CBC instead of Fernet for data encryption,
                        can be used to transfer large files or for performance.
                        /!\ You will get no packet authentification, only
                        encryption /!\.
                        """)

    args = parser.parse_args()

    token = args.password
    rdv = FifoClient(token)

    if args.server_host:
        host = args.server_host.split(":")
        serv_ip = host[0]
        if len(host) == 2:
            serv_port = int(host[1])
        else:
            serv_port  = SERVER_PORT
    else:
        serv_ip, serv_port = SERVER_IP, SERVER_PORT

    bases = []
    if args.use_upnp:
        bases.append(TCP_UPnP)
    if args.use_aes_gcm:
        bases.append(TCP_AGCM)
    elif args.use_aes_cbc:
        bases.append(TCP_ACBC)
    else:
        bases.append(TCP_FERNET)

    transfer = type("Transfer", tuple(bases), {})(port=args.tcp_port)

    rdv.initialization(server_ip=serv_ip, server_port=serv_port)
    exch = Exchange(rdv, transfer)

    if args.task == "send":
        if not os.access(args.path, os.R_OK):
            print("File is not readable")
            sys.exit(1)
        res = exch.register(host_ip="", host_port=args.tcp_port)
        res = json.loads(res)
        try:
            transfer.initialization(res["msg"])
        except:
            print("You must give a password in the format string,integer")
            sys.exit(1)
        print("Waiting for file to be pick up ...")
        exch.serve(args.path)
        print("Transfer completed.")

    elif args.task == "get":
        if not os.access(os.path.split(args.path)[0], os.W_OK):
            print("File is not writable")
            sys.exit(1)
        result = json.loads(exch.retreive())
        if not "msg" in result:
            transfer.initialization(result["key"])
            exch.get((result["ip"], result["port"]), args.path)
            print("Transfer completed.")
        else:
            print("Failed to get file: " + result["msg"])
