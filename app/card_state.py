from abc import ABC, abstractmethod


class CardState(ABC):
    @abstractmethod
    def withdraw(self):
        pass

    @abstractmethod
    def deposit(self):
        pass


class Enabled(CardState):
    def withdraw(self, account: "app.models.Account", amount: int):
        if account.balance >= amount:
            account.balance -= amount
            return True, f"Withdrawing {amount} from active card."
        else:
            return False, "FAILED: Insufficient balance for withdrawal."

    def deposit(self, account: "app.models.Account", amount: int):
        account.balance += amount
        return f"Depositing {amount} to active card."


class Disabled(CardState):
    def withdraw(self, account: "app.models.Account", amount: int):
        return "Cannot withdraw. Card is blocked."

    def deposit(self, account: "app.models.Account", amount: int):
        return "Cannot deposit. Card is blocked."
