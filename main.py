from wallet_system.manager import WalletManager
from wallet_system.wallets import PersonalWallet, MerchantWallet

def main():
    manager = WalletManager()

    anshal = manager.create(PersonalWallet,"Anshal Thapa",20000.0)
    Upakar = manager.create(PersonalWallet,"Upakar Shrestha", 0)

    manager.transfer(anshal.wallet_id,Upakar.wallet_id, 15000.0)

    print(anshal.balance)
    print(len(anshal._history))
    print(repr(anshal))

    for txn in anshal:                      # calls alice.__iter__() under the hood
        print(txn.type, txn.amount, txn.balance_after)

if __name__ == "__main__":
    main()
