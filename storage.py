import os
import csv
from datetime import datetime
from config import DATA_FILE
from models import InitialChange, Expense

# === Save Data to CSV ===
def save_data(
    initial_changes: list[InitialChange],
    expenses: dict[str, Expense]
) -> None:
    """
    Save initial changes and expenses to a CSV file.

    Args:
        initial_changes: List of InitialChange objects.
        expenses: Dictionary of Expense objects keyed by unique identifiers.
    """
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write header row
        writer.writerow([
            'record_type', 'date', 'amount',
            'category', 'place'
        ])

        # Write initial change records
        for ch in initial_changes:
            writer.writerow([
                'initial_change',
                ch.date.strftime("%d.%m.%Y"),
                f"{ch.amount:.2f}",
                '', ''  # Empty category and place for initial changes
            ])

        # Write expense records
        for exp in expenses.values():
            writer.writerow([
                'expense',
                exp.date.strftime("%d.%m.%Y"),
                f"{exp.amount:.2f}",
                exp.category,
                exp.place
            ])

# === Load Data from CSV ===
def load_data() -> tuple[list[InitialChange], float, list[Expense]]:
    """
    Load data from CSV file.

    Returns:
        A tuple containing:
        - List of InitialChange objects
        - Last initial amount (float)
        - List of Expense objects
    """
    initial_changes: list[InitialChange] = []
    expenses: list[Expense] = []
    last_initial = 0.0

    # Return empty data if file doesn't exist
    if not os.path.exists(DATA_FILE):
        return initial_changes, last_initial, expenses

    with open(DATA_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            rtype = row.get('record_type', '').strip()
            dstr  = row.get('date', '').strip()
            astr  = row.get('amount', '').strip()

            # Skip rows with missing essential fields
            if not (rtype and dstr and astr):
                continue

            try:
                dt = datetime.strptime(dstr, "%d.%m.%Y").date()
                amt = float(astr)
            except ValueError:
                continue  # Skip rows with invalid date or amount format

            if rtype == 'initial_change':
                initial_changes.append(InitialChange(dt, amt))
                last_initial = amt  # Update last initial amount

            elif rtype == 'expense':
                cat = row.get('category', '').strip()
                plc = row.get('place', '').strip()
                expenses.append(Expense(dt, amt, cat, plc))

    return initial_changes, last_initial, expenses
