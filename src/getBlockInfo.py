#!/usr/bin/env python
import sys
import json
import rlp
import eth_keys
import struct
from pprint import pprint
from web3 import Web3
from trie import HexaryTrie
w3 = Web3()
format_example = """
{
    "parentHash": "0x3b8fb240d288781d4aac94d3fd16809ee413bc99294a085798a589dae51ddd4a",
    "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
    "coinbase/miner": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
    "stateRoot": "0xca3149fa9e37db08d1cd49c9061db1002ef1cd58db2210f2115c8c989b2bdf45",
    "transactions": [],
    "receiptRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
    "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "difficulty": 0,
    "blockNumber": "0x1",
    "gasLimit": "0x1c9c380",
    "gasUsed": "0x0",
    "timestamp": "0x5",
    "extraData": "0x",
    "random/mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "nonce": "0x0000000000000000",
    "baseFeePerGas": "0x7",
    "blockHash": "0x3559e851470f6e7bbed1db474980683e8c315bfce99b2a6ef47c057c04de7858"
}
"""

def print_usage():
    print('Usage:\n{} /path/to/block.json\n'.format(sys.argv[0]))
    print('Json file format example:\n{}'.format(format_example))

if len(sys.argv) != 2:
    print_usage()
    raise Exception('Incorrect number of arguments')

(_, block_json_path) = sys.argv

emptyTrieHash = "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
emptyOmmersHash = "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"

block = None
with open(block_json_path, 'r') as f:
    block = json.load(f)

def format_value_for_rlp(k, v):
    if k == 'transactions':
        t = HexaryTrie(db={})
        for i, tx in enumerate(v):
            id = rlp.encode(i)
            txBytes = bytes.fromhex(tx[2:])
            t.set(id, txBytes)
        v = t.root_hash
    else:
        if type(v) is str:
            if v.startswith('0x'):
                v = v[2:]
                if (len(v) % 2) != 0:
                    v = '0' + v
                try:
                    v = bytes.fromhex(v)
                except Exception as ex:
                    print(v)
                    raise ex
    return v

def get_block_rlp(block: dict) -> bytes:
    rlp_array = []

    for k in (
                "parentHash",
                "ommersHash/sha3Uncles",
                "coinbase/miner",
                "stateRoot",
                "transactions",
                "receiptRoot",
                "logsBloom",
                "difficulty",
                "blockNumber",
                "gasLimit",
                "gasUsed",
                "timestamp",
                "extraData",
                "mixHash/prevRandao",
                "nonce",
                "baseFeePerGas"
            ):
        v = None
        found = False
        for kk in k.split('/'):
            if kk in block:
                v = block[kk]
                k = kk
                found = True
        if not found:
            raise Exception("Required key not found: " + k)
        rlp_array.append(format_value_for_rlp(k, v))
    return rlp.encode(rlp_array)

def get_block_hash(block: dict) -> bytes:
    rlp = get_block_rlp(block)
    return w3.keccak(rlp)

pprint(block)
block_hash = get_block_hash(block)
print('block hash = ' + block_hash.hex())
if "blockHash" in block:
    if block_hash.hex() != block["blockHash"]:
        print(f"Fail: Block hash is different than expected {block_hash.hex()} / {block['blockHash']}")
    else:
        print("Block hash is ok")