import json
from pathlib import Path

import requests_mock

from pytest import raises
from requests import HTTPError
from eth_validator_watcher.beacon import Beacon, NoBlockError
from eth_validator_watcher.models import SyncCommitteeReward
from tests.beacon import assets


def test_get_sync_committee_reward():
    beacon_url = "http://beacon:5052"
    sync_committee_reward_path = Path(assets.__file__).parent / "sync_committee_rewards.json"

    with sync_committee_reward_path.open() as file_descriptor:
        sync_committee_reward = json.load(file_descriptor)

    expected = SyncCommitteeReward(
        data=[
            SyncCommitteeReward.Data(
                validator_index=42,
                reward=123,
            ),
            SyncCommitteeReward.Data(
                validator_index=24,
                reward=321,
            ),
        ]
    )

    with requests_mock.Mocker() as mock:
        mock.post(
            f"{beacon_url}/eth/v1/beacon/rewards/sync_committee/42",
            json=sync_committee_reward,
        )
        beacon = Beacon(beacon_url)

        assert beacon.get_sync_committee_reward(42) == expected


def test_get_sync_committee_reward_slot_not_found():
    beacon_url = "http://beacon:5052"

    with requests_mock.Mocker() as mock:
        mock.post(
            f"{beacon_url}/eth/v1/beacon/rewards/sync_committee/42",
            status_code=404,
            text='{"message":"Could not find requested block: %ssigned beacon block can''t be nil","code":404}',
        )
        beacon = Beacon(beacon_url)

        with raises(NoBlockError):
            beacon.get_sync_committee_reward(42)


def test_get_sync_committee_reward_slot_beacon_error():
    beacon_url = "http://beacon:5052"

    with requests_mock.Mocker() as mock:
        mock.post(
            f"{beacon_url}/eth/v1/beacon/rewards/sync_committee/42",
            status_code=500,
        )
        beacon = Beacon(beacon_url)

        with raises(HTTPError):
            beacon.get_sync_committee_reward(42)
