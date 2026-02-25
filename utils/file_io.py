import json
import os
from core.script import Script

GHOSTCLICK_EXT = ".ghostclick"


def save_script(script: Script, filepath: str) -> str:
    if not filepath.endswith(GHOSTCLICK_EXT):
        filepath += GHOSTCLICK_EXT

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(script.to_dict(), f, indent=2)

    return filepath


def load_script(filepath: str) -> Script:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Script.from_dict(data)


def get_recent_dir():
    """Return the last directory used, or fall back to Desktop."""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def register_file_association():
    """
    Registers .ghostclick files so double-clicking opens them with this app.
    Writes to HKCU so it doesn't need admin privileges.
    """
    try:
        import winreg
        import sys

        if getattr(sys, "frozen", False):
            exe_path = f'"{sys.executable}"'
        else:
            main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "main.py")
            main_path = os.path.normpath(main_path)
            exe_path = f'"{sys.executable}" "{main_path}"'

        # set up the file type
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.ghostclick") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "GhostClick.Script")

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, r"Software\Classes\GhostClick.Script"
        ) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "GhostClick Script File")

        cmd = f'{exe_path} "%1"'
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Classes\GhostClick.Script\shell\open\command",
        ) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, cmd)

        return True
    except Exception:
        return False
