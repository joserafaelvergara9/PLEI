from abc import ABC, abstractmethod
from receipt import Receipt
from general_purpose_functions.id_generator import id_generator
import json
import os

class Transaction(ABC):
    def __init__(
            self, 
            name: str, 
            amount: float, 
            mode_of_payment: str,
            timestamp: str,
            receipt: Receipt = None,
            comments: list = None
        ):
        self._name = name
        self._amount = amount
        self._mode_of_payment = mode_of_payment
        self._timestamp = timestamp
        self._receipt = receipt
        self._comments = comments if comments is not None else []

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def amount(self) -> float:
        return self._amount
    
    @property
    def mode_of_payment(self) -> str:
        return self._mode_of_payment
    
    @property
    def timestamp(self) -> str:
        return self._timestamp
    
    @property
    def receipt(self) -> Receipt:
        return self._receipt
    
    @property
    def comments(self) -> list:
        return self._comments
    
    def add_comment(self, comment: str) -> None:
        self._comments.append(comment)

    def remove_comment(self, comment: str) -> None:
        if comment in self._comments:
            self._comments.remove(comment)

    @abstractmethod
    def display_transaction(self) -> None:
        pass

class Expense(Transaction):
    def __init__(
            self, 
            name: str, 
            amount: float, 
            mode_of_payment: str,
            timestamp: str,
            category_of_payment: str,
            quantity: int = 1,
            receipt: Receipt = None,
            comments: list = None,
        ):
        super().__init__(name, amount, mode_of_payment, timestamp, receipt, comments)
        self._category_of_payment = category_of_payment
        self._quantity = quantity
        self._expense_id = id_generator("expense")
    
    @property
    def category_of_payment(self) -> str:
        return self._category_of_payment

    @property
    def quantity(self) -> int:
        return self._quantity

    @category_of_payment.setter
    def category_of_payment(self, category: str) -> None:
        self._category_of_payment = category

    @quantity.setter
    def quantity(self, quantity: int) -> None:
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")
        self._quantity = quantity

    def __str__(self) -> str:
        return (
            f"Expense ID:          {self._expense_id}\n"
            f"Name:                {self._name}\n"
            f"Amount:              P{self._amount:,.2f}\n"
            f"Quantity:            {self._quantity}\n"
            f"Mode of Payment:     {self._mode_of_payment}\n"
            f"Category of Payment: {self._category_of_payment}\n"
            f"Timestamp:           {self._timestamp}\n"
            f"Receipt:             {self._receipt}\n"
            f"Comments:            {', '.join(self._comments)}"
        )

    def display_transaction(self) -> None:
        print(self)
        
class Income(Transaction):
    pass


'''
test_dict = {
    "name": "Jess",
    "version": 1.0
}

def readData():
    with open("income_expense_tracker/iet_json_files/test.json", "r", encoding="utf-8") as file:
        return json.load(file)

def writeData(name, version):
    with open("income_expense_tracker/iet_json_files/test.json", "w", encoding="utf-8") as file:
        json.dump({"name": name, "version": version}, file, indent=4)


class Transaction(ABC):
    pass

print()
print(os.getcwd())
print()

print(readData())
writeData("Mark", 2.0)
print(readData())
'''

