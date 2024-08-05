import sqlite3
from datetime import datetime, timedelta

class DatabaseHandler:
    def __init__(self, db_file='peanut.db'):
        self.db_file = db_file
        self.create_tables()

    def save_status(self, status):
        # Save the status to the database
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''UPDATE UserSettings SET status = ? WHERE user_id = 1''', (status,))
            conn.commit()

    def load_status(self):
        # Load the status from the database
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''SELECT status FROM UserSettings WHERE user_id = 1''')
            status = c.fetchone()
            return status[0] if status else 0  # Default to 0 (paused) if no status is found


    def create_tables(self):
        conn = sqlite3.connect('peanut.db')
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
                        description TEXT NOT NULL
                     )''')

        # UserSettings table
        c.execute('''CREATE TABLE IF NOT EXISTS UserSettings (
                        user_id INTEGER PRIMARY KEY,
                        status INTEGER NOT NULL DEFAULT 0,  -- 0: paused, 1: running
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

        conn.commit()
        conn.close()

    def delete_action(self, action_id):
        conn = sqlite3.connect('peanut.db')
        c = conn.cursor()
        c.execute('''DELETE FROM Actions WHERE action_id = ?''', (action_id,))
        conn.commit()
        conn.close()

    def add_redirect(self, keyword, from_directory, to_directory):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''INSERT INTO AutoDirects (keyword, from_directory, to_directory) 
                     VALUES (?, ?, ?)''', (keyword, from_directory, to_directory))
        conn.commit()
        conn.close()

    def delete_redirect(self, keyword, from_directory, to_directory):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''DELETE FROM AutoDirects WHERE keyword = ? AND from_directory = ? AND to_directory = ?''',
                  (keyword, from_directory, to_directory))
        conn.commit()
        conn.close()

    def delete_all_redirects(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''DELETE FROM AutoDirects''')
        conn.commit()
        conn.close()

    def get_redirects(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT keyword, from_directory, to_directory FROM AutoDirects''')
        rows = c.fetchall()
        conn.close()
        return rows


    ''' %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% EDIT BELOW %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% '''

    def check_status(self):
        conn = sqlite3.connect('peanut.db')
        c = conn.cursor()

        c.execute('''SELECT status FROM UserSettings WHERE user_id = 1''')
        status = c.fetchone()
        conn.close()
        return status[0] if status else None

    # TODO FUNCTION TO SET THE PROGRAM STATUS, ACTUAL IMPLEMENT
    def set_status(self, new_status):
        conn = sqlite3.connect('peanut.db')
        c = conn.cursor()

        c.execute('''UPDATE UserSettings SET status = ? WHERE user_id = 1''', (new_status,))
        conn.commit()
        conn.close()

        status_map = {0: "paused", 1: "running"}
        print(f"Program {status_map.get(new_status, 'unknown')}.")

    # TODO FUNCTION TO PRINT FAILED ACTIONS, PRINT FOR USER MESSAGE
    def print_failed_actions(self):
        conn = sqlite3.connect('peanut.db')
        c = conn.cursor()

        c.execute('''SELECT * FROM Actions WHERE action_type LIKE 'FAIL_%' ''')
        failed_actions = c.fetchall()

        if failed_actions:
            print("Failed Actions:")
            print("action_id | timestamp           | action_type  | file_path         | description")
            print("-------------------------------------------------------------------------------")
            for action in failed_actions:
                print("{:<10} | {:<20} | {:<12} | {:<17} | {:<30}".format(action[0], action[1], action[2], action[3],
                                                                          action[4]))
        else:
            print("No failed actions found.")

        conn.close()

    def log_action(self, action_type, file_path, description, success=True):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        if success:
            action_type = "SUCC_" + action_type
        else:
            action_type = "FAIL_" + action_type

        c.execute('''INSERT INTO Actions (action_type, file_path, description)
                     VALUES (?, ?, ?)''', (action_type, file_path, description))
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

    def update_system_info(self, os=None, downloads_directory=None, desktop_directory=None,
                           recycling_bin_directory=None, main_browser=None):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        # Check if there's already a record
        c.execute('''SELECT COUNT(*) FROM SystemInfo''')
        count = c.fetchone()[0]

        if count == 0:
            # Insert new record if none exists
            c.execute('''INSERT INTO SystemInfo (
                             os, downloads_directory, desktop_directory, 
                             recycling_bin_directory, main_browser
                          ) VALUES (?, ?, ?, ?, ?)''',
                      (os, downloads_directory, desktop_directory, recycling_bin_directory, main_browser))
        else:
            # Update existing record
            c.execute('''UPDATE SystemInfo
                          SET os = COALESCE(?, os), 
                              downloads_directory = COALESCE(?, downloads_directory), 
                              desktop_directory = COALESCE(?, desktop_directory), 
                              recycling_bin_directory = COALESCE(?, recycling_bin_directory), 
                              main_browser = COALESCE(?, main_browser)
                          WHERE info_id = 1''',
                      (os, downloads_directory, desktop_directory, recycling_bin_directory, main_browser))

        conn.commit()
        conn.close()

    def get_system_info(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''SELECT os, downloads_directory, desktop_directory, recycling_bin_directory, main_browser 
                      FROM SystemInfo WHERE info_id = 1''')
        system_info = c.fetchone()
        conn.close()
        if system_info:
            return {'os': system_info[0], 'downloads_directory': system_info[1], 'desktop_directory': system_info[2],
                    'recycling_bin_directory': system_info[3], 'main_browser': system_info[4]}
        else:
            return None

    def get_autoclean_settings(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM AutoCleanSettings WHERE setting_id=1')
            row = c.fetchone()
            if row:
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
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            if frequency:
                c.execute('UPDATE AutoCleanSettings SET frequency = ? WHERE setting_id = 1', (frequency,))
            if empty_folders is not None:
                c.execute('UPDATE AutoCleanSettings SET empty_folders = ? WHERE setting_id = 1', (empty_folders,))
            if unused_files is not None:
                c.execute('UPDATE AutoCleanSettings SET unused_files = ? WHERE setting_id = 1', (unused_files,))
            if duplicate_files is not None:
                c.execute('UPDATE AutoCleanSettings SET duplicate_files = ? WHERE setting_id = 1', (duplicate_files,))
            if recycling_bin is not None:
                c.execute('UPDATE AutoCleanSettings SET recycling_bin = ? WHERE setting_id = 1', (recycling_bin,))
            if browser_history is not None:
                c.execute('UPDATE AutoCleanSettings SET browser_history = ? WHERE setting_id = 1', (browser_history,))
            if previous_clean_time is not None:
                c.execute('UPDATE AutoCleanSettings SET previous_clean_time = ? WHERE setting_id = 1',
                          (previous_clean_time.isoformat(),))
            if next_clean_time is not None:
                c.execute('UPDATE AutoCleanSettings SET next_clean_time = ? WHERE setting_id = 1',
                          (next_clean_time.isoformat(),))
            conn.commit()

    def add_action(self, action_type, file_path, description, success=True):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        # Set status based on success or failure
        status = "SUCCESS" if success else "FAILURE"

        c.execute('''INSERT INTO Actions (action_type, file_path, description, status)
                     VALUES (?, ?, ?, ?)''', (action_type, file_path, description, status))
        conn.commit()
        conn.close()

    def get_latest_error(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()

        c.execute('''SELECT description FROM Actions WHERE status = 'FAILURE' ORDER BY timestamp DESC LIMIT 1''')
        error = c.fetchone()

        conn.close()
        return error[0] if error else None
