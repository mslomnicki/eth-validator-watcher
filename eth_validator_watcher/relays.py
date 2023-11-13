"""Contains the Relays class which is used to interact with the relays."""

from time import sleep
import random

from prometheus_client import Counter
from requests import Session, codes
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import ConnectionError

from eth_validator_watcher.models import ProposerPayloadDelivered

MAX_TRIALS = 5
WAIT_SEC = 0.5
RELAY_KEY = "mev_relay"
RELAY_MAPPING: dict[str, str] = {
    "https://0xa1559ace749633b997cb3fdacffb890aeebdb0f5a3b6aaa7eeeaf1a38af0a8fe88b9e4b1f61f236d2e64d95733327a62@relay.ultrasound.money": "ultra sound",
    "https://0x8b5d2e73e2a3a55c6c87b8b6eb92e0149a125c852751db1422fa951e42a09b82c142c3ea98d0d9930b056a3bc9896b8f@bloxroute.max-profit.blxrbdn.com": "BloXroute [Max-Profit]",
}

bad_relay_count = Counter(
    "bad_relay_count",
    "Bad relay count",
)

our_mev_boost_reward_per_validator_count: Counter | None = None


def init_relays_per_validator_counters(our_labels: dict[str, dict[str, str]]) -> None:
    global our_mev_boost_reward_per_validator_count

    if len(our_labels) == 0 or our_mev_boost_reward_per_validator_count is not None:
        return

    labels_neg = list(random.choice(list(our_labels.values())).keys())
    labels_pos = labels_neg.copy()
    labels_pos.append(RELAY_KEY)
    our_mev_boost_reward_per_validator_count = Counter(
        "our_mev_boost_reward_per_validator_count",
        "Our MEV boost reward per validator counter",
        labels_pos)
    for labels_dict in our_labels.values():
        for relay in RELAY_MAPPING.values():
            labels_with_relay = labels_dict.copy()
            labels_with_relay[RELAY_KEY] = relay
            our_mev_boost_reward_per_validator_count.labels(**labels_with_relay)


class Relays:
    """Relays abstraction."""

    def __init__(self, urls: list[str]) -> None:
        """Relays

        Parameters:
        urls: URLs where the relays can be reached
        """
        self.__urls = urls
        self.__http = Session()

        adapter = HTTPAdapter(
            max_retries=Retry(
                backoff_factor=0.5,
                total=3,
                status_forcelist=[codes.not_found],
            )
        )

        self.__http.mount("http://", adapter)
        self.__http.mount("https://", adapter)

    def process(self, slot: int, our_labels: dict[str, dict[str, str]]) -> None:
        """Detect if the block was built by a known relay.

        Parameters:
        slot: Slot
        """
        if len(self.__urls) == 0:
            return

        if len(our_labels) == 0:
            if not any(
                    (
                            self.__is_proposer_payload_delivered(relay_url, slot)
                            for relay_url in self.__urls
                    )
            ):
                bad_relay_count.inc()
                print(
                    "🟧 Block proposed with unknown builder (may be a locally built block)"
                )
        else:
            known_builder = False
            for relay_url in self.__urls:
                payload = self.__proposer_payload_delivered(relay_url, slot)
                if payload is not None:
                    known_builder = True
                    pubkey = payload.proposer_pubkey
                    labels = our_labels[pubkey]
                    labels_with_relay = labels.copy()
                    labels_with_relay[RELAY_KEY] = RELAY_MAPPING[relay_url]
                    our_mev_boost_reward_per_validator_count.labels(**labels_with_relay).inc(
                        payload.value / 10 ** 9)  # value in Gwei
            if not known_builder:
                bad_relay_count.inc()
                print(
                    "🟧 Block proposed with unknown builder (may be a locally built block)"
                )

    def __is_proposer_payload_delivered(
            self,
            url: str,
            slot: int,
            trial_count=0,
            wait_sec=WAIT_SEC,
    ) -> bool:
        """Check if the block was built by a known relay.

        Parameters:
        url: URL where the relay can be reached
        slot: Slot
        """
        try:
            response = self.__http.get(
                f"{url}/relay/v1/data/bidtraces/proposer_payload_delivered",
                params=dict(slot=slot),
            )
        except ConnectionError:
            if trial_count >= MAX_TRIALS:
                raise

            sleep(wait_sec)

            return self.__is_proposer_payload_delivered(
                url, slot, trial_count + 1, wait_sec
            )

        response.raise_for_status()
        proposer_payload_delivered_json: list = response.json()

        assert (
                len(proposer_payload_delivered_json) <= 1
        ), "Relay returned more than one block"

        return len(proposer_payload_delivered_json) == 1

    def __proposer_payload_delivered(
            self,
            url: str,
            slot: int,
            trial_count=0,
            wait_sec=WAIT_SEC,
    ) -> ProposerPayloadDelivered | None:
        """Check if the block was built by a known relay.

        Parameters:
        url: URL where the relay can be reached
        slot: Slot
        """
        try:
            response = self.__http.get(
                f"{url}/relay/v1/data/bidtraces/proposer_payload_delivered",
                params=dict(slot=slot),
            )
        except ConnectionError:
            if trial_count >= MAX_TRIALS:
                raise

            sleep(wait_sec)

            return self.__proposer_payload_delivered(
                url, slot, trial_count + 1, wait_sec
            )

        response.raise_for_status()
        proposer_payload_delivered_json: list = response.json()

        assert (
                len(proposer_payload_delivered_json) <= 1
        ), "Relay returned more than one block"

        return (
            ProposerPayloadDelivered(**proposer_payload_delivered_json[0])
            if len(proposer_payload_delivered_json) == 1
            else None)
