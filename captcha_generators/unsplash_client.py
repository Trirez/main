"""
Unsplash API Client with Caching
Fetches images from Unsplash for captcha generation with local caching
"""

import os
import random
import requests
from io import BytesIO
from PIL import Image

from .image_cache import image_cache


class UnsplashClient:
    # Default API key (can be overridden via environment variable or set_api_key method)
    DEFAULT_API_KEY = "gRD18QNRs9hEmcrPNlJryXDwRNCuwAAeJs4VdBB8Upc"
    
    # Minimum cached images before fetching from API
    MIN_CACHE_THRESHOLD = 5
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('UNSPLASH_API_KEY') or self.DEFAULT_API_KEY
        self.base_url = "https://api.unsplash.com"
        self.use_cache = True  # Enable caching by default
        self.cache_only_mode = True  # Default to cache-only for faster loading (no slow API calls)
        
    def set_api_key(self, api_key):
        """Set the API key"""
        self.api_key = api_key
        
    def set_cache_mode(self, use_cache=True, cache_only=False):
        """Configure caching behavior"""
        self.use_cache = use_cache
        self.cache_only_mode = cache_only
        
    def get_random_image(self, query=None, size=(300, 300)):
        """
        Fetch a random image, preferring cache over API
        
        Args:
            query: Search term (e.g., 'nature', 'car', 'mountain')
            size: Tuple of (width, height) to resize the image
            
        Returns:
            PIL Image object or None if failed
        """
        category = query or 'random'
        
        # Try cache first if enabled
        if self.use_cache:
            cached_images = image_cache.get_cached_images(category, count=1, size=size)
            if cached_images:
                return cached_images[0]
        
        # If cache-only mode, don't call API
        if self.cache_only_mode:
            return None
            
        # Fetch from API
        if not self.api_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Client-ID {self.api_key}"
            }
            
            params = {}
            if query:
                params['query'] = query
                
            response = requests.get(
                f"{self.base_url}/photos/random",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                image_url = data.get('urls', {}).get('small') or data.get('urls', {}).get('regular')
                image_id = data.get('id', '')
                
                if image_url:
                    img = self._download_and_resize(image_url, size)
                    
                    # Cache the image
                    if img and self.use_cache:
                        image_cache.save_image(img, category, image_id)
                        
                    return img
            else:
                print(f"Unsplash API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching from Unsplash: {e}")
            return None
            
    def get_images_by_query(self, query, count=3, size=(120, 120)):
        """
        Fetch multiple images matching a query, using cache when available
        
        Args:
            query: Search term
            count: Number of images to fetch
            size: Tuple of (width, height) to resize images
            
        Returns:
            List of PIL Image objects
        """
        category = query
        
        # Check cache first
        if self.use_cache and image_cache.has_enough_cached(category, min_count=count):
            cached_images = image_cache.get_cached_images(category, count=count, size=size)
            if len(cached_images) >= count:
                return cached_images[:count]
        
        # If cache-only mode, return what we have
        if self.cache_only_mode:
            return image_cache.get_cached_images(category, count=count, size=size)
            
        # Fetch from API
        if not self.api_key:
            # Return cached images if available when no API key
            return image_cache.get_cached_images(category, count=count, size=size)
            
        try:
            headers = {
                "Authorization": f"Client-ID {self.api_key}"
            }
            
            # Fetch more images to build up cache
            fetch_count = max(count, 10)  # Always fetch at least 10 to build cache
            
            params = {
                'query': query,
                'per_page': fetch_count,
                'orientation': 'squarish'
            }
            
            response = requests.get(
                f"{self.base_url}/search/photos",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                images = []
                for photo in results:
                    image_url = photo.get('urls', {}).get('small') or photo.get('urls', {}).get('thumb')
                    image_id = photo.get('id', '')
                    
                    if image_url:
                        img = self._download_and_resize(image_url, size)
                        if img:
                            images.append(img)
                            
                            # Cache the image
                            if self.use_cache:
                                image_cache.save_image(img, category, image_id)
                            
                return images[:count]
            else:
                print(f"Unsplash API error: {response.status_code}")
                # Fall back to cache
                return image_cache.get_cached_images(category, count=count, size=size)
                
        except Exception as e:
            print(f"Error fetching from Unsplash: {e}")
            # Fall back to cache
            return image_cache.get_cached_images(category, count=count, size=size)
            
    def _download_and_resize(self, url, size):
        """Download image from URL and resize it"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img = img.convert('RGB')
                img = img.resize(size, Image.Resampling.LANCZOS)
                return img
        except Exception as e:
            print(f"Error downloading image: {e}")
        return None
        
    def prefetch_category(self, query, count=10, size=(120, 120)):
        """
        Pre-fetch images for a category to build up cache
        
        Args:
            query: Search term
            count: Number of images to fetch
            size: Tuple of (width, height)
        """
        current_count = image_cache.get_cache_count(query)
        if current_count < count:
            needed = count - current_count
            self.get_images_by_query(query, count=needed, size=size)
            
    def get_cache_stats(self):
        """Get cache statistics"""
        return image_cache.get_stats()


# Global instance
unsplash_client = UnsplashClient()

