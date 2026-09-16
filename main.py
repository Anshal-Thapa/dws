from wallet_system.manager import WalletManager
from wallet_system.wallets import PersonalWallet


def main():
    manager = WalletManager()

    anshal = manager.create(PersonalWallet, "Anshal Thapa", 20000.0)
    Upakar = manager.create(PersonalWallet, "Upakar Shrestha", 0)

    manager.transfer(anshal.wallet_id, Upakar.wallet_id, 15000.0)

    w = PersonalWallet(owner="Alice")
    print(w.wallet_id)
    print(w.wallet_id)


if __name__ == "__main__":
    main()
