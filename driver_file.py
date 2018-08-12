import json

from iMedChain import *

# Creating New Chain
chain = IMedChain()
# Genesis Block is generated automatically and mined, hence we are getting its hash to link it to the next block
prev_hash = chain.get_latest_block().get_hash()
# New Block is created
block = Block(prev_hash, chain.get_difficulty())
# New Users are created to simulate transactions
user1 = Wallet()
user2 = Wallet()
# Data Generated
data = json.dumps({"data": "I am testing blockchain"})
# Getting latest transaction hash from the merkel tree of genesis block
prev_trx_hash = chain.get_latest_block().get_merkel_tree().get_all_transactions()[-1].get_data()
# Generating new transaction
trx = Transaction(data, user1.get_public_key())
# Adding the transaction to the block
block.add_transaction(trx)
