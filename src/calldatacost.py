#!/usr/bin/env python
import sys


def print_usage():
    print("Usage:\n{} <calldata hex>".format(sys.argv[0]))
    exit()


if len(sys.argv) != 2:
    print_usage()

(_, calldatahex) = sys.argv

if calldatahex[:2] == "0x":
    calldatahex = calldatahex[2:]

Gtxdatazero = 4
Gtxdatanonzero = 16

calldata = bytes.fromhex(calldatahex)

zero_bytes = 0
non_zero_bytes = 0

for b in calldata:
    if b == 0:
        zero_bytes += 1
    else:
        non_zero_bytes += 1

print(f"Zero bytes = {zero_bytes}")
print(f"Non zero bytes = {non_zero_bytes}")
print(f"Total cost = {zero_bytes * Gtxdatazero + non_zero_bytes * Gtxdatanonzero}")
