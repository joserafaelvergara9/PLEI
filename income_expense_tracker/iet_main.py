import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
import general_purpose_functions.custom_exceptions as cusexc
import general_purpose_functions.id_generator as id_generator
import os

from receipt import Receipt
from transaction import Expense, Income
from filter import Filter
from transaction_history import TransactionHistory
import json
from datetime import datetime

class IncomeExpenseTracker:
    def __init__(self):
        self.transaction_history = TransactionHistory([])

    def add_income(self, 
                   name, 
                   amount, 
                   mode_of_payment, 
                   category_of_income, 
                   receipt, 
                   comments, 
                   timestamp=None, 
                   income_id=None):
        
        income = Income(self, 
                        name,
                        amount,
                        mode_of_payment,
                        category_of_income,
                        receipt,
                        comments,
                        timestamp,
                        income_id
                        )
        self.transaction_history.add_transaction(income)

    def add_expense(self, 
                    name, 
                    amount, 
                    mode_of_payment, 
                    category_of_payment, 
                    quantity, 
                    receipt, 
                    comments, 
                    timestamp=None, 
                    expense_id=None):
        
        expense = Expense(self, 
                    name,
                    amount, 
                    mode_of_payment, 
                    category_of_payment, 
                    quantity, 
                    receipt, 
                    comments,
                    timestamp,
                    expense_id 
                    )
        self.transaction_history.add_transaction(expense)

    def filter_transactions(self, filter_criteria):
        filter_obj = Filter(filter_criteria)
        return filter_obj.apply(self.transaction_history.transactions)

def show_menu():
    print("Income and Expense Tracker")
    print("1. Add Income")
    print("2. Add Expense")
    print("3. Remove Income")
    print("4. Remove Expense")
    print("5. Show Transaction History")
    print("6. Search Transactions by ID")
    print("7. Filter Transactions")
    print("8. Export Transactions to CSV")
    print("9. Exit")

def show_filter_menu():
    print("Filter Transactions")
    print("1. Filter by Name")
    print("2. Filter by Amount")
    print("3. Filter by Mode of Payment")
    print("4. Filter by Category of Payment")
    print("5. Filter by Date")
    print("6. Back to Main Menu")

def main():
    tracker = IncomeExpenseTracker()


    # Load existing transactions from JSON files
    with open("iet_json_files/expenses.json", "r", encoding="utf-8") as file:
        temp_expense_history = json.load(file)
    with open("iet_json_files/income.json", "r", encoding="utf-8") as file:
        temp_income_history = json.load(file)
    for i in range(1, len(temp_expense_history)):
        tracker.transaction_history.add_transaction(Expense(**temp_expense_history[i]))
    for i in range(1, len(temp_income_history)):
        tracker.transaction_history.add_transaction(Income(**temp_income_history[i]))


    while True:
        show_menu()
        choice = input("Enter your choice: ")

        match choice:
            case "1":
                transaction_choice = input("Enter '1' to create an income transaction or '2' to create an expense transaction: ")
                match transaction_choice:

                    case "1":
                        #ADD NEW INCOME TRANSACTION
                        name = input("Enter income name: ")
                        amount = float(input("Enter income amount: "))
                        mode_of_payment = input("Enter income mode of payment: ")
                        category_of_income = input("Enter income category: ")
                        comments = input("Enter any comments: ")
                        tracker.add_income(name=name, amount=amount, mode_of_payment=mode_of_payment, category_of_income=category_of_income, comments=comments)

                    case "2":     #ADD NEW EXPENSE TRANSACTION
                        name = input("Enter expense name: ")
                        amount = float(input("Enter expense amount: "))
                        mode_of_payment = input("Enter expense mode of payment: ")
                        category_of_payment = input("Enter expense category: ")
                        quantity = int(input("Enter quantity: "))
                        comments = input("Enter any comments: ")
                        tracker.add_expense(name=name, amount=amount, mode_of_payment=mode_of_payment, category_of_payment=category_of_payment, quantity=quantity, comments=comments)

                    case _:
                        print("Invalid choice. Please try again.")


            case "2":     #REMOVE TRANSACTION
                transaction_id = input("Enter transaction ID to remove: ")
                transaction = tracker.transaction_history.search_transaction_by_id(transaction_id)
                tracker.remove_transaction(transaction)

            case "3":     #SHOW TRANSACTION HISTORY
                print(tracker.transaction_history.display_transaction_history())

            case "4":     #SEARCH TRANSACTION BY ID
                transaction_id = input("Enter transaction ID to search: ")
                print(tracker.transaction_history.search_transaction_by_id(transaction_id))

            case "5":     #SEARCH BY NAME
                name = input("Enter transaction name to search: ")
                print(tracker.transaction_history.search_transaction_by_name(name))

            case "6":     #FILTER TRANSACTIONS
                show_filter_menu()

                while True:
                    filter_choice = input("Would you like to enter a transaction subclass?: (y/n)")
                    match filter_choice:
                        case "y":
                            transaction_subclass = input("Enter a type of transaction ('income' or 'expense')")
                        case "n":
                            print("OK, transaction subclass will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")

                while True:
                    filter_choice = input("Would you like to enter a transaction category?: (y/n)")
                    match filter_choice:
                        case "y":
                            transaction_category = input("Enter a transaction category: ")
                        case "n":
                            print("OK, transaction category will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")

                while True:
                    filter_choice = input("Would you like to enter a mode of payment?: (y/n)")
                    match filter_choice:
                        case "y":
                            mode_of_payment = input("Enter a mode of payment: ")
                        case "n":
                            print("OK, mode of payment will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")

                while True:
                    filter_choice = input("Would you like to enter a time range?: (y/n)")
                    match filter_choice:
                        case "y":
                            year_min = int(input("Enter a minimum year: "))
                            month_min = int(input("Enter a minimum month: "))
                            day_min = int(input("Enter a minimum day: "))
                            hour_min = int(input("Enter a minimum hour: "))
                            minute_min = int(input("Enter a minimum minute: "))

                            year_max = int(input("Enter a maximum year: "))
                            month_max = int(input("Enter a maximum month: "))
                            day_max = int(input("Enter a maximum day: "))
                            hour_max = int(input("Enter a maximum hour: "))
                            minute_max = int(input("Enter a maximum minute: "))

                            timestamp_range_min = datetime(year_min, month_min, day_min, hour_min, minute_min)
                            timestamp_range_max = datetime(year_max, month_max, day_max, hour_max, minute_max)

                        case "n":
                            print("OK, mode of payment will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")


                while True:
                    filter_choice = input("Would you like to enter an amount range?: (y/n)")
                    match filter_choice:
                        case "y":
                            amount_min = float(input("Enter a minimum amount: "))
                            amount_max = float(input("Enter a maximum amount: "))
                        case "n":
                            print("OK, amount range will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")

                custom_filter = Filter(transaction_subclass, transaction_category, mode_of_payment, (timestamp_range_min, timestamp_range_max), (amount_min, amount_max))
                tracker.transaction_history.filter_transactions(custom_filter)

            case "7":     #EXPORT TRANSACTION HISTORY
                tracker.transaction_history.export_transaction_history()

            case "9":     #EXIT IET MENU
                print("Leaving the Income Expense Tracker Menu.")
                break

            case _:
                print("Invalid choice. Please try again.")



"""
from receipt import Receipt
from transaction import Expense, Income
from filter import Filter
from transaction_history import TransactionHistory


import sys
import json
import csv ## TO DO: Move the valid categories and methods to the CSV
import os
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
from abc import ABC, abstractmethod
from datetime import datetime
from income_expense_tracker.receipt import Receipt
from general_purpose_functions.id_generator import id_generator
import general_purpose_functions.custom_exceptions as cusexc
import income_expense_tracker.transaction_history as transac_his
import income_expense_tracker.transaction as transac

def main():
    while True:
        print("Transaction Manager Menu")
        print("Enter a command below: ")
        print("(1) ENTER A TRANSACTION: ")
        print("(2) DELETE A TRANSACTION: ")
        print("(3) ")
    

if __name__ == "__main__":
    main()
"""