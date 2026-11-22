import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
import general_purpose_functions.custom_exceptions as cusexc
import json

def id_generator(id_type):
    # The paths are built from the root folder (not the current working directory),
    # so the saved IDs are found no matter where the program is run from
    match id_type:
        case "income":
            json_source = root_dir / "income_expense_tracker" / "iet_json_files" / "income.json"
            id_variable = "income_id"
            prefix = "INC"
        case "expense":
            json_source = root_dir / "income_expense_tracker" / "iet_json_files" / "expenses.json"
            id_variable = "expense_id"
            prefix = "EXP"
        case "receipt":
            json_source = root_dir / "income_expense_tracker" / "iet_json_files" / "receipt.json"
            id_variable = "receipt_id"
            prefix = "REC"
        case "financialReport":
            json_source = root_dir / "fin_report_generator" / "frg_json_files" / "financial_reports.json"
            id_variable = "report_id"
            prefix = "FIN"
        case "pieChart":
            json_source = root_dir / "fin_report_generator" / "frg_json_files" / "pie_charts.json"
            id_variable = "chart_id"
            prefix = "PIE"
        case _:
            raise cusexc.InvalidIDType(f"Unknown id_type: '{id_type}'")

    try:
        with open(json_source, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    if not isinstance(data, list):
        data = []

    last_num = 0

    for entry in data:
        # Skip anything that is not a record with a text ID
        if not isinstance(entry, dict):
            continue
        current_id = entry.get(id_variable, "")
        if not isinstance(current_id, str):
            continue
        if current_id.startswith(f"{prefix}-"):
            numeric_part = current_id.removeprefix(f"{prefix}-")
            if numeric_part.isdigit():
                num = int(numeric_part)
                if num > last_num:
                    last_num = num

    next_num = last_num + 1
    return f"{prefix}-{next_num:04d}"