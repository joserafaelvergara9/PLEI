import sys
import os
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
from abc import ABC, abstractmethod
from datetime import datetime
from receipt import Receipt, DataFileError, read_json_list, write_json_list
from general_purpose_functions.id_generator import id_generator

VALID_PAYMENT_METHODS = ["cash", "credit", "debit", "qrph", "paypal", "venmo"]

# The folder where this file is located, so the data files are always found next to it no matter where the program is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPENSES_JSON_PATH = os.path.join(BASE_DIR, "iet_json_files", "expenses.json")
INCOME_JSON_PATH = os.path.join(BASE_DIR, "iet_json_files", "income.json")
EXPENSE_CATEGORIES_PATH = os.path.join(BASE_DIR, "custom_categories", "expense_categories.json")
INCOME_CATEGORIES_PATH = os.path.join(BASE_DIR, "custom_categories", "income_categories.json")


# Custom errors, which are kinds of Value Error so a single "except ValueError" also catches them
class InvalidCategoryError(ValueError):
    pass

class InvalidPaymentMethodError(ValueError):
    pass


class Transaction(ABC):
    def __init__(
            self,
            name: str,
            amount: float,
            mode_of_payment: str,
            receipt: Receipt = None,
            comments: list = None,
            timestamp: datetime = None
        ):
        self.name = name
        self.amount = amount
        self.mode_of_payment = mode_of_payment
        self.timestamp = datetime.now() if timestamp is None else timestamp
        self.receipt = receipt
        self.comments = comments

    # Static methods that return the cleaned version of a value, or raise Value Error if it is not valid
    # The setters use them, and so can the menu, to check one value at a time
    @staticmethod
    def clean_text(value, label):
        return Receipt.clean_text(value, label)

    @staticmethod
    def clean_name(value):
        return Receipt.clean_text(value, "Name")

    @staticmethod
    def clean_amount(value):
        return Receipt.clean_amount(value)

    @staticmethod
    def clean_mode_of_payment(value):
        text = Receipt.clean_text(value, "Mode of payment").lower()
        if text not in VALID_PAYMENT_METHODS:
            raise InvalidPaymentMethodError(f"Unknown mode of payment: {value.strip()}")
        return text

    @staticmethod
    def clean_timestamp(value):
        return Receipt.clean_timestamp(value)

    # None becomes an empty list, otherwise it must be a list of non-empty strings
    @staticmethod
    def clean_comments(value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("Comments must be a list of text.")
        return [Receipt.clean_text(comment, "Comment") for comment in value]

    # None is allowed, a Receipt is kept as it is, and a dictionary (from a JSON file) is turned into a Receipt
    @staticmethod
    def clean_receipt(value):
        if value is None or isinstance(value, Receipt):
            return value
        if isinstance(value, dict):
            return Receipt.load_from_dict(value)
        raise ValueError("Receipt must be a Receipt object or None.")

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value):
        self._name = self.clean_name(value)

    @property
    def amount(self) -> float:
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = self.clean_amount(value)

    @property
    def mode_of_payment(self) -> str:
        return self._mode_of_payment

    @mode_of_payment.setter
    def mode_of_payment(self, value):
        self._mode_of_payment = self.clean_mode_of_payment(value)

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = self.clean_timestamp(value)

    @property
    def receipt(self) -> Receipt:
        return self._receipt

    @receipt.setter
    def receipt(self, value):
        self._receipt = self.clean_receipt(value)

    @property
    def comments(self) -> list:
        return self._comments

    @comments.setter
    def comments(self, value):
        self._comments = self.clean_comments(value)

    def add_comment(self, comment: str) -> None:
        self._comments.append(Receipt.clean_text(comment, "Comment"))

    def remove_comment(self, comment: str) -> None:
        if comment not in self._comments:
            raise ValueError("That comment was not found.")
        self._comments.remove(comment)

    # A method to return the fields that every kind of transaction has, in a form that can be saved as JSON
    def _common_fields_as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "receipt": self.receipt.convert_to_dict() if self.receipt is not None else None,
            "comments": list(self.comments)
        }

    @property
    @abstractmethod
    def transaction_id(self) -> str:
        pass

    @property
    @abstractmethod
    def json_path(self) -> str:
        pass

    @abstractmethod
    def convert_to_dict(self) -> dict:
        pass


# A mixin that gives Expense and Income their own list of valid categories, which is loaded from and saved to a JSON file
# Each subclass must define its own valid_categories list and custom_categories_path
class _CategoryRegistry:
    valid_categories = []
    custom_categories_path = None
    # The reason why changing the categories is blocked (so a bad file is not overwritten), or None
    _categories_error = None

    # A class method to load the valid categories from the JSON file and return how many were loaded, or raises DataFileError and blocks changes if the file is not valid
    # A missing file is not an error and just means there are no categories yet
    @classmethod
    def load_valid_categories(cls) -> int:
        cls.valid_categories.clear()
        cls._categories_error = None
        try:
            data = read_json_list(cls.custom_categories_path)
            categories = []
            for number, item in enumerate(data, start=1):
                if not isinstance(item, str) or not item.strip():
                    raise DataFileError(f"Category {number} in '{cls.custom_categories_path}' is not a non-empty text")
                name = item.strip().lower()
                if name not in categories:
                    categories.append(name)
        except DataFileError as error:
            cls._categories_error = f"{error}; changing the categories is blocked so the file cannot be overwritten."
            raise DataFileError(cls._categories_error) from error
        cls.valid_categories.extend(categories)
        return len(categories)

    # A class method to return the cleaned version of a category, or raises InvalidCategoryError if it is not one of the valid categories
    @classmethod
    def clean_category(cls, value):
        name = Receipt.clean_text(value, "Category").lower()
        if name not in cls.valid_categories:
            raise InvalidCategoryError(f"Unknown category: {value.strip()}")
        return name

    # A class method to add a category and save it, or if saving fails, removes it again and raises DataFileError
    @classmethod
    def add_valid_category(cls, category_name: str) -> str:
        if cls._categories_error:
            raise DataFileError(cls._categories_error)
        name = Receipt.clean_text(category_name, "Category").lower()
        if name in cls.valid_categories:
            raise ValueError(f"The category '{name}' already exists.")
        cls.valid_categories.append(name)
        try:
            write_json_list(cls.custom_categories_path, cls.valid_categories)
        except DataFileError:
            cls.valid_categories.remove(name)
            raise
        return name

    # A class method to delete a category and save, or if saving fails, puts it back and raises DataFileError
    @classmethod
    def delete_valid_category(cls, category_name: str) -> str:
        if cls._categories_error:
            raise DataFileError(cls._categories_error)
        name = Receipt.clean_text(category_name, "Category").lower()
        if name not in cls.valid_categories:
            raise ValueError(f"The category '{name}' does not exist.")
        position = cls.valid_categories.index(name)
        cls.valid_categories.remove(name)
        try:
            write_json_list(cls.custom_categories_path, cls.valid_categories)
        except DataFileError:
            cls.valid_categories.insert(position, name)
            raise
        return name


class Expense(_CategoryRegistry, Transaction):
    valid_categories = []
    custom_categories_path = EXPENSE_CATEGORIES_PATH
    # The fields that must be in a dictionary for load_from_dict (receipt and comments are optional)
    REQUIRED_FIELDS = (
        "expense_id", "name", "amount", "quantity",
        "mode_of_payment", "category_of_payment", "timestamp"
    )

    def __init__(
            self,
            name: str,
            amount: float,
            mode_of_payment: str,
            category_of_payment: str,
            quantity: int = 1,
            receipt: Receipt = None,
            comments: list = None,
            expense_id: str = None,
            timestamp: datetime = None
        ):
        super().__init__(name, amount, mode_of_payment, receipt, comments, timestamp)
        self.category_of_payment = category_of_payment
        self.quantity = quantity
        self._expense_id = id_generator("expense") if expense_id is None else self.clean_text(expense_id, "Expense ID")

    # A static method to return the quantity, or raises Value Error if it is not a whole number of at least 1
    @staticmethod
    def clean_quantity(value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Quantity must be a whole number.")
        if value < 1:
            raise ValueError("Quantity must be at least 1.")
        return value

    @property
    def expense_id(self) -> str:
        return self._expense_id

    @property
    def transaction_id(self) -> str:
        return self._expense_id

    @property
    def json_path(self) -> str:
        return EXPENSES_JSON_PATH

    @property
    def category_of_payment(self) -> str:
        return self._category_of_payment

    @category_of_payment.setter
    def category_of_payment(self, category: str) -> None:
        self._category_of_payment = self.clean_category(category)

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, quantity: int) -> None:
        self._quantity = self.clean_quantity(quantity)

    # Converts an expense object into a dictionary
    def convert_to_dict(self) -> dict:
        data = {
            "expense_id": self._expense_id,
            "name": self.name,
            "amount": self.amount,
            "quantity": self.quantity,
            "mode_of_payment": self.mode_of_payment,
            "category_of_payment": self.category_of_payment
        }
        data.update(self._common_fields_as_dict())
        return data

    # A class method to create an expense from a dictionary, or raises Value Error if it is not a dict or has missing fields or invalid values
    @classmethod
    def load_from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Expense data must be a dictionary type")
        missing_fields = [field for field in cls.REQUIRED_FIELDS if field not in data]
        if missing_fields:
            raise ValueError(f"Missing fields: {', '.join(missing_fields)}")
        return cls(
            name=data["name"],
            amount=data["amount"],
            mode_of_payment=data["mode_of_payment"],
            category_of_payment=data["category_of_payment"],
            quantity=data["quantity"],
            receipt=data.get("receipt"),
            comments=data.get("comments"),
            expense_id=data["expense_id"],
            timestamp=data["timestamp"]
        )

    def __str__(self) -> str:
        return (
            f"Expense ID:          {self._expense_id}\n"
            f"Name:                {self.name}\n"
            f"Amount:              P{self.amount:,.2f}\n"
            f"Quantity:            {self.quantity}\n"
            f"Mode of Payment:     {self.mode_of_payment}\n"
            f"Category of Payment: {self.category_of_payment}\n"
            f"Timestamp:           {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Receipt:             {self.receipt if self.receipt is not None else 'None'}\n"
            f"Comments:            {self.comments}"
        )


class Income(_CategoryRegistry, Transaction):
    valid_categories = []
    custom_categories_path = INCOME_CATEGORIES_PATH
    # The fields that must be in a dictionary for load_from_dict (receipt and comments are optional)
    REQUIRED_FIELDS = (
        "income_id", "name", "amount",
        "mode_of_payment", "category_of_income", "timestamp"
    )

    def __init__(
            self,
            name: str,
            amount: float,
            mode_of_payment: str,
            category_of_income: str,
            receipt: Receipt = None,
            comments: list = None,
            income_id: str = None,
            timestamp: datetime = None
        ):
        super().__init__(name, amount, mode_of_payment, receipt, comments, timestamp)
        self.category_of_income = category_of_income
        self._income_id = id_generator("income") if income_id is None else self.clean_text(income_id, "Income ID")

    @property
    def income_id(self) -> str:
        return self._income_id

    @property
    def transaction_id(self) -> str:
        return self._income_id

    @property
    def json_path(self) -> str:
        return INCOME_JSON_PATH

    @property
    def category_of_income(self) -> str:
        return self._category_of_income

    @category_of_income.setter
    def category_of_income(self, category: str) -> None:
        self._category_of_income = self.clean_category(category)

    # Converts an income object into a dictionary
    def convert_to_dict(self) -> dict:
        data = {
            "income_id": self._income_id,
            "name": self.name,
            "amount": self.amount,
            "mode_of_payment": self.mode_of_payment,
            "category_of_income": self.category_of_income
        }
        data.update(self._common_fields_as_dict())
        return data

    # A class method to create an income from a dictionary, or raises Value Error if it is not a dict or has missing fields or invalid values
    @classmethod
    def load_from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Income data must be a dictionary type")
        missing_fields = [field for field in cls.REQUIRED_FIELDS if field not in data]
        if missing_fields:
            raise ValueError(f"Missing fields: {', '.join(missing_fields)}")
        return cls(
            name=data["name"],
            amount=data["amount"],
            mode_of_payment=data["mode_of_payment"],
            category_of_income=data["category_of_income"],
            receipt=data.get("receipt"),
            comments=data.get("comments"),
            income_id=data["income_id"],
            timestamp=data["timestamp"]
        )

    def __str__(self) -> str:
        return (
            f"Income ID:           {self._income_id}\n"
            f"Name:                {self.name}\n"
            f"Amount:              P{self.amount:,.2f}\n"
            f"Mode of Payment:     {self.mode_of_payment}\n"
            f"Category of Income:  {self.category_of_income}\n"
            f"Timestamp:           {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Receipt:             {self.receipt if self.receipt is not None else 'None'}\n"
            f"Comments:            {self.comments}"
        )