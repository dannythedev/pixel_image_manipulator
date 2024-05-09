import time
from multiprocessing import Pool
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageEnhance
import numpy as np
import os
from collections import Counter
from Functions import export_message
from collections import defaultdict

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
