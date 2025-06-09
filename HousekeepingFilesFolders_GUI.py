import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import json
import os
import glob

CONFIG_PATH = "HousekeepingFilesFolders.json"
HOUSEKEEPING_SCRIPT = "HousekeepingFilesFolders.py"
TEST_SCRIPT = os.path.join("Testing", "create_filesfortesting.py")
LOG_DIR = "Logs"
LOG_FILE = os.path.join(LOG_DIR, "housekeeping.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error.log")  # Assumes error log is named error.log

class HousekeepingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Housekeeping Files & Folders GUI")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook.Tab', font=('Segoe UI', 12, 'bold'))
        style.configure('TButton', font=('Segoe UI', 11))
        style.configure('TLabel', font=('Segoe UI', 11))
        style.configure('Config.TFrame', background='#f5f6fa')
        style.configure('Config.TLabel', background='#f5f6fa', font=('Segoe UI', 12, 'bold'), foreground='#273c75')

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        # --- Beautiful Housekeeping (Config) Tab ---
        config_frame = ttk.Frame(self.notebook, style='Config.TFrame')
        self.notebook.add(config_frame, text="Housekeeping")

        # Title at the top
        title_label = ttk.Label(config_frame, text="Edit Housekeeping Config", style='Config.TLabel')
        title_label.pack(anchor='nw', pady=(15, 5), padx=20)

        # Button row below title
        btn_frame = tk.Frame(config_frame, bg='#f5f6fa')
        btn_frame.pack(anchor='nw', padx=20, pady=(0, 10), fill='x')

        save_btn = ttk.Button(btn_frame, text="💾 Save Config", command=self.save_config)
        save_btn.pack(side='left', padx=(0, 8), ipadx=8, ipady=2)
        run_btn = ttk.Button(btn_frame, text="▶ Run Housekeeping", command=self.run_housekeeping)
        run_btn.pack(side='left', padx=(0, 8), ipadx=8, ipady=2)
        test_btn = ttk.Button(btn_frame, text="🧪 Generate Test Files", command=self.run_test_script)
        test_btn.pack(side='left', padx=(0, 8), ipadx=8, ipady=2)
        reload_btn = ttk.Button(btn_frame, text="⟳ Reload Config", command=self.load_config)
        reload_btn.pack(side='left', padx=(0, 8), ipadx=8, ipady=2)
        edit_file_btn = ttk.Button(btn_frame, text="📝 Edit Config File", command=self.open_config_in_editor)
        edit_file_btn.pack(side='left', padx=(0, 8), ipadx=8, ipady=2)

        # Table for config editing
        columns = ("folder", "action", "enabled", "extensions", "days", "hours", "minutes")
        self.tree = ttk.Treeview(config_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor='center')
        self.tree.pack(padx=20, pady=(0, 10), fill='both', expand=True)

        # Buttons for row operations
        row_btn_frame = tk.Frame(config_frame, bg='#f5f6fa')
        row_btn_frame.pack(anchor='nw', padx=20, pady=(0, 10))
        ttk.Button(row_btn_frame, text="Add Row", command=self.add_row).pack(side='left', padx=5)
        ttk.Button(row_btn_frame, text="Edit Row", command=self.edit_row).pack(side='left', padx=5)
        ttk.Button(row_btn_frame, text="Delete Row", command=self.delete_row).pack(side='left', padx=5)

        self.load_config()

        # --- Logs Tab (single tab, no error tab) ---
        logs_frame = tk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")

        # Dropdown for log files
        self.log_files = sorted(glob.glob(os.path.join(LOG_DIR, "housekeeping*.log")), reverse=True)
        self.selected_log = tk.StringVar()
        if self.log_files:
            self.selected_log.set(self.log_files[0])
        else:
            self.selected_log.set("")

        dropdown_frame = tk.Frame(logs_frame)
        dropdown_frame.pack(anchor='w', pady=2)
        tk.Label(dropdown_frame, text="Select log file:").pack(side='left')
        self.log_dropdown = ttk.Combobox(dropdown_frame, values=[os.path.basename(f) for f in self.log_files], state="readonly", width=40)
        if self.log_files:
            self.log_dropdown.current(0)
        self.log_dropdown.pack(side='left', padx=5)
        self.log_dropdown.bind("<<ComboboxSelected>>", self.on_logfile_selected)

        self.housekeeping_logs_text = scrolledtext.ScrolledText(logs_frame, width=90, height=25, state='disabled')
        self.housekeeping_logs_text.pack()
        tk.Button(logs_frame, text="Reload Housekeeping Logs", command=self.reload_log_dropdown).pack(pady=5)

        # Initial load
        self.load_housekeeping_logs()

    def reload_log_dropdown(self):
        self.log_files = sorted(glob.glob(os.path.join(LOG_DIR, "housekeeping*.log")), reverse=True)
        self.log_dropdown['values'] = [os.path.basename(f) for f in self.log_files]
        if self.log_files:
            self.log_dropdown.current(0)
            self.selected_log.set(self.log_files[0])
        else:
            self.log_dropdown.set("")
            self.selected_log.set("")
        self.load_housekeeping_logs()

    def on_logfile_selected(self, event=None):
        idx = self.log_dropdown.current()
        if idx >= 0 and idx < len(self.log_files):
            self.selected_log.set(self.log_files[idx])
            self.load_housekeeping_logs()
        else:
            self.selected_log.set("")
            self.housekeeping_logs_text.config(state='normal')
            self.housekeeping_logs_text.delete(1.0, tk.END)
            self.housekeeping_logs_text.insert(tk.END, "No housekeeping log files found.\n")
            self.housekeeping_logs_text.config(state='disabled')

    def load_config(self):
        # Load config and populate the table
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
            self.tree.delete(*self.tree.get_children())
            for rule in data.get("rules", []):
                self.tree.insert("", "end", values=(
                    rule.get("folder", ""),
                    rule.get("action", ""),
                    rule.get("enabled", ""),
                    rule.get("extensions", ""),
                    rule.get("days", ""),
                    rule.get("hours", ""),
                    rule.get("minutes", "")
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def save_config(self):
        # Save the table back to config
        try:
            rules = []
            for row in self.tree.get_children():
                values = self.tree.item(row)["values"]
                rules.append({
                    "folder": values[0],
                    "action": values[1],
                    "enabled": values[2],
                    "extensions": values[3],
                    "days": int(values[4]),
                    "hours": int(values[5]),
                    "minutes": int(values[6])
                })
            with open(CONFIG_PATH, "w") as f:
                json.dump({"rules": rules}, f, indent=4)
            messagebox.showinfo("Success", "Config saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def add_row(self):
        # Simple dialog for adding a row
        self.edit_row(new=True)

    def edit_row(self, new=False):
        # Edit selected row or add new
        import tkinter.simpledialog as sd
        columns = ("folder", "action", "enabled", "extensions", "days", "hours", "minutes")
        if not new:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("Select Row", "Please select a row to edit.")
                return
            values = self.tree.item(selected[0])["values"]
        else:
            values = ["", "", "", "", "0", "0", "0"]

        # Simple dialog for each field
        new_values = []
        for i, col in enumerate(columns):
            val = sd.askstring("Edit", f"Enter {col}:", initialvalue=values[i])
            if val is None:
                return  # Cancelled
            new_values.append(val)
        if new:
            self.tree.insert("", "end", values=new_values)
        else:
            self.tree.item(selected[0], values=new_values)

    def delete_row(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Row", "Please select a row to delete.")
            return
        self.tree.delete(selected[0])

    def run_housekeeping(self):
        try:
            result = subprocess.run(
                ["python3", HOUSEKEEPING_SCRIPT],
                capture_output=True, text=True, check=True
            )
            messagebox.showinfo("Housekeeping Complete", result.stdout or "Housekeeping finished.")
            self.load_housekeeping_logs()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Housekeeping failed:\n{e.stderr}")
            self.load_housekeeping_logs()

    def run_test_script(self):
        try:
            result = subprocess.run(
                ["python3", TEST_SCRIPT],
                capture_output=True, text=True, check=True
            )
            messagebox.showinfo("Test Files Created", result.stdout or "Test files created.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Test file creation failed:\n{e.stderr}")

    def load_housekeeping_logs(self):
        self.housekeeping_logs_text.config(state='normal')
        self.housekeeping_logs_text.delete(1.0, tk.END)
        log_file = self.selected_log.get() if self.selected_log.get() else (self.log_files[0] if self.log_files else None)
        if not log_file or not os.path.exists(log_file):
            self.housekeeping_logs_text.insert(tk.END, "No housekeeping log files found.\n")
        else:
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                reversed_lines = lines[::-1]
                self.housekeeping_logs_text.insert(tk.END, f"--- {os.path.basename(log_file)} ---\n")
                self.housekeeping_logs_text.insert(tk.END, ''.join(reversed_lines))
                self.housekeeping_logs_text.insert(tk.END, "\n")
            except Exception as e:
                self.housekeeping_logs_text.insert(tk.END, f"Could not read {log_file}: {e}\n\n")
        self.housekeeping_logs_text.config(state='disabled')

    def open_config_in_editor(self):
        # Open the config file in the user's default editor
        import subprocess
        import platform
        try:
            if platform.system() == "Linux":
                subprocess.Popen(["xdg-open", CONFIG_PATH])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", CONFIG_PATH])
            elif platform.system() == "Windows":
                os.startfile(CONFIG_PATH)
            else:
                messagebox.showerror("Error", "Unsupported OS for opening files.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open config file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HousekeepingGUI(root)
    root.mainloop()

