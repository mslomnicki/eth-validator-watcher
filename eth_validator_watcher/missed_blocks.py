"""Contains functions to handle missed block proposals detection on head"""

import functools
import random

from prometheus_client import Counter

from .beacon import Beacon, NoBlockError
from .models import Block, BlockIdentierType
from .utils import NB_SLOT_PER_EPOCH, Slack

print = functools.partial(print, flush=True)

missed_block_proposals_head_count = Counter(
    "missed_block_proposals_head_count",
    "Missed block proposals head count",
)

missed_block_proposals_head_count_details = Counter(
    "missed_block_proposals_head_count_details",
    "Missed block proposals head count details",
    ["slot", "epoch"],
)

missed_block_proposals_finalized_count = Counter(
    "missed_block_proposals_finalized_count",
    "Missed block proposals finalized count",
)

missed_block_proposals_finalized_count_details = Counter(
    "missed_block_proposals_finalized_count_details",
    "Missed block proposals finalized count details",
    ["slot", "epoch"],
)

our_block_processed_head_per_validator_count: Counter | None = None
our_block_processed_finalized_per_validator_count: Counter | None = None
our_missed_block_proposals_head_per_validator_count: Counter | None = None
our_missed_block_proposals_finalized_per_validator_count: Counter | None = None


def init_blocks_per_validator_counters(our_labels: dict[str, dict[str, str]]) -> None:
    global our_block_processed_head_per_validator_count
    global our_block_processed_finalized_per_validator_count
    global our_missed_block_proposals_head_per_validator_count
    global our_missed_block_proposals_finalized_per_validator_count

    if len(our_labels) == 0 or our_block_processed_head_per_validator_count is not None:
        return

    labels = list(random.choice(list(our_labels.values())).keys())
    our_block_processed_head_per_validator_count = Counter(
        "our_block_processed_head_per_validator_count",
        "Our processed block proposals per validator (head)",
        labels)
    our_block_processed_finalized_per_validator_count = Counter(
        "our_block_processed_finalized_per_validator_count",
        "Our processed block proposals per validator (finalized)",
        labels)
    our_missed_block_proposals_head_per_validator_count = Counter(
        "our_missed_block_proposals_head_per_validator_count",
        "Our missed block proposals per validator (head)",
        labels)
    our_missed_block_proposals_finalized_per_validator_count = Counter(
        "our_missed_block_proposals_finalized_per_validator_count",
        "Our missed block proposals per validator (finalized)",
        labels)
    for labels_dict in our_labels.values():
        our_block_processed_head_per_validator_count.labels(**labels_dict)
        our_block_processed_finalized_per_validator_count.labels(**labels_dict)
        our_missed_block_proposals_head_per_validator_count.labels(**labels_dict)
        our_missed_block_proposals_finalized_per_validator_count.labels(**labels_dict)


def process_missed_blocks_head(
        beacon: Beacon,
        potential_block: Block | None,
        slot: int,
        our_pubkeys: set[str],
        our_labels: dict[str, dict[str, str]],
        slack: Slack | None,
) -> bool:
    """Process missed block proposals detection at head

    Parameters:
    beacon         : Beacon
    potential_block: Potential block
    slot           : Slot
    our_pubkeys    : Set of our validators public keys
    slack          : Slack instance

    Returns `True` if we had to propose the block, `False` otherwise
    """
    missed = potential_block is None
    epoch = slot // NB_SLOT_PER_EPOCH
    proposer_duties = beacon.get_proposer_duties(epoch)

    # Get proposer public key for this slot
    proposer_duties_data = proposer_duties.data

    # In `data` list, items seem to be ordered by slot.
    # However, there is no specification for that, so it is wiser to
    # iterate on the list
    proposer_pubkey = next(
        (
            proposer_duty_data.pubkey
            for proposer_duty_data in proposer_duties_data
            if proposer_duty_data.slot == slot
        )
    )

    # Check if the validator that has to propose is ours
    is_our_validator = proposer_pubkey in our_pubkeys
    positive_emoji = "✨" if is_our_validator else "✅"
    negative_emoji = "🔺" if is_our_validator else "💩"

    emoji, proposed_or_missed = (
        (negative_emoji, "missed  ") if missed else (positive_emoji, "proposed")
    )

    short_proposer_pubkey = proposer_pubkey[:10]

    message_console = (
        f"{emoji} {'Our ' if is_our_validator else '    '}validator "
        f"{short_proposer_pubkey} {proposed_or_missed} block at head at epoch {epoch} "
        f"- slot {slot} {emoji} - 🔑 {len(our_pubkeys)} keys "
        "watched"
    )

    print(message_console)

    if slack is not None and missed and is_our_validator:
        message_slack = (
            f"{emoji} {'Our ' if is_our_validator else '    '}validator "
            f"`{short_proposer_pubkey}` {proposed_or_missed} block at head at epoch "
            f"`{epoch}` - slot `{slot}` {emoji}"
        )

        slack.send_message(message_slack)

    if is_our_validator and missed:
        missed_block_proposals_head_count.inc()
        missed_block_proposals_head_count_details.labels(slot=slot, epoch=epoch).inc()

    if is_our_validator and our_missed_block_proposals_head_per_validator_count is not None:
        labels = our_labels[proposer_pubkey]
        (our_missed_block_proposals_head_per_validator_count
         if missed
         else our_block_processed_head_per_validator_count
         ).labels(**labels).inc()
    return is_our_validator


def process_missed_blocks_finalized(
        beacon: Beacon,
        last_processed_finalized_slot: int,
        slot: int,
        our_pubkeys: set[str],
        our_labels: dict[str, dict[str, str]],
        slack: Slack | None,
) -> int:
    """Process missed block proposals detection at finalized

    Parameters:
    beacon         : Beacon
    potential_block: Potential block
    slot           : Slot
    our_pubkeys    : Set of our validators public keys
    slack          : Slack instance

    Returns the last finalized slot
    """
    assert last_processed_finalized_slot <= slot, "Last processed finalized slot > slot"

    last_finalized_header = beacon.get_header(BlockIdentierType.FINALIZED)
    last_finalized_slot = last_finalized_header.data.header.message.slot
    epoch_of_last_finalized_slot = last_finalized_slot // NB_SLOT_PER_EPOCH

    # Only to memoize it, in case of the BN does not serve this request for too old
    # epochs
    beacon.get_proposer_duties(epoch_of_last_finalized_slot)

    for slot_ in range(last_processed_finalized_slot + 1, last_finalized_slot + 1):
        epoch = slot_ // NB_SLOT_PER_EPOCH
        proposer_duties = beacon.get_proposer_duties(epoch)

        # Get proposer public key for this slot
        proposer_duties_data = proposer_duties.data

        # In `data` list, items seem to be ordered by slot.
        # However, there is no specification for that, so it is wiser to
        # iterate on the list
        proposer_pubkey = next(
            (
                proposer_duty_data.pubkey
                for proposer_duty_data in proposer_duties_data
                if proposer_duty_data.slot == slot_
            )
        )

        # Check if the validator that has to propose is ours
        is_our_validator = proposer_pubkey in our_pubkeys

        if not is_our_validator:
            continue

        # Check if the block has been proposed
        try:
            beacon.get_header(slot_)
            if our_block_processed_finalized_per_validator_count is not None:
                our_block_processed_finalized_per_validator_count.labels(**our_labels[proposer_pubkey]).inc()
        except NoBlockError:
            short_proposer_pubkey = proposer_pubkey[:10]

            message_console = (
                f"❌ Our validator {short_proposer_pubkey} missed block at finalized "
                f"at epoch {epoch} - slot {slot_} ❌"
            )

            print(message_console)

            if slack is not None:
                message_slack = (
                    f"❌ Our validator `{short_proposer_pubkey}` missed block at "
                    f"finalized at epoch {epoch}` - slot `{slot_}` ❌"
                )

                slack.send_message(message_slack)

            missed_block_proposals_finalized_count.inc()

            missed_block_proposals_finalized_count_details.labels(
                slot=slot_, epoch=epoch
            ).inc()

            if our_missed_block_proposals_finalized_per_validator_count is not None:
                our_missed_block_proposals_finalized_per_validator_count.labels(**our_labels[proposer_pubkey]).inc()
    return last_finalized_slot
