"""
Image Selection Captcha Generator
Displays 3 images and asks user to select the correct one(s)
Uses Unsplash API for real images with fallback to generated shapes
"""

import random
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import os

from .unsplash_client import unsplash_client


class ImageCaptcha:
    def __init__(self):
        # Define image categories with search queries for Unsplash
        self.categories = {
            'car': {'emoji': '🚗', 'query': 'car vehicle', 'colors': [(220, 50, 50), (50, 50, 220), (50, 180, 50)]},
            'tree': {'emoji': '🌳', 'query': 'tree nature', 'colors': [(34, 139, 34), (46, 139, 87), (0, 100, 0)]},
            'house': {'emoji': '🏠', 'query': 'house building', 'colors': [(139, 69, 19), (160, 82, 45), (205, 133, 63)]},
            'sun': {'emoji': '☀️', 'query': 'sunset sunshine', 'colors': [(255, 200, 0), (255, 165, 0), (255, 215, 0)]},
            'mountain': {'emoji': '⛰️', 'query': 'mountain landscape', 'colors': [(105, 105, 105), (128, 128, 128), (169, 169, 169)]},
            'flower': {'emoji': '🌸', 'query': 'flower bloom', 'colors': [(255, 182, 193), (255, 105, 180), (255, 20, 147)]},
            'ocean': {'emoji': '🌊', 'query': 'ocean sea waves', 'colors': [(0, 119, 190), (0, 105, 148), (0, 77, 128)]},
            'dog': {'emoji': '🐕', 'query': 'dog pet', 'colors': [(139, 90, 43), (160, 120, 60), (180, 140, 80)]},
            'cat': {'emoji': '🐱', 'query': 'cat kitten', 'colors': [(128, 128, 128), (255, 165, 0), (60, 60, 60)]},
            'bird': {'emoji': '🐦', 'query': 'bird wildlife', 'colors': [(135, 206, 250), (255, 99, 71), (50, 205, 50)]},
        }
        self.use_unsplash = False  # Use generated images by default (faster)
        
    def set_api_key(self, api_key):
        """Set the Unsplash API key"""
        unsplash_client.set_api_key(api_key)
        
    def fetch_unsplash_image(self, category, size=120):
        """Fetch an image from Unsplash for the given category"""
        if not self.use_unsplash:
            return None
            
        query = self.categories[category].get('query', category)
        images = unsplash_client.get_images_by_query(query, count=1, size=(size, size))
        return images[0] if images else None
        
    def generate_category_image(self, category, size=120):
        """Generate a simple representative image for a category"""
        colors = self.categories[category]['colors']
        color = random.choice(colors)
        
        image = Image.new('RGB', (size, size), (245, 245, 250))
        draw = ImageDraw.Draw(image)
        
        if category == 'car':
            # Draw a simple car
            draw.rectangle([20, 50, 100, 80], fill=color)
            draw.rectangle([35, 30, 85, 55], fill=color)
            draw.ellipse([25, 70, 45, 90], fill=(30, 30, 30))
            draw.ellipse([75, 70, 95, 90], fill=(30, 30, 30))
            
        elif category == 'tree':
            # Draw a simple tree
            draw.rectangle([50, 70, 70, 110], fill=(139, 69, 19))
            draw.polygon([(60, 20), (20, 75), (100, 75)], fill=color)
            
        elif category == 'house':
            # Draw a simple house
            draw.rectangle([25, 55, 95, 105], fill=color)
            draw.polygon([(60, 20), (15, 60), (105, 60)], fill=(150, 75, 25))
            draw.rectangle([50, 70, 70, 105], fill=(100, 60, 30))
            draw.rectangle([30, 65, 45, 80], fill=(135, 206, 235))
            draw.rectangle([75, 65, 90, 80], fill=(135, 206, 235))
            
        elif category == 'sun':
            # Draw a simple sun
            draw.ellipse([35, 35, 85, 85], fill=color)
            for angle in range(0, 360, 45):
                import math
                x1 = 60 + 35 * math.cos(math.radians(angle))
                y1 = 60 + 35 * math.sin(math.radians(angle))
                x2 = 60 + 50 * math.cos(math.radians(angle))
                y2 = 60 + 50 * math.sin(math.radians(angle))
                draw.line([(x1, y1), (x2, y2)], fill=color, width=3)
                
        elif category == 'mountain':
            # Draw a simple mountain
            draw.polygon([(60, 20), (10, 100), (110, 100)], fill=color)
            draw.polygon([(60, 20), (45, 40), (75, 40)], fill=(255, 255, 255))
            
        elif category == 'flower':
            # Draw a simple flower
            draw.ellipse([50, 70, 70, 100], fill=(34, 139, 34))  # stem
            draw.rectangle([58, 70, 62, 100], fill=(34, 139, 34))
            for i in range(5):
                import math
                cx = 60 + 20 * math.cos(math.radians(i * 72 - 90))
                cy = 50 + 20 * math.sin(math.radians(i * 72 - 90))
                draw.ellipse([cx-12, cy-12, cx+12, cy+12], fill=color)
            draw.ellipse([50, 40, 70, 60], fill=(255, 255, 0))
        
        # Add some texture/noise
        for _ in range(50):
            x = random.randint(0, size-1)
            y = random.randint(0, size-1)
            r, g, b = image.getpixel((x, y))
            variation = random.randint(-15, 15)
            new_color = (
                max(0, min(255, r + variation)),
                max(0, min(255, g + variation)),
                max(0, min(255, b + variation))
            )
            draw.point((x, y), fill=new_color)
        
        return image
    
    def image_to_base64(self, image):
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
    
    def generate(self):
        """Generate image captcha with 9 images in a 3x3 grid, 3 being correct answers"""
        categories = list(self.categories.keys())
        
        # Select target category
        target_category = random.choice(categories)
        
        # Select categories for wrong images (need 6 wrong categories)
        wrong_categories = [c for c in categories if c != target_category]
        # If we don't have enough unique wrong categories, allow repeats
        if len(wrong_categories) >= 6:
            selected_wrong = random.sample(wrong_categories, 6)
        else:
            selected_wrong = wrong_categories.copy()
            while len(selected_wrong) < 6:
                selected_wrong.append(random.choice(wrong_categories))
        
        # Create 9 images - 3 correct, 6 wrong
        # Randomly assign which positions get correct images
        correct_indices = random.sample(range(9), 3)
        
        images = []
        wrong_idx = 0
        
        for i in range(9):
            if i in correct_indices:
                cat = target_category
                is_correct = True
            else:
                cat = selected_wrong[wrong_idx]
                wrong_idx += 1
                is_correct = False
            
            # Try Unsplash first, fallback to generated image
            img = self.fetch_unsplash_image(cat)
            if img is None:
                img = self.generate_category_image(cat)
                
            images.append({
                'image': self.image_to_base64(img),
                'category': cat,
                'is_correct': is_correct,
                'index': i
            })
        
        return {
            'target': target_category,
            'prompt': f"Select all images containing a {target_category}",
            'images': images,
            'correct_indices': sorted(correct_indices),
            'required_selections': 3
        }

