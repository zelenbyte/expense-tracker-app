import os

# === File Paths ===
# Get the absolute path to the current script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the path to the CSV file storing expense data
DATA_FILE = os.path.join(BASE_DIR, "expenses.csv")

# === UI Color Palette ===
# Background and foreground colors
BG_COLOR     = "#ecf0f1"  # Light gray background
FG_COLOR     = "#2c3e50"  # Dark blue foreground text

# Accent and hover colors
ACCENT_COLOR = "#2980b9"  # Primary accent (buttons, highlights)
HOVER_COLOR  = "#1c6693"  # Hover effect color

# Entry and header styling
ENTRY_BG     = "#ffffff"  # Input field background
HEADER_BG    = ACCENT_COLOR  # Header background
HEADER_FG    = "#ffffff"     # Header text color

# Selection styling
SEL_BG       = ACCENT_COLOR  # Selected row background
SEL_FG       = "#ffffff"     # Selected row text color

# Row hover effect
ROW_HOVER_COLOR = "#d3d3d3"  # Light gray hover for table rows

# === Expense Categories ===
# Predefined categories for expense tracking
CATEGORIES = [
    "",             # Default empty option
    "Food",         # Groceries, dining out
    "Transport",    # Public transit, fuel, parking
    "Utilities",    # Electricity, water, internet
    "Entertainment",# Movies, subscriptions, outings
    "Other"         # Miscellaneous expenses
]
