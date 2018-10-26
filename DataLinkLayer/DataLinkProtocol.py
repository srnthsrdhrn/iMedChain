import json
import socket
import sys

from BlockChain.Aes_Cypher import AESCipher
from NetworkLayer.ProtocolDefinition import process_network_layer_messages
from Variables.variables import *


def format_return_data(*args, **kwargs):
    data = str(args[0])
    for arg in args[1:]:
        data += "|" + str(arg)
    key = kwargs.get("key")
    if key:
        cipher = AESCipher(key)
        data = cipher.encrypt(data)
    data += TERMINATOR
    return data


def decipher(peer, raw):
    key = peer["key"]
    cipher = AESCipher(key)
    data = cipher.decrypt(raw)
    return data


def format_peers():
    data = []
    for peer in peers:
        temp = {"address": peer['address'], "type": peer['type'], "peer_id": peer['peer_id']}
        data.append(temp)
    return json.dumps(data)


def get_peer(address):
    for peer in peers:
        if peer['address'] == address:
            return peer


def disconnect_peer(address):
    for peer in peers:
        if peer['address'] == address:
            peer_mutex.acquire()
            PEER_IDS.remove(peer['peer_id'])
            peers.remove(peer)
            peer_mutex.release()
            return True
    return False


def msg_received(msocket, address, payload):
    global peers
    peer = get_peer(address)
    # print "\n\n" + str(address) + "\n\n" + str(payload) + "\n\n"
    if not payload:
        disconnect_peer(address)
    else:
        payload = payload.split("|")
        try:
            if int(payload[0]) == CLIENT_REGISTRATION:
                peer_type = payload[1]
                peer_id = payload[2]
                peer_mutex.acquire()
                if peer_id not in PEER_IDS:
                    peer_data = {"address": address, "type": peer_type, "ping": None, "key": None, "socket": msocket,
                                 "peer_id": peer_id}
                    peers.append(peer_data)
                    PEER_IDS.append(peer_id)
                    # print "Client Registered. Return Sync Sent"
                    data = format_return_data(IP_SYNC_1, format_peers())
                    msocket.send(data)
                peer_mutex.release()
            elif int(payload[0]) == IP_SYNC_1:
                # print "IP sync 1 Received"
                data = payload[1]
                data = json.loads(data)
                peer_mutex.acquire()
                for peer1 in data:
                    if peer1['address'] is None and peer1['peer_id'] not in PEER_IDS:
                        peer1['address'] = address
                        peer1['socket'] = msocket
                        peers.append(peer1)
                        PEER_IDS.append(peer1['peer_id'])
                        continue
                    if peer1['peer_id'] not in PEER_IDS:
                        Client(peer1["address"])
                        peers.append(peer1)
                        PEER_IDS.append(peer1['peer_id'])
                msocket.send(format_return_data(IP_SYNC_2, format_peers()))
                peer_mutex.release()
            elif int(payload[0]) == IP_SYNC_2:
                # print "IP SYNC 2 received"
                key = key_generator()
                peer['key'] = key
                msocket.send(format_return_data(KEY_SYNC, key))
                # print "Connected to Client {}".format(address)
                # pickle.dump(peer, "data/peers.pickle")
            elif int(payload[0]) == KEY_SYNC:
                # print "Received Key Sync"
                key = payload[1]
                peer['key'] = key
                # print "Connected to Server {}".format(address)
                # pickle.dump(peer, "data/peers.pickle")
        except Exception, e:
            payload = decipher(peer, payload[0]).split("|")
            if int(payload[0]) == DATA:
                process_network_layer_messages(payload[1], peer['peer_id'])
            elif int(payload[0]) == CHAIN_SYNC:
                pass


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
            if data.endswith(TERMINATOR):
                payload = payload[:-TERMINATOR.__len__()]
                callback(msocket, a, payload)
                payload = ""

        except KeyboardInterrupt:
            sys.exit(0)
        except Exception, e:
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
            # print "Connected to {}.".format(a[0])


class Client:
    global peers

    def __init__(self, address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.connect((address, 10000))
        # print "Connected to Server {}".format(address)
        sock.send(format_return_data(CLIENT_REGISTRATION, TYPE, PEER_ID))
        iThread = threading.Thread(target=handler, args=(sock, address, msg_received))
        iThread.daemon = True
        iThread.start()


def start_server(arg):
    Server()


def start(code=0, address=None):
    global TYPE
    code = int(code)
    TYPE = code
    if code != TRACKER:
        Client(address)
    cThread = threading.Thread(target=start_server, args=(1,))
    cThread.daemon = True
    cThread.start()
    # if code != TRACKER:
    #     Client(address)
    # else:
    #     Server()


def send_message(peer_id, message):
    peer_mutex.acquire()
    if peer_id not in PEER_IDS:
        print "Peer id doesnt exist"
        peer_mutex.release()
        return
    for peer in peers:
        if peer['peer_id'] == peer_id:
            peer['socket'].send(format_return_data(DATA, message, key=peer['key']))
            print "Data Sent"
            peer_mutex.release()
            return True
    peer_mutex.release()
