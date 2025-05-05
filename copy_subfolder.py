import tkinter as tk
from tkinter import filedialog, messagebox
import os
from pathlib import Path
import shutil

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
        except PermissionError:
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


def copy_source_folders():
    global failed_copy
    global total_size

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

    messagebox.showinfo("Action", "Final function executed!")


# GUI setup
root = tk.Tk()
root.title("Folder Selector with Subfolder Enforcement")
root.geometry("600x200")

BUTTON_WIDTH = 25

# Source folder
source_button = tk.Button(root, text="Open Source Folder", width=BUTTON_WIDTH, command=lambda: get_source_folder(source_label, store_path=True))
source_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")
source_label = tk.Label(root, text="", anchor="w", justify="left")
source_label.grid(row=0, column=1, sticky="w", padx=10)

# Subfolder
subfolder_button = tk.Button(root, text="Open Subfolder Folder", width=BUTTON_WIDTH, command=lambda: get_sub_folder(subfolder_label))
subfolder_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")
subfolder_label = tk.Label(root, text="", anchor="w", justify="left")
subfolder_label.grid(row=1, column=1, sticky="w", padx=10)

# Destination folder
dest_button = tk.Button(root, text="Open Destination Folder", width=BUTTON_WIDTH, command=lambda: get_dest_folder(dest_label))
dest_button.grid(row=2, column=0, padx=10, pady=10, sticky="w")
dest_label = tk.Label(root, text="", anchor="w", justify="left")
dest_label.grid(row=2, column=1, sticky="w", padx=10)

# Run button
run_button = tk.Button(root, text="Run", width=BUTTON_WIDTH, command=copy_source_folders)
run_button.grid(row=3, column=0, padx=10, pady=20, sticky="w")

root.mainloop()
