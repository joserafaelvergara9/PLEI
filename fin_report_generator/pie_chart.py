import sys
import os
import json
import math
import tempfile
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path

from typing import Any, Dict, List, Optional
import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure

from general_purpose_functions.id_generator import id_generator

# The folder where this file is located, so the data files are always found next to it no matter where the program is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PIE_CHARTS_JSON_PATH = os.path.join(BASE_DIR, "frg_json_files", "pie_charts.json")

# Any transaction-shaped object, which needs an amount (and optionally a quantity) and the attribute that is charted
# The FRG never imports the IET classes, so it only relies on this shape
TransactionLike = Any
# The attributes of a transaction that a pie chart can group by
VALID_ATTRIBUTES = ("category_of_payment", "category_of_income", "mode_of_payment")


# A custom error to raise when a JSON file or a chart image cannot be read or understood or written
# It lives here (the lowest-level module) so that financial_report.py and frg_main.py can import it without a circular import
class DataFileError(Exception):
    pass


# A function to read a JSON file that holds a list, and return that list
# A missing file is not an error and just means an empty list, but a file that is unreadable or not a list raises DataFileError so it is never silently overwritten
def read_json_list(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise DataFileError(f"The file '{path}' is not a valid JSON text") from error
    except OSError as error:
        raise DataFileError(f"The file '{path}' could not be opened ({error.strerror})") from error
    if not isinstance(data, list):
        raise DataFileError(f"The file '{path}' does not contain a list")
    return data


# A function to write data to a JSON file, or raises DataFileError if it cannot be written
# It writes to a temporary file in the same folder first, then replaces the real file, so a failed save cannot damage it
def write_json_file(path, data):
    folder = os.path.dirname(os.path.abspath(path))
    temp_path = None
    try:
        os.makedirs(folder, exist_ok=True)
        file_descriptor, temp_path = tempfile.mkstemp(dir=folder, prefix="frg_", suffix=".tmp")
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=4, ensure_ascii=False, default=str)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # Ask the OS to really write it to disk
        os.replace(temp_path, path)
    except (OSError, TypeError, ValueError) as error:
        # Remove the temporary file if it was created, then raise DataFileError
        if temp_path is not None and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        reason = getattr(error, "strerror", None) or str(error)
        raise DataFileError(f"Could not save to '{path}' ({reason}).") from error


class PieChart:
    def __init__(
            self,
            attribute: str,
            transactions: List[TransactionLike]
    ):
        self._chart_id = id_generator("pieChart")
        self._attribute = self.clean_attribute(attribute)
        self._transactions = self.clean_transactions(transactions)
        self._percentages: Dict[str, float] = {}
        self.calculate_percentages()
        self._json_path = PIE_CHARTS_JSON_PATH

    # A static method to return the attribute stripped, or raises Value Error if it is not one of the attributes a chart can group by
    @staticmethod
    def clean_attribute(value):
        if not isinstance(value, str):
            raise ValueError("Attribute must be in String (text) format.")
        value = value.strip()
        if value not in VALID_ATTRIBUTES:
            raise ValueError(f"Attribute must be one of: {', '.join(VALID_ATTRIBUTES)}.")
        return value

    # A static method to return a copy of the list of transactions, or raises Value Error if it is not a list or a transaction has an invalid amount or quantity
    @staticmethod
    def clean_transactions(transactions):
        if not isinstance(transactions, (list, tuple)):
            raise ValueError("Transactions must be a list.")
        for number, transaction in enumerate(transactions, start=1):
            amount = getattr(transaction, "amount", None)
            if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
                raise ValueError(f"Transaction {number} does not have an amount greater than 0.")
            quantity = getattr(transaction, "quantity", 1)
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
                raise ValueError(f"Transaction {number} does not have a whole number quantity of at least 1.")
        return list(transactions)

    @property
    def chart_id(self) -> str:
        return self._chart_id

    @property
    def json_path(self) -> str:
        return self._json_path

    @property
    def attribute(self) -> str:
        return self._attribute

    @property
    def percentages(self) -> Dict[str, float]:
        return self._percentages

    # A method to work out the percentage of the total that each value of the attribute makes up, and return them
    def calculate_percentages(self) -> Dict[str, float]:
        totals = {}
        total_sum = 0.0

        for transaction in self._transactions:
            attribute_value = getattr(transaction, self._attribute, None)
            # A transaction without the attribute (for example an income when charting expense categories) is left out
            if attribute_value is not None:
                amount = transaction.amount * getattr(transaction, 'quantity', 1)
                totals[attribute_value] = totals.get(attribute_value, 0.0) + amount
                total_sum += amount
        if total_sum > 0:
            self._percentages = {key: (value / total_sum) * 100 for key, value in totals.items()}
        else:
            self._percentages = {}
        return self._percentages

    # A method to draw the pie chart and return the figure, or raises Value Error if the title or colors are not valid
    def generate_pie_chart(self, title: Optional[str] = None, colors: Optional[List[str]] = None) -> Figure:
        if title is not None and (not isinstance(title, str) or not title.strip()):
            raise ValueError("Title must be a non-empty text.")
        if colors is not None and (
            not isinstance(colors, (list, tuple)) or not colors
            or not all(isinstance(color, str) and color.strip() for color in colors)
        ):
            raise ValueError("Colors must be a non-empty list of color names or codes.")

        if not self._percentages:
            self.calculate_percentages()

        fig, ax = pyplot.subplots(figsize=(5, 5))
        labels = [str(label).upper() for label in self._percentages.keys()]
        sizes = list(self._percentages.values())

        try:
            if not sizes:
                ax.text(0.5, 0.5, "No Data Available", horizontalalignment='center', verticalalignment='center')
            else:
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
                ax.axis('equal')
        except ValueError as error:
            # Close the half-drawn figure so it does not stay in memory, then raise a clearer error
            pyplot.close(fig)
            raise ValueError(f"Could not draw the pie chart: {error}") from error

        chart_title = title.strip() if title else f"Distribution by {self._attribute.replace('_', ' ').title()}"
        ax.set_title(chart_title)
        return fig

    # A method to show the pie chart in a window, and close the figure afterwards
    def display_pie_chart(self) -> None:
        fig = self.generate_pie_chart()
        try:
            pyplot.show()
        finally:
            pyplot.close(fig)

    # A method to save the pie chart as an image file, or raises DataFileError if the file cannot be written
    def export_pie_chart(self, filename: str) -> None:
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Filename must be a non-empty text.")
        fig = self.generate_pie_chart()
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            fig.savefig(filename, bbox_inches='tight')
        except (OSError, ValueError) as error:
            reason = getattr(error, "strerror", None) or str(error)
            raise DataFileError(f"Could not save the chart to '{filename}' ({reason}).") from error
        finally:
            pyplot.close(fig)

    def convert_to_dict(self) -> Dict:
        return {
            "chart_id": self._chart_id,
            "attribute": self._attribute,
            "percentages": self._percentages
        }

    # A method to add the chart to a JSON file, or raises DataFileError if the file is not valid or cannot be written
    def save_to_json(self, filepath: Optional[str] = None) -> None:
        path = self._json_path if filepath is None else filepath
        data = read_json_list(path)
        data.append(self.convert_to_dict())
        write_json_file(path, data)


# A small test that draws a chart from stand-in transactions, so it needs no IET data
def pie_chart_test():
    from types import SimpleNamespace

    def expense(name, amount, mode, category, quantity=1):
        return SimpleNamespace(
            name=name, amount=amount, mode_of_payment=mode,
            category_of_payment=category, quantity=quantity
        )

    oct_expenses = [
        expense("Supermarket", 450.0, "cash", "groceries"),
        expense("AngryBee", 150.0, "credit", "food"),
        expense("Electric Bill", 450.0, "debit", "utilities"),
        expense("Supermarket 2", 550.0, "cash", "groceries"),
        expense("McDo", 500.0, "credit", "food"),
        expense("Paying Mr. Soprano", 800.0, "cash", "debt"),
        expense("FX Ride", 40.0, "cash", "transportation", quantity=2)
    ]

    chart = PieChart(attribute="category_of_payment", transactions=oct_expenses)
    custom_colors = ["#ad2c2c", "#006ad4", "#ffda1f", "#32a438", "#9010ba"]
    fig = chart.generate_pie_chart(colors=custom_colors)
    pyplot.show()
    pyplot.close(fig)


if __name__ == "__main__":
    pie_chart_test()