import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection

class ServiceManager(tk.Toplevel):
    def __init__(self, parent, radio_id, serial):
        super().__init__(parent)
        self.title(f"Service History for {serial}")
        self.geometry("800x400")
        self.radio_id = radio_id

        # Table
        self.tree = ttk.Treeview(self, columns=(
            "ID", "Status", "Date Service", "LRC #", "Sent", "Repaired", "Amount", "Problem", "Notes"
        ), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Add New Service", command=self.add_service_form).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Close Selected Service", command=self.close_service).grid(row=0, column=1, padx=5)

        self.load_services()

    def load_services(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, status, date_service, lrc_service_num, date_sent,
                   date_repaired, amount, problem, notes
            FROM services
            WHERE radio_id=?
            ORDER BY date_service DESC
        """, (self.radio_id,))
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, values=row)
        conn.close()

    def add_service_form(self):
        form = tk.Toplevel(self)
        form.title("Add Service Entry")
        form.geometry("400x500")

        lrc_var = tk.StringVar()
        date_sent_var = tk.StringVar()
        problem_var = tk.StringVar()
        notes_var = tk.StringVar()
        amount_var = tk.StringVar()

        tk.Label(form, text="LRC Service #:").pack()
        tk.Entry(form, textvariable=lrc_var).pack()
        tk.Label(form, text="Date Sent (YYYY-MM-DD):").pack()
        tk.Entry(form, textvariable=date_sent_var).pack()
        tk.Label(form, text="Problem:").pack()
        tk.Entry(form, textvariable=problem_var).pack()
        tk.Label(form, text="Notes:").pack()
        tk.Entry(form, textvariable=notes_var).pack()
        tk.Label(form, text="Amount (if known):").pack()
        tk.Entry(form, textvariable=amount_var).pack()

        def save():
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO services (radio_id, status, date_service, lrc_service_num,
                                          date_sent, problem, notes, amount)
                    VALUES (?, 'open', DATE('now'), ?, ?, ?, ?, ?)
                """, (
                    self.radio_id,
                    lrc_var.get().strip(),
                    date_sent_var.get().strip(),
                    problem_var.get().strip(),
                    notes_var.get().strip(),
                    float(amount_var.get().strip() or 0)
                ))
                conn.commit()
                self.load_services()
                form.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not save service: {e}")
            finally:
                conn.close()

        tk.Button(form, text="Save Service", command=save).pack(pady=10)

    def close_service(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No selection", "Please select a service to close.")
            return

        values = self.tree.item(selected, "values")
        if values[1] == "closed":
            messagebox.showinfo("Already Closed", "This service is already closed.")
            return

        confirm = messagebox.askyesno("Confirm", "Mark this service as closed?")
        if not confirm:
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE services
                SET status='closed', date_repaired=DATE('now')
                WHERE id=?
            """, (values[0],))
            conn.commit()
            self.load_services()
        except Exception as e:
            messagebox.showerror("Error", f"Could not close service: {e}")
        finally:
            conn.close()
