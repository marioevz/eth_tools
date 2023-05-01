#!/usr/bin/env python
import sys

import rlp
from Crypto.Hash import keccak


def print_usage():
    print("Usage:\n{} <address> <nonce>".format(sys.argv[0]))
    exit()


def main() -> None:
    if len(sys.argv) != 3:
        print_usage()

    (_, addr, nonce) = sys.argv

    if addr.startswith("0x"):
        addr = addr[2:]
    if nonce.startswith("0x"):
        nonce = nonce[2:]
    else:
        nonce = hex(int(nonce))[2:]

    if (len(addr) % 2) != 0:
        addr = "0" + addr
    if (len(nonce) % 2) != 0:
        nonce = "0" + nonce

    addr = bytes.fromhex(addr)
    nonce = bytes.fromhex(nonce)

    if nonce == bytes.fromhex("00"):
        nonce = ""

    kec = keccak.new(data=rlp.encode([addr, nonce]), digest_bits=256).digest()
    print("0x" + kec[12:].hex())
