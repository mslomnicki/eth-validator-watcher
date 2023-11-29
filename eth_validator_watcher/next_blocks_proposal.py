"""Contains function to handle next blocks proposal"""

import functools
import random

from prometheus_client import Gauge, Counter

from .beacon import Beacon
from .relays import Relays
from .utils import NB_SLOT_PER_EPOCH

print = functools.partial(print, flush=True)

future_block_proposals_count = Gauge(
    "future_block_proposals_count",
    "Future block proposals count",
)

future_block_proposals_without_mev_relay_registration_per_validator_counter: Counter | None = None


def init_next_block_proposal_per_validator_counters(our_labels: dict[str, dict[str, str]]) -> None:
    global future_block_proposals_without_mev_relay_registration_per_validator_counter

    if len(our_labels) == 0 or future_block_proposals_without_mev_relay_registration_per_validator_counter is not None:
        return

    labels = list(random.choice(list(our_labels.values())).keys())
    future_block_proposals_without_mev_relay_registration_per_validator_counter = Gauge(
        "future_block_proposals_without_mev_relay_per_validator_count",
        "Future block proposals without MEV relay registration per validator counter",
        labels
    )
    for labels_dict in our_labels.values():
        future_block_proposals_without_mev_relay_registration_per_validator_counter.labels(**labels_dict)


def process_future_blocks_proposal(
    beacon: Beacon,
    our_pubkeys: set[str],
    slot: int,
    is_new_epoch: bool,
    relays: Relays,
    our_labels: dict[str, dict[str, str]],
) -> int:
    """Handle next blocks proposal

    Parameters:
    beacon      : Beacon
    our_pubkeys : Set of our validators public keys
    slot        : Slot
    is_new_epoch: Is new epoch
    relays      : MEV relays
    our_labels  : Pubkey to labels dictionary
    """
    epoch = slot // NB_SLOT_PER_EPOCH
    proposers_duties_current_epoch = beacon.get_proposer_duties(epoch)
    proposers_duties_next_epoch = beacon.get_proposer_duties(epoch + 1)

    concatenated_data = (
        proposers_duties_current_epoch.data + proposers_duties_next_epoch.data
    )

    filtered = [
        item
        for item in concatenated_data
        if item.pubkey in our_pubkeys and item.slot >= slot
    ]

    future_block_proposals_count.set(len(filtered))

    if is_new_epoch:
        for item in filtered:
            print(
                f"💍 Our validator {item.pubkey[:10]} is going to propose a block "
                f"at   slot {item.slot} (in {item.slot - slot} slots)"
            )

    if is_new_epoch and len(filtered) > 0 and len(our_labels) > 0:
        filtered_in_current_epoch = [
            item
            for item in proposers_duties_current_epoch.data
            if item.pubkey in our_pubkeys
        ]
        if len(filtered_in_current_epoch) > 0:
            slots_wo_relay = relays.check_validator_registration_for_slots(filtered_in_current_epoch)
            if len(slots_wo_relay) > 0:
                for item in slots_wo_relay:
                    labels = our_labels[item.pubkey]
                    future_block_proposals_without_mev_relay_registration_per_validator_counter.labels(**labels).inc()
                    print(
                        f"❗ Our validator {item.pubkey[:10]} is going to propose a block "
                        f"at   slot {item.slot} (in {item.slot - slot} slots) w/o registration to any MEV relay"
                    )

    return len(filtered)
