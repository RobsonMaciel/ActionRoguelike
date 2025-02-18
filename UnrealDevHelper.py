import sys
import os
import platform
import subprocess
import threading
import queue
import glob
import json
import shutil
import winreg
import re

import customtkinter as ctk

###############################################################################
# Log Queue and Logging Functions
###############################################################################
log_queue = queue.Queue()

def log(message: str):
    """Sends a message to the queue, which will be processed by the GUI."""
    log_queue.put(message)

###############################################################################
# ANSI Parser for Coloring Output in CTkTextbox
###############################################################################
ANSI_COLORS = {
    '30': "ansi_black",
    '31': "ansi_red",
    '32': "ansi_green",
    '33': "ansi_yellow",
    '34': "ansi_blue",
    '35': "ansi_magenta",
    '36': "ansi_cyan",
    '37': "ansi_white",
}

def parse_ansi(text: str):
    """
    Extracts ANSI codes (e.g., \x1b[31m) and returns a list of (segment, color_tag).
    If there is no color, color_tag is None.
    """
    segments = []
    current_color = None
    last_pos = 0
    pattern = re.compile(r'(\x1b\[[0-9;]*m)')
    
    for match in pattern.finditer(text):
        esc_sequence = match.group(1)
        start, end = match.span()
        if start > last_pos:
            segment = text[last_pos:start]
            segments.append((segment, current_color))
        # Process ANSI code
        code = esc_sequence[2:-1]  # remove "\x1b[" and "m"
        codes = code.split(';')
        new_color = current_color
        for c in codes:
            if c == '0':
                new_color = None
            elif c in ANSI_COLORS:
                new_color = ANSI_COLORS[c]
        current_color = new_color
        last_pos = end
        
    if last_pos < len(text):
        segment = text[last_pos:]
        segments.append((segment, current_color))
        
    return segments

def poll_log_queue_colored(text_widget):
    """
    Checks the log queue and inserts each message into text_widget,
    parsing ANSI codes to display colors.
    """
    real_text_widget = getattr(text_widget, "_textbox", text_widget)
    try:
        while True:
            message = log_queue.get_nowait()
            for segment, color_tag in parse_ansi(message + "\n"):
                if color_tag:
                    real_text_widget.insert("end", segment, color_tag)
                else:
                    real_text_widget.insert("end", segment)
            real_text_widget.see("end")
    except queue.Empty:
        pass
    text_widget.after(100, poll_log_queue_colored, text_widget)

###############################################################################
# Running Commands in Real-Time (Streaming)
###############################################################################
def run_command_stream(command: str, status_var: ctk.StringVar, start_message: str, finish_message: str):
    """
    Executes 'command' with Popen, reading stdout line by line and sending it
    to the log in real time.
    """
    status_var.set(start_message)
    log(start_message)
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for line in iter(process.stdout.readline, ""):
            if line:
                log(line.rstrip("\n"))
        process.stdout.close()
        process.wait()
        retcode = process.returncode
        if retcode == 0:
            status_var.set("Done")
            log(finish_message)
        else:
            status_var.set("Error")
            log(f"Error: command returned exit code {retcode}")
    except Exception as e:
        log(f"Error: {e}")
        status_var.set("Error")

###############################################################################
# Utility Functions for Cleanup and Engine Path Lookup
###############################################################################
def find_unreal_engine_path_from_registry(version: str):
    registry_path = rf"SOFTWARE\EpicGames\Unreal Engine\{version}"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path, 0, winreg.KEY_READ)
        installed_directory, _ = winreg.QueryValueEx(key, "InstalledDirectory")
        winreg.CloseKey(key)
        if installed_directory and os.path.exists(installed_directory):
            return installed_directory
        else:
            log(f"Unreal Engine {version} found, but directory '{installed_directory}' does not exist.")
            return None
    except FileNotFoundError:
        log(f"Unreal Engine {version} not found in Windows registry.")
        return None

def remove_items_recursively(directory, folders_to_delete, files_to_delete):
    for folder in folders_to_delete:
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            try:
                shutil.rmtree(folder_path)
                log(f"Removed folder: {folder_path}")
            except Exception as e:
                log(f"Error removing folder {folder_path}: {e}")
    for file in files_to_delete:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                log(f"Removed file: {file_path}")
            except Exception as e:
                log(f"Error removing file {file_path}: {e}")
    for entry in os.listdir(directory):
        entry_path = os.path.join(directory, entry)
        if os.path.isdir(entry_path):
            remove_items_recursively(entry_path, folders_to_delete, files_to_delete)

def clean_plugins_folder(script_directory: str, project_name: str):
    plugins_directory = os.path.join(script_directory, "Plugins")
    if not os.path.isdir(plugins_directory):
        log(f"Plugins folder not found in {script_directory}.")
        return
    log("Cleaning plugin folders and files...")
    folders_to_delete = [".vs", "Binaries", "DerivedDataCache", "Intermediate", "Saved"]
    files_to_delete = [f"{project_name}.sln", ".vsconfig"]
    remove_items_recursively(plugins_directory, folders_to_delete, files_to_delete)

def clean_files_and_folders(script_directory: str, project_name: str):
    log("Cleaning project root folders...")
    folders_to_delete = [
        os.path.join(script_directory, ".vs"),
        os.path.join(script_directory, ".idea"),
        os.path.join(script_directory, "Binaries"),
        os.path.join(script_directory, "DerivedDataCache"),
        os.path.join(script_directory, "Intermediate"),
        os.path.join(script_directory, "Saved")
    ]
    for folder in folders_to_delete:
        if os.path.isdir(folder):
            try:
                shutil.rmtree(folder)
                log(f"Removed folder: {folder}")
            except Exception as e:
                log(f"Error removing folder {folder}: {e}")
    log("Cleaning project root files...")
    uproject_list = glob.glob("*.uproject")
    if uproject_list:
        project_file = uproject_list[0]
        project_name_local = os.path.splitext(os.path.basename(project_file))[0]
        files_to_delete = [
            os.path.join(script_directory, f"{project_name_local}.sln"),
            os.path.join(script_directory, ".vsconfig")
        ]
        for file in files_to_delete:
            if os.path.isfile(file):
                try:
                    os.remove(file)
                    log(f"Removed file: {file}")
                except Exception as e:
                    log(f"Error removing file {file}: {e}")
    clean_plugins_folder(script_directory, project_name)
    log("Cleanup completed successfully!")

###############################################################################
# Build Process (Compile the Editor)
###############################################################################
def run_build_process(open_sln: bool, open_uproject: bool, status_var: ctk.StringVar):
    """
    Compiles the Editor project via dotnet + UnrealBuildTool.
    Reads the .uproject file to determine the engine version, cleans the project,
    recreates the SLN file, and compiles the project.
    """
    try:
        script_directory = os.getcwd()
        uproject_files = glob.glob("*.uproject")
        if not uproject_files:
            log("No .uproject file found in the current directory.")
            return
        if len(uproject_files) > 1:
            log("More than one .uproject file found. Selecting the first one.")
        uproject_path = os.path.abspath(uproject_files[0])
        log(f".uproject file found: {uproject_path}")

        with open(uproject_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        engine_version = project_data.get("EngineAssociation")
        if not engine_version:
            log("'EngineAssociation' key not found in the .uproject file.")
            return
        log(f"Unreal Engine version set in project: {engine_version}")

        project_name = os.path.splitext(os.path.basename(uproject_path))[0]
        target_name = f"{project_name}Editor"
        log(f"Target to compile: {target_name}")

        unreal_engine_path = os.environ.get("UNREAL_ENGINE_PATH")
        if not unreal_engine_path:
            unreal_engine_path = find_unreal_engine_path_from_registry(engine_version)
            if not unreal_engine_path:
                unreal_engine_path = rf"C:\Program Files\Epic Games\UE_{engine_version}"
                log(f"Using default path: {unreal_engine_path}")
            else:
                log(f"Path obtained from registry: {unreal_engine_path}")
        else:
            log(f"Path defined by environment variable: {unreal_engine_path}")

        build_tool_dll = os.path.join(
            unreal_engine_path,
            "Engine",
            "Binaries",
            "DotNET",
            "UnrealBuildTool",
            "UnrealBuildTool.dll"
        )
        if not os.path.exists(build_tool_dll):
            log(f"File '{build_tool_dll}' not found.")
            return

        platform_str = "Win64"
        configuration = "Development"
        compile_command = (
            f'dotnet "{build_tool_dll}" {target_name} {platform_str} {configuration} '
            f'-Project="{uproject_path}" -WaitMutex -FromMsBuild -Rebuild'
        )

        log("\n=== Cleaning project files for rebuild ===")
        clean_files_and_folders(script_directory, project_name)

        build_script_path = os.path.join(unreal_engine_path, "Engine", "Build", "BatchFiles", "Build.bat")
        if not os.path.exists(build_script_path):
            log(f"Build.bat file not found at: {build_script_path}")
            return
        build_command = f'"{build_script_path}" -projectfiles -project="{uproject_path}" -game -rocket'
        log("\n=== Recreating SLN file (calling Build.bat) ===")
        log(f"Executing: {build_command}")
        run_command_stream(build_command, status_var, "Recreating SLN", "SLN file recreated successfully")

        log("\n=== Compiling the project ===")
        log(f"Executing: {compile_command}")
        run_command_stream(compile_command, status_var, "Compiling project", "Project compiled successfully")
        log("\nProject files compiled successfully.")

        if open_sln:
            sln_path = os.path.join(script_directory, f"{project_name}.sln")
            if os.path.isfile(sln_path):
                log("Opening SLN file...")
                os.startfile(sln_path)
            else:
                log("SLN file not found to open.")
        if open_uproject:
            if os.path.isfile(uproject_path):
                log("Opening .uproject file...")
                os.startfile(uproject_path)
            else:
                log(".uproject file not found to open.")
    except Exception as e:
        log(f"Error: {e}")

###############################################################################
# UAT Build Process (Packaging)
###############################################################################
def run_UAT_build_process(status_var: ctk.StringVar, build_path: str, build_config: str):
    """
    Executes BuildCookRun via RunUAT.bat for packaging.
    Builds, cooks, and packages the project.
    """
    try:
        script_directory = os.getcwd()
        uproject_files = glob.glob("*.uproject")
        if not uproject_files:
            log("No .uproject file found in the current directory.")
            return
        if len(uproject_files) > 1:
            log("More than one .uproject file found. Selecting the first one.")
        uproject_path = os.path.abspath(uproject_files[0])
        log(f".uproject file found: {uproject_path}")

        with open(uproject_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        engine_version = project_data.get("EngineAssociation")
        if not engine_version:
            log("'EngineAssociation' key not found in the .uproject file.")
            return
        log(f"Unreal Engine version set in project: {engine_version}")

        project_name = os.path.splitext(os.path.basename(uproject_path))[0]
        target = project_name
        log(f"Target to be built: {target}")

        unreal_engine_path = os.environ.get("UNREAL_ENGINE_PATH")
        if not unreal_engine_path:
            unreal_engine_path = find_unreal_engine_path_from_registry(engine_version)
            if not unreal_engine_path:
                unreal_engine_path = rf"C:\Program Files\Epic Games\UE_{engine_version}"
                log(f"Using default path: {unreal_engine_path}")
            else:
                log(f"Path obtained from registry: {unreal_engine_path}")
        else:
            log(f"Path defined by environment variable: {unreal_engine_path}")

        runUAT_path = os.path.join(unreal_engine_path, "Engine", "Build", "BatchFiles", "RunUAT.bat")
        if not os.path.exists(runUAT_path):
            log(f"RunUAT.bat file not found at: {runUAT_path}")
            return

        command = (
            f'"{runUAT_path}" '
            f'-ScriptsForProject="{uproject_path}" '
            f'Turnkey '
            f'-command=VerifySdk '
            f'-platform=Win64 '
            f'-UpdateIfNeeded '
            f'-EditorIO '
            f'-EditorIOPort=52904 '
            f'-project="{uproject_path}" '
            f'BuildCookRun '
            f'-nop4 '
            f'-utf8output '
            f'-nocompileeditor '
            f'-skipbuildeditor '
            f'-cook '
            f'-project="{uproject_path}" '
            f'-target={target} '
            f'-unrealexe="{os.path.join(unreal_engine_path, "Engine", "Binaries", "Win64", "UnrealEditor-Cmd.exe")}" '
            f'-platform=Win64 '
            f'-installed '
            f'-stage '
            f'-archive '
            f'-package '
            f'-build '
            f'-pak '
            f'-compressed '
            f'-prereqs '
            f'-archivedirectory="{build_path}" '
            f'-clientconfig={build_config} '
            f'-nocompile '
            f'-nocompileuat'
        )
        log("Executing UAT command:")
        log(command)
        run_command_stream(command, status_var, "Starting Build UAT...", "UAT Build completed successfully!")
    except Exception as e:
        log(f"Error in Build UAT: {e}")
        status_var.set("Error in Build UAT")

###############################################################################
# CustomTkinter UI (with Checkboxes and Radiobuttons)
###############################################################################
class MobileStyleApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.title("Unreal Build Tool - Dark Mobile Style")
        self.geometry("500x600")
        
        self.tabview = ctk.CTkTabview(self, corner_radius=0, width=500, height=600)
        self.tabview.pack(fill="both", expand=True)
        
        self.build_tab = self.tabview.add("Build")
        
        self.build_frame = ctk.CTkFrame(self.build_tab)
        self.build_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.status_var = ctk.StringVar(value="Ready")
        self.status_label = ctk.CTkLabel(
            self.build_frame,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.status_label.pack(pady=5)
        
        # Checkboxes to open SLN and .uproject afterwards
        self.open_sln = ctk.BooleanVar()
        self.open_uproject = ctk.BooleanVar()
        ctk.CTkCheckBox(self.build_frame, text="Open SLN afterwards", variable=self.open_sln).pack(pady=2)
        ctk.CTkCheckBox(self.build_frame, text="Open .uproject afterwards", variable=self.open_uproject).pack(pady=2)
        
        # Compile button
        self.compile_btn = ctk.CTkButton(self.build_frame, text="Compile Editor", command=self.start_compile_thread)
        self.compile_btn.pack(pady=10)
        
        # Packaging section
        ctk.CTkLabel(self.build_frame, text="Packaging").pack(pady=(10, 0))
        self.build_path_entry = ctk.CTkEntry(self.build_frame, width=250)
        self.build_path_entry.insert(0, os.path.join(os.getcwd(), "BuildOutput"))
        self.build_path_entry.pack(pady=5)
        
        # Radiobuttons for build config
        self.build_config = ctk.StringVar(value="Shipping")
        build_options = ["Debug", "DebugGame", "Development", "Shipping", "Test"]
        config_frame = ctk.CTkFrame(self.build_frame)
        config_frame.pack()
        for i, cfg in enumerate(build_options):
            rb = ctk.CTkRadioButton(config_frame, text=cfg, variable=self.build_config, value=cfg)
            rb.grid(row=0, column=i, padx=5)
        
        self.package_btn = ctk.CTkButton(self.build_frame, text="Build (UAT)", command=self.start_package_thread)
        self.package_btn.pack(pady=10)
        
        # Textbox for logs
        self.build_log_text = ctk.CTkTextbox(self.build_frame, width=450, height=200)
        self.build_log_text.pack(pady=10)
        
        # Configure ANSI color tags in the internal tk.Text widget if needed
        self.configure_ansi_tags(self.build_log_text)
        
        # Start polling for colored logs
        self.build_log_text.after(100, poll_log_queue_colored, self.build_log_text)
        
    def configure_ansi_tags(self, text_widget):
        """
        Configures ANSI color tags in the CTkTextbox or its internal tk.Text widget.
        """
        real_text_widget = getattr(text_widget, "_textbox", text_widget)
        real_text_widget.tag_config("ansi_black", foreground="#aaaaaa")
        real_text_widget.tag_config("ansi_red", foreground="#ff5555")
        real_text_widget.tag_config("ansi_green", foreground="#55ff55")
        real_text_widget.tag_config("ansi_yellow", foreground="#ffff55")
        real_text_widget.tag_config("ansi_blue", foreground="#5599ff")
        real_text_widget.tag_config("ansi_magenta", foreground="#ff55ff")
        real_text_widget.tag_config("ansi_cyan", foreground="#55ffff")
        real_text_widget.tag_config("ansi_white", foreground="#ffffff")
        
    def start_compile_thread(self):
        self.compile_btn.configure(state="disabled")
        self.status_var.set("Compiling Editor...")
        threading.Thread(target=self.run_compile, daemon=True).start()
        
    def run_compile(self):
        run_build_process(self.open_sln.get(), self.open_uproject.get(), self.status_var)
        self.compile_btn.configure(state="normal")
        
    def start_package_thread(self):
        self.package_btn.configure(state="disabled")
        self.status_var.set("Starting Build UAT...")
        build_path = self.build_path_entry.get().strip() or os.path.join(os.getcwd(), "BuildOutput")
        build_cfg = self.build_config.get()
        threading.Thread(target=self.run_package, args=(build_path, build_cfg), daemon=True).start()
        
    def run_package(self, build_path: str, build_cfg: str):
        run_UAT_build_process(self.status_var, build_path, build_cfg)
        self.package_btn.configure(state="normal")
        
if __name__ == "__main__":
    app = MobileStyleApp()
    app.mainloop()
