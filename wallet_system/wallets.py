from abc import ABC,abstractmethod
from datetime import datetime
from typing import ClassVar, Iterator
import uuid

from wallet_system.enums import TransactionType,WalletType
from wallet_system.exceptions import DailyLimitExceededError, FrozenAccountError, InsufficientFundsError, InvalidAmountError
from wallet_system.transaction import Transaction, TransactionHistory

class BaseWallet(ABC):
    def __init__(self, owner: str,opening_balance: float = 0.0):
        self._wallet_id = str(uuid.uuid4())
        self._owner = owner
        self._balance = self._validate_amount(opening_balance)
        self._history = TransactionHistory()
        self._frozen = False

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def freeze(self) -> None:
        self._frozen = True

    def unfreeze(self) -> None:
        self._frozen = False

    def _check_not_frozen(self) -> None: #Need to understand the purpose of this function. Why here and not elsewhere.
        if self._frozen:
            raise FrozenAccountError(self._wallet_id)

    @property
    def wallet_id(self) -> str:
        return self._wallet_id

    @property
    @abstractmethod
    def wallet_type(self) -> str:
        pass

    @staticmethod
    def _validate_amount(amount: float) -> None:
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount < 0:
            raise InvalidAmountError(amount)
        return amount

    def deposit(self, amount: float, *,transaction_type: TransactionType = TransactionType.DEPOSIT) -> None: #WTF
        self._check_not_frozen()
        amount = self._validate_amount(amount)
        self._balance += amount
        self._history.add(
            Transaction(
                id=str(uuid.uuid4()),
                type= transaction_type,
                amount=amount,
                timestamp=datetime.now(),
                balance_after=self._balance
            )
        )

    def withdraw(self, amount: float, *,transaction_type: TransactionType = TransactionType.WITHDRAWAL) -> None:
        self._check_not_frozen()
        amount = self._validate_amount(amount)
        if amount > self._balance:
            raise InsufficientFundsError(amount, self._balance)
        self._balance -= amount
        self._history.add(
            Transaction(
                id=str(uuid.uuid4()),
                type= transaction_type,
                amount=amount,
                timestamp=datetime.now(),
                balance_after=self._balance
            )
        )

    @property
    def transactions(self) ->Iterator[Transaction]:
        return iter(self._history)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BaseWallet) and self._wallet_id == other._wallet_id

    def __len__(self):
        return len(self._history)

    def __iter__(self) -> Iterator[Transaction]:
        return iter(self._history)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} wallet_id={self._wallet_id}, owner={self._owner}, balance={self._balance}, frozen={self._frozen}>"

class PersonalWallet(BaseWallet):
    DAILY_LIMIT: ClassVar[float] = 25_000.0

    @property
    def wallet_type(self) -> WalletType:
        return WalletType.PERSONAL

    def _sent_today(self) -> float:
            today = datetime.now().date()
            return sum(
                transaction.amount for transaction in self._history if transaction.type in (TransactionType.WITHDRAWAL,TransactionType.TRANSFER_OUT) and transaction.timestamp.date() == today
            )
    
    def withdraw(self, amount, *, transaction_type = TransactionType.WITHDRAWAL) -> None:
        amount = self._validate_amount(amount)
        if self._sent_today() + amount > self.DAILY_LIMIT:
            raise DailyLimitExceededError(amount, self.DAILY_LIMIT, self._sent_today())
        super().withdraw(amount, transaction_type=transaction_type)

    
class MerchantWallet(BaseWallet):
    FEE_RATE: ClassVar[float] = 0.015

    @property
    def wallet_type(self) -> WalletType:
        return WalletType.MERCHANT

    def deposit(self, amount, *, transaction_type = TransactionType.DEPOSIT) -> None:
        amount = self._validate_amount(amount)
        fee = round(amount * self.FEE_RATE, 2)
        super().deposit(amount - fee, transaction_type=transaction_type)
        self._history.add(
            Transaction(
                id=str(uuid.uuid4()),
                type=TransactionType.FEE,
                amount=fee,
                timestamp=datetime.now(),
                balance_after=self._balance
            )
        )
    