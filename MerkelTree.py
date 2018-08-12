from _sha512 import sha512


class MerkelTree:
    def __init__(self):
        self.__merkel_root = None
        self.__leaf_transaction_hashes = []

    def get_merkel_root(self):
        return self.__merkel_root

    def __construct_merkel_tree(self, transactions):
        onward_transactions = []
        temp = None
        flag = True
        if transactions.__len__() == 1:
            self.__merkel_root = transactions[0]
            return
        if not transactions.__len__() % 2 == 0:
            transactions.append(transactions[-1])
        for transaction in transactions:
            if flag:
                temp = transaction
                flag = False
            else:
                flag = True
                string = temp.data + transaction.data
                data = sha512(string).hexdigest()
                node = MerkelNode(data)
                node.__left_child = temp
                node.__right_child = transaction
                onward_transactions.append(node)
        self.__construct_merkel_tree(onward_transactions)

    def get_all_transactions(self):
        return self.__leaf_transaction_hashes

    def add_transaction(self, _hash):
        self.__leaf_transaction_hashes.append(MerkelNode(_hash))

    def build_tree(self):
        if self.__leaf_transaction_hashes.__len__() == 0:
            print("Merkel Tree doesnt any transactions")
            return None
        else:
            self.__construct_merkel_tree(self.__leaf_transaction_hashes)
            return True

    def get_transaction_length(self):
        return self.__leaf_transaction_hashes.__len__()


class MerkelNode:
    def __init__(self, data):
        self.__data = data
        self.__left_child = None
        self.__right_child = None

    def get_data(self):
        return self.__data

    def get_left_child(self):
        return self.__left_child

    def get_right_child(self):
        return self.__right_child
