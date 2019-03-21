from block import Block


class Blockchain:
    def __init__(self, *args, **kwargs):

        if kwargs.get('json', False):
            # Got a JSON Object
            bs = kwargs.get('blocks')
            self.blocks = [Block(**b) for b in bs]
        else:
            self.blocks = kwargs.get('blocks', [Block(previousHash=b"0")])

    def serialize(self):
        return {'blocks': [i.serialize() for i in self.blocks]}

    def get_transactions(self):
        transactions = []
        for block in self.blocks:
            transactions = transactions + block.listOfTransactions
        return(transactions)

    def add_block(self, block):
        if(block.previousHash == self.blocks[-1].hash):
            self.blocks.append(block)
            return(True)
        else:
            return(False)

    def get_last_block(self):
        return(self.blocks[-1])
