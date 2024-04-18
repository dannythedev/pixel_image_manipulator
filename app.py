import threading
from tkinter.colorchooser import askcolor
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
import numpy as np
import os
from collections import Counter
import tkinter as tk
import json

BG_COLOR = "#121212"
FG_COLOR = "#EEEEEE"

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


class ImageManipulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Manipulator")

        self.frame = tk.Frame(root, bg=BG_COLOR)
        self.frame.pack(padx=20, pady=20)

        self.btn_select_images = tk.Button(self.frame, text="Resize Images", command=self.resize_images_option,
                                           bg="#007bff", fg="white", relief="flat", padx=10)
        self.btn_select_images.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
        ToolTip(self.btn_select_images,
                "Select PNG images, input resize percentage,\nresize, save to subfolder in initial directory.")

        self.btn_select_spritesheet = tk.Button(self.frame, text="Make Spritesheet",
                                                command=self.create_spritesheet_option,
                                                bg="#28a745", fg="white", relief="flat", padx=10)
        self.btn_select_spritesheet.grid(row=1, column=1, pady=10, padx=10, sticky="ew")
        ToolTip(self.btn_select_spritesheet,
                "Select PNG images, combine into sprite-\nsheet, save to subfolder in initial directory.")

        self.btn_select_colors = tk.Button(self.frame, text="Replace Colors", command=self.select_colors,
                                           bg="#dc3545", fg="white", relief="flat", padx=10)
        self.btn_select_colors.grid(row=2, column=0, pady=10, padx=10, sticky="ew")
        ToolTip(self.btn_select_colors,
                "Choose color to replace, select new color, select PNG images,\nreplace colors, save to subfolder in initial directory.")

        self.btn_select_images = tk.Button(self.frame, text="Pixelate", command=self.pixelate_images_option,
                                           bg="#17a2b8", fg="white", relief="flat", padx=10)
        self.btn_select_images.grid(row=3, column=0, pady=10, columnspan=2, padx=10, sticky="ew")
        ToolTip(self.btn_select_images,
                "Select PNG images, adjust options, pixelate,\nsave to subfolder in initial directory.")

        self.btn_remove_color = tk.Button(self.frame, text="Remove Color", command=self.remove_color_option,
                                          bg="#ebad07", fg="white", relief="flat", padx=10)
        self.btn_remove_color.grid(row=2, column=1, pady=10, padx=10, sticky="ew")
        ToolTip(self.btn_remove_color,
                "Choose color to remove, select PNG images,\n remove color, save to subfolder in initial directory.")

    def resize_images_option(self):
        files = filedialog.askopenfilenames(filetypes=[("PNG files", "*.png")])
        if files:
            directory = os.path.dirname(files[0])

            # Use custom dialog to get resize percentage
            dialog = CustomDialog(self.root, "Input", "Enter Resize Percentage (%):")
            resize_percent_str = dialog.show()

            if resize_percent_str:
                resize_percent = float(resize_percent_str) / 100.0
                ImageManipulator.resize_images(files, directory, resize_percent)
            else:
                messagebox.showerror("Error", "Please enter a resize percentage.")

    def create_spritesheet_option(self):
        files = filedialog.askopenfilenames(filetypes=[("PNG files", "*.png")])
        if files:
            directory = os.path.dirname(files[0])
            ImageManipulator.create_spritesheet(files, directory)

    def select_colors(self):
        # Set default colors
        default_color1 = (127, 127, 127)
        default_color2 = (96, 180, 242)
        # Create a custom color picker dialog to choose the colors to replace
        target_color = askcolor(title="Choose Color to Replace", color=default_color1)
        if target_color:
            target_color = tuple(int(x) for x in target_color[0])
            new_color = askcolor(title="Choose New Color", color=default_color2)[0]
            if new_color:
                new_color = tuple(int(x) for x in new_color)
                # Get selected files
                files = filedialog.askopenfilenames(filetypes=[("PNG files", "*.png")])
                if files:
                    # Get the directory of the first selected file
                    directory = os.path.dirname(files[0])
                    ImageManipulator.replace_color(files, directory, target_color, new_color)

    def pixelate_images_option(self):
        files = filedialog.askopenfilenames(filetypes=[("PNG files", "*.png")])
        if files:
            PixelateWindow(self.root, files)

    def remove_color_option(self):
        # Create a custom color picker dialog to choose the color to remove
        default_color = (59, 93, 201)
        target_color = askcolor(title="Choose Color to Remove", color=default_color)[0]
        if target_color:
            target_color = tuple(int(x) for x in target_color)
            files = filedialog.askopenfilenames(filetypes=[("PNG files", "*.png")])
            if files:
                # Get the directory of the first selected file
                directory = os.path.dirname(files[0])
                self.remove_color(files, directory, target_color)

    def remove_color(self, files, output_directory, target_color):
        removed_directory = output_directory + "/removed_images"
        os.makedirs(removed_directory, exist_ok=True)

        for file in files:
            img = Image.open(file)
            img = img.convert("RGBA")
            img = ImageManipulator.remove_color(img, target_color[:3])
            file_name = os.path.basename(file)
            img.save(f"{removed_directory}/{file_name}")

        export_message(files, message="Color removed from images and saved successfully.")


class CustomProgressBar:
    def __init__(self, parent):
        self.progress_bar = Progressbar(parent, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.grid(row=7, column=1, columnspan=3, padx=10, pady=5, sticky="e")

    def update_progress(self, value, maximum):
        self.progress_bar['value'] = value
        self.progress_bar['maximum'] = maximum

    def destroy(self):
        self.progress_bar.destroy()


class PixelateWindow:
    def __init__(self, root, files):
        self.preview_photo = None
        self.files = files
        self.pixelate_window = tk.Toplevel(root)
        self.pixelate_window.title("Pixelation Options")

        self.pixelate_window.configure(bg=BG_COLOR)

        # Initialize the preview area
        self.preview_canvas = tk.Canvas(self.pixelate_window, bg=BG_COLOR, highlightbackground=BG_COLOR, width=200,
                                        height=200)
        self.preview_canvas.grid(row=0, column=1, padx=10, pady=5)
        self.values = {'block_size': 4, 'saturation': -25, 'brightness': 0, 'contrast': 0, 'palette': '',
                       'background': 0}
        self.block_size_label = tk.Label(self.pixelate_window, text="Block Size", bg=BG_COLOR, fg=FG_COLOR)
        self.block_size_label.grid(row=1, column=0, padx=10, pady=5)
        self.block_size_scale = tk.Scale(self.pixelate_window, from_=1, to=20, orient="horizontal", bg=BG_COLOR,
                                         fg=FG_COLOR)
        self.block_size_scale.set(self.values['block_size'])
        self.block_size_scale.grid(row=1, column=1, padx=10, pady=5)

        def create_slider(label_text, default_value, row):
            label = tk.Label(self.pixelate_window, text=label_text, bg=BG_COLOR, fg=FG_COLOR)
            label.grid(row=row, column=0, padx=10, pady=5)
            scale = tk.Scale(self.pixelate_window, from_=-100, to=100, orient="horizontal", bg=BG_COLOR, fg=FG_COLOR,
                             length=200)
            scale.set(default_value)
            scale.grid(row=row, column=1, padx=10, pady=5)
            return scale
        # Create saturation slider
        self.saturation_scale = create_slider("Saturation Level", self.values['saturation'], 2)
        # Create brightness slider
        self.brightness_scale = create_slider("Brightness Level", self.values['brightness'], 3)
        # Create brightness slider
        self.contrast_scale = create_slider("Contrast Level", self.values['contrast'], 4)
        self.palette_label = tk.Label(self.pixelate_window, text="Select Palette:", bg=BG_COLOR, fg=FG_COLOR)
        self.palette_label.grid(row=5, column=0, padx=10, pady=5)

        # Define sample palettes with names
        self.palettes = [
            {"name": "Basic Colors", "colors": [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255),
                                                (255, 255, 0), (255, 0, 255), (0, 255, 255), (128, 128, 128),
                                                (32, 32, 32),
                                                (64, 64, 64), (192, 192, 192), (244, 244, 244), (128, 0, 0),
                                                (128, 128, 0),
                                                (0, 128, 0), (128, 0, 128), (0, 128, 128), (0, 0, 128), (255, 128, 0),
                                                (128, 255, 0), (0, 255, 128), (0, 128, 255), (128, 0, 255),
                                                (255, 0, 128),
                                                (255, 128, 128), (128, 255, 128), (128, 128, 255), (255, 255, 128),
                                                (255, 128, 255), (128, 255, 255), (192, 192, 192), (128, 64, 0),
                                                (128, 0, 64),
                                                (64, 0, 128), (0, 64, 128), (0, 128, 64), (64, 128, 0)]},
            {"name": "Earthy Tones", "colors": [(140, 143, 174), (88, 69, 99), (62, 33, 55), (154, 99, 72),
                                                (215, 155, 125), (245, 237, 186), (192, 199, 65), (100, 125, 52),
                                                (228, 148, 58), (157, 48, 59), (210, 100, 113), (112, 55, 127),
                                                (126, 196, 193), (52, 133, 157), (23, 67, 75), (31, 14, 28)]},
            {"name": "Oceanic Hues", "colors": [(26, 28, 44), (93, 39, 93), (177, 62, 83), (239, 125, 87),
                                                (255, 205, 117), (167, 240, 112), (56, 183, 100), (37, 113, 121),
                                                (41, 54, 111), (59, 93, 201), (65, 166, 246), (115, 239, 247),
                                                (244, 244, 244), (148, 176, 194), (86, 108, 134), (51, 60, 87)]},
            {"name": "Neutral Shades", "colors": [(94, 96, 110), (34, 52, 209), (12, 126, 69), (68, 170, 204),
                                                  (138, 54, 34), (235, 138, 96), (0, 0, 0), (92, 46, 120),
                                                  (226, 61, 105), (170, 92, 61), (255, 217, 63), (181, 181, 181),
                                                  (255, 255, 255)]},
            {"name": "Warm Palette", "colors": [(48, 0, 48), (96, 40, 120), (248, 144, 32), (248, 240, 136)]},
            {"name": "Pastel Dreams", "colors": [(49, 31, 95), (22, 135, 167), (31, 213, 188), (237, 255, 177)]},
            {"name": "Warm Earthy", "colors": [(208, 56, 24), (49, 59, 98), (148, 150, 179), (234, 222, 186),
                                               (255, 171, 145), (251, 119, 70), (180, 144, 111), (122, 87, 97),
                                               (193, 102, 135), (226, 169, 176), (232, 191, 217), (138, 108, 127),
                                               (61, 33, 43), (92, 142, 144), (182, 200, 170), (242, 241, 231)]},
            {"name": "Vibrant Mix", "colors": [(220, 20, 60), (255, 99, 71), (255, 215, 0), (255, 140, 0),
                                               (65, 105, 225), (0, 191, 255), (0, 128, 128), (0, 206, 209),
                                               (255, 69, 0), (255, 105, 180)]},
            {"name": "Dusk Burst", "colors": [(255, 209, 102),(255, 174, 45),(255, 117, 0),
                (255, 107, 165),(221, 72, 133),(152, 0, 109),(239, 98, 72),(221, 47, 45),
                (194, 0, 0),(218, 218, 218),(168, 168, 168),(107, 107, 107),(255, 38, 38),
                (191, 0, 0),(128, 0, 0),(255, 94, 0)]},
            {"name": "Rainy Dark Day",
             "colors": [(33, 68, 120), (0, 128, 128), (75, 0, 130), (38, 38, 51), (72, 61, 139), (25, 25, 112)]},
            {"name": "Calm Waters",
             "colors": [(195, 225, 254), (143, 179, 224), (80, 125, 184), (46, 81, 162), (0, 39, 118)]},
            {"name": "Spring Meadow",
             "colors": [(220, 237, 200), (150, 205, 100), (110, 171, 101), (67, 116, 62), (41, 83, 65)]},
            {"name": "Golden Sunset",
             "colors": [(255, 195, 160), (255, 140, 0), (204, 85, 0), (153, 51, 0), (102, 34, 0)]},
            {"name": "Soft Lavender",
             "colors": [(200, 180, 215), (160, 120, 180), (120, 80, 145), (80, 40, 110), (40, 0, 75)]},
        ]
        self.progress_bar = None

        # Display sample palettes
        self.palette_var = tk.StringVar()
        self.palette_var.set(self.palettes[0]["name"])  # Default palette
        self.palette_menu = tk.OptionMenu(self.pixelate_window, self.palette_var,
                                          *[palette["name"] for palette in self.palettes])
        self.palette_menu.grid(row=5, column=1, padx=10, pady=5)
        self.palette_menu.configure(bg=BG_COLOR, fg=FG_COLOR)
        self.palette_dropdown = tk.Menu(self.palette_menu, tearoff=0, bg=BG_COLOR, fg=FG_COLOR)
        self.palette_menu.configure(menu=self.palette_dropdown)

        # Add palettes to the dropdown menu
        for palette in self.palettes:
            self.add_palette_to_menu(palette)

        self.remove_background_var = tk.IntVar()
        self.remove_background_checkbutton = tk.Checkbutton(self.pixelate_window, text="Remove Background",
                                                            variable=self.remove_background_var,
                                                            onvalue=1, offvalue=0, bg=BG_COLOR, fg=FG_COLOR,
                                                            selectcolor="black")
        self.remove_background_checkbutton.grid(row=6, column=0, columnspan=2, pady=5)
        self.remove_background_checkbutton.select()

        self.pixelate_button = tk.Button(self.pixelate_window, text="Pixelate",
                                         bg="#17a2b8", fg="white", relief="flat", padx=10,
                                         command=self.start_pixelation_thread)
        self.pixelate_button.grid(row=7, column=0, columnspan=2, pady=10)
        # Add Export Settings button
        self.export_settings_button = tk.Button(self.pixelate_window, text="Export Settings",
                                                bg="#28a745", fg="white", relief="flat", padx=10,
                                                command=self.export_settings)
        self.export_settings_button.grid(row=6, column=0, pady=5, sticky="s")

        # Add Import Settings button
        self.load_settings_button = tk.Button(self.pixelate_window, text="Import Settings",
                                              bg="#007bff", fg="white", relief="flat", padx=10,
                                              command=self.load_settings)
        self.load_settings_button.grid(row=7, column=0, pady=5, sticky="n")

        self.palette_var.trace("w", lambda *args: self.update_preview())  # Bind to palette dropdown
        self.block_size_scale.bind("<ButtonRelease-1>", lambda *args: self.update_preview())  # Bind to block size scale
        self.saturation_scale.bind("<ButtonRelease-1>", lambda *args: self.update_preview())  # Bind to saturation scale
        self.brightness_scale.bind("<ButtonRelease-1>", lambda *args: self.update_preview())  # Bind to saturation scale
        self.contrast_scale.bind("<ButtonRelease-1>", lambda *args: self.update_preview())  # Bind to saturation scale
        self.update_preview()  # Update the preview initially

    def export_settings(self):
        # Ask the user to choose where to save the file
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        # If the user cancels the dialog, return None
        if not file_path:
            return None
        # Export the current settings to a JSON file
        with open(file_path, 'w') as json_file:
            json.dump(self.values, json_file)
        # Get the directory path
        directory = os.path.dirname(file_path)
        export_message(self.files, message="Settings exported.", dir=directory)

    def load_settings(self):
        # Ask the user to choose the JSON file to load
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])

        # If the user cancels the dialog, return None
        if not file_path:
            return None
        try:
            # Load settings from the JSON file
            with open(file_path, 'r') as json_file:
                self.values = json.load(json_file)

            self.block_size_scale.set(self.values['block_size'])
            self.saturation_scale.set(self.values['saturation'])
            self.brightness_scale.set(self.values['brightness'])
            self.contrast_scale.set(self.values['contrast'])
            self.palette_var.set(self.values['palette'])
            self.remove_background_var.set(self.values['background'])
            self.update_preview()
        except:
            messagebox.showerror("Error", f"File could not be read.")

    def update_preview(self):
        # Define the maximum width and height for the preview
        max_width = 300
        max_height = 300

        # Load the first chosen exported image
        if self.files:
            first_image_path = self.files[0]
            image = Image.open(first_image_path)
            # Resize the image to fit within the maximum width and height while maintaining aspect ratio
            image.thumbnail((max_width, max_height))
            # Get the size of the resized image
            width, height = image.size

            # Get parameters
            block_size = self.block_size_scale.get()
            saturation = self.saturation_scale.get()
            brightness = self.brightness_scale.get()
            contrast = self.contrast_scale.get()
            background = self.remove_background_var.get()

            selected_palette = next((p["colors"] for p in self.palettes if p["name"] == self.palette_var.get()), None)
            # if self.values['block_size'] != block_size or self.values['palette'] != selected_palette:
            # Pixelate the image
            self.preview_photo = ImageManipulator.pixelate(image, block_size, selected_palette, resize=False)
            self.preview_photo = ImageManipulator.adjust_saturation(self.preview_photo, saturation)
            self.preview_photo = ImageManipulator.adjust_brightness(self.preview_photo, brightness)
            self.preview_photo = ImageManipulator.adjust_contrast(self.preview_photo, contrast)

            self.values = {'block_size': block_size, 'saturation': saturation, 'brightness': brightness,
                           'contrast': contrast,
                           'palette': next((p["name"] for p in self.palettes if p["name"] == self.palette_var.get()),
                                           None),
                           'background': background}
            # Convert to PhotoImage
            self.preview_photo = ImageTk.PhotoImage(self.preview_photo)

            # Update the preview canvas
            self.preview_canvas.config(width=width, height=height)  # Adjust canvas size
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor="nw", image=self.preview_photo)

    def add_palette_to_menu(self, palette):
        # Create a menu item for the palette
        palette_menu = tk.Menu(self.palette_dropdown, tearoff=0, borderwidth=1)

        # Create a frame for each palette to display colors horizontally
        palette_frame = tk.Frame(palette_menu, relief='raised', borderwidth=1)
        palette_frame.pack()

        # Add colors to the frame
        for color in palette["colors"]:
            color_hex = '#%02x%02x%02x' % color
            color_button = tk.Button(palette_frame, bg=color_hex, width=2, height=1)
            color_button.pack(side='left', padx=1, pady=1)
            color_button.bind('<Button-1>', lambda event, p=palette["name"]: self.select_palette(p))

        # Add a command to the menu item to select the palette
        palette_menu.add_command(label='Choose', command=lambda p=palette["name"]: self.select_palette(p))
        self.palette_dropdown.add_cascade(label=palette["name"], menu=palette_menu)
        for color in palette["colors"]:
            color_hex = '#%02x%02x%02x' % color
            palette_menu.add_command(label='', background=color_hex, activebackground=color_hex, state='disabled')

    def select_palette(self, palette_name):
        # Set the selected palette
        self.palette_var.set(palette_name)

    def start_pixelation_thread(self):
        # Disable the pixelate button during pixelation
        self.pixelate_button.config(state=tk.DISABLED)

        # Start a new thread for pixelation
        threading.Thread(target=self.pixelate_images).start()

    def pixelate_images(self):
        block_size = self.block_size_scale.get()
        saturation = self.saturation_scale.get()
        remove_background = self.remove_background_var.get()

        # Get selected palette
        selected_palette = next((p["colors"] for p in self.palettes if p["name"] == self.palette_var.get()), None)

        # Progress bar
        self.progress_bar = CustomProgressBar(self.pixelate_window)  # Create instance of CustomProgressBar
        self.progress_bar.update_progress(0, len(self.files))

        # Pixelate images
        for i, file in enumerate(self.files):
            ImageManipulator.pixelate_image(file, block_size, saturation, remove_background, selected_palette)
            # Update progress bar
            self.progress_bar.update_progress(i + 1, len(self.files))
            self.pixelate_window.update_idletasks()
        # Usage
        self.progress_bar.destroy()
        # Re-enable the pixelate button
        self.pixelate_button.config(state=tk.NORMAL)
        export_message(self.files, message="Pixelated images saved successfully.")


def export_message(files, message, dir=None):
    if files:
        if not dir:
            exported_dir = os.path.dirname(files[0])
        else:
            exported_dir = dir

        def open_directory():
            os.startfile(exported_dir)

        custom_box = CustomMessageBox("Success", message, f"{exported_dir}", open_directory)
        custom_box.show()


class ImageManipulator:
    @staticmethod
    def resize_images(files, output_directory, resize_percent):
        resized_directory = output_directory + "/resized_images"
        os.makedirs(resized_directory, exist_ok=True)

        for file in files:
            img = Image.open(file)
            width, height = img.size
            new_width = int(width * resize_percent)
            new_height = int(height * resize_percent)
            resized_img = img.resize((new_width, new_height), Image.NEAREST)
            file_name = os.path.basename(file)
            resized_img.save(f"{resized_directory}/{file_name}")
        export_message(files, message="Images resized and saved successfully.")

    @staticmethod
    def create_spritesheet(files, output_directory):
        MAX_WIDTH = 3000
        MAX_HEIGHT = 6000
        PADDING = 5

        current_x = 0
        current_y = 0
        max_row_height = 0
        total_width = 0

        for file in files:
            img = Image.open(file)
            width, height = img.size

            if current_x + width > MAX_WIDTH:
                current_x = 0
                current_y += max_row_height + PADDING
                max_row_height = 0

            if current_y + height > MAX_HEIGHT:
                messagebox.showwarning("Warning", "Spritesheet maximum size reached. Some images may be cut off.")
                break

            current_x += width + PADDING
            max_row_height = max(max_row_height, height)
            total_width = max(total_width, current_x)

        spritesheet = Image.new("RGBA", (total_width, current_y + max_row_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(spritesheet)

        current_x = 0
        current_y = 0
        max_row_height = 0

        for file in files:
            img = Image.open(file)
            width, height = img.size
            aspect_ratio = width / height

            if current_x + width > MAX_WIDTH:
                current_x = 0
                current_y += max_row_height + PADDING
                max_row_height = 0

            spritesheet.paste(img, (current_x, current_y))
            draw.rectangle([current_x, current_y, current_x + width - 1, current_y + height - 1], outline="black")

            current_x += width + PADDING
            max_row_height = max(max_row_height, height)

        spritesheet_path = output_directory + "/spritesheet.png"
        spritesheet.save(spritesheet_path)
        export_message(files, message="Spritesheet exported successfully.")

    @staticmethod
    def replace_color(files, output_directory, target_color, new_color):
        replaced_directory = output_directory + "/replaced_images"
        os.makedirs(replaced_directory, exist_ok=True)

        for file in files:
            img = Image.open(file)
            img = img.convert("RGBA")
            data = img.getdata()
            newData = []
            for item in data:
                if item[:3] == target_color:
                    newData.append(new_color + (item[3],))
                else:
                    newData.append(item)
            img.putdata(newData)
            file_name = os.path.basename(file)
            img.save(f"{replaced_directory}/{file_name}")
        export_message(files, message="Color replaced and images saved successfully.")

    @staticmethod
    def pixelate_image(image_path, block_size, saturation, remove_background, palette):
        image = Image.open(image_path)
        pixelated_image = ImageManipulator.pixelate(image, block_size, palette)
        pixelated_image = ImageManipulator.adjust_saturation(pixelated_image, saturation)
        if remove_background:
            pixelated_image = ImageManipulator.remove_img_background(pixelated_image)
        output_dir = os.path.join(os.path.dirname(image_path), 'pixelated_images')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, os.path.basename(image_path))
        pixelated_image.save(output_path)

    @staticmethod
    def adjust_saturation(image, saturation):
        if saturation == 0:
            return image
        image = image.convert("HSV")
        data = np.array(image)
        data[:, :, 1] = np.clip(data[:, :, 1] * (1 + saturation / 100), 0, 255)
        return Image.fromarray(data, "HSV").convert("RGB")

    @staticmethod
    def adjust_contrast(image, contrast):
        if contrast == 0:
            return image

        enhancer = ImageEnhance.Contrast(image)
        # Convert contrast from a scale of -100 to 100 to a factor between 0 and 2
        contrast_factor = 1.0 + contrast / 100.0
        return enhancer.enhance(contrast_factor)

    @staticmethod
    def adjust_brightness(image, brightness):
        if brightness == 0:
            return image

        enhancer = ImageEnhance.Brightness(image)
        # Convert brightness from a scale of -100 to 100 to a factor between 0 and 2
        brightness_factor = 1.0 + brightness / 100.0
        return enhancer.enhance(brightness_factor)

    @staticmethod
    def pixelate(image, block_size, palette, resize=True):
        width, height = image.size
        h_blocks = height // block_size
        w_blocks = width // block_size
        new_width = w_blocks * block_size
        new_height = h_blocks * block_size
        image = image.resize((new_width, new_height), resample=Image.NEAREST)
        for j in range(h_blocks):
            for i in range(w_blocks):
                box = (i * block_size, j * block_size, (i + 1) * block_size, (j + 1) * block_size)
                region = image.crop(box)
                average_color = tuple(map(int, np.mean(region, axis=(0, 1))))
                closest = ImageManipulator.closest_color(average_color, palette)
                image.paste(closest, box)
        if resize:
            resize_factor = 1 / block_size
            new_width = int(new_width * resize_factor)
            new_height = int(new_height * resize_factor)
            image = image.resize((new_width, new_height), resample=Image.NEAREST)

        return image

    @staticmethod
    def convert(photoimage):
        return Image(photoimage)

    @staticmethod
    def closest_color(pixel, palette):
        min_dist = float('inf')
        closest = None
        for color in palette:
            dist = np.linalg.norm(np.array(pixel[:3]) - np.array(color))
            if dist < min_dist:
                min_dist = dist
                closest = color
        return closest

    @staticmethod
    def remove_img_background(image):
        image = image.convert("RGBA")
        pixels = image.getdata()
        color_counts = Counter(pixels)
        max_color = color_counts.most_common(1)[0][0]
        return ImageManipulator.remove_color(image, max_color)

    @staticmethod
    def remove_color(image, color):
        newData = []
        pixels = image.getdata()
        for item in pixels:
            if item[:3] == color[:3]:
                newData.append((color[0], color[1], color[2], 0))
            else:
                newData.append(item)
        image.putdata(newData)
        return image


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg=BG_COLOR)  # Dark mode
    app = ImageManipulatorApp(root)
    root.mainloop()
