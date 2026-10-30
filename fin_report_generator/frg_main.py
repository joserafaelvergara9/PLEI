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
import financial_report
import pie_chart

expenses = []
incomes = []


for transaction in transac_his.transaction_history:
    if type(transaction) == transac.Expense():
        expenses.append(transaction)

    elif type(transaction) == transac.Income():
        incomes.append(transaction)







year = ""
month = ""
day = ""
hour = "" 
minute = "" 
second = ""


pie = pie_chart.PieChart("_category_of_payment", transac.transaction_history)


fin_report = financial_report.FinancialReport(datetime(year, month, day, hour, minute, second), expenses, incomes, pie)


"""

MAIN FUNCTION: create function that customizes financial report and generate one


"""