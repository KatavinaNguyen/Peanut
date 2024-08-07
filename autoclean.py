from datetime import datetime, timedelta
import os
from hashlib import md5
import threading
import schedule
import time
from watchdog.events import FileSystemEventHandler
from database import DatabaseHandler

class AutoCleanHandler(FileSystemEventHandler):
    def __init__(self):
        self.user_home_directory = os.path.expanduser('~')
        self.selected_frequency = "quarter"
        self.previous_cleaning_time = datetime.now()
        self.next_cleaning_time = None
        self.clean_empty_folders_flag = False
        self.clean_unused_files_flag = False
        self.clean_duplicate_files_flag = False
        self.clean_recycling_bin_flag = False
        self.clean_browser_history_flag = False
        self.frequency = None
        self.paused = False
        self.db_handler = DatabaseHandler()

        # Load the settings from the database
        settings = self.db_handler.get_autoclean_settings()
        if settings:
            self.frequency = settings['frequency']
            self.next_cleaning_time = settings['next_clean_time']
            self.clean_empty_folders_flag = settings['empty_folders']
            self.clean_unused_files_flag = settings['unused_files']
            self.clean_duplicate_files_flag = settings['duplicate_files']
            self.clean_recycling_bin_flag = settings['recycling_bin']
            self.clean_browser_history_flag = settings['browser_history']

    def get_next_cleaning_time(self):
        if not self.next_cleaning_time:
            return "N/A"
        remaining_time = self.next_cleaning_time - datetime.now()
        days, seconds = remaining_time.days, remaining_time.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{days} days {hours} hours {minutes} minutes"

    def set_clean_frequency(self, frequency):
        self.frequency = frequency
        self.update_next_cleaning_time()
        self.db_handler.update_autoclean_settings(frequency=frequency, next_clean_time=self.next_cleaning_time)

    def update_next_cleaning_time(self):
        now = datetime.now()
        frequency_map = {
            'never': None,
            'day': timedelta(days=1),
            'week': timedelta(weeks=1),
            'month': timedelta(days=30),
            'quarter': timedelta(days=90),
            'year': timedelta(days=365)
        }
        if self.frequency in frequency_map:
            self.next_cleaning_time = now + frequency_map[self.frequency]
        else:
            self.next_cleaning_time = None

    def activate_selected_AC(self):
        if self.paused:
            return

        self.previous_cleaning_time = datetime.now()
        self.db_handler.update_autoclean_settings(previous_clean_time=self.previous_cleaning_time)
        self.update_next_cleaning_time()
        self.db_handler.update_autoclean_settings(next_clean_time=self.next_cleaning_time)

        directories = [
            os.path.join(self.user_home_directory, 'Documents'),
            os.path.join(self.user_home_directory, 'Downloads'),
            os.path.join(self.user_home_directory, 'Desktop'),
            os.path.join(self.user_home_directory, 'AppData', 'Local', 'Temp')
        ]

        if self.clean_empty_folders_flag:
            for directory in directories:
                self.clean_empty_folders(directory)

        if self.clean_unused_files_flag:
            for directory in directories:
                self.clean_unused_files(directory)

        if self.clean_duplicate_files_flag:
            for directory in directories:
                self.clean_duplicate_files(directory)

        if self.clean_recycling_bin_flag:
            self.clean_recycling_bin()

        if self.clean_browser_history_flag:
            self.clean_browser_history()

    def clean_empty_folders(self, root_directory):
        for root, dirs, _ in os.walk(root_directory):
            for d in dirs:
                folder_path = os.path.join(root, d)
                if not os.listdir(folder_path):
                    os.rmdir(folder_path)

    def clean_unused_files(self, root_directory):
        threshold = datetime.now() - timedelta(days=90)
        for root, _, files in os.walk(root_directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getatime(file_path) < threshold.timestamp():
                    os.remove(file_path)

    def clean_duplicate_files(self, root_directory):
        seen_files = {}
        for root, _, files in os.walk(root_directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_hash = self.hash_file(file_path)
                if file_hash in seen_files:
                    existing_file_path = seen_files[file_hash]
                    # Compare the last modified times
                    if os.path.getmtime(file_path) > os.path.getmtime(existing_file_path):
                        # The current file is newer, so delete the existing one
                        os.remove(existing_file_path)
                        seen_files[file_hash] = file_path
                    else:
                        # The existing file is newer, so delete the current one
                        os.remove(file_path)
                else:
                    seen_files[file_hash] = file_path

    @staticmethod
    def hash_file(file_path):
        hash_md5 = md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def clean_recycling_bin():
        try:
            os.system('powershell.exe Clear-RecycleBin -Force')
        except Exception:
            pass

    def clean_browser_history(self):
        browsers = {
            "Chrome": os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default", "History"),
            "Firefox": os.path.join(os.getenv("APPDATA"), "Mozilla", "Firefox", "Profiles"),
            "Edge": os.path.join(os.getenv("LOCALAPPDATA"), "Microsoft", "Windows", "WebCache", "WebCacheV01.dat")
        }

        for browser, path in browsers.items():
            if browser == "Firefox":
                if os.path.exists(path):
                    for profile in os.listdir(path):
                        profile_path = os.path.join(path, profile, "places.sqlite")
                        if os.path.exists(profile_path):
                            try:
                                os.remove(profile_path)
                            except Exception:
                                pass
            else:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

    def run_auto_cleaning(self):
        if not self.paused:
            self.activate_selected_AC()

    def schedule_cleaning(self, user_chosen_frequency):
        self.set_clean_frequency(user_chosen_frequency)

        def scheduler_thread():
            while True:
                if not self.paused:
                    schedule.run_pending()
                time.sleep(1)

        schedule.every().day.at("05:00").do(self.run_auto_cleaning)
        threading.Thread(target=scheduler_thread).start()

    def pause_operations(self):
        self.paused = True
        schedule.clear()  # Clear all scheduled tasks to pause them effectively

    def resume_operations(self):
        self.paused = False
        self.schedule_cleaning(self.frequency)  # Reschedule the tasks

    def clean_now(self):
        if not self.paused:
            self.activate_selected_AC()
