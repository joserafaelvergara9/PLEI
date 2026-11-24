import json
import os
import sys
from datetime import datetime

# main.py works out the root folder and sets up sys.path, so it is reused here
import main as program

ROOT_DIR = program.ROOT_DIR
EXPENSES_PATH = program.IET_DIR / "iet_json_files" / "expenses.json"
INCOME_PATH = program.IET_DIR / "iet_json_files" / "income.json"
REPORTS_PATH = program.FRG_DIR / "frg_json_files" / "financial_reports.json"
WIDTH = 60
APP_TITLE = "PERSONAL LEDGER FOR EXPENSES AND INCOME (P.L.E.I.)"
APP_VERSION = "0.1"

def _setup_terminal():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if os.name == "nt":
        os.system("")  
        os.system("title Personal Ledger for Expenses and Income")


def _colors_enabled():
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


class Style:
    """ANSI color helpers that return plain text when colors are off."""
    ENABLED = False
    CODES = {"pink": "38;5;218", "green": "32", "yellow": "33", "red": "31",
         "baby_blue": "38;5;117", "dim": "2", "bold": "1"}

    @classmethod
    def paint(cls, text, *names):
        if not cls.ENABLED:
            return text
        codes = ";".join(cls.CODES[name] for name in names)
        return f"\033[{codes}m{text}\033[0m"


def clear_screen():
    if Style.ENABLED:
        os.system("cls" if os.name == "nt" else "clear")


def box(lines, color="pink"):
    """Print the lines inside a double-line box, each line centered."""
    paint = lambda t: Style.paint(t, color)
    print(paint("╔" + "═" * (WIDTH - 2) + "╗"))
    for line in lines:
        print(paint("║") + Style.paint(line.center(WIDTH - 2), "bold") + paint("║"))
    print(paint("╚" + "═" * (WIDTH - 2) + "╝"))


def heading(text):
    print()
    print(Style.paint(f"── {text} ".ljust(WIDTH, "─"), "pink"))


def info(text):
    print(Style.paint(f"  ℹ {text}", "dim"))


def success(text):
    print(Style.paint(f"  ✔ {text}", "green"))


def warn(text):
    print(Style.paint(f"  ⚠ {text}", "yellow"))


def error(text):
    print(Style.paint(f"  ✖ {text}", "red"))


def pause(message="Press Enter to continue..."):
    input(Style.paint(f"\n  {message}", "dim"))


def ask_yes_no(question, default=True):
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"  {question} [{hint}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        warn("Please answer with y or n.")


def _count_records(path):
    """Return how many records a JSON list file has, or None if it is missing or unreadable."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return 0
    except (OSError, ValueError):
        return None
    return len(data) if isinstance(data, list) else None


def _sum_totals():
    """Return (total income, total expenses) from the saved files, or None if either cannot be read."""
    try:
        with open(EXPENSES_PATH, "r", encoding="utf-8") as file:
            expenses = json.load(file)
    except FileNotFoundError:
        expenses = []
    except (OSError, ValueError):
        return None
    try:
        with open(INCOME_PATH, "r", encoding="utf-8") as file:
            income = json.load(file)
    except FileNotFoundError:
        income = []
    except (OSError, ValueError):
        return None
    try:
        spent = sum(float(e["amount"]) * int(e.get("quantity", 1)) for e in expenses)
        earned = sum(float(i["amount"]) for i in income)
    except (KeyError, TypeError, ValueError):
        return None
    return round(earned, 2), round(spent, 2)


def _fmt_count(value):
    return "unreadable" if value is None else str(value)


def show_dashboard():
    expenses = _count_records(EXPENSES_PATH)
    income = _count_records(INCOME_PATH)
    reports = _count_records(REPORTS_PATH)
    totals = _sum_totals()

    heading("Your data at a glance")
    print(f"  Expenses recorded : {Style.paint(_fmt_count(expenses), 'bold')}")
    print(f"  Income recorded   : {Style.paint(_fmt_count(income), 'bold')}")
    print(f"  Saved reports     : {Style.paint(_fmt_count(reports), 'bold')}")
    if totals is not None and (expenses or income):
        earned, spent = totals
        net = round(earned - spent, 2)
        color = "green" if net > 0 else "red" if net < 0 else "yellow"
        print(f"  Total income      : P{earned:,.2f}")
        print(f"  Total expenses    : P{spent:,.2f}")
        print(f"  Net balance       : {Style.paint(f'P{net:,.2f}', color, 'bold')}")


def run_branch(branch, banner):
    """Start one branch (IET or FRG) with its own menu, and come back here when it exits."""
    name, module_name, folder = branch
    clear_screen()
    box([banner, "Choose Exit inside it to return here"], "baby_blue")
    program.ProgramManager._launch(name, module_name, folder)


def guided_walkthrough():
    clear_screen()
    box(["GUIDED WALKTHROUGH", "Track money  →  Build a report  →  Save it"], "green")
    print("""
  This takes you through the whole process in order:

    STEP 1  Set up categories and record your income and expenses
            (Income and Expense Tracker)
    STEP 2  Pick a date range, view the report and pie charts, then
            save or export them (Financial Report Generator)
""")
    info("Tip: in Step 1 use option [8] to add categories first, then [1] to add transactions.")
    info("Choose Exit inside each tool when you are done, and the walkthrough moves on.")
    if not ask_yes_no("Ready to begin?"):
        return

    heading("STEP 1 of 2 - Record transactions")
    run_branch(program.IET_BRANCH, "STEP 1 · INCOME & EXPENSE TRACKER")

    expenses, income = _count_records(EXPENSES_PATH), _count_records(INCOME_PATH)
    if not (expenses or income):
        warn("There are no transactions saved yet, so a report would be empty.")
        if not ask_yes_no("Go back and record some now?"):
            return
        run_branch(program.IET_BRANCH, "STEP 1 · INCOME & EXPENSE TRACKER")
        if not (_count_records(EXPENSES_PATH) or _count_records(INCOME_PATH)):
            warn("Still no transactions, so the walkthrough stops here.")
            return

    show_dashboard()
    if not ask_yes_no("Continue to Step 2 and build a report?"):
        return

    heading("STEP 2 of 2 - Generate a report")
    info("In the report tool: [1] generate, [3] view charts, [4] save or export.")
    run_branch(program.FRG_BRANCH, "STEP 2 · FINANCIAL REPORT GENERATOR")

    print()
    box(["WALKTHROUGH COMPLETE", "Your data and reports are saved"], "green")
    show_dashboard()
    pause("Press Enter to return to the main menu...")


def show_help():
    clear_screen()
    box(["HELP & TIPS"], "yellow")
    print(f"""
  Where things are saved
    Transactions : {EXPENSES_PATH.parent}
    Reports      : {REPORTS_PATH.parent}

  Good to know
    - Every change in the Tracker is saved straight away.
    - The Report Generator reads the latest Tracker data each time it
      opens (or when you use its Reload option).
    - Add a category in the Tracker before adding transactions.
    - Dates: reports use YYYY-MM-DD, the Tracker's filters use
      YYYY-MM-DD HH:MM.
    - Press Ctrl+C at any prompt to cancel the current action.
    - Set the NO_COLOR environment variable to turn colors off.
""")
    pause()


class CommandPromptApp:
    @staticmethod
    def _show_menu():
        print()
        box([APP_TITLE, f"v{APP_VERSION}  ·  {datetime.now():%A, %d %B %Y}"])
        show_dashboard()
        heading("Main menu")
        print(f"  {Style.paint('[1]', 'pink', 'bold')} Guided walkthrough  {Style.paint('(recommended for first use)', 'dim')}")
        print(f"  {Style.paint('[2]', 'pink', 'bold')} Income and Expense Tracker")
        print(f"  {Style.paint('[3]', 'pink', 'bold')} Financial Report Generator")
        print(f"  {Style.paint('[4]', 'pink', 'bold')} Help & tips")
        print(f"  {Style.paint('[5]', 'pink', 'bold')} Exit")

    def run(self):
        actions = {
            "1": guided_walkthrough,
            "2": lambda: run_branch(program.IET_BRANCH, "INCOME & EXPENSE TRACKER"),
            "3": lambda: run_branch(program.FRG_BRANCH, "FINANCIAL REPORT GENERATOR"),
            "4": show_help,
        }
        first = True
        while True:
            if first:
                clear_screen()
                first = False
            self._show_menu()
            try:
                choice = input(Style.paint("\n  Enter your choice (1-5): ", "bold")).strip()
                if choice == "5":
                    print()
                    box(["Thank you for using the program!", "Goodbye 👋"], "green")
                    break
                action = actions.get(choice)
                if action is None:
                    error(f"'{choice}' is not a valid choice. Please enter a number from 1 to 5."
                          if choice else "You did not enter anything. Please enter a number from 1 to 5.")
                    continue
                action()
            except KeyboardInterrupt:
                print()
                warn("Operation cancelled.")
            except EOFError:
                print()
                warn("Input ended. Exiting.")
                break


def main():
    _setup_terminal()
    Style.ENABLED = _colors_enabled()
    CommandPromptApp().run()


if __name__ == "__main__":
    main()