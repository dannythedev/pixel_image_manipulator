import threading
import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter import filedialog, messagebox, simpledialog
from tkinter.ttk import Progressbar

from PIL import Image, ImageDraw
import numpy as np
import os
from collections import Counter

class ImageManipulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Manipulator")

        self.frame = tk.Frame(root)
        self.frame.pack(padx=20, pady=20)

        self.btn_select_images = tk.Button(self.frame, text="Resize Images", command=self.resize_images_option)
        self.btn_select_images.grid(row=1, column=0, pady=10)

        self.btn_select_spritesheet = tk.Button(self.frame, text="Make Spritesheet", command=self.create_spritesheet_option)
        self.btn_select_spritesheet.grid(row=1, column=1, pady=10)

        self.btn_select_colors = tk.Button(self.frame, text="Replace Colors", command=self.select_colors)
        self.btn_select_colors.grid(row=2, column=0, columnspan=1, pady=10)

        self.btn_select_images = tk.Button(self.frame, text="Pixelate", command=self.pixelate_images_option)
        self.btn_select_images.grid(row=2, column=1, columnspan=2, pady=10)

    def resize_images_option(self):
        files = filedialog.askopenfilenames(filetypes=[("PNG files", "*.png")])
        if files:
            directory = os.path.dirname(files[0])
            resize_percent_str = simpledialog.askstring("Input", "Enter Resize Percentage (%):", parent=self.root)
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
        default_color2 = (153, 251, 87)
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

class PixelateWindow:
    def __init__(self, root, files):
        self.files = files
        self.pixelate_window = tk.Toplevel(root)
        self.pixelate_window.title("Pixelation Options")

        self.block_size_label = tk.Label(self.pixelate_window, text="Block Size")
        self.block_size_label.grid(row=0, column=0, padx=10, pady=5)
        self.block_size_scale = tk.Scale(self.pixelate_window, from_=1, to=20, orient="horizontal")
        self.block_size_scale.set(4)
        self.block_size_scale.grid(row=0, column=1, padx=10, pady=5)

        self.saturation_label = tk.Label(self.pixelate_window, text="Saturation Level")
        self.saturation_label.grid(row=1, column=0, padx=10, pady=5)
        self.saturation_scale = tk.Scale(self.pixelate_window, from_=-100, to=100, orient="horizontal")
        self.saturation_scale.set(-25)
        self.saturation_scale.grid(row=1, column=1, padx=10, pady=5)

        self.palette_label = tk.Label(self.pixelate_window, text="Select Palette:")
        self.palette_label.grid(row=2, column=0, padx=10, pady=5)

        # Define sample palettes
        # Define sample palettes
        self.palettes = [
            [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
             (128, 128, 128), (32, 32, 32), (64, 64, 64), (192, 192, 192), (244, 244, 244), (128, 0, 0), (128, 128, 0),
             (0, 128, 0), (128, 0, 128), (0, 128, 128), (0, 0, 128), (255, 128, 0), (128, 255, 0), (0, 255, 128),
             (0, 128, 255), (128, 0, 255), (255, 0, 128), (255, 128, 128), (128, 255, 128), (128, 128, 255), (255, 255, 128),
             (255, 128, 255), (128, 255, 255), (192, 192, 192), (128, 64, 0), (128, 0, 64), (64, 0, 128), (0, 64, 128),
             (0, 128, 64), (64, 128, 0)],
            [(140, 143, 174), (88, 69, 99), (62, 33, 55), (154, 99, 72), (215, 155, 125), (245, 237, 186),
             (192, 199, 65), (100, 125, 52), (228, 148, 58), (157, 48, 59), (210, 100, 113), (112, 55, 127),
             (126, 196, 193), (52, 133, 157), (23, 67, 75), (31, 14, 28)],
            [(26, 28, 44), (93, 39, 93), (177, 62, 83), (239, 125, 87), (255, 205, 117), (167, 240, 112),
             (56, 183, 100), (37, 113, 121), (41, 54, 111), (59, 93, 201), (65, 166, 246), (115, 239, 247),
             (244, 244, 244), (148, 176, 194), (86, 108, 134), (51, 60, 87)]
        ]


        # Display sample palettes
        self.palette_var = tk.StringVar()
        self.palette_var.set("Palette 1")  # Default palette
        self.palette_menu = tk.OptionMenu(self.pixelate_window, self.palette_var, *["Palette "+str(i+1) for i in range(len(self.palettes))])
        self.palette_menu.grid(row=2, column=1, padx=10, pady=5)

        self.palette_dropdown = tk.Menu(self.palette_menu, tearoff=0)
        self.palette_menu.configure(menu=self.palette_dropdown)

        # Add palettes to the dropdown menu
        for i, palette in enumerate(self.palettes):
            palette_name = "Palette " + str(i + 1)
            self.add_palette_to_menu(palette_name, palette)

        self.remove_background_var = tk.IntVar()
        self.remove_background_checkbutton = tk.Checkbutton(self.pixelate_window, text="Remove Background",
                                                             variable=self.remove_background_var,
                                                             onvalue=1, offvalue=0)
        self.remove_background_checkbutton.select()
        self.remove_background_checkbutton.grid(row=3, column=0, columnspan=2, pady=5)

        self.pixelate_button = tk.Button(self.pixelate_window, text="Pixelate",
                                         command=self.start_pixelation_thread)
        self.pixelate_button.grid(row=4, column=0, columnspan=2, pady=10)

    def add_palette_to_menu(self, palette_name, palette):
        # Create a menu item for the palette
        palette_menu = tk.Menu(self.palette_dropdown, tearoff=0)

        # Create a frame for each palette to display colors horizontally
        palette_frame = tk.Frame(palette_menu, relief='raised', borderwidth=1)
        palette_frame.pack()

        # Add colors to the frame
        for color in palette:
            color_hex = '#%02x%02x%02x' % color
            color_button = tk.Button(palette_frame, bg=color_hex, width=2, height=1)
            color_button.pack(side='left', padx=1, pady=1)
            color_button.bind('<Button-1>', lambda event, p=palette_name: self.select_palette(p))

        # Add a command to the menu item to select the palette
        palette_menu.add_command(label='Choose', command=lambda p=palette_name: self.select_palette(p))
        self.palette_dropdown.add_cascade(label=palette_name, menu=palette_menu)
        for color in palette:
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
        selected_palette_index = int(self.palette_var.get().split(" ")[1]) - 1
        selected_palette = self.palettes[selected_palette_index]

        # Progress bar
        self.progress_bar = Progressbar(self.pixelate_window, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

        # Initialize progress bar
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = len(self.files)

        # Pixelate images
        for i, file in enumerate(self.files):
            ImageManipulator.pixelate_image(file, block_size, saturation, remove_background, selected_palette)
            # Update progress bar
            self.progress_bar['value'] = i + 1
            self.pixelate_window.update_idletasks()
        messagebox.showinfo("Success", f"Pixelated image saved successfully.")
        self.progress_bar.destroy()
        # Re-enable the pixelate button
        self.pixelate_button.config(state=tk.NORMAL)

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

        messagebox.showinfo("Success", "Images resized and saved successfully.")

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
            aspect_ratio = width / height

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

        messagebox.showinfo("Success", f"Spritesheet saved as {spritesheet_path}")

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

        messagebox.showinfo("Success", "Color replaced and images saved successfully.")

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
    def pixelate(image, block_size, palette):
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

        resize_factor = 1 / block_size
        new_width = int(new_width * resize_factor)
        new_height = int(new_height * resize_factor)
        image = image.resize((new_width, new_height), resample=Image.NEAREST)

        return image

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
        newData = []
        for item in pixels:
            if item == max_color:
                newData.append((max_color[0], max_color[1], max_color[2], 0))
            else:
                newData.append(item)
        image.putdata(newData)
        return image


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageManipulatorApp(root)
    root.mainloop()
