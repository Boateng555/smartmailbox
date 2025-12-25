#!/usr/bin/env python3
"""
Generate PWA icons for Smart Camera IoT Platform.
Requires Pillow: pip install Pillow
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
except ImportError:
    print("Please install Pillow: pip install Pillow")
    exit(1)

def create_icon(size, filename):
    """Create an icon with the specified size."""
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw a circle in the center
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill='white',
        outline='#764ba2',
        width=max(2, size // 64)
    )
    
    # Draw camera icon (simplified)
    center = size // 2
    camera_size = size // 3
    
    # Camera body
    body_left = center - camera_size // 2
    body_top = center - camera_size // 3
    body_right = center + camera_size // 2
    body_bottom = center + camera_size // 2
    draw.rectangle(
        [body_left, body_top, body_right, body_bottom],
        fill='#667eea',
        outline='#764ba2',
        width=max(2, size // 128)
    )
    
    # Camera lens
    lens_size = camera_size // 2
    lens_left = center - lens_size // 2
    lens_top = center - lens_size // 4
    lens_right = center + lens_size // 2
    lens_bottom = center + lens_size // 2
    draw.ellipse(
        [lens_left, lens_top, lens_right, lens_bottom],
        fill='#1a1a2e',
        outline='#764ba2',
        width=max(1, size // 256)
    )
    
    # Flash
    flash_left = center + camera_size // 3
    flash_top = center - camera_size // 3
    flash_right = center + camera_size // 2 - (camera_size // 8)
    flash_bottom = center - camera_size // 4
    if flash_right > flash_left and flash_bottom > flash_top:
        draw.rectangle(
            [flash_left, flash_top, flash_right, flash_bottom],
            fill='white'
        )
    
    img.save(filename)
    print(f"Created {filename} ({size}x{size})")

if __name__ == '__main__':
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create icons
    create_icon(192, os.path.join(script_dir, 'icon-192x192.png'))
    create_icon(512, os.path.join(script_dir, 'icon-512x512.png'))
    
    print("\nIcons generated successfully!")
    print("Files created:")
    print("  - icon-192x192.png")
    print("  - icon-512x512.png")

