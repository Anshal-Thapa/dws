"""
Tests for wallet_system.wallets.MerchantWallet.

The one behavior unique to this class is the settlement fee on deposits —
that's where most of the test weight goes. withdraw() is inherited
unchanged from BaseWallet, so it isn't re-tested exhaustively here
(that's PersonalWallet/BaseWallet's job); we only confirm it has no
daily cap, which IS specific to this subclass by omission.
"""
import pytest

from wallet_system.enums import TransactionType, WalletType
from wallet_system.exceptions import InvalidAmountError, FrozenAccountError
from wallet_system.wallets import MerchantWallet


def test_wallet_type_is_merchant(merchant_wallet):
    assert merchant_wallet.wallet_type == WalletType.MERCHANT


# ---------------------------------------------------------------------------
# deposit — settlement fee
# ---------------------------------------------------------------------------

def test_deposit_credits_amount_minus_fee(merchant_wallet):
    merchant_wallet.deposit(1000)
    expected_fee = round(1000 * MerchantWallet.FEE_RATE, 2)
    assert merchant_wallet.balance == 1000 - expected_fee


def test_deposit_logs_two_separate_transactions(merchant_wallet):
    merchant_wallet.deposit(1000)
    records = list(merchant_wallet)

    assert len(records) == 2
    deposit_record = next(r for r in records if r.type == TransactionType.DEPOSIT)
    fee_record = next(r for r in records if r.type == TransactionType.FEE)

    expected_fee = round(1000 * MerchantWallet.FEE_RATE, 2)
    assert deposit_record.amount == 1000 - expected_fee
    assert fee_record.amount == expected_fee


def test_deposit_and_fee_sum_to_the_original_amount(merchant_wallet):
    """The fee shouldn't make money appear or disappear from the total."""
    merchant_wallet.deposit(1000)
    records = list(merchant_wallet)
    total_logged = sum(r.amount for r in records if r.type in (TransactionType.DEPOSIT, TransactionType.FEE))
    assert total_logged == 1000


@pytest.mark.parametrize("bad_amount", [-1, -50.5, "abc", None, True])
def test_deposit_invalid_amounts_raise(merchant_wallet, bad_amount):
    with pytest.raises(InvalidAmountError):
        merchant_wallet.deposit(bad_amount)


def test_deposit_on_frozen_wallet_raises(merchant_wallet):
    merchant_wallet.freeze()
    with pytest.raises(FrozenAccountError):
        merchant_wallet.deposit(1000)


def test_deposit_invalid_amount_leaves_balance_unchanged(merchant_wallet):
    original = merchant_wallet.balance
    with pytest.raises(InvalidAmountError):
        merchant_wallet.deposit(-50)
    assert merchant_wallet.balance == original


# ---------------------------------------------------------------------------
# withdraw — no daily cap (the specific way this subclass differs from PersonalWallet)
# ---------------------------------------------------------------------------

def test_withdraw_large_amount_in_one_go_succeeds():
    wallet = MerchantWallet(owner="Kathmandu Coffee", opening_balance=1_000_000)
    wallet.withdraw(500_000)  # would blow past PersonalWallet's daily limit; must succeed here
    assert wallet.balance == 500_000


def test_withdraw_on_frozen_wallet_raises(merchant_wallet):
    merchant_wallet.deposit(1000)
    merchant_wallet.freeze()
    with pytest.raises(FrozenAccountError):
        merchant_wallet.withdraw(100)