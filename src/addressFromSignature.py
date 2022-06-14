#!/usr/bin/env python
import sys
from eth_keys.datatypes import PublicKey
from eth_keys.backends.native.ecdsa import private_key_to_public_key, ecdsa_raw_recover

def print_usage():
    print('Usage:\n{} <Hash> <V> <R> <S>\n'.format(sys.argv[0]))
    exit()

if len(sys.argv) != 5:
    print_usage()

(_, h, v, r, s) = sys.argv

def check_parse_hex(val) -> bytes:
    if val.startswith('0x'):
        val = val[2:]
    if (len(val) % 2) != 0:
        val = '0' + val
    return bytes.fromhex(val)

def check_parse_int(val) -> int:
    if val.startswith('0x'):
        return int(val, 16)
    return int(val)

h = check_parse_hex(h)
v = check_parse_int(v) - 27
r = check_parse_int(r)
s = check_parse_int(s)

vrs = tuple([v, r, s])

print('0x' + PublicKey(ecdsa_raw_recover(h, vrs)).to_canonical_address().hex())