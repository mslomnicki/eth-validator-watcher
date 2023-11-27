"""Contains function to handle next sync committees"""

import random

from prometheus_client import Gauge

from .beacon import Beacon
from .models import Validators
from .utils import NB_SYNC_COMMITTEE_EPOCHS

current_round_sync_committee_per_validator_count: Gauge | None = None
next_round_sync_committee_per_validator_count: Gauge | None = None


def init_sync_committee_per_validator_counters(our_labels: dict[str, dict[str, str]]) -> None:
    global current_round_sync_committee_per_validator_count
    global next_round_sync_committee_per_validator_count

    if len(our_labels) == 0 or current_round_sync_committee_per_validator_count is not None:
        return

    labels = list(random.choice(list(our_labels.values())).keys())
    current_round_sync_committee_per_validator_count = Gauge(
        "current_round_sync_committee_per_validator_count",
        "Validators in sync committee in current round",
        labels
    )
    next_round_sync_committee_per_validator_count = Gauge(
        "next_round_sync_committee_per_validator_count",
        "Validators in sync committee in next round",
        labels
    )
    for labels_dict in our_labels.values():
        current_round_sync_committee_per_validator_count.labels(**labels_dict)
        next_round_sync_committee_per_validator_count.labels(**labels_dict)


def process_sync_committee(
        beacon: Beacon,
        index_to_validator: dict[int, Validators.DataItem.Validator],
        epoch: int,
        our_labels: dict[str, dict[str, str]],
) -> None:
    """Handle sync committees

    Parameters:
    beacon      : Beacon
    index_to_validator    : Dictionary with:
            key  : validator index
            value: validator data corresponding to the validator index
    epoch        : Epoch
    is_new_epoch: Is new epoch
    our_labels : Validator nodes dictionaries
    """
    if len(our_labels) == 0 or current_round_sync_committee_per_validator_count is None:
        return

    sync_committee_current_round_idx = beacon.get_sync_committee(epoch).data.validators
    sync_committee_next_round_idx = beacon.get_sync_committee(epoch + NB_SYNC_COMMITTEE_EPOCHS).data.validators

    sync_committee_current_round_pubkeys = [
        index_to_validator[item].pubkey
        for item in sync_committee_current_round_idx
        if item in index_to_validator
    ]

    sync_committee_next_round_pubkeys = [
        index_to_validator[item].pubkey
        for item in sync_committee_next_round_idx
        if item in index_to_validator
    ]

    for labels in list(map(dict, set(tuple(sorted(d.items())) for d in our_labels.values()))):
        current_round_sync_committee_per_validator_count.labels(**labels).set(0)
        next_round_sync_committee_per_validator_count.labels(**labels).set(0)

    for pk in sync_committee_current_round_pubkeys:
        labels = our_labels[pk]
        current_round_sync_committee_per_validator_count.labels(**labels).inc()

    for pk in sync_committee_next_round_pubkeys:
        labels = our_labels[pk]
        next_round_sync_committee_per_validator_count.labels(**labels).inc()
