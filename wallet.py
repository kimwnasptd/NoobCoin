import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
from utils import create_logger

logger = create_logger(__name__)


class Wallet:

    def __init__(self, utxos_arg=[]):
        self.public_key, self.private_key = self.generate_rsa()
        self.utxos = utxos_arg

    def balance(self):
        ret = 0
        for utxo in self.utxos:
            ret = ret + utxo.amount
        return ret

    def generate_rsa(self, bits=2048):
        '''
        Generate an RSA keypair with an exponent of 65537 in PEM format
        param: bits The key length in bits
        Return private key and public key
        '''
        new_key = RSA.generate(bits, e=65537)
        public_key = new_key.publickey().exportKey("PEM")
        private_key = new_key.exportKey("PEM")
        return public_key, private_key
