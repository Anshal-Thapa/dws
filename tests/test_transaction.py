"""
Tests for wallet_system.transaction (Transaction, TransactionHistory).

Kept independent of BaseWallet where possible — these classes have no
dependency on wallets, so they shouldn't need one to be tested.
"""
from dataclasses import FrozenInstanceError
from datetime import datetime,UTC

import pytest

from wallet_system.enums import TransactionType
from wallet_system.transaction import Transaction, TransactionHistory


def make_transaction(amount: float = 100.0, txn_type: TransactionType = TransactionType.DEPOSIT) -> Transaction:
    return Transaction(
        id="txn-1",
        type=txn_type,
        amount=amount,
        timestamp=datetime.now(UTC),
        balance_after=amount,
    )


# ---------------------------------------------------------------------------
# Transaction — should be immutable
# ---------------------------------------------------------------------------

def test_transaction_holds_the_fields_it_was_given():
    txn = make_transaction(amount=250.0, txn_type=TransactionType.WITHDRAWAL)
    assert txn.amount == 250.0
    assert txn.type == TransactionType.WITHDRAWAL


def test_transaction_is_immutable():
    txn = make_transaction()
    with pytest.raises(FrozenInstanceError):
        txn.amount = 999.0


# ---------------------------------------------------------------------------
# TransactionHistory
# ---------------------------------------------------------------------------

def test_new_history_is_empty():
    history = TransactionHistory()
    assert len(history) == 0
    assert list(history) == []


def test_add_increases_length():
    history = TransactionHistory()
    history.add(make_transaction())
    assert len(history) == 1


def test_iteration_returns_records_in_the_order_added():
    history = TransactionHistory()
    first = make_transaction(amount=100.0)
    second = make_transaction(amount=200.0)
    history.add(first)
    history.add(second)

    records = list(history)

    assert records == [first, second]


def test_can_iterate_twice_independently():
    """
    Regression test for a real bug class: if __iter__ stored a single
    iterator as instance state and returned `self`, a second loop would
    come up empty because the first loop already exhausted it.
    """
    history = TransactionHistory()
    history.add(make_transaction())

    first_pass = list(history)
    second_pass = list(history)

    assert first_pass == second_pass
    assert len(first_pass) == 1