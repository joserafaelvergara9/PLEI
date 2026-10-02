import datetime
import json
import os
from general_purpose_functions.id_generator import id_generator

JSON_PATH = "income_expense_tracker/iet_json_files/receipt.json"

class Receipt:
    def __init__(self, timestamp: str, amount: float, organization: str, address: str, image: str):
        self._timestamp = timestamp
        self._amount = amount
        self._organization = organization
        self._address = address
        self._image = image # link to local image file
        self._receipt_id = id_generator("receipt")

    @property
    def timestamp(self) -> str:
        return self._timestamp
    
    @property
    def amount(self) -> float:
        return self._amount
    
    @property
    def organization(self) -> str:
        return self._organization
    
    @property
    def address(self) -> str:
        return self._address
    
    @property
    def image(self) -> str:
        return self._image
    
    @property
    def receipt_id(self) -> str:
        return self._receipt_id
    
    def convert_to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "amount": self.amount,
            "organization": self.organization,
            "address": self.address,
            "image": self.image
        }
    
    def save_to_json(self, filepath: str = JSON_PATH) -> None:
        if os.path.exists(filepath): # Load data if file exists
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                data = []
        else:
            data = []
        data.append(self.convert_to_dict()) # Append the entry
        os.makedirs(os.path.dirname(filepath), exist_ok=True) # Check if target directory exists again (?)
        with open(filepath, "w", encoding="utf-8") as file: # Write to json
            json.dump(data, file, indent=4)

    def __str__(self) -> str:
        return (
            f"Receipt ID:   {self.receipt_id}\n"
            f"Organization: {self.organization}\n"
            f"Address:      {self.address}\n"
            f"Timestamp:    {self.timestamp}\n"
            f"Amount:       P{self.amount:,.2f}\n"
            f"Image:        {self.image}"
        )

    def display_receipt(self) -> None:
        print(self)
        
