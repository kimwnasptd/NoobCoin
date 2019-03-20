from Crypto.Random.random import getrandbits


class TransactionInput:
    def __init__(self, previousOutputId, amount):
        self.previousOutputId = previousOutputId
        self.amount = amount  # maybe not needed

    def serialize(self):
        return {'previousOutputId': self.previousOutputId,
                'amount': self.amount}


class TransactionOutput:
    def __init__(self, amount, transaction_id, address):
        self.amount = amount
        self.id = getrandbits(256)  # some number ?? random
        self.transaction_id = transaction_id
        # id from transaction that this utxo came from
        self.address = address   # to who this utxo is going ,
        # if it's change: sender_address else: receiver_address

    def serialize(self):
        return{'amount': self.amount,
               'id': self.id,
               'transaction_id': self.transaction_id,
               'address': self.address.decode()}
