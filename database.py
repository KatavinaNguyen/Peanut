import sqlite3
import datetime

class DatabaseHandler:
    def __init__(self):
        self.db_file = 'peanut.db'
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS UserSettings (
                        user_id INTEGER PRIMARY KEY,
                        status TEXT,
                        ui_size INTEGER,
                        theme TEXT
                     )''')

        c.execute('''CREATE TABLE IF NOT EXISTS Redirects (
                        redirect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT,
                        from_directory TEXT,
                        to_directory TEXT
                     )''')

        c.execute('''CREATE TABLE IF NOT EXISTS AutoCleanSettings (
                        id INTEGER PRIMARY KEY,
                        frequency TEXT,
                        clean_empty_folders_flag BOOLEAN,
                        clean_unused_files_flag BOOLEAN,
                        clean_duplicate_files_flag BOOLEAN,
                        clean_recycling_bin_flag BOOLEAN,
                        clean_browser_history_flag BOOLEAN,
                        next_cleaning_time TEXT
                     )''')

        c.execute('''CREATE TABLE IF NOT EXISTS ErrorLogs (
                        error_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        description TEXT
                     )''')

        c.execute('''CREATE TABLE IF NOT EXISTS CustomFolders (
                        folder_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folder_path TEXT,
                        folder_name TEXT
                     )''')

        conn.commit()
        conn.close()

    # System Settings
    def load_status(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT status FROM UserSettings WHERE user_id = 1")
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def save_status(self, status):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO UserSettings (user_id, status) VALUES (1, ?)", (status,))
        conn.commit()
        conn.close()

    def get_user_settings(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT status, ui_size, theme FROM UserSettings WHERE user_id = 1''')
        settings = c.fetchone()
        conn.close()
        if settings:
            return {'status': settings[0], 'ui_size': settings[1], 'theme': settings[2]}
        else:
            return None

    def update_user_settings(self, status=None, ui_size=None, theme=None):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        if status is not None:
            c.execute('''UPDATE UserSettings SET status = ? WHERE user_id = 1''', (status,))
        if ui_size is not None:
            c.execute('''UPDATE UserSettings SET ui_size = ? WHERE user_id = 1''', (ui_size,))
        if theme is not None:
            c.execute('''UPDATE UserSettings SET theme = ? WHERE user_id = 1''', (theme,))
        conn.commit()
        conn.close()

    # AutoClean
    def get_clean_frequency(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT frequency FROM AutoCleanSettings WHERE id = 1''')
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def update_clean_frequency(self, frequency):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO AutoCleanSettings (id, frequency) VALUES (1, ?)''', (frequency,))
        conn.commit()
        conn.close()

    def get_clean_flags(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT clean_empty_folders_flag, clean_unused_files_flag, clean_duplicate_files_flag,
                            clean_recycling_bin_flag, clean_browser_history_flag
                     FROM AutoCleanSettings WHERE id = 1''')
        result = c.fetchone()
        conn.close()
        return {
            'clean_empty_folders_flag': result[0],
            'clean_unused_files_flag': result[1],
            'clean_duplicate_files_flag': result[2],
            'clean_recycling_bin_flag': result[3],
            'clean_browser_history_flag': result[4]
        } if result else None

    def update_clean_flags(self, autoclean_frequency, clean_empty_folders_flag, clean_unused_files_flag, clean_duplicate_files_flag,
                           clean_recycling_bin_flag, clean_browser_history_flag, next_cleaning_time):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO AutoCleanSettings (id, clean_empty_folders_flag, clean_unused_files_flag, 
                                              clean_duplicate_files_flag, clean_recycling_bin_flag, 
                                              clean_browser_history_flag, frequency, next_cleaning_time)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
        ''', (clean_empty_folders_flag, clean_unused_files_flag, clean_duplicate_files_flag, clean_recycling_bin_flag,
              clean_browser_history_flag, autoclean_frequency, next_cleaning_time))
        conn.commit()
        conn.close()

    def get_next_cleaning_time(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT next_cleaning_time FROM AutoCleanSettings WHERE id = 1''')
        result = c.fetchone()
        conn.close()
        return datetime.datetime.fromisoformat(result[0]) if result and result[0] else None

    def update_next_cleaning_time(self, next_cleaning_time):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO AutoCleanSettings (id, next_cleaning_time) VALUES (1, ?)''',
                  (next_cleaning_time.isoformat(),))
        conn.commit()
        conn.close()

    def get_autoclean_settings(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''
            SELECT frequency, clean_empty_folders_flag, clean_unused_files_flag, 
                   clean_duplicate_files_flag, clean_recycling_bin_flag, clean_browser_history_flag, 
                   next_cleaning_time FROM AutoCleanSettings WHERE id = 1
        ''')
        settings = c.fetchone()
        conn.close()
        if settings:
            return {
                'autoclean_frequency': settings[0],
                'clean_empty_folders_flag': settings[1],
                'clean_unused_files_flag': settings[2],
                'clean_duplicate_files_flag': settings[3],
                'clean_recycling_bin_flag': settings[4],
                'clean_browser_history_flag': settings[5],
                'next_cleaning_time': settings[6]
            }
        else:
            return None

    def add_redirect(self, keyword, from_directory, to_directory):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''INSERT INTO Redirects (keyword, from_directory, to_directory)
                     VALUES (?, ?, ?)''', (keyword, from_directory, to_directory))
        conn.commit()
        conn.close()

    def get_redirects(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT * FROM Redirects''')
        redirects = c.fetchall()
        conn.close()
        return redirects

    def delete_redirect(self, keyword, from_directory, to_directory):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''DELETE FROM Redirects WHERE keyword = ? AND from_directory = ? AND to_directory = ?''',
                  (keyword, from_directory, to_directory))
        conn.commit()
        conn.close()

    def clear_all_redirects(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''DELETE FROM Redirects''')
        conn.commit()
        conn.close()

    def get_custom_folder_path(self, folder_id):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('SELECT folder_path FROM CustomFolders WHERE folder_id = ?', (folder_id,))
        path = c.fetchone()
        conn.close()
        return path[0] if path else None

    def update_custom_folder(self, index, folder_path, folder_name):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO CustomFolders (folder_id, folder_path, folder_name) VALUES (?, ?, ?)''',
                  (index, folder_path, folder_name))
        conn.commit()
        conn.close()

    def get_custom_folder_name(self, index):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT folder_name FROM CustomFolders WHERE folder_id = ?''', (index,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else f"Custom folder {index}"

    # Error Handling
    def log_action(self, action_type, src_path, dst_path):  # TODO : add log_action for multisearch
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        c.execute('''INSERT INTO ActionLogs (action_type, src_path, dst_path, timestamp)
                     VALUES (?, ?, ?, ?)''', (action_type, src_path, dst_path, timestamp))
        conn.commit()
        conn.close()

    def log_error(self, description):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        c.execute('''INSERT INTO ErrorLogs (timestamp, description) VALUES (?, ?)''', (timestamp, description))
        conn.commit()
        conn.close()

    def get_latest_error(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT description FROM ErrorLogs ORDER BY error_id DESC LIMIT 1''')
        result = c.fetchone()
        conn.close()
        return {'description': result[0]} if result else None

    # TODO : wipe system/delete db for factory reset
