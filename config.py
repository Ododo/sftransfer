#config file for ftransfer
import os


#tcp filetransfer default values
TCP_CHUNK_SIZE=4096
TCP_PORT=6667

#RDV server default values
SERVER_KEY = os.urandom(16) #must be per instance generated
SERVER_PORT = 80
SERVER_IP = "193.54.15.207"
CERT_FILE="pems/cert.pem"
KEY_FILE="pems/key.pem"
MAX_ITEM = 1024
MSG_SIZE = 512
