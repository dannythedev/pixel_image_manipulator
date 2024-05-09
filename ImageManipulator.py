import time
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageEnhance
import numpy as np
import os
from collections import Counter
from Functions import export_message
from collections import defaultdict

class ImageManipulator:
    def __init__(self):
        self.closest_color_cache = defaultdict(dict)
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
    def remove_img_background(image):
        image = image.convert("RGBA")
        pixels = image.getdata()
        color_counts = Counter(pixels)
        max_color = color_counts.most_common(1)[0][0]
        return ImageManipulator.remove_color(image, max_color)

    @staticmethod
    def closest_color(pixel, palette):
        pixel_rgb = np.array(pixel[:3])
        palette_array = np.array(palette)

        # Compute Euclidean distances between the pixel and all colors in the palette
        distances = np.linalg.norm(palette_array - pixel_rgb, axis=1)
        # Find the index of the color with the minimum distance
        closest_index = np.argmin(distances)
        # Retrieve the closest color from the palette
        closest = palette[closest_index]

        return closest

    @staticmethod
    def _encode_color(color):
        # Encode the color as a unique integer
        return (color[0] << 16) + (color[1] << 8) + color[2]

    def process_block(self, average_colors_list, palette_name, palette):
        closest_colors_list = []
        count1, count2 = 0, 0

        # Retrieve the cache dictionary for the given palette_name
        palette_cache = self.closest_color_cache[palette_name]

        for average_color in average_colors_list:
            encoded_color = self._encode_color(average_color)
            cached_closest = palette_cache.get(encoded_color)
            if cached_closest:
                closest = cached_closest
                count1 += 1
            else:
                closest = ImageManipulator.closest_color(average_color, palette)
                palette_cache[encoded_color] = closest
                count2 += 1
            closest_colors_list.append(closest)

        return closest_colors_list, (count1, count2)

    def pixelate(self, image, block_size, palette_name, palette, resize=True):
        # start = time.time()
        width, height = image.size
        h_blocks = height // block_size
        w_blocks = width // block_size

        block_coords = [(i * block_size, j * block_size, (i + 1) * block_size, (j + 1) * block_size)
                        for j in range(h_blocks) for i in range(w_blocks)]

        average_colors = []
        for coords in block_coords:
            region = np.array(image.crop(coords))
            average_color = tuple(np.mean(region, axis=(0, 1)).astype(int))
            average_colors.append(average_color)

        closest_colors, (count1, count2) = self.process_block(average_colors, palette_name, palette)

        for closest, coords in zip(closest_colors, block_coords):
            image.paste(closest, coords)

        print(f'{count1}/{count1 + count2}')

        if resize:
            resize_factor = 1 / block_size
            new_width = int(width * resize_factor)
            new_height = int(height * resize_factor)
            image = image.resize((new_width, new_height), resample=Image.NEAREST)

        # print(abs(start - time.time()))
        return image