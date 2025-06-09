from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import json
import os
import subprocess

CONFIG_PATH = "HousekeepingFiles.json"
HOUSEKEEPING_SCRIPT = "HousekeepingFiles_main.py"
TEST_SCRIPT = "create_filesfortesting.py"
LOG_DIR = "Logs"
LOG_FILE = os.path.join(LOG_DIR, "housekeeping.log")

app = Flask(__name__)
app.secret_key = "housekeeping_secret"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

def get_log_content():
    if not os.path.exists(LOG_FILE):
        return "No log file found."
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    # Show last 100 lines, newest first
    return "".join(lines[-100:][::-1])

@app.route("/")
def index():
    config = load_config()
    rules = config.get("rules", [])
    log_content = get_log_content()
    return render_template("index.html", rules=rules, log_content=log_content)

@app.route("/add", methods=["GET", "POST"])
def add_rule():
    if request.method == "POST":
        config = load_config()
        rules = config.get("rules", [])
        rule = {
            "folder": request.form["folder"],
            "action": request.form["action"],
            "enabled": request.form["enabled"],
            "extensions": request.form["extensions"],
            "days": int(request.form["days"]),
            "hours": int(request.form["hours"]),
            "minutes": int(request.form["minutes"])
        }
        rules.append(rule)
        config["rules"] = rules
        save_config(config)
        flash("Rule added successfully.", "msg")
        return redirect(url_for('index'))
    # Default values for new rule
    rule = {"folder": "", "action": "gzip", "enabled": "yes", "extensions": "", "days": 0, "hours": 0, "minutes": 0}
    return render_template("form.html", rule=rule, edit=False)

@app.route("/edit/<int:idx>", methods=["GET", "POST"])
def edit_rule(idx):
    config = load_config()
    rules = config.get("rules", [])
    if idx < 0 or idx >= len(rules):
        flash("Invalid rule index.", "error")
        return redirect(url_for('index'))
    if request.method == "POST":
        rules[idx] = {
            "folder": request.form["folder"],
            "action": request.form["action"],
            "enabled": request.form["enabled"],
            "extensions": request.form["extensions"],
            "days": int(request.form["days"]),
            "hours": int(request.form["hours"]),
            "minutes": int(request.form["minutes"])
        }
        config["rules"] = rules
        save_config(config)
        flash("Rule updated successfully.", "msg")
        return redirect(url_for('index'))
    rule = rules[idx]
    return render_template("form.html", rule=rule, edit=True)

@app.route("/delete/<int:idx>")
def delete_rule(idx):
    config = load_config()
    rules = config.get("rules", [])
    if idx < 0 or idx >= len(rules):
        flash("Invalid rule index.", "error")
    else:
        rules.pop(idx)
        config["rules"] = rules
        save_config(config)
        flash("Rule deleted.", "msg")
    return redirect(url_for('index'))

@app.route("/edit_config", methods=["GET", "POST"])
def edit_config():
    error = None
    if request.method == "POST":
        try:
            data = json.loads(request.form["config_json"])
            save_config(data)
            flash("Config saved.", "msg")
            return redirect(url_for('index'))
        except Exception as e:
            error = f"Invalid JSON: {e}"
    else:
        with open(CONFIG_PATH) as f:
            config_json = f.read()
        return render_template("edit_config.html", config_json=config_json, error=None)
    return render_template("edit_config.html", config_json=request.form["config_json"], error=error)

@app.route("/run_housekeeping", methods=["POST"])
def run_housekeeping():
    try:
        result = subprocess.run(["python3", HOUSEKEEPING_SCRIPT], capture_output=True, text=True, check=True)
        flash("Housekeeping completed.", "msg")
    except subprocess.CalledProcessError as e:
        flash(f"Housekeeping failed: {e.stderr}", "error")
    return redirect(url_for('index'))

@app.route("/generate_test_files", methods=["POST"])
def generate_test_files():
    try:
        result = subprocess.run(["python3", TEST_SCRIPT], capture_output=True, text=True, check=True)
        flash("Test files created.", "msg")
    except subprocess.CalledProcessError as e:
        flash(f"Test file creation failed: {e.stderr}", "error")
    return redirect(url_for('index'))

@app.route("/download_log")
def download_log():
    if os.path.exists(LOG_FILE):
        return send_file(LOG_FILE, as_attachment=True)
    else:
        flash("Log file not found.", "error")
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)