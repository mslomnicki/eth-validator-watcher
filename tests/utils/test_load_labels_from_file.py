from pathlib import Path

from eth_validator_watcher.utils import load_labels_from_file
from tests.utils import assets


def test_load_labels_from_file():
    labels_path = Path(assets.__file__).parent / "labels.csv"
    expected = {
        "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {
            "validator_pubkey": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "machine": "ma",
            "mevb_status": "mevb_no",
            "location": "site_a"
        },
        "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": {
            "validator_pubkey": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "machine": "mb",
            "mevb_status": "mevb_yes",
            "location": "site_b"
        },
        "0xcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc": {
            "validator_pubkey": "0xcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "machine": "mc",
            "mevb_status": "mevb_yes",
            "location": "site_c"
        },
        "0xdddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd": {
            "validator_pubkey": "0xdddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
            "machine": "mc",
            "mevb_status": "mevb_yes",
            "location": "site_c"
        },
    }
    assert load_labels_from_file(labels_path, False) == expected


def test_load_labels_from_file_with_pubkey_removed():
    labels_path = Path(assets.__file__).parent / "labels.csv"
    expected = {
        "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa": {
            "machine": "ma",
            "mevb_status": "mevb_no",
            "location": "site_a"
        },
        "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": {
            "machine": "mb",
            "mevb_status": "mevb_yes",
            "location": "site_b"
        },
        "0xcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc": {
            "machine": "mc",
            "mevb_status": "mevb_yes",
            "location": "site_c"
        },
        "0xdddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd": {
            "machine": "mc",
            "mevb_status": "mevb_yes",
            "location": "site_c"
        },
    }
    assert load_labels_from_file(labels_path, True) == expected
