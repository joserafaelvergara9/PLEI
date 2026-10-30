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