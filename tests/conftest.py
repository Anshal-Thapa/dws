import pytest
 
from wallet_system.manager import WalletManager
from wallet_system.wallets import PersonalWallet, MerchantWallet
 
 
@pytest.fixture
def manager() -> WalletManager:
    return WalletManager()
 
 
@pytest.fixture
def personal_wallet() -> PersonalWallet:
    return PersonalWallet(owner="Alice", opening_balance=1000.0)
 
 
@pytest.fixture
def merchant_wallet() -> MerchantWallet:
    return MerchantWallet(owner="Kathmandu Coffee", opening_balance=0.0)
