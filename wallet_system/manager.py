from .wallets import BaseWallet
from .exceptions import AccountNotFoundError,WalletError
from .enums import TransactionType

class WalletManager:
    def __init__(self):
        self._wallets = {}

    def register(self, wallet: BaseWallet) -> None:
        self._wallets[wallet.wallet_id] = wallet

    def get(self, wallet_id: str) -> BaseWallet:
        wallet = self._wallets.get(wallet_id)
        if wallet is None:
            raise AccountNotFoundError(wallet_id)
        return wallet

    def transfer(self, from_wallet_id: str, to_wallet_id: str, amount: float) -> None:
        from_wallet = self.get(from_wallet_id)
        to_wallet = self.get(to_wallet_id)

        from_wallet.withdraw(amount, transaction_type=TransactionType.TRANSFER_OUT)
        try:
            to_wallet.deposit(amount, transaction_type=TransactionType.TRANSFER_IN)
        except WalletError:
            from_wallet.deposit(amount, transaction_type=TransactionType.REFUND)
            raise

    def create(self, wallet_cls: type[BaseWallet],*args,**kwargs) -> BaseWallet:
        wallet = wallet_cls(*args,**kwargs)
        self.register(wallet)
        return wallet
