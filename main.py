import tkinter as tk
from gui import FamiliadaGUI

def main():
    root = tk.Tk()
    app = FamiliadaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()