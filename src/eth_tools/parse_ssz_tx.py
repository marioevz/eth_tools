#!/usr/bin/env python
import sys

from Crypto.Hash import keccak
from eth2spec.utils.ssz.ssz_typing import (
    ByteList,
    Bytes20,
    Bytes32,
    Container,
    List,
    Union,
    uint8,
    uint64,
    uint256,
)
from eth_keys.backends.native.ecdsa import ecdsa_raw_recover
from eth_keys.datatypes import PublicKey


def print_usage():
    print("Usage:\n{} <SSZ Transaction Hex>\n".format(sys.argv[0]))
    exit()


# Constants

MAX_CALLDATA_SIZE = 1 << 24
MAX_ACCESS_LIST_SIZE = 1 << 24
MAX_ACCESS_LIST_STORAGE_KEYS = 1 << 24
MAX_VERSIONED_HASHES_LIST_SIZE = 1 << 24


# Types


class ECDSASignature(Container):
    v: uint8
    r: uint256
    s: uint256


class AccessTuple(Container):
    Address: Bytes20
    StorageKeys: List[Bytes32, MAX_ACCESS_LIST_STORAGE_KEYS]


class Type3TxMessage(Container):
    ChainID: uint256
    Nonce: uint64
    GasTipCap: uint256
    GasFeeCap: uint256
    Gas: uint64
    To: Union[None, Bytes20]
    Value: uint256
    Data: ByteList[MAX_CALLDATA_SIZE]
    AccessList: List[AccessTuple, MAX_ACCESS_LIST_SIZE]
    MaxFeePerDataGas: uint256
    BlobVersionedHashes: List[Bytes32, MAX_VERSIONED_HASHES_LIST_SIZE]


class SignedType3Tx(Container):
    Message: Type3TxMessage
    Signature: ECDSASignature


BLOB_TX_TYPE = bytes([3])


def main() -> None:
    if len(sys.argv) != 2:
        print_usage()

    (_, ssz_hex) = sys.argv

    if ssz_hex.startswith("0x"):
        ssz_hex = ssz_hex[2:]
    ssz_bytes = bytes.fromhex(ssz_hex)

    if len(ssz_bytes) < 1:
        raise Exception("Invalid SSZ length: empty")

    tx_type, ssz_bytes = ssz_bytes[0], ssz_bytes[1:]
    tx = SignedType3Tx.decode_bytes(ssz_bytes)
    print("Signed Transaction", tx)

    # This will change with https://eips.ethereum.org/EIPS/eip-6493
    messageHash = keccak.new(
        data=BLOB_TX_TYPE + tx.Message.encode_bytes(), digest_bits=256
    ).digest()

    print("Signing Message Hash", messageHash.hex())

    pk = PublicKey(
        ecdsa_raw_recover(
            bytes(messageHash),
            (int(tx.Signature.v), int(tx.Signature.r), int(tx.Signature.s)),
        )
    )
    print("Recovered Address", "0x" + pk.to_canonical_address().hex())
