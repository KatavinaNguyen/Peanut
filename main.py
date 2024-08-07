import datetime
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import schedule
from PIL import Image
import os
from autoclean import AutoCleanHandler
from autodirect import AutoDirectHandler
from multisearch import MultiSearchHandler
from database import DatabaseHandler


class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None

    def show_tip(self, text, wraplength=250):
        if self.tip_window or not text:
            return

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 65
        y += self.widget.winfo_rooty() + 45

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=text, justify=tk.LEFT, wraplength=wraplength,
                         bg="#ccfd7f", relief=tk.RIDGE, borderwidth=1,
                         font=("Arial", 10))
        label.pack(ipadx=1)

    def hide_tip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


def create_tooltip(widget, message):
    tool_tip = ToolTip(widget)

    def enter(event):
        tool_tip.show_tip(message)

    def leave(event):
        tool_tip.hide_tip()

    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


def browse_folder(entry):
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        entry.delete(0, "end")
        entry.insert(0, folder_selected)


class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_width = 790
        self.original_height = 460
        self.geometry(f"{self.original_width}x{self.original_height}")
        self.title("Peanut File Manager")
        self.iconbitmap("images/peanut.ico")
        self.is_paused = False
        self.tab_view = TabView(master=self)
        self.auto_clean_handler = AutoCleanHandler()
        self.auto_direct_handler = AutoCleanHandler()
        self.tab_view = TabView(master=self)
        self.update_next_cleaning_time_label()
        self.show_blank = True
        self.show_progress = True
        self.show_error = True
        self.load_saved_status()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # TODO : ugly
        '''User Feedback Frame'''
        self.user_feedback_frame = ctk.CTkFrame(self)
        self.user_feedback_frame.grid(row=2, column=1, columnspan=2, sticky="nsew", padx=20, pady=(0, 10))
        self.user_feedback_label = ctk.CTkLabel(self.user_feedback_frame, text="")
        self.user_feedback_label.grid(row=0, column=1, padx=(10, 20), sticky="w")
        self.user_feedback_frame.grid_columnconfigure(0, weight=1)
        self.user_feedback_frame.grid_columnconfigure(1, weight=0)

        if self.show_progress:
            self.user_feedback_frame = ctk.CTkFrame(self)
            self.user_feedback_frame.grid(row=2, column=1, columnspan=2, sticky="nsew", padx=20, pady=(0, 10))
            self.bouncing_progress_bar = ctk.CTkProgressBar(self.user_feedback_frame, mode="indeterminate",
                                                            indeterminate_speed=1)
            self.bouncing_progress_bar.grid(row=0, column=0, sticky="ew", padx=20)
            self.bouncing_progress_bar.start()
            self.progress_label = ctk.CTkLabel(self.user_feedback_frame, text="AutoClean in progress....",
                                               font=("Arial", 8))
            self.progress_label.grid(row=0, column=1, padx=(10, 20), sticky="w")
            self.user_feedback_frame.grid_columnconfigure(0, weight=1)
            self.user_feedback_frame.grid_columnconfigure(1, weight=0)

        if self.show_error:
            self.user_feedback_frame = ctk.CTkFrame(self)
            self.user_feedback_frame.grid(row=2, column=1, columnspan=2, sticky="nsew", padx=20, pady=(0, 10))
            self.user_feedback_label = ctk.CTkLabel(self.user_feedback_frame, text="An error has occurred...",
                                                    font=("Arial", 8))
            self.user_feedback_label.grid(row=0, column=1, padx=(10, 20), sticky="w")
            self.user_feedback_frame.grid_columnconfigure(0, weight=1)
            self.user_feedback_frame.grid_columnconfigure(1, weight=0)

    def load_saved_status(self):
        status = self.db_handler.load_status()
        if status == "running":
            self.start_operations()
        elif status == "paused":
            self.pause_operations()

    def update_next_cleaning_time_label(self):
        next_cleaning_time = self.auto_clean_handler.get_next_cleaning_time()
        self.tab_view.ac_next_cleaning_label.configure(text=f"Next Clean in\n\n{next_cleaning_time}")
        self.tab_view.ac_next_cleaning_label.after(600000,
                                                   self.update_next_cleaning_time_label)  # Update every 10 minutes

        # Sidebar Menu
        self.db_handler = DatabaseHandler()
        settings = self.db_handler.get_user_settings()
        if settings:
            self.user_status = settings['status']
            self.ui_size = settings['ui_size']
            self.theme = settings['theme']
        else:
            self.user_status = 0
            self.ui_size = 100
            self.theme = 'system'

        self.create_sidebar()

        self.tab_view = TabView(master=self)
        self.tab_view.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

        self.apply_settings()
        self.tab_view.load_redirects()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Peanut", font=("Helvetica", 20, "bold"),
                                       text_color="#3C4142")
        self.logo_label.grid(row=0, column=0, padx=18, pady=(20, 10))
        self.create_sidebar_buttons()
        self.create_sidebar_theme_scaling()

    def create_sidebar_buttons(self):
        self.start_pause_button = ctk.CTkButton(self.sidebar_frame, text="Start", fg_color="#2EB77C",
                                                command=self.toggle_start_pause)
        self.start_pause_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        create_tooltip(self.start_pause_button, "Click to start AutoClean and AutoDirect. Click again to pause.")

        self.help_button = ctk.CTkButton(self.sidebar_frame, text="Help", command=self.open_help_window)
        self.help_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        create_tooltip(self.help_button, "Open the FAQ page.")

    def toggle_start_pause(self):
        current_text = self.start_pause_button.cget("text")
        if current_text == "Start":
            self.start_operations()
        else:
            self.pause_operations()

    def start_operations(self):
        # Save settings and start AutoClean and AutoDirect
        self.user_status_event("save_and_start")
        self.auto_clean_handler.resume_operations()
        self.auto_direct_handler.resume_operations()
        # Update button text and color
        self.start_pause_button.configure(text="Pause", fg_color="gray")
        create_tooltip(self.start_pause_button, "Click to pause the program. Click again to resume.")
        # Save status to the database
        self.db_handler.save_status("running")

    def pause_operations(self):
        # Pause AutoClean and AutoDirect
        self.user_status_event("pause")
        self.auto_clean_handler.pause_operations()
        self.auto_direct_handler.pause_operations()
        # Update button text and color
        self.start_pause_button.configure(text="Start", fg_color="#2EB77C")
        create_tooltip(self.start_pause_button, "Click to start the program. Click again to pause.")
        # Save status to the database
        self.db_handler.save_status("paused")

    def user_status_event(self, status):
        if status == "save_and_start":
            # Save current settings and start AutoClean and AutoDirect
            self.load_application_status()
        elif status == "pause":
            # Pause AutoClean and AutoDirect
            self.auto_clean_handler.pause_operations()
            self.auto_direct_handler.pause_operations()

    def load_application_status(self):
        self.auto_clean_handler.resume_operations()
        self.auto_direct_handler.resume_operations()

    def create_sidebar_theme_scaling(self):
        self.theme_label_image = ctk.CTkImage(light_image=Image.open("images/13125625.png"),
                                              dark_image=Image.open("images/13125625.png"))
        self.theme_label = ctk.CTkLabel(self.sidebar_frame, image=self.theme_label_image, text="")
        self.theme_label.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.theme_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["System", "Light", "Dark"],
                                            command=self.change_theme_event)
        self.theme_menu.set(self.theme)
        self.theme_menu.grid(row=6, column=0, padx=20, pady=(10, 10), sticky="ew")

        self.scaling_label_image = ctk.CTkImage(light_image=Image.open("images/4606575.png"),
                                                dark_image=Image.open("images/4606575.png"))
        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, image=self.scaling_label_image, text="")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(5, 0), sticky="ew")
        self.scaling_menu_var = ctk.StringVar(value=f"{self.ui_size}%")
        self.scaling_menu = ctk.CTkOptionMenu(self.sidebar_frame,
                                              values=["50%", "75%", "100%", "125%", "150%", "175%", "200%"],
                                              variable=self.scaling_menu_var, command=self.change_scaling_event)
        self.scaling_menu.grid(row=8, column=0, padx=20, pady=(5, 20), sticky="ew")

    def apply_settings(self):
        ctk.set_appearance_mode(self.theme)
        self.change_scaling_event(f"{self.ui_size}%")

    def change_theme_event(self, new_appearance_mode: str):
        self.db_handler.update_user_settings(theme=new_appearance_mode)
        ctk.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        self.db_handler.update_user_settings(ui_size=int(new_scaling.replace("%", "")))
        ctk.set_widget_scaling(new_scaling_float)
        new_width = int(self.original_width * new_scaling_float)
        new_height = int(self.original_height * new_scaling_float)
        self.geometry(f"{new_width}x{new_height}")

    def open_help_window(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Frequently Asked Questions")
        help_window.geometry("600x500")

        help_scroll_frame = ctk.CTkScrollableFrame(help_window)
        help_scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # TODO : Finish Q & A
        q_and_a = [
            ("What does Peanut do?", "A system software that organizes and manages files..."),
            ("What is AutoClean?", "Toggle the types of files/data you want to clean and choose how often it does."),
            ("What is AutoDirect?",
             "Automatically redirect files to specified folders based on keywords.\n1. Open the AutoDirect Tab at the top of the screen\n2. Click ‘+’ to create a new redirect entry\n3. Enter a keyword to identify the files\n4. Click the ‘browse’ button to set the folder you want your files to move to\n5. Press ‘Save and Start’ on the left sidebar. Your redirect rule is now active!"),
            ("What is MultiSearch?",
             "MultiSearch allows you to find and edit files quickly and easily. Here's how to use it:\n1. Open the MultiSearch Tab\n2. Enter a directory (required) and a keyword: Click the ‘search’ button to see the results.\n3. Select files: Check the boxes next to the files you want to work with.\n4. Choose an action:\n\t- Delete: Remove the selected files.\n\t- Copy: Move the selected files into a new folder within your Downloads directory.\n\t- Rename:\n\t\t- Find & Replace:\n\t\t\t- Box 1: Enter the word(s) you want to find.\n\t\t\t- Box 2: Enter the word(s) you want to replace them with.\n\t\t- Convert File Formats:\n\t\t\t- Box 1: Enter the file extension you want to find.\n\t\t\t- Box 2: Enter the file extension you want to convert to.\n\t\t- Add Prefix/Suffix:\n\t\t\t- Box 1: Enter ‘+’ for prefix or ‘-’ for suffix.\n\t\t\t- Box 2: Enter the word you want to add to the filenames."),
            ("How can I recover a file that has been deleted?", ""),
            ("How can I temporarily suspend the program without having to uninstall?",
             "Press the “Pause” button on the left sidebar to pause Peanut and then press the “Save and Start” button when you’re ready to unpause."),
            ("Will Peanut slow down my computer?", "it can slow down, so to be safe use it at night... "),
            ("Will Peanut ever cost money?", "Peanut will never cost money nor require a subscription service.")
        ]

        for question, answer in q_and_a:
            q_label = ctk.CTkLabel(help_scroll_frame, text=question, font=("Arial", 14, "bold"), wraplength=550,
                                   anchor="w", justify="left", text_color="#7cb06d")
            q_label.pack(fill="x", padx=5, pady=(10, 0), anchor="w")
            a_label = ctk.CTkLabel(help_scroll_frame, text=answer, font=("Arial", 12), wraplength=550, anchor="w",
                                   justify="left")
            a_label.pack(fill="x", padx=5, pady=(0, 10), anchor="w")

        # TODO : logs
        see_logs_button = ctk.CTkButton(help_window, text="See Peanut's Logs")
        see_logs_button.pack(side="right", padx=10, pady=10)
        setup_info_button = ctk.CTkButton(help_window, text="Get Started: Setup System Info",
                                          command=self.open_setup_info_popup)
        setup_info_button.pack(side="right", pady=10)

    def open_setup_info_popup(self):
        setup_info_popup = ctk.CTkToplevel(self)
        setup_info_popup.title("Get Started: Setup System Info")
        setup_info_popup.geometry("400x300")
        setup_info_popup.resizable(False, False)
        setup_info_popup.grab_set()

        system_label = ctk.CTkLabel(setup_info_popup,
                                    text="Enter info about your PC to improve accuracy and performance.",
                                    text_color="#979da2")
        system_label.grid(row=0, column=0, padx=10, pady=5, columnspan=2, sticky="w")

        system_label = ctk.CTkLabel(setup_info_popup, text="Operating System")
        system_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        system_optionmenu = ctk.CTkOptionMenu(setup_info_popup,
                                              values=["Windows 10", "Windows 11", "Others unsupported"],
                                              font=("Arial", 12))
        system_optionmenu.grid(row=1, column=1, padx=10, pady=5)

        webbrowser_label = ctk.CTkLabel(setup_info_popup, text="Main Web Browser")
        webbrowser_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        webbrowser_optionmenu = ctk.CTkOptionMenu(setup_info_popup,
                                                  values=["Chrome", "Firefox", "Microsoft Edge", "Other"],
                                                  font=("Arial", 12))
        webbrowser_optionmenu.grid(row=2, column=1, padx=10, pady=5)

        favorite_folders_list = []
        folder_labels = ["Downloads", "Desktop", "Recycling Bin"]
        for i, label in enumerate(folder_labels):
            directory_label = ctk.CTkLabel(setup_info_popup, text=f"{label} Directory")
            directory_label.grid(row=i + 3, column=0, padx=10, pady=5, sticky="w")
            directory_entry = ctk.CTkEntry(setup_info_popup, placeholder_text=f"Enter your {label.lower()} directory",
                                           width=220)
            directory_entry.grid(row=i + 3, column=1, padx=10, pady=5)
            favorite_folders_list.append(directory_entry)

            browse_button_image = ctk.CTkImage(light_image=Image.open("images/3240447.png"),
                                               dark_image=Image.open("images/3240447.png"))
            browse_button = ctk.CTkButton(setup_info_popup, image=browse_button_image, text="", width=20,
                                          command=lambda entry=directory_entry: browse_folder(entry))
            browse_button.grid(row=i + 3, column=2, padx=10, pady=5, sticky="w")

        confirm_button = ctk.CTkButton(setup_info_popup, text="Confirm", width=380,
                                       command=lambda: self.save_system_info(setup_info_popup,
                                                                             system_optionmenu.get_selected_value(),
                                                                             webbrowser_optionmenu.get_selected_value(),
                                                                             *[entry.get() for entry in
                                                                               favorite_folders_list]))
        confirm_button.grid(row=len(folder_labels) + 3, column=0, padx=10, pady=20, columnspan=2)

    def save_system_info(self, setup_info_popup, os, main_browser, downloads_directory="", desktop_directory="",
                         recycling_bin_directory=""):
        if not all([os, main_browser]):
            return

        db_handler = DatabaseHandler()
        db_handler.update_system_info(os, downloads_directory, desktop_directory, recycling_bin_directory, main_browser)

        setup_info_popup.destroy()


class TabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.ac_next_cleaning_label = None
        self.next_cleaning_time = None
        self.db_handler = DatabaseHandler()
        self.auto_clean_handler = AutoCleanHandler()
        self.auto_direct_handler = AutoDirectHandler()
        self.multi_search_handler = MultiSearchHandler()
        self.add("AutoClean")
        self.add("AutoDirect")
        self.add("MultiSearch")

        self.create_autoclean_tab()
        self.create_autodirect_tab()
        self.create_multisearch_tab()

        self.load_autoclean_settings()

    def create_autoclean_tab(self):
        self.ac_frame = ctk.CTkFrame(master=self.tab("AutoClean"))
        self.ac_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=3)
        self.ac_next_cleaning_label = ctk.CTkLabel(self.ac_frame, text=f"Next Clean in\n\nN/A")
        self.ac_next_cleaning_label.pack(side="top", padx=15, pady=5)
        self.update_next_cleaning_time_label()

        self.clean_now_button = ctk.CTkButton(self.ac_frame, text="Clean Now", command=self.clean_now)
        self.clean_now_button.pack(side="top", padx=15, pady=15)

        self.ac_freq_label = ctk.CTkLabel(self.ac_frame, text="Clean every")
        self.ac_freq_label.pack(side="top", padx=5)
        self.ac_freq_menu = ctk.CTkOptionMenu(self.ac_frame,
                                              values=["never", "day", "week", "month", "quarter", "year"],
                                              command=self.set_clean_frequency)
        self.ac_freq_menu.pack(side="top", padx=5, pady=(5, 13))
        self.ac_folders_switch = ctk.CTkSwitch(self.ac_frame, text="Empty folders",
                                               command=self.toggle_clean_empty_folders)
        self.ac_folders_switch.pack(anchor="w", padx=188, pady=3)
        self.ac_unused_files_switch = ctk.CTkSwitch(self.ac_frame, text="Unused files",
                                                    command=self.toggle_clean_unused_files)
        self.ac_unused_files_switch.pack(anchor="w", padx=188, pady=3)
        self.ac_duplicate_files_switch = ctk.CTkSwitch(self.ac_frame, text="Duplicate files",
                                                       command=self.toggle_clean_duplicate_files)
        self.ac_duplicate_files_switch.pack(anchor="w", padx=188, pady=3)
        self.ac_recycling_switch = ctk.CTkSwitch(self.ac_frame, text="Recycling bin",
                                                 command=self.toggle_clean_recycling_bin)
        self.ac_recycling_switch.pack(anchor="w", padx=188, pady=3)
        self.ac_browser_history_switch = ctk.CTkSwitch(self.ac_frame, text="Browser history",
                                                       command=self.toggle_clean_browser_history)
        self.ac_browser_history_switch.pack(anchor="w", padx=188, pady=3)

    def create_autodirect_tab(self):
        self.redirect_entries = []
        self.ad_scroll_frame = ctk.CTkScrollableFrame(master=self.tab("AutoDirect"), height=280)
        self.ad_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.ad_inner_frame = ctk.CTkFrame(self.ad_scroll_frame)
        self.ad_inner_frame.pack(side="left", fill="both", expand=True)

        self.ad_button_frame = ctk.CTkFrame(master=self.tab("AutoDirect"))
        self.ad_button_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        self.ad_custom_folder_button = ctk.CTkButton(self.ad_button_frame, text="Set Custom Folders", width=140,
                                                     command=self.open_custom_folder_settings)
        self.ad_custom_folder_button.grid(row=0, column=0, padx=(5, 252), pady=(10, 5), sticky="w")

        self.ad_remove_all_button = ctk.CTkButton(self.ad_button_frame, text="Remove All", width=80,
                                                  command=self.remove_all_redirects)
        self.ad_remove_all_button.grid(row=0, column=1, padx=(5, 5), pady=(10, 5), sticky="e")

        self.ad_add_button_image = ctk.CTkImage(light_image=Image.open("images/plus_1104323.png"),
                                                dark_image=Image.open("images/plus_1104323.png"))
        self.ad_add_button = ctk.CTkButton(self.ad_button_frame, text="", image=self.ad_add_button_image, width=20,
                                           command=self.add_redirect)
        self.ad_add_button.grid(row=0, column=2, padx=(5, 10), pady=(10, 5), sticky="e")

    def create_multisearch_tab(self):
        self.ms_frame = ctk.CTkFrame(master=self.tab("MultiSearch"))
        self.ms_frame.grid(row=1, column=1, sticky="nsew", padx=0, pady=3)  # Removed side padding
        self.ms_directory_entry = ctk.CTkEntry(self.ms_frame, placeholder_text="folder", width=220)
        self.ms_directory_entry.pack(side="left", padx=5, pady=1)
        self.ms_browse_button_image = ctk.CTkImage(light_image=Image.open("images/3240447.png"),
                                                   dark_image=Image.open("images/3240447.png"))
        self.ad_browse_button = ctk.CTkButton(self.ms_frame, image=self.ms_browse_button_image, text="", width=20,
                                              command=lambda: browse_folder(self.ms_directory_entry))
        self.ad_browse_button.pack(side="left", padx=(2, 10))
        self.ms_keyword_entry = ctk.CTkEntry(self.ms_frame, placeholder_text="search  (or ' . ' for all files)",
                                             width=220)
        self.ms_keyword_entry.pack(side="left", padx=5, pady=1)
        self.ms_search_button_image = ctk.CTkImage(light_image=Image.open("images/7270638.png"),
                                                   dark_image=Image.open("images/7270638.png"))
        self.ms_search_button = ctk.CTkButton(self.ms_frame, text="", image=self.ms_search_button_image,
                                              command=self.perform_search, width=20)
        self.ms_search_button.pack(side="left", padx=3)

        self.search_results_frame = ctk.CTkScrollableFrame(master=self.tab("MultiSearch"), height=260)
        self.search_results_frame.grid(row=3, column=1, sticky="nsew", padx=0, pady=1)  # Removed side padding
        self.search_results_frame.grid_rowconfigure(0, weight=1)
        self.search_results_frame.grid_columnconfigure(0, weight=1)

        self.ms_button_frame = ctk.CTkFrame(master=self.tab("MultiSearch"))
        self.ms_button_frame.grid(row=4, column=1, sticky="nsew", padx=0, pady=1)  # Removed side padding

        self.ms_select_all_button = ctk.CTkButton(self.ms_button_frame, text="select all", width=20,
                                                  command=self.open_ms_rename_popup)
        self.ms_select_all_button.pack(side="left", padx=5, pady=1)

        self.ms_rename_button_image = ctk.CTkImage(light_image=Image.open("images/pencil.png"),
                                                   dark_image=Image.open("images/pencil.png"))
        self.ms_rename_button = ctk.CTkButton(self.ms_button_frame, text="", image=self.ms_rename_button_image,
                                              width=20, command=self.open_ms_rename_popup)
        self.ms_rename_button.pack(side="right", padx=5, pady=5)
        create_tooltip(self.ms_rename_button,
                       "(1) Find and replace, (2) Convert file formats, or (3) Add a prefix or suffix to the filenames")

        self.ms_copy_button_image = ctk.CTkImage(light_image=Image.open("images/11092355.png"),
                                                 dark_image=Image.open("images/11092355.png"))
        self.ms_copy_button = ctk.CTkButton(self.ms_button_frame, text="", image=self.ms_copy_button_image, width=20,
                                            command=self.open_ms_copy_popup)
        self.ms_copy_button.pack(side="right", padx=5, pady=5)
        create_tooltip(self.ms_copy_button, "Copy all selected items into a new folder.")

        self.ms_delete_button_image = ctk.CTkImage(light_image=Image.open("images/delete.png"),
                                                   dark_image=Image.open("images/delete.png"))
        self.ms_delete_button = ctk.CTkButton(self.ms_button_frame, text="", image=self.ms_delete_button_image,
                                              width=20, command=self.open_ms_delete_popup)
        self.ms_delete_button.pack(side="right", padx=5, pady=5)
        create_tooltip(self.ms_delete_button, "Delete all selected items.")

    ''' AutoClean Functions '''

    def load_autoclean_settings(self):
        settings = self.db_handler.get_autoclean_settings()
        if settings:
            self.ac_freq_menu.set(settings['frequency'])
            self.ac_folders_switch.select() if settings.get('empty_folders',
                                                            False) else self.ac_folders_switch.deselect()
            self.ac_unused_files_switch.select() if settings.get('unused_files',
                                                                 False) else self.ac_unused_files_switch.deselect()
            self.ac_duplicate_files_switch.select() if settings.get('duplicate_files',
                                                                    False) else self.ac_duplicate_files_switch.deselect()
            self.ac_recycling_switch.select() if settings.get('recycling_bin',
                                                              False) else self.ac_recycling_switch.deselect()
            self.ac_browser_history_switch.select() if settings.get('browser_history',
                                                                    False) else self.ac_browser_history_switch.deselect()

            next_cleaning_time = settings.get('next_clean_time', None)
            if next_cleaning_time:
                try:
                    # Ensure next_cleaning_time is a string before converting it
                    if isinstance(next_cleaning_time, datetime.datetime):
                        next_cleaning_time = next_cleaning_time.isoformat()
                    next_cleaning_time = datetime.datetime.fromisoformat(next_cleaning_time)
                    remaining_time = next_cleaning_time - datetime.datetime.now()
                    days, seconds = remaining_time.days, remaining_time.seconds
                    hours = seconds // 3600
                    minutes = (seconds % 3600) // 60
                    formatted_time = f"{days} days {hours} hours {minutes} minutes"
                except ValueError:
                    formatted_time = "N/A"
            else:
                formatted_time = "N/A"

            self.ac_next_cleaning_label.configure(text=f"Next Clean in\n\n{formatted_time}")

            # Schedule the next update for the label
            self.ac_next_cleaning_label.after(60000, self.load_autoclean_settings)  # Update every minute

    def set_clean_frequency(self, frequency):
        self.db_handler.update_autoclean_settings(frequency=frequency)
        self.auto_clean_handler.set_clean_frequency(frequency)
        self.update_next_cleaning_time_label()

    def update_next_cleaning_time_label(self):
        next_cleaning_time = self.auto_clean_handler.get_next_cleaning_time()
        self.ac_next_cleaning_label.configure(text=f"Next Clean in\n\n{next_cleaning_time}")
        self.ac_next_cleaning_label.after(60000, self.update_next_cleaning_time_label)  # Update every minute

    def clean_now(self):
        self.auto_clean_handler.clean_now()
        self.update_next_cleaning_time_label()

    def toggle_clean_empty_folders(self):
        value = int(self.ac_folders_switch.get())
        self.db_handler.update_autoclean_settings(empty_folders=value)
        self.auto_clean_handler.toggle_clean_flag('clean_empty_folders_flag', value)

    def toggle_clean_unused_files(self):
        value = int(self.ac_unused_files_switch.get())
        self.db_handler.update_autoclean_settings(unused_files=value)
        self.auto_clean_handler.toggle_clean_flag('clean_unused_files_flag', value)

    def toggle_clean_duplicate_files(self):
        value = int(self.ac_duplicate_files_switch.get())
        self.db_handler.update_autoclean_settings(duplicate_files=value)
        self.auto_clean_handler.toggle_clean_flag('clean_duplicate_files_flag', value)

    def toggle_clean_recycling_bin(self):
        value = int(self.ac_recycling_switch.get())
        self.db_handler.update_autoclean_settings(recycling_bin=value)
        self.auto_clean_handler.toggle_clean_flag('clean_recycling_bin_flag', value)

    def toggle_clean_browser_history(self):
        value = int(self.ac_browser_history_switch.get())
        self.db_handler.update_autoclean_settings(browser_history=value)
        self.auto_clean_handler.toggle_clean_flag('clean_browser_history_flag', value)

    ''' AutoDirect Functions '''

    # TODO : ugly
    def add_redirect(self, keyword="", from_directory="", to_directory="", id=None):
        new_frame = ctk.CTkFrame(self.ad_inner_frame)
        new_frame.pack(side="top", fill="x", padx=5, pady=5)

        remove_button = ctk.CTkButton(new_frame, text="×",
                                      command=lambda: self.remove_redirect(new_frame, ad_redir_key_entry,
                                                                           ad_from_dir_menu, ad_to_dir_entry), width=15,
                                      height=0, font=("Arial", 10))
        remove_button.pack(side="left", padx=8)

        ad_redir_key_entry = ctk.CTkEntry(new_frame, placeholder_text="Redirect keyword", width=120, font=("Arial", 12))
        ad_redir_key_entry.pack(side="left", padx=4)
        ad_redir_key_entry.insert(0, keyword if keyword else "Redirect keyword")
        if keyword == "":
            ad_redir_key_entry.configure(text_color="gray")
        else:
            ad_redir_key_entry.configure(text_color="white")
        ad_redir_key_entry.bind("<FocusIn>", lambda event: self.clear_placeholder(event, "Redirect keyword"))
        ad_redir_key_entry.bind("<FocusOut>", lambda event: self.set_placeholder(event, "Redirect keyword"))

        ad_from_dir_menu = ctk.CTkOptionMenu(new_frame,
                                             values=["-- from --", "Downloads", "Desktop", "custom folder 1",
                                                     "custom folder 2", "custom folder 3"],
                                             font=("Arial", 12), command=lambda choice: self.browse_folder(
                ad_from_dir_menu) if choice == "Custom folder" else None)
        ad_from_dir_menu.pack(side="left", padx=4)
        if from_directory:
            ad_from_dir_menu.set(from_directory)
        else:
            ad_from_dir_menu.set("-- from --")

        ad_to_dir_entry = ctk.CTkEntry(new_frame, placeholder_text="to this folder", width=150, font=("Arial", 12))
        ad_to_dir_entry.pack(side="left", padx=4)
        ad_to_dir_entry.insert(0, to_directory if to_directory else "to this folder")
        if to_directory == "":
            ad_to_dir_entry.configure(text_color="gray")
        else:
            ad_to_dir_entry.configure(text_color="white")
        ad_to_dir_entry.bind("<FocusIn>", lambda event: self.clear_placeholder(event, "to this folder"))
        ad_to_dir_entry.bind("<FocusOut>", lambda event: self.set_placeholder(event, "to this folder"))

        ad_browse_button_image = ctk.CTkImage(light_image=Image.open("images/3240447.png"),
                                              dark_image=Image.open("images/3240447.png"))
        ad_browse_button = ctk.CTkButton(new_frame, image=ad_browse_button_image, text="", width=20,
                                         command=lambda: browse_folder(ad_to_dir_entry))
        ad_browse_button.pack(side="left", padx=4)

        self.redirect_entries.append((ad_redir_key_entry, ad_from_dir_menu, ad_to_dir_entry))

        # Only add to the database if the entries are not blank and id is None
        if id is None:
            keyword = ad_redir_key_entry.get().strip()
            from_directory = ad_from_dir_menu.get().strip()
            to_directory = ad_to_dir_entry.get().strip()
            if keyword and from_directory and to_directory:
                # Check if redirect already exists before adding
                existing_redirects = self.db_handler.get_redirects()
                if (keyword, from_directory, to_directory) not in existing_redirects:
                    self.db_handler.add_redirect(keyword, from_directory, to_directory)

    def open_custom_folder_settings(self):
        custom_folders_popup = ctk.CTkToplevel(self)
        custom_folders_popup.title("Custom Folder Settings")
        custom_folders_popup.geometry("460x250")
        custom_folders_popup.resizable(False, False)
        custom_folders_popup.grab_set()
        folder_entries = []
        custom_folders_description_label = ctk.CTkLabel(custom_folders_popup,
                                                        text="Select up to 3 folders to choose from as the starting folder for AutoDirects.")
        custom_folders_description_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 0), sticky="w")

        for i in range(1, 4):
            folder_label = ctk.CTkLabel(custom_folders_popup, text=f"Custom Folder {i}")
            folder_label.grid(row=i + 1, column=0, padx=10, pady=10, sticky="w")

            folder_entry = ctk.CTkEntry(custom_folders_popup, placeholder_text=f"custom folder", width=270)
            folder_entry.grid(row=i + 1, column=1, padx=10, pady=10)
            folder_entry.insert(0, self.db_handler.get_custom_folder_path(i))
            folder_entries.append(folder_entry)

            browse_button_image = ctk.CTkImage(light_image=Image.open("images/3240447.png"),
                                               dark_image=Image.open("images/3240447.png"))
            browse_button = ctk.CTkButton(custom_folders_popup, image=browse_button_image, text="", width=20,
                                          command=lambda entry=folder_entry: self.browse_and_set_folder(entry, i))
            browse_button.grid(row=i + 1, column=2, padx=10, pady=10)

        save_button = ctk.CTkButton(custom_folders_popup, text="Save", width=450,
                                    command=lambda: self.save_custom_folders(folder_entries))
        save_button.grid(row=5, column=0, columnspan=4, padx=5, pady=20)

    def browse_and_set_folder(self, entry, index):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            entry.delete(0, "end")
            entry.insert(0, folder_selected)
            folder_name = os.path.basename(folder_selected)
            self.db_handler.update_custom_folder(index, folder_selected, folder_name)
            self.update_custom_folder_options()

    def save_custom_folders(self, folder_entries):
        for i, entry in enumerate(folder_entries, 1):
            folder_path = entry.get()
            if folder_path:
                folder_name = os.path.basename(folder_path)
                self.db_handler.update_custom_folder(i, folder_path, folder_name)
        self.update_custom_folder_options()

    def update_custom_folder_options(self):
        custom_folder_names = [self.db_handler.get_custom_folder_name(i) for i in range(1, 4)]
        self.custom_folders = ["-- from --", "Downloads", "Desktop"] + custom_folder_names
        for entry in self.redirect_entries:
            entry[1].configure(values=self.custom_folders)

    def clear_placeholder(self, event, placeholder):
        widget = event.widget
        if widget.get() == placeholder:
            widget.delete(0, "end")

    def set_placeholder(self, event, placeholder):
        widget = event.widget
        if widget.get() == "":
            widget.insert(0, placeholder)
            widget.config(fg="grey")

    def remove_redirect(self, frame, ad_redir_key_entry, ad_from_dir_menu, ad_to_dir_entry):
        keyword = ad_redir_key_entry.get()
        from_directory = ad_from_dir_menu.get()
        to_directory = ad_to_dir_entry.get()

        self.db_handler.delete_redirect(keyword, from_directory, to_directory)
        self.auto_direct_handler.remove_mapping(keyword, from_directory, to_directory)

        frame.pack_forget()
        frame.destroy()
        self.redirect_entries = [(e1, e2, e3) for e1, e2, e3 in self.redirect_entries if
                                 e1.winfo_exists() and e2.winfo_exists() and e3.winfo_exists()]

    def remove_all_redirects(self):
        self.db_handler.delete_all_redirects()
        self.auto_direct_handler.remove_mapping('', '', '')

        for child in self.ad_inner_frame.winfo_children():
            child.destroy()
        self.redirect_entries = []

    def load_redirects(self):
        redirects = self.db_handler.get_redirects()
        for keyword, from_directory, to_directory in redirects:
            self.add_redirect(keyword, from_directory, to_directory)

    def save_and_start(self):
        self.save_redirects()
        self.auto_direct_handler.clear_mappings()
        for entry in self.redirect_entries:
            keyword = entry[0].get().strip()
            from_directory = entry[1].get().strip()
            to_directory = entry[2].get().strip()
            if keyword and from_directory and to_directory:
                self.auto_direct_handler.add_mapping(keyword, from_directory, to_directory)
        self.auto_direct_handler.start()

    def save_redirects(self):
        self.db_handler.delete_all_redirects()
        for entry in self.redirect_entries:
            keyword = entry[0].get().strip()
            from_directory = entry[1].get().strip()
            to_directory = entry[2].get().strip()
            if keyword and from_directory and to_directory:
                self.db_handler.add_redirect(keyword, from_directory, to_directory)

    ''' MultiSearch Functions '''

    def perform_search(self):
        self.clear_search_results()
        directory = self.ms_directory_entry.get()
        keyword = self.ms_keyword_entry.get()
        if keyword:
            files_found = self.multi_search_handler.multi_search_for_files(keyword, directory)
            for file in files_found:
                result_checkbox = ctk.CTkCheckBox(self.search_results_frame, text=file)
                result_checkbox.pack(anchor="w", padx=15, pady=5)

    def clear_search_results(self):
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()

    def open_ms_delete_popup(self):
        selected_files = self.get_selected_files()

        if not selected_files:
            return

        ms_delete_popup = ctk.CTkToplevel(self)
        ms_delete_popup.title("Delete Multiple Items")
        ms_delete_popup.geometry("300x150")
        ms_delete_popup.resizable(False, False)
        ms_delete_popup.grab_set()

        ms_warning_image = ctk.CTkImage(light_image=Image.open("images/4096970.png"),
                                        dark_image=Image.open("images/4096970.png"), size=(50, 50))
        ms_warning_image_label = ctk.CTkLabel(ms_delete_popup, image=ms_warning_image, text="")
        ms_warning_image_label.pack(side="top")
        ms_warning_label = ctk.CTkLabel(ms_delete_popup, text="Are you sure?\n\nThis action cannot be undone.")
        ms_warning_label.pack(side="top", padx=10)
        ms_yes_button = ctk.CTkButton(ms_delete_popup, text="Yes, delete selected items", width=150,
                                      command=lambda: self.confirm_delete(ms_delete_popup, selected_files))
        ms_yes_button.pack(side="left", padx=5)
        ms_no_button = ctk.CTkButton(ms_delete_popup, text="No", width=150, command=ms_delete_popup.destroy)
        ms_no_button.pack(side="right", padx=5)

    def confirm_delete(self, popup, files):
        self.multi_search_handler.multi_delete_files(files)
        popup.destroy()
        self.perform_search()

    def open_ms_copy_popup(self):
        selected_files = self.get_selected_files()

        if not selected_files:
            return

        ms_copy_popup = ctk.CTkToplevel(self)
        ms_copy_popup.title("Copy to Folder")
        ms_copy_popup.geometry("250x150")
        ms_copy_popup.resizable(False, False)
        ms_copy_popup.grab_set()

        ms_name_file_image = ctk.CTkImage(light_image=Image.open("images/5762171.png"),
                                          dark_image=Image.open("images/5762171.png"), size=(50, 50))
        ms_name_file_label = ctk.CTkLabel(ms_copy_popup, image=ms_name_file_image, text="")
        ms_name_file_label.pack(side="top", pady=10)
        ms_name_file_entry = ctk.CTkEntry(ms_copy_popup, placeholder_text="Name new folder", width=200)
        ms_name_file_entry.pack(side="top", padx=10)
        ms_yes_button = ctk.CTkButton(ms_copy_popup, text="Copy", width=85,
                                      command=lambda: self.confirm_copy(ms_copy_popup, selected_files,
                                                                        ms_name_file_entry.get()))
        ms_yes_button.pack(side="right", padx=26)
        ms_no_button = ctk.CTkButton(ms_copy_popup, text="Cancel", width=85, command=ms_copy_popup.destroy)
        ms_no_button.pack(side="right")

    def confirm_copy(self, popup, files, folder_name):
        if not folder_name:
            return

        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        new_folder = os.path.join(downloads_path, folder_name)

        self.multi_search_handler.multi_copy_files(files, new_folder)
        popup.destroy()

    def open_ms_rename_popup(self):
        selected_files = self.get_selected_files()

        if not selected_files:
            return

        ms_rename_popup = ctk.CTkToplevel(self)
        ms_rename_popup.title("Rename Multiple Items")
        ms_rename_popup.geometry("250x200")
        ms_rename_popup.resizable(False, False)
        ms_rename_popup.grab_set()

        ms_warning_image = ctk.CTkImage(light_image=Image.open("images/caution.png"),
                                        dark_image=Image.open("images/caution.png"), size=(50, 50))
        ms_warning_image_label = ctk.CTkLabel(ms_rename_popup, image=ms_warning_image, text="")
        ms_warning_image_label.pack(side="top")
        ms_warning_label = ctk.CTkLabel(ms_rename_popup, text="Enter words for Renaming")
        ms_warning_label.pack(side="top", padx=10)
        ms_find_pattern_entry = ctk.CTkEntry(ms_rename_popup, placeholder_text="find", width=200)
        ms_find_pattern_entry.pack(side="top", padx=10, pady=5)
        ms_replace_pattern_entry = ctk.CTkEntry(ms_rename_popup, placeholder_text="replace", width=200)
        ms_replace_pattern_entry.pack(side="top", padx=10, pady=5)
        ms_yes_button = ctk.CTkButton(ms_rename_popup, text="Rename", width=85,
                                      command=lambda: self.confirm_rename(ms_rename_popup, selected_files,
                                                                          ms_find_pattern_entry.get(),
                                                                          ms_replace_pattern_entry.get()))
        ms_yes_button.pack(side="right", padx=26, pady=10)
        ms_no_button = ctk.CTkButton(ms_rename_popup, text="Cancel", width=85, command=ms_rename_popup.destroy)
        ms_no_button.pack(side="right", pady=10)

    def confirm_rename(self, popup, files, find_pattern, replace_pattern):
        if find_pattern and replace_pattern:
            self.multi_search_handler.multi_rename_files(files, find_pattern, replace_pattern)
            popup.destroy()
            self.perform_search()

    def get_selected_files(self):
        selected_files = []
        for widget in self.search_results_frame.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox) and widget.get() == 1:
                selected_files.append(widget.cget("text"))
        return selected_files


def main():
    ctk.set_default_color_theme("green")
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
