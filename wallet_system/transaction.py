from wallet_system.enums import TransactionType
from typing import Iterator
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Transaction:
    id: str
    type: TransactionType
    amount: float
    timestamp: datetime
    balance_after: float


# class Transaction:
#     def __init__(self ,id:str ,type: TransactionType ,amount:float ,timestamp:str ,balance_after: float):
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