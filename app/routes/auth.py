from flask import Blueprint, request, jsonify
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.jwt_handler import JWTHandler
import logging

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = logging.getLogger(__name__)

# ============================================================
# ENDPOINT 1: REGISTER
# ============================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register new user for AqarBot
    
    Expected JSON: {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123",
        "phone_number": "0551234567"  // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        phone_number = data.get('phone_number', '').strip()
        
        # Call service
        result = AuthService.register(name, email, password, phone_number if phone_number else None)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Register error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during registration: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 2: LOGIN
# ============================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    
    Expected JSON: {
        "email": "john@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Call service
        result = AuthService.login(email, password)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error during login: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 3: VERIFY TOKEN
# ============================================================

@auth_bp.route('/verify-token', methods=['GET'])
def verify_token():
    """
    Verify if token is valid
    
    Expected header: Authorization: Bearer <token>
    """
    try:
        # Extract token
        token = JWTHandler.extract_token_from_header(request)
        
        # Call service
        result = AuthService.verify_token(token)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error verifying token: {str(e)}'
        }), 500
        

# ============================================================
# ENDPOINT 4: VERIFY EMAIL FOR PASSWORD RESET
# ============================================================

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Verify email exists before allowing password reset
    Expected JSON: { "email": "john@example.com" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'success': False, 'message': 'Email is required'}), 400

        user = User.get_user_by_email(email)

        if not user:
            return jsonify({'success': False, 'message': 'No account found with this email'}), 404

        return jsonify({'success': True, 'message': 'Email verified', 'email': email}), 200

    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================================
# ENDPOINT 5: RESET PASSWORD
# ============================================================

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password after email verification
    Expected JSON: { "email": "john@example.com", "new_password": "newpass123" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        new_password = data.get('new_password', '')

        if not email or not new_password:
            return jsonify({'success': False, 'message': 'Email and new password are required'}), 400

        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

        # Verify email still exists
        user = User.get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'message': 'Account not found'}), 404

        success, message = User.update_password(email, new_password)

        if success:
            return jsonify({'success': True, 'message': 'Password reset successfully'}), 200
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500