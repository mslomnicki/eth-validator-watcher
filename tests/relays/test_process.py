from pytest import raises
from requests.exceptions import ConnectionError
from requests_mock import Mocker

from eth_validator_watcher.models import ProposerPayloadDelivered
from eth_validator_watcher.relays import Relays, metric_bad_relay_count


def test_process_no_relay() -> None:
    counter_before = metric_bad_relay_count.collect()[0].samples[0].value  # type: ignore
    relays = Relays(urls=[])
    relays.process(slot=42, our_labels={})
    counter_after = metric_bad_relay_count.collect()[0].samples[0].value  # type: ignore

    delta = counter_after - counter_before
    assert delta == 0


def test_process_bad_relay() -> None:
    relays = Relays(urls=["http://relay-1.com", "http://relay-2.com"])

    counter_before = metric_bad_relay_count.collect()[0].samples[0].value  # type: ignore

    with Mocker() as mock:
        mock.get(
            "http://relay-1.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            json=[],
        )

        mock.get(
            "http://relay-2.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            json=[],
        )

        relays.process(slot=42, our_labels={})

    counter_after = metric_bad_relay_count.collect()[0].samples[0].value  # type: ignore
    delta = counter_after - counter_before
    assert delta == 1


def test_process_good_relay() -> None:
    relays = Relays(urls=["http://relay-1.com", "http://relay-2.com"])

    counter_before = metric_bad_relay_count.collect()[0].samples[0].value  # type: ignore

    with Mocker() as mock:
        mock.get(
            "http://relay-1.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            json=[],
        )

        mock.get(
            "http://relay-2.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            json=["a block"],
        )

        relays.process(slot=42, our_labels={})

    counter_after = metric_bad_relay_count.collect()[0].samples[0].value  # type: ignore
    delta = counter_after - counter_before
    assert delta == 0


def test_process_relay_bad_answer() -> None:
    relays = Relays(urls=["http://relay.com"])

    with Mocker() as mock:
        mock.get(
            "http://relay.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            json=["first block", "second block"],
        )

        with raises(AssertionError):
            relays.process(slot=42, our_labels={})


def test___is_proposer_payload_delivered() -> None:
    relays = Relays(urls=["http://relay.com"])

    with Mocker() as mock:
        mock.get(
            "http://relay.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            exc=ConnectionError,
        )

        with raises(ConnectionError):
            relays._Relays__is_proposer_payload_delivered(  # type: ignore
                url="http://relay.com", slot=42, wait_sec=0
            )


def test___proposer_payload_delivered_with_connection_error() -> None:
    relays = Relays(urls=["http://relay.com"])

    with Mocker() as mock:
        mock.get(
            "http://relay.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            exc=ConnectionError,
        )

        with raises(ConnectionError):
            relays._Relays__proposer_payload_delivered(  # type: ignore
                url="http://relay.com", slot=42, wait_sec=0
            )


def test___proposer_payload_delivered_with_empty_response() -> None:
    relays = Relays(urls=["http://relay.com"])

    with Mocker() as mock:
        mock.get(
            "http://relay.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            json=[]
        )

        response = relays._Relays__proposer_payload_delivered(  # type: ignore
            url="http://relay.com", slot=42, wait_sec=0
        )

        assert response is None


def test___proposer_payload_delivered_with_single_response() -> None:
    relays = Relays(urls=["http://relay.com"])

    with Mocker() as mock:
        mock.get(
            "http://relay.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            json=[
                {"slot": "42", "parent_hash": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                 "block_hash": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                 "builder_pubkey": "0xcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                 "proposer_pubkey": "0xdddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
                 "proposer_fee_recipient": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "gas_limit": "30000000",
                 "gas_used": "12345678", "value": "12345678901234567", "num_tx": "123", "block_number": "56"}]
        )

        response: ProposerPayloadDelivered = relays._Relays__proposer_payload_delivered(  # type: ignore
            url="http://relay.com", slot=42, wait_sec=0
        )

        assert response.slot == 42
        assert response.value == 12345678901234567
        assert response.proposer_pubkey == "0xdddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"


def test___proposer_payload_delivered_with_multiple_responses() -> None:
    relays = Relays(urls=["http://relay.com"])

    with Mocker() as mock:
        mock.get(
            "http://relay.com/relay/v1/data/bidtraces/proposer_payload_delivered?slot=42",
            json=["first block", "second block"],
        )

        with raises(AssertionError):
            relays._Relays__proposer_payload_delivered(  # type: ignore
                url="http://relay.com", slot=42, wait_sec=0
            )
