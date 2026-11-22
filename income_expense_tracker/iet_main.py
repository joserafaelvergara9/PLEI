import os
from datetime import datetime

from receipt import Receipt, DataFileError
from transaction import Transaction, Expense, Income, VALID_PAYMENT_METHODS
from filter import Filter
from transaction_history import (
    TransactionHistory,
    DuplicateTransactionError,
    TransactionNotFoundError,
    EXPORTED_EXPENSES_PATH,
    EXPORTED_INCOME_PATH,
)

# The text the user can type to choose a kind of transaction, and the class it stands for
SUBCLASSES = {"income": Income, "expense": Expense}
# The format the user types a date and time in
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


# A class that handles the menu and all the user input and output, while the transaction history handles the storing of the data
class IncomeExpenseTrackerManager:
    def __init__(self, transaction_history):
        self.transaction_history = transaction_history

    # Static methods to convert the text typed by the user to the right type, or raise Value Error if it cannot be converted
    @staticmethod
    def _to_float(text):
        try:
            return float(text)
        except ValueError:
            # "from None" hides the original float() error so only the friendlier message is shown
            raise ValueError("Value must be a number") from None

    @staticmethod
    def _to_int(text):
        try:
            return int(text)
        except ValueError:
            raise ValueError("Value must be a whole number") from None

    @staticmethod
    def _to_datetime(text):
        try:
            return datetime.strptime(text, DATETIME_FORMAT)
        except ValueError:
            raise ValueError("Date and time must be in the format YYYY-MM-DD HH:MM") from None

    # A static method to keep asking for one value until a valid one is entered, and return it
    # converter turns the typed text into the right type, and cleaner checks the value and raises Value Error if it is not valid
    # If optional is True, pressing Enter skips the question and returns None
    @staticmethod
    def _ask_field(label, cleaner=None, converter=None, optional=False):
        while True:
            suffix = " (Enter to skip)" if optional else ""
            text = input(f"{label}{suffix}: ").strip()
            if optional and not text:
                return None
            try:
                value = converter(text) if converter else text
                return cleaner(value) if cleaner else value
            except ValueError as error:
                print(f"  Invalid input: {str(error).rstrip('.')}. Please try again.")

    # A static method to ask a yes or no question until the user answers, and return True for yes or False for no
    @staticmethod
    def _confirm(question):
        while True:
            answer = input(f"{question} (y/n): ").strip().lower()
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no"):
                return False
            print("Please answer with y or n")

    # A static method to ask for comments one at a time until the user presses Enter, and return them as a list
    @staticmethod
    def _ask_comments():
        comments = []
        while True:
            text = input("Add a comment (Enter to finish): ").strip()
            if not text:
                return comments
            comments.append(text)

    # A method to ask if the user wants to attach a receipt, and return a Receipt for the given amount or None
    def _ask_receipt(self, amount):
        if not self._confirm("Attach a receipt?"):
            return None
        organization = self._ask_field("Receipt organization", lambda v: Receipt.clean_text(v, "Organization"))
        address = self._ask_field("Receipt address", lambda v: Receipt.clean_text(v, "Address"))
        return Receipt(amount, organization, address)

    # A method to ask for a transaction ID and return the matching transaction, or print a message and return None if the ID is not valid or no transaction has it
    def _find_transaction(self):
        transaction_id = input("Enter the transaction ID: ").strip()
        try:
            transaction = self.transaction_history.search_by_id(transaction_id)
        except ValueError as error:
            print(f"  {error}")
            return None
        if transaction is None:
            print(f"  No transaction with ID '{transaction_id}' was found")
        return transaction

    # A static method to print a list of transactions, with the total count
    @staticmethod
    def _print_transactions(transactions):
        for transaction in transactions:
            print("**********************")
            print(transaction)
            print("**********************")
        print(f"\nTotal: {len(transactions)} transaction(s)")

    # A static method to print the main menu
    @staticmethod
    def _show_menu():
        print()
        print("=-" * 17)
        print("   INCOME AND EXPENSE TRACKER")
        print("=-" * 17)
        print("[1] Add Transaction")
        print("[2] Remove Transaction")
        print("[3] Show Transaction History")
        print("[4] Search Transactions by ID")
        print("[5] Search Transactions by Name")
        print("[6] Filter Transactions")
        print("[7] Export Transactions")
        print("[8] Add a Category")
        print("[9] Delete a Category")
        print("[10] Exit")

    # A static method to print the filter menu
    @staticmethod
    def _show_filter_menu():
        print("Filter by any of these (you will be asked about each one):")
        print("  - Transaction Subclass (income or expense)")
        print("  - Transaction Category")
        print("  - Mode of Payment")
        print("  - Time Range")
        print("  - Amount Range")

    # A method to ask for the shared fields of a transaction, and return them as a dictionary
    # The words "income" or "expense" are used in the prompts, and category_class is Income or Expense
    def _ask_shared_fields(self, kind, category_class):
        name = self._ask_field(f"{kind.capitalize()} name", Transaction.clean_name)
        amount = self._ask_field(f"{kind.capitalize()} amount", Transaction.clean_amount, self._to_float)
        print(f"Valid modes of payment: {', '.join(VALID_PAYMENT_METHODS)}")
        mode_of_payment = self._ask_field("Mode of payment", Transaction.clean_mode_of_payment)
        print(f"Valid categories: {', '.join(category_class.valid_categories)}")
        category = self._ask_field(f"{kind.capitalize()} category", category_class.clean_category)
        return {"name": name, "amount": amount, "mode_of_payment": mode_of_payment, "category": category}

    # [1] Add Transaction
    # A method to ask whether to add an income or an expense
    def add_transaction(self):
        print("\n=-= Add Transaction =-=")
        choice = input("Enter '1' to create an income transaction or '2' to create an expense transaction: ").strip()
        match choice:
            case "1":
                self._add_income()
            case "2":
                self._add_expense()
            case _:
                print("  Invalid choice. Please try again.")

    # A method to ask for every field of a new income, then add it to the history and save
    def _add_income(self):
        if not Income.valid_categories:
            print("  There are no income categories yet. Add one first with option 8.")
            return
        fields = self._ask_shared_fields("income", Income)
        receipt = self._ask_receipt(fields["amount"])
        comments = self._ask_comments()

        # The values were already checked one by one, so these errors are only a safety net
        try:
            income = Income(
                fields["name"], fields["amount"], fields["mode_of_payment"],
                fields["category"], receipt, comments
            )
            self.transaction_history.add_transaction(income)
        except ValueError as error:
            print(f"  Could not add the income: {error}")
        except DuplicateTransactionError as error:
            print(f"  {error}.")
        except DataFileError as error:
            print(f"  {error}\n  The income was not added.")
        else:
            # The else block only runs if no error was raised
            print(f"Income {income.income_id} was added and saved.")

    # A method to ask for every field of a new expense, then add it to the history and save
    def _add_expense(self):
        if not Expense.valid_categories:
            print("  There are no expense categories yet. Add one first with option 8.")
            return
        fields = self._ask_shared_fields("expense", Expense)
        quantity = self._ask_field("Quantity", Expense.clean_quantity, self._to_int)
        # The receipt is for the total that was paid, so the amount is multiplied by the quantity (rounded to centavos)
        receipt = self._ask_receipt(round(fields["amount"] * quantity, 2))
        comments = self._ask_comments()

        try:
            expense = Expense(
                fields["name"], fields["amount"], fields["mode_of_payment"],
                fields["category"], quantity, receipt, comments
            )
            self.transaction_history.add_transaction(expense)
        except ValueError as error:
            print(f"  Could not add the expense: {error}")
        except DuplicateTransactionError as error:
            print(f"  {error}.")
        except DataFileError as error:
            print(f"  {error}\n  The expense was not added.")
        else:
            print(f"Expense {expense.expense_id} was added and saved.")

    # [2] Remove Transaction
    # A method to find a transaction, ask for confirmation, then remove it from the history and save
    def remove_transaction(self):
        print("\n=-= Remove Transaction =-=")
        transaction = self._find_transaction()
        if transaction is None:
            return
        print(transaction)
        if not self._confirm("Are you sure you want to remove this transaction?"):
            print("Removal cancelled.")
            return
        try:
            self.transaction_history.remove_transaction(transaction.transaction_id)
        except TransactionNotFoundError as error:
            print(f"  {error}.")
        except DataFileError as error:
            print(f"  {error}\n  The transaction was not removed.")
        else:
            print(f"Transaction {transaction.transaction_id} was removed and saved.")

    # [3] Show Transaction History
    def show_transaction_history(self):
        print("\n=-= Transaction History =-=")
        transactions = self.transaction_history.read_all()
        if not transactions:
            print("No transactions found.")
            return
        self._print_transactions(transactions)

    # [4] Search Transactions by ID
    def search_by_id(self):
        print("\n=-= Search Transaction by ID =-=")
        transaction = self._find_transaction()
        if transaction is not None:
            print("Transaction found:")
            print(transaction)

    # [5] Search Transactions by Name
    def search_by_name(self):
        print("\n=-= Search Transactions by Name =-=")
        name = input("Enter the transaction name to search: ").strip()
        try:
            results = self.transaction_history.search_by_name(name)
        except ValueError as error:
            print(f"  {error}")
            return
        if not results:
            print(f"No transaction with a name containing '{name}' was found.")
            return
        print("Search Results:")
        self._print_transactions(results)

    # [6] Filter Transactions
    # A method to ask which filters to use, then print the transactions that match all of them
    def filter_transactions(self):
        print("\n=-= Filter Transactions =-=")
        self._show_filter_menu()

        # Filter by transaction subclass
        transaction_subclass = None
        if self._confirm("Filter by transaction subclass?"):
            while True:
                text = input("Enter 'income' or 'expense': ").strip().lower()
                if text in SUBCLASSES:
                    transaction_subclass = SUBCLASSES[text]
                    break
                print("  Please enter 'income' or 'expense'.")

        # Filter by transaction category
        category = None
        if self._confirm("Filter by transaction category?"):
            category = self._ask_field("Category", lambda v: Transaction.clean_text(v, "Category"))

        # Filter by mode of payment
        mode_of_payment = None
        if self._confirm("Filter by mode of payment?"):
            print(f"Valid modes of payment: {', '.join(VALID_PAYMENT_METHODS)}")
            mode_of_payment = self._ask_field("Mode of payment", Transaction.clean_mode_of_payment)

        # Filter by time range, where leaving one side empty leaves that side open
        timestamp_range = None
        if self._confirm("Filter by time range?"):
            print("Enter dates in the format YYYY-MM-DD HH:MM.")
            start = self._ask_field("Earliest date and time", converter=self._to_datetime, optional=True)
            end = self._ask_field("Latest date and time", converter=self._to_datetime, optional=True)
            timestamp_range = (start, end)

        # Filter by amount range, where leaving one side empty leaves that side open
        amount_range = None
        if self._confirm("Filter by amount range?"):
            minimum = self._ask_field("Minimum amount", converter=self._to_float, optional=True)
            maximum = self._ask_field("Maximum amount", converter=self._to_float, optional=True)
            amount_range = (minimum, maximum)

        try:
            custom_filter = Filter(
                transaction_subclass,
                category,
                mode_of_payment,
                timestamp_range,
                amount_range
            )
        except ValueError as error:
            print(f"  Could not apply the filter: {error}")
            return

        results = self.transaction_history.filter_transactions(custom_filter)
        print("\nFilter used:")
        print(custom_filter)
        if not results:
            print("No transactions matched the filter.")
            return
        print("Filtered Transactions:")
        self._print_transactions(results)

    # [7] Export Transactions
    # A method to export the expenses and the income to JSON files, then print how many records were written
    def export_transactions(self):
        print("\n=-= Export Transactions =-=")
        try:
            expense_count, income_count = self.transaction_history.export_transaction_history()
        except DataFileError as error:
            print(f"  {error}")
            return
        if expense_count == 0 and income_count == 0:
            print("There are no transactions to export, so no file was created.")
            return
        if expense_count:
            print(f"Exported {expense_count} expense(s) to '{EXPORTED_EXPENSES_PATH}'.")
        if income_count:
            print(f"Exported {income_count} income record(s) to '{EXPORTED_INCOME_PATH}'.")

    # A method to ask whether the user means expense or income categories, and return the matching class or None
    def _ask_category_class(self):
        choice = input("Enter '1' for expense categories or '2' for income categories: ").strip()
        match choice:
            case "1":
                return Expense
            case "2":
                return Income
            case _:
                print("  Invalid choice. Please try again.")
                return None

    # [8] Add a Category
    def add_category(self):
        print("\n=-= Add a Category =-=")
        category_class = self._ask_category_class()
        if category_class is None:
            return
        name = input("Enter the new category: ")
        try:
            saved_name = category_class.add_valid_category(name)
        except ValueError as error:
            print(f"  Could not add the category: {error}")
        except DataFileError as error:
            print(f"  {error}\n  The category was not added.")
        else:
            print(f"Category '{saved_name}' was added and saved.")

    # [9] Delete a Category
    # A category that is still used by a transaction cannot be deleted, because those transactions would no longer load
    def delete_category(self):
        print("\n=-= Delete a Category =-=")
        category_class = self._ask_category_class()
        if category_class is None:
            return
        print(f"Current categories: {', '.join(category_class.valid_categories)}")
        name = input("Enter the category to delete: ")
        try:
            if self.transaction_history.category_in_use(category_class, name):
                print("  That category is used by existing transactions. Remove those transactions first.")
                return
            deleted_name = category_class.delete_valid_category(name)
        except ValueError as error:
            print(f"  Could not delete the category: {error}")
        except DataFileError as error:
            print(f"  {error}\n  The category was not deleted.")
        else:
            print(f"Category '{deleted_name}' was deleted and saved.")

    # A method to load the valid categories and the saved transactions when the program starts, and tell the user how many were loaded
    # If a file is not valid, the program continues and the files are blocked from being overwritten
    def _load_data(self):
        for category_class in (Expense, Income):
            try:
                category_class.load_valid_categories()
            except DataFileError as error:
                print(f"\nWARNING: {error}")
        try:
            count = self.transaction_history.load()
        except DataFileError as error:
            print(f"\nWARNING: {error}")
            print("The program will continue with no records, and nothing will be saved.")
            return
        if count == 0:
            print("\nNo saved transactions found. Starting with an empty history.")
        else:
            print(f"\nLoaded {count} transaction(s).")

    # A method to show the menu again and again until the user chooses Exit
    def run(self):
        self._load_data()
        # A dictionary that maps each menu choice to the method to run, so no long if/else chain is needed (10 is handled separately as Exit)
        actions = {
            "1": self.add_transaction,
            "2": self.remove_transaction,
            "3": self.show_transaction_history,
            "4": self.search_by_id,
            "5": self.search_by_name,
            "6": self.filter_transactions,
            "7": self.export_transactions,
            "8": self.add_category,
            "9": self.delete_category,
        }
        while True:
            self._show_menu()
            try:
                choice = input("Enter your choice (1-10): ").strip()
                if choice == "10":
                    print("Leaving the Income Expense Tracker Menu.")
                    break
                action = actions.get(choice)
                # None means the choice is not in the dictionary, so it is not valid
                if action is None:
                    if choice:
                        print(f"  '{choice}' is not a valid choice. Please enter a number from 1 to 10.")
                    else:
                        print("  You did not enter anything. Please enter a number from 1 to 10.")
                    continue
                action()
            except KeyboardInterrupt:
                # Ctrl+C cancels the current action and goes back to the menu
                print("\nOperation cancelled.")
            except EOFError:
                # The input has ended (for example Ctrl+D), so there is nothing more to read
                print("\nInput ended. Exiting.")
                break


def main():
    transaction_history = TransactionHistory()
    manager = IncomeExpenseTrackerManager(transaction_history)
    manager.run()

if __name__ == "__main__":
    main()