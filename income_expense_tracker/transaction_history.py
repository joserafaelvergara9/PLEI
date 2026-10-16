import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
import general_purpose_functions.custom_exceptions as cusexc
import general_purpose_functions.id_generator as id_generator


import transaction as tr
import filter as flt

class TransactionHistory:
    def __init__(self, transactions):
        self.transactions = transactions

    def display_transaction_history(self):
        print("Transaction History:")
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

    def filter_transactions(self, filter: flt.Filter):
        filtered_transactions = []
        for transaction in self.transactions:
            if filter.matches(transaction):
                filtered_transactions.append(transaction)

        print("Filtered Transactions:")
        for transaction in filtered_transactions:
            print("**********************")
            print(transaction)
            print("**********************")
        

    def search_by_id(self, transaction_id):

        search_results = []
        for transaction in self.transactions:
            if isinstance(transaction, tr.Income) and transaction.income_id.lower().strip() == transaction_id.lower().strip():
                search_results.append(transaction)
            elif isinstance(transaction, tr.Expense) and transaction.expense_id.lower().strip() == transaction_id.lower().strip():
                search_results.append(transaction)

        if len(search_results) > 0:
            print("Search Results: ")
            for result in search_results:
                print(result)

        else:
            print("Searched ID cannot be found.")
            return None
        

    def search_by_name(self, name):
        search_results = []
        for transaction in self.transactions:
            if transaction.name.lower().strip() == name.lower().strip():
                search_results.append(transaction)

            elif name.lower().strip() in transaction.name.lower().strip():
                search_results.append(transaction)  

        if len(search_results) > 0:
            print("Search Results: ")
            for result in search_results:
                print(result)
        else:
            print("Searched name cannot be found.")
        



transaction_history = TransactionHistory([])

transaction1 = tr.Income("october 13 allowance", 2500.00, "cash", "allowance", receipt = None, comments = "I have extra allowance!")
transaction2 = tr.Expense("mom's groceries", 1500.00, "credit", "groceries", receipt = None, comments = "I bought groceries for the week.")
transaction3 = tr.Expense("uber ride", 500.00, "cash", "transportation", receipt = None, comments = "I took an uber ride to school.")
transaction4 = tr.Income("october 20 allowance", 2500.00, "cash", "allowance", receipt = None, comments = "I have extra allowance!")
transaction5 = tr.Expense("lunch", 300.00, "cash", "food", receipt = None, comments = "I bought lunch at school.")
transaction6 = tr.Expense("movie ticket", 400.00, "credit", "personal", receipt = None, comments = "I watched a movie with friends.")
transaction7 = tr.Income("october 27 allowance", 2500.00, "cash", "allowance", receipt = None, comments = "I have extra allowance!")
transaction8 = tr.Expense("bus fare", 100.00, "cash", "transportation", receipt = None, comments = "I took the bus to school.")
transaction9 = tr.Expense("gym membership", 2000.00, "credit", "personal", receipt = None, comments = "I paid for my gym membership.")
transaction10 = tr.Income("october 31 allowance", 2500.00, "cash", "allowance", receipt = None, comments = "I have extra allowance!")


#print(transaction1)
#print()
#print(transaction2)

transaction_history.add_transaction(transaction1)
transaction_history.add_transaction(transaction2)
transaction_history.add_transaction(transaction3)
transaction_history.add_transaction(transaction4)
transaction_history.add_transaction(transaction5)
transaction_history.add_transaction(transaction6)
transaction_history.add_transaction(transaction7)
transaction_history.add_transaction(transaction8)
transaction_history.add_transaction(transaction9)
transaction_history.add_transaction(transaction10)
#transaction_history.display_transaction_history()
#transaction_history.search_by_id("exp-0000")
#transaction_history.search_by_name("mom's groceries")

filter1 = flt.Filter(transaction_subclass=tr.Expense, category=None, mode_of_payment="cash", timestamp_range=None, amount_range=None)


transaction_history.filter_transactions(filter1)


#print("hi")