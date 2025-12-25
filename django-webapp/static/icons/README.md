# PWA Icons

This directory should contain the following icon files for the Progressive Web App:

- `icon-192x192.png` - 192x192 pixels
- `icon-512x512.png` - 512x512 pixels

## Creating Icons

You can create these icons using any image editing software. The icons should:
- Be square (1:1 aspect ratio)
- Have a transparent or solid background
- Represent the Smart Camera IoT Platform
- Be optimized for mobile devices

### Quick Generation Script

Run the following Python script to generate placeholder icons:

```python
from PIL import Image, ImageDraw

# Create 192x192 icon
img192 = Image.new('RGB', (192, 192), color='#667eea')
draw = ImageDraw.Draw(img192)
draw.ellipse([20, 20, 172, 172], fill='white')
draw.text((60, 70), '📷', font_size=60)
img192.save('icon-192x192.png')

# Create 512x512 icon
img512 = Image.new('RGB', (512, 512), color='#667eea')
draw = ImageDraw.Draw(img512)
draw.ellipse([50, 50, 462, 462], fill='white')
draw.text((180, 200), '📷', font_size=200)
img512.save('icon-512x512.png')
```

Or use an online icon generator like:
- https://realfavicongenerator.net/
- https://www.pwabuilder.com/imageGenerator







