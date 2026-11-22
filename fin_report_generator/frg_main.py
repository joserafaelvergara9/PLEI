import math
import sys
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fin_report_generator.financial_report import FinancialReport
from fin_report_generator.pie_chart import DataFileError, read_json_list


FRG_DIR = Path(__file__).resolve().parent
IET_DIR = BASE_DIR / "income_expense_tracker"
EXPENSES_PATH = IET_DIR / "iet_json_files" / "expenses.json"
INCOME_PATH = IET_DIR / "iet_json_files" / "income.json"
REPORTS_PATH = FRG_DIR / "frg_json_files" / "financial_reports.json"
EXPORT_DIR = FRG_DIR / "frg_exports"


@dataclass(frozen=True)
class TransactionRecord:
    """A read-only transaction-shaped record used by the FRG.

    The FRG reads IET JSON files and wraps valid rows in this small object.
    This avoids taking responsibility for IET transaction creation or editing.
    """

    name: str
    amount: float
    mode_of_payment: str
    timestamp: datetime
    transaction_type: str
    category: str
    quantity: int = 1
    transaction_id: str = ""
    receipt: Any = None
    comments: Any = None

    # A static method to return a stripped version of a string, or if it is not a str or is empty, raises Value Error
    @staticmethod
    def _clean_text(value, label):
        if not isinstance(value, str):
            raise ValueError(f"{label} must be in String (text) format.")
        value = value.strip()
        if not value:
            raise ValueError(f"{label} cannot be empty.")
        return value

    # A static method to return the amount as a float, or raises Value Error if it is not a number greater than 0
    @staticmethod
    def _clean_amount(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Amount must be a number.")
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Amount must be greater than 0.")
        return float(value)

    # A static method to return the quantity, or raises Value Error if it is not a whole number of at least 1
    @staticmethod
    def _clean_quantity(value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Quantity must be a whole number.")
        if value < 1:
            raise ValueError("Quantity must be at least 1.")
        return value

    # A static method to return a datetime from a date-time string, or raises Value Error if it is missing, not valid or has a time zone (IET never saves one, and it could not be compared with the report range)
    @staticmethod
    def _clean_timestamp(value):
        text = TransactionRecord._clean_text(value, "Timestamp")
        try:
            timestamp = datetime.fromisoformat(text)
        except ValueError:
            raise ValueError(f"Timestamp '{text}' is not a valid date and time.") from None
        if timestamp.tzinfo is not None:
            raise ValueError("Timestamp must not include a time zone.")
        return timestamp

    # A class method to create a record from a dictionary of an IET JSON file, or raises Value Error if it is not a dict or has missing fields or invalid values
    @classmethod
    def load_from_dict(cls, data, transaction_type):
        if transaction_type not in ("expense", "income"):
            raise ValueError("Transaction type must be 'expense' or 'income'.")
        if not isinstance(data, dict):
            raise ValueError("Record is not a JSON object.")

        if transaction_type == "expense":
            id_field, category_field = "expense_id", "category_of_payment"
        else:
            id_field, category_field = "income_id", "category_of_income"
        required_fields = ("name", "amount", "mode_of_payment", "timestamp", id_field, category_field)
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing fields: {', '.join(missing_fields)}")

        # An expense without a quantity counts as 1, but an income has no quantity
        quantity = cls._clean_quantity(data.get("quantity", 1)) if transaction_type == "expense" else 1
        return cls(
            name=cls._clean_text(data["name"], "Name"),
            amount=cls._clean_amount(data["amount"]),
            mode_of_payment=cls._clean_text(data["mode_of_payment"], "Mode of payment"),
            timestamp=cls._clean_timestamp(data["timestamp"]),
            transaction_type=transaction_type,
            category=cls._clean_text(data[category_field], "Category"),
            quantity=quantity,
            transaction_id=cls._clean_text(data[id_field], "Transaction ID"),
            receipt=data.get("receipt"),
            comments=data.get("comments", []),
        )

    @property
    def category_of_payment(self) -> Optional[str]:
        return self.category if self.transaction_type == "expense" else None

    @property
    def category_of_income(self) -> Optional[str]:
        return self.category if self.transaction_type == "income" else None

    def convert_to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "amount": self.amount,
            "mode_of_payment": self.mode_of_payment,
            "timestamp": self.timestamp.isoformat(sep=" "),
            "receipt": self.receipt,
            "comments": self.comments,
        }
        if self.transaction_type == "expense":
            result.update({
                "expense_id": self.transaction_id,
                "category_of_payment": self.category,
                "quantity": self.quantity,
            })
        else:
            result.update({
                "income_id": self.transaction_id,
                "category_of_income": self.category,
            })
        return result

    def __str__(self) -> str:
        return f"{self.name} ({self.transaction_type}) - PHP {self.amount:,.2f}"


# A class that handles the menu and all the user input and output, while FinancialReport handles the report itself
class FinancialReportManager:
    def __init__(self):
        self.expenses: List[TransactionRecord] = []
        self.income: List[TransactionRecord] = []
        self.current_report: Optional[FinancialReport] = None
        self.load_warnings: List[str] = []

    # ------------------------- DATA LOADING -------------------------

    # A method to read one IET JSON file and return the valid records in it, and add a warning for each file or record that was skipped
    # IET's data is only read and never changed, so a bad record is skipped instead of stopping everything
    def _load_transaction_file(self, filepath: Path, transaction_type: str) -> List[TransactionRecord]:
        records: List[TransactionRecord] = []
        seen_ids = set()
        try:
            raw_records = read_json_list(filepath)
        except DataFileError as error:
            self.load_warnings.append(f"{error}; no {transaction_type} records were loaded")
            return records
        for number, data in enumerate(raw_records, start=1):
            try:
                record = TransactionRecord.load_from_dict(data, transaction_type)
            except ValueError as error:
                self.load_warnings.append(f"{filepath.name}, record {number}: {error} (skipped)")
                continue
            if record.transaction_id in seen_ids:
                self.load_warnings.append(
                    f"{filepath.name}, record {number}: repeats the ID '{record.transaction_id}' (skipped)"
                )
                continue
            seen_ids.add(record.transaction_id)
            records.append(record)
        return records

    # A method to load the expenses and the income of IET, and tell the user how many were loaded and what was skipped
    def _load_transactions(self) -> None:
        self.load_warnings = []
        self.expenses = self._load_transaction_file(EXPENSES_PATH, "expense")
        self.income = self._load_transaction_file(INCOME_PATH, "income")

        print("\nIET transaction data loaded for FRG.")
        print(f"  Expenses: {len(self.expenses)}")
        print(f"  Income:   {len(self.income)}")
        if self.load_warnings:
            print(f"  Warnings: {len(self.load_warnings)}")
            for warning in self.load_warnings:
                print(f"  - {warning}")

    # ------------------------- INPUT HELPERS -------------------------

    # A static method to convert the text typed by the user to a date, or raises Value Error if it is not valid
    @staticmethod
    def _to_date(text):
        try:
            return datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            # "from None" hides the original strptime error so only the friendlier message is shown
            raise ValueError("Date must be a real date in the format YYYY-MM-DD") from None

    # A static method to keep asking for one value until a valid one is entered, and return it
    # converter turns the typed text into the right type, and cleaner checks the value and raises Value Error if it is not valid
    # If optional is True, pressing Enter skips the question and returns None
    @staticmethod
    def _ask_field(label, cleaner=None, converter=None, optional=False):
        while True:
            suffix = " (Enter to skip)" if optional else ""
            text = input(f"{label}{suffix}: ").strip()
            if optional and not text:
                return None
            try:
                value = converter(text) if converter else text
                return cleaner(value) if cleaner else value
            except ValueError as error:
                print(f"  Invalid input: {str(error).rstrip('.')}. Please try again.")

    # A static method to ask a yes or no question until the user answers, and return True for yes or False for no
    @staticmethod
    def _confirm(question: str) -> bool:
        while True:
            answer = input(f"{question} (y/n): ").strip().lower()
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no"):
                return False
            print("Please answer with y or n.")

    # ------------------------- DISPLAY HELPERS -------------------------

    # A static method to print the main menu
    @staticmethod
    def _show_menu() -> None:
        print()
        print("=-" * 17)
        print("   FINANCIAL REPORT GENERATOR")
        print("=-" * 17)
        print("[1] Generate Financial Report")
        print("[2] View Current Report")
        print("[3] View Pie Chart")
        print("[4] Save / Export Current Report")
        print("[5] View Saved Reports")
        print("[6] Reload IET Transaction Data")
        print("[7] Exit")

    def _print_current_report(self) -> None:
        if self.current_report is None:
            print("\nNo report has been generated yet. Choose option [1] first.")
            return
        print("\n" + "=-" * 17)
        print("        FINANCIAL REPORT")
        print("=-" * 17)
        print(self.current_report)
        print("=-" * 17)

    # A static method to return a readable name for a chart, saying whether it is about expenses or income
    @staticmethod
    def _chart_label(chart) -> str:
        source = "Income" if chart.attribute == "category_of_income" else "Expenses"
        return f"{source}: Distribution by {chart.attribute.replace('_', ' ').title()}"

    # A static method to print the transactions of the report as a table, sorted by time
    @staticmethod
    def _print_transaction_summary(expenses: List[TransactionRecord], income: List[TransactionRecord]) -> None:
        print("\nTRANSACTION SUMMARY FOR SELECTED PERIOD")
        print("-" * 73)
        print(f"{'TYPE':<10}{'DATE':<13}{'DESCRIPTION':<25}{'AMOUNT':>14} {'CATEGORY':>10}")
        print("-" * 73)
        combined = [(item, "Expense") for item in expenses] + [(item, "Income") for item in income]
        combined.sort(key=lambda pair: pair[0].timestamp)
        for item, kind in combined:
            category = item.category
            total_amount = f"{item.amount * item.quantity:,.2f}"
            print(f"{kind:<10}{item.timestamp:%Y-%m-%d}   {item.name[:24]:<25}{total_amount:>14} {category[:10]:>10}")
        print("-" * 73)
        print(f"Transactions included: {len(combined)}")

    # ------------------------- MENU ACTIONS -------------------------

    # [1] Generate Financial Report
    # A method to ask for the dates and descriptions, then build the report and print it
    def generate_financial_report(self) -> None:
        print("\n=-= Generate Financial Report =-=")
        if not self.expenses and not self.income:
            print("No IET transaction records are available to generate a report.")
            return

        start_date = self._ask_field("Start date (YYYY-MM-DD)", converter=self._to_date)
        end_date = self._ask_field("End date (YYYY-MM-DD)", converter=self._to_date)
        # The whole of the end date counts, so the range ends at the last moment of that day
        end_date = datetime.combine(end_date.date(), time.max)
        if end_date < start_date:
            print("  End date cannot be earlier than start date.")
            return

        # None means the user pressed Enter, so the description stays empty
        expenses_description = self._ask_field(
            "Expense description", FinancialReport.clean_description, optional=True) or ""
        income_description = self._ask_field(
            "Income description", FinancialReport.clean_description, optional=True) or ""

        # The values were already checked one by one, so these errors are only a safety net
        try:
            report = FinancialReport(
                range_of_time=(start_date, end_date),
                expenses=self.expenses,
                income=self.income,
                expenses_description=expenses_description,
                income_description=income_description,
            )
        except (ValueError, TypeError) as error:
            print(f"  Could not generate the report: {error}")
            return

        self.current_report = report
        print("\nFinancial report generated successfully.")
        self._print_transaction_summary(report.expenses, report.income)
        self._print_current_report()

    # [2] View Current Report
    def view_current_report(self) -> None:
        self._print_current_report()

    # [3] View Pie Chart
    # A method to ask which chart of the current report to show, then show it
    def view_pie_chart(self) -> None:
        print("\n=-= View Pie Chart =-=")
        if self.current_report is None:
            print("Generate a financial report first before viewing its charts.")
            return
        charts = self.current_report.pie_charts
        if not charts:
            print("There are no pie charts for this report's date range.")
            return

        print("Available charts:")
        for index, chart in enumerate(charts, start=1):
            print(f"[{index}] {self._chart_label(chart)}")

        while True:
            choice = input(f"Choose a chart (1-{len(charts)}) or 0 to cancel: ").strip()
            if choice == "0":
                print("Chart viewing cancelled.")
                return
            if choice.isdecimal() and 1 <= int(choice) <= len(charts):
                try:
                    charts[int(choice) - 1].display_pie_chart()
                except (ValueError, RuntimeError) as error:
                    print(f"  Could not show the chart: {error}")
                return
            print("  Invalid choice. Please select one of the listed charts.")

    # [4] Save / Export Current Report
    def save_export_report(self) -> None:
        print("\n=-= Save / Export Current Report =-=")
        if self.current_report is None:
            print("Generate a financial report first.")
            return

        print("[1] Save report to FRG report history (JSON)")
        print("[2] Export report as a separate JSON file")
        print("[3] Export all pie charts as PNG files")
        print("[4] Return to main menu")
        choice = input("Choose an action (1-4): ").strip()

        try:
            if choice == "1":
                self.current_report.save_to_json(str(REPORTS_PATH))
                print(f"Report saved to: {REPORTS_PATH}")
            elif choice == "2":
                filename = EXPORT_DIR / f"{self.current_report.report_id}.json"
                self.current_report.export_report(str(filename))
                print(f"Report exported to: {filename}")
            elif choice == "3":
                charts = self.current_report.pie_charts
                if not charts:
                    print("There are no charts to export.")
                    return
                for chart in charts:
                    filename = EXPORT_DIR / f"{self.current_report.report_id}_{chart.attribute}.png"
                    chart.export_pie_chart(str(filename))
                    print(f"Chart exported: {filename.name}")
            elif choice == "4":
                return
            else:
                print("  Invalid choice. Please select 1-4.")
        except DataFileError as error:
            print(f"  {error}\n  Nothing more was saved.")
        except ValueError as error:
            print(f"  Could not save or export the report: {error}")

    # [5] View Saved Reports
    # A method to print a table of the saved reports, where an unreadable record is shown as such instead of stopping
    def view_saved_reports(self) -> None:
        print("\n=-= Saved Financial Reports =-=")
        try:
            reports = read_json_list(REPORTS_PATH)
        except DataFileError as error:
            print(f"  {error}")
            return
        if not reports:
            print("No saved reports were found.")
            return

        print(f"{'#':<4}{'REPORT ID':<25}{'TOTAL INCOME':>15}{'TOTAL EXPENSES':>18}{'RESULT':>12}")
        print("-" * 74)
        readable_count = 0
        for index, report in enumerate(reports, start=1):
            try:
                report_id = str(report["report_id"])
                income_total = float(report["total_income"])
                expense_total = float(report["total_expenses"])
                result = str(report["gain_or_loss"])
            except (KeyError, TypeError, ValueError):
                print(f"{index:<4}(this record is unreadable)")
                continue
            readable_count += 1
            print(f"{index:<4}{report_id[:24]:<25}{income_total:>15,.2f}{expense_total:>18,.2f}{result:>12}")
        print("-" * 74)
        print(f"Saved report count: {len(reports)} ({readable_count} readable)")

    # [6] Reload IET Transaction Data
    def reload_transaction_data(self) -> None:
        if self._confirm("Reload the latest transaction data from IET"):
            self._load_transactions()
            self.current_report = None
            print("Current report cleared. Generate a new report to use the refreshed data.")

    # ------------------------- MAIN LOOP -------------------------

    # A method to show the menu again and again until the user chooses Exit
    def run(self) -> None:
        self._load_transactions()
        # A dictionary that maps each menu choice to the method to run, so no long if/else chain is needed (7 is handled separately as Exit)
        actions = {
            "1": self.generate_financial_report,
            "2": self.view_current_report,
            "3": self.view_pie_chart,
            "4": self.save_export_report,
            "5": self.view_saved_reports,
            "6": self.reload_transaction_data,
        }

        while True:
            self._show_menu()
            try:
                choice = input("Enter your choice (1-7): ").strip()
                if choice == "7":
                    print("Thank you for using the Financial Report Generator!")
                    break
                action = actions.get(choice)
                # None means the choice is not in the dictionary, so it is not valid
                if action is None:
                    if choice:
                        print(f"  '{choice}' is not a valid choice. Please enter a number from 1 to 7.")
                    else:
                        print("  You did not enter anything. Please enter a number from 1 to 7.")
                    continue
                action()
            except KeyboardInterrupt:
                # Ctrl+C cancels the current action and goes back to the menu
                print("\nOperation cancelled. Returning to the main menu.")
            except EOFError:
                # The input has ended (for example Ctrl+D), so there is nothing more to read
                print("\nInput ended. Exiting the FRG.")
                break


def main() -> None:
    manager = FinancialReportManager()
    manager.run()


if __name__ == "__main__":
    main()