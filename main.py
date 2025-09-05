import tkinter as tk
from app import ExpenseTrackerApp  # Import your main application class

# === Launch the Expense Tracker App ===
if __name__ == "__main__":
    root = tk.Tk()                     # Create the main window
    app = ExpenseTrackerApp(root)      # Initialize the app with the window
    root.mainloop()                    # Start the Tkinter event loop
