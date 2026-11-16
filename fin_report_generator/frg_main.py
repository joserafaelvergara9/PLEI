import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fin_report_generator.financial_report import FinancialReport


FRG_DIR = Path(__file__).resolve().parent
IET_DIR = BASE_DIR / "income_expense_tracker"
EXPENSES_PATH = IET_DIR / "iet_json_files" / "expenses.json"
INCOME_PATH = IET_DIR / "iet_json_files" / "income.json"
REPORTS_PATH = FRG_DIR / "frg_json_files" / "financial_reports.json"
EXPORT_DIR = FRG_DIR / "frg_exports"


@dataclass
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


class FinancialReportCLI:
    """Handles FRG menus, report inputs, chart display, and report exports."""

    def __init__(self):
        self.expenses: List[TransactionRecord] = []
        self.income: List[TransactionRecord] = []
        self.current_report: Optional[FinancialReport] = None
        self.load_warnings: List[str] = []

    # ------------------------- DATA LOADING -------------------------

    @staticmethod
    def _read_json_records(filepath: Path) -> List[dict]:
        if not filepath.exists():
            return []
        try:
            with filepath.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError) as error:
            raise ValueError(f"Could not read {filepath.name}: {error}") from error
        if not isinstance(data, list):
            raise ValueError(f"{filepath.name} must contain a JSON list.")
        return data

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Missing transaction timestamp.")
        return datetime.fromisoformat(value.strip())

    def _make_record(self, data: dict, transaction_type: str) -> TransactionRecord:
        timestamp = self._parse_timestamp(data.get("timestamp"))
        amount = float(data["amount"])
        if amount < 0:
            raise ValueError("Transaction amount cannot be negative.")

        if transaction_type == "expense":
            category = data.get("category_of_payment")
            transaction_id = data.get("expense_id", "")
            quantity = int(data.get("quantity", 1))
            if quantity < 1:
                raise ValueError("Expense quantity must be at least 1.")
        else:
            category = data.get("category_of_income")
            transaction_id = data.get("income_id", "")
            quantity = 1

        if not category:
            raise ValueError("Missing transaction category.")

        comments = data.get("comments", [])
        return TransactionRecord(
            name=str(data.get("name", "Unnamed transaction")),
            amount=amount,
            mode_of_payment=str(data.get("mode_of_payment", "Unknown")),
            timestamp=timestamp,
            transaction_type=transaction_type,
            category=str(category),
            quantity=quantity,
            transaction_id=str(transaction_id),
            receipt=data.get("receipt"),
            comments=comments,
        )

    def _load_transaction_file(self, filepath: Path, transaction_type: str) -> List[TransactionRecord]:
        records: List[TransactionRecord] = []
        raw_records = self._read_json_records(filepath)
        for line_number, data in enumerate(raw_records, start=1):
            try:
                if not isinstance(data, dict):
                    raise ValueError("Record is not a JSON object.")
                records.append(self._make_record(data, transaction_type))
            except (KeyError, TypeError, ValueError) as error:
                self.load_warnings.append(
                    f"{filepath.name}, record {line_number}: {error} (skipped)"
                )
        return records

    def _load_transactions(self) -> None:
        """Read IET's existing JSON records; no IET data is modified."""
        self.load_warnings = []
        try:
            self.expenses = self._load_transaction_file(EXPENSES_PATH, "expense")
            self.income = self._load_transaction_file(INCOME_PATH, "income")
        except ValueError as error:
            print(f"\nUnable to load transaction data: {error}")
            self.expenses = []
            self.income = []
            return

        print("\nIET transaction data loaded for FRG.")
        print(f"  Expenses: {len(self.expenses)}")
        print(f"  Income:   {len(self.income)}")
        if self.load_warnings:
            print(f"  Skipped records: {len(self.load_warnings)}")
            for warning in self.load_warnings:
                print(f"  - {warning}")

    # ------------------------- INPUT HELPERS -------------------------

    @staticmethod
    def _ask_date(label: str) -> datetime:
        while True:
            text = input(f"{label} (YYYY-MM-DD): ").strip()
            try:
                return datetime.strptime(text, "%Y-%m-%d")
            except ValueError:
                print("  Invalid date. Please use YYYY-MM-DD.")

    @staticmethod
    def _ask_text(label: str, allow_blank: bool = True) -> str:
        while True:
            value = input(f"{label}: ").strip()
            if value or allow_blank:
                return value
            print("  This field cannot be empty.")

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

    @staticmethod
    def _show_menu() -> None:
        print("\n" + "=" * 43)
        print("       FINANCIAL REPORT GENERATOR")
        print("=" * 43)
        print("[1] Generate Financial Report")
        print("[2] View Current Report")
        print("[3] View Pie Chart")
        print("[4] Save / Export Current Report")
        print("[5] View Saved Reports")
        print("[6] Reload IET Transaction Data")
        print("[7] Exit")
        print("=" * 43)

    def _print_current_report(self) -> None:
        if self.current_report is None:
            print("\nNo report has been generated yet. Choose option [1] first.")
            return
        print("\n" + "=" * 43)
        print("             FINANCIAL REPORT")
        print("=" * 43)
        print(self.current_report)
        print("=" * 43)

    @staticmethod
    def _print_transaction_summary(expenses: List[TransactionRecord], income: List[TransactionRecord]) -> None:
        print("\nTRANSACTION SUMMARY FOR SELECTED PERIOD")
        print("-" * 72)
        print(f"{'TYPE':<10}{'DATE':<13}{'DESCRIPTION':<25}{'AMOUNT':>14}{'CATEGORY':>10}")
        print("-" * 72)
        combined = [(item, "Expense") for item in expenses] + [(item, "Income") for item in income]
        combined.sort(key=lambda pair: pair[0].timestamp)
        for item, kind in combined:
            category = item.category
            signed_amount = f"{item.amount * item.quantity:,.2f}"
            print(f"{kind:<10}{item.timestamp:%Y-%m-%d}   {item.name[:24]:<25}{signed_amount:>14} {category[:10]:>10}")
        print("-" * 72)
        print(f"Transactions included: {len(combined)}")

    # ------------------------- MENU ACTIONS -------------------------

    def generate_financial_report(self) -> None:
        print("\n=-= Generate Financial Report =-=")
        if not self.expenses and not self.income:
            print("No IET transaction records are available to generate a report.")
            return

        start_date = self._ask_date("Start date")
        end_date = self._ask_date("End date")
        end_date = datetime.combine(end_date.date(), time.max)
        if end_date < start_date:
            print("End date cannot be earlier than start date.")
            return

        expenses_description = self._ask_text("Expense description (optional)")
        income_description = self._ask_text("Income description (optional)")

        try:
            report = FinancialReport(
                range_of_time=(start_date, end_date),
                expenses=self.expenses,
                income=self.income,
                expenses_description=expenses_description,
                income_description=income_description,
            )
        except (ValueError, TypeError, OSError) as error:
            print(f"Could not generate the report: {error}")
            return

        self.current_report = report
        print("\nFinancial report generated successfully.")
        self._print_transaction_summary(report.expenses, report.income)
        self._print_current_report()

    def view_current_report(self) -> None:
        self._print_current_report()

    def view_pie_chart(self) -> None:
        print("\n=-= View Pie Chart =-=")
        if self.current_report is None:
            print("Generate a financial report first before viewing its charts.")
            return
        charts = self.current_report.pie_charts
        if not charts:
            print("There are no expense pie charts for this report's date range.")
            return

        print("Available charts:")
        for index, chart in enumerate(charts, start=1):
            print(f"[{index}] Distribution by {chart.attribute.replace('_', ' ').title()}")

        while True:
            choice = input(f"Choose a chart (1-{len(charts)}) or 0 to cancel: ").strip()
            if choice == "0":
                print("Chart viewing cancelled.")
                return
            if choice.isdigit() and 1 <= int(choice) <= len(charts):
                charts[int(choice) - 1].display_pie_chart()
                return
            print("Invalid choice. Please select one of the listed charts.")

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
                EXPORT_DIR.mkdir(parents=True, exist_ok=True)
                filename = EXPORT_DIR / f"{self.current_report.report_id}.json"
                self.current_report.export_report(str(filename))
                print(f"Report exported to: {filename}")
            elif choice == "3":
                charts = self.current_report.pie_charts
                if not charts:
                    print("There are no charts to export.")
                    return
                EXPORT_DIR.mkdir(parents=True, exist_ok=True)
                for chart in charts:
                    filename = EXPORT_DIR / f"{self.current_report.report_id}_{chart.attribute}.png"
                    chart.export_pie_chart(str(filename))
                    print(f"Chart exported: {filename.name}")
            elif choice == "4":
                return
            else:
                print("Invalid choice. Please select 1-4.")
        except (OSError, TypeError, ValueError) as error:
            print(f"Could not save or export the report: {error}")

    def view_saved_reports(self) -> None:
        print("\n=-= Saved Financial Reports =-=")
        if not REPORTS_PATH.exists():
            print("No saved report history was found.")
            return
        try:
            with REPORTS_PATH.open("r", encoding="utf-8") as file:
                reports = json.load(file)
        except (json.JSONDecodeError, OSError) as error:
            print(f"Could not read saved reports: {error}")
            return

        if not isinstance(reports, list) or not reports:
            print("No saved reports were found.")
            return

        print(f"{'#':<4}{'REPORT ID':<25}{'TOTAL INCOME':>15}{'TOTAL EXPENSES':>18}{'RESULT':>12}")
        print("-" * 76)
        for index, report in enumerate(reports, start=1):
            if not isinstance(report, dict):
                continue
            report_id = str(report.get("report_id", "Unknown"))
            income_total = float(report.get("total_income", 0))
            expense_total = float(report.get("total_expenses", 0))
            result = str(report.get("gain_or_loss", "Unknown"))
            print(f"{index:<4}{report_id[:24]:<25}{income_total:>15,.2f}{expense_total:>18,.2f}{result:>12}")
        print("-" * 76)
        print(f"Saved report count: {len(reports)}")

    def reload_transaction_data(self) -> None:
        if self._confirm("Reload the latest transaction data from IET"):
            self._load_transactions()
            self.current_report = None
            print("Current report cleared. Generate a new report to use the refreshed data.")

    # ------------------------- MAIN LOOP -------------------------

    def run(self) -> None:
        self._load_transactions()
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
                if action is None:
                    print("Invalid choice. Please enter a number from 1 to 7.")
                    continue
                action()
            except KeyboardInterrupt:
                print("\nOperation cancelled. Returning to the main menu.")
            except EOFError:
                print("\nInput ended. Exiting the FRG.")
                break


def main() -> None:
    cli = FinancialReportCLI()
    cli.run()


if __name__ == "__main__":
    main()