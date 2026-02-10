"""
Image Cache Manager
Stores and retrieves cached images to reduce Unsplash API calls
"""

import os
import random
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image


class ImageCache:
    def __init__(self, cache_dir=None, max_images_per_category=20, cache_expiry_days=7):
        """
        Initialize the image cache manager
        
        Args:
            cache_dir: Directory to store cached images (default: ./image_cache)
            max_images_per_category: Maximum images to keep per category
            cache_expiry_days: Days before cached images are considered stale
        """
        if cache_dir is None:
            # Default to image_cache folder in project root
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image_cache')
        
        self.cache_dir = Path(cache_dir)
        self.max_images_per_category = max_images_per_category
        self.cache_expiry_days = cache_expiry_days
        self.metadata_file = self.cache_dir / 'cache_metadata.json'
        
        # Ensure cache directory exists
        self._ensure_cache_dir()
        
        # Load metadata
        self.metadata = self._load_metadata()
        
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_category_dir(self, category):
        """Get the directory path for a specific category"""
        # Sanitize category name for filesystem
        safe_category = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in category)
        category_dir = self.cache_dir / safe_category
        category_dir.mkdir(parents=True, exist_ok=True)
        return category_dir
        
    def _load_metadata(self):
        """Load cache metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {'categories': {}, 'last_cleanup': None}
        return {'categories': {}, 'last_cleanup': None}
        
    def _save_metadata(self):
        """Save cache metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving cache metadata: {e}")
            
    def get_cached_images(self, category, count=1, size=None):
        """
        Get random cached images for a category
        
        Args:
            category: Image category/query
            count: Number of images to retrieve
            size: Optional tuple (width, height) to resize images
            
        Returns:
            List of PIL Image objects (may be less than count if cache is small)
        """
        category_dir = self._get_category_dir(category)
        
        # Get list of cached images
        image_files = list(category_dir.glob('*.jpg')) + list(category_dir.glob('*.png'))
        
        if not image_files:
            return []
            
        # Select random images
        selected_files = random.sample(image_files, min(count, len(image_files)))
        
        images = []
        for file_path in selected_files:
            try:
                img = Image.open(file_path)
                img = img.convert('RGB')
                
                if size:
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    
                images.append(img)
            except Exception as e:
                print(f"Error loading cached image {file_path}: {e}")
                # Remove corrupted file
                try:
                    file_path.unlink()
                except:
                    pass
                    
        return images
        
    def get_cache_count(self, category):
        """Get the number of cached images for a category"""
        category_dir = self._get_category_dir(category)
        image_files = list(category_dir.glob('*.jpg')) + list(category_dir.glob('*.png'))
        return len(image_files)
        
    def has_enough_cached(self, category, min_count=5):
        """Check if category has enough cached images"""
        return self.get_cache_count(category) >= min_count
        
    def save_image(self, image, category, image_id=None):
        """
        Save an image to the cache
        
        Args:
            image: PIL Image object
            category: Image category/query
            image_id: Optional unique identifier (generates one if not provided)
            
        Returns:
            Path to saved image or None if failed
        """
        category_dir = self._get_category_dir(category)
        
        # Generate unique filename
        if image_id is None:
            image_id = hashlib.md5(f"{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()[:12]
            
        filename = f"{image_id}.jpg"
        file_path = category_dir / filename
        
        try:
            # Ensure RGB mode for JPEG
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            image.save(file_path, 'JPEG', quality=85)
            
            # Update metadata
            if category not in self.metadata['categories']:
                self.metadata['categories'][category] = {
                    'count': 0,
                    'last_updated': None
                }
            
            self.metadata['categories'][category]['count'] = self.get_cache_count(category)
            self.metadata['categories'][category]['last_updated'] = datetime.now().isoformat()
            self._save_metadata()
            
            # Cleanup if over limit
            self._cleanup_category(category)
            
            return str(file_path)
            
        except Exception as e:
            print(f"Error saving image to cache: {e}")
            return None
            
    def _cleanup_category(self, category):
        """Remove oldest images if category exceeds max limit"""
        category_dir = self._get_category_dir(category)
        image_files = list(category_dir.glob('*.jpg')) + list(category_dir.glob('*.png'))
        
        if len(image_files) > self.max_images_per_category:
            # Sort by modification time (oldest first)
            image_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Remove oldest files
            files_to_remove = len(image_files) - self.max_images_per_category
            for file_path in image_files[:files_to_remove]:
                try:
                    file_path.unlink()
                except:
                    pass
                    
    def cleanup_all(self):
        """Clean up all expired cache entries"""
        if not self.cache_dir.exists():
            return
            
        cutoff_date = datetime.now() - timedelta(days=self.cache_expiry_days)
        
        for category_dir in self.cache_dir.iterdir():
            if category_dir.is_dir() and category_dir.name != '__pycache__':
                for file_path in category_dir.glob('*'):
                    if file_path.is_file() and file_path.suffix in ('.jpg', '.png'):
                        try:
                            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if mtime < cutoff_date:
                                file_path.unlink()
                        except:
                            pass
                            
        self.metadata['last_cleanup'] = datetime.now().isoformat()
        self._save_metadata()
        
    def get_stats(self):
        """Get cache statistics"""
        stats = {
            'total_images': 0,
            'categories': {},
            'cache_dir': str(self.cache_dir)
        }
        
        for category_dir in self.cache_dir.iterdir():
            if category_dir.is_dir() and category_dir.name != '__pycache__':
                image_files = list(category_dir.glob('*.jpg')) + list(category_dir.glob('*.png'))
                count = len(image_files)
                stats['categories'][category_dir.name] = count
                stats['total_images'] += count
                
        return stats


# Global instance
image_cache = ImageCache()
