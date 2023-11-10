import json
from pathlib import Path

import requests_mock

from eth_validator_watcher.beacon import Beacon
from eth_validator_watcher.models import BlockReward
from tests.beacon import assets


def test_get_block_reward():
    beacon_url = "http://beacon:5052"
    block_reward_path = Path(assets.__file__).parent / "block_reward.json"

    with block_reward_path.open() as file_descriptor:
        block_reward = json.load(file_descriptor)

    expected = BlockReward(
        data=BlockReward.Data(
            proposer_index=718836,
            total=41915528,
        )
    )

    with requests_mock.Mocker() as mock:
        mock.get(
            f"{beacon_url}/eth/v1/beacon/rewards/blocks/42",
            json=block_reward,
        )
        beacon = Beacon(beacon_url)

        assert beacon.get_block_reward(42) == expected
