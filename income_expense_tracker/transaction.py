from abc import ABC, abstractmethod
import json
import os

test_dict = {
    "name": "Jess",
    "version": 1.0
}

def readData():
    with open("income_expense_tracker/iet_json_files/test.json", "r", encoding="utf-8") as file:
        return json.load(file)

def writeData(name, version):
    with open("income_expense_tracker/iet_json_files/test.json", "w", encoding="utf-8") as file:
        json.dump({"name": name, "version": version}, file, indent=4)


class Transaction(ABC):
    pass

print()
print(os.getcwd())
print()

print(readData())
writeData("Mark", 2.0)
print(readData())


