import requests
import logging
import sys
import json
import blockchain
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from werkzeug.contrib.cache import SimpleCache
from utils import create_logger
from node import Node
from transaction import Transaction
from block import Block
from blockchain import Blockchain
import time

logger = create_logger('rest')
app = Flask(__name__)
CORS(app)
# blockchain = Blockchain()
cache = SimpleCache()

# ------------------------------ Bootstrapping --------------------------------
'''
Context: Bootstrapper Node | Used from: Other Nodes (because of nbc CLI)
This route will only be used from the bootstrapper node. All other nodes will
POST it when initializing. It is used to keep track of the nodes that want to
connect. Once all of them POST, then the bootstrapper will notify everyone
'''
@app.route('/nodes', methods=['POST'])
def post_node():
    counter = cache.get('counter')
    node = cache.get('node')
    data = request.get_json()

    logger.info('New node connected: ' + data['address'] + '. ' +
                'It will have ID {' + str(counter) + '}.')

    # Add the new node to the bootstrapper's ring and update the counters
    data['id'] = counter
    node.register_node_to_ring(data)

    cache.set('node', node)
    cache.set('counter', counter + 1)

    return jsonify('Bootstrap notified successfully'), 200


'''
Context: Bootstrapper Node | Called from: nbc CLI
Once all the nodes are up and have pinged the Bootstrapper, the CLI will make a
GET to this route in the Bootstrapper node. Then the BS node will broadcast to
everyone the final ring.
'''
@app.route('/broadcast-ring')
def get_broadcast_ring():
    node = cache.get('node')
    node.broadcast_ring()
    cache.set('node', node)
    logger.info('Bootstrapping: All nodes connected!')
    logger.info([node['address'] for node in cache.get('node').ring])

    return jsonify('Broadcasted the ring successfully'), 200


'''
Context: Non-Bootstrapper Nodes | Used from: Bootstrapper Node
The Bootstrapper will POST each node when everyone is connected.
The node must update its own ring with the one he got from the bootstrapper
and also update his id value
'''
@app.route('/connect', methods=['POST'])
def post_connect():
    data = request.get_json()
    ring = data['ring']
    genesis_chain = data['genesis_chain']
    node = cache.get('node')

    for nd in ring:
        if nd['address'] == node.address:
            node.id = nd['id']
            node.ring = ring
            node.chain = Blockchain(json=True, **genesis_chain)
            cache.set('node', node)

    logger.info('Node successfully connected with ID: ' + str(node.id))
    logger.info('Network ring: ' + str(node.ring))
    logger.info('Network genesis_chain: ' + str(node.chain.blocks[0].listOfTransactions[0].sender_address))
    # Transaction(**genesis_chain['blocks'][0]['listOfTransactions'][0])
    # Block(**genesis_chain['blocks'][0])
    # Blockchain(json=True, **genesis_chain)

    return jsonify('OK'), 200


# ------------------------------- NoobCoin ------------------------------------
'''
get all transactions in the blockchain
'''
@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    transactions = blockchain.get_transactions()

    response = {'transactions': transactions}
    return jsonify(response), 200


'''
Used by CLI to create and broadcast a new transaction
based on the receiver's id and the amount
'''
@app.route('/create-transaction', methods=['POST'])
def create_transaction():
    args = request.get_json()
    node = cache.get('node')
    target_id = args['id']
    value = args['value']

    logger.info('Node ' + str(node.id) + ' is attempting a transaction')
    logger.info('Target: ' + str(target_id) + 'amount: ' + str(value))
    logger.info("Target id value/type: " + str(target_id) +' ' + str(type(target_id)))
    logger.info("Value value/type: " + str(value) + ' ' + str(type(value)))
    t = node.create_transaction(target_id, value)
    cache.set('node',node)
    if t is not None:
        logger.info('INSIDE CREATE TRANSACTION Signature verification = ' + str(t.verify_signature()))
        logger.info('INSIDE CREATE TRANSACTION Transaction validation = ' + str(node.validate_transaction(t)))
        node.broadcast_transaction(t)  # hit /send-transaction endpoint n times
        logger.info('Transaction successfully broadcasted')
        return jsonify('OK'), 200
    else:
        logger.info('Transaction could not be completed')
        return jsonify('ERROR'), 404


'''
Used by nodes to notify each other of a transaction.
'''
@app.route('/send-transaction', methods=['POST'])
def send_transaction():
    logger.info('INSIDE /send-transaction')
    data = request.get_json()
    logger.info("Data json is: " + str(data))
    node = cache.get('node')
    MINING = cache.get('MINING')
    transaction = Transaction(**data['transaction'])
    # logger.info('Signature  = ' + str(transaction.Signature))
    logger.info('Inside /send-transaction Signature verification = ' + str(transaction.verify_signature()))
    # logger.info('Transaction validation = ' + str(node.validate_transaction(transaction)))
    if node.validate_transaction(transaction):
        logger.info('Transaction validated')
        # update buffer
        node.tx_buffer.append(transaction)
        logger.info('Buffer updated, new length: ' + str(len(node.tx_buffer)))
        # update wallet if needed
        if transaction.receiver_address == node.public_key:  # get sent money
            node.wallet.utxos.append(transaction.transaction_outputs[0])
            logger.info('Updated my wallet with sent amount + ' + str(node.wallet.utxos[-1].amount))
        if transaction.sender_address == node.public_key:  # get change money
            node.wallet.utxos.append(transaction.transaction_outputs[1])
            logger.info('Updated my wallet with change money+ ' + str(node.wallet.utxos[-1].amount))
        if (not MINING) and (len(node.tx_buffer) >= node.CAPACITY):
            # send request to node.address/mine-block with our id number
            address = 'http://' + node.address + '/mine-block'
            try:
                logger.info('Pinging /mine-block of node ' + node.address)
                requests.get(address, timeout=1)
                logger.info('******PING EXCEPTION NOT THROWN')
            except Exception as e:
                logger.info('Ping EXCEPTION')
        cache.set('node', node)
        return jsonify('OK'), 200
    else:
        logger.info('Transaction couldn\'t be validated')
        cache.set('node', node)
        return jsonify('INVTR'), 500


'''
Get notified to start mining
'''
@app.route('/mine-block')
def mineBlock():
    node = cache.get('node')
    MINING = cache.get('MINING')
    if (not MINING) and (len(node.tx_buffer) >= node.CAPACITY):
        # construct Block to mine
        block_to_mine = Block(**{'previousHash': node.chain.get_last_block().hash})
        # fill the block with transactions from the buffer
        for t in range(node.CAPACITY):
            block_to_mine.add_transaction(node.tx_buffer[t])
        # calculate block hash
        block_to_mine.hash = block_to_mine.get_hash()
        logger.info('BLOCK HASH TYPE ' + str(type(block_to_mine.hash)))
        # start mining
        cache.set('MINING', True)
        mined_block = node.mine_block(block_to_mine)
        cache.set('MINING', False)
        node.broadcast_block(mined_block)
    cache.set('node', node)
    return jsonify('OK'), 200


'''
Get a Node's blockchain
'''
@app.route('/blockchain')
def get_blockchain():
    node = cache.get('node')
    return jsonify({'blockchain': node.chain.serialize()}), 200


'''
Other Nodes POST this route to inform the Node that they found a new Block
'''
@app.route('/block', methods=['POST'])
def post_block():
    logger.info('Got a new block from ' + request.remote_addr)
    node = cache.get('node')
    data = request.get_json()
    blk = Block(**data['block'])

    # Check if the block is valid, add it to the blockchain
    if node.validate_block(blk):
        node.chain.blocks.append(blk)
        # TODO: Stop the minning
        cache.set('node', node)
        return jsonify('Block added'), 200

    # Else, we need to see if we must update our blockchain
    node.resolve_conflict()
    cache.set('node', node)
    return jsonify('Coflict Resolved'), 200


@app.route('/hi')
def lets_get_hi():
    # for debugging
    return jsonify('Hi')


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int,
                        help='port to listen on')
    parser.add_argument('-b', '--bootstrap', action='store_true',
                        help='if node is the bootstrap one')
    parser.add_argument('-n', '--nodes_count', default=1, type=int,
                        help='number of nodes. Must have -b flag set')
    args = parser.parse_args()
    port = args.port
    is_bootstrap = args.bootstrap
    nodes_count = args.nodes_count

    address = 'localhost:' + str(port)

    # The state
    node = Node(address)
    cache.set('counter', 1)
    cache.set('MINING', False)
    cache.set('node', node)
    cache.set('nodes_count', nodes_count)

    # The Bootstrapping process
    if not is_bootstrap:
        # Regular nodes need to talk to bootstrap node first
        logger.info('Notifying bootstrap')
        data = {
            'address': address,
            'public_key': node.wallet.public_key.decode('utf-8'),
        }

        resp = requests.post('http://localhost:5000/nodes', json=data).json()
        logger.info(resp)
    else:
        # The bootstrapper node cant post himself since he hasn't yet started
        node.register_node_to_ring({
            'address': address,
            'public_key': node.wallet.public_key.decode('utf-8'),
            'id': 0,
        })
        node.id = 0
        cache.set('node', node)
        logger.info('Bootstrapper ID: ' + str(node.id))

    logger.info('Node initialized successfully!')
    app.run(host='127.0.0.1', port=port)
