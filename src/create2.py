#!/usr/bin/env python
import sys
from Crypto.Hash import keccak


def print_usage():
    print("Usage:\n{} <address> <salt> <init_code>".format(sys.argv[0]))
    exit()


if len(sys.argv) != 4:
    print_usage()

(_, addr, salt, init_code) = sys.argv


if addr.startswith("0x"):
    addr = addr[2:]
if salt.startswith("0x"):
    salt = salt[2:]
if init_code.startswith("0x"):
    init_code = init_code[2:]

if (len(addr) % 2) != 0:
    addr = "0" + addr
while len(salt) < 64:
    salt = "0" + salt
if (len(init_code) % 2) != 0:
    init_code = "0" + init_code

ff = bytes.fromhex("ff")
addr = bytes.fromhex(addr)
salt = bytes.fromhex(salt)
init_code = bytes.fromhex(init_code)


init_kec = keccak.new(data=init_code, digest_bits=256).digest()
kec = keccak.new(data=(ff + addr + salt + init_kec), digest_bits=256).digest()
print("0x" + kec[12:].hex())
