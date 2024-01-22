class AdapterError(Exception):
    def __init__(self, message=None) -> None:
        """Initialize adapter error"""

        self.message = message or "Adapter error"
        super().__init__(self.message)
