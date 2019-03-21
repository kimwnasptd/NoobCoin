# import block
from wallet import Wallet
from random import randint
from Crypto.Hash import SHA256
import requests
from utils import create_logger
from blockchain import Blockchain
from utxo import TransactionInput, TransactionOutput
from transaction import Transaction
from block import Block

logger = create_logger(__name__)

CAPACITY = 10
MINING_DIFFICULTY = 7


class Node:
    def __init__(self, address):
        self.NBC = 100
        self.wallet = Wallet()
        self.address = address  # URL: localhost:id
        self.public_key = self.wallet.public_key
        self.id = -1  # Will be automatically set after bootstrapping
        self.tx_buffer = []    # a tx_buffer for transactions yet to be added
        self.chain = Blockchain()

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

    def create_genesis_chain(self):
        # Construct Bootstrap node first utxo : n*100 coins
        B0 = Block(b'0')
        n = len(self.ring)
        T0 = Transaction(sender_address=self.public_key,
                         sender_private_key=self.wallet.private_key,
                         recipient_address=self.public_key, amount=n*100,
                         transaction_inputs=[],
                         transaction_outputs=[
                            TransactionOutput(n*100, -1, self.public_key),
                            TransactionOutput(0, -1, self.public_key)])
        B0.add_transaction(T0)
        self.chain = Blockchain(blocks=[B0])

    '''
    The Bootstrapper Node will POST every other node and inform it about
    the final ring with all the connected nodes
    '''
    def broadcast_ring(self):
        self.create_genesis_chain()
        for node in self.ring:
            if node['address'] != self.address:
                addr = 'http://' + node['address'] + '/connect'
                requests.post(addr,
                              json={'ring': self.ring,
                                    'genesis_chain': self.chain.serialize()})

    def get_public_key_by_id(self, id):
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
        for transaction in self.tx_buffer:
            if (transaction.find_utxo(id, value, sender) == "INPUT"):
                return(False)
            if (transaction.find_utxo(id, value, sender) == "OUTPUT"):
                flag = True
        return(flag)

    def check_transaction_balance(self, transaction):
        input_sum = 0
        for item in transaction.transaction_inputs:
            input_sum = input_sum + item.amount
            if not(self.check_sanity(item.previousOutputId, item.amount,
                                     transaction.sender)):
                return False
        output_sum = (transaction.transaction_outputs[0].amount +
                      transaction.transaction_outputs[0].amount)
        return(input_sum == output_sum)

    def validate_transaction(self, transaction):
        """
        Validates a transaction, checking both its signature, and that the
        UTXO inputs/outputs are proper.
        """
        if(transaction.validate_signature() and
           self.check_transaction_balance(transaction)):
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
        if(self.validate_transaction(transaction)):
            # if the transaction is valid
            number_of_transactions = block.add_transaction(transaction)
            # add it to the  block
            if(number_of_transactions >= CAPACITY):
                # if enough transactions, add the block hash and then mine
                block.hash = block.get_hash()
                mined_block = self.mine_block(block)
                return(mined_block)
        return(block)

    def create_transaction(self, receiverId, amount):
        '''
        Create a Transaction() Object,
        receiverId: id of receiver node (as in the Transactions.txt)
        amount: how much to transfer
        '''
        # get my public key
        sender_address = self.wallet.public_key

        # find public key by receiverId from ring
        recipient_address = self.get_public_key_by_id(receiverId)

        # get my private key
        sender_private_key = self.wallet.private_key

        # find utxos that will be used
        tospend_utxo_list = []
        # utxos that will be used for the transaction if adequate
        used_utxo_indexes = []
        # indexes of those utxos in the list to be removed after
        gathered_amount = 0
        for idx, t in enumerate(self.wallet.utxos):
            # NOTE: GET MY utxo_list SOMEHOW
            # type(t) == class<TransactionOutput>, just saying
            tospend_utxo_list.append(t)
            used_utxo_indexes.append(idx)
            gathered_amount += t.amount
            if (gathered_amount >= amount):
                break
        if gathered_amount < amount:   # get a job, not enough money
            return False
        #  remove used utxos
        self.wallet.utxos = [utxo for i, utxo in enumerate(self.wallet.utxos)
                             if i not in used_utxo_indexes]

        # create transaction_inputs
        transaction_inputs = [TransactionInput(utxo.id, utxo.amount) for
                              utxo in tospend_utxo_list]
        # create transaction_outputs: sent amount and change
        sent_amount = amount
        change = gathered_amount - amount
        transaction_outputs = [TransactionOutput(sent_amount, -1,
                                                 recipient_address),
                               TransactionOutput(change, -1, sender_address)]
        # create Transaction Object
        T = Transaction(sender_address=sender_address,
                        sender_private_key=sender_private_key,
                        recipient_address=recipient_address, amount=amount,
                        transaction_inputs=transaction_inputs,
                        transaction_outputs=transaction_outputs)

        # remember to broadcast it
        self.broadcast_transaction(T)
        return(True)

    def validate_block(self, block, index=None):
        """
        Is called by the nodes when a new block is received. Ensures that:
        1) The current hash field is correct
        2) The previous hash field agrees with the hash of the previous
        block in the chain
        """
        if(not index):
            len(self.chain.blocks)
        curr_hash = self.blockchain.blocks[index - 1]
        return(block.validate_hash() and (curr_hash == block.previousHash))

    def validate_chain(self):
        flag = True
        block_list = self.chain.blocks
        for i in range(1, len(block_list)):
            flag = flag and self.validate_block(block_list[i])
        return(flag)





        # #concencus functions

    # def valid_chain(self, chain):
    #     #check for the longer chain accroose all nodes


        # def resolve_conflicts(self):
        #     #resolve correct chain



    # def.create_new_block():



    # def broadcast_transaction():




    # def broadcast_block():
