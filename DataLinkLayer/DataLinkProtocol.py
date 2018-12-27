import json
import socket
import sys

from hotqueue import HotQueue

from BlockChain.Aes_Cypher import AESCipher
from Utilities.Functions import get_peer, disconnect_peer, format_peers
from Utilities.Variables import *

DataLinkQueue = HotQueue(DATA_LINK_QUEUE_NAME, host=REDIS_HOSTNAME, port=REDIS_PORT)
RoutingTableQueue = HotQueue(ROUTING_TABLE_QUEUE_NAME, host=REDIS_HOSTNAME, port=REDIS_PORT)


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


def sync_peers(new_peers, address, peer_type, key):
    flag = False
    if not peer_mutex.locked():
        peer_mutex.acquire()
        flag = True
    for peer1 in new_peers:
        if peer1['type'] == -1:
            if get_peer(address) is None:
                peer1['address'] = address
                peer1['socket'] = None
                peer1['type'] = peer_type
                peer1['key'] = key
                peers.append(peer1)
                PEER_IDS.append(peer1['peer_id'])
                RoutingTableQueue.put([COMPUTE_ROUTING_TABLE, 0])
        if peer1['peer_id'] not in PEER_IDS:
            Client(peer1["address"])
            peers.append(peer1)
            PEER_IDS.append(peer1['peer_id'])
            RoutingTableQueue.put([COMPUTE_ROUTING_TABLE, 0])
    if flag:
        peer_mutex.release()


def msg_received(msocket, address, payload):
    if not payload:
        disconnect_peer(address)
    else:
        payload = payload.split("|")
        try:
            if int(payload[0]) == CLIENT_REGISTRATION:
                # Server
                key = key_generator()
                peer_type = payload[1]
                data = payload[2]
                data = json.loads(data)
                sync_peers(data, address, peer_type, key)
                msocket.send(format_return_data(RETURN_SYNC, format_peers(), key))
            elif int(payload[0]) == RETURN_SYNC:
                # Client
                data = payload[1]
                data = json.loads(data)
                key = payload[2]
                sync_peers(data, address, TYPE, key)
                # msocket.close()
                # disconnect_peer(address)
                return False
        except Exception, e:
            print e.message
            print payload
            peer = get_peer(address)
            payload = decipher(peer, payload[0]).split("|")
            if int(payload[0]) == DATA:
                data = [peer['peer_id'], address, payload[1]]
                DataLinkQueue.put(data)
            elif int(payload[0]) == CHAIN_SYNC:
                print "Chain Sync Not Yet Implemented"


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
                is_socket_closed = callback(msocket, a, payload)
                payload = ""
                if is_socket_closed:
                    print "Disconnected from {}".format(a)
                    break
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception, e:
            print e.message
            pass


class Server:
    global peers

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", 10000))
        self.sock.listen(5)
        while True:
            c, a = self.sock.accept()
            cThread = threading.Thread(target=handler, args=(c, a[0], msg_received))
            cThread.daemon = True
            cThread.start()
            # print "Connected to {}.".format(a[0])


class Client:
    global peers

    def __init__(self, address, port=10000, lsr_flooding=False):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.connect((address, port))

        # print "Connected to Server {}".format(address)
        if lsr_flooding:
            flag = False
            if not peer_mutex.locked():
                flag = True
                peer_mutex.acquire()
            peer = get_peer(address=address)
            peer['socket'] = self.sock
            DataLinkQueue.put([peer['peer_id'], address, str(LSR_INIT) + "%"])
            if flag:
                peer_mutex.release()
        else:
            self.sock.send(format_return_data(CLIENT_REGISTRATION, TYPE, format_peers()))
        iThread = threading.Thread(target=handler, args=(self.sock, address, msg_received))
        iThread.daemon = True
        iThread.start()
        # print "Connected to {}.".format(address)


def start_server(arg):
    server = Server()


def start(code=0, address=None, port=10000):
    global TYPE
    code = int(code)
    TYPE = code
    if code != TRACKER:
        client = Client(address, port)
    cThread = threading.Thread(target=start_server, args=(1,))
    cThread.daemon = True
    cThread.start()
    # if code != TRACKER:
    #     Client(address)
    # else:
    #     Server()


#
def send_message(message, peer_id=None, address=None, lsr_flooding=False):
    peer = get_peer(peer_id=peer_id, address=address)
    if peer:
        print(peer)
        client = Client(peer['address'], lsr_flooding=lsr_flooding)
        client.sock.send(format_return_data(DATA, message, key=peer['key']))
        client.sock.close()
        return True
