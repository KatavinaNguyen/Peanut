import sqlite3
from datetime import datetime, timedelta

class DatabaseHandler:
    def __init__(self, db_file='peanut.db'):
        self.db_file = db_file
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        # SystemInfo table
        c.execute('''CREATE TABLE IF NOT EXISTS SystemInfo (
                        info_id INTEGER PRIMARY KEY,
                        os TEXT NOT NULL,
                        downloads_directory TEXT NOT NULL,
                        desktop_directory TEXT NOT NULL,
                        recycling_bin_directory TEXT NOT NULL,
                        main_browser TEXT NOT NULL
                     )''')

        # Actions table
        c.execute('''CREATE TABLE IF NOT EXISTS Actions (
                        action_id INTEGER PRIMARY KEY,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                        action_type TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        description TEXT NOT NULL,
                        status TEXT NOT NULL
                     )''')

        # UserSettings table
        c.execute('''CREATE TABLE IF NOT EXISTS UserSettings (
                        user_id INTEGER PRIMARY KEY,
                        status TEXT NOT NULL DEFAULT 'paused',  
                        ui_size INTEGER,
                        theme TEXT
                     )''')

        # AutoCleanSettings table
        c.execute('''CREATE TABLE IF NOT EXISTS AutoCleanSettings (
                        setting_id INTEGER PRIMARY KEY,
                        frequency TEXT NOT NULL,
                        previous_clean_time DATETIME,
                        next_clean_time DATETIME,
                        empty_folders BOOLEAN NOT NULL DEFAULT 0,
                        unused_files BOOLEAN NOT NULL DEFAULT 0,
                        duplicate_files BOOLEAN NOT NULL DEFAULT 0,
                        recycling_bin BOOLEAN NOT NULL DEFAULT 0,
                        browser_history BOOLEAN NOT NULL DEFAULT 0
                     )''')
        # Check if the table is empty and insert the initial row
        c.execute('SELECT COUNT(*) FROM AutoCleanSettings')
        if c.fetchone()[0] == 0:
            current_time = datetime.now().isoformat()
            next_clean_time = (datetime.now() + timedelta(days=30)).isoformat()
            c.execute('''INSERT INTO AutoCleanSettings (frequency, previous_clean_time, next_clean_time, empty_folders, 
                        unused_files, duplicate_files, recycling_bin, browser_history) 
                        VALUES (?, ?, ?, 0, 0, 0, 0, 0)''', ('never', current_time, next_clean_time))
        conn.commit()

        # AutoDirects table
        c.execute('''CREATE TABLE IF NOT EXISTS AutoDirects (
                        redirect_id INTEGER PRIMARY KEY,
                        keyword TEXT NOT NULL,
                        from_directory TEXT NOT NULL,
                        to_directory TEXT NOT NULL
                     )''')

        # Default AutoCleanSettings
        c.execute('''INSERT OR IGNORE INTO AutoCleanSettings (
                        setting_id, frequency, previous_clean_time, next_clean_time,
                        empty_folders, unused_files, duplicate_files,
                        recycling_bin, browser_history
                     ) VALUES (1, 'month', NULL, NULL, 0, 0, 0, 0, 0)''')

        # Default UserSettings
        c.execute('''INSERT OR IGNORE INTO UserSettings (
                        user_id, status, ui_size, theme
                     ) VALUES (1, 0, 100, 'system')''')

        # Custom Folders table
        c.execute('''CREATE TABLE IF NOT EXISTS AutoDirectCustomFolders (
                        id INTEGER PRIMARY KEY,
                        path TEXT NOT NULL,
                        name TEXT NOT NULL
                     )''')

        conn.commit()
        conn.close()

    def execute_query(self, query, params=()):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute(query, params)
            conn.commit()
            return c.fetchall()

    def save_status(self, status):
        self.execute_query('''UPDATE UserSettings SET status = ? WHERE user_id = 1''', (status,))

    def load_status(self):
        result = self.execute_query('''SELECT status FROM UserSettings WHERE user_id = 1''')
        return result[0][0] if result else 0  # Default to 0 (paused) if no status is found

    def log_action(self, action_type, file_path, description, success=True):
        status = "SUCCESS" if success else "FAILURE"
        self.execute_query('''INSERT INTO Actions (action_type, file_path, description, status)
                              VALUES (?, ?, ?, ?)''', (action_type, file_path, description, status))

    def get_latest_error(self):
        result = self.execute_query('''SELECT description FROM Actions WHERE status = 'FAILURE' ORDER BY timestamp DESC LIMIT 1''')
        return result[0][0] if result else None

    def get_user_settings(self):
        result = self.execute_query('''SELECT status, ui_size, theme FROM UserSettings WHERE user_id = 1''')
        if result:
            return {'status': result[0][0], 'ui_size': result[0][1], 'theme': result[0][2]}
        else:
            return None

    def update_user_settings(self, status=None, ui_size=None, theme=None):
        if status is not None:
            self.execute_query('''UPDATE UserSettings SET status = ? WHERE user_id = 1''', (status,))
        if ui_size is not None:
            self.execute_query('''UPDATE UserSettings SET ui_size = ? WHERE user_id = 1''', (ui_size,))
        if theme is not None:
            self.execute_query('''UPDATE UserSettings SET theme = ? WHERE user_id = 1''', (theme,))

    def update_system_info(self, os=None, downloads_directory=None, desktop_directory=None,
                           recycling_bin_directory=None, main_browser=None):
        # Check if there's already a record
        result = self.execute_query('''SELECT COUNT(*) FROM SystemInfo''')
        count = result[0][0]

        if count == 0:
            # Insert new record if none exists
            self.execute_query('''INSERT INTO SystemInfo (
                                     os, downloads_directory, desktop_directory, 
                                     recycling_bin_directory, main_browser
                                  ) VALUES (?, ?, ?, ?, ?)''',
                               (os, downloads_directory, desktop_directory, recycling_bin_directory, main_browser))
        else:
            # Update existing record
            self.execute_query('''UPDATE SystemInfo
                                  SET os = COALESCE(?, os), 
                                      downloads_directory = COALESCE(?, downloads_directory), 
                                      desktop_directory = COALESCE(?, desktop_directory), 
                                      recycling_bin_directory = COALESCE(?, recycling_bin_directory), 
                                      main_browser = COALESCE(?, main_browser)
                                  WHERE info_id = 1''',
                               (os, downloads_directory, desktop_directory, recycling_bin_directory, main_browser))

    def get_system_info(self):
        result = self.execute_query('''SELECT os, downloads_directory, desktop_directory, recycling_bin_directory, main_browser 
                                       FROM SystemInfo WHERE info_id = 1''')
        if result:
            return {'os': result[0][0], 'downloads_directory': result[0][1], 'desktop_directory': result[0][2],
                    'recycling_bin_directory': result[0][3], 'main_browser': result[0][4]}
        else:
            return None

    def get_autoclean_settings(self):
        result = self.execute_query('SELECT * FROM AutoCleanSettings WHERE setting_id=1')
        if result:
            row = result[0]
            return {
                'frequency': row[1],
                'previous_clean_time': datetime.fromisoformat(row[2]) if row[2] else None,
                'next_clean_time': datetime.fromisoformat(row[3]) if row[3] else None,
                'empty_folders': bool(row[4]),
                'unused_files': bool(row[5]),
                'duplicate_files': bool(row[6]),
                'recycling_bin': bool(row[7]),
                'browser_history': bool(row[8])
            }
        else:
            return None

    def update_autoclean_settings(self, frequency=None, empty_folders=None, unused_files=None,
                                  duplicate_files=None, recycling_bin=None, browser_history=None,
                                  previous_clean_time=None, next_clean_time=None):
        if frequency:
            self.execute_query('UPDATE AutoCleanSettings SET frequency = ? WHERE setting_id = 1', (frequency,))
        if empty_folders is not None:
            self.execute_query('UPDATE AutoCleanSettings SET empty_folders = ? WHERE setting_id = 1', (empty_folders,))
        if unused_files is not None:
            self.execute_query('UPDATE AutoCleanSettings SET unused_files = ? WHERE setting_id = 1', (unused_files,))
        if duplicate_files is not None:
            self.execute_query('UPDATE AutoCleanSettings SET duplicate_files = ? WHERE setting_id = 1', (duplicate_files,))
        if recycling_bin is not None:
            self.execute_query('UPDATE AutoCleanSettings SET recycling_bin = ? WHERE setting_id = 1', (recycling_bin,))
        if browser_history is not None:
            self.execute_query('UPDATE AutoCleanSettings SET browser_history = ? WHERE setting_id = 1', (browser_history,))
        if previous_clean_time is not None:
            self.execute_query('UPDATE AutoCleanSettings SET previous_clean_time = ? WHERE setting_id = 1', (previous_clean_time.isoformat(),))
        if next_clean_time is not None:
            self.execute_query('UPDATE AutoCleanSettings SET next_clean_time = ? WHERE setting_id = 1', (next_clean_time.isoformat(),))

    def add_redirect(self, keyword, from_directory, to_directory):
        self.execute_query('''INSERT INTO AutoDirects (keyword, from_directory, to_directory)
                              VALUES (?, ?, ?)''', (keyword, from_directory, to_directory))

    def delete_redirect(self, keyword, from_directory, to_directory):
        self.execute_query('''DELETE FROM AutoDirects WHERE keyword = ? AND from_directory = ? AND to_directory = ?''',
                           (keyword, from_directory, to_directory))

    def delete_all_redirects(self):
        self.execute_query('''DELETE FROM AutoDirects''')

    def get_redirects(self):
        result = self.execute_query('''SELECT keyword, from_directory, to_directory FROM AutoDirects''')
        return result if result else []

    def get_custom_folder_name(self, index):
        result = self.execute_query('''SELECT name FROM AutoDirectCustomFolders WHERE id = ?''', (index,))
        return result[0][0] if result else f"Custom folder {index}"

    def get_custom_folder_path(self, index):
        result = self.execute_query('''SELECT path FROM AutoDirectCustomFolders WHERE id = ?''', (index,))
        return result[0][0] if result else ""

    def update_custom_folder(self, index, path, name):
        self.execute_query('''INSERT OR REPLACE INTO AutoDirectCustomFolders (id, path, name)
                              VALUES (?, ?, ?)''', (index, path, name))

    def get_error_logs(self, limit=10):
        result = self.execute_query('''SELECT timestamp, action_type, description, status 
                                       FROM Actions 
                                       WHERE status = 'FAILURE' 
                                       ORDER BY timestamp DESC LIMIT ?''', (limit,))
        return result if result else []
