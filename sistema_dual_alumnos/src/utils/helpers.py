import re
from datetime import date, datetime

def validate_email(email: str) -> bool:
    """Validates an email address format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def calculate_age(born: date) -> int:
    """Calculates age from birthdate."""
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def format_currency(amount: float) -> str:
    """Formats a number as currency."""
    return "${:,.2f}".format(amount)
