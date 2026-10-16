import sys
import os
import json
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
import general_purpose_functions.custom_exceptions as cusexc

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from general_purpose_functions.id_generator import id_generator
from income_expense_tracker.transaction import Expense, Income 
from fin_report_generator.pie_chart import PieChart

class FinancialReport:
    def __init__(
        self,
        range_of_time: Tuple[datetime, datetime],
        expenses: Optional[List[Expense]] = None,
        income: Optional[List[Income]] = None,
        pie_charts: Optional[List[PieChart]] = None,
        expenses_description: str = "",
        income_description: str = ""
    ):
        self._report_id = id_generator("financialReport")
        self._range_of_time = range_of_time
        start_time, end_time = range_of_time
        self._expenses = [
            e for e in (expenses if expenses is not None else [])
            if start_time <= e.timestamp <= end_time
        ]
        self._income = [
            i for i in (income if income is not None else [])
            if start_time <= i.timestamp <= end_time
        ]
        if pie_charts is not None:
            self._pie_charts = pie_charts
        else:
            self._pie_charts = []
            if self._expenses:
                self._pie_charts.append(PieChart(attribute="category_of_payment", transactions=self._expenses))
                self._pie_charts.append(PieChart(attribute="mode_of_payment", transactions=self._expenses))
        self._expenses_description = expenses_description
        self._income_description = income_description

        self._total_expenses = self.calculate_total_expenses()
        self._total_income = self.calculate_total_income()
        self._gain_or_loss = self.calculate_gain_loss()
        self._json_path = "fin_report_generator/frg_json_files/financial_reports.json"

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
    def expenses(self) -> List[Expense]:
        return self._expenses

    @property
    def income(self) -> List[Income]:
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
    def gain_or_loss(self) -> float:
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
        self._expenses_description = description

    @income_description.setter
    def income_description(self, description: str) -> None:
        self._income_description = description

    def calculate_total_expenses(self) -> float:
        total = 0.0
        for expense in self._expenses:
            quantity = getattr(expense, 'quantity', 1)
            total += expense.amount * quantity
        self._total_expenses = total
        return total

    def calculate_total_income(self) -> float:
        total = 0.0
        for income in self._income:
            total += income.amount
        self._total_income = total
        return total

    def calculate_gain_loss(self) -> str:
        if self.total_income - self.total_expenses > 0:
            self._gain_or_loss = "gain"
        elif self.total_income - self.total_expenses < 0:
            self._gain_or_loss = "loss"
        elif self.total_income - self.total_expenses == 0:
            self._gain_or_loss = "neutral"
        return self._gain_or_loss

    def add_pie_chart(self, pie_chart: PieChart) -> None:
        if pie_chart not in self._pie_charts:
            self._pie_charts.append(pie_chart)

    def remove_pie_chart(self, pie_chart: PieChart) -> None:
        if pie_chart in self._pie_charts:
            self._pie_charts.remove(pie_chart)

    def generate_report(self) -> Dict:
        report_data = {
            "report_id": self._report_id,
            "range_of_time": [str(self._range_of_time[0]), str(self._range_of_time[1])],
            "total_income": self.total_income,
            "total_expenses": self.total_expenses,
            "gain_or_loss": self.gain_or_loss,
            "income_description": self._income_description,
            "expenses_description": self._expenses_description,
            "income_transactions": [income.convert_to_dict() if hasattr(income, 'convert_to_dict') else str(income) for income in self._income],
            "expense_transactions": [expense.convert_to_dict() if hasattr(expense, 'convert_to_dict') else str(expense) for expense in self._expenses],
            "pie_charts": [chart.convert_to_dict() if hasattr(chart, 'convert_to_dict') else chart.percentages for chart in self._pie_charts]
        }
        return report_data

    def convert_to_dict(self) -> Dict:
        return self.generate_report()

    def save_to_json(self, filepath: str = json_path) -> None:
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                data = []
        else:
            data = []
        data.append(self.convert_to_dict())
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, default=str)

    def export_report(self, filename: str) -> None:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        report_data = self.generate_report()
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(report_data, file, indent=4, default=str)

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
