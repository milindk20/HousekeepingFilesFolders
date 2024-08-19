import os
import gzip
import shutil
import json
import logging
from datetime import datetime, timedelta

# Setup logging
log_dir = "Logs"
housekeeping_log_file = os.path.join(log_dir, "housekeeping.log")

# Function to set up logging
def setup_logging():
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Check if log files are older than one day and rotate if needed
    for log_file in [housekeeping_log_file]:
        if os.path.exists(log_file):
            log_mod_time = os.path.getmtime(log_file)
            log_age = datetime.now() - datetime.fromtimestamp(log_mod_time)
            if log_age.days >= 1:
                old_log_file = log_file + f".{datetime.now().strftime('%Y%m%d')}"
                os.rename(log_file, old_log_file)
                if log_file.endswith(".log"):
                    with open(log_file, 'w'):  # Create new log file
                        pass

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(housekeeping_log_file),
                            logging.StreamHandler()
                        ])


def load_config(config_path):
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.error(f"Configuration file '{config_path}' not found.")
        raise
    except json.JSONDecodeError:
        logging.error(f"Configuration file '{config_path}' is not a valid JSON.")
        raise

def get_file_age(file_path):
    try:
        file_stat = os.stat(file_path)
        file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
        return file_age
    except Exception as e:
        logging.error(f"Unable to get the age of file '{file_path}'. Exception: {e}")
        raise

def gzip_file(file_path):
    try:
        with open(file_path, 'rb') as f_in:
            with gzip.open(file_path + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(file_path)
        logging.info(f"Gzipped: {file_path}")
    except Exception as e:
        logging.error(f"Unable to gzip file '{file_path}'. Exception: {e}")
        raise

def delete_file(file_path):
    try:
        os.remove(file_path)
        logging.info(f"Deleted: {file_path}")
    except Exception as e:
        logging.error(f"Unable to delete file '{file_path}'. Exception: {e}")
        raise

def perform_housekeeping(folder, extension, age_limit, action):
    try:
        age_threshold = timedelta(days=age_limit.get('days', 0),
                                  hours=age_limit.get('hours', 0),
                                  minutes=age_limit.get('minutes', 0))
        
        for root, dirs, files in os.walk(folder):
            for file_name in files:
                if extension and not file_name.endswith(extension):
                    continue
                file_path = os.path.join(root, file_name)
                file_age = get_file_age(file_path)
                if file_age > age_threshold:
                    if action == 'gzip':
                        gzip_file(file_path)
                    elif action == 'delete':
                        delete_file(file_path)
    except Exception as e:
        logging.error(f"An error occurred during housekeeping in folder '{folder}'. Exception: {e}")
        raise

def main():
    config_path = 'HousekeepingFilesFolders.json'  # Change to your config path
    try:
        config = load_config(config_path)
        for folder_config in config['folders']:
            perform_housekeeping(
                folder=folder_config['path'],
                extension=folder_config.get('extension', ''),
                age_limit=folder_config['age_limit'],
                action=folder_config['action']
            )
    except Exception as e:
        logging.critical(f"Failed to complete housekeeping. Exception: {e}")
        raise

if __name__ == "__main__":
    setup_logging()
    try:
        main()
    except Exception as e:
        logging.critical(f"Critical Error: The script encountered an unrecoverable error. Exception: {e}")
