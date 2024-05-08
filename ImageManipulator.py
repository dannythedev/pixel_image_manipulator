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
    def pixelate_image(image_path, block_size, saturation, remove_background, palette_name, palette,
                       closest_color_cache=None):
        image = Image.open(image_path)

        pixelated_image, updated_cache = ImageManipulator.pixelate(image, block_size, palette_name, palette,
                                                                   closest_color_cache=closest_color_cache)
        pixelated_image = ImageManipulator.adjust_saturation(pixelated_image, saturation)
        if remove_background:
            pixelated_image = ImageManipulator.remove_img_background(pixelated_image)
        output_dir = os.path.join(os.path.dirname(image_path), 'pixelated_images')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, os.path.basename(image_path))
        pixelated_image.save(output_path)

        # Update the original closest_color_cache with the updated_cache
        closest_color_cache.update(updated_cache)

        return closest_color_cache  # Return the updated closest_color_cache dictionary

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
    def process_block(args):
        image, block_coords, palette_name, palette, closest_color_cache = args
        x0, y0, x1, y1 = block_coords

        region = np.array(image.crop((x0, y0, x1, y1)))
        average_color = tuple(np.mean(region, axis=(0, 1)).astype(int))

        if average_color in closest_color_cache[palette_name]:
            closest = closest_color_cache[palette_name][average_color]
            count = 1
        else:
            closest = ImageManipulator.closest_color(average_color, palette)
            closest_color_cache[palette_name][average_color] = closest
            count = 0

        cache_update = {palette_name: {average_color: closest}}
        return block_coords, closest, cache_update, (count, 1 - count)

    @staticmethod
    def pixelate(image, block_size, palette_name, palette, resize=True, closest_color_cache=None):
        start = time.time()
        width, height = image.size
        h_blocks = height // block_size
        w_blocks = width // block_size
        new_image = image.copy()

        block_coords = [(i * block_size, j * block_size, (i + 1) * block_size, (j + 1) * block_size)
                        for j in range(h_blocks) for i in range(w_blocks)]

        palette_cache_updates = defaultdict(dict)
        count1, count2 = 0, 0
        for coords in block_coords:
            args = (image, coords, palette_name, palette, closest_color_cache)
            block_coords, closest, cache_update, counts = ImageManipulator.process_block(args)
            count1 += counts[0]
            count2 += counts[1]
            new_image.paste(closest, block_coords)
            # Accumulate updates for each palette
            palette_cache_updates[palette_name].update(cache_update)
        print(f'{count1}/{count1+count2}')
        # Update the cache for each palette after processing all blocks
        if count2 > 0:
            for palette_name, updates in palette_cache_updates.items():
                closest_color_cache[palette_name].update(updates)

        if resize:
            resize_factor = 1 / block_size
            new_width = int(width * resize_factor)
            new_height = int(height * resize_factor)
            new_image = new_image.resize((new_width, new_height), resample=Image.NEAREST)

        print(abs(start - time.time()))
        return new_image, closest_color_cache

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
