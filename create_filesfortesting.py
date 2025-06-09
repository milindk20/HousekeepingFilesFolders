import os
import json
import random
import string
from datetime import datetime, timedelta

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "HousekeepingFiles.json")

def random_filename(ext):
    name = ''.join(random.choices(string.ascii_lowercase, k=8))
    return f"{name}{ext}"

def random_content(size=1024):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size))

def create_file(path, content, mtime=None):
    with open(path, "w") as f:
        f.write(content)
    if mtime:
        atime = mtime
        os.utime(path, (atime, mtime))

def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    # Collect all unique folders and their extensions from rules
    folder_rules = {}
    for rule in config.get("rules", []):
        folder = rule.get("folder")
        if not folder:
            continue
        if folder not in folder_rules:
            folder_rules[folder] = []
        folder_rules[folder].append(rule)

    # For negative testing, add some extra extensions
    extra_extensions = [".dat", ".csv", ".tmp"]

    for folder, rules in folder_rules.items():
        os.makedirs(folder, exist_ok=True)
        # Collect all extensions for this folder from all rules
        all_exts = set()
        for rule in rules:
            exts = rule.get("extensions", "")
            # Split by comma and strip spaces
            exts = [e.strip() for e in exts.split(",") if e.strip()]
            all_exts.update(exts)
        all_exts.update(extra_extensions)

        # Use the first rule for age-based file creation (for testing)
        rule = rules[0]
        # Files with extensions to be tested (matching)
        for ext in all_exts:
            for i in range(2):
                file_path = os.path.join(folder, random_filename(ext))
                # Set mtime to now minus age (use rule's days/hours/minutes)
                age = timedelta(
                    days=int(rule.get("days", 0)),
                    hours=int(rule.get("hours", 0)),
                    minutes=int(rule.get("minutes", 0)) + i  # create files with slightly different ages
                )
                mtime = (datetime.now() - age).timestamp()
                create_file(file_path, random_content(), mtime=mtime)

        # Files with no extension
        for i in range(2):
            file_path = os.path.join(folder, random_filename(""))
            create_file(file_path, random_content())

if __name__ == "__main__":
    main()