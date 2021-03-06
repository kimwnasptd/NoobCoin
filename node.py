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
import time
import random
logger = create_logger(__name__)

# CAPACITY = 10
# MINING_DIFFICULTY = 7


class Node:
    def __init__(self, address):
        self.NBC = 100
        self.CAPACITY = 5
        self.MINING_DIFFICULTY = 5
        self.mining = False
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
        B0 = Block(previousHash=(b'0').decode())
        n = len(self.ring)
        txo_sent = TransactionOutput(amount=n*100,
                          transaction_id=-1,
                          address=self.public_key)
        txo_change = TransactionOutput(amount=0,
                          transaction_id=-1,
                          address=self.public_key)
        T0 = Transaction(
            sender_address=self.public_key,
            sender_private_key=self.wallet.private_key,
            receiver_address=self.public_key,
            amount=n*100,
            transaction_inputs=[],
            transaction_outputs=[txo_sent, txo_change]
        )
        B0.add_transaction(T0)
        self.chain = Blockchain(blocks=[B0])
        #adding n*100 coins to my wallet (BS node)

        self.wallet.utxos = [txo_sent]
        logger.info('added n*100 to genesis, exiting create genesis')

    '''
    The Bootstrapper Node will POST every other node and inform it about
    the final ring with all the connected nodes
    '''
    def broadcast_ring(self):
        self.create_genesis_chain()
        for node in self.ring:
            if node['address'] != self.address:
                addr = 'http://' + node['address'] + '/connect'
                requests.post(addr, json={
                    'ring': self.ring,
                    'genesis_chain': self.chain.serialize()
                })

    def get_public_key_by_id(self, id):
        """
        Gets the public key of the wanted recipient of the transaction.
        """
        for item in self.ring:
            if (item['id'] == id):
                return((item['public_key']).encode())
        return(False)

    def get_id_by_public_key(self, pk):
        for node in self.ring:
            if node['public_key'] == pk:
                return node['id']

        return None

    def mine_block(self, block):
        """
            Mines the given, filled block until a nonce that sets its first
        # MINING_DIFFICULTY blocks to 0.
        """
        time.sleep(2)
        sol_length = 300
        while(258 - sol_length < self.MINING_DIFFICULTY):   # we check against 258 and not
            #  256 because the sol_length also has the leading '0b' characters
            block.nonce = randint(0, 100000000000000000)

            block_str = str(block.__dict__.values()).encode()
            h = SHA256.new(block_str)
            res_hex = h.hexdigest()
            sol_length = len(bin(int(res_hex, 16)))    # the bin result always
            # starts with 1, so 258 - length gives us the leading zeros
            # print(sol_length)
        return(block)      # return the block with the correct nonce

    def valid_proof(self, block):
        """
        Hashes the block, to confirm that the given nonce results in at least
        # MINING_DIFFICULTY first bits of the hash being set to 0.
        """
        block_str = str(block.__dict__.values()).encode()
        h = SHA256.new(block_str)
        res_hex = h.hexdigest()
        sol_length = len(bin(int(res_hex, 16)))
        if(258 - sol_length < self.MINING_DIFFICULTY):
            return(False)
        else:
            return(True)

    def check_sanity(self, id, value, sender):
        """
        Returns True if the specific utxo can be used by the specified sender,
        and has that specific amount. Else, returns false
        """
        flag = False
        for i, transaction in enumerate(self.chain.get_transactions()):
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
                                     transaction.sender_address)):
                return False
        output_sum = (transaction.transaction_outputs[0].amount +
                      transaction.transaction_outputs[1].amount)
        return(input_sum == output_sum)

    def validate_transaction(self, transaction):
        """
        Validates a transaction, checking both its signature, and that the
        UTXO inputs/outputs are proper.
        """
        if(transaction.verify_signature() and
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
            if(number_of_transactions >= self.CAPACITY):
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
        if not recipient_address:
            return None

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
            return None
        #  remove used utxos
        self.wallet.utxos = [utxo for i, utxo in enumerate(self.wallet.utxos)
                             if i not in used_utxo_indexes]

        # create transaction_inputs
        transaction_inputs = [
            TransactionInput(previousOutputId=utxo.id, amount=utxo.amount)
            for utxo in tospend_utxo_list
        ]
        # create transaction_outputs: sent amount and change
        sent_amount = amount
        change = gathered_amount - amount
        transaction_outputs = [
            TransactionOutput(amount=sent_amount,
                              transaction_id=-1,
                              address=recipient_address),
            TransactionOutput(amount=change,
                              transaction_id=-1,
                              address=sender_address)
        ]
        # create Transaction Object
        t = Transaction(sender_address=sender_address,
                        sender_private_key=sender_private_key,
                        receiver_address=recipient_address, amount=amount,
                        transaction_inputs=transaction_inputs,
                        transaction_outputs=transaction_outputs)

        return t

    def validate_block(self, block, index=None):
        """
        Is called by the nodes when a new block is received. Ensures that:
        1) The current hash field is correct
        2) The previous hash field agrees with the hash of the previous
        block in the chain
        """
        if(not index):
            # Only compare with the head of the blockchain
            curr_hash = self.chain.blocks[-1].hash
            return (block.validate_hash() and curr_hash == block.previousHash)

        curr_hash = self.chain.blocks[index - 1].hash
        return(block.validate_hash() and (curr_hash == block.previousHash))

    def validate_chain(self):
        flag = True
        block_list = self.chain.blocks
        for i in range(1, len(block_list)):
            flag = flag and self.validate_block(block_list[i])
        return(flag)

    def broadcast_transaction(self, t):
        lst = [x for x in self.ring]
        random.shuffle(lst)
        for node in lst:
            addr = 'http://' + node['address'] + '/send-transaction'
            requests.post(addr, json={'transaction': t.serialize()})

    def broadcast_block(self, block):
        serial_block = block.serialize()
        lst = [x for x in self.ring]
        random.shuffle(lst)

        for node in lst:
            if node['address'] != self.address:
                addr = 'http://' + node['address'] + '/block'
                requests.post(addr, json={'block': serial_block})

    def resolve_conflicts(self):
        # Ask every other node in the ring and only keep the largest chain
        curr = self.chain
        found = False

        for node in self.ring:
            if node['address'] != self.address:
                chain = requests \
                    .get('http://' + node['address'] + '/blockchain').json()

                # Check if new Blockchain is larger
                if len(curr.blocks) < len(chain['blockchain']['blocks']):
                    found = True
                    curr = Blockchain(json=True, **chain)  # AUTH MAS GAMAEI

        # If we found a new blockchain, again we must stop minning and change
        # our active blockchain
        return found, curr

    def refresh_wallet_from_chain(self):
        transactions = self.chain.get_transactions()
        input_ids = []
        outputs = []
        for t in transactions:
            outputs.append(t.transaction_outputs[0])
            outputs.append(t.transaction_outputs[1])
            input_ids.extend([q.previousOutputId for q in t.transaction_inputs])
        self.wallet.utxos = [out for out in outputs if((out.id not in input_ids) and (out.address == self.public_key))]
        return self.wallet

    def get_last_transactions(self):
        blk = self.chain.get_last_block()
        ts = [i for i in blk.listOfTransactions]

        res = []
        for t in ts:
            res.append({
                'src': self.get_id_by_public_key(t.sender_address.decode()),
                'dst': self.get_id_by_public_key(t.receiver_address.decode()),
                'val': t.transaction_outputs[0].amount,
            })

        return res
