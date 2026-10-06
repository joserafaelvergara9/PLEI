## TO ADD: CHECKS FOR MODE AND CATEGORY !!
## ALSO ADD: WHEN TRANSACTION IS ADDED, PUT INTO TRANSACTION HISTORY
## ALSO FIGURE OUT: HOW THE RECEIPT OBJECT IS GOING TO WORK EXACTLY
## ADD TRY, EXCEPT, ELSE, FINALLY
## MAKE ALL TIMESTAMP INSTANCES DATETIME

## MAKE THE USER BE ABLE TO DECIDE VALID CATEGORIES
## CUSTOM EXCEPTION


from abc import ABC, abstractmethod
from receipt import Receipt
from general_purpose_functions.id_generator import id_generator
from datetime import datetime
import json
import os


class Transaction(ABC):
    def __init__(
            self, 
            name: str, 
            amount: float, 
            mode_of_payment: str,
            receipt: Receipt = None,
            comments: list = None
        ):
        self._name = name
        self._amount = amount
        self._mode_of_payment = mode_of_payment
        self._timestamp = datetime.now()
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
            category_of_payment: str,
            quantity: int = 1,
            receipt: Receipt = None,
            comments: list = None,
        ):
        # self._valid_payment_methods = ["cash", "credit", "debit", "qrph", "paypal", "venmo"]
        # self._valid_categories = ["housing", "utilities", "insurance", "debt", "groceries", "food", "transportation", "grooming", "healthcare", "personal"]
        super().__init__(name, amount, mode_of_payment, receipt, comments)
        self._category_of_payment = category_of_payment
        self._quantity = quantity
        self._expense_id = id_generator("expense")
        self._json_path = "income_expense_tracker/iet_json_files/expenses.json"
    
    @property
    def category_of_payment(self) -> str:
        return self._category_of_payment

    @property
    def quantity(self) -> int:
        return self._quantity
    
    @property
    def json_path(self) -> str:
        return self._json_path

    @category_of_payment.setter
    def category_of_payment(self, category: str) -> None:
        self._category_of_payment = category

    @quantity.setter
    def quantity(self, quantity: int) -> None:
        if quantity < 1:
            raise ValueError("Quantity must be at least 1.")
        self._quantity = quantity

    def convert_to_dict(self) -> dict:
        return {
            "expense_id": self._expense_id,
            "name": self.name,
            "amount": self.amount,
            "quantity": self.quantity,
            "mode_of_payment": self.mode_of_payment,
            "category_of_payment": self.category_of_payment,
            "timestamp": self.timestamp,
            "receipt": self.receipt,
            "comments": self.comments
        }
    
    def save_to_json(self, filepath: str = json_path) -> None:
        if os.path.exists(filepath): # Load data if file exists
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                data = []
        else:
            data = []
        data.append(self.convert_to_dict()) # Append the entry
        os.makedirs(os.path.dirname(filepath), exist_ok=True) # Check if target directory exists again (?)
        with open(filepath, "w", encoding="utf-8") as file: # Write to json
            json.dump(data, file, indent=4)

    def __str__(self) -> str:
        return (
            f"Expense ID:          {self._expense_id}\n"
            f"Name:                {self.name}\n"
            f"Amount:              P{self.amount:,.2f}\n"
            f"Quantity:            {self.quantity}\n"
            f"Mode of Payment:     {self.mode_of_payment}\n"
            f"Category of Payment: {self.category_of_payment}\n"
            f"Timestamp:           {self.timestamp}\n"
            f"Receipt:             {self.receipt}\n"
            f"Comments:            {', '.join(self.comments)}"
        )

    def display_transaction(self) -> None:
        print(self)
        
class Income(Transaction):
    def __init__(
            self, 
            name: str, 
            amount: float, 
            mode_of_payment: str,
            category_of_income: str,
            receipt: Receipt = None,
            comments: list = None,
        ):
        super().__init__(name, amount, mode_of_payment, receipt, comments)
        self._category_of_income = category_of_income
        self._income_id = id_generator("income")
        self._json_path = "income_expense_tracker/iet_json_files/income.json"
    
    @property
    def category_of_income(self) -> str:
        return self._category_of_income
    
    @property
    def json_path(self) -> str:
        return self._json_path

    @category_of_income.setter
    def category_of_income(self, category: str) -> None:
        self._category_of_income = category

    def convert_to_dict(self) -> dict:
        return {
            "income_id": self._income_id,
            "name": self.name,
            "amount": self.amount,
            "mode_of_payment": self.mode_of_payment,
            "category_of_income": self.category_of_income,
            "timestamp": self.timestamp,
            "receipt": self.receipt,
            "comments": self.comments
        }
    
    def save_to_json(self, filepath: str = json_path) -> None:
        if os.path.exists(filepath): # Load data if file exists
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                data = []
        else:
            data = []
        data.append(self.convert_to_dict()) # Append the entry
        os.makedirs(os.path.dirname(filepath), exist_ok=True) # Check if target directory exists again (?)
        with open(filepath, "w", encoding="utf-8") as file: # Write to json
            json.dump(data, file, indent=4)

    def __str__(self) -> str:
        return (
            f"Income ID:           {self._income_id}\n"
            f"Name:                {self.name}\n"
            f"Amount:              P{self.amount:,.2f}\n"
            f"Mode of Payment:     {self.mode_of_payment}\n"
            f"Category of Income:  {self.category_of_income}\n"
            f"Timestamp:           {self.timestamp}\n"
            f"Receipt:             {self.receipt}\n"
            f"Comments:            {', '.join(self.comments)}"
        )

    def display_transaction(self) -> None:
        print(self)


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

