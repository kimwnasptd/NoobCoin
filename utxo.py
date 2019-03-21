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

        if kwargs.get(id, None) is not None:
            # Got a JSON object
            self.id = kwargs['id']
            self.address = bytes(kwargs['address'])
        else:
            self.id = getrandbits(256)  # some number ?? random
            self.address = kwargs['address']   # to who this utxo is going ,
            # if it's change: sender_address else: receiver_address

    def serialize(self):
        return{
            'amount': self.amount,
            'id': self.id,
            'transaction_id': self.transaction_id,
            'address': [int(b) for b in self.address]
        }
