from functools import wraps
from flask import request, jsonify
from models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            # Assuming token is in format: "Bearer <token>"
            token = auth_header.split(' ')[1]
            # Here you would validate the token and get the user
            # For now, we'll just set a mock user
            request.user = User.query.first()  # Replace with actual token validation
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated_function 