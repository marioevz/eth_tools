#!/usr/bin/env python
import sys
import json


def print_usage():
    print("{} <Path to old test> <Name of the Test> <Fork>".format(sys.argv[0]))


if len(sys.argv) == 2 and sys.argv[1] == "-h":
    print_usage()
    sys.exit()
elif len(sys.argv) != 4:
    print_usage()
    raise Exception("Incorrect number of arguments")

(_, path_to_test, test_name, fork) = sys.argv

fork_pushback_block_count = {
    "Frontier": 0,
    "Homestead": 0,
    "Byzantium": 3000000,
    "Constantinople": 5000000,
    "MuirGlacier": 9000000,
    "Berlin": 9000000,
    "London": 9700000,
    "ArrowGlacier": 10700000,
}

if fork not in fork_pushback_block_count.keys():
    raise Exception("Invalid fork")


def calculateDifficulty(
    parent_diff,
    parent_timestamp,
    parent_uncle_hash,
    current_timestamp,
    current_block,
    fork,
):
    emptyOmmersHash = (
        "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
    )

    BLOCK_DIFF_FACTOR = 2048

    parent_uncle_count = parent_uncle_hash.lower() != emptyOmmersHash.lower()

    expected_diff = None

    if fork == "Frontier":
        expected_diff = (
            parent_diff
            + parent_diff
            // 2048
            * (1 if current_timestamp - parent_timestamp < 13 else -1)
            + int(2 ** ((current_block // 100000) - 2))
        )
    elif fork == "Homestead":
        expected_diff = (
            parent_diff
            + parent_diff
            // 2048
            * max(1 - (current_timestamp - parent_timestamp) // 10, -99)
            + int(2 ** ((current_block // 100000) - 2))
        )
    else:
        adj_factor = max(
            (2 if parent_uncle_count else 1)
            - ((current_timestamp - parent_timestamp) // 9),
            -99,
        )

        diff_minus_bomb = parent_diff + (parent_diff // BLOCK_DIFF_FACTOR) * adj_factor

        minimum_difficulty = 131072

        diff_minus_bomb = (
            minimum_difficulty
            if diff_minus_bomb < minimum_difficulty
            else diff_minus_bomb
        )

        periodCount = (current_block - fork_pushback_block_count[fork]) // 100000

        if periodCount > 0:
            bomb = int(2 ** (periodCount - 2))
        else:
            bomb = 0

        expected_diff = diff_minus_bomb + bomb
    return expected_diff


"""
Old Format:
{

    "DifficultyTest1" : {
		"parentTimestamp" : "0x028d214818",
		"parentDifficulty" : "0x6963001f28ba95c2",
		"parentUncles" : "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
		"currentTimestamp" : "0x028d214818",
		"currentBlockNumber" : "0x0186a0",
		"currentDifficulty" : "0x69702c7f2c9fad14"
	}, 
    ...
}

{
    "TestName": {
        "DifficultyTest1" : {
            "network" : "Berlin",
            "parentTimestamp": "0xa325b151",
            "parentDifficulty": "0x3d7463c8ec830cb1",
            "parentUncles": "0x00",
            "currentTimestamp": "0xa325b17f",
            "currentBlockNumber": "0x989be4",
            "currentDifficulty": "0x3d55a997080ccc2d"
        }
    }
}
"""

emptyOmmersHash = "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"

og_tests = None
with open(path_to_test, "r") as f:
    og_tests = json.load(f)

if not og_tests:
    raise Exception("Unable to read original tests")

new_tests = {}

for og_test in og_tests:
    if (
        "parentDifficulty" not in og_tests[og_test]
        or "parentUncles" not in og_tests[og_test]
        or "currentBlockNumber" not in og_tests[og_test]
        or "currentDifficulty" not in og_tests[og_test]
        or "parentTimestamp" not in og_tests[og_test]
        or "currentTimestamp" not in og_tests[og_test]
    ):
        raise Exception("Test case {} is incomplete".format(og_test))
    (
        parent_diff,
        parent_uncles_hash,
        current_block_number,
        current_diff,
        parent_timestamp,
        current_timestamp,
    ) = (
        og_tests[og_test]["parentDifficulty"],
        og_tests[og_test]["parentUncles"],
        og_tests[og_test]["currentBlockNumber"],
        og_tests[og_test]["currentDifficulty"],
        og_tests[og_test]["parentTimestamp"],
        og_tests[og_test]["currentTimestamp"],
    )
    parent_timestamp = int(parent_timestamp, 16)
    current_timestamp = int(current_timestamp, 16)
    new_test = {}
    new_test["network"] = fork
    new_test["parentTimestamp"] = hex(parent_timestamp)
    new_test["parentDifficulty"] = parent_diff
    new_test["parentUncles"] = (
        "0x00" if parent_uncles_hash.lower() == emptyOmmersHash.lower() else "0x01"
    )
    new_test["parentTimestamp"] = hex(parent_timestamp)

    new_test["currentBlockNumber"] = current_block_number

    if current_timestamp == parent_timestamp:
        # For some reason, the BasicTests had equal timestamps for parent and current, when they really meant it was a 1-second difference
        current_timestamp += 1
    else:
        if parent_timestamp > current_timestamp:
            raise Exception(
                "Invalid timestamp in test case {}, parent_timestamp={}, current_timestamp={}".format(
                    og_test, parent_timestamp, current_timestamp
                )
            )

    new_test["currentTimestamp"] = hex(current_timestamp)
    new_test["currentDifficulty"] = current_diff

    exp_diff = calculateDifficulty(
        int(parent_diff, 16),
        parent_timestamp,
        parent_uncles_hash,
        current_timestamp,
        int(current_block_number, 16),
        fork,
    )

    if int(current_diff, 16) != exp_diff:
        raise Exception(
            "Invalid calculated difficulty! exp={}, act={}".format(
                exp_diff, current_diff
            )
        )

    new_tests[og_test] = new_test

print(json.dumps({test_name: new_tests}, indent=4))
