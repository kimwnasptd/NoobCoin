from Crypto.Random.random import getrandbits
from utils import create_logger

logger = create_logger(__name__)


class TransactionInput:
    def __init__(self, *args, **kwargs):
        '''
        previousOutputId: string
        amount: int
        '''
        self.previousOutputId = kwargs['previousOutputId']
        self.amount = kwargs['amount']  # maybe not needed

    def serialize(self):
        logger.info('INPUT TXO SERIALIZE PRVID TYPE: ' + str(type(self.previousOutputId)))
        logger.info('INPUT TXO SERIALIZE AMOUNT TYPE: ' + str(type(self.amount)))
        return {'previousOutputId': self.previousOutputId,
                'amount': self.amount}


class TransactionOutput:
    def __init__(self, *args, **kwargs):
        '''
        amount: int
        transaction_id: int
        address: bytes
        id: int
        '''
        self.amount = kwargs['amount']
        self.transaction_id = kwargs['transaction_id']
        # id from transaction that this utxo came from

        if kwargs.get('id', None) is not None:
            # Got a JSON object
            logger.info("UTXO creation through json object")
            self.id = kwargs['id']  # maybe int() is needed
            self.address = (kwargs['address']).encode()
        else:
            self.id = getrandbits(256)  # some number ?? random
            self.address = kwargs['address']   # to who this utxo is going ,
            # if it's change: sender_address else: receiver_address

    def serialize(self):
        logger.info('UTXO SERIALIZE AMOUNT TYPE: ' + str(type(self.amount)))
        logger.info('UTXO SERIALIZE ID TYPE: ' + str(type( self.id)))
        logger.info('UTXO SERIALIZE TID TYPE: ' + str(type(self.transaction_id)))
        logger.info('UTXO SERIALIZE ADRS TYPE: ' + str(type(self.address.decode())))
        return{
            'amount': self.amount,
            'id': self.id,
            'transaction_id': self.transaction_id,
            'address': self.address.decode()
        }
