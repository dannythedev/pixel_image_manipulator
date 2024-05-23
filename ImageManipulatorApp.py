from tkinter.colorchooser import askcolor
from tkinter import filedialog, messagebox
from PIL import Image
import os
import tkinter as tk
from CustomWidgets import ToolTip, CustomDialog
from Functions import BG_COLOR, export_message
from ImageManipulator import ImageManipulator
from PixelateWindow import PixelateWindow


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

        link_label = tk.Label(root, text="About", fg="blue", cursor="hand2",
                              bg=BG_COLOR)
        link_label.place(relx=0.555, rely=0.86, anchor="ne")
        link_label.bind("<Button-1>", lambda event: self.open_about_window())

    def open_about_window(self):
        messagebox.showinfo("About Pixel Image Manipulator", "Pixel Image Manipulator - A tool designed for simplifying\n"
                                           "image manipulation!\n\n"
                                           "- Resize Images: Resize multiple images by specifying the\n  percentage of resizing.\n"
                                           "- Replace Colors: Replace specific colors in images with new\n  ones.\n"
                                           "- Remove Color: Turns a specific color in images transparent.\n"
                                           "- Pixelate: Pixelate images with customizable block size,"
                                           "\n  saturation level, and palette selection.\n\n"
                                           "Developed by dannythedev.")
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
        default_color2 = (0, 0, 153)
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

