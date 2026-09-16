from abc import ABC
from ast import List
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from wallet_system.enums import TransactionType

if TYPE_CHECKING:
    from wallet_system.wallets import BaseWallet


@dataclass(frozen=True)
class Transaction:
    id: str
    type: TransactionType
    amount: float
    timestamp: datetime
    balance_after: float


class TransactionObserver(ABC):
    def update(self, wallet, transaction):
        ...


class TransactionLogger(TransactionObserver):
    def __init__(self, verbose: bool = False) -> None:
        self.entries: List[str] = []
        self.verbose = verbose


    def update(self, wallet: "BaseWallet", transaction: "Transaction"):
        entry = (
            f"[{transaction.timestamp.isoformat()}] "
            f"wallet={wallet.wallet_id} type={transaction.type.name} "
            f"amount={transaction.amount:.2f} balance_after={transaction.balance_after:.2f}"
        )
        self.entries.append(entry)
        if self.verbose:
            print(entry)



# class Transaction:
#     def __init__(self ,id:str ,type: TransactionType ,amount:float, timestamp:str,balance_after: float):
#         self.id = id
#         self.type = type
#         self.amount = amount
#         self.timestamp = timestamp
#         self.balance_after = balance_after


class TransactionHistory:
    def __init__(self) -> None:
        self._transactions: list[Transaction] = []

    def add(self, transaction: Transaction) -> None:
        self._transactions.append(transaction)

    def __len__(self) -> int:
        return len(self._transactions)

    def __iter__(self) -> Iterator[Transaction]:
        return iter(self._transactions)
