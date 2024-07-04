import threading
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import tkinter as tk
import json
from CustomWidgets import CustomProgressBar
from Functions import export_message, BG_COLOR, PALETTES, FG_COLOR
from ImageManipulator import ImageManipulator


class PixelateWindow:
    def __init__(self, root, files):
        self.pixelization = ImageManipulator()
        self.preview_photo = None
        self.files = files
        self.pixelate_window = tk.Toplevel(root)
        self.pixelate_window.title("Pixelation Options")

        self.pixelate_window.configure(bg=BG_COLOR)

        # Initialize the preview area
        self.preview_canvas = tk.Canvas(self.pixelate_window, bg=BG_COLOR, highlightbackground=BG_COLOR, width=200,
                                        height=200)
        self.preview_canvas.grid(row=0, column=1, padx=10, pady=5)
        self.values = {'block_size': 8, 'saturation': 0, 'brightness': 0, 'contrast': 0, 'palette': '',
                       'background': 0}
        self.block_size_label = tk.Label(self.pixelate_window, text="Block Size", bg=BG_COLOR, fg=FG_COLOR)
        self.block_size_label.grid(row=1, column=0, padx=10, pady=5)
        self.block_size_scale = tk.Scale(self.pixelate_window, from_=1, to=20, orient="horizontal", bg=BG_COLOR,
                                         fg=FG_COLOR)
        self.block_size_scale.set(self.values['block_size'])
        self.block_size_scale.grid(row=1, column=1, padx=10, pady=5)
        self.canceled = False



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

        self.progress_bar = None

        # Display sample palettes
        self.palette_var = tk.StringVar()
        self.palette_var.set(PALETTES[0]["name"])  # Default palette
        self.palette_menu = tk.OptionMenu(self.pixelate_window, self.palette_var,
                                          *[palette["name"] for palette in PALETTES])
        self.palette_menu.grid(row=5, column=1, padx=10, pady=5)
        self.palette_menu.configure(bg=BG_COLOR, fg=FG_COLOR)
        self.palette_dropdown = tk.Menu(self.palette_menu, tearoff=0, bg=BG_COLOR, fg=FG_COLOR)
        self.palette_menu.configure(menu=self.palette_dropdown)
        self.initial = False

        # Add palettes to the dropdown menu
        for palette in PALETTES:
            self.add_palette_to_menu(palette)

        self.remove_background_var = tk.IntVar()
        self.remove_background_checkbutton = tk.Checkbutton(self.pixelate_window, text="Remove Background",
                                                            variable=self.remove_background_var,
                                                            onvalue=1, offvalue=0, bg=BG_COLOR, fg=FG_COLOR,
                                                            selectcolor="black")
        self.remove_background_checkbutton.grid(row=7, column=1)
        self.remove_background_checkbutton.select()

        self.pixelate_button = tk.Button(self.pixelate_window, text="Pixelate",
                                         bg="#17a2b8", fg="white", relief="flat", padx=10,
                                         command=self.start_pixelation_thread)
        self.pixelate_button.grid(row=7, column=2, columnspan=1, padx=10, pady=5, sticky="n")

        self.browse_button = tk.Button(self.pixelate_window, text="Browse",
                                       bg="#ccbb00", fg="white", relief="flat", padx=10,
                                       command=self.choose_images)
        self.browse_button.grid(row=6, column=2, columnspan=1, pady=5, padx=5, sticky="s")

        # Add Export Settings button
        self.export_settings_button = tk.Button(self.pixelate_window, text="Export Settings",
                                                bg="#28a745", fg="white", relief="flat", padx=10,
                                                command=self.export_settings)
        self.export_settings_button.grid(row=6, column=0, pady=5, padx=5, sticky="s")

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
        self.pixelate_button.config(state="disabled")

    def choose_images(self):
        self.files = filedialog.askopenfilenames(filetypes=[("PNG files", "*.png")])
        self.update_preview()

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
        # Load the first chosen exported image
        if self.files:
            first_image_path = self.files[0]
            image = Image.open(first_image_path)

            # Get parameters
            block_size = self.block_size_scale.get()
            saturation = self.saturation_scale.get()
            brightness = self.brightness_scale.get()
            contrast = self.contrast_scale.get()
            background = self.remove_background_var.get()

            selected_palette = next((p["colors"] for p in PALETTES if p["name"] == self.palette_var.get()), None)
            # if self.values['block_size'] != block_size or self.values['palette'] != selected_palette:
            # Pixelate the image
            if self.initial:
                self.preview_photo = self.pixelization.pixelate(image, block_size, self.palette_var.get(), selected_palette,
                                                   resize=False)
                self.preview_photo = self.pixelization.adjust_saturation(self.preview_photo, saturation)
                self.preview_photo = self.pixelization.adjust_brightness(self.preview_photo, brightness)
                self.preview_photo = self.pixelization.adjust_contrast(self.preview_photo, contrast)
            else:
                # Convert the PIL Image to a Tkinter PhotoImage
                self.preview_photo = image
                self.initial = True

            # Resize the image to fit within the maximum width and height while maintaining aspect ratio
            self.preview_photo.thumbnail((300, 300))
            width, height = self.preview_photo.size

            self.preview_photo = ImageTk.PhotoImage(self.preview_photo)

            # Update the preview canvas
            self.preview_canvas.delete("all")

            self.preview_canvas.config(width=width,
                                       height=height)
            self.preview_canvas.create_image(0, 0, anchor="nw", image=self.preview_photo)

            self.values = {'block_size': block_size, 'saturation': saturation, 'brightness': brightness,
                           'contrast': contrast,
                           'palette': next((p["name"] for p in PALETTES if p["name"] == self.palette_var.get()),
                                           None),
                           'background': background}
        self.pixelate_button.config(state="normal")

    def print_canvas_dimensions(self):
        print(self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height())

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
        self.disable_buttons("disabled")
        self.canceled = False
        # Start a new thread for pixelation
        threading.Thread(target=self.pixelate_images).start()

    def pixelate_images(self):
        block_size = self.block_size_scale.get()
        saturation = self.saturation_scale.get()
        remove_background = self.remove_background_var.get()

        # Get selected palette
        selected_palette = next((p["colors"] for p in PALETTES if p["name"] == self.palette_var.get()), None)

        # Progress bar
        self.progress_bar = CustomProgressBar(self.pixelate_window, self.cancel_pixelation)  # Pass cancel handler
        self.progress_bar.update_progress(0, len(self.files))

        # Disable the pixelate button
        self.pixelate_button.config(state=tk.DISABLED)

        # Pixelate images
        for i, file in enumerate(self.files):
            if self.canceled:
                break
            self.pixelate_image(file, block_size, saturation, remove_background,
                                self.palette_var.get(), selected_palette)
            # Update progress bar
            self.progress_bar.update_progress(i + 1, len(self.files))
            self.pixelate_window.update_idletasks()

        # Cleanup
        self.disable_buttons("normal")
        self.progress_bar.destroy()
        self.canceled = False  # Reset cancel flag
        self.pixelate_button.config(state=tk.NORMAL)
        export_message(self.files, message="Pixelated images saved successfully.")

    def cancel_pixelation(self):
        self.canceled = True

    def pixelate_image(self, image_path, block_size, saturation, remove_background, palette_name, palette):
        image = Image.open(image_path)

        # Directory
        output_dir = os.path.join(os.path.dirname(image_path), 'pixelated_images')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, os.path.basename(image_path))

        if remove_background:
            image = ImageManipulator.remove_img_background(image)
        pixelated_image = self.pixelization.pixelate(image, block_size, palette_name, palette)
        pixelated_image = self.pixelization.adjust_saturation(pixelated_image, saturation)
        pixelated_image.save(output_path)

    def disable_buttons(self, state):
        self.pixelate_button.config(state=state)
        self.browse_button.config(state=state)
        self.export_settings_button.config(state=state)
        self.load_settings_button.config(state=state)
