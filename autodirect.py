import os
import shutil
import threading
import time

class AutoDirectHandler:
    def __init__(self):
        self.file_mappings = []
        self.paused = False
        self.running_thread = None

    def add_mapping(self, keyword, from_dir, to_dir):
        self.file_mappings.append((keyword, from_dir, to_dir))

    def remove_mapping(self, keyword, from_dir, to_dir):
        self.file_mappings = [(kw, frm, to) for kw, frm, to in self.file_mappings if
                              not (kw == keyword and frm == from_dir and to == to_dir)]

    def clear_mappings(self):
        self.file_mappings = []

    def auto_direct_files(self):
        while not self.paused:
            for keyword, from_directory, to_directory in self.file_mappings:
                if not os.path.exists(to_directory):
                    os.makedirs(to_directory)

                for filename in os.listdir(from_directory):
                    if self.paused:
                        return

                    if keyword in filename:
                        source_path = os.path.join(from_directory, filename)
                        destination_path = os.path.join(to_directory, filename)
                        shutil.move(source_path, destination_path)
            time.sleep(5)  # Add a sleep interval to avoid continuous high CPU usage

    def pause_operations(self):
        self.paused = True

    def resume_operations(self):
        self.paused = False
        if not self.running_thread or not self.running_thread.is_alive():
            self.running_thread = threading.Thread(target=self.auto_direct_files)
            self.running_thread.start()

    def start(self):
        self.resume_operations()

    def stop(self):
        self.pause_operations()
