from flask import Blueprint, jsonify, request
from app.models.user import User
from app.models.user_profile import UserProfile
from app.utils.jwt_handler import JWTHandler
import logging

user_bp = Blueprint('user', __name__, url_prefix='/api/users')
logger = logging.getLogger(__name__)

# ============================================================
# ENDPOINT: GET USER PROFILE (API ONLY)
# ============================================================

@user_bp.route('/profile', methods=['GET'])
def user_profile():
    """
    GET: Get logged-in user's profile information
    
    URL: GET /api/users/profile
    Auth: Required (Bearer token)
    
    Returns: User name, email, phone
    """
    try:
        # Verify token and get user_id
        token = JWTHandler.extract_token_from_header(request)
        if not token:
            return jsonify({
                'success': False,
                'message': 'No token provided'
            }), 401
        
        user_id = JWTHandler.verify_token(token)
        if user_id is None:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401
        
        # Get user basic info
        user = User.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get user profile (phone, etc.)
        profile = UserProfile.get_profile_by_user(user_id)
        
        logger.info(f"Profile retrieved for user: {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Profile retrieved successfully',
            'data': {
                'user_id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'phone_number': user.get('phone_number'),
                'profile': profile if profile else None
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in user profile: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500