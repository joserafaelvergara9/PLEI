import sys
import os
import math
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from general_purpose_functions.id_generator import id_generator
from fin_report_generator.pie_chart import PieChart, DataFileError, read_json_list, write_json_file

# The folder where this file is located, so the data files are always found next to it no matter where the program is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_JSON_PATH = os.path.join(BASE_DIR, "frg_json_files", "financial_reports.json")

# Any transaction-shaped object (an Expense or Income from IET, or a record read from IET's JSON files)
# The FRG never imports the IET classes, so it only relies on this shape
TransactionLike = Any


class FinancialReport:
    def __init__(
        self,
        range_of_time: Tuple[datetime, datetime],
        expenses: Optional[List[TransactionLike]] = None,
        income: Optional[List[TransactionLike]] = None,
        pie_charts: Optional[List[PieChart]] = None,
        expenses_description: str = "",
        income_description: str = ""
    ):
        self._report_id = id_generator("financialReport")
        self._range_of_time = self._clean_range(range_of_time)
        start_time, end_time = self._range_of_time
        # Only the transactions inside the range of time are kept
        self._expenses = [
            e for e in self._clean_transactions(expenses, "Expenses", "category_of_payment")
            if start_time <= e.timestamp <= end_time
        ]
        self._income = [
            i for i in self._clean_transactions(income, "Income", "category_of_income")
            if start_time <= i.timestamp <= end_time
        ]
        if pie_charts is not None:
            self._pie_charts = self._clean_pie_charts(pie_charts)
        else:
            self._pie_charts = []
            if self._expenses:
                self._pie_charts.append(PieChart(attribute="category_of_payment", transactions=self._expenses))
                self._pie_charts.append(PieChart(attribute="mode_of_payment", transactions=self._expenses))
            # Income gets its own chart by category, since it is charted separately from the expenses
            if self._income:
                self._pie_charts.append(PieChart(attribute="category_of_income", transactions=self._income))
        self._expenses_description = self.clean_description(expenses_description)
        self._income_description = self.clean_description(income_description)

        self._total_expenses = self.calculate_total_expenses()
        self._total_income = self.calculate_total_income()
        self._gain_or_loss = self.calculate_gain_loss()
        self._json_path = REPORTS_JSON_PATH

    # A static method to return the range as a (start, end) tuple, or raises Value Error if it is not two datetimes with the start not after the end
    @staticmethod
    def _clean_range(value):
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise ValueError("Range of time must be a (start, end) pair.")
        start_time, end_time = value
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            raise ValueError("Both the start and the end of the range of time must be datetimes.")
        if start_time > end_time:
            raise ValueError("The start of the range of time cannot be after its end.")
        return (start_time, end_time)

    # A static method to check that one transaction has what a report needs, or raises Value Error saying what is wrong
    @staticmethod
    def _check_transaction(item, category_attribute):
        if not callable(getattr(item, "convert_to_dict", None)):
            raise ValueError("it has no convert_to_dict() method")
        if not isinstance(getattr(item, "timestamp", None), datetime):
            raise ValueError("its timestamp is not a datetime")
        amount = getattr(item, "amount", None)
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
            raise ValueError("its amount is not a number greater than 0")
        quantity = getattr(item, "quantity", 1)
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError("its quantity is not a whole number of at least 1")
        category = getattr(item, category_attribute, None)
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"it has no {category_attribute}")

    # A static method to return a list of the transactions (None becomes an empty list), or raises Value Error if it is not a list or a transaction is not valid
    # The category attribute also makes sure that an income is not passed in as an expense, or the other way around
    @classmethod
    def _clean_transactions(cls, items, label, category_attribute):
        if items is None:
            return []
        if not isinstance(items, (list, tuple)):
            raise ValueError(f"{label} must be a list.")
        for number, item in enumerate(items, start=1):
            try:
                cls._check_transaction(item, category_attribute)
            except ValueError as error:
                raise ValueError(f"{label} item {number} is invalid: {error}.") from error
        return list(items)

    # A static method to return a list of the pie charts, or raises Value Error if it is not a list of PieChart objects
    @staticmethod
    def _clean_pie_charts(value):
        if not isinstance(value, (list, tuple)) or not all(isinstance(chart, PieChart) for chart in value):
            raise ValueError("Pie charts must be a list of PieChart objects.")
        return list(value)

    # A static method to return a stripped description, where an empty description is allowed, or raises Value Error if it is not a string
    @staticmethod
    def clean_description(value):
        if not isinstance(value, str):
            raise ValueError("Description must be in String (text) format.")
        return value.strip()

    @property
    def json_path(self) -> str:
        return self._json_path

    @property
    def report_id(self) -> str:
        return self._report_id

    @property
    def range_of_time(self) -> Tuple[datetime, datetime]:
        return self._range_of_time

    @property
    def expenses(self) -> List[TransactionLike]:
        return self._expenses

    @property
    def income(self) -> List[TransactionLike]:
        return self._income

    @property
    def pie_charts(self) -> List[PieChart]:
        return self._pie_charts

    @property
    def total_expenses(self) -> float:
        self._total_expenses = self.calculate_total_expenses()
        return self._total_expenses

    @property
    def total_income(self) -> float:
        self._total_income = self.calculate_total_income()
        return self._total_income

    @property
    def gain_or_loss(self) -> str:
        self._gain_or_loss = self.calculate_gain_loss()
        return self._gain_or_loss

    @property
    def expenses_description(self) -> str:
        return self._expenses_description

    @property
    def income_description(self) -> str:
        return self._income_description

    @expenses_description.setter
    def expenses_description(self, description: str) -> None:
        self._expenses_description = self.clean_description(description)

    @income_description.setter
    def income_description(self, description: str) -> None:
        self._income_description = self.clean_description(description)

    def calculate_total_expenses(self) -> float:
        total = 0.0
        for expense in self._expenses:
            quantity = getattr(expense, 'quantity', 1)
            total += expense.amount * quantity
        # Rounded to centavos so that tiny floating point errors do not show up
        self._total_expenses = round(total, 2)
        return self._total_expenses

    def calculate_total_income(self) -> float:
        total = 0.0
        for income in self._income:
            total += income.amount
        self._total_income = round(total, 2)
        return self._total_income

    # A method to return "gain", "loss" or "neutral" by comparing the totals (rounded to centavos, so 0.1 + 0.2 against 0.3 is neutral)
    def calculate_gain_loss(self) -> str:
        difference = round(self.calculate_total_income() - self.calculate_total_expenses(), 2)
        if difference > 0:
            self._gain_or_loss = "gain"
        elif difference < 0:
            self._gain_or_loss = "loss"
        else:
            self._gain_or_loss = "neutral"
        return self._gain_or_loss

    # A method to add a pie chart, or raises Value Error if it is not a PieChart (a chart that is already in the report is ignored)
    def add_pie_chart(self, pie_chart: PieChart) -> None:
        if not isinstance(pie_chart, PieChart):
            raise ValueError("Only a PieChart object can be added.")
        if pie_chart not in self._pie_charts:
            self._pie_charts.append(pie_chart)

    # A method to remove a pie chart, or raises Value Error if it is not in the report
    def remove_pie_chart(self, pie_chart: PieChart) -> None:
        if pie_chart not in self._pie_charts:
            raise ValueError("That pie chart is not in this report.")
        self._pie_charts.remove(pie_chart)

    def generate_report(self) -> Dict:
        report_data = {
            "report_id": self._report_id,
            "range_of_time": [self._range_of_time[0].isoformat(), self._range_of_time[1].isoformat()],
            "total_income": self.total_income,
            "total_expenses": self.total_expenses,
            "gain_or_loss": self.gain_or_loss,
            "income_description": self._income_description,
            "expenses_description": self._expenses_description,
            "income_transactions": [income.convert_to_dict() for income in self._income],
            "expense_transactions": [expense.convert_to_dict() for expense in self._expenses],
            "pie_charts": [chart.convert_to_dict() for chart in self._pie_charts]
        }
        return report_data

    def convert_to_dict(self) -> Dict:
        return self.generate_report()

    # A method to add the report to the history JSON file, or raises DataFileError if the file is not valid or cannot be written
    # A report that was saved before (same report ID) is replaced, so saving it twice does not make a duplicate
    def save_to_json(self, filepath: Optional[str] = None) -> None:
        path = self._json_path if filepath is None else filepath
        data = read_json_list(path)
        data = [
            saved for saved in data
            if not (isinstance(saved, dict) and saved.get("report_id") == self._report_id)
        ]
        data.append(self.convert_to_dict())
        write_json_file(path, data)

    # A method to write the report to its own JSON file, or raises Value Error if the filename is empty or DataFileError if it cannot be written
    def export_report(self, filename: str) -> None:
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Filename must be a non-empty text.")
        write_json_file(filename, self.generate_report())

    def __str__(self) -> str:
        return (
            f"Financial Report ID: {self._report_id}\n"
            f"Time Range:          {self._range_of_time[0]} to {self._range_of_time[1]}\n"
            f"Total Income:        P{self.total_income:,.2f}\n"
            f"Total Expenses:      P{self.total_expenses:,.2f}\n"
            f"Gain or Loss:        {self.gain_or_loss}\n"
            f"Income Desc.:        {self._income_description}\n"
            f"Expense Desc.:       {self._expenses_description}\n"
            f"Pie Charts Count:    {len(self._pie_charts)}"
        )