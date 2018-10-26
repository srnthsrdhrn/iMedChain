import string
import threading
from random import random

"""
------------------------------------------------------------------------------------------------------------------------
                                            Data Link Level Constants
------------------------------------------------------------------------------------------------------------------------
"""
# Types of Trackers
peers = []
# try:
#     peers = pickle.load("data/peers.pickle")
# except Exception, e:
#     peers = []
peer_mutex = threading.Lock()

# Pre Shared Key
PSK = "F624CD3B3CDCB026C89FAF545A09835D3914454C"
SELF = -1
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
CHAIN_SYNC = 5


def key_generator(size=128, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


PEER_ID = key_generator(size=64, chars=string.digits)
peer_data = {"address": None, "type": SELF, "ping": None, "key": None, "socket": None,
             "peer_id": PEER_ID}
peers.append(peer_data)
PEER_IDS = [PEER_ID]

"""
------------------------------------------------------------------------------------------------------------------------
                                            Network Level Constants
------------------------------------------------------------------------------------------------------------------------
"""
routing_mutex = threading.Lock()
ROUTING_TABLE = {}
DESTINATION = 'destination'
PING = 'ping'
FORWARD_TO = 'forward_to'
FORWARD_TO_PEER_ID = 'forward_to_peer_id'
SEQUENCE_NO='sequence'
# Header Flags
NODE_JOIN_REQUEST = 1
LSR_SYNC_PACKET = 0

LSR_SYNC_PACKET_SEQUENCE = 0
NODE_JOIN_REQUEST_SEQUENCE = 0
