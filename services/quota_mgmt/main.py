from google.cloud.firestore_v1.base_query import FieldFilter
from web3 import Web3
from time import sleep
from google.cloud import firestore
from flask import abort
import functions_framework
import io
from flask_cors import CORS
from flask import Flask, request, send_from_directory, make_response
from werkzeug.utils import secure_filename
import os

# web3 settings:

# add quota to firestore
def add_quota(address, count):
    db = firestore.Client()
    doc_ref = db.collection('nounifyquota').document(address)
    doc_ref.set({
        'address': address,
        'count': count
    })

def increase_quota(address, count):
    db = firestore.Client()
    doc_ref = db.collection('nounifyquota').document(address)
    doc_ref.update({
        'count': firestore.Increment(count)
    })

def user_has_record(address):
    db = firestore.Client()
    doc_ref = db.collection('nounifyquota').document(address)
    doc = doc_ref.get()
    if doc.exists:
        return True
    else:
        return False

# store the transaction hash
def store_transaction_hash(transaction_hash):
    # store it in the boughtnounifyquota
    db = firestore.Client()
    doc_ref = db.collection('boughtnounifyquota').document(transaction_hash)
    doc_ref.set({
        'transactionHash': transaction_hash,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'processed': False
    })

def set_success(transaction_hash):
    db = firestore.Client()
    doc_ref = db.collection('boughtnounifyquota').document(transaction_hash)
    doc_ref.update({
        'processed': True
    })

def decode_transfer_event(transaction_hash):
    # decode the transaction hash, and verify how much the address transfer
    # if the address transfer 1 usdt, and they got 1 quota.
    # if the address transfer 100 usdt, and they got 100 quota.
    # if the address transfer 0.1 usdt, and they got 0 quota.
    w3 = Web3(Web3.HTTPProvider('https://polygon.llamarpc.com'))
    # abi for transfering erc20 function
    abi = [
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "recipient",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "amount",
                    "type": "uint256"
                }
            ],
            "name": "transfer",
            "outputs": [
                {
                    "internalType": "bool",
                    "name": "success",
                    "type": "bool"
                }
            ],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
    tx = w3.eth.get_transaction(transaction_hash)
    contract = w3.eth.contract(address='0xc2132D05D31c914a87C6611C10748AEb04B58e8F', abi=abi)
    decoded_transaction = contract.decode_function_input(tx.input)
    # get amount of usdt, and get rid of decimals
    amount = decoded_transaction[1]['amount'] / 10 ** 6
    sender = tx['from']
    print(sender.lower())
    print(amount)
    return sender.lower(), amount

@functions_framework.http
def decode_add_quota(request):
    # TODO: duplicated quota adding
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    else:
        dict_data = request.get_json()
        print(dict_data)
        if dict_data is None or 'transactionHash' not in dict_data:
            abort(400)
        transaction_hash = dict_data['transactionHash']
        sender, amount = decode_transfer_event(transaction_hash)
        # store the transaction hash
        store_transaction_hash(transaction_hash)
        if amount < 1:
            abort(400)
        # if the sender not in the database, add it to the database
        if user_has_record(sender):
            # if the sender in the database, increase the quota
            increase_quota(sender, amount)
        else:
            # if the sender not in the database, add it to the database
            add_quota(sender, amount)
        # if the transaction is already  in the state 'success',  decrease 1 quota
        db = firestore.Client()
        doc_ref = db.collection('boughtnounifyquota').document(transaction_hash)
        doc = doc_ref.get()
        if doc.exists:
            # if the transaction is already  in the state 'success',  decrease 1 quota
            if doc.to_dict()['processed']:
                print('already processed')
                increase_quota(sender, -1)
                return 'success'
        # set the transaction hash to success
        set_success(transaction_hash)
        return 'success'


if __name__ == '__main__':
    # test add quota function
    # add_quota('0xca84541d8b8bf50fd8b042acfd28b1e390703e20', 99999)
    decode_transfer_event('0xec2f80839fc7ef3d9d0d82b9a6eec050eaf64068074b4b6ecd053dc3ada527f3')
