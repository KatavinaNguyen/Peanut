import customtkinter as ctk

class ExampleApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure grid weights for resizing
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Create a frame for the progress bar at the bottom
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Add horizontal bouncing progress bar
        self.bouncing_progress_bar = ctk.CTkProgressBar(self.progress_frame, mode="indeterminate", indeterminate_speed=1)
        self.bouncing_progress_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.bouncing_progress_bar.start()

        # Additional widgets to demonstrate filling space
        self.main_content = ctk.CTkFrame(self)
        self.main_content.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 0))

        # Ensure main content expands
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

# Create an instance of the application
app = ExampleApp()
app.mainloop()
