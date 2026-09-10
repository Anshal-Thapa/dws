import pytest

from wallet_system.enums import TransactionType
from wallet_system.exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
    FrozenAccountError,
    DailyLimitExceededError,
)
from wallet_system.wallets import PersonalWallet, MerchantWallet

def test_get_unknown_id_raises_account_not_found(manager):
    with pytest.raises(AccountNotFoundError):
        manager.get("does-not-exist")


def test_register_makes_a_wallet_findable_by_id(manager, personal_wallet):
    manager.register(personal_wallet)
    found = manager.get(personal_wallet.wallet_id)
    assert found is personal_wallet


def test_unregistered_wallet_is_not_findable(manager, personal_wallet):
    # intentionally NOT registered
    with pytest.raises(AccountNotFoundError):
        manager.get(personal_wallet.wallet_id)


def test_create_registers_the_wallet_automatically(manager):
    wallet = manager.create(PersonalWallet, owner="Alice", opening_balance=500)
    found = manager.get(wallet.wallet_id)
    assert found is wallet


def test_create_returns_the_correct_type(manager):
    wallet = manager.create(MerchantWallet, owner="Shop")
    assert isinstance(wallet, MerchantWallet)


def test_transfer_moves_funds_between_two_personal_wallets(manager):
    alice = manager.create(PersonalWallet, owner="Alice", opening_balance=1000)
    bob = manager.create(PersonalWallet, owner="Bob", opening_balance=0)

    manager.transfer(alice.wallet_id, bob.wallet_id, 300)

    assert alice.balance == 700
    assert bob.balance == 300


def test_transfer_logs_transfer_out_and_transfer_in(manager):
    alice = manager.create(PersonalWallet, owner="Alice", opening_balance=1000)
    bob = manager.create(PersonalWallet, owner="Bob", opening_balance=0)

    manager.transfer(alice.wallet_id, bob.wallet_id, 300)

    alice_record = list(alice)[-1]
    bob_record = list(bob)[-1]
    assert alice_record.type == TransactionType.TRANSFER_OUT
    assert bob_record.type == TransactionType.TRANSFER_IN


def test_transfer_applies_merchant_fee_when_receiver_is_merchant(manager):
    alice = manager.create(PersonalWallet, owner="Alice", opening_balance=1000)
    shop = manager.create(MerchantWallet, owner="Shop", opening_balance=0)

    manager.transfer(alice.wallet_id, shop.wallet_id, 1000)

    expected_fee = round(1000 * MerchantWallet.FEE_RATE, 2)
    assert alice.balance == 0
    assert shop.balance == 1000 - expected_fee


def test_transfer_unknown_sender_raises_account_not_found(manager):
    bob = manager.create(PersonalWallet, owner="Bob")
    with pytest.raises(AccountNotFoundError):
        manager.transfer("no-such-id", bob.wallet_id, 100)


def test_transfer_unknown_receiver_raises_account_not_found(manager):
    alice = manager.create(PersonalWallet, owner="Alice", opening_balance=1000)
    with pytest.raises(AccountNotFoundError):
        manager.transfer(alice.wallet_id, "no-such-id", 100)


def test_transfer_insufficient_funds_leaves_both_balances_unchanged(manager):
    alice = manager.create(PersonalWallet, owner="Alice", opening_balance=100)
    bob = manager.create(PersonalWallet, owner="Bob", opening_balance=0)

    with pytest.raises(InsufficientFundsError):
        manager.transfer(alice.wallet_id, bob.wallet_id, 5000)

    assert alice.balance == 100
    assert bob.balance == 0


def test_transfer_respects_sender_daily_limit(manager):
    alice = manager.create(PersonalWallet, owner="Alice", opening_balance=100_000)
    bob = manager.create(PersonalWallet, owner="Bob", opening_balance=0)

    with pytest.raises(DailyLimitExceededError):
        manager.transfer(alice.wallet_id, bob.wallet_id, PersonalWallet.DAILY_LIMIT + 1)

    assert alice.balance == 100_000
    assert bob.balance == 0


# ---------------------------------------------------------------------------
# transfer — rollback on partial failure (the case most likely to be skipped)
# ---------------------------------------------------------------------------

def test_transfer_to_frozen_receiver_rolls_back_sender_balance(manager):
    alice = manager.create(PersonalWallet, owner="Alice", opening_balance=1000)
    bob = manager.create(PersonalWallet, owner="Bob", opening_balance=0)
    bob.freeze()

    with pytest.raises(FrozenAccountError):
        manager.transfer(alice.wallet_id, bob.wallet_id, 300)

    # sender must end up exactly where they started — no funds lost
    assert alice.balance == 1000
    assert bob.balance == 0


def test_transfer_rollback_is_visible_in_sender_history(manager):
    """
    The rollback should go through deposit(), not a silent balance
    correction — so the sender's history should show the failed attempt
    AND the compensating credit, both auditable.
    """
    alice = manager.create(PersonalWallet, owner="Alice", opening_balance=1000)
    bob = manager.create(PersonalWallet, owner="Bob", opening_balance=0)
    bob.freeze()

    with pytest.raises(FrozenAccountError):
        manager.transfer(alice.wallet_id, bob.wallet_id, 300)

    records = list(alice)
    assert len(records) == 2  # the withdraw attempt + the rollback deposit
    assert records[0].type == TransactionType.TRANSFER_OUT
    assert records[1].type == TransactionType.REFUND