#!/usr/bin/env python
import sys
import json
import rlp
import eth_keys
from pprint import pprint
from web3 import Web3
w3 = Web3()
format_example = """
{
    "data" : "",
    "gasLimit" : "0x989680",
    "gasPrice" : "0x10",
    "nonce" : "0x01",
    "to" : "0x000000000000000000000000000000000000ff0c",
    "value" : "0x01",
    "v" : "27",
    "r" : "0x98ff921201554726367d2be8c804a7ff89ccf285ebc57dff8ae4c44b9c19ac4a",
    "s" : "0x45de7595d2738a58caa0bf81c0af0efe37a882cca0eac8b7043373ed60a31fca"
}
"""

def print_usage():
    print('Usage:\n{} /path/to/tx.json\n'.format(sys.argv[0]))
    print('Json file format example:\n{}'.format(format_example))

if len(sys.argv) != 2:
    print_usage()
    raise Exception('Incorrect number of arguments')

(_, tx_json_path) = sys.argv


tx = None
with open(tx_json_path, 'r') as f:
    tx = json.load(f)

def format_value_for_rlp(v):
    if type(v) is str:
        if v.startswith('0x'):
            v = bytes.fromhex(v[2:])
    return v

def get_msg_rlp(tx: dict) -> bytes:
    rlp_array = []

    for k in ("nonce", "gasPrice", "gasLimit", "to","value", "data"):
        if not k in tx:
            raise Exception('malformed tx')
        rlp_array.append(format_value_for_rlp(tx[k]))

    if "chainId" in tx:
        rlp_array.append(format_value_for_rlp(tx["chainId"]))
        rlp_array.append(0)
        rlp_array.append(0)
    return rlp.encode(rlp_array)

def get_msg_hash(tx: dict) -> bytes:
    rlp = get_msg_rlp(tx)
    return w3.keccak(rlp)

def get_tx_rlp(tx: dict) -> bytes:
    rlp_array = []

    for k in ("nonce", "gasPrice", "gasLimit", "to","value", "data", "v", "r", "s"):
        if not k in tx:
            raise Exception('malformed tx')
        rlp_array.append(format_value_for_rlp(tx[k]))

    return rlp.encode(rlp_array)

def get_tx_hash(tx: dict) -> bytes:
    rlp = get_tx_rlp(tx)
    print(rlp.hex())
    return w3.keccak(rlp)

def get_vrs(tx: dict) -> tuple[int, int ,int]:
    vrs = []
    for k in ("v", "r", "s"):
        if not k in tx:
            raise Exception('tx has no signature')
        val = tx[k]
        if type(val) is str:
            if val.startswith('0x'):
                val = int(val, 16)
            else:
                val = int(val)
        if k == "v":
            val -= 27
        vrs.append(val)
    return tuple(vrs)

def get_sender(tx: dict) -> bytes:
    vrs = get_vrs(tx)
    return eth_keys.datatypes.PublicKey(eth_keys.backends.native.ecdsa.ecdsa_raw_recover(get_msg_hash(tx), vrs)).to_canonical_address()

pprint(tx)
print('msg hash = ' + get_msg_hash(tx).hex())
print('tx hash = ' + get_tx_hash(tx).hex())
print('sender = 0x' + get_sender(tx).hex())