import tkinter as tk
import db_manager
from ui_main import MainWindow


def main():
    root = tk.Tk()
    app = MainWindow(root, db_manager)
    root.mainloop()


if __name__ == "__main__":
    main()