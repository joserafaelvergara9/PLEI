import datetime

class Receipt:
    def __init__(self, timestamp: datetime, amount: float, organization: str, address: str, image: str):
        self._timestamp = timestamp
        self._amount = amount
        self._organization = organization
        self._address = address
        self._image = image
        self._receipt_id = "placeholder"