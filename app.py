"""
Captcha Generator - Flask Application
Provides multiple captcha types: text, image, cloudflare, and puzzle
With user authentication and captcha verification
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
import secrets
import os

from captcha_generators.text_captcha import TextCaptcha
from captcha_generators.image_captcha import ImageCaptcha
from captcha_generators.cloudflare_captcha import CloudflareCaptcha
from captcha_generators.puzzle_captcha import PuzzleCaptcha
from captcha_generators.unsplash_client import unsplash_client
from database import db, User, init_db

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Initialize database
init_db(app)

# Initialize captcha generators
text_captcha = TextCaptcha()
image_captcha = ImageCaptcha()
cloudflare_captcha = CloudflareCaptcha()
puzzle_captcha = PuzzleCaptcha()

# Load Unsplash API key from environment variable if available
if os.environ.get('UNSPLASH_API_KEY'):
    unsplash_client.set_api_key(os.environ.get('UNSPLASH_API_KEY'))


@app.route('/')
def home():
    """Landing page with two sections: Captcha Demo and User Authentication"""
    return render_template('home.html')


@app.route('/demo')
def captcha_demo():
    """Captcha demo page with all captcha types"""
    return render_template('index.html')



# ============== UNSPLASH API CONFIGURATION ==============

@app.route('/api/config/unsplash', methods=['POST'])
def set_unsplash_api_key():
    """Set the Unsplash API key for image fetching"""
    data = request.get_json()
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({'success': False, 'message': 'API key is required'})
    
    unsplash_client.set_api_key(api_key)
    image_captcha.set_api_key(api_key)
    puzzle_captcha.set_api_key(api_key)
    
    return jsonify({'success': True, 'message': 'Unsplash API key configured successfully'})


@app.route('/api/config/unsplash/status', methods=['GET'])
def get_unsplash_status():
    """Check if Unsplash API is configured"""
    is_configured = unsplash_client.api_key is not None
    cache_stats = unsplash_client.get_cache_stats()
    return jsonify({
        'configured': is_configured,
        'message': 'Unsplash API is configured' if is_configured else 'Unsplash API key not set',
        'cache': cache_stats
    })


# ============== IMAGE CACHE MANAGEMENT ==============

@app.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics"""
    stats = unsplash_client.get_cache_stats()
    return jsonify({
        'success': True,
        'stats': stats
    })


@app.route('/api/cache/prefetch', methods=['POST'])
def prefetch_images():
    """Pre-fetch images for specified categories to build cache"""
    data = request.get_json()
    categories = data.get('categories', [])
    count = data.get('count', 10)
    
    if not categories:
        # Default categories used by captchas
        categories = ['car vehicle', 'tree nature', 'house building', 'sunset sunshine',
                     'mountain landscape', 'flower bloom', 'ocean sea waves', 
                     'dog pet', 'cat kitten', 'bird wildlife']
    
    results = {}
    for category in categories:
        unsplash_client.prefetch_category(category, count=count, size=(120, 120))
        from captcha_generators.image_cache import image_cache
        results[category] = image_cache.get_cache_count(category)
    
    return jsonify({
        'success': True,
        'message': f'Prefetched images for {len(categories)} categories',
        'results': results
    })


@app.route('/api/cache/mode', methods=['POST'])
def set_cache_mode():
    """Set cache mode (cache-only disables API calls)"""
    data = request.get_json()
    use_cache = data.get('use_cache', True)
    cache_only = data.get('cache_only', False)
    
    unsplash_client.set_cache_mode(use_cache=use_cache, cache_only=cache_only)
    
    return jsonify({
        'success': True,
        'use_cache': use_cache,
        'cache_only': cache_only,
        'message': 'Cache mode updated'
    })


@app.route('/api/cache/cleanup', methods=['POST'])
def cleanup_cache():
    """Clean up expired cache entries"""
    from captcha_generators.image_cache import image_cache
    image_cache.cleanup_all()
    
    return jsonify({
        'success': True,
        'message': 'Cache cleanup completed',
        'stats': unsplash_client.get_cache_stats()
    })


# ============== TEXT CAPTCHA ==============

@app.route('/api/text-captcha', methods=['GET'])
def generate_text_captcha():
    """Generate a new text captcha"""
    result = text_captcha.generate()
    # Store the answer in session
    session['text_captcha_answer'] = result['text']
    return jsonify({
        'image': result['image'],
        'length': len(result['text'])
    })


@app.route('/api/text-captcha/verify', methods=['POST'])
def verify_text_captcha():
    """Verify text captcha answer"""
    data = request.get_json()
    user_answer = data.get('answer', '').upper()
    correct_answer = session.get('text_captcha_answer', '')
    
    if user_answer == correct_answer:
        return jsonify({'success': True, 'message': 'Correct!'})
    else:
        return jsonify({'success': False, 'message': 'Incorrect. Try again.'})


# ============== IMAGE CAPTCHA ==============

@app.route('/api/image-captcha', methods=['GET'])
def generate_image_captcha():
    """Generate a new image selection captcha with 3x3 grid"""
    result = image_captcha.generate()
    # Store correct answers in session (list of correct indices)
    session['image_captcha_answers'] = result['correct_indices']
    session['image_required_selections'] = result['required_selections']
    
    # Remove is_correct from response
    images = [{
        'image': img['image'],
        'index': img['index']
    } for img in result['images']]
    
    return jsonify({
        'prompt': result['prompt'],
        'images': images,
        'required_selections': result['required_selections']
    })


@app.route('/api/image-captcha/verify', methods=['POST'])
def verify_image_captcha():
    """Verify image captcha selection - user must select all correct images"""
    data = request.get_json()
    selected_indices = data.get('selected_indices', [])
    correct_indices = session.get('image_captcha_answers', [])
    required = session.get('image_required_selections', 3)
    
    # Check if user selected exactly the right images
    if sorted(selected_indices) == sorted(correct_indices):
        return jsonify({'success': True, 'message': 'Correct! All images selected correctly.'})
    elif len(selected_indices) < required:
        return jsonify({'success': False, 'message': f'Please select {required} images.'})
    else:
        return jsonify({'success': False, 'message': 'Wrong selection. Try again.'})


# ============== CLOUDFLARE CAPTCHA ==============

@app.route('/api/cloudflare-captcha', methods=['GET'])
def generate_cloudflare_captcha():
    """Generate a new Cloudflare-style captcha challenge"""
    result = cloudflare_captcha.generate()
    session['cloudflare_challenge_id'] = result['challenge_id']
    return jsonify(result)


@app.route('/api/cloudflare-captcha/complete', methods=['POST'])
def complete_cloudflare_captcha():
    """Complete Cloudflare captcha challenge"""
    challenge_id = session.get('cloudflare_challenge_id')
    if not challenge_id:
        return jsonify({'success': False, 'error': 'No active challenge'})
    
    result = cloudflare_captcha.complete_challenge(challenge_id, user_interaction=True)
    if result['success']:
        session['cloudflare_token'] = result['token']
    return jsonify(result)


@app.route('/api/cloudflare-captcha/verify', methods=['POST'])
def verify_cloudflare_captcha():
    """Verify Cloudflare captcha token"""
    data = request.get_json()
    token = data.get('token') or session.get('cloudflare_token')
    
    if not token:
        return jsonify({'success': False, 'message': 'No token provided'})
    
    result = cloudflare_captcha.verify_token(token)
    return jsonify(result)


# ============== PUZZLE CAPTCHA - SLIDING ==============

@app.route('/api/puzzle-captcha/sliding', methods=['GET'])
def generate_sliding_puzzle():
    """Generate a new sliding puzzle captcha"""
    result = puzzle_captcha.generate_sliding_puzzle()
    session['sliding_puzzle_answer'] = result['correct_x']
    session['sliding_puzzle_tolerance'] = result['tolerance']
    
    # Remove correct answer from response
    return jsonify({
        'background': result['background'],
        'piece': result['piece'],
        'piece_y': result['piece_y'],
        'puzzle_width': result['puzzle_width'],
        'puzzle_height': result['puzzle_height'],
        'piece_size': result['piece_size']
    })


@app.route('/api/puzzle-captcha/sliding/verify', methods=['POST'])
def verify_sliding_puzzle():
    """Verify sliding puzzle answer"""
    data = request.get_json()
    submitted_x = data.get('x', 0)
    correct_x = session.get('sliding_puzzle_answer', 0)
    tolerance = session.get('sliding_puzzle_tolerance', 10)
    
    if puzzle_captcha.verify_sliding(submitted_x, correct_x, tolerance):
        return jsonify({'success': True, 'message': 'Puzzle solved correctly!'})
    else:
        return jsonify({'success': False, 'message': 'Incorrect position. Try again.'})


# ============== PUZZLE CAPTCHA - DRAG ==============

@app.route('/api/puzzle-captcha/drag', methods=['GET'])
def generate_drag_puzzle():
    """Generate a new drag puzzle captcha"""
    result = puzzle_captcha.generate_drag_puzzle()
    # Store only the correct positions (not full image data to avoid cookie overflow)
    session['drag_puzzle_answers'] = [{
        'id': p['id'],
        'correct_x': p['correct_x'],
        'correct_y': p['correct_y']
    } for p in result['pieces']]
    session['drag_puzzle_tolerance'] = result['tolerance']
    
    # Prepare response without correct positions in pieces
    pieces = [{
        'id': p['id'],
        'image': p['image']
    } for p in result['pieces']]
    
    return jsonify({
        'background': result['background'],
        'pieces': pieces,
        'positions': result['positions'],
        'puzzle_width': result['puzzle_width'],
        'puzzle_height': result['puzzle_height'],
        'piece_size': result['piece_size']
    })


@app.route('/api/puzzle-captcha/drag/verify', methods=['POST'])
def verify_drag_puzzle():
    """Verify drag puzzle answer"""
    data = request.get_json()
    submitted_positions = data.get('positions', [])
    correct_answers = session.get('drag_puzzle_answers', [])
    tolerance = session.get('drag_puzzle_tolerance', 15)
    
    if puzzle_captcha.verify_drag(submitted_positions, correct_answers, tolerance):
        return jsonify({'success': True, 'message': 'All pieces placed correctly!'})
    else:
        return jsonify({'success': False, 'message': 'Some pieces are not in the right position.'})


# ============== AUTHENTICATION ==============

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get the currently logged in user"""
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with captcha verification"""
    if request.method == 'GET':
        return render_template('register.html')
    
    # POST - process registration
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    captcha_type = request.form.get('captcha_type', 'text')
    
    # Validate captcha based on type
    captcha_valid = verify_captcha(captcha_type, request.form)
    if not captcha_valid:
        return render_template('register.html', error='Invalid captcha. Please try again.')
    
    # Validate passwords match
    if password != confirm_password:
        return render_template('register.html', error='Passwords do not match.')
    
    # Validate password length
    if len(password) < 6:
        return render_template('register.html', error='Password must be at least 6 characters.')
    
    # Check if username exists
    if User.get_by_username(username):
        return render_template('register.html', error='Username already exists.')
    
    # Check if email exists
    if User.get_by_email(email):
        return render_template('register.html', error='Email already registered.')
    
    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return redirect(url_for('login', success='Registration successful! Please sign in.'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with captcha verification"""
    if request.method == 'GET':
        success = request.args.get('success')
        return render_template('login.html', success=success)
    
    # POST - process login
    identifier = request.form.get('identifier', '').strip()
    password = request.form.get('password', '')
    captcha_type = request.form.get('captcha_type', 'text')
    
    # Validate captcha based on type
    captcha_valid = verify_captcha(captcha_type, request.form)
    if not captcha_valid:
        return render_template('login.html', error='Invalid captcha. Please try again.')
    
    # Find user
    user = User.get_by_username_or_email(identifier)
    
    if not user or not user.check_password(password):
        return render_template('login.html', error='Invalid username/email or password.')
    
    if not user.is_active:
        return render_template('login.html', error='Account is deactivated.')
    
    # Login successful
    session['user_id'] = user.id
    session['username'] = user.username
    
    return redirect(url_for('dashboard'))


def verify_captcha(captcha_type, form_data):
    """Verify captcha based on type"""
    import json
    
    if captcha_type == 'text':
        captcha_answer = form_data.get('captcha_answer', '').upper()
        correct_captcha = session.get('text_captcha_answer', '')
        return captcha_answer == correct_captcha
    
    elif captcha_type == 'image':
        try:
            selections = json.loads(form_data.get('image_selections', '[]'))
            correct_indices = session.get('image_captcha_answers', [])
            return sorted(selections) == sorted(correct_indices)
        except:
            return False
    
    elif captcha_type == 'cloudflare':
        cf_verified = form_data.get('cf_verified', 'false')
        return cf_verified == 'true'
    
    elif captcha_type == 'slider':
        try:
            position = int(form_data.get('slider_position', 0))
            correct_x = session.get('sliding_puzzle_answer', 0)
            tolerance = session.get('sliding_puzzle_tolerance', 15)
            return abs(position - correct_x) <= tolerance
        except:
            return False
    
    return False


@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - requires login"""
    user = get_current_user()
    return render_template('dashboard.html', user=user)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
