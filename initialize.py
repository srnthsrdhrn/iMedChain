import pickle

from BlockChain.iMedChain import Block, IMedChain, Wallet

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
            print "Mining Block Failed"


def start_chain():
    global chain
    chain = IMedChain.restore_chain()
    if chain:
        print "Restored Chain"
    else:
        chain = IMedChain()
        print "Created Chain"
    if Wallet.restore_wallet():
        print "Restored Wallet"
    else:
        Wallet()
        print "Created Wallet"
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


chain = start_chain()
instances = Wallet.get_instances()
# if sys.argv.__len__() > 0:
#     code = sys.argv[0]
#     address = sys.argv[1]
# if instances.__len__() > 0:
#     user1 = instances[-1]
#     trx = Transaction("Hello World", user1.get_public_key())
#     for _ in range(0, 11):
#         add_transaction(trx)
