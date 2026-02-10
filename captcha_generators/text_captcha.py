"""
Text Captcha Generator
Generates distorted text images for captcha verification
"""

import random
import string
import io
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter


class TextCaptcha:
    def __init__(self, width=280, height=90):
        self.width = width
        self.height = height
        self.characters = string.ascii_uppercase + string.digits
        # Remove confusing characters
        self.characters = self.characters.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
    
    def generate_text(self, length=6):
        """Generate random captcha text"""
        return ''.join(random.choices(self.characters, k=length))
    
    def generate_image(self, text):
        """Generate captcha image with distorted text"""
        # Create image with gradient background
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Add gradient background
        for y in range(self.height):
            r = int(240 + (15 * y / self.height))
            g = int(240 + (15 * y / self.height))
            b = int(250 - (10 * y / self.height))
            for x in range(self.width):
                draw.point((x, y), fill=(r, g, b))
        
        # Add noise lines
        for _ in range(random.randint(4, 8)):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            color = (random.randint(100, 180), random.randint(100, 180), random.randint(100, 180))
            draw.line([(x1, y1), (x2, y2)], fill=color, width=1)
        
        # Add noise dots
        for _ in range(random.randint(100, 200)):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
            draw.point((x, y), fill=color)
        
        # Draw text characters with random positioning and colors
        try:
            font = ImageFont.truetype("arial.ttf", random.randint(38, 48))
        except:
            font = ImageFont.load_default()
        
        char_width = self.width // (len(text) + 1)
        
        for i, char in enumerate(text):
            x = char_width * (i + 0.5) + random.randint(-5, 5)
            y = random.randint(10, 30)
            
            # Random dark color for each character
            color = (random.randint(0, 80), random.randint(0, 80), random.randint(80, 150))
            
            # Create a temporary image for rotation
            char_img = Image.new('RGBA', (60, 70), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((10, 10), char, font=font, fill=color)
            
            # Rotate character
            angle = random.randint(-25, 25)
            char_img = char_img.rotate(angle, expand=True, resample=Image.BICUBIC)
            
            # Paste onto main image
            image.paste(char_img, (int(x), int(y)), char_img)
        
        # Apply slight blur
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        return image
    
    def generate(self, length=6):
        """Generate captcha text and image, return base64 encoded image and text"""
        text = self.generate_text(length)
        image = self.generate_image(text)
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            'text': text,
            'image': f'data:image/png;base64,{image_base64}'
        }
