from Crypto.Hash import SHA256
from random import randint
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import ipaddress
import datetime

MINING_DIFFICULTY = 6


def generate_RSA(bits=2048):
    '''
    Generate an RSA keypair with an exponent of 65537 in DER format
    param: bits The key length in bits
    Return private key and public key
    '''
    new_key = RSA.generate(bits, e=65537)
    public_key = new_key.publickey().exportKey("DER")
    private_key = new_key.exportKey("DER")
    return private_key, public_key


class Block:
    def __init__(self):
        self.previousHash = "paparia"
        self.timestamp = "paparia"
        self.hash = "paparia"
        self.nonce = None
        self.listOfTransactions = ["paparia1", "paparia2"]


def mine_block(block, difficulty=MINING_DIFFICULTY):
    sol_length = 300
    while( 258 - sol_length <  difficulty):     # we check against 258 and not 256 because the sol_length also has the leading '0b' characters
        block.nonce = randint(0, 100000000000000000)

        block_str = str(block.__dict__.values()).encode()
        h = SHA256.new(block_str)
        res_hex = h.hexdigest()
        sol_length = len(bin(int(res_hex, 16)))       # the bin result always starts with 1, so 258 - length gives us the leading zeros
	# print(sol_length)
    return( block)      # return the block with the correct nonce


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


    #     # self.sender_address: To public key του wallet από το οποίο προέρχονται τα χρήματα
    #     # self.receiver_address: To public key του wallet στο οποίο θα καταλήξουν τα χρήματα
    #     # self.amount: το ποσό που θα μεταφερθεί
    #     # self.transaction_id: το hash του transaction
    #     # self.transaction_inputs: λίστα από Transaction Input
    #     # self.transaction_outputs: λίστα από Transaction Output
    #     # self.Signature

    def to_dict(self):
        """
        Get a COPY of the dictionary of the transaction class, with all its fields
        Modifications in that dictionary won't affect the Transaction Object
        """
        return(self.__dict__.copy())

    def get_id(self):
        dict = self.to_dict()

        print("Transaction dictionary inside GET_ID is:")
        print(dict)
        class_str = str( list(dict.values())).encode()

        h = SHA256.new(class_str)
        res_hex = h.hexdigest()
        return(res_hex)

    def get_signature(self , key):
        """
        Signs a transaction, using the users given (private ) key, in DER format
        """
        dict = self.to_dict()
        print("Transaction dictionary inside GET_SIGNATURE is:")
        print(dict)

        class_str = str( list(dict.values())).encode()
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
        key_obj = RSA.importKey(key)         # key here is the PUBLIC KEY of the sender

        dict.pop('Signature')                # the signature field didn't exist during the mesage signing
        print("Transaction dictionary inside validate_signature is:")
        print(dict)

        class_str = str( list(dict.values())).encode()
        h = SHA256.new(class_str)
        try:
            PKCS1_v1_5.new(key_obj).verify(h, signature)
            return(True)
        except (ValueError, TypeError):
            return(False)


class node:
    def __init__(self):

        self.NBC=100
        self.chain = [Block(0),Block(1),Block(2),Block(3)]
        self.current_id_count = 10
        #self.wallet
        self.ring = [ { "address" : ipaddress.ip_address('192.168.1.1'), "public_key": "fousta_blouza", "id" : 10  } ]
        #here we store information for every node, as its id, its address (ip:port) its public key and its balance

    def get_sender_key(self, sender_address):
        """
        Gets the public key of the node that claims to have sent the message.
        """
        try:
            target_address = ipaddress.ip_address(sender_address)
            for item in self.ring:
                if (item['address'] == target_address):
                    return(item['public_key'])
            return(False)
        except:
            return(False)

    def add_transaction_to_block(self, block, transaction):
        """
        If the transaction is valid, it is added to the block, and if the block is filled,
        then its hash is added, and then it is mined
        """
        #if enough transactions  mine
        if( validdate_transaction(transaction) ):                        # if the transaction is valid
            number_of_transactions = block.add_transaction(transaction)  # add it to the  block
            if( number_of_transactions >= CAPACITY ):                    # if enough transactions, add the block hash and then mine
                block.hash = block.get_hash()
                mined_block = mine_block(block)
                return(mined_block)
        return(block)


class Block:
    def __init__(self, previousHash):
		##set
        self.previousHash = previousHash
        self.timestamp = datetime.datetime.now()
        self.listOfTransactions = []         # will be filled by add_transaction
        self.nonce = 0                       # will be filled by mine_block when the  block is full
        self.hash = 0                        # will be filled once the list of transactions is full


    def get_hash(self):
        """
        Calculates the hash of the block.
        It is called only after the list of transactions is filled,
        and right before the block starts getting mined.
        """
        dict = self.__dict__.copy()
        dict.pop("hash")
        dict.pop("nonce")
        class_str = str( list(dict.values())).encode()
        h = SHA256.new(class_str)
        res_hex = h.hexdigest()
        return(res_hex)



    def add_transaction(self, transaction):
        """
        Add a VALID transaction to the block.
        Returns the number of transactions on the block, after the addition,
        so that the node knows when to mine the block.
        """
        self.listOfTransactions.append(transaction)
        return(len(listOfTransactions))

def poutsa(item,key):
    """
    Signs a transaction, using the users given (private ) key, in DER format
    """
    # dict = self.to_dict()
    # print("Transaction dictionary inside GET_SIGNATURE is:")
    # print(dict)

    class_str = item
    h = SHA256.new(class_str)
    key_obj = RSA.importKey(key)
    signature = PKCS1_v1_5.new(key_obj).sign(h)
    return signature
