from income_expense_tracker.transaction import Transaction, Expense, Income

class Filter:
    def __init__(
            self, 
            transaction_subclass: type | None, 
            category: str | None, 
            mode_of_payment: str | None,
            timestamp_range: tuple | None,
            amount_range: tuple | None,
        ):
        self._transaction_subclass = transaction_subclass
        self._category = category
        self._mode_of_payment = mode_of_payment
        self._timestamp_range = timestamp_range
        self._amount_range = amount_range

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
        if isinstance(transaction, Expense) and getattr(transaction, "category_of_payment", None) == self.category:
            return True
        if isinstance(transaction, Income) and getattr(transaction, "category_of_income", None) == self.category:
            return True
        return False

    # returns True if Transaction object matches the filters of a Filter object, else False
    def matches(self, transaction: Transaction) -> bool:
        # by subclass
        if self.transaction_subclass and not isinstance(transaction, self.transaction_subclass):
            return False

        # by category
        if self.category and not self._matches_category(transaction):
            return False

        # by mode of payment
        if self.mode_of_payment and transaction.mode_of_payment.lower() != self.mode_of_payment.lower():
            return False

        # by range of time
        if self.timestamp_range:
            start_date, end_date = self.timestamp_range
            if start_date and transaction.timestamp < start_date:
                return False
            if end_date and transaction.timestamp > end_date:
                return False

        # by range of amount
        if self.amount_range:
            min_amount, max_amount = self.amount_range
            if min_amount is not None and transaction.amount < min_amount:
                return False
            if max_amount is not None and transaction.amount > max_amount:
                return False

        # default
        return True

    def __str__(self) -> str:
        return (
            f"Transaction Subclass:     {self.transaction_subclass}\n"
            f"Category:                 {self.category}\n"
            f"Mode of Payment:          {self.mode_of_payment}\n"
            f"Timestamp Range:          {self.timestamp_range}\n"
            f"Amount Range:             {self.amount_range}\n"
        )

    def apply_filter(self):
        pass