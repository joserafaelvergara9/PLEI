import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
import general_purpose_functions.custom_exceptions as cusexc
from general_purpose_functions.id_generator import id_generator
from income_expense_tracker.transaction import Expense, Income 
from fin_report_generator.pie_chart import PieChart

class FinancialReport:
    pass