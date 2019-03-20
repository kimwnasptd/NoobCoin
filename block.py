# import blockchain
import datetime
from Crypto.Hash import SHA256


class Block:
    def __init__(self, previousHash):

        self.previousHash = previousHash
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.listOfTransactions = []       # will be filled by add_transaction
        self.nonce = 0   # will be filled by mine_block when the  block is full
        self.hash = b"0"   # will be filled once the list of transactions is full

    def serialize(self):
        return{'previousHash': self.previousHash.decode(),
               'timestamp': self.timestamp,
               'listOfTransactions': [i.serialize() for i in self.listOfTransactions],
               'nonce': self.nonce,
               'hash': self.hash.decode()}

    def get_hash(self):
        """
        Calculates the hash of the block.
        It is called only after the list of transactions is filled,
        and right before the block starts getting mined.
        """
        dict = self.__dict__.copy()
        dict.pop("hash")
        dict.pop("nonce")
        class_str = str(list(dict.values())).encode()
        h = SHA256.new(class_str)
        res_hex = h.hexdigest()
        return(res_hex)

    def add_transaction(self, transaction):
        """
        Add a VALID transaction to the block.
        Returns the number of transactions on the block, after the addition,
        so that the node knows when to mine the block.
        """
        self.listOfTransactions.append(transaction)
        return(len(self.listOfTransactions))
