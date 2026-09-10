from enum import Enum

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    FEE = "FEE"
    REFUND = "REFUND"

class WalletType(str, Enum):
    PERSONAL = "PERSONAL"
    MERCHANT = "MERCHANT"
    