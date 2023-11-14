import json
from pathlib import Path

import requests_mock

from eth_validator_watcher.beacon import Beacon
from eth_validator_watcher.models import SyncCommittee
from tests.beacon import assets


def test_get_sync_committee():
    beacon_url = "http://beacon:5052"
    sync_committee_path = Path(assets.__file__).parent / "sync_committee.json"

    with sync_committee_path.open() as file_descriptor:
        sync_committee = json.load(file_descriptor)

    expected = SyncCommittee(
        data=SyncCommittee.Data(
            validators=[1, 2, 3, 4, 5, 6, 7, 8]
        )
    )

    with requests_mock.Mocker() as mock:
        mock.get(
            f"{beacon_url}/eth/v1/beacon/states/head/sync_committees?epoch=42",
            json=sync_committee,
        )
        beacon = Beacon(beacon_url)

        assert beacon.get_sync_committee(42) == expected
