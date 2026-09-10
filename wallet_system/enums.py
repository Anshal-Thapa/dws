from enum import StrEnum,auto

class TransactionType(StrEnum):
    DEPOSIT = auto()
    WITHDRAWAL = auto()
    TRANSFER_IN = auto()
    TRANSFER_OUT = auto()
    FEE = auto()
    REFUND = auto()

class WalletType(StrEnum):
    PERSONAL = auto()
    MERCHANT = auto()
    