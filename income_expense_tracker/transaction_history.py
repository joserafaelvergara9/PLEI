import os
from transaction import (
    Transaction,
    Expense,
    Income,
    DataFileError,
    read_json_list,
    write_json_list,
    EXPENSES_JSON_PATH,
    INCOME_JSON_PATH,
)
from filter import Filter

# The default paths of the JSON files that the transactions are exported to
EXPORT_DIR = os.path.dirname(EXPENSES_JSON_PATH)
EXPORTED_EXPENSES_PATH = os.path.join(EXPORT_DIR, "exported_expense_data.json")
EXPORTED_INCOME_PATH = os.path.join(EXPORT_DIR, "exported_income_data.json")


# A custom error to raise when adding a transaction whose ID already exists
class DuplicateTransactionError(Exception):
    pass

# A custom error to raise when a transaction with the given ID cannot be found
class TransactionNotFoundError(Exception):
    pass


class TransactionHistory:
    def __init__(
            self,
            transactions: list | None = None,
            expenses_path: str = EXPENSES_JSON_PATH,
            income_path: str = INCOME_JSON_PATH
        ):
        self.transactions = []
        self.expenses_path = expenses_path
        self.income_path = income_path
        self._reason_for_blocking_save = None
        # Transactions given here are only put in the list, and are not saved until the next save
        for transaction in transactions or []:
            self._insert(transaction)

    # A static method to return a stripped version of an ID, or if it is not a string or is empty, raises Value Error
    @staticmethod
    def _cleaned_id(transaction_id):
        return Transaction.clean_text(transaction_id, "Transaction ID")

    # A method to return True if a transaction with the given ID is in the history, or False if not
    def exists(self, transaction_id):
        key = self._cleaned_id(transaction_id).lower()
        return any(t.transaction_id.lower() == key for t in self.transactions)

    # A method to store the reason for blocking saving, so the files cannot be overwritten, and return a DataFileError with that reason
    def _block_from_saving(self, problem):
        self._reason_for_blocking_save = (
            f"{problem}; The data files remain untouched, "
            f"and saving is blocked so they cannot be overwritten. "
            f"Fix or rename the file then restart."
        )
        return DataFileError(self._reason_for_blocking_save)

    # A method to load the transactions from the JSON files and return how many were loaded, or raises DataFileError and blocks saving if a file is not valid
    def load(self):
        # Clear any transactions and any reason for blocking saving from before
        self.transactions = []
        self._reason_for_blocking_save = None

        try:
            expense_records = read_json_list(self.expenses_path)
            income_records = read_json_list(self.income_path)
        except DataFileError as error:
            raise self._block_from_saving(str(error)) from error

        # A list of the transactions loaded so far, which only replaces the current ones once every record is valid
        loaded = []
        seen_ids = set()
        for label, transaction_class, records in (
            ("expenses", Expense, expense_records),
            ("income", Income, income_records),
        ):
            for number, record in enumerate(records, start=1):
                try:
                    transaction = transaction_class.load_from_dict(record)
                except ValueError as error:
                    raise self._block_from_saving(f"Record {number} in the {label} file is invalid: {error}") from error
                key = transaction.transaction_id.lower()
                if key in seen_ids:
                    raise self._block_from_saving(f"Record {number} in the {label} file repeats the ID '{transaction.transaction_id}'")
                seen_ids.add(key)
                loaded.append(transaction)

        self.transactions = loaded
        return len(self.transactions)

    # A static method to turn a list of transactions into a list of dictionaries, sorted by time
    @staticmethod
    def _as_dicts(transactions):
        ordered = sorted(transactions, key=lambda t: (t.timestamp, t.transaction_id))
        return [transaction.convert_to_dict() for transaction in ordered]

    # A method to save all transactions to their JSON files, or raises DataFileError if saving is blocked or a file cannot be written
    def save(self):
        if self._reason_for_blocking_save:
            raise DataFileError(self._reason_for_blocking_save)
        expenses = [t for t in self.transactions if isinstance(t, Expense)]
        income = [t for t in self.transactions if isinstance(t, Income)]
        write_json_list(self.expenses_path, self._as_dicts(expenses))
        write_json_list(self.income_path, self._as_dicts(income))

    # A method to add a transaction to the list without saving, or raises TypeError if it is not a Transaction or raises DuplicateTransactionError if the ID already exists
    def _insert(self, transaction):
        if not isinstance(transaction, Transaction):
            raise TypeError("_insert() requires a Transaction object")
        if self.exists(transaction.transaction_id):
            raise DuplicateTransactionError(f"A transaction with ID '{transaction.transaction_id}' already exists")
        self.transactions.append(transaction)

    # A method to add a transaction to the list and save, or if saving fails, removes the transaction again and raises DataFileError
    def add_transaction(self, transaction):
        self._insert(transaction)
        try:
            self.save()
        except DataFileError:
            # Undo the insert, then raise the same error again
            self.transactions.remove(transaction)
            raise

    # A method to remove the transaction with the given ID, save, and return it, or raises TransactionNotFoundError if there is no such transaction, or if saving fails, puts it back and raises DataFileError
    def remove_transaction(self, transaction_id):
        transaction = self.search_by_id(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError(f"No transaction with ID '{self._cleaned_id(transaction_id)}' found")
        position = self.transactions.index(transaction)
        self.transactions.remove(transaction)
        try:
            self.save()
        except DataFileError:
            # Put the transaction back where it was, then raise the same error again
            self.transactions.insert(position, transaction)
            raise
        return transaction

    # A method to return a list of all transactions, sorted by time
    def read_all(self):
        return sorted(self.transactions, key=lambda t: (t.timestamp, t.transaction_id))

    # A method to return the transaction with the given ID, or None if there is no such transaction
    def search_by_id(self, transaction_id):
        key = self._cleaned_id(transaction_id).lower()
        for transaction in self.transactions:
            if transaction.transaction_id.lower() == key:
                return transaction
        return None

    # A method to return a list of all transactions whose name contains the given text (not case sensitive), sorted by time
    def search_by_name(self, name):
        key = Transaction.clean_text(name, "Name").lower()
        return [t for t in self.read_all() if key in t.name.lower()]

    # A method to return a list of the transactions that match the filter, sorted by time
    def filter_transactions(self, filter: Filter):
        if not isinstance(filter, Filter):
            raise TypeError("filter_transactions() requires a Filter object")
        return filter.apply_filter(self.read_all())

    # A method to return True if any transaction of the given subclass uses the given category, so a category that is in use is not deleted
    def category_in_use(self, transaction_subclass, category):
        used = Filter(transaction_subclass=transaction_subclass, category=category)
        return len(used.apply_filter(self.transactions)) > 0

    # A method to export the expenses and the income to their own JSON files and return how many of each were written
    # A file is only created if it has at least one record, so (0, 0) means nothing was exported
    def export_transaction_history(self, expenses_path=EXPORTED_EXPENSES_PATH, income_path=EXPORTED_INCOME_PATH):
        expenses = [t for t in self.transactions if isinstance(t, Expense)]
        income = [t for t in self.transactions if isinstance(t, Income)]
        if expenses:
            write_json_list(expenses_path, self._as_dicts(expenses))
        if income:
            write_json_list(income_path, self._as_dicts(income))
        return len(expenses), len(income)