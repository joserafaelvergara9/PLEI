import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
import general_purpose_functions.custom_exceptions as cusexc
import general_purpose_functions.id_generator as id_generator
import os

from receipt import Receipt
from transaction import Expense, Income, VALID_PAYMENT_METHODS
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
                   receipt=None, 
                   comments=None, 
                   income_id=None,
                   timestamp=None
                   ):
        
        income = Income(name,
                        amount,
                        mode_of_payment,
                        category_of_income,
                        receipt,
                        comments
                        )
        self.transaction_history.add_transaction(income)

    def add_expense(self, 
                    name, 
                    amount, 
                    mode_of_payment, 
                    category_of_payment, 
                    quantity, 
                    receipt=None, 
                    comments=None
                    ):
        
        expense = Expense(name,
                          amount, 
                          mode_of_payment, 
                          category_of_payment, 
                          quantity, 
                          receipt, 
                          comments
                          )
        self.transaction_history.add_transaction(expense)

    def filter_transactions(self, filter_criteria):
        filter_obj = Filter(filter_criteria)
        return filter_obj.apply(self.transaction_history.transactions)

def show_menu():
    print("Income and Expense Tracker")
    print("1. Add Transaction")
    print("2. Remove Transaction")
    print("3. Show Transaction History")
    print("4. Search Transactions by ID")
    print("5. Search Transactions by Name")
    print("6. Filter Transactions")
    print("7. Export Transactions")
    print("8. Add an Expense Category")
    print("9. Delete an Expense Category")
    print("10. Exit")

def show_filter_menu():
    print("Filter Transactions")
    print("1. Filter by Transaction Subclass")
    print("2. Filter by Transaction Category")
    print("3. Filter by Mode of Payment")
    print("4. Filter by Time Range")
    print("5. Filter by Amount Range")

def main():
    tracker = IncomeExpenseTracker()


    # Load existing transactions from JSON files
    with open("iet_json_files/expenses.json", "r", encoding="utf-8") as file:
        temp_expense_history = json.load(file)
    with open("iet_json_files/income.json", "r", encoding="utf-8") as file:
        temp_income_history = json.load(file)
    for i in range(0, len(temp_expense_history)):
        tracker.transaction_history.transactions.append(Expense(**temp_expense_history[i]))
    for i in range(0, len(temp_income_history)):
        tracker.transaction_history.transactions.append(Income(**temp_income_history[i]))


    while True:
        show_menu()
        choice = input("Enter your choice: ")

        match choice:
            case "1":
                transaction_choice = input("Enter '1' to create an income transaction or '2' to create an expense transaction: ")
                
                match transaction_choice:
                    case "1":   #ADD TRANSACTION

                        #ADD NEW INCOME TRANSACTION
                        name = input("Enter income name: ")
                        amount = float(input("Enter income amount: "))
                        print(VALID_PAYMENT_METHODS)
                        mode_of_payment = input("Enter income mode of payment: ")
                        print(Income.valid_categories)
                        category_of_income = input("Enter income category: ")
                        comments = input("Enter any comments: ")
                        tracker.add_income(name=name, amount=amount, mode_of_payment=mode_of_payment, category_of_income=category_of_income, comments=comments)
                        print("Expense Transaction was successfully created!")

                    case "2":     #ADD NEW EXPENSE TRANSACTION
                        name = input("Enter expense name: ")
                        amount = float(input("Enter expense amount: "))
                        print(VALID_PAYMENT_METHODS)
                        mode_of_payment = input("Enter expense mode of payment: ")
                        print(Expense.valid_categories)
                        category_of_payment = input("Enter expense category: ")
                        quantity = int(input("Enter quantity: "))
                        comments = input("Enter any comments: ")
                        tracker.add_expense(name=name, amount=amount, mode_of_payment=mode_of_payment, category_of_payment=category_of_payment, quantity=quantity, comments=comments)
                        print("Expense Transaction was successfully created!")

                    case _:
                        print("Invalid choice. Please try again.")


            case "2":     #REMOVE TRANSACTION
                transaction_id = input("Enter transaction ID to remove: ")
                transaction = tracker.transaction_history.search_by_id(transaction_id)
                if transaction != None:
                    tracker.transaction_history.remove_transaction(transaction)

            case "3":     #SHOW TRANSACTION HISTORY
                print(tracker.transaction_history.display_transaction_history())

            case "4":     #SEARCH TRANSACTION BY ID
                transaction_id = input("Enter transaction ID to search: ")
                print(tracker.transaction_history.search_by_id(transaction_id))

            case "5":     #SEARCH BY NAME
                name = input("Enter transaction name to search: ")
                print(tracker.transaction_history.search_by_name(name))

            case "6":     #DISPLAY TRANSACTIONS USING A FILTER
                show_filter_menu()

                while True:      #FILTER BY TRANSACTION SUBCLASS
                    filter_choice = input("Would you like to enter a transaction subclass? (y/n): ")
                    match filter_choice:
                        case "y":
                            transaction_subclass = input("Enter a type of transaction ('income' or 'expense')")
                            break
                        case "n":
                            transaction_subclass = None
                            print("OK, transaction subclass will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")

                while True:     #FILTER BY TRANSACTION CATEGORY
                    filter_choice = input("Would you like to enter a transaction category? (y/n): ")
                    match filter_choice:
                        case "y":
                            transaction_category = input("Enter a transaction category: ")
                            break
                        case "n":
                            transaction_category = None
                            print("OK, transaction category will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")

                while True:      #FILTER BY MODE OF PAYMENT
                    filter_choice = input("Would you like to enter a mode of payment? (y/n): ")
                    match filter_choice:
                        case "y":
                            mode_of_payment = input("Enter a mode of payment: ")
                            break
                        case "n":
                            mode_of_payment = None
                            print("OK, mode of payment will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")

                while True:     #FILTER BY TIME RANGE
                    filter_choice = input("Would you like to enter a time range? (y/n): ")
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
                            timestamp_range = (timestamp_range_min, timestamp_range_max)
                            break

                        case "n":
                            timestamp_range = None
                            print("OK, mode of payment will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")


                while True:        #FILTER BY AMOUNT RANGE
                    filter_choice = input("Would you like to enter an amount range? (y/n): ")
                    match filter_choice:
                        case "y":
                            amount_min = float(input("Enter a minimum amount: "))
                            amount_max = float(input("Enter a maximum amount: "))
                            amount_range = (amount_min, amount_max)
                            break
                        case "n":
                            amount_range = None
                            print("OK, amount range will not be applied in the filter.")
                            break
                        case _:
                            print("Invalid choice!")

                custom_filter = Filter(transaction_subclass, 
                                       transaction_category, 
                                       mode_of_payment, 
                                       timestamp_range, 
                                       amount_range)
                tracker.transaction_history.filter_transactions(custom_filter)

            case "7":     #EXPORT TRANSACTION HISTORY
                tracker.transaction_history.export_transaction_history()

            case "8":     #ADD VALID CATEGORY
                valid_category = input("Enter a valid expense category: ")
                Expense.add_valid_category(valid_category)

            case "9":     #DELETE VALID CATEGORY
                valid_category = input("Enter a valid expense category: ")
                Expense.add_valid_category(valid_category)

            case "10":     #EXIT IET MENU
                print("Leaving the Income Expense Tracker Menu.")
                break

            case _:
                print("Invalid choice. Please try again.")


main()