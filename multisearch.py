import os
import shutil
from database import DatabaseHandler

class MultiSearchHandler:
    def __init__(self):
        self.db_handler = DatabaseHandler()
        self.found_files = []
        self.valid_extensions = [
            ".txt", ".doc", ".docx", ".rtf", ".odt", ".pdf",  # Document formats
            ".xls", ".xlsx", ".csv", ".ods",  # Spreadsheet formats
            ".ppt", ".pptx", ".key",  # Presentation formats
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".tif", ".tiff",  # Image formats
            ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",  # Audio formats
            ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".mpeg", ".mpg",  # Video formats
            ".py", ".java", ".c", ".cpp", ".h", ".html", ".css", ".js", ".php", ".xml",  # Programming/scripting formats
            ".zip", ".rar", ".tar.gz", ".7z",  # Archive formats
            ".exe", ".app", ".bat", ".sh"]  # Executable formats

    def multi_search_for_files(self, keyword, directory):
        self.found_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if keyword in file:
                    self.found_files.append(os.path.join(root, file))
        return self.found_files

    def get_root_directories(self):
        if os.name == 'nt':  # Windows
            return [f"{chr(d)}:\\" for d in range(ord('A'), ord('Z') + 1) if os.path.exists(f"{chr(d)}:\\")]
        else:  # Unix-based (Linux, macOS)
            return ['/']

    def multi_delete_files(self, files):
        for file in files:
            try:
                os.remove(file)
                self.db_handler.log_action('Delete', file, 'File deleted successfully')
            except FileNotFoundError:
                self.db_handler.log_action('Delete', file, 'File not found', success=False)

    def multi_copy_files(self, files, new_folder):
        for file in files:
            try:
                os.makedirs(new_folder, exist_ok=True)
                shutil.copy(file, new_folder)
                self.db_handler.log_action('Copy', file, f'File copied to {new_folder}')
            except FileNotFoundError:
                self.db_handler.log_action('Copy', file, 'File not found', success=False)
            except shutil.Error as e:
                self.db_handler.log_action('Copy', file, str(e), success=False)

    def multi_rename_files(self, files, find_pattern, replace_pattern):
        try:
            for file in files:
                file_extension = os.path.splitext(file)[1]
                if file_extension.lower() in self.valid_extensions:
                    directory, filename = os.path.split(file)
                    filename_without_ext, ext = os.path.splitext(filename)

                    if find_pattern == '+':
                        new_filename = f"{replace_pattern}{filename_without_ext}{ext}"
                    elif find_pattern == '-':
                        new_filename = f"{filename_without_ext}{replace_pattern}{ext}"
                    else:
                        new_filename = filename.replace(find_pattern, replace_pattern)

                    new_path = os.path.join(directory, new_filename)

                    if os.path.exists(file):
                        os.rename(file, new_path)
                        self.db_handler.log_action('Rename', file, f'File renamed to {new_path}')
                else:
                    self.db_handler.log_action('Rename', file, f"Invalid file extension: {file_extension}. File skipped.", success=False)
        except Exception as e:
            self.db_handler.log_action('Rename', file, str(e), success=False)
