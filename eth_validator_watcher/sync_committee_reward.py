import random

from prometheus_client import Counter
from eth_validator_watcher.beacon import Beacon, NoBlockError
from eth_validator_watcher.models import Validators

our_pos_sync_committee_reward_per_validator_count: Counter | None = None
our_neg_sync_committee_reward_per_validator_count: Counter | None = None


def init_sync_committee_reward_per_validator_counters(our_labels: dict[str, dict[str, str]]) -> None:
    global our_pos_sync_committee_reward_per_validator_count
    global our_neg_sync_committee_reward_per_validator_count

    if len(our_labels) == 0 or our_pos_sync_committee_reward_per_validator_count is not None:
        return

    labels = list(random.choice(list(our_labels.values())).keys())
    our_pos_sync_committee_reward_per_validator_count = Counter(
        "our_pos_sync_committee_reward_per_validator_count",
        "Our positive sync committee reward per validator counter",
        labels)
    our_neg_sync_committee_reward_per_validator_count = Counter(
        "our_neg_sync_committee_reward_per_validator_count",
        "Our negative sync committee reward per validator counter",
        labels)
    for labels_dict in our_labels.values():
        our_pos_sync_committee_reward_per_validator_count.labels(**labels_dict)
        our_neg_sync_committee_reward_per_validator_count.labels(**labels_dict)


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
                (our_pos_sync_committee_reward_per_validator_count
                 if val.reward >= 0
                 else our_neg_sync_committee_reward_per_validator_count
                 ).labels(**labels).inc(abs(val.reward))
    except NoBlockError:
        pass
