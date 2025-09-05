from dataclasses import dataclass
from datetime import date

# === Data Model for Initial Balance Change ===
@dataclass
class InitialChange:
    date: date       # The date when the initial change occurred
    amount: float    # The amount of the initial change (e.g., starting balance)

# === Data Model for an Expense Entry ===
@dataclass
class Expense:
    date: date       # The date of the expense
    amount: float    # The amount spent
    category: str    # The category of the expense (e.g., Food, Transport)
    place: str       # The place or vendor where the expense occurred
