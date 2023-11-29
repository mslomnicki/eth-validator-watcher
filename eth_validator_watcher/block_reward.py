import random

from prometheus_client import Counter
from eth_validator_watcher.beacon import Beacon
from eth_validator_watcher.models import Validators

our_block_reward_per_validator_count: Counter | None = None


def init_block_reward_per_validator_counters(our_labels: dict[str, dict[str, str]]) -> None:
    global our_block_reward_per_validator_count

    if len(our_labels) == 0 or our_block_reward_per_validator_count is not None:
        return

    labels = list(random.choice(list(our_labels.values())).keys())
    our_block_reward_per_validator_count = Counter(
        "our_block_reward_per_validator_count",
        "Our block reward per validator counter",
        labels)
    for labels_dict in our_labels.values():
        our_block_reward_per_validator_count.labels(**labels_dict)


def process_block_reward(beacon: Beacon,
                         slot: int,
                         index_to_validator: dict[int, Validators.DataItem.Validator],
                         our_labels: dict[str, dict[str, str]]) -> None:
    """Process block rewards for given block

    Parameters:
        beacon (Beacon): Beacon object
        slot (int): Slot number
        index_to_validator    : Dictionary with:
            key  : validator index
            value: validator data corresponding to the validator index
        our_labels : Pubkey to labels dictionary
    """
    if len(index_to_validator) == 0 or len(our_labels) == 0:
        return

    data = beacon.get_block_reward(slot).data
    reward = data.total
    proposer_index = data.proposer_index
    proposer_pubkey = index_to_validator[proposer_index].pubkey
    proposer_labels = our_labels[proposer_pubkey]
    our_block_reward_per_validator_count.labels(**proposer_labels).inc(reward)
