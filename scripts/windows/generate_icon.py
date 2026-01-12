#!/usr/bin/env python3
"""
Generate a simple icon for the Lens system tray application.
This script creates a simple icon with an "L" letter on a colored background.
Run this once to generate the icon file, then commit it to git.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create a 64x64 image with a purple/indigo background (common for Lens/tech apps)
size = (64, 64)
img = Image.new('RGB', size, color='#4F46E5')  # Indigo color
draw = ImageDraw.Draw(img)

# Draw a circle background
draw.ellipse([2, 2, 61, 61], fill='#6366F1', outline='#4338CA', width=2)

# Try to use a larger font, fallback to default
try:
    # Try to load a truetype font (adjust path as needed)
    font_size = 40
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
except:
    font = ImageFont.load_default()

# Draw "L" letter in white, centered
text = "L"
# Calculate text position to center it
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
position = ((size[0] - text_width) // 2 - bbox[0], (size[1] - text_height) // 2 - bbox[1])

draw.text(position, text, fill='white', font=font)

# Save as PNG
output_path = os.path.join(os.path.dirname(__file__), 'lens_icon.png')
img.save(output_path)
print(f"Icon generated successfully: {output_path}")

# Also create a smaller 32x32 version for better tray icon display
img_small = img.resize((32, 32), Image.Resampling.LANCZOS)
output_path_small = os.path.join(os.path.dirname(__file__), 'lens_icon_32.png')
img_small.save(output_path_small)
print(f"Small icon generated: {output_path_small}")
