#!/usr/bin/env python
import sys
import json
import os

def print_usage():
    print('{} <Parent difficulty> <Parent Uncle Count> <Parent Timestamp> <Timestamp> <Block> <Fork>'.format(sys.argv[0]))

if len(sys.argv) == 2 and sys.argv[1] == '-h':
    print_usage()
    sys.exit()
elif len(sys.argv) != 7:
    print_usage()
    raise Exception('Incorrect number of arguments')

(_, parent_diff, parent_uncle_count, parent_timestamp, timestamp, block, fork) = sys.argv

diff_forks = ['Byzantium', 'Constantinople', 'MuirGlacier', 'London', 'ArrowGlacier']

if not fork in diff_forks:
    raise Exception('Incorrect fork')

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

print(parent_diff, parent_uncle_count, parent_timestamp, timestamp, block, fork)

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
    'London': 9700000,
    'ArrowGlacier': 10700000
}

BLOCK_DIFF_FACTOR = 2048

adj_factor = max((2 if parent_uncle_count else 1) - ((timestamp - parent_timestamp) // 9), -99)

diff_minus_bomb = (parent_diff +
            (parent_diff // BLOCK_DIFF_FACTOR) * adj_factor
        )

minimum_difficulty = 131072

diff_minus_bomb = minimum_difficulty if diff_minus_bomb < minimum_difficulty else diff_minus_bomb

periodCount = (block - fork_pushback_block_count[fork]) // 100000

if periodCount > 0:
    bomb = int(2 ** (periodCount - 2))
else:
    bomb = 0

expected_diff = diff_minus_bomb + bomb

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

emptyOmmersHash =    "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
nonEmptyOmmersHash = "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49348"

env = {
  "currentCoinbase": "0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b",
  "currentGasLimit": "0x750a163df65e8a",
  "currentBaseFee": "0x500",
  "currentNumber": str(block),
  "currentTimestamp": str(timestamp),
  "parentTimestamp" : str(parent_timestamp),
  "parentDifficulty" : hex(parent_diff),
  "parentUncleHash": nonEmptyOmmersHash if parent_uncle_count else emptyOmmersHash
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


# Run EVM
stream = os.popen('evm t8n --input.alloc={} --input.txs={} --input.env={} --output.result={} --state.fork={}'.format(alloc_out_path, txs_out_path, env_out_path, output_path, fork))
output = stream.read()

data = {}
if os.path.exists(output_path):
    with open(output_path, 'r') as f:
        data = json.load(f)
print(data)

if not 'currentDifficulty' in data:
    raise Exception('Difficulty not returned')

if int(data['currentDifficulty'], 16) == expected_diff:
    print('Verification OK')
else:
    print('Verification FAIL: Expected {}'.format(hex(expected_diff)))