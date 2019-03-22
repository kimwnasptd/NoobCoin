# import blockchain
import datetime
from Crypto.Hash import SHA256
from utils import create_logger
from transaction import Transaction

logger = create_logger(__name__)


class Block:
    def __init__(self, *args, **kwargs):
        '''
        previousHash: STRING ACTUALLY
        timestamp: string
        listOfTransactions: [Transaction]
        nonce: int
        hash: STRING ACTUALLY
        '''

        if kwargs.get('timestamp', None) is not None:
            logger.info("BLOCK creation through json object")
            # self.previousHash = (kwargs['previousHash']).encode()
            self.previousHash = (kwargs['previousHash'])
            # Got a JSON Object
            self.timestamp = kwargs['timestamp']
            ts = kwargs['listOfTransactions']
            self.listOfTransactions = [Transaction(**t) for t in ts]
            self.nonce = kwargs['nonce']
            # self.hash = (kwargs['hash']).encode()
            self.hash = (kwargs['hash'])
            logger.info('BLOCK CONSTRUCTOR UP HASH TYPE: ' + str(type(self.hash)))
        else:
            self.previousHash = kwargs['previousHash']
            self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.listOfTransactions = []       # will be filled by add_transaction
            self.nonce = 0   # will be filled by mine_block when the  block is full
            self.hash = (b"0").decode()  # will be filled once the list of transactions is full
            logger.info('BLOCK CONSTRUCTOR DOWN HASH TYPE: ' + str(type(self.hash)))

    def serialize(self):
        logger.info('BLOCK SERIALIZE PREV HASH TYPE : ' + str(type(self.previousHash)))
        logger.info('BLOCK SERIALIZE PREV FUCKING HASH : ' + str((self.previousHash)))
        logger.info('BLOCK SERIALIZE timestamp TYPE : ' + str(type(self.timestamp)))
        logger.info('BLOCK SERIALIZE nonce TYPE : ' + str(type(self.nonce)))
        logger.info('BLOCK SERIALIZE HASH TYPE : ' + str(type(self.hash)))
        return {
            'previousHash': self.previousHash,
            'timestamp': self.timestamp,
            'listOfTransactions': [i.serialize() for i in self.listOfTransactions],
            'nonce': self.nonce,
            'hash': self.hash  # [int(b) for b in self.hash],
        }

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
        logger.info('BLOCK HASH TYPE INSIDE GET HASH: ' + str(type(res_hex)))
        return(res_hex)

    def add_transaction(self, transaction):
        """
        Add a VALID transaction to the block.
        Returns the number of transactions on the block, after the addition,
        so that the node knows when to mine the block.
        """
        self.listOfTransactions.append(transaction)
        return(len(self.listOfTransactions))

    def validate_hash(self):
        """
        Follows the same procedure as the get_hash function and ensures that
        the given hash is correct.
        """
        hash = self.hash
        dict = self.__dict__.copy()
        dict.pop("hash")
        dict.pop("nonce")
        class_str = str(list(dict.values())).encode()
        h = SHA256.new(class_str)
        res_hex = h.hexdigest()
        return(res_hex == hash)
