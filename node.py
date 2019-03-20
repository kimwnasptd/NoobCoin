# import block
from wallet import Wallet
from random import randint
from Crypto.Hash import SHA256
import requests
from blockchain import Blockchain

CAPACITY = 10
MINING_DIFFICULTY = 7


class Node:
    def __init__(self, address):
        self.NBC = 100
        self.wallet = Wallet(address)
        self.address = address
        self.public_key = self.wallet.public_key
        self.id = -1  # Will be automatically set after bootstrapping
        self.cache = []    # a cache for transactions yet to be added
        self.chain = Blockchain()
        # self.NBCs
        # self.wallet

        # here we store information for every node, as its id, its
        # address (ip:port), public key, balance
        self.ring = []

    '''
    Add this node to the ring, only the bootstrap node can add a node to the
    ring after checking his wallet and ip:port address
    bottstrap node informs all other nodes and gives the request node an id
    and 100 NBCs
    '''
    def register_node_to_ring(self, node):
        # node is {address: , public_key}
        self.ring.append({
            'address': node['address'],
            'public_key': node['public_key'],
            'id': node['id'],
            'NBCs': 100,
        })

    '''
    The Bootstrapper Node will POST every other node and inform it about
    the final ring with all the connected nodes
    '''
    def broadcast_ring(self):
        for node in self.ring:
            if node['address'] != self.address:
                addr = 'http://' + node['address'] + '/connect'
                requests.post(addr, json=self.ring)

    def get_receiver_key(self, id):
        """
        Gets the public key of the wanted recipient of the transaction.
        """
        for item in self.ring:
            if (item['id'] == id):
                return(item['public_key'])
        return(False)

    def mine_block(self, block, difficulty=MINING_DIFFICULTY):
        """
        Mines the given, filled block until a nonce that sets its first
        # MINING_DIFFICULTY blocks to 0.
        """
        sol_length = 300
        while(258 - sol_length < difficulty):   # we check against 258 and not
            #  256 because the sol_length also has the leading '0b' characters
            block.nonce = randint(0, 100000000000000000)

            block_str = str(block.__dict__.values()).encode()
            h = SHA256.new(block_str)
            res_hex = h.hexdigest()
            sol_length = len(bin(int(res_hex, 16)))    # the bin result always
            # starts with 1, so 258 - length gives us the leading zeros
            # print(sol_length)
        return(block)      # return the block with the correct nonce

    def valid_proof(self, block, difficulty=MINING_DIFFICULTY):
        """
        Hashes the block, to confirm that the given nonce results in at least
        # MINING_DIFFICULTY first bits of the hash being set to 0.
        """
        block_str = str(block.__dict__.values()).encode()
        h = SHA256.new(block_str)
        res_hex = h.hexdigest()
        sol_length = len(bin(int(res_hex, 16)))
        if(258 - sol_length < difficulty):
            return(False)
        else:
            return(True)

    def check_sanity(self, id, value, sender):
        """
        Returns True if the specific utxo can be used by the specified sender,
        and has that specific amount. Else, returns false
        """
        flag = False
        for transaction in self.chain.get_transactions():
            if (transaction.find_utxo(id, value, sender) == "INPUT"):
                return(False)
            if (transaction.find_utxo(id, value, sender) == "OUTPUT"):
                flag = True
        for transaction in self.cache:
            if (transaction.find_utxo(id, value, sender) == "INPUT"):
                return(False)
            if (transaction.find_utxo(id, value, sender) == "OUTPUT"):
                flag = True
        return(flag)

    def check_transaction_balance(self, transaction):
        input_sum = 0
        for item in transaction.transaction_inputs:
            input_sum = input_sum + item.amount
            if not(check_sanity(item.previousOutputId, item.amount,
                         transaction.sender)):
                return False
        output_sum = (transaction.transaction_outputs[0].amount
            + transaction.transaction_outputs[0].amount)
        return(input_sum == output_sum)

    def validate_transaction(self, transaction):
        """
        Validates a transaction, checking both its signature, and that the
        UTXO inputs/outputs are proper.
        """
        if(transaction.validate_signature() and
           check_transaction_balance(transaction)):
            return(True)
        else:
            return(False)

    def add_transaction_to_block(self, block, transaction):
        """
        If the transaction is valid, it is added to the block,
        and if the block is filled, then its hash is added,
        and then it is mined
        """
        # if enough transactions  mine
        if(validate_transaction(transaction)):   # if the transaction is valid
            number_of_transactions = block.add_transaction(transaction)
            # add it to the  block
            if(number_of_transactions >= CAPACITY):
                # if enough transactions, add the block hash and then mine
                block.hash = block.get_hash()
                mined_block = mine_block(block)
                return(mined_block)
        return(block)





    # def.create_new_block():


    # def create_transaction(sender, receiver, signature):
    #     #remember to broadcast it


    # def broadcast_transaction():




    # def broadcast_block():




    # #concencus functions

    # def valid_chain(self, chain):
    #     #check for the longer chain accroose all nodes


    # def resolve_conflicts(self):
    #     #resolve correct chain
