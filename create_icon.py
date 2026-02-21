#!/usr/bin/env python
"""
Icon Generator for Web Video Downloader
Creates a simple application icon using PIL/Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    """Create a simple application icon for the Web Video Downloader."""
    
    print("Creating application icon...")
    
    # Create a 256x256 image with a transparent background
    icon_size = 256
    icon = Image.new('RGBA', (icon_size, icon_size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # Draw a rounded rectangle as background
    background_color = (65, 105, 225)  # Royal Blue
    draw.rounded_rectangle([(20, 20), (icon_size-20, icon_size-20)], 
                          radius=30, 
                          fill=background_color)
    
    # Draw a play button triangle
    play_color = (255, 255, 255)  # White
    triangle_points = [
        (icon_size//2 - 10, icon_size//2 - 40),  # Top
        (icon_size//2 - 10, icon_size//2 + 40),  # Bottom
        (icon_size//2 + 40, icon_size//2)        # Right
    ]
    draw.polygon(triangle_points, fill=play_color)
    
    # Draw a download arrow
    arrow_color = (255, 255, 255)  # White
    # Arrow shaft
    draw.rectangle([(icon_size//2 - 10, icon_size//2 + 50), 
                   (icon_size//2 + 10, icon_size//2 + 90)], 
                  fill=arrow_color)
    # Arrow head
    arrow_head = [
        (icon_size//2 - 30, icon_size//2 + 90),  # Left
        (icon_size//2 + 30, icon_size//2 + 90),  # Right
        (icon_size//2, icon_size//2 + 120)       # Bottom
    ]
    draw.polygon(arrow_head, fill=arrow_color)
    
    # Save as .ico file
    icon_path = 'app_icon.ico'
    
    # For .ico format, we need to save as PNG first, then convert
    png_path = 'app_icon.png'
    icon.save(png_path)
    
    # Try to use PIL's built-in ICO support
    try:
        # Create different sizes for the ICO file
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        icon_images = []
        
        for size in sizes:
            resized_img = icon.resize(size, Image.LANCZOS)
            icon_images.append(resized_img)
        
        # Save the icon with multiple sizes
        icon_images[0].save(
            icon_path, 
            format='ICO', 
            sizes=[(img.width, img.height) for img in icon_images],
            append_images=icon_images[1:]
        )
        print(f"Icon saved to {os.path.abspath(icon_path)}")
    except Exception as e:
        # Fallback: just save the PNG
        print(f"Could not create ICO file: {e}")
        print(f"PNG icon saved to {os.path.abspath(png_path)} instead")
        print("You'll need to convert this to ICO format manually.")

if __name__ == "__main__":
    try:
        create_app_icon()
    except ImportError:
        print("Error: This script requires the Pillow library.")
        print("Install it with: pip install Pillow")
