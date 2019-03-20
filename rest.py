import requests
import logging
import sys
import json
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from werkzeug.contrib.cache import SimpleCache
from node import Node


# import block
# import node
# import blockchain
# import wallet
# import transaction
# import wallet


logger = None
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
    ring = request.get_json()
    node = cache.get('node')

    for nd in ring:
        if nd['address'] == node.address:
            node.id = nd['id']
            cache.set('node', node)

    logger.info('Node successfully connected with ID: ' + str(node.id))
    logger.info('Network ring: ' + str(ring))
    return jsonify('OK'), 200


# ------------------------------- NoobCoin ------------------------------------
'''
get all transactions in the blockchain
'''
@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    transactions = blockchain.transactions

    response = {'transactions': transactions}
    return jsonify(response), 200


@app.route('/connect', methods=['POST'])
def post_connect():
    ring = request.get_json()
    node = cache.get('node')

    for nd in ring:
        if nd['address'] == node.address:
            node.id = nd['id']
            cache.set('node', node)

    logger.info('Node successfully connected with ID: ' + str(node.id))
    logger.info('Network ring: ' + str(ring))
    return jsonify('OK'), 200


@app.route('/create_transaction', methods=['POST'])
def create_transaction():
    args = request.get_json()
    node = cache.get('node')
    target_id = args['id']
    value = args['value']

    logger.info('Node ' + str(node.id) + 'is attempting a transaction')

    # response = {'transactions': transactions}
    return jsonify('OK'), 200


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

    # Set up logging
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s'))
    logger = logging.getLogger(address)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # The state
    node = Node(address)
    cache.set('counter', 1)
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
        cache.set('node', node)

    logger.info('Node initialized successfully!')
    app.run(host='127.0.0.1', port=port)
