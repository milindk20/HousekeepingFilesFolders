import os
import json
import random
import string
from datetime import datetime, timedelta

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "create_filesfortesting.json")

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

    # Collect all extensions to create both matching and non-matching files
    all_extensions = set()
    for folder in config["folders"]:
        all_extensions.update(folder.get("extensions", []))
    # Add some extra extensions for negative testing
    extra_extensions = [".dat", ".csv", ".tmp"]
    all_extensions.update(extra_extensions)

    for folder in config["folders"]:
        folder_path = folder["path"]
        os.makedirs(folder_path, exist_ok=True)

        # Files with extensions to be tested (matching)
        for ext in folder.get("extensions", []):
            for i in range(2):
                file_path = os.path.join(folder_path, random_filename(ext))
                # Set mtime to now minus age_limit to test age-based logic
                age = timedelta(
                    days=folder["age_limit"]["days"],
                    hours=folder["age_limit"]["hours"],
                    minutes=folder["age_limit"]["minutes"] + i  # create files with slightly different ages
                )
                mtime = (datetime.now() - age).timestamp()
                create_file(file_path, random_content(), mtime=mtime)

        # Files with extensions NOT to be affected (non-matching)
        for ext in extra_extensions:
            for i in range(2):
                file_path = os.path.join(folder_path, random_filename(ext))
                create_file(file_path, random_content())

        # Files with no extension
        for i in range(2):
            file_path = os.path.join(folder_path, random_filename(""))
            create_file(file_path, random_content())

if __name__ == "__main__":
    main()