
import os
import subprocess
import shutil
from PIL import Image

def run_command(command):
    print(f"Running: {command}")
    subprocess.check_call(command, shell=True)

def convert_icon():
    if os.path.exists("icon.png"):
        print("Converting icon.png to icon.ico...")
        img = Image.open("icon.png")
        img.save("icon.ico", format='ICO')
        return "icon.ico"
    return None

def main():
    print("--- Qt-XKiller Release Builder ---")
    
    # 1. Clean previous builds
    print("Cleaning up...")
    # Kill running instances if any
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] in ('Qt-XKiller.exe', 'Qt-XKiller-Setup.exe'):
                print(f"Killing running instance: {proc.info['name']}")
                proc.kill()
    except ImportError:
        pass # psutil might not be installed in the build env (though it should be)
    except Exception as e:
        print(f"Warning: Could not kill processes: {e}")

    if os.path.exists("build"): 
        try: shutil.rmtree("build", ignore_errors=True)
        except: pass
    if os.path.exists("dist"): 
        try: shutil.rmtree("dist", ignore_errors=True)
        except: pass
    
    # 2. Prepare Icon
    icon_arg = ""
    icon_file = convert_icon()
    if icon_file:
        icon_arg = f'--icon="{icon_file}"'
    
    # 3. Build Main App
    print("\n[1/3] Building Main Application...")
    cmd = f'pyinstaller --noconfirm --onefile --windowed --name "Qt-XKiller" {icon_arg} --add-data "src;src" --hidden-import "qtawesome" --hidden-import "qt_material" main.py'
    run_command(cmd)
    
    if not os.path.exists("dist/Qt-XKiller.exe"):
        print("Error: Main app build failed.")
        return

    # 4. Build Installer
    print("\n[2/3] Building Setup Installer...")
    # Installer also gets the icon if available
    inst_cmd = f'pyinstaller --noconfirm --onefile --windowed --name "Qt-XKiller-Setup" {icon_arg} --add-data "dist/Qt-XKiller.exe;." src/installer.py'
    run_command(inst_cmd)
    
    print("\n[3/3] Build Complete!")
    print("Artifacts:")
    print(" - App: dist/Qt-XKiller.exe")
    print(" - Installer: dist/Qt-XKiller-Setup.exe")

if __name__ == "__main__":
    main()
