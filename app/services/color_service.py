
"""
app/services/color_service.py
-----------------------------

This service is responsible for extracting the dominant color from an image.
It uses the Pillow library to open an image, resize it to a single pixel
to get the average color, and then returns that color as a hex string.
A simple in-memory cache is used to avoid reprocessing the same image.
"""

from PIL import Image
import os
from functools import lru_cache

class ColorService:
    """A service to extract dominant colors from images."""

    @staticmethod
    @lru_cache(maxsize=128)
    def get_dominant_color(image_path: str) -> str:
        """
        Get the dominant color of an image as a hex string.

        Args:
            image_path: The absolute path to the image file.

        Returns:
            The dominant color as a hex string (e.g., '#RRGGBB').
            Returns a default color if the image cannot be processed.
        """
        if not os.path.exists(image_path):
            return '#FFFFFF'  # Return white if image not found

        try:
            with Image.open(image_path) as img:
                # Convert to RGB if it's not
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to 1x1 to get the average color
                img.thumbnail((1, 1))
                dominant_color = img.getpixel((0, 0))
                
                return f'#{dominant_color[0]:02x}{dominant_color[1]:02x}{dominant_color[2]:02x}'
        except Exception:
            return '#FFFFFF'  # Return white on error
