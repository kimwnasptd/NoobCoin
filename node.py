# import block
from wallet import Wallet
import requests


class Node:
    def __init__(self, address):
        self.NBC = 100
        self.wallet = Wallet(address)
        self.address = address
        self.public_key = self.wallet.public_key
        self.id = -1  # Will be automatically set after bootstrapping
        # self.chain
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

    # def.create_new_block():


    # def create_transaction(sender, receiver, signature):
    #     #remember to broadcast it


    # def broadcast_transaction():





    # def validdate_transaction():
    #     #use of signature and NBCs balance


    # def add_transaction_to_block():
    #     #if enough transactions  mine



    # def mine_block():



    # def broadcast_block():




    # def valid_proof(.., difficulty=MINING_DIFFICULTY):




    # #concencus functions

    # def valid_chain(self, chain):
    #     #check for the longer chain accroose all nodes


    # def resolve_conflicts(self):
    #     #resolve correct chain



