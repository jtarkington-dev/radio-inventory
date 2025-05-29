import tkinter as tk
from tkinter import ttk, messagebox
from ui.add_radio_form import AddRadioForm
from ui.department_manager import DepartmentManager
from ui.service_manager import ServiceManager
from ui.all_services_viewer import AllServicesViewer
from ui.reports_window import ReportsWindow
from database import init_db, get_connection, log_radio_change

init_db()

class RadioInventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Radios Inventory")
        self.root.bind("<Control-n>", lambda e: self.open_add_radio())
        self.root.bind("<Control-d>", lambda e: self.delete_selected_radio())
        self.root.bind("<Control-e>", lambda e: self.edit_selected_radio())
        self.root.bind("<Control-m>", lambda e: self.toggle_missing_status())
        self.root.bind("<Control-s>", lambda e: self.open_services())
        self.root.geometry("1200x700")

        self.tree = ttk.Treeview(root, columns=(
            "ID", "Serial", "Model", "Last Updated", "Dept ID", "Department", "Assigned", "Status", "Missing", "Notes"
        ), show="headings")

        column_widths = {
            "ID": 40,
            "Serial": 80,
            "Model": 100,
            "Last Updated": 110,
            "Dept ID": 60,
            "Department": 120,
            "Assigned": 100,
            "Status": 60,
            "Missing": 70,
            "Notes": 250
        }

        for col in self.tree["columns"]:
            # Add row color highlights
            self.tree.tag_configure("missing", background="#ffcccc")      # light red
            self.tree.tag_configure("in_service", background="#fff7cc")   # light yellow
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=column_widths.get(col, 100))

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Edit Radio", command=self.edit_selected_radio)
        self.menu.add_command(label="Delete Radio", command=self.delete_selected_radio)
        self.menu.add_command(label="Put Into Service", command=self.put_radio_in_service)
        self.tree.bind("<Button-3>", self.show_context_menu)

        search_frame = tk.Frame(root)
        search_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        # Search bar
        tk.Label(search_frame, text="Search:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT)
        search_entry.bind("<KeyRelease>", self.filter_rows)

        # Status filter
        tk.Label(search_frame, text="Status:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(10, 5))
        self.status_filter = tk.StringVar()
        status_combo = ttk.Combobox(search_frame, textvariable=self.status_filter, width=12, state="readonly")
        status_combo["values"] = ("", "Active", "In Service")
        status_combo.pack(side=tk.LEFT)
        status_combo.bind("<<ComboboxSelected>>", self.filter_rows)

        # Missing filter
        tk.Label(search_frame, text="Missing:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(10, 5))
        self.missing_filter = tk.StringVar()
        missing_combo = ttk.Combobox(search_frame, textvariable=self.missing_filter, width=10, state="readonly")
        missing_combo["values"] = ("", "Yes", "No")
        missing_combo.pack(side=tk.LEFT)
        missing_combo.bind("<<ComboboxSelected>>", self.filter_rows)

        # Department filter
        tk.Label(search_frame, text="Dept:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(10, 5))
        self.dept_filter = tk.StringVar()
        self.dept_combo = ttk.Combobox(search_frame, textvariable=self.dept_filter, width=20, state="readonly")
        self.dept_combo["values"] = []  # Populated in load_data()
        self.dept_combo.pack(side=tk.LEFT)
        self.dept_combo.bind("<<ComboboxSelected>>", self.filter_rows)

        toolbar = tk.Frame(root)
        toolbar.pack(fill=tk.X, padx=10, pady=(5, 10))

        tk.Button(toolbar, text="Add Radio", command=self.open_add_radio).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Departments", command=self.open_departments).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Services", command=self.open_services).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="All Services Viewer", command=self.open_all_services_viewer).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Reports", command=self.open_reports).pack(side=tk.LEFT, padx=5)

        # Keyboard shortcuts tooltip
        shortcut_tip = tk.Label(
            self.root,
            text="Shortcuts: Ctrl+N = Add | Ctrl+D = Delete | Ctrl+E = Edit | Ctrl+M = Toggle Missing | Ctrl+S = Services",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            fg="gray"
        )
        shortcut_tip.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 5))

        self.load_data()


    def load_data(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.serial, r.model, r.last_updated, r.department_id,
                   d.name, r.assigned_to, r.status, r.missing, r.notes
            FROM radios r
            LEFT JOIN departments d ON r.department_id = d.id
        """)
        rows = cursor.fetchall()
        # Populate department filter dropdown
        cursor.execute("SELECT DISTINCT name FROM departments ORDER BY name")
        dept_names = [row[0] for row in cursor.fetchall()]
        self.dept_combo["values"] = [""] + dept_names
        conn.close()

        self.tree.delete(*self.tree.get_children())
        self.all_rows = rows
        self.filter_rows()

    def filter_rows(self, event=None):
        search_term = self.search_var.get().lower()
        status_filter = self.status_filter.get().lower()
        missing_filter = self.missing_filter.get().lower()
        dept_filter = self.dept_filter.get().lower()

        self.tree.delete(*self.tree.get_children())

        for row in self.all_rows:
            match = True

            if search_term and not any(search_term in str(cell).lower() for cell in row):
                match = False

            if status_filter and status_filter != str(row[7]).lower():
                match = False

            if missing_filter and missing_filter != str(row[8]).lower():
                match = False

            if dept_filter and dept_filter != str(row[5]).lower():
                match = False

            if match:
                tag = ""
                if str(row[8]).strip().lower() == "yes":
                    tag = "missing"
                elif str(row[7]).strip().lower() == "in service":
                    tag = "in_service"

                self.tree.insert("", tk.END, values=row, tags=(tag,))

    def open_add_radio(self):
        form = AddRadioForm(self.root, self.load_data)
        self.root.wait_window(form)

    def edit_selected_radio(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a radio to edit.")
            return

        values = self.tree.item(selected[0], "values")
        radio_id = values[0]
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT radio_id FROM radios WHERE id = ?", (radio_id,))
        radio_id_val = cursor.fetchone()[0]
        conn.close()

        radio = {
            "id": values[0],
            "radio_id": radio_id_val,
            "serial": values[1],
            "model": values[2],
            "last_updated": values[3],
            "department_id": values[4],
            "department": values[5],
            "assigned_to": values[6],
            "status": values[7],
            "missing": values[8],
            "notes": values[9]
        }

        form = AddRadioForm(self.root, self.load_data, existing=radio)
        self.root.wait_window(form)

    def delete_selected_radio(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a radio to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this radio?")
        if not confirm:
            return

        values = self.tree.item(selected[0], "values")
        radio_id = values[0]
        serial = values[1]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM radios WHERE id = ?", (radio_id,))
        conn.commit()
        log_radio_change(cursor, radio_id, "DELETE", "ALL", serial, "")
        conn.close()
        self.load_data()

    def put_radio_in_service(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a radio.")
            return

        values = self.tree.item(selected[0], "values")
        radio_id = values[0]
        serial = values[1]

        confirm = messagebox.askyesno("Confirm", f"Mark radio {serial} as 'In Service' and log service entry?")
        if not confirm:
            return

        # Update status to In Service
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE radios SET status = 'In Service' WHERE id = ?", (radio_id,))
            conn.commit()
            log_radio_change(cursor, radio_id, "STATUS", "status", values[7], "In Service")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update status: {e}")
        finally:
            conn.close()

        # Open Service Manager to log service
        win = ServiceManager(self.root, radio_id, serial)
        self.root.wait_window(win)
        self.load_data()

    def take_out_of_service(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a radio.")
            return

        values = self.tree.item(selected[0], "values")
        radio_id = values[0]
        serial = values[1]
        old_status = values[7]

        confirm = messagebox.askyesno("Confirm", f"Mark radio {serial} as 'Active' after service?")
        if not confirm:
            return

        # Update status to Active
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE radios SET status = 'Active' WHERE id = ?", (radio_id,))
            conn.commit()
            log_radio_change(cursor, radio_id, "STATUS", "status", old_status, "Active")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update status: {e}")
        finally:
            conn.close()

        # Open service form to log service removal
        win = ServiceManager(self.root, radio_id, serial)
        self.root.wait_window(win)
        self.load_data()

    def toggle_missing_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a radio.")
            return

        values = self.tree.item(selected[0], "values")
        radio_id = values[0]
        serial = values[1]
        current_missing = values[8]

        new_missing = "No" if current_missing == "Yes" else "Yes"

        confirm = messagebox.askyesno("Confirm", f"Mark radio {serial} as {'Missing' if new_missing == 'Yes' else 'Found'}?")
        if not confirm:
            return

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE radios SET missing = ? WHERE id = ?", (new_missing, radio_id))
            conn.commit()
            log_radio_change(cursor, radio_id, "MISSING", "missing", current_missing, new_missing)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update missing status: {e}")
        finally:
            conn.close()
            self.load_data()

    def show_context_menu(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.menu.delete(0, tk.END)

            self.menu.add_command(label="Edit Radio", command=self.edit_selected_radio)
            self.menu.add_command(label="Delete Radio", command=self.delete_selected_radio)

            values = self.tree.item(row_id, "values")
            current_status = str(values[7]).lower()

            if current_status == "in service":
                self.menu.add_command(label="Take Out of Service", command=self.take_out_of_service)
            else:
                self.menu.add_command(label="Put Into Service", command=self.put_radio_in_service)

            # Add Missing toggle
            missing_status = str(values[8]).strip().lower()
            if missing_status == "yes":
                self.menu.add_command(label="Mark as Found", command=self.toggle_missing_status)
            else:
                self.menu.add_command(label="Mark as Missing", command=self.toggle_missing_status)

            self.menu.post(event.x_root, event.y_root)

    def open_departments(self):
        win = DepartmentManager(self.root)
        self.root.wait_window(win)
        self.load_data()

    def open_services(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a radio from the list first.")
            return

        item = self.tree.item(selected[0])
        values = item["values"]
        radio_id = values[0]
        serial = values[1]

        win = ServiceManager(self.root, radio_id, serial)
        self.root.wait_window(win)
        self.load_data()

    def open_all_services_viewer(self):
        win = AllServicesViewer(self.root)
        self.root.wait_window(win)

    def open_reports(self):
        win = ReportsWindow(self.root)
        self.root.wait_window(win)

if __name__ == '__main__':
    root = tk.Tk()
    app = RadioInventoryApp(root)
    root.mainloop()
