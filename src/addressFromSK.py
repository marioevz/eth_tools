#!/usr/bin/env python
import sys
from eth_keys.datatypes import PublicKey
from eth_keys.backends.native.ecdsa import private_key_to_public_key


def print_usage():
    print("Usage:\n{} <Secret key>".format(sys.argv[0]))
    exit()


if len(sys.argv) != 2:
    print_usage()

(_, sk) = sys.argv


if sk.startswith("0x"):
    sk = sk[2:]

if (len(sk) % 2) != 0:
    sk = "0" + sk

sk = bytes.fromhex(sk)
pk = PublicKey(private_key_to_public_key(sk))
print("0x" + pk.to_canonical_address().hex())
