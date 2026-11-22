import sys
import os
import json
import math
import tempfile
from datetime import datetime
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent # Get path to your root folder
sys.path.append(str(root_dir)) # Add root folder to sys.path
from general_purpose_functions.id_generator import id_generator

# The folder where this file is located, so the data files are always found next to it no matter where the program is run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "iet_json_files", "receipt.json")


# A custom error to raise when a JSON file cannot be read or understood or written
# It lives here (the lowest-level module) so that every other module can import it without a circular import
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


# A function to write a list to a JSON file, or raises DataFileError if it cannot be written
# It writes to a temporary file in the same folder first, then replaces the real file, so a failed save cannot damage it
def write_json_list(path, data):
    folder = os.path.dirname(os.path.abspath(path))
    temp_path = None
    try:
        os.makedirs(folder, exist_ok=True)
        file_descriptor, temp_path = tempfile.mkstemp(dir=folder, prefix="iet_", suffix=".tmp")
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, indent=4, ensure_ascii=False)
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


class Receipt:
    # Constants for the names of all fields related to Receipt
    FIELDS = ("receipt_id", "timestamp", "amount", "organization", "address")

    def __init__(
            self,
            amount: float,
            organization: str,
            address: str,
            receipt_id: str = None,
            timestamp: datetime = None
        ):
        self.amount = amount
        self.organization = organization
        self.address = address
        self.timestamp = datetime.now() if timestamp is None else timestamp
        self._receipt_id = id_generator("receipt") if receipt_id is None else self.clean_text(receipt_id, "Receipt ID")

    # A static method to return a stripped version of a string, or if it is not a str or is empty, raises Value Error
    @staticmethod
    def clean_text(value, label):
        if not isinstance(value, str):
            raise ValueError(f"{label} must be in String (text) format.")
        value = value.strip()
        if not value:
            raise ValueError(f"{label} cannot be empty.")
        return value

    # A static method to return the amount as a float, or raises Value Error if it is not a number greater than 0
    @staticmethod
    def clean_amount(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Amount must be a number.")
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Amount must be greater than 0.")
        return float(value)

    # A static method to return a datetime from a datetime or an ISO format string, or raises Value Error
    # A time zone is not allowed, because the program never saves one and naive and aware datetimes cannot be compared or sorted together
    @staticmethod
    def clean_timestamp(value):
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.strip())
            except ValueError:
                raise ValueError(f"Timestamp '{value}' is not a valid date and time.") from None
        if not isinstance(value, datetime):
            raise ValueError("Timestamp must be a datetime or a date-time string.")
        if value.tzinfo is not None:
            raise ValueError("Timestamp must not include a time zone.")
        return value

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = self.clean_timestamp(value)

    @property
    def amount(self) -> float:
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = self.clean_amount(value)

    @property
    def organization(self) -> str:
        return self._organization

    @organization.setter
    def organization(self, value):
        self._organization = self.clean_text(value, "Organization")

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value):
        self._address = self.clean_text(value, "Address")

    @property
    def receipt_id(self) -> str:
        return self._receipt_id

    # A method to return the receipt as a dictionary that can be saved as JSON (the timestamp becomes text)
    def convert_to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp.isoformat(),
            "amount": self.amount,
            "organization": self.organization,
            "address": self.address
        }

    # A class method to create a receipt from a dictionary, or raises Value Error if it is not a dict or has missing fields
    @classmethod
    def load_from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Receipt data must be a dictionary type")
        missing_fields = [field for field in cls.FIELDS if field not in data]
        if missing_fields:
            raise ValueError(f"Receipt is missing fields: {', '.join(missing_fields)}")
        return cls(
            amount=data["amount"],
            organization=data["organization"],
            address=data["address"],
            receipt_id=data["receipt_id"],
            timestamp=data["timestamp"]
        )

    # A method to add the receipt to a JSON file, or raises DataFileError if the file is not valid or cannot be written
    def save_to_json(self, filepath: str = JSON_PATH) -> None:
        data = read_json_list(filepath)
        data.append(self.convert_to_dict())
        write_json_list(filepath, data)

    def __str__(self) -> str:
        return (
            f"Receipt ID:   {self.receipt_id}\n"
            f"Organization: {self.organization}\n"
            f"Address:      {self.address}\n"
            f"Timestamp:    {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Amount:       P{self.amount:,.2f}"
        )

    def display_receipt(self) -> None:
        print(self)