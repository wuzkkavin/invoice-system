import sys
import os
import tkinter as tk


if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)


def main():
    import db_manager
    from ui_main import MainWindow

    root = tk.Tk()
    root.minsize(800, 500)
    app = MainWindow(root, db_manager)
    root.mainloop()


if __name__ == "__main__":
    main()
