from wallet_system.transaction import TransactionLogger
from wallet_system.wallets import MerchantWallet, PersonalWallet


def test_observer_receives_notification_on_deposit():
    wallet = PersonalWallet(owner="Alice", opening_balance=100)
    logger = TransactionLogger()
    wallet.attach(logger)

    wallet.deposit(50)

    assert len(logger.entries) == 1
    assert "DEPOSIT" in logger.entries[0]


def test_multiple_observers_all_notified():
    wallet = PersonalWallet(owner="Bob", opening_balance=100)
    logger1 = TransactionLogger()
    logger2 = TransactionLogger()
    wallet.attach(logger1)
    wallet.attach(logger2)

    wallet.withdraw(20)

    assert len(logger1.entries) == 1
    assert len(logger2.entries) == 1


def test_detached_observer_not_notified():
    wallet = PersonalWallet(owner="Carol", opening_balance=100)
    logger = TransactionLogger()
    wallet.attach(logger)
    wallet.detach(logger)

    wallet.deposit(10)

    assert logger.entries == []


def test_merchant_fee_transaction_also_notified():
    wallet = MerchantWallet(owner="Shop", opening_balance=0)
    logger = TransactionLogger()
    wallet.attach(logger)

    wallet.deposit(100)

    # one entry for the net deposit, one for the fee
    assert len(logger.entries) == 2
    assert any("FEE" in entry for entry in logger.entries)