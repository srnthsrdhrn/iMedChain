import json
import random
import socket
import string
import sys
import threading

from Aes_Cypher import AESCipher

peers = []

# Pre Shared Key
PSK = "F624CD3B3CDCB026C89FAF545A09835D3914454C"

# Types of Trackers
TRACKER = 0
MINER = 1
NODE = 2
FULL_NODE = 3
DJANGO_SERVER = 4
TYPE = TRACKER
TERMINATOR = "\n28375"
# Request Header Code Types
CLIENT_REGISTRATION = 0
IP_SYNC_1 = 1
IP_SYNC_2 = 2
KEY_SYNC = 3
DATA = 4


def format_return_data(*args, **kwargs):
    data = str(args[0])
    for arg in args[1:]:
        data += "|" + str(arg)
    data += TERMINATOR
    key = kwargs.get("key")
    if key:
        cipher = AESCipher(key)
        data = cipher.encrypt(data)
    return data


def decipher(peer, raw):
    key = peer["key"]
    cipher = AESCipher(key)
    data = cipher.decrypt(raw)
    return data


def format_peers():
    data = []
    for peer in peers:
        temp = {"address": peer['address'], "type": peer['type']}
        data.append(temp)
    return json.dumps(data)


def get_peer(address):
    for peer in peers:
        if peer['address'] == address:
            return peer


def disconnect_peer(address):
    for peer in peers:
        if peer['address'] == address:
            peers.remove(peer)
            return True
    return False


def key_generator(size=128, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def msg_received(msocket, address, payload):
    global peers
    peer = get_peer(address)
    if not payload:
        print "Disconnected from {}".format(peer['address'])
        peers.remove(peer)
    else:
        payload = payload.split("|")
        try:
            code = int(payload[0])
            if int(payload[0]) == CLIENT_REGISTRATION:
                peer_type = payload[1]
                peer_data = {"address": address, "type": peer_type, "ping": None, "key": None, "socket": msocket}
                peers.append(peer_data)
                print "Client Registered. Return Sync Sent"
                data = format_return_data(IP_SYNC_1, format_peers())
                msocket.send(data)
            elif int(payload[0]) == IP_SYNC_1:
                print "IP sync 1 Received"
                data = payload[1]
                data = json.loads(data)
                for peer1 in data:
                    flag = False
                    for peer in peers:
                        if peer1["address"] == peer["address"]:
                            flag = True
                            break
                    if not flag:
                        # print "New Peer Received. Connect Request Sent"
                        # Client(peer1["address"])
                        peers.append(peer1)
                msocket.send(format_return_data(IP_SYNC_2, format_peers()))
            elif int(payload[0]) == IP_SYNC_2:
                print "IP SYNC 2 received"
                key = key_generator()
                peer['key'] = key
                msocket.send(format_return_data(KEY_SYNC, key))
            elif int(payload[0]) == KEY_SYNC:
                print "Received Key Sync"
                key = payload[1]
                peer['key'] = key
                msocket.send(format_return_data(DATA, "Hello World", key=key))
        except Exception,e:
            payload = decipher(peer, payload[0]).split("|")
            if int(payload[0]) == DATA:
                print payload[1]


def handler(msocket, a, callback):
    payload = ""
    while True:
        try:
            data = msocket.recv(2048)
            payload += data
            if not data:
                print "Disconnected from {}".format(a)
                disconnect_peer(a)
                break
            if data:
                payload = payload[:-TERMINATOR.__len__()]
                callback(msocket, a, payload)
                payload = ""

        except KeyboardInterrupt:
            sys.exit(0)
        except Exception,e:
            print e.message
            pass


class Server:
    global peers

    def __init__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", 10000))
        sock.listen(5)
        while True:
            c, a = sock.accept()
            cThread = threading.Thread(target=handler, args=(c, a[0], msg_received))
            cThread.daemon = True
            cThread.start()
            print "Connected to {}.".format(a[0])


class Client:
    global peers

    def __init__(self, address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((address, 10000))
        print "Connected to Server {}".format(address)
        peers.append({"address": address, "socket": socket, "type": TRACKER, "key": None})
        sock.send(format_return_data(CLIENT_REGISTRATION, TYPE))
        iThread = threading.Thread(target=handler, args=(sock, address, msg_received))
        iThread.daemon = True
        iThread.start()


if (len(sys.argv)) > 1:
    code = int(sys.argv[1])
    TYPE = code
    if code != TRACKER:
        Client(sys.argv[2])
    Server()
else:
    print "Missing Arguments, Program Exiting ..."
