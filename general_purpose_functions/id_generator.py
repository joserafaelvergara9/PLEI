from custom_exceptions import *
import json

def id_generator(id_type):
    match id_type:
        case "income":
            json_source = "income_expense_tracker/iet_json_files/income.json"
            id_variable = "income_id"
            prefix = "INC"    
        case "expense":
            json_source = "income_expense_tracker/iet_json_files/expenses.json"
            id_variable = "expense_id"
            prefix = "EXP"
        case "receipt":
            json_source = "income_expense_tracker/iet_json_files/receipts.json"
            id_variable = "receipt_id"
            prefix = "REC"
        case "financialReport":
            json_source = "fin_report_generator/frg_json_files/financial_reports.json"
            id_variable = "report_id"
            prefix = "FIN"
        case "pieChart":
            json_source = "fin_report_generator/frg_json_files/pie_charts.json"
            id_variable = "chart_id"
            prefix = "PIE"
        case _:
            raise InvalidIDType(f"Unknown id_type: '{id_type}'")
    
    try:
        with open(json_source, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    last_num = 0

    for entry in data:
        current_id = entry.get(id_variable, "")
        if current_id.startswith(f"{prefix}-"):
            numeric_part = current_id.removeprefix(f"{prefix}-")
            if numeric_part.isdigit():
                num = int(numeric_part)
                if num > last_num: 
                    last_num = num

    next_num = last_num + 1
    return f"{prefix}-{next_num:04d}"