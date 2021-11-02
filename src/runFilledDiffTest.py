#!/usr/bin/env python
import sys
import json
import os
import pprint
import subprocess

# Constants
fork_activation_blocks = {
    'Byzantium': 4370000,
    'Constantinople': 7280000,
    'MuirGlacier': 9200000,
    'London': 12965000,
    'ArrowGlacier': 13773000
}

fork_pushback_block_count = {
    'Byzantium': 3000000,
    'Constantinople': 5000000,
    'MuirGlacier': 9000000,
    'Berlin': 9000000,
    'London': 9700000,
    'ArrowGlacier': 10700000
}

BLOCK_DIFF_FACTOR = 2048

# Start

def print_usage():
    print('Usage:\n{} /path/to/FilledTest.json'.format(sys.argv[0]))

if len(sys.argv) != 2:
    print_usage()
    raise Exception('Incorrect number of arguments')

(_, filled_test_path) = sys.argv

filled_test = {}
if not os.path.exists(filled_test_path):
    raise Exception('File not found!')

with open(filled_test_path, 'r') as f:
    filled_test = json.load(f)

test_count = 0
failing_count = 0
passing_count = 0
expected_diff_count = 0

err = False

for test_name in filled_test.keys():

    for tc in filled_test[test_name]:
        
        if tc == '_info':
            continue
        test_count += 1
        tc = filled_test[test_name][tc]
        block = tc["currentBlockNumber"]
        tc_difficulty = tc["currentDifficulty"]
        timestamp = tc["currentTimestamp"]
        fork = tc["network"]
        if not fork in fork_pushback_block_count:
            raise Exception('Incorrect fork')
        parent_diff = tc["parentDifficulty"]
        parent_timestamp = tc["parentTimestamp"]
        parent_uncle_count = tc["parentUncles"]

        if parent_diff.startswith('0x'):
            parent_diff = int(parent_diff, 16)
        else:
            parent_diff = int(parent_diff)

        if parent_uncle_count.startswith('0x'):
            parent_uncle_count = int(parent_uncle_count, 16)
        else:
            parent_uncle_count = int(parent_uncle_count)

        if parent_timestamp.startswith('0x'):
            parent_timestamp = int(parent_timestamp, 16)
        else:
            parent_timestamp = int(parent_timestamp)

        if timestamp.startswith('0x'):
            timestamp = int(timestamp, 16)
        else:
            timestamp = int(timestamp)

        if block.startswith('0x'):
            block = int(block, 16)
        else:
            block = int(block)
        
        if tc_difficulty.startswith('0x'):
            tc_difficulty = int(tc_difficulty, 16)
        else:
            tc_difficulty = int(tc_difficulty)
        
        emptyOmmersHash =    "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
        nonEmptyOmmersHash = "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49348"

        # parent_uncle_count = hex(parent_uncle_hash).lower() != emptyOmmersHash.lower()

        parent_uncle_hash = nonEmptyOmmersHash if parent_uncle_count else emptyOmmersHash

        adj_factor = max((2 if parent_uncle_count else 1) - ((timestamp - parent_timestamp) // 9), -99)

        diff_minus_bomb = (parent_diff + (parent_diff // BLOCK_DIFF_FACTOR) * adj_factor)

        minimum_difficulty = 131072

        diff_minus_bomb = minimum_difficulty if diff_minus_bomb < minimum_difficulty else diff_minus_bomb

        periodCount = (block - fork_pushback_block_count[fork]) // 100000

        if periodCount > 0:
            bomb = int(2 ** (periodCount - 2))
        else:
            bomb = 0

        expected_diff = diff_minus_bomb + bomb

        if expected_diff != tc_difficulty:
            failing_count += 1
            expected_diff_count += 1
            print("TC {} Fail: Expected difficulty is different from actual difficulty in test case (expected={} / test case={})".format(tc, hex(expected_diff), hex(tc_difficulty)))
            pprint.pprint(tc)
            pprint.pprint({
                "currentNumber": str(block),
                "currentTimestamp": str(timestamp),
                "currentDifficulty": hex(tc_difficulty),
                "parentTimestamp" : str(parent_timestamp),
                "parentDifficulty" : hex(parent_diff),
                "parentUncleHash": parent_uncle_hash,
                "adjustmentFactor": adj_factor,
                "difficultyMinusBomb": hex(diff_minus_bomb),
                "periodCount": periodCount,
                "bomb": bomb,
            })
            err = True

        alloc = {
        "a94f5374fce5edbc8e2a8697c15331677e6ebf0b": {
            "balance": "0x5ffd4878be161d74",
            "code": "0x",
            "nonce": "0xac",
            "storage": {}
        },
        "0x8a8eafb1cf62bfbeb1741769dae1a9dd47996192":{
            "balance": "0xfeedbead",
            "nonce" : "0x00"
        }
        }

        txs = []

        env = {
        "currentCoinbase": "0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b",
        "currentGasLimit": "0x750a163df65e8a",
        "currentBaseFee": "0x500",
        "currentNumber": str(block),
        "currentTimestamp": str(timestamp),
        "parentTimestamp" : str(parent_timestamp),
        "parentDifficulty" : hex(parent_diff),
        "parentUncleHash": parent_uncle_hash
        }

        env_out_path = '/dev/shm/env.json'
        alloc_out_path = '/dev/shm/alloc.json'
        txs_out_path = '/dev/shm/txs.json'
        output_path = '/dev/shm/out.json'

        with open(env_out_path, 'w') as f:
            json.dump(env, f)
        with open(alloc_out_path, 'w') as f:
            json.dump(alloc, f)
        with open(txs_out_path, 'w') as f:
            json.dump(txs, f)

        if os.path.exists(output_path):
            os.remove(output_path)

        proc_output = subprocess.DEVNULL
        proc_err = subprocess.DEVNULL
        if err:
            proc_output = None
            proc_err = None

        # Run EVM
        command = ['evm', 't8n', 
                    '--input.alloc='+alloc_out_path,
                    '--input.txs='+txs_out_path,
                    '--input.env='+env_out_path,
                    '--output.result='+output_path,
                    '--state.fork='+fork
                ]
        if err:
            print(command)
        subprocess.call(command, stdout=proc_output, stderr=proc_err)

        data = {}
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                data = json.load(f)

        if not 'currentDifficulty' in data:
            raise Exception('Difficulty not returned')

        if int(data['currentDifficulty'], 16) == expected_diff:
            passing_count += 1
        else:
            failing_count += 1
            print('Verification FAIL: Expected {}, Received {}'.format(hex(expected_diff), data['currentDifficulty']))
        
        if err:
            sys.exit()
        
if failing_count > 0 or passing_count < test_count:
    print("Verification FAIL: One or more test cases failed, f={} (exp={},other={}), p={}, t={}".format(failing_count, expected_diff_count, failing_count - expected_diff_count, passing_count, test_count))
else:
    print("Verification OK: All test cases succeeded")