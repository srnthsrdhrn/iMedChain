from DataLinkLayer.DataLinkProtocol import start
from NetworkLayer.NetworkLayerProtocol import *


start_network_workers()
start_lsr_packet_flood()
machine_code = int(os.environ.get("MACHINE_CODE", 1))
if machine_code == 1:
    start()
else:
    start(1, 'imedchain_machine1_1')
