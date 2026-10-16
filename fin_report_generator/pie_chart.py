import sys
import json
import os

from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path

from typing import List, Dict, Optional, Tuple
import matplotlib.pyplot as pyplot

import general_purpose_functions.custom_exceptions as cusexc
from general_purpose_functions.id_generator import id_generator
from income_expense_tracker.transaction import Transaction, Expense, Income 

class PieChart:
    def __init__(
            self,
            attribute: str,
            transactions: List[Transaction]
    ):
        self._attribute = attribute
        self._transactions = transactions
        self._percentages: Dict[str, float] = {}
        self.calculate_percentages()

    @property
    def attribute(self) -> str:
        return self._attribute

    @property
    def percentages(self) -> Dict[str, float]:
        return self._percentages

    def calculate_percentages(self) -> Dict[str, float]:
        totals = {}
        total_sum = 0.0

        for transaction in self._transactions:
            attribute_value = getattr(transaction, self._attribute, None)
            if attribute_value is not None:
                amount = transaction.amount * getattr(transaction, 'quantity', 1)
                totals[attribute_value] = totals.get(attribute_value, 0.0) + amount
                total_sum += amount
        if total_sum > 0:
            self._percentages = {key: (value / total_sum) * 100 for key, value in totals.items()}
        else:
            self._percentages = {}
        return self._percentages

    def generate_pie_chart(self, title: Optional[str] = None, colors: Optional[List[str]] = None) -> pyplot.Figure:
        if not self._percentages:
            self.calculate_percentages()

        fig, ax = pyplot.subplots(figsize=(5, 5))
        labels = [str(label).upper() for label in self._percentages.keys()]
        sizes = list(self._percentages.values())

        if not sizes:
            ax.text(0.5, 0.5, "No Data Available", horizontalalignment='center', verticalalignment='center')
        else:
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
            ax.axis('equal')

        chart_title = title if title else f"Distribution by {self._attribute.replace('_', ' ').title()}"
        ax.set_title(chart_title)
        return fig

    def display_pie_chart(self) -> None:
        fig = self.generate_pie_chart()
        pyplot.show()

    def export_pie_chart(self, filename: str) -> None:
        fig = self.generate_pie_chart()
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        fig.savefig(filename, bbox_inches='tight')
        pyplot.close(fig) 

def pie_chart_test():
    oct_expenses = [
        Expense(name="Supermarket", amount=450.0, mode_of_payment="cash", category_of_payment="groceries", quantity=1),
        Expense(name="AngryBee", amount=150.0, mode_of_payment="credit", category_of_payment="food", quantity=1),
        Expense(name="Electric Bill", amount=450.0, mode_of_payment="debit", category_of_payment="utilities", quantity=1),
        Expense(name="Supermarket 2", amount=550.0, mode_of_payment="cash", category_of_payment="groceries", quantity=1),
        Expense(name="McDo", amount=500.0, mode_of_payment="credit", category_of_payment="food", quantity=1),
        Expense(name="Paying Mr. Soprano", amount=800.0, mode_of_payment="cash", category_of_payment="debt", quantity=1)
    ]

    chart = PieChart(attribute="_category_of_payment", transactions=oct_expenses)
    custom_colors = ["#ad2c2c", "#006ad4", "#ffda1f", "#32a438"]
    fig = chart.generate_pie_chart(colors=custom_colors)
    pyplot.show()

pie_chart_test()