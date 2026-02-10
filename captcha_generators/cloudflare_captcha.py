"""
Cloudflare-style Captcha Generator
Simulates Cloudflare Turnstile with test token verification
"""

import random
import string
import time
import hashlib


class CloudflareCaptcha:
    def __init__(self):
        self.valid_tokens: dict[str, dict] = {}
        self.token_expiry = 300  # 5 minutes
        
    def generate_challenge_id(self):
        """Generate a unique challenge ID"""
        timestamp = str(time.time())
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        return hashlib.sha256(f"{timestamp}{random_str}".encode()).hexdigest()[:32]
    
    def generate_token(self, challenge_id):
        """Generate a verification token for a challenge"""
        token_data = f"{challenge_id}{time.time()}{random.random()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()
        
        # Store token with expiry
        self.valid_tokens[token] = {
            'challenge_id': challenge_id,
            'created_at': time.time(),
            'expires_at': time.time() + self.token_expiry
        }
        
        return token
    
    def verify_token(self, token):
        """Verify if a token is valid"""
        # Clean expired tokens
        current_time = time.time()
        self.valid_tokens = {
            k: v for k, v in self.valid_tokens.items() 
            if v['expires_at'] > current_time
        }
        
        if token in self.valid_tokens:
            # Token is valid - remove it (one-time use)
            self.valid_tokens.pop(token)
            return {
                'success': True,
                'message': 'Verification successful'
            }
        
        return {
            'success': False,
            'message': 'Invalid or expired token'
        }
    
    def generate(self):
        """Generate a new Cloudflare-style captcha challenge"""
        challenge_id = self.generate_challenge_id()
        
        return {
            'challenge_id': challenge_id,
            'site_key': 'test_site_key_' + challenge_id[:8],
            'type': 'invisible',
            'theme': 'auto'
        }
    
    def complete_challenge(self, challenge_id, user_interaction=True):
        """
        Complete a challenge and generate token
        In a real implementation, this would involve browser fingerprinting,
        mouse movement analysis, etc.
        """
        if not user_interaction:
            return {
                'success': False,
                'error': 'Human interaction required'
            }
        
        # Simulate verification delay
        token = self.generate_token(challenge_id)
        
        return {
            'success': True,
            'token': token,
            'expires_in': self.token_expiry
        }
