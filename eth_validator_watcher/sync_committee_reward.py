import random

from prometheus_client import Counter
from eth_validator_watcher.beacon import Beacon, NoBlockError
from eth_validator_watcher.models import Validators

our_sync_committee_reward_per_validator_count: Counter | None = None


def init_sync_committee_reward_per_validator_counters(our_labels: dict[str, dict[str, str]]) -> None:
    global our_sync_committee_reward_per_validator_count

    if len(our_labels) == 0 or our_sync_committee_reward_per_validator_count is not None:
        return

    labels = list(random.choice(list(our_labels.values())).keys())
    our_sync_committee_reward_per_validator_count = Counter(
        "our_sync_committee_reward_per_validator_count",
        "Our sync committee reward per validator counter",
        labels)
    for labels_dict in our_labels.values():
        our_sync_committee_reward_per_validator_count.labels(**labels_dict)


def process_sync_committee_reward(beacon: Beacon,
                                  slot: int,
                                  index_to_validator: dict[int, Validators.DataItem.Validator],
                                  our_labels: dict[str, dict[str, str]]) -> None:
    """Process sync committee rewards for given block

    Parameters:
        beacon (Beacon): Beacon object
        slot (int): Slot number
        index_to_validator    : Dictionary with:
            key  : validator index
            value: validator data corresponding to the validator index
        our_labels : Validator nodes dictionaries
    """
    if len(index_to_validator) == 0 or len(our_labels) == 0:
        return

    try:
        data = beacon.get_sync_committee_reward(slot).data
        for val in data:
            if val.validator_index in index_to_validator:
                labels = our_labels[index_to_validator[val.validator_index].pubkey]
                our_sync_committee_reward_per_validator_count.labels(**labels).inc(val.reward)
    except NoBlockError:
        pass
