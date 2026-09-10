import pytest

from wallet_system.exceptions import (
    WalletError,
    InvalidAmountError,
    InsufficientFundsError,
    FrozenAccountError,
    DailyLimitExceededError,
    AccountNotFoundError,
)
from wallet_system.wallets import PersonalWallet


ALL_WALLET_EXCEPTIONS = [
    InvalidAmountError,
    InsufficientFundsError,
    FrozenAccountError,
    DailyLimitExceededError,
    AccountNotFoundError,
]


# ---------------------------------------------------------------------------
# Hierarchy
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("exc_class", ALL_WALLET_EXCEPTIONS)
def test_all_exceptions_inherit_from_wallet_error(exc_class):
    assert issubclass(exc_class, WalletError)


def test_wallet_error_catches_any_subclass_when_raised():
    """Proves the hierarchy actually works at runtime, not just in theory."""
    wallet = PersonalWallet(owner="Alice")
    with pytest.raises(WalletError):
        wallet.deposit(-50)  # actually raises InvalidAmountError


# ---------------------------------------------------------------------------
# InvalidAmountError
# ---------------------------------------------------------------------------

def test_invalid_amount_error_stores_the_bad_amount():
    exc = InvalidAmountError(-50)
    assert exc.amount == -50


def test_invalid_amount_error_raised_via_wallet_deposit():
    wallet = PersonalWallet(owner="Alice")
    with pytest.raises(InvalidAmountError) as exc_info:
        wallet.deposit(-50)
    assert exc_info.value.amount == -50


# ---------------------------------------------------------------------------
# InsufficientFundsError
# ---------------------------------------------------------------------------

def test_insufficient_funds_error_stores_requested_and_available():
    exc = InsufficientFundsError(requested=500, available=200)
    assert exc.requested == 500
    assert exc.available == 200
    assert "500" in str(exc)
    assert "200" in str(exc)


def test_insufficient_funds_error_raised_via_wallet_withdraw():
    wallet = PersonalWallet(owner="Alice", opening_balance=100)
    with pytest.raises(InsufficientFundsError) as exc_info:
        wallet.withdraw(500)
    assert exc_info.value.requested == 500
    assert exc_info.value.available == 100


# ---------------------------------------------------------------------------
# FrozenAccountError
# ---------------------------------------------------------------------------

def test_frozen_account_error_stores_wallet_id():
    exc = FrozenAccountError(wallet_id="abc-123")
    assert exc.wallet_id == "abc-123"


def test_frozen_account_error_raised_on_deposit():
    wallet = PersonalWallet(owner="Alice")
    wallet.freeze()
    with pytest.raises(FrozenAccountError):
        wallet.deposit(100)


def test_frozen_account_error_raised_on_withdraw():
    wallet = PersonalWallet(owner="Alice", opening_balance=500)
    wallet.freeze()
    with pytest.raises(FrozenAccountError):
        wallet.withdraw(100)


# ---------------------------------------------------------------------------
# DailyLimitExceededError
# ---------------------------------------------------------------------------

def test_daily_limit_exceeded_error_stores_requested_limit_and_sent():
    exc = DailyLimitExceededError(amount=5000, limit=25000, already_sent_today=22000)
    assert exc.amount == 5000
    assert exc.daily_limit == 25000
    assert exc.already_sent_today == 22000


def test_daily_limit_exceeded_error_raised_via_wallet_withdraw():
    wallet = PersonalWallet(owner="Alice", opening_balance=100_000)
    wallet.withdraw(20_000)
    with pytest.raises(DailyLimitExceededError) as exc_info:
        wallet.withdraw(10_000)  # 20,000 + 10,000 > 25,000 daily limit
    assert exc_info.value.daily_limit == PersonalWallet.DAILY_LIMIT


# ---------------------------------------------------------------------------
# AccountNotFoundError
# ---------------------------------------------------------------------------

def test_account_not_found_error_stores_wallet_id():
    exc = AccountNotFoundError(wallet_id="does-not-exist")
    assert exc.wallet_id == "does-not-exist"


def test_account_not_found_error_raised_by_manager_get(manager):
    with pytest.raises(AccountNotFoundError):
        manager.get("does-not-exist")