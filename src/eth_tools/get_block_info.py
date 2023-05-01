#!/usr/bin/env python
import json
import sys
from pprint import pprint

import rlp
from Crypto.Hash import keccak

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
    print("Usage:\n{} /path/to/block.json\n".format(sys.argv[0]))
    print("Json file format example:\n{}".format(format_example))


def main() -> None:
    if len(sys.argv) != 2:
        print_usage()
        raise Exception("Incorrect number of arguments")

    (_, block_json_path) = sys.argv

    emptyTrieHash = "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
    emptyOmmersHash = (
        "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
    )

    block = None
    with open(block_json_path, "r") as f:
        block = json.load(f)

    def format_value_for_rlp(k, v):
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
        optional_fields = (
            "baseFeePerGas",
            "withdrawals/withdrawalsRoot",
            "excessDataGas",
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
            if block["transactionsTrie"] != emptyTrieHash:
                raise Exception(
                    "Cannot get the block rlp without the actual transactions"
                )
        rlp_array.append(txs_rlp_array)

        ommers_rlp_array = []
        if "ommmers" in block:
            for om in block["ommmers"]:
                ommers_rlp_array.append(format_value_for_rlp("ommer", om))
        elif "ommersHash" in block:
            if block["ommersHash"] != emptyOmmersHash:
                raise Exception("Cannot get the block rlp without the actual ommers")
        elif "sha3Uncles" in block:
            if block["sha3Uncles"] != emptyOmmersHash:
                raise Exception("Cannot get the block rlp without the actual ommers")
        elif "uncleHash" in block:
            if block["uncleHash"] != emptyOmmersHash:
                raise Exception("Cannot get the block rlp without the actual ommers")
        rlp_array.append(ommers_rlp_array)

        return rlp.encode(rlp_array)

    def can_get_block_rlp(block: dict) -> bool:
        return (
            "transactions" in block
            or (
                "transactionsTrie" in block
                and block["transactionsTrie"] == emptyTrieHash
            )
        ) and (
            "ommers" in block
            or ("ommersHash" in block and block["ommersHash"] == emptyOmmersHash)
            or ("sha3Uncles" in block and block["sha3Uncles"] == emptyOmmersHash)
            or ("uncleHash" in block and block["uncleHash"] == emptyOmmersHash)
        )

    def get_block_hash(block: dict) -> bytes:
        rlp = get_header_rlp(block)
        return keccak.new(data=rlp, digest_bits=256).digest()

    pprint(block)
    block_hash = get_block_hash(block)
    print("header rlp = " + get_header_rlp(block).hex())
    if can_get_block_rlp(block):
        print("block rlp = " + get_block_rlp(block).hex())
    print("block hash = " + block_hash.hex())
    expected_hash = None
    if "blockHash" in block:
        expected_hash = block["blockHash"]
    elif "hash" in block:
        expected_hash = block["hash"]
    if expected_hash is not None:
        if block_hash.hex() != expected_hash:
            print(
                f"Fail: Block hash is different than expected {block_hash.hex()} / {expected_hash}"
            )
        else:
            print("Block hash is ok")
    if "rlp" in block and can_get_block_rlp(block):
        block_rlp = get_block_rlp(block)
        expected_rlp: str = block["rlp"]
        if expected_rlp.startswith("0x"):
            expected_rlp = expected_rlp[2:]
        if block_rlp.hex() != expected_rlp:
            print(
                f"Fail: Block RLP is different than expected {block_rlp.hex()} / {expected_rlp}"
            )
        else:
            print("Block RLP is ok")