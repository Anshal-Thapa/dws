class WalletError(Exception):
    pass

class InvalidAmountError(WalletError):
    def __init__(self, amount):
        self.amount = amount
        super().__init__(f"Invalid amount: Rs.{amount}. Amount must be a positive number.")
    pass

class InsufficientFundsError(WalletError):
    def __init__(self,requested: float, available: float):
        self.requested = requested
        self.available = available
        super().__init__(f"Requested {requested} exceeds currently available balance {available}")
    pass

class FrozenAccountError(WalletError):
    def __init__(self, wallet_id):
        self.wallet_id = wallet_id
        super().__init__(wallet_id)
    pass

class DailyLimitExceededError(WalletError):
    def __init__(self, amount:float, limit: float, already_sent_today: float):
        self.amount = amount
        self.daily_limit = limit
        self.already_sent_today = already_sent_today
        super().__init__(f"You have already sent Rs.{already_sent_today} today. Transaction amount Rs.{amount} exceeds daily limit of Rs.{limit}.")
    pass

class AccountNotFoundError(WalletError):
    def __init__(self, wallet_id):
        self.wallet_id = wallet_id
        super().__init__(f"Account with wallet ID {wallet_id} not found.")
    pass
