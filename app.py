import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import tkinter.font as tkFont
from datetime import date, datetime
from collections import Counter

# Import custom configuration and models
from config import (
    BG_COLOR, FG_COLOR, ACCENT_COLOR, HOVER_COLOR,
    ENTRY_BG, HEADER_BG, HEADER_FG, SEL_BG, SEL_FG,
    ROW_HOVER_COLOR, CATEGORIES
)
from storage import save_data, load_data
from models import Expense, InitialChange


class ExpenseTrackerApp:
    def __init__(self, root):
        """Initialize the Expense Tracker application."""
        self.root = root
        self.root.title("Expenses Tracker")
        self.root.state('zoomed')  # Maximize window
        self.root.configure(bg=BG_COLOR)

        self._configure_styles()     # Apply custom styles
        self._init_state()           # Initialize internal state
        self._build_ui()            # Build the user interface
        self._load_saved_data()     # Load previously saved expenses

        self.update_button_width()  # Adjust button sizes
        self.root.after(200, self.redraw_action_buttons)  # Redraw buttons after delay
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # Handle window close

    def _configure_styles(self):
        """Configure custom styles for widgets using ttk.Style."""
        style = ttk.Style(self.root)
        style.theme_use('clam')  # Use a clean theme

        # Define fonts
        self.normal_font = tkFont.Font(family="Segoe UI", size=10)
        self.bold_font   = tkFont.Font(family="Segoe UI", size=10, weight="bold")

        # Frame and Label styling
        style.configure("TFrame", background=BG_COLOR, borderwidth=0, relief='flat')
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=self.normal_font)

        # General Button styling
        style.configure("TButton",
                        background=ACCENT_COLOR,
                        foreground=HEADER_FG,
                        font=self.bold_font,
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor=ACCENT_COLOR)
        style.map("TButton",
                  background=[("active", HOVER_COLOR)],
                  foreground=[("disabled", "#bdc3c7")])

        # Summary Button styling
        style.configure("Summary.TButton",
                        background=ACCENT_COLOR,
                        foreground=HEADER_FG,
                        font=("Segoe UI", 11, "bold"),
                        borderwidth=0)
        style.map("Summary.TButton",
                  background=[("active", HOVER_COLOR)],
                  foreground=[("disabled", HEADER_FG)])

        # Action Button styling (smaller buttons)
        style.configure("Action.TButton",
                        background=ACCENT_COLOR,
                        foreground=HEADER_FG,
                        font=("Segoe UI", 8),
                        padding=(2, 0),
                        borderwidth=0)
        style.map("Action.TButton",
                  background=[("active", HOVER_COLOR)],
                  foreground=[("disabled", "#bdc3c7")])

        # Entry field styling (e.g., amount input)
        style.configure("TEntry",
                        foreground=FG_COLOR,
                        fieldbackground=ENTRY_BG,
                        background=ENTRY_BG,
                        bordercolor="#cccccc",
                        lightcolor="#cccccc",
                        darkcolor="#cccccc",
                        relief="flat")

        # Combobox styling (e.g., category/place dropdowns)
        style.configure("TCombobox",
                        foreground=FG_COLOR,
                        selectforeground='#000000',
                        selectbackground='#ffffff',
                        fieldbackground=ENTRY_BG,
                        background=ENTRY_BG,
                        bordercolor="#cccccc",
                        lightcolor="#cccccc",
                        darkcolor="#cccccc",
                        relief="flat")
        style.map("TCombobox",
                  fieldbackground=[("readonly", ENTRY_BG)],
                  background=[("readonly", ENTRY_BG)],
                  bordercolor=[("focus", "#cccccc")])

        # Treeview styling (expense table)
        style.configure("Treeview",
                        relief="flat",
                        padding=(0, 0),
                        rowheight=36,
                        background="#ffffff",
                        fieldbackground="#ffffff",
                        foreground=FG_COLOR,
                        font=self.normal_font)

        # Treeview header styling
        style.configure("Treeview.Heading",
                        background=HEADER_BG,
                        foreground=HEADER_FG,
                        font=self.bold_font,
                        padding=(5, 5),
                        relief="flat")
        style.map("Treeview.Heading",
                  background=[],
                  foreground=[])

        # Treeview row selection styling
        style.map("Treeview",
                  background=[("selected", "#d3d3d3")],
                  foreground=[("selected", "#000000")])

        # Date button styling (e.g., calendar picker)
        style.configure("Date.TButton",
                        background="#ffffff",
                        foreground="#000000",
                        padding=(4, 0),
                        font=self.normal_font)
        style.map("Date.TButton",
                  background=[("active", "#f4f4f4")],
                  foreground=[("active", "#000000")])

    def _init_state(self):
        """Initialize internal state variables for tracking expenses and UI behavior."""
        self.expenses        = {}              # Maps Treeview row ID to Expense object
        self.place_counter   = Counter()       # Tracks frequency of places used
        self.action_frames   = {}              # Maps row ID to action button frames
        self.selected_date   = date.today()    # Default selected date is today
        self.initial_changes = []              # List of InitialChange objects
        self.initial_amount  = 0.00            # Starting budget amount

        # UI-related state
        self.button_font      = tkFont.nametofont("TkDefaultFont")  # Default font for buttons
        self.initial_text_var = tk.StringVar()  # Text for initial amount button
        self.current_text_var = tk.StringVar()  # Text for current amount button
        self._hovered_row     = None            # Tracks hovered row in Treeview
        self._hover_inside_actions = False      # Tracks if mouse is inside action buttons

    def _build_ui(self):
        """Build and layout the main UI components."""
        # Top section: summary + input fields
        top = ttk.Frame(self.root)
        top.pack(pady=20)

        left = ttk.Frame(top)     # Left column for summary buttons
        left.grid(row=0, column=0, padx=20)

        inp = ttk.Frame(top)      # Right column for input fields
        inp.grid(row=0, column=1, padx=20)

        # Initial amount button
        self.initial_button = ttk.Button(
            left,
            textvariable=self.initial_text_var,
            style="Summary.TButton",
            command=self.change_initial_amount
        )
        self.initial_button.pack(ipadx=20, ipady=10)

        # Current amount display (disabled)
        self.current_amount_button = ttk.Button(
            left,
            textvariable=self.current_text_var,
            style="Summary.TButton",
            state="disabled"
        )
        self.current_amount_button.pack(ipadx=20, ipady=10, pady=(10, 0))

        # Date picker label + button
        ttk.Label(inp, text="Date:").grid(row=0, column=0, sticky="w", pady=4)
        date_button_border = tk.Frame(inp, bg="#cccccc", bd=1)
        date_button_border.grid(row=0, column=1, pady=4)

        self.date_button = ttk.Button(
            date_button_border,
            text=self.selected_date.strftime("%d.%m.%Y"),
            width=25,
            style="Date.TButton",
            command=self.toggle_calendar
        )
        self.date_button.pack()

        # Amount entry field
        ttk.Label(inp, text="Amount (€):").grid(row=1, column=0, sticky="w", pady=4)
        self.amount_entry = ttk.Entry(inp, width=31)
        self.amount_entry.grid(row=1, column=1, pady=4)

        # Category dropdown
        ttk.Label(inp, text="Category:").grid(row=2, column=0, sticky="w", pady=4)
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(
            inp,
            textvariable=self.category_var,
            values=CATEGORIES,
            state="readonly",
            width=28
        )
        self.category_dropdown.grid(row=2, column=1, pady=4)
        self.category_dropdown.current(0)

        # Place dropdown
        ttk.Label(inp, text="Place:").grid(row=3, column=0, sticky="w", pady=4)
        self.place_var = tk.StringVar()
        self.place_dropdown = ttk.Combobox(
            inp,
            textvariable=self.place_var,
            values=[],
            width=28
        )
        self.place_dropdown.grid(row=3, column=1, pady=4)

        # Add Expense button
        ttk.Button(
            inp,
            text="Add Expense",
            width=25,
            command=self.add_expense
        ).grid(row=4, column=1, pady=(10, 0))
        self.root.bind("<Return>", lambda e: self.add_expense())  # Enter key adds expense

        # Calendar popup for date selection
        self.calendar_popup = tk.Toplevel(self.root, bg=BG_COLOR)
        self.calendar_popup.withdraw()           # Hide initially
        self.calendar_popup.overrideredirect(True)  # Remove window decorations

        self.calendar = Calendar(
            self.calendar_popup,
            selectmode="day",
            year=self.selected_date.year,
            month=self.selected_date.month,
            day=self.selected_date.day,
            date_pattern="dd.mm.yyyy",
            background="#ffffff",
            foreground="#2c3e50",
            selectbackground="#3498db",
            selectforeground="#ffffff",
            headersbackground="#ecf0f1",
            headersforeground="#2c3e50",
            weekendbackground="#ffffff",
            weekendforeground="#95a5a6",
            othermonthbackground="#ffffff",
            othermonthforeground="#d0d0d0",
            bordercolor="#ffffff",
            font=("Segoe UI", 10),
            headersfont=("Segoe UI", 9, "bold"),
            normalfont=("Segoe UI", 10),
            weekendfont=("Segoe UI", 10, "italic")
        )
        self.calendar.pack(padx=10, pady=10)

        ttk.Button(
            self.calendar_popup,
            text="Select",
            command=self.select_date
        ).pack(pady=(0, 10))

        # Expense table (Treeview)
        cols = ("Date", "Amount", "Category", "Place", "Actions")
        self.tree = ttk.Treeview(
            self.root,
            columns=cols,
            show="headings",
            height=18,
            takefocus=0
        )
        for c in cols[:-1]:  # All except "Actions"
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150, anchor="center")

        self.tree.heading("Actions", text="Edit/Delete")
        self.tree.column("Actions", width=140, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=10, padx=20)

        # Row styling: zebra stripes + hover effect
        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background="#f2f2f2")
        self.tree.tag_configure("hover", background=ROW_HOVER_COLOR)

        # Treeview event bindings
        self.tree.bind("<Motion>", self._on_tree_motion)     # Hover effect
        self.tree.bind("<Leave>", self._on_tree_leave)       # Remove hover
        self.tree.bind("<Button-1>", self._on_tree_click)    # Click actions
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)  # Row selection

        # Redraw action buttons on layout changes
        for evt in ("<Configure>", "<Expose>", "<MouseWheel>"):
            self.tree.bind(evt, lambda e: self.redraw_action_buttons())

        # Deselect rows when clicking outside Treeview
        self.root.bind("<Button-1>", self._on_click_outside)

    def _load_saved_data(self):
        """Load saved expenses and initial amount from storage, then populate the UI."""
        # Retrieve saved data from storage
        initial_changes, last_init, loaded_expenses = load_data()
        self.initial_changes = initial_changes
        self.initial_amount  = last_init

        # Count frequency of each place for dropdown suggestions
        for exp in loaded_expenses:
            self.place_counter[exp.place] += 1

        # Update place dropdown with most common places
        self.place_dropdown['values'] = [
            p for p, _ in self.place_counter.most_common()
        ]

        # Populate Treeview with loaded expenses
        for exp in loaded_expenses:
            idx = len(self.tree.get_children())  # Current number of rows
            tag = "even" if idx % 2 == 0 else "odd"  # Zebra striping
            rid = self.tree.insert(
                "", "end",
                values=(
                    exp.date.strftime("%d.%m.%Y"),  # Format date
                    f"{exp.amount:.2f}",            # Format amount
                    exp.category,
                    exp.place,
                    ""                              # Placeholder for action buttons
                ),
                tags=(tag,)
            )
            self.expenses[rid] = exp  # Map row ID to Expense object
            self.add_action_buttons(rid)  # Add Edit/Delete buttons

        # Update initial amount display
        self.initial_text_var.set(f"Initial Amount: €{self.initial_amount:.2f}")
        self.refresh_current()  # Recalculate and display current balance

    def _restyle_rows(self):
        """Reapply zebra striping to Treeview rows after any change."""
        for i, rid in enumerate(self.tree.get_children()):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.item(rid, tags=(tag,))

    def _set_widget_bg(self, widget, color):
        """Set background color for a widget if it's a Frame."""
        if isinstance(widget, tk.Frame):
            widget.config(bg=color)

    def _set_action_frame_color(self, row_id, color):
        """
        Set the background color of the action frame and all its child widgets
        for a given Treeview row.

        Args:
            row_id (str): The Treeview row ID associated with the action frame.
            color (str): The background color to apply.
        """
        frame = self.action_frames.get(row_id)
        if frame:
            # Set background for the frame itself
            self._set_widget_bg(frame, color)

            # Set background for each child widget inside the frame
            for child in frame.winfo_children():
                self._set_widget_bg(child, color)

                # Set background for grandchildren (e.g., buttons inside nested frames)
                for grandchild in child.winfo_children():
                    self._set_widget_bg(grandchild, color)

    def _on_tree_motion(self, event):
        """
        Triggered when the mouse moves over the Treeview.
        Applies hover styling to the row under the cursor and resets the previous one.
        """
        row_id = self.tree.identify_row(event.y)  # Get row under mouse

        # If hovering over a new row
        if row_id != self._hovered_row:
            # Restore background of previously hovered row
            if self._hovered_row:
                idx = self.tree.index(self._hovered_row)
                orig = "even" if idx % 2 == 0 else "odd"  # Determine original zebra tag
                self.tree.item(self._hovered_row, tags=(orig,))

                # Restore background of action frame and its children
                if self._hovered_row in self.action_frames:
                    frame = self.action_frames[self._hovered_row]
                    color = "#f2f2f2" if orig == "even" else "#ffffff"
                    self._set_widget_bg(frame, color)
                    for child in frame.winfo_children():
                        self._set_widget_bg(child, color)
                        for grandchild in child.winfo_children():
                            self._set_widget_bg(grandchild, color)

            # Apply hover styling to the new row
            if row_id:
                self.tree.item(row_id, tags=("hover",))

                # Highlight action frame and its children
                if row_id in self.action_frames:
                    frame = self.action_frames[row_id]
                    self._set_widget_bg(frame, ROW_HOVER_COLOR)
                    for child in frame.winfo_children():
                        self._set_widget_bg(child, ROW_HOVER_COLOR)
                        for grandchild in child.winfo_children():
                            self._set_widget_bg(grandchild, ROW_HOVER_COLOR)

            # Reset hover state
            self._hover_inside_actions = False
            self._hovered_row = row_id

    def _on_tree_leave(self, event):
        """
        Triggered when the mouse leaves the Treeview area.
        Restores the original styling of the previously hovered row.
        """
        if self._hovered_row:
            idx = self.tree.index(self._hovered_row)
            orig = "even" if idx % 2 == 0 else "odd"  # Determine original zebra tag
            self.tree.item(self._hovered_row, tags=(orig,))
            self._hovered_row = None  # Clear hover state

    def _on_tree_click(self, event):
        """
        Triggered when the Treeview is clicked.
        If the click is outside any row, deselect all selected rows.
        """
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            self.tree.selection_remove(self.tree.selection())

    def center_window(self, win):
        """
        Center a given window on the screen.

        Args:
            win (tk.Toplevel or tk.Tk): The window to center.
        """
        win.update_idletasks()  # Ensure geometry info is up-to-date
        w, h   = win.winfo_width(), win.winfo_height()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x, y   = (sw - w) // 2, (sh - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")

    def update_button_width(self):
        """
        Adjust the width of the initial and current amount buttons
        based on the length of their displayed text.
        """
        # Measure pixel width of each button's text
        w1 = self.button_font.measure(self.initial_text_var.get())
        w2 = self.button_font.measure(self.current_text_var.get())

        # Estimate average character width using "0" as a baseline
        avg = self.button_font.measure("0")

        # Calculate button width in character units (+2 for padding)
        width = int(max(w1, w2) / avg) + 2

        # Apply calculated width to both buttons
        self.initial_button.config(width=width)
        self.current_amount_button.config(width=width)

    def change_initial_amount(self):
        """
        Opens a popup window allowing the user to change the initial budget amount.
        Validates input and updates state/UI accordingly.
        """
        # Create popup window near the initial amount button
        popup = tk.Toplevel(self.root, bg=BG_COLOR)
        popup.overrideredirect(True)  # Remove window decorations
        popup.grab_set()              # Make popup modal

        # Position popup directly below the initial amount button
        bx = self.initial_button.winfo_rootx()
        by = self.initial_button.winfo_rooty() + self.initial_button.winfo_height()
        popup.geometry(f"+{bx}+{by}")

        # Outer frame with border
        outer = tk.Frame(popup, bg="#cccccc", bd=2)
        outer.pack(padx=1, pady=1)

        # Inner content frame
        frm = ttk.Frame(outer, padding=20)
        frm.pack()

        # Label prompt
        ttk.Label(frm, text="Enter new initial amount (€):").pack(pady=(0, 10))

        # Entry field with current amount pre-filled
        var = tk.StringVar(value=f"{self.initial_amount:.2f}")
        ent = ttk.Entry(frm, textvariable=var, width=20)
        ent.pack(pady=(0, 10))
        ent.focus()

        # Save button logic
        def save():
            val = var.get().replace(",", ".").strip()
            try:
                amt = float(val)
                # Ensure max two decimal places
                if '.' in val and len(val.split('.')[-1]) > 2:
                    raise ValueError

                # Update internal state
                self.initial_amount = round(amt, 2)
                self.initial_changes.append(
                    InitialChange(date.today(), self.initial_amount)
                )

                # Update UI
                self.initial_text_var.set(f"Initial Amount: €{self.initial_amount:.2f}")
                self.refresh_current()
                popup.destroy()

            except:
                messagebox.showerror("Invalid", "Enter a valid amount.")

        # Save button
        ttk.Button(frm, text="Save", command=save).pack()

        # Allow pressing Enter to trigger save
        popup.bind("<Return>", lambda e: save())

    def refresh_current(self):
        """
        Recalculate and update the current remaining budget.
        Displays the difference between initial amount and total expenses.
        """
        total = sum(exp.amount for exp in self.expenses.values())  # Sum all expenses
        bal   = self.initial_amount - total                         # Calculate remaining balance

        # Update UI label
        self.current_text_var.set(f"Current Amount: €{bal:.2f}")

        # Adjust button width to fit new text
        self.update_button_width()

    def toggle_calendar(self):
        """
        Toggle visibility of the calendar popup.
        Positions it directly below the date button.
        """
        if self.calendar_popup.winfo_viewable():
            self.calendar_popup.withdraw()  # Hide calendar
        else:
            # Position calendar below the date button
            x = self.date_button.winfo_rootx()
            y = self.date_button.winfo_rooty() + self.date_button.winfo_height()
            self.calendar_popup.geometry(f"+{x}+{y}")
            self.calendar_popup.deiconify()  # Show calendar
            self.calendar_popup.lift()       # Bring to front

    def select_date(self):
        """
        Apply the selected date from the calendar to the date button.
        Updates internal state and hides the calendar popup.
        """
        ds = self.calendar.get_date()  # Get selected date string
        self.selected_date = datetime.strptime(ds, "%d.%m.%Y").date()  # Convert to date object

        # Update button label
        self.date_button.config(text=ds)

        # Hide calendar popup
        self.calendar_popup.withdraw()

    def add_expense(self):
        """
        Adds a new expense entry to the tracker.
        Validates input, updates internal data, and refreshes the UI.
        """
        # Get and sanitize input values
        amt_s = self.amount_entry.get().strip()
        cat   = self.category_var.get().strip()
        plc   = self.place_var.get().strip()

        # Validate amount
        try:
            amt = float(amt_s)
        except:
            return messagebox.showerror("Invalid", "Enter numeric amount.")

        # Validate category and place
        if not cat:
            return messagebox.showerror("Missing", "Select a category.")
        if not plc:
            return messagebox.showerror("Missing", "Enter a place.")

        # Update place frequency counter and dropdown suggestions
        self.place_counter[plc] += 1
        self.place_dropdown['values'] = [
            p for p, _ in self.place_counter.most_common()
        ]

        # Determine row styling tag (zebra striping)
        idx = len(self.tree.get_children())
        tag = "even" if idx % 2 == 0 else "odd"

        # Insert new row into Treeview
        rid = self.tree.insert(
            "", "end",
            values=(
                self.selected_date.strftime("%d.%m.%Y"),  # Format date
                f"{amt:.2f}",                             # Format amount
                cat,
                plc,
                ""                                        # Placeholder for action buttons
            ),
            tags=(tag,)
        )

        # Store expense object and add action buttons
        self.expenses[rid] = Expense(self.selected_date, amt, cat, plc)
        self.add_action_buttons(rid)

        # Refresh current balance display
        self.refresh_current()

        # ✅ Clear input fields for next entry
        self.amount_entry.delete(0, tk.END)
        self.place_var.set("")
        self.category_dropdown.current(0)  # Optional: reset category to first item

        # ✅ Reposition action buttons after Treeview update
        self.root.after(100, self.redraw_action_buttons)

    def add_action_buttons(self, row_id):
        """
        Adds Edit and Delete buttons to the 'Actions' column of a Treeview row.

        Args:
            row_id (str): The Treeview row ID to attach buttons to.
        """
        # Avoid duplicate button frames
        if row_id in self.action_frames:
            return

        self.tree.update_idletasks()  # Ensure layout is up-to-date

        # Get bounding box of the 'Actions' column for this row
        bbox = self.tree.bbox(row_id, column="#5")  # Column index as string
        if not bbox:
            return  # Row might not be visible yet

        x, y, w, h = bbox

        # Calculate absolute position relative to root window
        abs_x = self.tree.winfo_rootx() - self.root.winfo_rootx() + x
        abs_y = self.tree.winfo_rooty() - self.root.winfo_rooty() + y

        # Determine background color based on zebra striping
        tags = self.tree.item(row_id, "tags")
        if "even" in tags:
            bg_color = "#f2f2f2"
        elif "odd" in tags:
            bg_color = "#ffffff"
        else:
            bg_color = "#ffffff"

        # Create outer frame that overlays the cell
        frm = tk.Frame(self.root, bg=bg_color, bd=0, highlightthickness=0)
        frm.place(x=abs_x, y=abs_y, width=w, height=h)

        # Bind hover events for styling
        frm.bind("<Enter>", lambda e: self._on_action_hover_enter(row_id))
        frm.bind("<Leave>", lambda e: self._on_action_hover_leave(row_id))

        # Inner frame to center buttons within the cell
        inner = tk.Frame(frm, bg=bg_color)
        inner.place(relx=0.5, rely=0.5, anchor="center")  # Centered placement

        # Create Edit button
        ttk.Button(
            inner,
            text="Edit",
            style="Action.TButton",
            command=lambda: self.open_edit_popup(row_id),
            width=6
        ).pack(side="left", padx=(2, 2))

        # Create Delete button
        ttk.Button(
            inner,
            text="Delete",
            style="Action.TButton",
            command=lambda: self.delete_expense(row_id),
            width=6
        ).pack(side="left", padx=(2, 2))

        # Store reference to the frame for future updates
        self.action_frames[row_id] = frm

    def delete_expense(self, row_id):
        """
        Deletes an expense entry from the Treeview and internal data.

        Args:
            row_id (str): The Treeview row ID to delete.
        """
        # Remove and destroy the associated action button frame
        frame = self.action_frames.pop(row_id, None)
        if frame:
            frame.destroy()

        # Remove the row from the Treeview
        self.tree.delete(row_id)

        # Remove the expense from internal tracking
        self.expenses.pop(row_id, None)

        # Reapply zebra striping to remaining rows
        self._restyle_rows()

        # Refresh the current balance display
        self.refresh_current()

    def redraw_action_buttons(self):
        """
        Repositions all floating action button frames to align with their
        corresponding Treeview rows. Hides frames if the row is not visible.
        """
        for rid, frm in list(self.action_frames.items()):
            # Get bounding box of the 'Actions' column for the row
            bbox = self.tree.bbox(rid, column="#5")  # "#5" refers to the 5th column
            if bbox:
                x, y, w, h = bbox

                # Calculate absolute position relative to root window
                abs_x = self.tree.winfo_rootx() - self.root.winfo_rootx() + x
                abs_y = self.tree.winfo_rooty() - self.root.winfo_rooty() + y

                # Move the frame to match the cell's position
                frm.place(x=abs_x, y=abs_y, width=w, height=h)
            else:
                # Hide the frame if the row is not currently visible
                frm.place_forget()

    def open_edit_popup(self, row_id):
        """
        Opens a popup window to edit an existing expense entry.
        Allows modification of date, amount, category, and place.
        """
        # Create modal popup
        popup = tk.Toplevel(self.root, bg=BG_COLOR)
        popup.overrideredirect(True)  # Remove window decorations
        popup.grab_set()              # Make popup modal

        data = self.expenses[row_id]  # Get expense data for the selected row

        # Outer frame with border
        outer = tk.Frame(popup, bg="#cccccc", bd=2)
        outer.pack(padx=1, pady=1)

        # Inner content frame
        frm = ttk.Frame(outer, padding=15)
        frm.pack()

        # --- Date Selector ---
        ttk.Label(frm, text="Date:").grid(row=0, column=0, sticky="w", pady=4)
        date_var = tk.StringVar(value=data.date.strftime("%d.%m.%Y"))

        # Border frame for date button
        date_button_border = tk.Frame(frm, bg="#cccccc", bd=1)
        date_button_border.grid(row=0, column=1, pady=4)

        # Styled date button
        date_btn = ttk.Button(date_button_border, textvariable=date_var, width=25, style="Date.TButton")
        date_btn.pack()

        # Calendar popup for date selection
        edit_cal = tk.Toplevel(popup, bg=BG_COLOR)
        edit_cal.withdraw()
        edit_cal.overrideredirect(True)

        cal_w = Calendar(
            edit_cal,
            selectmode="day",
            year=data.date.year,
            month=data.date.month,
            day=data.date.day,
            date_pattern="dd.mm.yyyy",
            background="#ffffff",
            foreground="#2c3e50",
            selectbackground="#3498db",
            selectforeground="#ffffff",
            headersbackground="#ecf0f1",
            headersforeground="#2c3e50",
            weekendbackground="#ffffff",
            weekendforeground="#95a5a6",
            othermonthbackground="#ffffff",
            othermonthforeground="#d0d0d0",
            bordercolor="#ffffff",
            font=("Segoe UI", 10),
            headersfont=("Segoe UI", 9, "bold"),
            normalfont=("Segoe UI", 10),
            weekendfont=("Segoe UI", 10, "italic")
        )
        cal_w.pack(padx=10, pady=10)

        # Select button for calendar
        ttk.Button(
            edit_cal, text="Select",
            command=lambda: self._select_edit_date(cal_w, date_var, edit_cal)
        ).pack(pady=(0, 10))

        # Toggle calendar visibility
        def toggle_edit():
            if edit_cal.winfo_viewable():
                edit_cal.withdraw()
            else:
                x = date_btn.winfo_rootx()
                y = date_btn.winfo_rooty() + date_btn.winfo_height()
                edit_cal.geometry(f"+{x}+{y}")
                edit_cal.deiconify()
                edit_cal.lift()

        date_btn.config(command=toggle_edit)

        # --- Amount Field ---
        ttk.Label(frm, text="Amount (€):").grid(row=1, column=0, sticky="w", pady=4)
        amt_var = tk.StringVar(value=f"{data.amount:.2f}")
        ttk.Entry(frm, textvariable=amt_var, width=31).grid(row=1, column=1, pady=4)

        # --- Category Dropdown ---
        ttk.Label(frm, text="Category:").grid(row=2, column=0, sticky="w", pady=4)
        cat_var = tk.StringVar(value=data.category)
        cat_cb = ttk.Combobox(
            frm, textvariable=cat_var,
            values=CATEGORIES, state="readonly", width=28
        )
        cat_cb.grid(row=2, column=1, pady=4)

        # --- Place Dropdown ---
        ttk.Label(frm, text="Place:").grid(row=3, column=0, sticky="w", pady=4)
        plc_var = tk.StringVar(value=data.place)
        plc_cb = ttk.Combobox(
            frm, textvariable=plc_var,
            values=list(self.place_counter.keys()),
            width=28
        )
        plc_cb.grid(row=3, column=1, pady=4)

        # --- Save Button Logic ---
        def save_edit():
            try:
                new_date = datetime.strptime(date_var.get(), "%d.%m.%Y").date()
                new_amt  = float(amt_var.get())
            except:
                return messagebox.showerror("Invalid", "Check date/amount format.")

            # Update expense data
            data.date     = new_date
            data.amount   = new_amt
            data.category = cat_var.get().strip()
            data.place    = plc_var.get().strip()

            # Update Treeview row
            self.tree.item(
                row_id,
                values=(
                    data.date.strftime("%d.%m.%Y"),
                    f"{data.amount:.2f}",
                    data.category,
                    data.place,
                    ""
                )
            )

            # Refresh UI
            self.refresh_current()
            self.redraw_action_buttons()
            popup.destroy()

        # --- Save & Cancel Buttons ---
        ttk.Button(frm, text="Save", width=28, command=save_edit)\
            .grid(row=4, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(frm, text="Cancel", width=28, command=popup.destroy)\
            .grid(row=5, column=0, columnspan=2, pady=(5, 0))

        # Center the popup on screen
        self.center_window(popup)

    def _select_edit_date(self, calendar_widget, date_var, popup):
        """
        Updates the date variable with the selected date from the calendar widget
        and hides the calendar popup.

        Args:
            calendar_widget (Calendar): The calendar instance used for selection.
            date_var (tk.StringVar): The variable to update with the selected date.
            popup (tk.Toplevel): The calendar popup window to hide.
        """
        ds = calendar_widget.get_date()  # Get selected date as string
        date_var.set(ds)                 # Update the date display
        popup.withdraw()                 # Hide the calendar popup

    def _on_click_outside(self, event):
        """
        Deselects any selected Treeview rows if the user clicks outside the Treeview.

        Args:
            event (tk.Event): The mouse click event.
        """
        widget = event.widget

        # If the clicked widget is not the Treeview or one of its children
        if not str(widget).startswith(str(self.tree)):
            self.tree.selection_remove(self.tree.selection())  # Clear selection

    def _on_row_select(self, event):
        """
        Triggered when a Treeview row is selected.
        Updates the background color of action frames to reflect selection.
        """
        selected = self.tree.selection()  # Get selected row IDs

        for row_id in self.tree.get_children():
            tags = self.tree.item(row_id, "tags")
            is_selected = row_id in selected

            # Use highlight color if selected, otherwise zebra striping
            color = "#d3d3d3" if is_selected else ("#f2f2f2" if "even" in tags else "#ffffff")
            self._set_action_frame_color(row_id, color)

    def on_closing(self):
        """
        Saves current data and closes the application.
        """
        save_data(self.initial_changes, self.expenses)  # Persist data
        self.root.destroy()  # Close the window

    def _on_action_hover_enter(self, row_id):
        """
        Triggered when mouse enters an action button frame.
        Simulates hover effect for the associated Treeview row.
        """
        self._hover_inside_actions = True
        if self._hovered_row != row_id:
            self._on_tree_motion_fake(row_id)  # Apply hover styling manually

    def _on_action_hover_leave(self, row_id):
        """
        Triggered when mouse leaves an action button frame.
        Removes hover effect from the associated Treeview row.
        """
        self._hover_inside_actions = False
        self._on_tree_motion_fake(None)  # Clear hover styling

    def _on_tree_motion_fake(self, row_id):
        """
        Simulates the hover effect on a Treeview row and its action buttons.
        Used when hover needs to be triggered manually (e.g. from button events).

        Args:
            row_id (str or None): The row to apply hover styling to, or None to clear hover.
        """
        # Only proceed if the target row is different from the currently hovered one
        if row_id != self._hovered_row:
            # Restore styling of previously hovered row
            if self._hovered_row:
                idx = self.tree.index(self._hovered_row)
                orig = "even" if idx % 2 == 0 else "odd"
                self.tree.item(self._hovered_row, tags=(orig,))

                # Restore background of associated action frame
                if self._hovered_row in self.action_frames:
                    frame = self.action_frames[self._hovered_row]
                    color = "#f2f2f2" if orig == "even" else "#ffffff"
                    self._set_widget_bg(frame, color)
                    for child in frame.winfo_children():
                        self._set_widget_bg(child, color)
                        for grandchild in child.winfo_children():
                            self._set_widget_bg(grandchild, color)

            # Apply hover styling to the new row
            if row_id:
                self.tree.item(row_id, tags=("hover",))

                # Highlight associated action frame
                if row_id in self.action_frames:
                    frame = self.action_frames[row_id]
                    self._set_widget_bg(frame, ROW_HOVER_COLOR)
                    for child in frame.winfo_children():
                        self._set_widget_bg(child, ROW_HOVER_COLOR)
                        for grandchild in child.winfo_children():
                            self._set_widget_bg(grandchild, ROW_HOVER_COLOR)

            # Update hover tracking
            self._hovered_row = row_id
