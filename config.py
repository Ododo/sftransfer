#config file for ftransfer
import os


#tcp filetransfer
TCP_CHUNK_SIZE=4096
TCP_PORT=6667

#relay
SERVER_KEY = os.urandom(16)
SERVER_PORT = 7888
SERVER_IP = ""
CERT_FILE=""
KEY_FILE=""
MAX_ITEM = 1024
MSG_SIZE = 512
