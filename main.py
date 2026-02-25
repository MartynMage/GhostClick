import sys
import customtkinter as ctk
from ui.app_window import GhostClickApp


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # check if a .ghostclick file was passed as a command-line argument
    script_path = None
    if len(sys.argv) > 1 and sys.argv[1].endswith(".ghostclick"):
        script_path = sys.argv[1]

    app = GhostClickApp(script_path=script_path)
    app.mainloop()


if __name__ == "__main__":
    main()
