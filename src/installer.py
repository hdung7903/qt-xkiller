
import sys
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import tempfile

class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Qt-XKiller Setup")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # Style
        style = ttk.Style()
        try:
            style.theme_use('vista')
        except: pass

        # Header
        header_frame = tk.Frame(root, bg='white', height=80)
        header_frame.pack(side='top', fill='x')
        
        lbl_title = tk.Label(header_frame, text="Qt-XKiller Setup", bg='white', font=('Segoe UI', 16, 'bold'))
        lbl_title.place(x=20, y=15)
        
        lbl_desc = tk.Label(header_frame, text="Install Qt-XKiller on your computer.", bg='white', font=('Segoe UI', 10))
        lbl_desc.place(x=20, y=50)

        # Content
        content_frame = tk.Frame(root, padx=20, pady=20)
        content_frame.pack(fill='both', expand=True)

        tk.Label(content_frame, text="Select Installation Folder:").pack(anchor='w')

        self.path_var = tk.StringVar(value=os.path.join(os.environ['LOCALAPPDATA'], "Qt-XKiller"))
        
        path_frame = tk.Frame(content_frame)
        path_frame.pack(fill='x', pady=5)
        
        entry_path = tk.Entry(path_frame, textvariable=self.path_var, width=40)
        entry_path.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        btn_browse = tk.Button(path_frame, text="Browse...", command=self.browse_folder)
        btn_browse.pack(side='right')

        # Options
        self.chk_desktop = tk.BooleanVar(value=True)
        tk.Checkbutton(content_frame, text="Create Desktop Shortcut", variable=self.chk_desktop).pack(anchor='w', pady=10)

        self.chk_startmenu = tk.BooleanVar(value=True)
        tk.Checkbutton(content_frame, text="Add to Start Menu", variable=self.chk_startmenu).pack(anchor='w')

        # Install Button
        self.btn_install = ttk.Button(root, text="Install", command=self.start_install)
        self.btn_install.pack(side='bottom', pady=20, padx=20, anchor='e')
        
        # Progress
        self.progress = ttk.Progressbar(content_frame, mode='determinate')
        self.lbl_status = tk.Label(content_frame, text="")

    def browse_folder(self):
        d = filedialog.askdirectory(initialdir=self.path_var.get())
        if d:
            self.path_var.set(d)

    def start_install(self):
        target_dir = self.path_var.get()
        if not target_dir:
            return

        self.btn_install.config(state='disabled')
        self.progress.pack(fill='x', pady=20)
        self.lbl_status.pack(anchor='w')
        
        self.root.update()
        
        try:
            self.install_process(target_dir)
            messagebox.showinfo("Success", "Installation completed successfully!")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Installation failed: {e}")
            self.btn_install.config(state='normal')
            self.progress.pack_forget()

    def get_resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def install_process(self, target_dir):
        # 1. Create Directory
        self.lbl_status.config(text="Creating directories...")
        self.progress['value'] = 20
        self.root.update()
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        # 2. Copy Executable
        self.lbl_status.config(text="Copying files...")
        self.progress['value'] = 40
        self.root.update()
        
        exe_source = self.get_resource_path("Qt-XKiller.exe")
        exe_dest = os.path.join(target_dir, "Qt-XKiller.exe")
        
        # If running from source (not bundled yet), check dist
        if not os.path.exists(exe_source):
             exe_source = os.path.join("dist", "Qt-XKiller.exe")
        
        if os.path.exists(exe_source):
            shutil.copy2(exe_source, exe_dest)
        else:
            raise FileNotFoundError(f"Source file not found: {exe_source}")
        
        # 3. Create Shortcuts
        self.lbl_status.config(text="Creating shortcuts...")
        self.progress['value'] = 80
        self.root.update()
        
        if self.chk_desktop.get():
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            self.create_shortcut(exe_dest, "Qt-XKiller", desktop)
            
        if self.chk_startmenu.get():
            start_menu = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')
            sm_dir = os.path.join(start_menu, "Qt-XKiller")
            if not os.path.exists(sm_dir):
                os.makedirs(sm_dir)
            self.create_shortcut(exe_dest, "Qt-XKiller", sm_dir)

        self.progress['value'] = 100
        self.lbl_status.config(text="Done.")
        self.root.update()

    def create_shortcut(self, target, name, folder):
        path = os.path.join(folder, name + ".lnk")
        vbs_script = f"""
        Set oWS = WScript.CreateObject("WScript.Shell")
        sLinkFile = "{path}"
        Set oLink = oWS.CreateShortcut(sLinkFile)
        oLink.TargetPath = "{target}"
        oLink.WorkingDirectory = "{os.path.dirname(target)}"
        oLink.IconLocation = "{target},0"
        oLink.Save
        """
        
        fd, vbs_path = tempfile.mkstemp(suffix=".vbs")
        with os.fdopen(fd, 'w') as f:
            f.write(vbs_script)
            
        subprocess.call(['cscript', '//Nologo', vbs_path], shell=True)
        os.remove(vbs_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()
