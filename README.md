# Digital Wallet System

A small, single-currency digital wallet backend built as a Week 2 OOP exercise
(Python roadmap: classes, inheritance, ABCs, `@property`, magic methods,
custom exceptions, pytest).

Two account types share a common base:

- **`PersonalWallet`** — everyday use, capped by a daily transaction limit.
- **`MerchantWallet`** — receives payments, automatically deducts a
  settlement fee on each deposit, no daily cap.

`WalletManager` coordinates transfers between wallets (P2P or to a merchant),
including rollback if the receiving side fails partway through.

## Scope

This is a library, not an application. There is **no CLI and no user
interface** — that's intentional, not missing. The project is verified
entirely through its test suite; there's nothing to run and click through.

## Setup

```bash
pip install -e .
pip install -r requirements.txt
```

## Running the tests

```bash
pytest -v
```

## Coverage

```bash
pytest --cov=wallet_system --cov-report=term-missing
```

Target: ≥80% (see the full spec doc for details on what's tested and why).

## Project structure

```
wallet_system/
├── enums.py         # TransactionType, WalletType
├── exceptions.py     # WalletError and its subclasses
├── transaction.py     # Transaction (immutable record), TransactionHistory
├── wallets.py          # BaseWallet (ABC), PersonalWallet, MerchantWallet
└── manager.py           # WalletManager — registry + transfer coordination
tests/                    # pytest suite, one file per module above
```

## Quick usage example

```python
from wallet_system.manager import WalletManager
from wallet_system.wallets import PersonalWallet, MerchantWallet

manager = WalletManager()
alice = manager.create(PersonalWallet, owner="Alice", opening_balance=1000)
shop = manager.create(MerchantWallet, owner="Kathmandu Coffee")

manager.transfer(alice.wallet_id, shop.wallet_id, 500)

print(alice.balance)   # 500.0
print(shop.balance)    # 500.0 minus the settlement fee
```