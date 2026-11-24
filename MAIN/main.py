import importlib
import sys
from functools import partial
from pathlib import Path

# The folder where this file is located, which is the root folder of the whole program
SCRIPT_DIR = Path(__file__).resolve().parent
# The root folder is the one that has the income_expense_tracker folder in it
# That is the folder of this file, or the one above it (for example if this file is kept in a subfolder such as "main")
ROOT_DIR = next(
    (folder for folder in (SCRIPT_DIR, SCRIPT_DIR.parent) if (folder / "income_expense_tracker").is_dir()),
    SCRIPT_DIR
)
IET_DIR = ROOT_DIR / "income_expense_tracker"
FRG_DIR = ROOT_DIR / "fin_report_generator"

# The root folder is needed so that the FRG and general_purpose_functions can be imported as packages
# The IET folder is needed because the IET files import each other directly (for example "from transaction import Expense")
for folder in (ROOT_DIR, IET_DIR):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

# The two branches of the program, as a name, the module that has its main() function, and its folder
IET_BRANCH = ("Income and Expense Tracker", "iet_main", IET_DIR)
FRG_BRANCH = ("Financial Report Generator", "fin_report_generator.frg_main", FRG_DIR)


# A class that handles the top-level menu and starts each branch, while each branch handles its own menu and data
# The IET saves every change to its JSON files, and the FRG reads those files each time it starts,
# so a report made right after using the IET always includes the latest transactions
class ProgramManager:
    # A static method to print the main menu
    @staticmethod
    def _show_menu():
        print()
        print("=-" * 17)
        print("   PERSONAL LEDGER FOR EXPENSES AND INCOME (P.L.E.I.)")
        print("=-" * 17)
        print("[1] Income and Expense Tracker")
        print("[2] Financial Report Generator")
        print("[3] Exit")

    # A static method to import the main module of a branch and run its main(), and return to the main menu when the branch exits
    # A branch that cannot be found or started, or stops because of an unexpected error, is reported instead of closing the whole program
    @staticmethod
    def _launch(name, module_name, folder):
        if not folder.is_dir():
            print(f"  The folder '{folder}' was not found, so the {name} cannot start.")
            return
        try:
            # The module is imported only when it is chosen, so a problem in one branch (for example a missing library) does not stop the other
            module = importlib.import_module(module_name)
            module.main()
        except ImportError as error:
            print(f"  Could not start the {name}: {error}")
        except (KeyboardInterrupt, EOFError):
            # Let the main loop below deal with these, the same way as for the menu itself
            raise
        except Exception as error:
            print(f"  The {name} stopped because of an unexpected error ({type(error).__name__}: {error}).")
        else:
            print(f"\nBack to the main menu.")

    # A method to show the menu again and again until the user chooses Exit
    def run(self):
        # A dictionary that maps each menu choice to the branch to start, so no long if/else chain is needed (3 is handled separately as Exit)
        actions = {
            "1": partial(self._launch, *IET_BRANCH),
            "2": partial(self._launch, *FRG_BRANCH),
        }
        while True:
            self._show_menu()
            try:
                choice = input("Enter your choice (1-3): ").strip()
                if choice == "3":
                    print("Thank you for using the program!")
                    break
                action = actions.get(choice)
                # None means the choice is not in the dictionary, so it is not valid
                if action is None:
                    if choice:
                        print(f"  '{choice}' is not a valid choice. Please enter a number from 1 to 3.")
                    else:
                        print("  You did not enter anything. Please enter a number from 1 to 3.")
                    continue
                action()
            except KeyboardInterrupt:
                # Ctrl+C cancels the current action and goes back to the menu
                print("\nOperation cancelled.")
            except EOFError:
                # The input has ended (for example Ctrl+D), so there is nothing more to read
                print("\nInput ended. Exiting.")
                break


def main():
    manager = ProgramManager()
    manager.run()

if __name__ == "__main__":
    main()