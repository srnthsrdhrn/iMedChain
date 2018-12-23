# Link State Routing
import pickle
import time

from hotqueue import HotQueue

from DataLinkLayer.DataLinkProtocol import send_message
from Utilities.Functions import get_ping, get_peer
from Utilities.Variables import *

DataLinkQueue = HotQueue(DATA_LINK_QUEUE_NAME, host=REDIS_HOSTNAME, port=REDIS_PORT)
RoutingTableQueue = HotQueue(ROUTING_TABLE_QUEUE_NAME, host=REDIS_HOSTNAME, port=REDIS_PORT)
routing_table = None


def get_from_routing_table(peer_id):
    try:
        route = ROUTING_TABLE[peer_id]
    except IndexError, e:
        return None
    return route


def compute_routing_table():
    global routing_table
    route_flag = False
    peer_flag = False
    if not routing_mutex.locked():
        routing_mutex.acquire()
        route_flag = True
    if not peer_mutex.locked():
        peer_mutex.acquire()
        peer_flag = True
    peer_ids = peers
    if peer_flag:
        peer_mutex.release()
    try:
        for peer in peer_ids:
            if peer['peer_id'] != PEER_ID:
                if ROUTING_TABLE.get(peer['peer_id'], None) is None:
                    ping = get_ping(peer['address'])
                    data = {PING: ping, FORWARD_TO_PEER_ID: None, LSR_SEQUENCE_NO: 0}
                    ROUTING_TABLE[peer['peer_id']] = data
        routing_table = ROUTING_TABLE
    except Exception, e:
        if route_flag:
            routing_mutex.release()
        print "Compute Routing Table Error: " + e.message
        return False
    if route_flag:
        routing_mutex.release()
    return True


def update_routing_table_from_peer(peer_routing_table, source_peer_id, sequence_no):
    flag = False
    if not routing_mutex.locked():
        routing_mutex.acquire()
        flag = True
    msequence = ROUTING_TABLE.items()[0][1][LSR_SEQUENCE_NO]
    if msequence > sequence_no:
        print "Old Sequence. Packet Dropped"
        if flag:
            routing_mutex.release()
        return
    for mpeer_id, mrow in peer_routing_table.iteritems():
        if mpeer_id != PEER_ID:
            try:
                row = ROUTING_TABLE[mpeer_id]
                source_row = ROUTING_TABLE[source_peer_id]
                if source_row[PING] + mrow[PING] < row[PING]:
                    row[PING] = source_row[PING] + mrow[PING]
                    row[FORWARD_TO_PEER_ID] = source_peer_id
                    row[LSR_SEQUENCE_NO] = sequence_no
            except KeyError, e:
                print "Peer Doesnt Exist"
    print "Routing Table updated"
    if flag:
        routing_mutex.release()
    return


def format_return_data(*args, **kwargs):
    delimiter = kwargs.pop("delimiter", "%")
    data = str(args[0])
    for arg in args[1:]:
        data += delimiter + str(arg)
    return data


@DataLinkQueue.worker
def process_network_layer_messages(queue_data):
    global routing_table
    source_peer_id, address, message = queue_data
    flag, data = message.split("%")
    flag = int(flag)
    # peer = get_peer(address=address)
    if flag == LSR_SYNC_PACKET:
        sequence, data = data.split("!")
        peer_routing_table = pickle.loads(data)
        update_routing_table_from_peer(peer_routing_table, source_peer_id, sequence)
        # peer['socket'].close()
        # peer['socket'] = None
        # disconnect_peer(address=peer['address'])


def lsr_packet_flood(args):
    while True:
        global routing_table
        compute_routing_table()
        if len(routing_table) == 0:
            print "Waiting for Peer Connect"
            time.sleep(10)
            continue
        sequence_no = routing_table.items()[0][1][LSR_SEQUENCE_NO] + 1
        print "LSR Sync Initiated for Sequence {}".format(sequence_no)
        for peer_id, row in routing_table.iteritems():
            peer = get_peer(peer_id=peer_id)
            print(peer)
            if peer['type'] == -1:
                continue
            flag = False
            if not routing_mutex.locked():
                routing_mutex.acquire()
                flag = True

            routing_table_string = pickle.dumps(routing_table)
            sync_packet = format_return_data(sequence_no, routing_table_string, delimiter="!")
            send_message(format_return_data(LSR_SYNC_PACKET, sync_packet), peer_id=peer['peer_id'],lsr_flooding=True)
            if flag:
                routing_mutex.release()
        time.sleep(10)


def start_lsr_packet_flood():
    cThread = threading.Thread(target=lsr_packet_flood, args=(1,))
    cThread.daemon = True
    cThread.start()


@RoutingTableQueue.worker
def add_to_routing_table(queue_data):
    flag, queue_data = queue_data
    if flag == ROUTING_TABLE_ENTRY:
        peer_id, ping, forward_to_peer_id, lsr_sequence = queue_data
        data = {PING: ping, FORWARD_TO_PEER_ID: forward_to_peer_id, LSR_SEQUENCE_NO: lsr_sequence}
        flag = False
        if not routing_mutex.locked():
            routing_mutex.acquire()
            flag = True
            ROUTING_TABLE[peer_id] = data
        if flag:
            routing_mutex.release()
    if flag == COMPUTE_ROUTING_TABLE:
        compute_routing_table()
    return True


def connect_neighbours():
    flag = False
    if not routing_mutex.locked():
        routing_mutex.acquire()

    if flag:
        routing_mutex.release()


def start_network_workers():
    iThread = threading.Thread(target=process_network_layer_messages, args=())
    iThread.daemon = True
    iThread.start()
    iThread = threading.Thread(target=add_to_routing_table, args=())
    iThread.daemon = True
    iThread.start()
