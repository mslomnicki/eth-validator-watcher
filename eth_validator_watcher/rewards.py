"""Contains functions to handle rewards calculation"""

from .models import Rewards, SyncCommitteeRewardsResponse
from .watched_validators import WatchedValidators


def process_rewards(validators: WatchedValidators, rewards: Rewards) -> None:
    """Processes rewards for all validators."""
    ideal_by_eb: dict[int, Rewards.Data.IdealReward] = {}
    for ideal_reward in rewards.data.ideal_rewards:
        ideal_by_eb[ideal_reward.effective_balance] = ideal_reward

    for reward in rewards.data.total_rewards:
        validator = validators.get_validator_by_index(reward.validator_index)
        if not validator:
            continue

        ideal = ideal_by_eb.get(validator.effective_balance)
        if not ideal:
            continue

        validator.process_rewards(ideal, reward)


def process_sync_committee_rewards(
    validators: WatchedValidators, rewards: SyncCommitteeRewardsResponse
) -> None:
    """Processes sync committee rewards for all validators."""
    for reward_entry in rewards.data:
        validator = validators.get_validator_by_index(reward_entry.validator_index)
        if not validator:
            continue

        validator.process_sync_committee_reward(reward_entry.reward)
