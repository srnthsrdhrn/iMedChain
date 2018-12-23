import json

from ping import Ping

from Variables import *


def format_peers():
    data = []
    flag = False
    if not peer_mutex.locked():
        peer_mutex.acquire()
        flag = True
    for peer in peers:
        # if peer['type'] == -1:
        #     continue
        temp = {"address": peer['address'], "type": peer['type'], "peer_id": peer['peer_id']}
        data.append(temp)
    if flag:
        peer_mutex.release()
    return json.dumps(data)


def get_peer(address=None, peer_id=None):
    flag = False
    if not peer_mutex.locked():
        peer_mutex.acquire()
        flag = True
    mpeers = peers
    if flag:
        peer_mutex.release()
    for peer in mpeers:
        if address:
            if peer['address'] == address:
                return peer
        if peer_id:
            if peer['peer_id'] == peer_id:
                return peer
    # print "Failed to get Peer {}".format(address)


def disconnect_peer(address):
    # peer = get_peer(address=address)
    # if peer:
    #     flag = False
    #     if not peer_mutex.locked():
    #         peer_mutex.acquire()
    #         flag = True
    #     PEER_IDS.remove(peer['peer_id'])
    #     peers.remove(peer)
    #     if flag:
    #         peer_mutex.release()
    #     return True
    # return False
    return True


def get_ping(address):
    p = Ping(destination=address)
    sum = 0
    for _ in range(0, 10):
        sum += p.do()
    mean = sum / 10.0
    return mean
