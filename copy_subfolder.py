import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
from pathlib import Path
import shutil
import sys

failed_copy = {
    "folder": [],
    "file": []
}
total_size = 0
def get_folder_size(folder_path):
    global total_size
    size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            if os.path.exists(file_path):  # Make sure the file exists
                size += os.path.getsize(file_path)
    total_size += size
    return size

def format_size(bytes_size):
    """Convert size in bytes to a more readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024


source_path = ""
def update_window_size():
    root.update_idletasks()  # Ensure all geometry updates are processed
    required_width = max(
        source_label.winfo_reqwidth(),
        subfolder_label.winfo_reqwidth(),
        dest_label.winfo_reqwidth()
    ) + 300  # Add padding for buttons and spacing
    required_height = root.winfo_reqheight()
    root.geometry(f"{required_width}x{required_height}")


def get_source_folder(label, store_path=False):
    global source_path
    folder_path = filedialog.askdirectory()
    if folder_path:
        label.config(text=folder_path)
        if store_path:
            source_path = folder_path
        update_window_size()


def get_sub_folder(label):
    global source_path
    if not source_path:
        messagebox.showwarning("Select Source Folder", "Please select the Source Folder.")
        return

    folder_path = filedialog.askdirectory(initialdir=source_path)
    if folder_path:
        common = os.path.commonpath([source_path, folder_path])
        if common != os.path.normpath(source_path):
            messagebox.showerror("Invalid Folder", "Sub Folder must be a subfolder of the Source Folder.")
            return

        relative_path = os.path.relpath(folder_path, source_path)
        parts = relative_path.split(os.sep)
        stripped_path = os.sep.join(parts[1:]) if len(parts) > 1 else ''
        label.config(text=stripped_path)
        update_window_size()


def get_dest_folder(label):
    folder_path = filedialog.askdirectory()
    if folder_path:
        label.config(text=folder_path)
        update_window_size()


def check_empty_labels():
    if not source_label.cget("text"):
        messagebox.showwarning("Missing Source Folder", "Please select a Source Folder.")
        return False
    if not subfolder_label.cget("text"):
        messagebox.showwarning("Missing Subfolder", "Please select a Subfolder.")
        return False
    if not dest_label.cget("text"):
        messagebox.showwarning("Missing Destination Folder", "Please select a Destination Folder.")
        return False
    return True


def copy_folder_safely(source_dir, dest_dir):
    failed = {
        "folder": [],
        "file": []
    }

    source = Path(source_dir)
    dest = Path(dest_dir)

    def copy_recursive(src, dst):
        try:
            entries = list(src.iterdir())
        except Exception:
            failed["folder"].append(str(src))
            return

        try:
            dst.mkdir(parents=True, exist_ok=True)
        except Exception:
            failed["folder"].append(str(src))
            return

        for entry in entries:
            dest_entry = dst / entry.name
            if entry.is_dir():
                copy_recursive(entry, dest_entry)
            elif entry.is_file():
                try:
                    shutil.copy2(entry, dest_entry)
                except Exception:
                    failed["file"].append(str(entry))

    copy_recursive(Path(source_dir), Path(dest_dir))

    return failed


def safe_list_dirs(folder_path):
    global failed_copy
    accessible_dirs = []
    for item in Path(folder_path).iterdir():
        try:
            if item.is_dir():
                accessible_dirs.append(item.name)
        except (PermissionError, OSError) as e:
            print(f"Failed to copy folder: \n {item}")
            failed_copy['folder'].append(item)
            # Optional: log this or show a messagebox
            continue
    return accessible_dirs


def copy_folder(source, dest):
    global failed_copy
    failed = copy_folder_safely(source, dest)
    failed_copy['file'] += failed['file']
    failed_copy['folder'] += failed['folder']
    print(Path(dest).name + "\nfolder size: " + format_size(get_folder_size(dest)) + "\t failed files:\n"  + str(failed))


def open_parent_folder(item_path):
    parent = os.path.dirname(item_path)
    try:
        if os.name == 'nt':  # Windows
            os.startfile(parent)
        elif os.name == 'posix':  # macOS or Linux
            import subprocess
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", parent])
    except Exception as e:
        messagebox.showerror("Error", f"Could not open folder: {parent}\n{e}")

def refresh_failed_display():
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    # Ensure the label stretches fully when the window resizes
    scrollable_frame.grid_columnconfigure(0, weight=0)
    scrollable_frame.grid_columnconfigure(1, weight=1)

    row = 0

    if failed_copy['folder']:
        header = tk.Label(
            scrollable_frame,
            text="Failed Folders:",
            font=("Arial", 10, "bold"),
            bg="#e0e0e0",
            anchor="w"
        )
        header.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=(0, 0))  # no top padding
        row += 1
        for path in failed_copy['folder']:
            ttk.Button(
                scrollable_frame,
                text="Open",
                command=lambda p=path: open_parent_folder(p)
            ).grid(row=row, column=0, sticky="w", padx=(0, 5))
            tk.Label(
                scrollable_frame,
                text=path,
                bg="white",
                anchor="w",
                justify="left",
                wraplength=500
            ).grid(row=row, column=1, sticky="w")
            row += 1

    if failed_copy['file']:
        header = tk.Label(
            scrollable_frame,
            text="Failed Files:",
            font=("Arial", 10, "bold"),
            bg="#e0e0e0",
            anchor="w"
        )
        header.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=(0, 0))
        row += 1
        for path in failed_copy['file']:
            ttk.Button(
                scrollable_frame,
                text="Open",
                command=lambda p=path: open_parent_folder(p)
            ).grid(row=row, column=0, sticky="w", padx=(0, 5))
            tk.Label(
                scrollable_frame,
                text=path,
                bg="white",
                anchor="w",
                justify="left",
                wraplength=500
            ).grid(row=row, column=1, sticky="w")
            row += 1

def copy_source_folders():
    global failed_copy
    global total_size
    total_size = 0
    failed_copy['file'] = []
    failed_copy['folder'] = []

    if not check_empty_labels():
        return
    
    source = source_label.cget("text")
    subfolder = subfolder_label.cget("text")
    dest = dest_label.cget("text")

    print("Source: " + source)
    print("Destination: " + dest)

    source_folders = safe_list_dirs(source)
    for folder in source_folders:
        copy_folder(source + "/" + folder + "/" + subfolder, dest + "/" + os.path.basename(folder))

    print("\nTotal size: " + str(format_size(total_size)))
    print("Items that failed to copy:")
    print(failed_copy)

    refresh_failed_display()
    messagebox.showinfo("Action", "Final function executed!")

# GUI setup
root = tk.Tk()
root.title("Folder Selector with Subfolder Enforcement")
root.geometry("800x410")
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(5, weight=1)

BUTTON_WIDTH = 25

ttk.Style().configure("TLabel", anchor="w")

# Source
source_button = ttk.Button(root, text="Open Source Folder", width=BUTTON_WIDTH, command=lambda: get_source_folder(source_label, store_path=True))
source_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")
source_label = ttk.Label(root, text="")
source_label.grid(row=0, column=1, sticky="w", padx=10)

# Subfolder
subfolder_button = ttk.Button(root, text="Open Subfolder Folder", width=BUTTON_WIDTH, command=lambda: get_sub_folder(subfolder_label))
subfolder_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")
subfolder_label = ttk.Label(root, text="")
subfolder_label.grid(row=1, column=1, sticky="w", padx=10)

# Destination
dest_button = ttk.Button(root, text="Open Destination Folder", width=BUTTON_WIDTH, command=lambda: get_dest_folder(dest_label))
dest_button.grid(row=2, column=0, padx=10, pady=10, sticky="w")
dest_label = ttk.Label(root, text="")
dest_label.grid(row=2, column=1, sticky="w", padx=10)

# Run Button
run_button = ttk.Button(root, text="Run Program", command=copy_source_folders)
run_button.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="ew")

# Failed items canvas
ttk.Label(root, text="Failed Items", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 0))
container_frame = ttk.Frame(root)
container_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")
container_frame.grid_columnconfigure(0, weight=1)
container_frame.grid_rowconfigure(0, weight=1)

canvas = tk.Canvas(container_frame, highlightthickness=0, bd=0)
scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

canvas.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")

scrollable_frame = tk.Frame(canvas, bg="white")
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="inner")

# Enable mouse scrolling
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

def expand_scroll_frame(event):
    canvas_width = event.width
    canvas_height = event.height
    canvas.itemconfig("inner", width=canvas_width)

    frame_height = scrollable_frame.winfo_height()
    canvas_height = canvas.winfo_height()
    if frame_height <= canvas_height:
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
        scrollbar.configure(command=lambda *args: None)
    else:
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        scrollbar.configure(command=canvas.yview)

canvas.bind("<Configure>", expand_scroll_frame)
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Start the app
root.mainloop()
