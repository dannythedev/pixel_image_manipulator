from tkinter.ttk import Progressbar
import tkinter as tk


class CustomMessageBox:
    def __init__(self, title, message, link_text, link_command, bg_color="#121212", fg_color="#EEEEEE"):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        self.title = title
        self.message = message
        self.link_text = link_text
        self.link_command = link_command
        self.bg_color = bg_color
        self.fg_color = fg_color

    def show(self):
        top = tk.Toplevel(self.root)
        top.title(self.title)
        top.configure(bg=self.bg_color)

        label = tk.Label(top, text=self.message, bg=self.bg_color, fg=self.fg_color)
        label.pack(pady=10, padx=10)

        link_label = tk.Label(top, text=self.link_text, fg="blue", cursor="hand2", bg=self.bg_color)
        link_label.pack(pady=5, padx=10)
        link_label.bind("<Button-1>", lambda event: self.link_command())

        ok_button = tk.Button(top, text="Ok", command=top.destroy, bg="#007bff", fg="white", relief="flat", padx=10)
        ok_button.pack(pady=10, padx=10)

        top.mainloop()

class CustomDialog:
    def __init__(self, parent, title, prompt, width=210, height=80):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)

        # Customize background color of the dialog
        self.dialog.configure(bg="#121212")

        self.label = tk.Label(self.dialog, text=prompt, bg="#121212", fg="white")
        self.label.pack()

        self.entry = tk.Entry(self.dialog)
        self.entry.pack()

        self.button = tk.Button(self.dialog, text="OK", command=self.on_ok, bg="#007bff", fg="white")
        self.button.pack()

        # Variable to store entered value
        self.result = None

        # Set window size and make it non-resizable
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.resizable(False, False)

    def on_ok(self):
        # Store the entered value
        self.result = self.entry.get()
        self.dialog.destroy()

    def show(self):
        self.parent.wait_window(self.dialog)
        return self.result


class CustomProgressBar:
    def __init__(self, parent, cancel_callback):
        self.progress_bar = Progressbar(parent, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.grid(row=6, column=1)

        # Create cancel button
        self.cancel_button = tk.Button(parent, text=" Cancel ",
                                         bg="#dc3545", fg="white", relief="flat", padx=10,
                                         command=cancel_callback)
        self.cancel_button.grid(row=7, column=2, columnspan=1, padx=10, pady=5, sticky="n")

    def update_progress(self, value, maximum):
        self.progress_bar['value'] = value
        self.progress_bar['maximum'] = maximum

    def destroy(self):
        self.progress_bar.destroy()
        self.cancel_button.destroy()


class ToolTip:
    def __init__(self, widget, text, fade_in_period=0.5):
        self.widget = widget
        self.text = text
        self.fade_in_period = fade_in_period
        self.opacity = 0
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.create_tooltip()
        self.reset()
        self.tooltip.deiconify()

    def reset(self):
        self.opacity = 0
        self.tooltip.attributes("-alpha", self.opacity)
        self.widget.after(50, self.fade_in)

    def leave(self, event=None):
        self.hide_tooltip()

    def create_tooltip(self):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.geometry(f"+{x}+{y}")
        self.tooltip.overrideredirect(True)
        self.tooltip.attributes("-alpha", self.opacity)

        label = tk.Label(self.tooltip, text=self.text, bg="white", padx=5, pady=2)
        label.pack()

        self.fade_in()

    def fade_in(self):
        if self.opacity < 1:
            self.opacity += 0.1
            self.tooltip.attributes("-alpha", self.opacity)
            self.widget.after(50, self.fade_in)
        else:
            self.opacity = 1

    def hide_tooltip(self):
        self.tooltip.withdraw()