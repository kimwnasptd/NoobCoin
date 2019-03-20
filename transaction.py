from collections import OrderedDict

import binascii
import Crypto
import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import requests
from flask import Flask, jsonify, request, render_template


class Transaction:

    def __init__(self, sender_address, sender_private_key,
                 recipient_address=305, value=10):
        self.sender_address = sender_address
        self.receiver_address = recipient_address
        self.amount = value
        self.transaction_inputs = []
        self.transaction_outputs = []
        self.transaction_id = self.get_id()
        self.Signature = self.get_signature(sender_private_key)

    #     # self.sender_address: To public key του wallet από το
    # οποίο προέρχονται τα χρήματα
    #     # self.receiver_address: To public key του wallet στο οποίο θα
    # καταλήξουν τα χρήματα
    #     # self.amount: το ποσό που θα μεταφερθεί
    #     # self.transaction_id: το hash του transaction
    #     # self.transaction_inputs: λίστα από Transaction Input
    #     # self.transaction_outputs: λίστα από Transaction Output
    #     # self.Signature

    def to_dict(self):
        """
        Get a COPY of the dictionary of the transaction class, with all its
        fields. Modifications in that dictionary won't affect
        the Transaction Object
        """
        return(self.__dict__.copy())

    def get_id(self):
        dict = self.to_dict()

        print("Transaction dictionary inside GET_ID is:")
        print(dict)
        class_str = str(list(dict.values())).encode()

        h = SHA256.new(class_str)
        res_hex = h.hexdigest()
        return(res_hex)

    def get_signature(self, key):
        """
        Signs a transaction, using the users given (private ) key,
        in DER format
        """
        dict = self.to_dict()
        print("Transaction dictionary inside GET_SIGNATURE is:")
        print(dict)

        class_str = str(list(dict.values())).encode()
        h = SHA256.new(class_str)
        key_obj = RSA.importKey(key)
        signature = PKCS1_v1_5.new(key_obj).sign(h)
        return signature

    def verify_signature(self, key):
        """
        Returns true if the specific transaction can be verified, else False
        The key is given in DER format.
        """
        dict = self.to_dict()
        signature = dict['Signature']
        key_obj = RSA.importKey(key)     # key here is the PUBLIC KEY of sender

        dict.pop('Signature')    # the signature field didn't exist during sign
        print("Transaction dictionary inside validate_signature is:")
        print(dict)

        class_str = str(list(dict.values())).encode()
        h = SHA256.new(class_str)
        try:
            PKCS1_v1_5.new(key_obj).verify(h, signature)
            return(True)
        except (ValueError, TypeError):
            return(False)
