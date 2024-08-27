import os
import shutil
import schedule
from database import DatabaseHandler

class AutoDirectHandler:
    def __init__(self):
        self.db_handler = DatabaseHandler()
        self.redirects = self.db_handler.get_redirects()
        self.is_paused = False
        self.load_scheduled_redirects()
        self.file_mappings = []
        self.paused = False

    def add_mapping(self, keyword, from_dir, to_dir):
        self.file_mappings.append((keyword, from_dir, to_dir))

    def remove_mapping(self, keyword, from_dir, to_dir):
        self.file_mappings = [(kw, frm, to) for kw, frm, to in self.file_mappings if
                              not (kw == keyword and frm == from_dir and to == to_dir)]

    def clear_mappings(self):
        self.file_mappings = []

    def load_scheduled_redirects(self):
        schedule.clear()
        self.redirects = self.db_handler.get_redirects()
        for redirect in self.redirects:
            schedule.every(10).minutes.do(self.check_redirect, redirect)

    def check_redirect(self, redirect):
        if self.is_paused:
            return

        keyword, from_directory, to_directory = redirect[1], redirect[2], redirect[3]
        # if one of the files does not exist, skip this redirect and
        if not os.path.exists(from_directory) or not os.path.exists(to_directory):
            return

        # log action for later use in error handling and displaying error messages
        for root, _, files in os.walk(from_directory):
            for file in files:
                if keyword in file:
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(to_directory, file)
                    dst_path = self.resolve_conflicts(dst_path)
                    shutil.move(src_path, dst_path)
                    self.db_handler.log_action("redirect", src_path, dst_path)

    def resolve_conflicts(self, dst_path):
        if os.path.exists(dst_path):
            base, ext = os.path.splitext(dst_path)
            i = 1
            while os.path.exists(f"{base} ({i}){ext}"):
                i += 1
            dst_path = f"{base} ({i}){ext}"
        return dst_path

    def pause_operations(self):
        self.is_paused = True

    def resume_operations(self):
        self.is_paused = False
        self.load_scheduled_redirects()

    def update_redirects(self):
        self.redirects = self.db_handler.get_redirects()
        self.load_scheduled_redirects()
