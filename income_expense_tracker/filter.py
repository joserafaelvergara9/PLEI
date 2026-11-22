import math
from datetime import datetime
from transaction import Transaction, Expense, Income, VALID_PAYMENT_METHODS, InvalidPaymentMethodError


class Filter:
    def __init__(
            self,
            transaction_subclass: type | None = None,
            category: str | None = None,
            mode_of_payment: str | None = None,
            timestamp_range: tuple | None = None,
            amount_range: tuple | None = None,
        ):
        self._transaction_subclass = self._cleaned_subclass(transaction_subclass)
        self._category = self._cleaned_category(category)
        self._mode_of_payment = self._cleaned_mode_of_payment(mode_of_payment)
        self._timestamp_range = self._cleaned_range(
            timestamp_range, "Timestamp range",
            lambda bound: isinstance(bound, datetime),
            "a datetime"
        )
        self._amount_range = self._cleaned_range(
            amount_range, "Amount range",
            lambda bound: not isinstance(bound, bool) and isinstance(bound, (int, float)) and math.isfinite(bound),
            "a number"
        )

    # A static method to return the subclass, or raises Value Error if it is not None or a Transaction class (Expense or Income)
    @staticmethod
    def _cleaned_subclass(value):
        if value is None:
            return None
        if not isinstance(value, type) or not issubclass(value, Transaction):
            raise ValueError("Transaction subclass must be Expense, Income, or None.")
        return value

    # A static method to return the category stripped and in lowercase, or raises Value Error if it is not None or a non-empty string
    @staticmethod
    def _cleaned_category(value):
        if value is None:
            return None
        return Transaction.clean_text(value, "Category").lower()

    # A static method to return the mode of payment stripped and in lowercase, or raises InvalidPaymentMethodError if it is not a valid one
    @staticmethod
    def _cleaned_mode_of_payment(value):
        if value is None:
            return None
        text = Transaction.clean_text(value, "Mode of payment").lower()
        if text not in VALID_PAYMENT_METHODS:
            raise InvalidPaymentMethodError(f"Unknown mode of payment: {value.strip()}")
        return text

    # A static method to return a (minimum, maximum) tuple, or None if there is no range at all
    # Either side may be None to leave it open, and raises Value Error if the range is not a pair, a side is the wrong type, or the minimum is above the maximum
    @staticmethod
    def _cleaned_range(value, label, is_valid_bound, expected_type):
        if value is None:
            return None
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise ValueError(f"{label} must be a (minimum, maximum) pair.")
        low, high = value
        for bound in (low, high):
            if bound is not None and not is_valid_bound(bound):
                raise ValueError(f"Each side of the {label.lower()} must be {expected_type} or None.")
        if low is None and high is None:
            return None
        if low is not None and high is not None and low > high:
            raise ValueError(f"The start of the {label.lower()} cannot be after its end.")
        return (low, high)

    @property
    def transaction_subclass(self) -> type | None:
        return self._transaction_subclass

    @property
    def category(self) -> str | None:
        return self._category

    @property
    def mode_of_payment(self) -> str | None:
        return self._mode_of_payment

    @property
    def timestamp_range(self) -> tuple | None:
        return self._timestamp_range

    @property
    def amount_range(self) -> tuple | None:
        return self._amount_range

    # helper function for the main matches() function in terms of filtering for the category
    def _matches_category(self, transaction: Transaction) -> bool:
        if self.category is None:
            return True
        if isinstance(transaction, Expense):
            return transaction.category_of_payment == self.category
        if isinstance(transaction, Income):
            return transaction.category_of_income == self.category
        return False

    # returns True if Transaction object matches the filters of a Filter object, else False
    def matches(self, transaction: Transaction) -> bool:
        if not isinstance(transaction, Transaction):
            raise TypeError("matches() requires a Transaction object")

        # by subclass
        if self.transaction_subclass is not None and not isinstance(transaction, self.transaction_subclass):
            return False

        # by category
        if not self._matches_category(transaction):
            return False

        # by mode of payment
        if self.mode_of_payment is not None and transaction.mode_of_payment != self.mode_of_payment:
            return False

        # by range of time
        if self.timestamp_range is not None:
            start_date, end_date = self.timestamp_range
            if start_date is not None and transaction.timestamp < start_date:
                return False
            if end_date is not None and transaction.timestamp > end_date:
                return False

        # by range of amount
        if self.amount_range is not None:
            min_amount, max_amount = self.amount_range
            if min_amount is not None and transaction.amount < min_amount:
                return False
            if max_amount is not None and transaction.amount > max_amount:
                return False

        # default
        return True

    # returns a new list of only the transactions that match the filters, in their original order
    def apply_filter(self, transactions: list) -> list:
        return [transaction for transaction in transactions if self.matches(transaction)]

    def __str__(self) -> str:
        subclass_name = self.transaction_subclass.__name__ if self.transaction_subclass else None
        return (
            f"Transaction Subclass:     {subclass_name}\n"
            f"Category:                 {self.category}\n"
            f"Mode of Payment:          {self.mode_of_payment}\n"
            f"Timestamp Range:          {self.timestamp_range}\n"
            f"Amount Range:             {self.amount_range}\n"
        )