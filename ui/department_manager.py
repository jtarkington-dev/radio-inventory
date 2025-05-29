import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection

class DepartmentManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Manage Departments")
        self.geometry("600x300")
        self.resizable(False, False)

        # === Table ===
        self.tree = ttk.Treeview(self, columns=("Dept ID", "Dept Name", "Contact"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", stretch=True)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === Buttons ===
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Add", width=12, command=self.add_department).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Edit", width=12, command=self.edit_selected).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete", width=12, command=self.delete_selected).grid(row=0, column=2, padx=5)

        self.load_departments()

    def load_departments(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, contact FROM departments ORDER BY id")
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, values=row)
        conn.close()

    def add_department(self):
        self._open_form()

    def edit_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Select a department to edit.")
            return
        values = self.tree.item(selected, "values")
        self._open_form(existing=values)

    def delete_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Select a department to delete.")
            return
        values = self.tree.item(selected, "values")
        confirm = messagebox.askyesno("Confirm Delete", f"Delete department '{values[1]}'?")
        if not confirm:
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM departments WHERE id = ?", (values[0],))
            conn.commit()
            self.load_departments()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete department:\n{e}")
        finally:
            conn.close()

    def _open_form(self, existing=None):
        form = tk.Toplevel(self)
        form.title("Edit Department" if existing else "Add Department")
        form.geometry("300x220")
        form.resizable(False, False)

        id_var = tk.StringVar(value=existing[0] if existing else "")
        name_var = tk.StringVar(value=existing[1] if existing else "")
        contact_var = tk.StringVar(value=existing[2] if existing else "")

        padding = {'padx': 10, 'pady': 5}

        tk.Label(form, text="Department ID:").pack(**padding)
        id_entry = tk.Entry(form, textvariable=id_var, state="readonly" if existing else "normal")
        id_entry.pack(fill='x', padx=10)

        tk.Label(form, text="Department Name:").pack(**padding)
        tk.Entry(form, textvariable=name_var).pack(fill='x', padx=10)

        tk.Label(form, text="Contact:").pack(**padding)
        tk.Entry(form, textvariable=contact_var).pack(fill='x', padx=10)

        def save():
            dept_id = id_var.get().strip()
            name = name_var.get().strip()
            contact = contact_var.get().strip()

            if not dept_id or not name:
                messagebox.showerror("Validation", "Department ID and Name are required.")
                return

            conn = get_connection()
            cursor = conn.cursor()
            try:
                if existing:
                    cursor.execute("""
                        UPDATE departments
                        SET name=?, contact=?
                        WHERE id=?
                    """, (name, contact, dept_id))
                else:
                    cursor.execute("""
                        INSERT INTO departments (id, name, contact)
                        VALUES (?, ?, ?)
                    """, (dept_id, name, contact))

                conn.commit()
                self.load_departments()
                form.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not save department:\n{e}")
            finally:
                conn.close()

        tk.Button(form, text="Save", command=save).pack(pady=10)
