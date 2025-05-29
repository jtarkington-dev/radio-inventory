import tkinter as tk
import datetime
from tkinter import ttk, messagebox
from database import get_connection, log_radio_change


class AddRadioForm(tk.Toplevel):
    def __init__(self, parent, refresh_callback, existing=None):
        super().__init__(parent)
        self.title("Edit Radio" if existing else "Add New Radio")
        self.geometry("320x550")
        self.resizable(False, False)

        self.refresh_callback = refresh_callback
        self.existing = existing
        self.department_map = {}

        # === Variables ===
        self.radio_id_var = tk.StringVar(value=existing["radio_id"] if existing else "")
        self.serial_var = tk.StringVar(value=existing["serial"] if existing else "")
        self.model_var = tk.StringVar(value=existing["model"] if existing else "")
        self.assigned_var = tk.StringVar(value=existing["assigned_to"] if existing else "")
        self.notes_var = tk.StringVar(value=existing["notes"] if existing else "")
        self.date_received_var = tk.StringVar(value=existing.get("date_received", "") if existing else "")
        self.date_issued_var = tk.StringVar(value=existing.get("date_issued", "") if existing else "")
        self.date_returned_var = tk.StringVar(value=existing.get("date_returned", "") if existing else "")
        self.department_var = tk.StringVar()

        padding = {'padx': 10, 'pady': 4}

        # === Form Layout ===
        tk.Label(self, text="Radio ID:").pack(**padding)
        tk.Entry(self, textvariable=self.radio_id_var).pack(fill="x", padx=15)

        tk.Label(self, text="Serial:").pack(**padding)
        tk.Entry(self, textvariable=self.serial_var).pack(fill="x", padx=15)

        tk.Label(self, text="Model:").pack(**padding)
        tk.Entry(self, textvariable=self.model_var).pack(fill="x", padx=15)

        tk.Label(self, text="Department:").pack(**padding)
        self.dept_combo = ttk.Combobox(self, textvariable=self.department_var, state="readonly")
        self.dept_combo.pack(fill="x", padx=15)
        self.load_departments()

        tk.Label(self, text="Assigned To:").pack(**padding)
        tk.Entry(self, textvariable=self.assigned_var).pack(fill="x", padx=15)

        tk.Label(self, text="Notes:").pack(**padding)
        tk.Entry(self, textvariable=self.notes_var).pack(fill="x", padx=15)

        tk.Label(self, text="Date Received (YYYY-MM-DD):").pack(**padding)
        tk.Entry(self, textvariable=self.date_received_var).pack(fill="x", padx=15)

        tk.Label(self, text="Date Issued (YYYY-MM-DD):").pack(**padding)
        tk.Entry(self, textvariable=self.date_issued_var).pack(fill="x", padx=15)

        tk.Label(self, text="Date Returned (YYYY-MM-DD):").pack(**padding)
        tk.Entry(self, textvariable=self.date_returned_var).pack(fill="x", padx=15)

        # === Save Button ===
        tk.Button(self, text="Save Radio", command=self.save_radio).pack(pady=15)

    def load_departments(self):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM departments ORDER BY name")
            departments = cursor.fetchall()

        dept_labels = [f"{id} - {name}" for id, name in departments]
        self.department_map = {label: id for label, id in zip(dept_labels, [id for id, _ in departments])}
        self.dept_combo["values"] = dept_labels

        if self.existing and "department_id" in self.existing:
            for label, dept_id in self.department_map.items():
                if str(dept_id) == str(self.existing["department_id"]):
                    self.department_var.set(label)
                    break

    def save_radio(self):
        radio_id = self.radio_id_var.get().strip()
        serial = self.serial_var.get().strip()

        if not serial or not radio_id:
            messagebox.showerror("Error", "Radio ID and Serial are required.")
            return

        model = self.model_var.get().strip()
        assigned = self.assigned_var.get().strip()
        notes = self.notes_var.get().strip()
        date_received = self.date_received_var.get().strip()
        date_issued = self.date_issued_var.get().strip()
        date_returned = self.date_returned_var.get().strip()
        department_label = self.department_var.get().strip()
        dept_id = self.department_map.get(department_label)

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                if self.existing:
                    last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db_id = self.existing["id"]

                    cursor.execute("""
                        SELECT radio_id, serial, model, assigned_to, notes, department_id, date_received, date_issued, date_returned
                        FROM radios WHERE id=?
                    """, (db_id,))
                    old = cursor.fetchone()

                    fields = ["radio_id", "serial", "model", "assigned_to", "notes", "department_id", "date_received", "date_issued", "date_returned"]
                    new_values = [radio_id, serial, model, assigned, notes, dept_id, date_received, date_issued, date_returned]

                    for idx, field in enumerate(fields):
                        old_val = old[idx]
                        new_val = new_values[idx]
                        if str(old_val) != str(new_val):
                            log_radio_change(cursor, db_id, "EDIT", field, old_val, new_val)

                    cursor.execute("""
                        UPDATE radios
                        SET radio_id=?, serial=?, model=?, assigned_to=?, notes=?, department_id=?, last_updated=?,
                            date_received=?, date_issued=?, date_returned=?
                        WHERE id=?
                    """, (radio_id, serial, model, assigned, notes, dept_id,
                        last_updated, date_received, date_issued, date_returned, db_id))

                    pass  # audit disabled

                else:
                    cursor.execute("""
                        INSERT INTO radios (radio_id, serial, model, assigned_to, notes, department_id, date_received, date_issued, date_returned)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (radio_id, serial, model, assigned, notes, dept_id, date_received, date_issued, date_returned))

                    new_id = cursor.lastrowid
                    log_radio_change(cursor, new_id, "ADD", "ALL", "", f"{radio_id}, {serial}, {model}, {assigned}, {notes}")
                    

            messagebox.showinfo("Success", "Radio saved successfully.")
            self.refresh_callback()
            self.destroy()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Could not save radio:\n{e}")


