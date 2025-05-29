import tkinter as tk
from tkinter import ttk, messagebox
from database import get_connection

class AllServicesViewer(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("All Service Records")
        self.geometry("1000x500")

        # Filters
        filter_frame = tk.Frame(self)
        filter_frame.pack(pady=10)

        self.status_filter = tk.StringVar(value="all")
        ttk.Combobox(filter_frame, textvariable=self.status_filter, values=["all", "open", "closed"], width=10).grid(row=0, column=0)
        tk.Button(filter_frame, text="Apply Filter", command=self.load_services).grid(row=0, column=1, padx=5)

        # Table
        self.tree = ttk.Treeview(self, columns=(
            "ID", "Radio Serial", "Status", "Date", "LRC #", "Sent", "Repaired", "Amount", "Problem", "Notes"
        ), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.load_services()

    def load_services(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_connection()
        cursor = conn.cursor()

        base_query = """
            SELECT s.id, r.serial, s.status, s.date_service, s.lrc_service_num,
                   s.date_sent, s.date_repaired, s.amount, s.problem, s.notes
            FROM services s
            LEFT JOIN radios r ON s.radio_id = r.id
        """
        filters = []
        if self.status_filter.get() in ["open", "closed"]:
            base_query += " WHERE s.status = ?"
            filters.append(self.status_filter.get())

        base_query += " ORDER BY s.date_service DESC"

        cursor.execute(base_query, filters)
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, values=row)
        conn.close()
