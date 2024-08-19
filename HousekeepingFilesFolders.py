import os
import gzip
import shutil
import json
import logging
from datetime import datetime, timedelta

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

# Log directory and file names
log_dir = "Logs"
housekeeping_log_file = os.path.join(log_dir, "housekeeping.log")

# Function to set up logging
def setup_logging():
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Check if log files are older than one day and rotate if needed
    if os.path.exists(housekeeping_log_file):
        log_mod_time = os.path.getmtime(housekeeping_log_file)
        log_age = datetime.now() - datetime.fromtimestamp(log_mod_time)
        if log_age.days >= 1:
            old_log_file = housekeeping_log_file + f".{datetime.now().strftime('%Y%m%d')}"
            os.rename(housekeeping_log_file, old_log_file)
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(housekeeping_log_file),
                            logging.StreamHandler()
                        ])

def get_file_age(file_path):
    file_stat = os.stat(file_path)
    file_age = datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
    return file_age

def gzip_file(file_path):
    gz_file_path = f"{file_path}.gz"
    try:
        with open(file_path, 'rb') as f_in:
            with gzip.open(gz_file_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(file_path)
        logging.info(f"Gzipped file: {file_path}")
    except Exception as e:
        logging.error(f"Error gzipping file {file_path}: {str(e)}")

def delete_file(file_path):
    try:
        os.remove(file_path)
        logging.info(f"Deleted file: {file_path}")
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {str(e)}")

def pre_gzip_delete(action,file_extension,file_path):
    if action == 'gzip':
        # Exclude .gz files from being compressed again
        if file_extension != '.gz':
            gzip_file(file_path)
    elif action == 'delete':
        # delete only of the file is zipped
        delete_file(file_path)

def perform_housekeeping(folder):
    path = folder['path']
    extensions = folder.get('extensions', [])
    age_limit = folder.get('age_limit', {})
    age_threshold = timedelta(days=age_limit.get('days', 0),
                              hours=age_limit.get('hours', 0),
                              minutes=age_limit.get('minutes', 0))
    action = folder.get('action', '')
    try:
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file)[-1]
                if len(extensions)<1:
                    if get_file_age(file_path) > age_threshold:
                        pre_gzip_delete(action,file_extension,file_path)
                elif file_extension in extensions:
                    if get_file_age(file_path) > age_threshold:
                        pre_gzip_delete(action,file_extension,file_path)

    except Exception as e:
        logging.error(f"Error processing folder {path}: {str(e)}")

def main():
    setup_logging()
    logging.info("Housekeeping process started.")
    config_path = 'HousekeepingFilesFolders.json'  # Change to your config path

    try:
        config = load_config(config_path)
        for folder_config in config['folders']:
            perform_housekeeping(folder_config)
    except Exception as e:
        logging.critical(f"Failed to complete housekeeping. Exception: {e}")
        raise

    logging.info("Housekeeping process completed.")

if __name__ == "__main__":
    main()
