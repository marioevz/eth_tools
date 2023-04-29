#!/usr/bin/env python
# Rename container ids in hive --docker.output to make it much more readable.
import fileinput
import re

lines = [x for x in fileinput.input()]

client_tags = ["⚫", "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤"]
sim_tags = ["⬜", "🟥", "🟧", "🟨", "🟩", "🟦", "🟪", "🟫"]
client_start_matches = {
    "Geth": r"\[([a-f0-9]{8})\] Running go-ethereum with flags .*",
    "Neth": r"\[([a-f0-9]{8})\] Running Nethermind\.\.\.",
    "Erigon": r"\[([a-f0-9]{8})\] Running erigon with flags .*",
    "Besu": r"\[([a-f0-9]{8})\] starting main client: /opt/besu/bin/besu",
    "EthJS": r"\[([a-f0-9]{8})\] Running ethereumjs with flags .*",
    "LH BN": r"\[([a-f0-9]{8})\] .* INFO Beacon chain initialized",
    "LH VC": r"\[([a-f0-9]{8})\] .* INFO Starting validator client",
    "Teku BN": r"\[([a-f0-9]{8})\] Starting Teku Beacon Node",
    "Teku VC": r"\[([a-f0-9]{8})\] Starting Teku Validator Client",
    "LS BN": r"\[([a-f0-9]{8})\] Starting Lodestar Beacon Node",
    "LS VC": r"\[([a-f0-9]{8})\] Starting Lodestar Validator Client",
    "Nimbus BN": r"\[([a-f0-9]{8})\] Starting Nimbus Beacon Node",
    "Nimbus VC": r"\[([a-f0-9]{8})\] Starting Nimbus Validator Client",
}
client_count = {}
substitutions = []

for line in lines:
    matches = {k: re.match(client_start_matches[k], line) for k in client_start_matches}
    if any(matches.values()):
        m = next((k, matches[k]) for k in matches if matches[k] is not None)
        sub_text = m[1].group(1)
        client = m[0]

        if client in client_count:
            client_index = client_count[client]
            client_count[client] += 1
        else:
            client_index = 0
            client_count[client] = 1

        if not substitutions:
            emoji = client_tags.pop(0)
        else:
            emoji = client_tags[len(substitutions) % len(client_tags)]

        client_str = f"{client:<6} {client_index:02d} {emoji}"
        substitutions.append((sub_text, client_str))

for i, line in enumerate(lines):
    for s in substitutions:
        if s[0] in line:
            lines[i] = line.replace(s[0], s[1])

substitutions = []

# Remaining is the simulator
for line in lines:
    m = re.match(r"\[([a-f0-9]{8})\]", line)
    if m:
        sub_text = m.group(1)
        if sub_text not in [x[0] for x in substitutions]:
            emoji = sim_tags[len(substitutions) % len(sim_tags)]
            client_str = f"{'Sim':<6} {len(substitutions):02d} {emoji}"
            substitutions.append((sub_text, client_str))

for line in lines:
    for s in substitutions:
        if s[0] in line:
            line = line.replace(s[0], s[1])
    print(line, end="")
