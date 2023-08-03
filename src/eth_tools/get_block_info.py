#!/usr/bin/env python
import json
import sys
from pprint import pprint

import rlp
from Crypto.Hash import keccak
from trie import HexaryTrie

EMPTY_TRIE_HASH = HexaryTrie(db={}).root_hash
EMPTY_OMMERS_HASH = keccak.new(data=rlp.encode([]), digest_bits=256).digest()
EMPTY_LOGS_BLOOM = bytes([0] * 256)
EMPTY_NONCE = bytes([0] * 8)
EMPTY_MIX_HASH = bytes([0] * 32)


def to_hex(b: bytes | str) -> str:
    if type(b) is bytes:
        return "0x" + b.hex()
    elif type(b) is str:
        if b.startswith("0x"):
            return b
        else:
            return "0x" + b
    raise Exception("invalid type")


def bytes_equal(b1: bytes | str, b2: bytes | str) -> bool:
    if type(b1) is str:
        if b1.startswith("0x"):
            b1 = b1[2:]
        b1 = bytes.fromhex(b1)
    if type(b2) is str:
        if b2.startswith("0x"):
            b2 = b2[2:]
        b2 = bytes.fromhex(b2)
    if type(b1) is not bytes:
        raise Exception("invalid type")
    if type(b2) is not bytes:
        raise Exception("invalid type")
    return b1 == b2


def format_value_for_rlp(k, v) -> bytes:
    if k == "transactions":
        t = HexaryTrie(db={})
        for i, tx in enumerate(v):
            id = rlp.encode(i)
            txBytes = bytes.fromhex(tx[2:])
            t.set(id, txBytes)
        v = t.root_hash
    elif k == "withdrawals":
        t = HexaryTrie(db={})
        for id, withdrawal in enumerate(v):
            fields = ("index", "validatorIndex", "address", "amount")
            rlp_array = []
            for field in fields:
                if field not in withdrawal:
                    raise Exception(f"Required withdrawal key not found: {field}")
                rlp_array.append(format_value_for_rlp(field, withdrawal[field]))
            t.set(rlp.encode(id), rlp.encode(rlp_array))
        v = t.root_hash
    elif k == "extraData":
        if type(v) is str:
            if v.startswith("0x"):
                v = v[2:]
                if (len(v) % 2) != 0:
                    v = "0" + v
                try:
                    v = bytes.fromhex(v)
                except Exception as ex:
                    print(v)
                    raise ex
    else:
        if type(v) is str:
            if v.startswith("0x"):
                v = v[2:]
                if (len(v) % 2) != 0:
                    v = "0" + v
                if v == "00":
                    v = ""
                try:
                    v = bytes.fromhex(v)
                except Exception as ex:
                    print(v)
                    raise ex
        elif type(v) is bytes:
            pass
        else:
            raise Exception("invalid type for key: {}".format(k))
    return v


def get_header_rlp_array(block: dict) -> list:
    rlp_array = []

    required_fields = (
        "parentHash",
        "ommers/ommersHash/sha3Uncles/uncleHash",
        "coinbase/miner/feeRecipient",
        "stateRoot",
        "transactions/transactionsTrie/transactionsRoot",
        "receiptRoot/receiptsRoot/receiptTrie",
        "bloom/logsBloom",
        "difficulty",
        "blockNumber/number",
        "gasLimit",
        "gasUsed",
        "timestamp",
        "extraData",
        "mixHash/prevRandao",
        "nonce",
    )

    fields_with_default = {
        "ommers/ommersHash/sha3Uncles/uncleHash": EMPTY_OMMERS_HASH,
        "difficulty": "0x0",
        "nonce": EMPTY_NONCE,
    }

    optional_fields = (
        "baseFeePerGas",
        "withdrawals/withdrawalsRoot",
        "blobGasUsed",
        "excessBlobGas",
        "parentBeaconBlockRoot",
    )

    for k in required_fields:
        v = None
        found = False
        for kk in k.split("/"):
            if kk in block:
                v = block[kk]
                k = kk
                found = True
        if not found:
            if k in fields_with_default:
                v = fields_with_default[k]
            else:
                raise Exception("Required key not found: " + k)
        rlp_array.append(format_value_for_rlp(k, v))

    for k in optional_fields:
        v = None
        found = False
        for kk in k.split("/"):
            if kk in block:
                v = block[kk]
                k = kk
                found = True
        if not found:
            continue
        if v is not None:
            rlp_array.append(format_value_for_rlp(k, v))

    return rlp_array


def get_header_rlp(block: dict) -> bytes:
    return rlp.encode(get_header_rlp_array(block))


def get_block_rlp(block: dict) -> bytes:
    rlp_array = []
    rlp_array.append(get_header_rlp_array(block))

    txs_rlp_array = []
    if "transactions" in block:
        for t in block["transactions"]:
            txs_rlp_array.append(format_value_for_rlp("transaction", t))
    elif "transactionsTrie" in block:
        if not bytes_equal(block["transactionsTrie"], EMPTY_TRIE_HASH):
            raise Exception("Cannot get the block rlp without the actual transactions")
    rlp_array.append(txs_rlp_array)

    ommers_rlp_array = []
    if "ommmers" in block:
        for om in block["ommmers"]:
            ommers_rlp_array.append(format_value_for_rlp("ommer", om))
    elif "ommersHash" in block:
        if not bytes_equal(block["ommersHash"], EMPTY_OMMERS_HASH):
            raise Exception("Cannot get the block rlp without the actual ommers")
    elif "sha3Uncles" in block:
        if not bytes_equal(block["sha3Uncles"], EMPTY_OMMERS_HASH):
            raise Exception("Cannot get the block rlp without the actual ommers")
    elif "uncleHash" in block:
        if not bytes_equal(block["uncleHash"], EMPTY_OMMERS_HASH):
            raise Exception("Cannot get the block rlp without the actual ommers")
    rlp_array.append(ommers_rlp_array)

    return rlp.encode(rlp_array)


def can_get_block_rlp(block: dict) -> bool:
    return (
        "transactions" in block
        or (
            "transactionsTrie" in block and bytes_equal(block["transactionsTrie"], EMPTY_TRIE_HASH)
        )
    ) and (
        "ommers" in block
        or ("ommersHash" in block and bytes_equal(block["ommersHash"], EMPTY_OMMERS_HASH))
        or ("sha3Uncles" in block and bytes_equal(block["sha3Uncles"], EMPTY_OMMERS_HASH))
        or ("uncleHash" in block and bytes_equal(block["uncleHash"], EMPTY_OMMERS_HASH))
    )


def get_block_hash(block: dict) -> bytes:
    rlp = get_header_rlp(block)
    return keccak.new(data=rlp, digest_bits=256).digest()


def print_usage():
    EXAMPLE_PARENT_HASH, EXAMPLE_STATE_ROOT, EXAMPLE_BLOCK_HASH = (
        "0x3b8fb240d288781d4aac94d3fd16809ee413bc99294a085798a589dae51ddd4a",
        "0xca3149fa9e37db08d1cd49c9061db1002ef1cd58db2210f2115c8c989b2bdf45",
        "0x3559e851470f6e7bbed1db474980683e8c315bfce99b2a6ef47c057c04de7858",
    )
    FORMAT_EXAMPLE = f"""
    {{
        "parentHash": "{EXAMPLE_PARENT_HASH}",
        "sha3Uncles": "{to_hex(EMPTY_OMMERS_HASH)}",
        "coinbase": "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
        "stateRoot": "{EXAMPLE_STATE_ROOT}",
        "transactions": [],
        "receiptRoot": "{to_hex(EMPTY_TRIE_HASH)}",
        "logsBloom": "{to_hex(EMPTY_LOGS_BLOOM)}",
        "difficulty": 0,
        "blockNumber": "0x1",
        "gasLimit": "0x1c9c380",
        "gasUsed": "0x0",
        "timestamp": "0x5",
        "extraData": "0x",
        "random": "{to_hex(EMPTY_MIX_HASH)}",
        "nonce": "{to_hex(EMPTY_NONCE)}",
        "baseFeePerGas": "0x7",
        "blockHash": "{EXAMPLE_BLOCK_HASH}"
    }}
    """
    print("Usage:\n{} /path/to/block.json\n".format(sys.argv[0]))
    print("Json file format example:\n{}".format(FORMAT_EXAMPLE))


def main() -> None:
    if len(sys.argv) != 2:
        print_usage()
        raise Exception("Incorrect number of arguments")

    (_, block_json_path) = sys.argv

    block = None
    with open(block_json_path, "r") as f:
        block = json.load(f)

    pprint(block)
    block_hash = get_block_hash(block)
    print("header rlp = " + to_hex(get_header_rlp(block)))
    if can_get_block_rlp(block):
        print("block rlp = " + to_hex(get_block_rlp(block)))
    print("block hash = " + to_hex(block_hash))
    expected_hash = None

    if "blockHash" in block:
        expected_hash = block["blockHash"]
    elif "hash" in block:
        expected_hash = block["hash"]

    if expected_hash is not None:
        if type(expected_hash) == str and expected_hash.startswith("0x"):
            # Convert to bytes
            expected_hash = bytes.fromhex(expected_hash[2:])

        if not bytes_equal(block_hash, expected_hash):
            print(
                f"""
                Fail: Block hash is different than expected
                {to_hex(block_hash)} / {to_hex(expected_hash)}"""
            )
        else:
            print("Block hash is ok")
    if "rlp" in block and can_get_block_rlp(block):
        block_rlp = get_block_rlp(block)
        expected_rlp: str = block["rlp"]
        if expected_rlp.startswith("0x"):
            expected_rlp = expected_rlp[2:]
        if not bytes_equal(block_rlp, expected_rlp):
            print(
                f"""
                Fail: Block RLP is different than expected
                {to_hex(block_rlp)} / {to_hex(expected_rlp)}
                """
            )
        else:
            print("Block RLP is ok")


if __name__ == "__main__":
    main()
