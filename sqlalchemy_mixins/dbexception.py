from sqlalchemy.exc import IntegrityError

class DBException(Exception):
    
    """
    custom exception class to handle sqlalchemy IntegrityError
    """

    def __init__(self, name: str, cause: str):
        self.name = name
        self.cause = cause.split(' ')[0]

    def __str__(self):
        return f"<name: {self.name}, cause: {self.cause}>"