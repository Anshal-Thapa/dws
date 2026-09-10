"""
Tests for wallet_system.wallets.PersonalWallet.

Structure follows the same shape for each behavior: happy path, obvious
failure, then boundary/edge cases. The daily-limit tests are the most
important in this file — that's the one business rule unique to
PersonalWallet, and boundaries are where off-by-one bugs hide.
"""
from unittest.mock import patch
from datetime import datetime

import pytest

from wallet_system.enums import TransactionType, WalletType
from wallet_system.exceptions import (
    InvalidAmountError,
    InsufficientFundsError,
    FrozenAccountError,
    DailyLimitExceededError,
)
from wallet_system.wallets import PersonalWallet


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_new_wallet_has_the_given_opening_balance():
    wallet = PersonalWallet(owner="Alice", opening_balance=500)
    assert wallet.balance == 500


def test_new_wallet_defaults_to_zero_balance():
    wallet = PersonalWallet(owner="Alice")
    assert wallet.balance == 0.0


def test_wallet_type_is_personal(personal_wallet):
    assert personal_wallet.wallet_type == WalletType.PERSONAL


def test_wallet_id_is_generated_and_unique():
    a = PersonalWallet(owner="Alice")
    b = PersonalWallet(owner="Alice")  # same owner name, different wallet
    assert a.wallet_id != b.wallet_id


@pytest.mark.parametrize("bad_opening_balance", [-1, -50.5])
def test_negative_opening_balance_raises(bad_opening_balance):
    with pytest.raises(InvalidAmountError):
        PersonalWallet(owner="Alice", opening_balance=bad_opening_balance)


# ---------------------------------------------------------------------------
# balance is read-only
# ---------------------------------------------------------------------------

def test_balance_cannot_be_set_directly(personal_wallet):
    with pytest.raises(AttributeError):
        personal_wallet.balance = 999999


# ---------------------------------------------------------------------------
# deposit
# ---------------------------------------------------------------------------

def test_deposit_increases_balance(personal_wallet):
    personal_wallet.deposit(500)
    assert personal_wallet.balance == 1500.0


def test_deposit_logs_a_transaction(personal_wallet):
    personal_wallet.deposit(500)
    records = list(personal_wallet)
    assert len(records) == 1
    assert records[0].type == TransactionType.DEPOSIT
    assert records[0].amount == 500.0
    assert records[0].balance_after == 1500.0


@pytest.mark.parametrize("bad_amount", [-1, -50.5, "abc", None, True])
def test_deposit_invalid_amounts_raise(personal_wallet, bad_amount):
    with pytest.raises(InvalidAmountError):
        personal_wallet.deposit(bad_amount)


def test_deposit_on_frozen_wallet_raises(personal_wallet):
    personal_wallet.freeze()
    with pytest.raises(FrozenAccountError):
        personal_wallet.deposit(100)


def test_deposit_invalid_amount_does_not_change_balance(personal_wallet):
    original = personal_wallet.balance
    with pytest.raises(InvalidAmountError):
        personal_wallet.deposit(-50)
    assert personal_wallet.balance == original


# ---------------------------------------------------------------------------
# withdraw — happy path, insufficient funds
# ---------------------------------------------------------------------------

def test_withdraw_reduces_balance(personal_wallet):
    personal_wallet.withdraw(200)
    assert personal_wallet.balance == 800.0


def test_withdraw_logs_a_transaction(personal_wallet):
    personal_wallet.withdraw(200)
    records = list(personal_wallet)
    assert records[0].type == TransactionType.WITHDRAWAL
    assert records[0].amount == 200.0
    assert records[0].balance_after == 800.0


def test_withdraw_more_than_balance_raises(personal_wallet):
    with pytest.raises(InsufficientFundsError):
        personal_wallet.withdraw(5000)


def test_withdraw_more_than_balance_does_not_change_balance(personal_wallet):
    original = personal_wallet.balance
    with pytest.raises(InsufficientFundsError):
        personal_wallet.withdraw(5000)
    assert personal_wallet.balance == original


def test_withdraw_on_frozen_wallet_raises(personal_wallet):
    personal_wallet.freeze()
    with pytest.raises(FrozenAccountError):
        personal_wallet.withdraw(100)


@pytest.mark.parametrize("bad_amount", [-1, -50.5, "abc", None, True])
def test_withdraw_invalid_amounts_raise(personal_wallet, bad_amount):
    with pytest.raises(InvalidAmountError):
        personal_wallet.withdraw(bad_amount)


# ---------------------------------------------------------------------------
# withdraw — daily limit (boundary cases)
# ---------------------------------------------------------------------------

def test_withdraw_at_exact_daily_limit_succeeds():
    wallet = PersonalWallet(owner="Alice", opening_balance=30_000)
    wallet.withdraw(PersonalWallet.DAILY_LIMIT)  # exactly at the cap
    assert wallet.balance == 30_000 - PersonalWallet.DAILY_LIMIT


def test_withdraw_one_unit_over_daily_limit_raises():
    wallet = PersonalWallet(owner="Alice", opening_balance=30_000)
    with pytest.raises(DailyLimitExceededError):
        wallet.withdraw(PersonalWallet.DAILY_LIMIT + 0.01)


def test_daily_limit_accumulates_across_multiple_withdrawals():
    wallet = PersonalWallet(owner="Alice", opening_balance=30_000)
    wallet.withdraw(20_000)
    with pytest.raises(DailyLimitExceededError):
        wallet.withdraw(10_000)  # 20,000 + 10,000 > 25,000


def test_daily_limit_error_carries_correct_context():
    wallet = PersonalWallet(owner="Alice", opening_balance=30_000)
    wallet.withdraw(20_000)
    with pytest.raises(DailyLimitExceededError) as exc_info:
        wallet.withdraw(10_000)
    assert exc_info.value.already_sent_today == 20_000
    assert exc_info.value.daily_limit == PersonalWallet.DAILY_LIMIT
    assert exc_info.value.amount == 10_000


def test_daily_limit_breach_does_not_change_balance():
    wallet = PersonalWallet(owner="Alice", opening_balance=30_000)
    wallet.withdraw(20_000)
    balance_before_failed_attempt = wallet.balance
    with pytest.raises(DailyLimitExceededError):
        wallet.withdraw(10_000)
    assert wallet.balance == balance_before_failed_attempt


def test_daily_limit_resets_on_a_new_day():
    wallet = PersonalWallet(owner="Alice", opening_balance=100_000)
    with patch("wallet_system.wallets.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 1, 10, 0)
        wallet.withdraw(20_000)

        mock_dt.now.return_value = datetime(2026, 1, 2, 10, 0)  # next day
        wallet.withdraw(20_000)  # should succeed — the daily total reset

    assert wallet.balance == 100_000 - 40_000


# ---------------------------------------------------------------------------
# freeze / unfreeze
# ---------------------------------------------------------------------------

def test_wallet_starts_unfrozen(personal_wallet):
    assert personal_wallet.is_frozen is False


def test_freeze_sets_is_frozen(personal_wallet):
    personal_wallet.freeze()
    assert personal_wallet.is_frozen is True


def test_unfreeze_allows_operations_again(personal_wallet):
    personal_wallet.freeze()
    personal_wallet.unfreeze()
    personal_wallet.deposit(100)  # should not raise
    assert personal_wallet.balance == 1100.0


# ---------------------------------------------------------------------------
# Magic methods
# ---------------------------------------------------------------------------

def test_equal_wallet_ids_are_equal():
    wallet = PersonalWallet(owner="Alice")
    same_reference = wallet
    assert wallet == same_reference


def test_different_wallets_are_not_equal():
    a = PersonalWallet(owner="Alice")
    b = PersonalWallet(owner="Alice")  # same owner, different id
    assert a != b


def test_wallet_not_equal_to_unrelated_object(personal_wallet):
    assert personal_wallet != "not a wallet"
    assert personal_wallet != 5


def test_len_matches_number_of_transactions(personal_wallet):
    personal_wallet.deposit(100)
    personal_wallet.withdraw(50)
    assert len(personal_wallet) == 2


def test_iter_yields_transactions_in_order(personal_wallet):
    personal_wallet.deposit(100)
    personal_wallet.withdraw(50)
    types = [txn.type for txn in personal_wallet]
    assert types == [TransactionType.DEPOSIT, TransactionType.WITHDRAWAL]


def test_repr_does_not_error(personal_wallet):
    assert "PersonalWallet" in repr(personal_wallet)


# ---------------------------------------------------------------------------
# transactions property (explicit accessor, alternative to iterating the wallet)
# ---------------------------------------------------------------------------

def test_transactions_property_matches_iteration(personal_wallet):
    personal_wallet.deposit(100)
    assert list(personal_wallet.transactions) == list(personal_wallet)