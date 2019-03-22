from collections import OrderedDict

import binascii
import Crypto
import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from utils import create_logger
from utxo import TransactionInput, TransactionOutput

import requests
from flask import Flask, jsonify, request, render_template

logger = create_logger(__name__)


class Transaction:

    def __init__(self, *args, **kwargs):
        '''
        sender_address: bytes
        receiver_address: bytes
        amount: int
        transaction_inputs: [TransactionInput]
        transaction_outputs: [TransactionOutput]
        transaction_id: string
        Signature: bytes
        '''

        # These are common between json constructor and object constructor
        self.amount = kwargs['amount']

        if kwargs.get('Signature', None) is not None:
            # Got a JSON object
            logger.info("TRANSACTION creation through json object")
            self.sender_address = (kwargs['sender_address']).encode()
            self.receiver_address = (kwargs['receiver_address']).encode()
            in_utxos = kwargs['transaction_inputs']
            out_utxos = kwargs['transaction_outputs']
            self.transaction_inputs = [TransactionInput(**t) for t in in_utxos]
            self.transaction_outputs = [TransactionOutput(**t) for t in out_utxos]

            self.transaction_id = kwargs['transaction_id']
            self.Signature = bytes(kwargs['Signature'])
        else:
            self.sender_address = kwargs['sender_address']
            self.receiver_address = kwargs['receiver_address']
            self.transaction_inputs = kwargs['transaction_inputs']
            self.transaction_outputs = kwargs['transaction_outputs']
            self.transaction_id = self.get_id()
            for utxo in self.transaction_outputs:
                utxo.transaction_id = self.transaction_id
            sender_private_key = kwargs['sender_private_key']
            self.Signature = self.get_signature(sender_private_key)

    def serialize(self):
        return {
            'sender_address': self.sender_address.decode(),#[int(b) for b in self.sender_address],
            'receiver_address': self.receiver_address.decode(),#[int(b) for b in self.receiver_address],
            'amount': self.amount,
            'transaction_inputs': [i.serialize() for i in self.transaction_inputs],
            'transaction_outputs': [i.serialize() for i in self.transaction_outputs],
            'transaction_id': self.transaction_id,
            'Signature': [int(b) for b in self.Signature],
        }

    def to_dict(self):
        """
        Get a COPY of the dictionary of the transaction class, with all its
        fields. Modifications in that dictionary won't affect
        the Transaction Object
        """
        return(self.__dict__.copy())

    def get_id(self):
        dict = self.to_dict()
        dict.pop('transaction_outputs')

        logger.info("Transaction dictionary inside GET_ID is:")
        logger.info(dict)
        class_str = str(list(dict.values())).encode()

        h = SHA256.new(class_str)
        res_hex = h.hexdigest()
        logger.info('TRANSACTION HASH TYPE: ' + str(type(res_hex)))
        return(res_hex)

    def get_signature(self, key):
        """
        Signs a transaction, using the users given (private ) key,
        in PEM format
        """
        dict = self.to_dict()
        logger.info("Transaction dictionary inside GET_SIGNATURE is:")
        logger.info(dict)

        class_str = str(list(dict.values())).encode()
        h = SHA256.new(class_str)
        key_obj = RSA.importKey(key)
        signature = PKCS1_v1_5.new(key_obj).sign(h)
        return signature

    def verify_signature(self):
        """
        Returns true if the specific transaction can be verified, else False
        The key, in PEM format, can be taken directly from the transaction.
        """
        dict = self.to_dict()
        signature = dict['Signature']
        key = self.sender_address
        key_obj = RSA.importKey(key)     # key here is the PUBLIC KEY of sender

        dict.pop('Signature')    # the signature field didn't exist during sign
        logger.info("Transaction dictionary inside validate_signature is:")
        logger.info(dict)

        class_str = str(list(dict.values())).encode()
        h = SHA256.new(class_str)
        try:
            PKCS1_v1_5.new(key_obj).verify(h, signature)
            return(True)
        except (ValueError, TypeError):
            return(False)

    def find_utxo(self, id, value, sender):
        """
        Check if the  transaction contains the specified utxo, either
        as input or output
        """
        logger.info('Searching for item with: ' + str(id) + ' ' + str(value) + ' ' + str(sender))
        for item in self.transaction_outputs:
            logger.info("UTXO ITEM FIELDS: " + str(item.id) + ' ' + str(item.amount) + str(item.address))
            if (item.id == id and item.amount == value and
                    item.address == sender):
                return("OUTPUT")
        for item in self.transaction_inputs:
            if (item.previousOutputId == id):
                return("INPUT")
        return("NOT FOUND")
