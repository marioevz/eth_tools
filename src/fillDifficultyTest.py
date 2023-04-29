#!/usr/bin/env python


fork_pushback_block_count = {
    "Byzantium": 3000000,
    "Constantinople": 5000000,
    "MuirGlacier": 9000000,
    "London": 9700000,
    "ArrowGlacier": 10700000,
}

emptyOmmersHash = "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
nonEmptyOmmersHash = (
    "0x2dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
)


def adj_factor(parent_uncles, delta_timestamp):
    return max((2 if parent_uncles else 1) - (delta_timestamp // 9), -99)


def periodCount(block_delta):
    return block_delta // 100000


def calcBomb(block_delta):
    return (
        0 if periodCount(block_delta) <= 0 else int(2 ** (periodCount(block_delta) - 2))
    )


BLOCK_DIFF_FACTOR = 2048


def diff_minus_bomb(parent_difficulty, adjustment_factor):
    return (
        parent_difficulty + (parent_difficulty // BLOCK_DIFF_FACTOR) * adjustment_factor
    )


def diff_minus_bomb_timestamp(parent_difficulty, parent_uncles, delta_timestamp):
    return diff_minus_bomb(
        parent_difficulty, adj_factor(parent_uncles, delta_timestamp)
    )


def calc_new_difficulty(parent_difficulty, parent_uncles, delta_timestamp, block_delta):
    return diff_minus_bomb_timestamp(
        parent_difficulty, parent_uncles, delta_timestamp
    ) + calcBomb(block_delta)


def unclesTimestampFromAdjustmentFactor(step, adjFactor):
    if adjFactor > 2 or adjFactor < -99:
        raise Exception("Invalid adjustment factor")
    timestampDelta = None
    uncles = None
    if adjFactor <= 0:
        step = (
            step % 18
        )  # For each adjustment Factor, there are 18 uncles/timestampDelta combinations that produce a certain adjustment factor
        timestampDelta = (
            ((adjFactor * -1) + 1) * 9
        ) + step  #  the range is 9 - 26, for adjFactor 0, 18 - 35 for adjFactor -1 and so on...
        uncles = (
            step >= 9
        )  # The lower half of timestamp delta range (0 - 9) is satisfied without the uncles, the upper half requires uncles to have the same adjFactor
    elif (
        adjFactor == 1
    ):  # For adjustment factor of 1, there are only 17 combinations (zero is excluded)
        timestampDelta = (step % 17) + 1
        uncles = timestampDelta >= 9
    elif (
        adjFactor == 2
    ):  # For adjustment factor of 1, there are only 8 combinations (zero is excluded)
        uncles = True  # For adjFactor two, uncles are always necessary
        timestampDelta = (step % 8) + 1
    return uncles, timestampDelta


def adjustmentFactorFromStep(step, adjFactorShares):
    adjFactorShares = adjFactorShares[1:-1].split(";")
    adjFactorShares = [tuple([int(y) for y in x.split(",")]) for x in adjFactorShares]
    totalShares = sum([x[1] for x in adjFactorShares])
    step = step % totalShares
    currentTotal = 0
    for adjFactor in adjFactorShares:
        currentTotal += adjFactor[1]
        if step < currentTotal:
            return adjFactor[0]
    return None


def unclesTimestampFromAdjustmentFactorShares(step, adjFactorShares):
    nextAdjFactor = adjustmentFactorFromStep(step, adjFactorShares)
    uncles, timestampDelta = unclesTimestampFromAdjustmentFactor(step, nextAdjFactor)
    return uncles, timestampDelta


def fillTestCase(testCase):
    parentTimestamp = testCase["startTimestamp"]
    parentDifficulty = testCase["startDifficutly"]
    retDict = {}
    parentBlock = None
    tc_count = 1

    if "comment" in testCase:
        retDict["_info"] = {"comment": testCase["comment"]}

    for br in testCase["blockRanges"]:
        startBlock = br["start"]
        endBlock = br["end"]
        stepBlocks = br["step"]
        if startBlock > endBlock:
            raise Exception("invalid start-end range")
        currentFork = br["network"]
        if currentFork not in fork_pushback_block_count:
            raise Exception("Invalid fork")
        currentPushbackBlocks = fork_pushback_block_count[currentFork]

        if not parentBlock:
            parentBlock = startBlock - 1

        while parentBlock < startBlock - 1:
            blockNum = parentBlock + 1
            block_delta = blockNum - currentPushbackBlocks
            uncles, timestampDelta = unclesTimestampFromAdjustmentFactorShares(
                blockNum, testCase["adjustmentFactor"]
            )
            parentDifficulty = hex(
                calc_new_difficulty(
                    int(parentDifficulty, 16), uncles, timestampDelta, block_delta
                )
            )
            parentTimestamp = hex(int(parentTimestamp, 16) + timestampDelta)

            parentBlock += 1

        for blockNum in range(startBlock, endBlock + 1):
            if parentBlock > blockNum:
                raise Exception("invalid range")

            block_delta = blockNum - currentPushbackBlocks
            uncles, timestampDelta = unclesTimestampFromAdjustmentFactorShares(
                blockNum, testCase["adjustmentFactor"]
            )
            currentDifficulty = hex(
                calc_new_difficulty(
                    int(parentDifficulty, 16), uncles, timestampDelta, block_delta
                )
            )
            currentTimestamp = hex(int(parentTimestamp, 16) + timestampDelta)

            if ((blockNum - startBlock) % stepBlocks) == 0:
                new_tc = {
                    "network": currentFork,
                    "currentBlockNumber": hex(blockNum),
                    "currentTimestamp": currentTimestamp,
                    "currentDifficulty": currentDifficulty,
                    "parentTimestamp": str(parentTimestamp),
                    "parentDifficulty": parentDifficulty,
                    "parentUncles": "0x01" if uncles else "0x00",
                }
                retDict["DifficultyTest{}".format(tc_count)] = new_tc
                tc_count += 1

            parentDifficulty = currentDifficulty
            parentTimestamp = currentTimestamp
            parentBlock = blockNum

    return retDict


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 3:
        raise Exception("Incorrect number of arguments")
    (_, tc_path, test_name) = sys.argv
    with open(tc_path, "r") as f:
        tc = json.load(f)
    print(json.dumps({"test_name": fillTestCase(tc)}, indent=4))
