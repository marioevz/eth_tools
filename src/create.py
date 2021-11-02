#!/usr/bin/env python
import sys

def print_usage():
    print('Usage:\n{} <address> <nonce>'.format(sys.argv[0]))
    exit()

if len(sys.argv) != 3:
    print_usage()

(_, addr, nonce) = sys.argv


import rlp
from web3 import Web3
w3 = Web3()

if addr.startswith('0x'):
    addr = addr[2:]
if nonce.startswith('0x'):
    nonce = nonce[2:]

if (len(addr) % 2) != 0:
    addr = '0' + addr
if (len(nonce) % 2) != 0:
    nonce = '0' + nonce

addr = bytes.fromhex(addr)
nonce = bytes.fromhex(nonce)

kec = w3.keccak(hexstr=rlp.encode([addr, nonce]).hex())
print(kec[12:].hex())