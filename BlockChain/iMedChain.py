import pickle
from datetime import datetime
from hashlib import sha512

import rsa

from BlockChain.MerkelTree import MerkelTree

BLOCK_TRANSACTION_LIMIT = 10
DIFFICULTY_CHECK_LIMIT = 5
PER_BLOCK_MINING_TIME = 60 * 2  # In Seconds


class IMedChain:
    def __init__(self):
        self.__difficulty = 2  # Initial Difficulty is set at 2
        self.__origin_wallet = Wallet()
        self.__genesis_transaction = Transaction("Genesis Initialization", self.__origin_wallet.get_public_key())
        self.__genesis_block = Block("0", self.__difficulty)
        self.__genesis_block.add_transaction(self.__genesis_transaction)
        print "Mining Genesis Block"
        self.__genesis_block.mine_block()
        self.__chain = []
        self.__chain.append(self.__genesis_block)
        print "Added Genesis Block to chain"
        self.unconfirmed_transaction_hashes = []

    def add_block(self, block):
        if self.__chain.__len__() % DIFFICULTY_CHECK_LIMIT == 0:
            total_time = 0
            for block in self.__chain[-1:-DIFFICULTY_CHECK_LIMIT]:
                total_time += block.get_mining_time()
            target = PER_BLOCK_MINING_TIME * DIFFICULTY_CHECK_LIMIT
            difference = target - total_time
            self.__difficulty = self.__difficulty + (difference / self.__difficulty)
        if block.calculate_block_hash() == block.get_hash() and block.get_hash()[:self.__difficulty] == \
                "0" * self.__difficulty and all(
            [True if transaction not in self.unconfirmed_transaction_hashes else False for transaction in
             block.get_merkel_tree().get_all_transactions()]):
            self.__chain.append(block)
            print "Block added to chain"
            return True
        else:
            print "Block Rejected"
            return False

    def get_latest_block(self):
        return self.__chain[-1]

    def get_block(self, index):
        try:
            return self.__chain[index]
        except Exception, e:
            print e.message

    def get_difficulty(self):
        return self.__difficulty

    def get_chain_string(self):
        return pickle.dumps(self.__chain)

    def store_chain(self):
        pickle.dump(self, "data/chain.pickle")
        print "Chain Stored at data/chain.pickle"

    @staticmethod
    def restore_chain():
        try:
            return pickle.load(open("data/chain.pickle"))
        except Exception, e:
            return False


class Block:
    def __init__(self, previous_hash, difficulty):
        self.__difficulty = difficulty
        self.__pre_mining_timestamp = None
        self.__post_mining_timestamp = None
        self.__timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.__previous_hash = previous_hash
        self.__merkel_tree = MerkelTree()
        self.__nonce = 0
        self.__hash = None
        self.__transaction_list = []

    def get_nonce(self):
        return self.__nonce

    def get_merkel_tree(self):
        return self.__merkel_tree

    def get_hash(self):
        return self.__hash

    def add_transaction(self, transaction):
        if self.__hash is not None:
            print "Block Already Mined and added to Chain. Cant be modified"
            return False
        if self.get_latest_transaction() is None:
            transaction.set_previous_transaction_hash("0")
        else:
            transaction.set_previous_transaction_hash(self.get_latest_transaction().get_hash())
        self.__merkel_tree.add_transaction(transaction)
        self.__transaction_list.append(transaction)
        if self.__merkel_tree.get_transaction_length() > BLOCK_TRANSACTION_LIMIT:
            self.__merkel_tree.build_tree()
            print("Block Full Initiating Merkel Tree Building and Block Mining")
            self.mine_block()

    def mine_block(self):
        print "Mining Block with difficulty " + str(self.__difficulty)
        self.__pre_mining_timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        while self.__hash is None:
            self.get_merkel_tree().build_tree()
            temp = self.calculate_block_hash()

            if temp.startswith("0" * self.__difficulty):
                self.__hash = temp
            else:
                self.__nonce += 1
        self.__post_mining_timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def get_mining_time(self):
        if self.__hash:
            pre = datetime.strptime(self.__pre_mining_timestamp, "%d/%m/%Y %H:%M:%S")
            post = datetime.strptime(self.__post_mining_timestamp, "%d/%m/%Y %H:%M:%S")
            return (post - pre).get_total_seconds()

    def get_latest_transaction(self):
        if self.__merkel_tree.get_transaction_length() > 0:
            return self.__merkel_tree.get_all_transactions()[-1]
        else:
            return None

    def calculate_block_hash(self):
        string = str(self.__previous_hash) + str(self.__timestamp) + str(
            self.get_merkel_tree().get_merkel_root().get_data()) + \
                 str(self.__nonce)
        return sha512(string).hexdigest()


class Transaction:
    CREATE = 0
    UPDATE = 1
    DELETE = 2

    def __init__(self, data, user_public_key):
        self.__timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.__user_public_key = user_public_key
        self.__previous_transaction_hash = None
        self.__input_transactions = []
        self.__output_transactions = []
        self.__encrypted_data = None
        self.__hash = None
        self.__type = None
        self.__source_transaction = None
        self.encrypt_data(data)

    def set_type(self, _type):
        self.__type = _type

    def get_type(self):
        return self.__type

    def set_previous_transaction_hash(self, _hash):
        self.__previous_transaction_hash = _hash

    def encrypt_data(self, data):
        string = data + "|" + self.__timestamp + "|" + "" if not self.__previous_transaction_hash else self.__previous_transaction_hash
        self.__encrypted_data = rsa.encrypt(string, pub_key=self.__user_public_key)
        string = data + self.__timestamp + "" if not self.__previous_transaction_hash else self.__previous_transaction_hash
        if self.__source_transaction:
            string += self.__source_transaction.get_hash()
        self.__hash = sha512(string).hexdigest()

    def get_hash(self):
        if self.__hash is None:
            try:

                self.encrypt_data()
            except Exception, e:
                return False
        return self.__hash

    def get_encrypted_data(self):
        return self.__encrypted_data

    def get_decrypted_data(self, private_key):
        try:
            string = rsa.decrypt(self.__encrypted_data, private_key)
            return string.split("|")[0]
        except rsa.DecryptionError, e:
            return "Decryption Error Key MisMatch"


class Wallet:
    __instances = []

    def __init__(self):

        self.__public_key, self.__private_key = rsa.newkeys(1024)
        Wallet.__instances.append(self)
        Wallet.store_wallet()

    @staticmethod
    def get_instances():
        return list(Wallet.__instances)

    @staticmethod
    def store_wallet():
        pickle.dump(Wallet.__instances, open("data/wallets.pickle", "w"))

    @staticmethod
    def restore_wallet():
        try:
            Wallet.__instances = pickle.load(open("data/wallets.pickle"))
            return True
        except Exception, e:
            print e.message
            return False

    @staticmethod
    def get_user_from_public_key(public_key):
        for wallet in Wallet.get_instances():
            if wallet.get_public_key() == public_key:
                return wallet
        return False

    def get_public_key(self):
        return self.__public_key

    def get_private_key(self):
        return self.__private_key

    def store_keys_as_file(self):
        pub = open("data/public_key.pem", "w")
        pub.write(self.__public_key.save_pkcs1("PEM"))
        private = open("data/private_key.pem", "w")
        private.write(self.__private_key.save_pkcs1("PEM"))
