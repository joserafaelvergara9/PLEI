class Filter:
    def __init__(
            self, 
            transaction_subclass: str, 
            category: str, 
            mode_of_payment: str,
            amount: range,
        ):
        self._transaction_subclass = transaction_subclass
        self._category = category
        self._mode_of_payment = mode_of_payment
        self._amount = amount