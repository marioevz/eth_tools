#!/usr/bin/env python
import json
import sys
from pprint import pprint
from typing import Tuple

import rlp
from Crypto.Hash import keccak
from eth_keys.backends.native.ecdsa import ecdsa_raw_recover, ecdsa_raw_sign
from eth_keys.datatypes import PublicKey


def keccak_256(data: bytes) -> bytes:
    return keccak.new(digest_bits=256, data=data).digest()


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
    print("Usage:\n{} /path/to/tx.json\n".format(sys.argv[0]))
    print("Json file format example:\n{}".format(format_example))


if len(sys.argv) != 2:
    print_usage()
    raise Exception("Incorrect number of arguments")


def format_value_for_rlp(v):
    if type(v) is list:
        v = v[0]
    if type(v) is str:
        if v.startswith("0x"):
            v = v[2:]
            if (len(v) % 2) != 0:
                v = "0" + v
            v = bytes.fromhex(v)
    return v


def get_msg_rlp(tx: dict) -> bytes:
    rlp_array = []

    for k in ("nonce", "gasPrice", "gasLimit", "to", "value", "data"):
        if k not in tx:
            raise Exception("malformed tx")
        rlp_array.append(format_value_for_rlp(tx[k]))

    if "chainId" in tx:
        rlp_array.append(format_value_for_rlp(tx["chainId"]))
        rlp_array.append(0)
        rlp_array.append(0)
    return rlp.encode(rlp_array)


def get_msg_hash(tx: dict) -> bytes:
    rlp = get_msg_rlp(tx)
    return keccak_256(rlp)


def get_secret_key_bytes(sk: str) -> bytes:
    return format_value_for_rlp(sk)


def get_vsr_from_tx_with_secret_key(tx: dict) -> Tuple[str, str, str]:
    msg_hash = get_msg_hash(tx)
    v, r, s = ecdsa_raw_sign(msg_hash, get_secret_key_bytes(tx["secretKey"]))
    return v, hex(r), hex(s)


def get_tx_rlp(tx: dict) -> bytes:
    rlp_array = []
    if "secretKey" in tx:
        v, r, s = get_vsr_from_tx_with_secret_key(tx)
        if "chainId" in tx:
            tx["v"] = v + tx["chainId"] * 2 + 35
        else:
            tx["v"] = v + 27
        tx["r"] = r
        tx["s"] = s
    if "v" in tx and "r" in tx and "s" in tx:
        for k in (
            "nonce",
            "gasPrice",
            "gasLimit",
            "to",
            "value",
            "data",
            "v",
            "r",
            "s",
        ):
            if k not in tx:
                raise Exception("malformed tx")
            rlp_array.append(format_value_for_rlp(tx[k]))
    else:
        raise Exception("Unsupported tx type")

    return rlp.encode(rlp_array)


def get_rlp_hash(rlp: bytes) -> bytes:
    return keccak_256(rlp)


def get_tx_hash(tx: dict) -> bytes:
    rlp = get_tx_rlp(tx)
    print(rlp.hex())
    return keccak_256(rlp)


def get_vrs(tx: dict) -> tuple[int, int, int]:
    vrs = []
    for k in ("v", "r", "s"):
        if k not in tx:
            raise Exception("tx has no signature")
        val = tx[k]
        if type(val) is str:
            if val.startswith("0x"):
                val = int(val, 16)
            else:
                val = int(val)
        if k == "v":
            if "chainId" in tx:
                val -= tx["chainId"] * 2 + 35
            else:
                val -= 27
        vrs.append(val)
    return tuple(vrs)


def get_sender(tx: dict) -> bytes:
    vrs = get_vrs(tx)
    pk = PublicKey(ecdsa_raw_recover(get_msg_hash(tx), vrs))
    return pk.to_canonical_address()


def get_raw_txn_rlp(tx: dict) -> bytes:
    pass


(_, tx_json_path) = sys.argv


if tx_json_path[:2] == "0x":
    rlp_hex = tx_json_path
    rlp_bytes = bytes.fromhex(rlp_hex[2:])
    print("tx hash = " + get_rlp_hash(rlp_bytes).hex())
else:
    tx = None
    with open(tx_json_path, "r") as f:
        tx = json.load(f)

    pprint(tx)
    print("msg hash = " + get_msg_hash(tx).hex())
    print("tx hash = " + get_tx_hash(tx).hex())
    print("sender = 0x" + get_sender(tx).hex())
    print("raw tx rlp = 0x" + get_tx_rlp(tx).hex())
