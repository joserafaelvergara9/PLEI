import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
import general_purpose_functions.custom_exceptions as cusexc
import general_purpose_functions.id_generator as id_generator
import transaction

class TransactionHistory:
    def __init__(self, transactions):
        self.transactions = transactions

    def display_transaction_history(self):
        for transaction in self.transactions:
            print("**********************")
            print(transaction)
            print("**********************")

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def remove_transaction(self, transaction):
        self.transactions.remove(transaction)

    def export_transaction_history():
        pass

    def filter_transactions():
        pass

    def search_by_id():
        pass

    def search_by_name():
        pass


transaction_history = TransactionHistory([])

transaction1 = transaction.Income("october 13 allowance", 2500.00, "cash", "allowance", receipt = None, comments = "I have extra allowance!")

print(transaction1)

print("hi")