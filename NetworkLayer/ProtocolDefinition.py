# Link State Routing
import pickle

from ping import Ping

from Variables.variables import *


def get_from_routing_table(peer_id):
    try:
        route = ROUTING_TABLE[peer_id]
    except IndexError, e:
        return None
    return route


def initialize_routing_table():
    routing_mutex.acquire()
    peer_mutex.acquire()
    peer_ids = PEER_IDS
    peer_mutex.release()
    try:
        for peer in peer_ids:
            if peer['peer_id'] != PEER_ID:
                p = Ping(destination=peer['address'])
                sum = 0
                for _ in range(0, 10):
                    sum += p.do()
                mean = sum / 10.0
                data = {DESTINATION: peer['address'], PING: mean, FORWARD_TO: None,
                        FORWARD_TO_PEER_ID: None, SEQUENCE_NO: 0}
                ROUTING_TABLE[peer['peer_id']] = data
    except Exception:
        routing_mutex.release()
        return False
    routing_mutex.release()
    return True


def update_routing_table(routing_table, source_peer_id, sequence_no):
    routing_mutex.acquire()
    for mpeer_id, mrow in routing_table.iteritems():
        if mpeer_id != PEER_ID:
            try:
                row = ROUTING_TABLE[mpeer_id]
                source_row = ROUTING_TABLE[source_peer_id]
                if source_row[PING] + mrow[PING] < row[PING]:
                    row[PING] = source_row[PING] + mrow[PING]
                    row[FORWARD_TO] = source_row[DESTINATION]
                    row[FORWARD_TO_PEER_ID] = source_peer_id
                    row[SEQUENCE_NO] = sequence_no
            except KeyError, e:
                print "Peer Doesnt Exist"
                pass
    print "Routing Table updated"
    routing_mutex.release()
    return


def process_network_layer_messages(source_peer_id, address, message):
    flag, sequence, data = message.split("%")
    flag = int(flag)
    if flag == LSR_SYNC_PACKET:
        routing_table = pickle.loads(data)
        update_routing_table(routing_table, source_peer_id, sequence)


def lsr_packet_flood():
    routing_mutex.acquire()
    routing_table = ROUTING_TABLE
    routing_mutex.release()

