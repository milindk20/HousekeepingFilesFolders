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

        title_label = ttk.Label(config_frame, text="Edit Housekeeping Config", style='Config.TLabel')
        title_label.pack(anchor='center', pady=(15, 5))

        self.text = scrolledtext.ScrolledText(
            config_frame, width=90, height=25, font=('Consolas', 11), background='#f8f8ff', foreground='#222', borderwidth=2, relief='groove', wrap='word'
        )
        self.text.pack(padx=20, pady=(0, 10), fill='both', expand=True)
        self.load_config()

        btn_frame = tk.Frame(config_frame, bg='#f5f6fa')
        btn_frame.pack(pady=10)

        save_btn = ttk.Button(btn_frame, text="💾 Save Config", command=self.save_config)
        save_btn.pack(side='left', padx=8)
        run_btn = ttk.Button(btn_frame, text="▶ Run Housekeeping", command=self.run_housekeeping)
        run_btn.pack(side='left', padx=8)
        test_btn = ttk.Button(btn_frame, text="🧪 Generate Test Files", command=self.run_test_script)
        test_btn.pack(side='left', padx=8)
        reload_btn = ttk.Button(btn_frame, text="⟳ Reload Config", command=self.load_config)
        reload_btn.pack(side='left', padx=8)

        # --- Logs Tab with sub-tabs ---
        logs_frame = tk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")

        self.logs_notebook = ttk.Notebook(logs_frame)
        self.logs_notebook.pack(fill='both', expand=True)

        # Housekeeping Logs Tab
        housekeeping_frame = tk.Frame(self.logs_notebook)
        self.logs_notebook.add(housekeeping_frame, text="Housekeeping Logs")

        # Dropdown for log files
        self.log_files = sorted(glob.glob(os.path.join(LOG_DIR, "housekeeping*.log")), reverse=True)
        self.selected_log = tk.StringVar()
        if self.log_files:
            self.selected_log.set(self.log_files[0])
        else:
            self.selected_log.set("")

        dropdown_frame = tk.Frame(housekeeping_frame)
        dropdown_frame.pack(anchor='w', pady=2)
        tk.Label(dropdown_frame, text="Select log file:").pack(side='left')
        self.log_dropdown = ttk.Combobox(dropdown_frame, values=[os.path.basename(f) for f in self.log_files], state="readonly", width=40)
        if self.log_files:
            self.log_dropdown.current(0)
        self.log_dropdown.pack(side='left', padx=5)
        self.log_dropdown.bind("<<ComboboxSelected>>", self.on_logfile_selected)

        self.housekeeping_logs_text = scrolledtext.ScrolledText(housekeeping_frame, width=90, height=25, state='disabled')
        self.housekeeping_logs_text.pack()
        tk.Button(housekeeping_frame, text="Reload Housekeeping Logs", command=self.reload_log_dropdown).pack(pady=5)

        # Error Logs Tab
        error_frame = tk.Frame(self.logs_notebook)
        self.logs_notebook.add(error_frame, text="Error Logs")

        # Dropdown for error log files
        self.error_log_files = sorted(glob.glob(os.path.join(LOG_DIR, "error*.log")), reverse=True)
        self.selected_error_log = tk.StringVar()
        if self.error_log_files:
            self.selected_error_log.set(self.error_log_files[0])
        else:
            self.selected_error_log.set("")

        error_dropdown_frame = tk.Frame(error_frame)
        error_dropdown_frame.pack(anchor='w', pady=2)
        tk.Label(error_dropdown_frame, text="Select error log file:").pack(side='left')
        self.error_log_dropdown = ttk.Combobox(
            error_dropdown_frame,
            values=[os.path.basename(f) for f in self.error_log_files],
            state="readonly",
            width=40
        )
        if self.error_log_files:
            self.error_log_dropdown.current(0)
        self.error_log_dropdown.pack(side='left', padx=5)
        self.error_log_dropdown.bind("<<ComboboxSelected>>", self.on_error_logfile_selected)

        self.error_logs_text = scrolledtext.ScrolledText(error_frame, width=90, height=25, state='disabled')
        self.error_logs_text.pack()
        tk.Button(error_frame, text="Reload Error Logs", command=self.reload_error_log_dropdown).pack(pady=5)

        # Initial load
        self.load_housekeeping_logs()
        self.load_error_logs()

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

    def reload_error_log_dropdown(self):
        self.error_log_files = sorted(glob.glob(os.path.join(LOG_DIR, "error*.log")), reverse=True)
        self.error_log_dropdown['values'] = [os.path.basename(f) for f in self.error_log_files]
        if self.error_log_files:
            self.error_log_dropdown.current(0)
            self.selected_error_log.set(self.error_log_files[0])
        else:
            self.error_log_dropdown.set("")
            self.selected_error_log.set("")
        self.load_error_logs()

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

    def on_error_logfile_selected(self, event=None):
        idx = self.error_log_dropdown.current()
        if idx >= 0 and idx < len(self.error_log_files):
            self.selected_error_log.set(self.error_log_files[idx])
            self.load_error_logs()
        else:
            self.selected_error_log.set("")
            self.error_logs_text.config(state='normal')
            self.error_logs_text.delete(1.0, tk.END)
            self.error_logs_text.insert(tk.END, "No error log files found.\n")
            self.error_logs_text.config(state='disabled')

    def load_config(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, json.dumps(data, indent=4))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def save_config(self):
        try:
            data = json.loads(self.text.get(1.0, tk.END))
            with open(CONFIG_PATH, "w") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Success", "Config saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def run_housekeeping(self):
        try:
            result = subprocess.run(
                ["python3", HOUSEKEEPING_SCRIPT],
                capture_output=True, text=True, check=True
            )
            messagebox.showinfo("Housekeeping Complete", result.stdout or "Housekeeping finished.")
            self.load_housekeeping_logs()
            self.load_error_logs()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Housekeeping failed:\n{e.stderr}")
            self.load_housekeeping_logs()
            self.load_error_logs()

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

    def load_error_logs(self):
        self.error_logs_text.config(state='normal')
        self.error_logs_text.delete(1.0, tk.END)
        error_log_file = self.selected_error_log.get() if self.selected_error_log.get() else (self.error_log_files[0] if self.error_log_files else None)
        if not error_log_file or not os.path.exists(error_log_file):
            self.error_logs_text.insert(tk.END, "No error log files found.\n")
        else:
            try:
                with open(error_log_file, "r") as f:
                    lines = f.readlines()
                reversed_lines = lines[::-1]
                self.error_logs_text.insert(tk.END, f"--- {os.path.basename(error_log_file)} ---\n")
                self.error_logs_text.insert(tk.END, ''.join(reversed_lines))
                self.error_logs_text.insert(tk.END, "\n")
            except Exception as e:
                self.error_logs_text.insert(tk.END, f"Could not read {error_log_file}: {e}\n\n")
        self.error_logs_text.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = HousekeepingGUI(root)
    root.mainloop()

