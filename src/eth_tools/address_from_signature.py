#!/usr/bin/env python
import sys

from eth_keys.backends.native.ecdsa import ecdsa_raw_recover
from eth_keys.datatypes import PublicKey


def print_usage():
    print("Usage:\n{} <Hash> <V> <R> <S>\n".format(sys.argv[0]))
    exit()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print_usage()

    (_, h, v, r, s) = sys.argv

    def check_parse_hex(val: str) -> bytes:
        if val.startswith("0x"):
            val = val[2:]
        if (len(val) % 2) != 0:
            val = "0" + val
        return bytes.fromhex(val)

    def check_parse_int(val: str) -> int:
        if val.startswith("0x"):
            return int(val, 16)
        return int(val)

    h = check_parse_hex(h)
    v = check_parse_int(v)
    if v >= 27:
        v -= 27
    r = check_parse_int(r)
    s = check_parse_int(s)

    vrs = tuple([v, r, s])
    pk = PublicKey(ecdsa_raw_recover(h, vrs))
    print("0x" + pk.to_canonical_address().hex())
