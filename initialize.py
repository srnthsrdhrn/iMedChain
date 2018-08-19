import pickle
import sys

from iMedChain import Block, IMedChain, Wallet, Transaction
from p2p import start

chain = None
block = None


def add_transaction(transaction):
    global chain
    global block
    if not block:
        block = Block(chain.get_latest_block().get_hash(), chain.get_difficulty())
    block.add_transaction(transaction)
    if block.get_hash():
        if chain.add_block(block):
            block = None
        else:
            pass


def start_chain():
    global chain
    try:
        chain = pickle.load(open("data/chain.pickle"))
        print "Restored Chain "
        Wallet.restore_wallet()
        print "Restored Wallet"
    except Exception, e:
        print e.message
        chain = IMedChain()
        print "Created chain"
    return chain


def stop_chain():
    global chain
    try:
        pickle.dump(chain, open("data/chain.pickle", "w"))
        print "Chain Saved"
        return True
    except Exception, e:
        print e.message
        return False


def get_block_string(index=0):
    _block = chain.get_block(index)
    if _block:
        return pickle.dumps(_block)


def get_wallets_string():
    return pickle.dumps(instances)


if sys.argv.__len__() > 0:
    global chain
    code = sys.argv[0]
    address = sys.argv[1]
    chain = start_chain()
    instances = Wallet.get_instances()
    if instances.__len__() > 0:
        user1 = instances[-1]
        trx = Transaction("Hello World", user1.get_public_key())
        for _ in range(0, 11):
            add_transaction(trx)
