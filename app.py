import tkinter as tk
from Functions import BG_COLOR
from ImageManipulatorApp import ImageManipulatorApp

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg=BG_COLOR)  # Dark mode
    app = ImageManipulatorApp(root)
    root.mainloop()
