from abc import ABC, abstractmethod
from app.models import Account


class CardState(ABC):
    @abstractmethod
    def enable(self):
        pass

    @abstractmethod
    def disable(self):
        pass

    @abstractmethod
    def withdraw(self):
        pass

    @abstractmethod
    def deposit(self):
        pass


class Enabled(CardState):
    def enable(self):
        return self

    def disable(self):
        return Disabled()

    def withdraw(self, account: Account, amount: int):
        if account.balance >= amount:
            account.balance -= amount
            return True, f"Withdrawing {amount} from active card. New balance: {account.balance}"
        else:
            return False, "FAILED: Insufficient balance for withdrawal."

    def deposit(self, account: Account, amount: int):
        account.balance += amount
        return True, f"Depositing {amount} to active card. New balance: {account.balance}"


class Disabled(CardState):
    def enable(self):
        return Enabled()
        
    def disable(self):
        return self

    def withdraw(self, account: Account, amount: int):
        return "Cannot withdraw. Card is blocked."

    def deposit(self, account: Account, amount: int):
        return "Cannot deposit. Card is blocked."
