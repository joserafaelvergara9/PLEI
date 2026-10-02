import datetime

class Receipt:
    def __init__(self, timestamp: datetime, amount: float, organization: str, address: str, image: str):
        self._timestamp = timestamp
        self._amount = amount
        self._organization = organization
        self._address = address
        self._image = image # link to local image file
        self._receipt_id = "placeholder"

    @property
    def timestamp(self) -> datetime:
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
    
    def display_receipt():
        pass
    
    
