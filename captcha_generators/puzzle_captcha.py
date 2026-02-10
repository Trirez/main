"""
Puzzle Captcha Generator
Two types: Sliding puzzle and Drag-to-position puzzle
Uses Unsplash API for background images with fallback to generated patterns
"""

import random
import io
import base64
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import math

from .unsplash_client import unsplash_client


class PuzzleCaptcha:
    def __init__(self):
        self.puzzle_size = 300
        self.piece_size = 60
        self.use_unsplash = True  # Try to use Unsplash by default
        # Search queries for interesting background images
        self.background_queries = [
            'landscape nature',
            'city street',
            'colorful abstract',
            'architecture building', 
            'forest trees',
            'beach ocean',
            'mountains scenery',
            'flowers garden',
            'sunset sky',
            'urban photography'
        ]
        
    def set_api_key(self, api_key):
        """Set the Unsplash API key"""
        unsplash_client.set_api_key(api_key)
        
    def fetch_unsplash_background(self, size=300):
        """Fetch a background image from Unsplash"""
        if not self.use_unsplash:
            return None
            
        query = random.choice(self.background_queries)
        img = unsplash_client.get_random_image(query=query, size=(size, size))
        return img
        
    def generate_background_image(self, size=300):
        """Generate a colorful abstract background (fallback)"""
        image = Image.new('RGB', (size, size), (100, 150, 200))
        draw = ImageDraw.Draw(image)
        
        # Create gradient background
        for y in range(size):
            for x in range(size):
                r = int(100 + 80 * math.sin(x / 30) + 50 * math.cos(y / 40))
                g = int(120 + 60 * math.cos(x / 25) + 40 * math.sin(y / 35))
                b = int(180 - 30 * math.sin((x + y) / 50))
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                draw.point((x, y), fill=(r, g, b))
        
        # Add some shapes
        for _ in range(5):
            shape_type = random.choice(['circle', 'rectangle'])
            x = random.randint(20, size - 60)
            y = random.randint(20, size - 60)
            w = random.randint(30, 80)
            h = random.randint(30, 80)
            color = (
                random.randint(50, 200),
                random.randint(50, 200),
                random.randint(50, 200),
            )
            if shape_type == 'circle':
                draw.ellipse([x, y, x + w, y + h], fill=color, outline=(255, 255, 255))
            else:
                draw.rectangle([x, y, x + w, y + h], fill=color, outline=(255, 255, 255))
        
        return image
    
    def get_background(self, size=300):
        """Get background image - try Unsplash first, fallback to generated"""
        background = self.fetch_unsplash_background(size)
        if background is None:
            background = self.generate_background_image(size)
        return background
    
    def image_to_base64(self, image):
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
    
    def generate_sliding_puzzle(self):
        """
        Generate a sliding puzzle captcha
        User must slide a piece to the correct position
        """
        # Generate background (Unsplash with fallback to generated)
        background = self.get_background(self.puzzle_size)
        
        # Define puzzle piece position (random y, piece slides horizontally)
        piece_y = random.randint(50, self.puzzle_size - self.piece_size - 50)
        correct_x = random.randint(100, self.puzzle_size - self.piece_size - 50)
        
        # Create the puzzle piece (with puzzle-piece shape)
        piece_img = Image.new('RGBA', (self.piece_size + 20, self.piece_size + 20), (0, 0, 0, 0))
        piece_draw = ImageDraw.Draw(piece_img)
        
        # Draw puzzle piece shape
        # Main square
        piece_draw.rectangle([10, 10, self.piece_size + 10, self.piece_size + 10], 
                            fill=(255, 255, 255, 255))
        # Tab on right
        piece_draw.ellipse([self.piece_size, 25, self.piece_size + 20, 55], 
                          fill=(255, 255, 255, 255))
        
        # Create mask for the piece
        mask = piece_img.split()[3]
        
        # Extract the piece from background
        piece_content = background.crop((correct_x - 10, piece_y - 10, 
                                         correct_x + self.piece_size + 10, 
                                         piece_y + self.piece_size + 10))
        piece_content = piece_content.convert('RGBA')
        
        # Apply mask
        piece_final = Image.new('RGBA', piece_content.size, (0, 0, 0, 0))
        piece_final.paste(piece_content, mask=mask)
        
        # Add shadow to piece
        shadow = Image.new('RGBA', piece_final.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rectangle([10, 10, self.piece_size + 10, self.piece_size + 10], 
                             fill=(0, 0, 0, 80))
        
        # Create the background with hole
        bg_with_hole = background.copy()
        bg_draw = ImageDraw.Draw(bg_with_hole)
        # Draw semi-transparent overlay on the hole
        for x in range(correct_x, correct_x + self.piece_size):
            for y in range(piece_y, piece_y + self.piece_size):
                if 0 <= x < self.puzzle_size and 0 <= y < self.puzzle_size:
                    r, g, b = bg_with_hole.getpixel((x, y))
                    bg_with_hole.putpixel((x, y), (r // 2, g // 2, b // 2))
        
        # Draw hole outline
        bg_draw.rectangle([correct_x, piece_y, 
                          correct_x + self.piece_size, piece_y + self.piece_size],
                         outline=(255, 255, 255), width=2)
        
        return {
            'type': 'sliding',
            'background': self.image_to_base64(bg_with_hole),
            'piece': self.image_to_base64(piece_final),
            'piece_y': piece_y,
            'correct_x': correct_x,
            'tolerance': 10,  # pixels tolerance for correct answer
            'puzzle_width': self.puzzle_size,
            'puzzle_height': self.puzzle_size,
            'piece_size': self.piece_size
        }
    
    def generate_drag_puzzle(self):
        """
        Generate a drag puzzle captcha
        User must drag 3 pieces to their correct positions
        """
        # Generate background (Unsplash with fallback to generated)
        background = self.get_background(self.puzzle_size)
        
        # Define 3 piece positions
        positions = []
        pieces = []
        
        # Create a grid of possible positions
        grid_size = 3
        cell_size = self.puzzle_size // grid_size
        available_cells = [(i, j) for i in range(grid_size) for j in range(grid_size)]
        selected_cells = random.sample(available_cells, 3)
        
        for idx, (grid_x, grid_y) in enumerate(selected_cells):
            # Calculate actual position
            x = grid_x * cell_size + (cell_size - self.piece_size) // 2
            y = grid_y * cell_size + (cell_size - self.piece_size) // 2
            
            positions.append({
                'id': idx,
                'x': x,
                'y': y
            })
            
            # Extract piece from background
            piece_img = background.crop((x, y, x + self.piece_size, y + self.piece_size))
            
            # Add border to piece
            piece_with_border = Image.new('RGB', 
                                         (self.piece_size + 4, self.piece_size + 4), 
                                         (255, 255, 255))
            piece_with_border.paste(piece_img, (2, 2))
            
            pieces.append({
                'id': idx,
                'image': self.image_to_base64(piece_with_border),
                'correct_x': x,
                'correct_y': y
            })
        
        # Create background with holes
        bg_with_holes = background.copy()
        bg_draw = ImageDraw.Draw(bg_with_holes)
        
        for pos in positions:
            x, y = pos['x'], pos['y']
            # Darken the hole area
            for px in range(x, x + self.piece_size):
                for py in range(y, y + self.piece_size):
                    if 0 <= px < self.puzzle_size and 0 <= py < self.puzzle_size:
                        r, g, b = bg_with_holes.getpixel((px, py))
                        bg_with_holes.putpixel((px, py), (r // 3, g // 3, b // 3))
            
            # Draw numbered indicator
            bg_draw.rectangle([x, y, x + self.piece_size, y + self.piece_size],
                             outline=(255, 255, 255), width=2)
            bg_draw.text((x + self.piece_size // 2 - 5, y + self.piece_size // 2 - 8),
                        str(pos['id'] + 1), fill=(255, 255, 255))
        
        # Shuffle pieces order for display
        random.shuffle(pieces)
        
        return {
            'type': 'drag',
            'background': self.image_to_base64(bg_with_holes),
            'pieces': pieces,
            'positions': positions,
            'tolerance': 15,  # pixels tolerance
            'puzzle_width': self.puzzle_size,
            'puzzle_height': self.puzzle_size,
            'piece_size': self.piece_size
        }
    
    def verify_sliding(self, submitted_x, correct_x, tolerance=10):
        """Verify sliding puzzle answer"""
        return abs(submitted_x - correct_x) <= tolerance
    
    def verify_drag(self, submitted_positions, correct_positions, tolerance=15):
        """
        Verify drag puzzle answer
        submitted_positions: list of {id, x, y}
        correct_positions: list of {id, correct_x, correct_y}
        """
        # Check that all pieces are submitted
        if len(submitted_positions) != len(correct_positions):
            return False
        
        correct_map = {p['id']: (p['correct_x'], p['correct_y']) for p in correct_positions}
        
        for submitted in submitted_positions:
            piece_id = submitted['id']
            if piece_id not in correct_map:
                return False
            
            correct_x, correct_y = correct_map[piece_id]
            if abs(submitted['x'] - correct_x) > tolerance or \
               abs(submitted['y'] - correct_y) > tolerance:
                return False
        
        return True

