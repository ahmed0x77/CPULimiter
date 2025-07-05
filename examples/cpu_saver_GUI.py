import customtkinter as ctk
import sys
import ctypes
import time
import threading
from cpulimiter import CpuLimiter, get_active_app_pids, get_active_window_info

from PIL import Image, ImageDraw, ImageFont
import pystray

# --- Default Configuration ---
DEFAULT_IGNORED_APPS = {
    "explorer.exe", "svchost.exe", "powershell.exe", "cmd.exe",
    "WindowsTerminal.exe", "python.exe", "conhost.exe", "dwm.exe",
    "winlogon.exe", "csrss.exe", "RuntimeBroker.exe", "startmenuexperiencehost.exe"
}

# --- UI Theme and Fonts ---
FONT_NORMAL = ("Segoe UI", 13)
FONT_BOLD = ("Segoe UI", 13, "bold")
FONT_HEADER_TITLE = ("Segoe UI", 16, "bold")
FONT_SECTION = ("Segoe UI", 16, "bold")
FONT_SMALL = ("Segoe UI", 11)
COLOR_TEXT_SECONDARY = "#A0A0A0"
COLOR_STATUS_ACTIVE = "#2ECC71"  # Green
COLOR_STATUS_INACTIVE = "#E74C3C" # Red
COLOR_PRIMARY = "#5b2fc0" # The primary green color

# --- Helper function to create an icon from an emoji ---
def create_tray_icon_image():
    """Creates a PIL Image for the tray icon from an emoji."""
    width, height = 64, 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("seguiemj.ttf", 48)
    except IOError:
        font = ImageFont.load_default()
    
    draw.text((width // 2, height // 2), "⚙️", font=font, anchor="mm", fill="white")
    return image

class ExitConfirmationDialog(ctk.CTkToplevel):
    """A modal dialog to confirm if the user wants to exit or minimize."""
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master

        self.title("")
        self.geometry("380x150") # Set initial size
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)

        # Center the window *after* the event loop has had a chance to process it
        self.master_app.after(50, lambda: self.master_app.center_toplevel_window(self))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        label = ctk.CTkLabel(main_frame, text="Do you want to exit or keep the app\nrunning in the background?", font=FONT_NORMAL)
        label.pack(pady=(0, 20))

        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        exit_button = ctk.CTkButton(button_frame, text="Exit", command=self.master_app.quit_application, fg_color=("#DCE4EE", "#343638"), hover_color=("#AEB9C4", "#4A4C4E"))
        exit_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        minimize_button = ctk.CTkButton(button_frame, text="Minimize to Tray", command=self.minimize, fg_color=COLOR_PRIMARY)
        minimize_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def minimize(self):
        self.master_app.hide_to_tray()
        self.destroy()

class ProcessSelectorWindow(ctk.CTkToplevel):
    """A window to select a process from a list of running applications."""
    def __init__(self, master):
        super().__init__(master)
        self.master = master # Refers to RulesWindow
        self.title("Select Running Process")
        self.geometry("350x400") # Set initial size
        self.transient(master)
        self.grab_set()
        
        # Center this window over its parent (the RulesWindow)
        self.master.master_app.after(50, lambda: self.master.master_app.center_toplevel_window(self))
        
        self.label = ctk.CTkLabel(self, text="Select an application to add a rule for:")
        self.label.pack(padx=10, pady=10)

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Schedule the process list population
        self.after(100, self._populate_process_list)

    def _populate_process_list(self):
        """Fetches and displays the list of running processes."""
        try:
            visible_apps_pids = get_active_app_pids()
            process_names = sorted(list(set(info['name'].lower() for info in visible_apps_pids.values())))

            if not process_names:
                ctk.CTkLabel(self.scrollable_frame, text="No visible applications found.").pack(pady=10)
            else:
                for name in process_names:
                    btn = ctk.CTkButton(self.scrollable_frame, text=name, command=lambda n=name: self.select_process(n))
                    btn.pack(pady=2, padx=5, fill="x")
        except Exception as e:
            error_label = ctk.CTkLabel(self.scrollable_frame, text=f"Could not load processes:\n{e}", text_color="orange")
            error_label.pack(pady=10)

    def select_process(self, process_name):
        self.master.add_process_from_selector(process_name)
        self.destroy()

class RulesWindow(ctk.CTkToplevel):
    """Window for managing custom per-app rules and the ignore list."""
    def __init__(self, master, custom_rules, ignored_apps):
        super().__init__(master)
        self.master_app = master
        self.custom_rules = custom_rules
        self.ignored_apps = ignored_apps
        self.title("Manage App Rules")
        self.geometry("550x600") # Set initial size
        self.transient(master)
        self.grab_set()

        # Center the window *after* the event loop has had a chance to process it
        self.master_app.after(50, lambda: self.master_app.center_toplevel_window(self))

        self.tabview = ctk.CTkTabview(self, border_color=COLOR_PRIMARY, segmented_button_selected_color=COLOR_PRIMARY)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tab_custom = self.tabview.add("Custom Limits")
        self.tab_ignore = self.tabview.add("Ignored Apps")

        self.setup_custom_limits_tab()
        self.setup_ignored_apps_tab()
        
        # Schedule the list updates to ensure frames are fully rendered
        self.after(100, self.update_custom_rules_list)
        self.after(100, self.update_ignored_list)

    def setup_custom_limits_tab(self):
        add_frame = ctk.CTkFrame(self.tab_custom)
        add_frame.pack(padx=10, pady=10, fill="x")
        add_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(add_frame, text="Add New Custom Rule", font=FONT_BOLD).grid(row=0, column=0, columnspan=3, pady=(5,10))
        btn_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=3, pady=5)
        ctk.CTkButton(btn_frame, text="Add from running apps...", command=self.open_process_selector, fg_color=COLOR_PRIMARY).pack(side="left", padx=5)
        ctk.CTkLabel(btn_frame, text="or enter manually:").pack(side="left", padx=5)
        self.process_entry = ctk.CTkEntry(add_frame, placeholder_text="e.g., steam.exe")
        self.process_entry.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.limit_slider = ctk.CTkSlider(add_frame, from_=1, to=99, number_of_steps=98, button_color=COLOR_PRIMARY, progress_color=COLOR_PRIMARY)
        self.limit_slider.set(90)
        self.limit_slider.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.limit_label = ctk.CTkLabel(add_frame, text="Limit by 90% (leaves 10% CPU)")
        self.limit_slider.configure(command=lambda v: self.limit_label.configure(text=f"Limit by {int(v)}% (leaves {100-int(v)}% CPU)"))
        self.limit_label.grid(row=3, column=1, padx=10, sticky="w")
        ctk.CTkButton(add_frame, text="+ Add Rule", command=self.add_custom_rule, fg_color=COLOR_PRIMARY).grid(row=4, column=0, columnspan=3, pady=10)
        self.rules_list_frame = ctk.CTkScrollableFrame(self.tab_custom, label_text="Current Custom Rules")
        self.rules_list_frame.pack(padx=10, pady=10, fill="both", expand=True)

    def setup_ignored_apps_tab(self):
        add_frame = ctk.CTkFrame(self.tab_ignore)
        add_frame.pack(padx=10, pady=10, fill="x")
        self.ignore_entry = ctk.CTkEntry(add_frame, placeholder_text="e.g., spotify.exe")
        self.ignore_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        ctk.CTkButton(add_frame, text="+ Ignore Process", command=self.add_ignored_app, fg_color=COLOR_PRIMARY).pack(side="left", padx=10)
        self.ignore_list_frame = ctk.CTkScrollableFrame(self.tab_ignore, label_text="Ignored Processes (will never be limited)")
        self.ignore_list_frame.pack(padx=10, pady=10, fill="both", expand=True)

    def add_process_from_selector(self, process_name):
        self.process_entry.delete(0, "end")
        self.process_entry.insert(0, process_name)
    
    def open_process_selector(self):
        ProcessSelectorWindow(self)

    def add_custom_rule(self):
        name = self.process_entry.get().strip().lower()
        if not name: return
        limit = int(self.limit_slider.get())
        if name in self.ignored_apps: self.ignored_apps.discard(name); self.update_ignored_list()
        self.custom_rules[name] = {'limit': limit, 'enabled': True}
        self.update_custom_rules_list()
        self.process_entry.delete(0, "end")
        self.master_app.limiter_worker_event.set()

    def toggle_rule(self, name):
        if name in self.custom_rules: self.custom_rules[name]['enabled'] = not self.custom_rules[name]['enabled']
        self.update_custom_rules_list()
        self.master_app.limiter_worker_event.set()

    def remove_rule(self, name):
        if name in self.custom_rules: del self.custom_rules[name]
        self.update_custom_rules_list()
        self.master_app.limiter_worker_event.set()
    
    def update_custom_rules_list(self):
        for widget in self.rules_list_frame.winfo_children(): widget.destroy()
        for name, data in sorted(self.custom_rules.items()):
            frame = ctk.CTkFrame(self.rules_list_frame)
            frame.pack(fill="x", pady=2, padx=2)
            toggle = ctk.CTkSwitch(frame, text="", width=0, progress_color=COLOR_PRIMARY, button_color=COLOR_PRIMARY)
            toggle.pack(side="left", padx=5)
            toggle.select() if data['enabled'] else toggle.deselect()
            toggle.configure(command=lambda n=name: self.toggle_rule(n))
            label_text = f"{name} (Limit by {data['limit']}%)"
            if not data['enabled']: label_text = f"{name} (Using Global Limit)"
            label = ctk.CTkLabel(frame, text=label_text)
            if not data['enabled']: label.configure(text_color="gray50")
            label.pack(side="left", padx=5, fill="x", expand=True)
            ctk.CTkButton(frame, text="Remove", width=70, fg_color=("#F9F9FA", "#343638"), hover_color=("#F0F2F5", "#4A4C4E"), command=lambda n=name: self.remove_rule(n)).pack(side="right", padx=5)

    def add_ignored_app(self):
        name = self.ignore_entry.get().strip().lower()
        if not name: return
        if name in self.custom_rules: del self.custom_rules[name]; self.update_custom_rules_list()
        self.ignored_apps.add(name)
        self.update_ignored_list()
        self.ignore_entry.delete(0, "end")
        self.master_app.limiter_worker_event.set()

    def remove_ignored_app(self, name):
        self.ignored_apps.discard(name)
        self.update_ignored_list()
        self.master_app.limiter_worker_event.set()

    def update_ignored_list(self):
        for widget in self.ignore_list_frame.winfo_children(): widget.destroy()
        for name in sorted(list(self.ignored_apps)):
            frame = ctk.CTkFrame(self.ignore_list_frame)
            frame.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(frame, text=name).pack(side="left", padx=10, pady=5, fill="x", expand=True)
            ctk.CTkButton(frame, text="Remove", width=70, fg_color=("#F9F9FA", "#343638"), hover_color=("#F0F2F5", "#4A4C4E"), command=lambda n=name: self.remove_ignored_app(n)).pack(side="right", padx=5)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CPU Saver")
        self.geometry("480x620")

        self.limiter_thread = None
        self.is_running = ctk.BooleanVar(value=False)
        self.limiter_worker_event = threading.Event()
        self.custom_rules = {}
        self.ignored_apps = DEFAULT_IGNORED_APPS.copy()
        self.tray_icon = None

        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing_request)
        self.setup_tray_icon()

    def _create_widgets(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_bar_frame = ctk.CTkFrame(self, fg_color="#343638", corner_radius=0)
        top_bar_frame.grid(row=0, column=0, sticky="ew")
        top_bar_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(top_bar_frame, text="CPU Saver", font=FONT_HEADER_TITLE).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.status_label_top = ctk.CTkLabel(top_bar_frame, text="Inactive", font=FONT_BOLD, text_color=COLOR_STATUS_INACTIVE)
        self.status_label_top.grid(row=0, column=2, padx=(0, 10), pady=10)

        self.service_switch = ctk.CTkSwitch(top_bar_frame, text="", variable=self.is_running, command=self.toggle_limiter, progress_color=COLOR_PRIMARY, button_color=COLOR_PRIMARY)
        self.service_switch.grid(row=0, column=3, padx=(0, 20), pady=10, sticky="e")
        
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, sticky="ew")
        controls_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(controls_frame, text="Global Limit Strength", font=FONT_NORMAL).grid(row=0, column=0, sticky="w", pady=15)
        self.global_limit_slider = ctk.CTkSlider(controls_frame, from_=10, to=99, number_of_steps=89, command=self.update_global_limit_label, button_color=COLOR_PRIMARY, progress_color=COLOR_PRIMARY)
        self.global_limit_slider.set(95)
        self.global_limit_slider.grid(row=0, column=1, sticky="ew", padx=20)
        self.global_limit_value_label = ctk.CTkLabel(controls_frame, text="95%", font=FONT_NORMAL)
        self.global_limit_value_label.grid(row=0, column=2, sticky="e")
        
        self.global_limit_sub_label = ctk.CTkLabel(controls_frame, text="", font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY)
        self.global_limit_sub_label.grid(row=1, column=0, columnspan=3, sticky="w", padx=(0, 20), pady=(0, 20))
        self.update_global_limit_label(95)

        ctk.CTkLabel(controls_frame, text="Apply Limit After", font=FONT_NORMAL).grid(row=2, column=0, columnspan=3, sticky="w", pady=10)
        self.threshold_options = ctk.CTkOptionMenu(controls_frame, values=["5 Seconds", "10 Seconds", "15 Seconds", "30 Seconds", "60 Seconds"], fg_color=COLOR_PRIMARY, button_color=COLOR_PRIMARY)
        self.threshold_options.set("10 Seconds")
        self.threshold_options.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 20))

        manage_rules_button = ctk.CTkButton(main_frame, text="Manage App Rules", command=self.open_rules_window, font=FONT_BOLD, fg_color=COLOR_PRIMARY)
        manage_rules_button.grid(row=1, column=0, pady=20)

        status_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        status_frame.grid(row=2, column=0, sticky="nsew", pady=(20, 0))
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(status_frame, text="Status", font=FONT_SECTION).grid(row=0, column=0, sticky="w", pady=(10, 5))
        self.active_app_label = ctk.CTkLabel(status_frame, text="Service is stopped.", font=FONT_NORMAL, text_color=COLOR_TEXT_SECONDARY)
        self.active_app_label.grid(row=1, column=0, sticky="w")
        
        ctk.CTkLabel(status_frame, text="Apps with Limits", font=FONT_SECTION).grid(row=2, column=0, sticky="w", pady=(20, 5))
        
        self.limited_apps_frame = ctk.CTkScrollableFrame(status_frame, fg_color="transparent", label_text="", scrollbar_button_color=COLOR_PRIMARY)
        self.limited_apps_frame.grid(row=3, column=0, sticky="nsew")
        self.limited_apps_frame.grid_columnconfigure(0, weight=1)
        self.update_limited_list({})

    def setup_tray_icon(self):
        icon_image = create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window, default=True),
            pystray.MenuItem("Exit", self.quit_application)
        )
        self.tray_icon = pystray.Icon("cpusaver", icon_image, "CPU Saver", menu)
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

    def on_closing_request(self):
        for widget in self.winfo_children():
            if isinstance(widget, ExitConfirmationDialog):
                widget.lift()
                return
        ExitConfirmationDialog(self)

    def hide_to_tray(self):
        self.withdraw()

    def show_window(self):
        self.deiconify()
        self.lift()

    def quit_application(self):
        if self.tray_icon: self.tray_icon.stop()
        if self.is_running.get():
            self.is_running.set(False)
            if self.limiter_thread and self.limiter_thread.is_alive():
                self.limiter_worker_event.set()
                self.limiter_thread.join(timeout=3)
        self.destroy()

    def center_toplevel_window(self, toplevel_win):
        """Centers a CTkToplevel window over the main application window."""
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()

        toplevel_win.update_idletasks() # Ensure toplevel has its actual size
        toplevel_width = toplevel_win.winfo_width()
        toplevel_height = toplevel_win.winfo_height()

        new_x = main_x + (main_width // 2) - (toplevel_width // 2)
        new_y = main_y + (main_height // 2) - (toplevel_height // 2)

        toplevel_win.geometry(f"+{new_x}+{new_y}")
        toplevel_win.lift()

    def update_global_limit_label(self, value):
        limit_strength = int(value)
        cpu_left = 100 - limit_strength
        self.global_limit_value_label.configure(text=f"{limit_strength}%")
        self.global_limit_sub_label.configure(text=f"This means other apps can use only up to {cpu_left}% of your CPU.")

    def open_rules_window(self):
        for widget in self.winfo_children():
            if isinstance(widget, RulesWindow):
                widget.lift()
                return
        RulesWindow(self, self.custom_rules, self.ignored_apps)
        
    def toggle_limiter(self):
        if self.is_running.get():
            self.status_label_top.configure(text="Active", text_color=COLOR_STATUS_ACTIVE)
            self.limiter_thread = threading.Thread(target=self.limiter_worker, daemon=True)
            self.limiter_thread.start()
        else:
            self.status_label_top.configure(text="Inactive", text_color=COLOR_STATUS_INACTIVE)
            if self.limiter_thread and self.limiter_thread.is_alive():
                self.limiter_worker_event.set()
                self.limiter_thread.join(timeout=3)
            self.update_active_app_display(None)
            self.update_limited_list({})

    def limiter_worker(self):
        limiter = CpuLimiter()
        last_active_time = {}
        limited_app_names = {}

        try:
            while self.is_running.get():
                current_time = time.time()
                
                global_limit_strength = int(self.global_limit_slider.get())
                global_limit_for_lib = global_limit_strength

                threshold_text = self.threshold_options.get()
                inactivity_threshold = int(threshold_text.split()[0])
                
                visible_apps_pids = get_active_app_pids()
                active_window_info = get_active_window_info()
                
                active_app_name = None
                if active_window_info and active_window_info['name']:
                    active_app_name = active_window_info['name'].lower()
                    last_active_time[active_app_name] = current_time
                self.after(0, self.update_active_app_display, active_app_name)
                
                current_visible_app_names = {info['name'].lower() for info in visible_apps_pids.values()}
                
                for app_name in current_visible_app_names:
                    is_active = (app_name == active_app_name)
                    is_currently_managed = (app_name in limited_app_names)

                    if app_name in self.ignored_apps:
                        if is_currently_managed:
                            limiter.stop(process_name=app_name)
                            del limited_app_names[app_name]
                        continue

                    limit_to_apply_for_lib = global_limit_for_lib
                    
                    rule = self.custom_rules.get(app_name)
                    if rule and rule['enabled']: limit_to_apply_for_lib = rule['limit']

                    if is_active:
                        if is_currently_managed:
                            limiter.stop(process_name=app_name)
                            del limited_app_names[app_name]
                    else:
                        time_since_active = current_time - last_active_time.get(app_name, 0)
                        if time_since_active > inactivity_threshold:
                            if not is_currently_managed or limited_app_names[app_name] != limit_to_apply_for_lib:
                                limiter.add(process_name=app_name, limit_percentage=limit_to_apply_for_lib)
                                limiter.start(process_name=app_name)
                                limited_app_names[app_name] = limit_to_apply_for_lib
                        elif is_currently_managed:
                            limiter.stop(process_name=app_name)
                            del limited_app_names[app_name]
                
                names_to_remove = {name for name in limited_app_names if name not in current_visible_app_names}
                for app_name in names_to_remove:
                    limiter.stop(process_name=app_name)
                    del limited_app_names[app_name]

                self.after(0, self.update_limited_list, limited_app_names)
                self.limiter_worker_event.wait(2.0)
                self.limiter_worker_event.clear()
        finally:
            limiter.stop_all()

    def update_active_app_display(self, active_app_name):
        if not self.is_running.get():
            display_text = "Service is stopped."
        elif active_app_name:
            display_text = f"Active: {active_app_name}"
        else:
            display_text = "No app is currently active"
        
        self.active_app_label.configure(text=display_text, text_color="white" if active_app_name else COLOR_TEXT_SECONDARY)

    def update_limited_list(self, limited_app_names_dict):
        for widget in self.limited_apps_frame.winfo_children():
            widget.destroy()

        if not limited_app_names_dict and self.is_running.get():
            ctk.CTkLabel(self.limited_apps_frame, text="No apps are currently being limited.", font=FONT_NORMAL, text_color=COLOR_TEXT_SECONDARY).grid(row=0, column=0, sticky="w")
            return

        for i, (app_name, limit_value_for_lib) in enumerate(sorted(limited_app_names_dict.items())):
            # Display the limit_value_for_lib directly as that is the "limit strength"
            ctk.CTkLabel(self.limited_apps_frame, text=app_name, font=FONT_NORMAL).grid(row=i, column=0, sticky="w", pady=2)
            ctk.CTkLabel(self.limited_apps_frame, text=f"{limit_value_for_lib}%", font=FONT_NORMAL, text_color=COLOR_TEXT_SECONDARY).grid(row=i, column=1, sticky="e", pady=2)


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = App()
    app.mainloop()