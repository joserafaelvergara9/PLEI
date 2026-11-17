import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
import general_purpose_functions.custom_exceptions as cusexc
import general_purpose_functions.id_generator as id_generator
import os
import transaction as tr
import filter as flt
import json


class TransactionHistory:
    def __init__(self, transactions: list):
        self.transactions = transactions
        self.test_expense_data = {
                    "expense_id": "EXP-0000",
                    "name": "Test Expense",
                    "amount": 189.92,
                    "quantity": 1,
                    "mode_of_payment": "Test Mode",
                    "category_of_payment": "Test Category",
                    "timestamp": "",
                    "receipt": "receipt",
                    "comments": ["comment 1","comment 2"]
                }
        self.test_income_data = {
                    "income_id": "INC-0000",
                    "name": "Test Income",
                    "amount": 189.92,
                    "mode_of_payment": "Test Mode",
                    "category_of_income": "Test Category",
                    "timestamp": "",
                    "receipt": "receipt",
                    "comments": ["comment 1", "comment 2"]
                }

    def display_transaction_history(self): #goes thru each transaction in the list and prints it out
        print("Transaction History:")
        for transaction in self.transactions:
            print("**********************")
            print(transaction)
            print("**********************")


    def add_transaction(self, transaction):     #puts the transaction into the list of transactions, and then updates its corresponding json file
        self.transactions.append(transaction)
        transaction.save_to_json(transaction.json_path)


    def remove_transaction(self, transaction_to_be_removed):  #removes the transaction from the list of transactions, and then updates its corresponding json file
        data = []
        temp_json_path = transaction_to_be_removed.json_path
        if(type(transaction_to_be_removed) == tr.Income):
            self.transactions.remove(transaction_to_be_removed)
            for transaction in self.transactions:

                if (isinstance(transaction, tr.Income)):
                    new_transaction_format = {
                            "income_id": transaction._income_id,
                            "name": transaction.name,
                            "amount": transaction.amount,
                            "mode_of_payment": transaction.mode_of_payment,
                            "category_of_income": transaction.category_of_income,
                            "timestamp": transaction.timestamp,
                            "receipt": transaction.receipt,
                            "comments": transaction.comments
                        }
                    data.append(new_transaction_format)
            os.makedirs(os.path.dirname("iet_json_files/exported_income_data.json"), exist_ok=True) # Check if target directory exists again (?)
            with open(temp_json_path, "w", encoding="utf-8") as file: # Write to json
                #json.dump([self.test_income_data] + data, file, default=str, indent=4)
                json.dump(data, file, default=str, indent=4)
            print("Transaction has been successfully removed!")

        elif(type(transaction_to_be_removed) == tr.Expense):
            self.transactions.remove(transaction_to_be_removed)
            for transaction in self.transactions:

                if (isinstance(transaction, tr.Expense)):
                    new_transaction_format = {
                            "expense_id": transaction._expense_id,
                            "name": transaction.name,
                            "amount": transaction.amount,
                            "mode_of_payment": transaction.mode_of_payment,
                            "category_of_payment": transaction.category_of_payment,
                            "quantity": transaction.quantity,
                            "timestamp": transaction.timestamp,
                            "receipt": transaction.receipt,
                            "comments": transaction.comments
                        }
                    data.append(new_transaction_format)
            os.makedirs(os.path.dirname("iet_json_files/exported_expense_data.json"), exist_ok=True) # Check if target directory exists again (?)
            with open(temp_json_path, "w", encoding="utf-8") as file: # Write to json
                #json.dump([self.test_expense_data] + data, file, default=str, indent=4)
                json.dump(data, file, default=str, indent=4)
            print("Transaction has been successfully removed!")

                
    def export_transaction_history(self):    #EXPORT TRANSACTION HISTORY
        data = []
        for transaction in self.transactions:

            if (isinstance(transaction, tr.Income)):            
                new_transaction_format = {
                        "income_id": transaction._income_id,
                        "name": transaction.name,
                        "amount": transaction.amount,
                        "mode_of_payment": transaction.mode_of_payment,
                        "category_of_income": transaction.category_of_income,
                        "timestamp": transaction.timestamp,
                        "receipt": transaction.receipt,
                        "comments": transaction.comments
                    }
                data.append(new_transaction_format)
        os.makedirs(os.path.dirname("iet_json_files/exported_income_data.json"), exist_ok=True) # Check if target directory exists again (?)
        with open("iet_json_files/exported_income_data.json", "w", encoding="utf-8") as file: # Write to json
            #json.dump([self.test_income_data] + data, file, default=str, indent=4)
            json.dump(data, file, default=str, indent=4)


        for transaction in self.transactions:
            if (isinstance(transaction, tr.Expense)):
                new_transaction_format = {
                        "expense_id": transaction._expense_id,
                        "name": transaction.name,
                        "amount": transaction.amount,
                        "mode_of_payment": transaction.mode_of_payment,
                        "category_of_payment": transaction.category_of_payment,
                        "quantity": transaction.quantity,
                        "timestamp": transaction.timestamp,
                        "receipt": transaction.receipt,
                        "comments": transaction.comments
                    }
                data.append(new_transaction_format)
        os.makedirs(os.path.dirname("iet_json_files/exported_expense_data.json"), exist_ok=True) # Check if target directory exists again (?)
        with open("iet_json_files/exported_expense_data.json", "w", encoding="utf-8") as file: # Write to json
            #json.dump([self.test_expense_data] + data, file, default=str, indent=4)
            json.dump(data, file, default=str, indent=4)


    def filter_transactions(self, filter: flt.Filter):  #DISPLAY TRANSACTIONS BASED ON FILTER
        filtered_transactions = []
        for transaction in self.transactions:
            if filter.matches(transaction):
                filtered_transactions.append(transaction)

        print("Filtered Transactions:")
        for transaction in filtered_transactions:
            print("**********************")
            print(transaction)
            print("**********************")
        

    def search_by_id(self, transaction_id):    #SEARCH TRANSACTION BY ID
        search_results = []
        for transaction in self.transactions:
            if isinstance(transaction, tr.Income):
                
                print("This is an income!")
                print(transaction)
                if transaction._income_id.lower().strip() == transaction_id.lower().strip():
                    search_results.append(transaction)
            elif isinstance(transaction, tr.Expense):
                if transaction._expense_id.lower().strip() == transaction_id.lower().strip():
                    search_results.append(transaction)

        if len(search_results) > 0:
            print("Search Results: ")
            for result in search_results:
                return result

        else:
            print("Searched ID cannot be found.")
            return None
        

    def search_by_name(self, name):      #SEARCH TRANSACTION BY NAME
        search_results = []
        for transaction in self.transactions:
            if transaction.name.lower().strip() == name.lower().strip():
                search_results.append(transaction)

            elif name.lower().strip() in transaction.name.lower().strip():
                search_results.append(transaction)  

        if len(search_results) > 0:
            print("Search Results: ")
            for result in search_results:
                return result
        else:
            print("Searched name cannot be found.")
            return None