from block import Block


class Blockchain:
    def __init__(self, initial_blocklist=[Block(b"0")]):

        self.blocks = initial_blocklist

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
