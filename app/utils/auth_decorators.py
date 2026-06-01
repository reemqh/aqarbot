from functools import wraps
from flask import request, jsonify
from app.utils.jwt_handler import JWTHandler
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


def roles_required(allowed_roles):
    """
    Decorator to restrict access to routes based on user role.

    Usage:
        @roles_required(['limited_admin'])
        def my_route():
            ...

    Args:
        allowed_roles: list of role strings that are permitted (e.g. ['limited_admin'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract token from Authorization header
            token = JWTHandler.extract_token_from_header(request)
            if not token:
                return jsonify({'success': False, 'message': 'No token provided'}), 401

            # Verify token
            user_id = JWTHandler.verify_token(token)
            if user_id is None:
                return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401

            # Get user and check role
            user = User.get_user_by_id(user_id)
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 401

            if user.get('role') not in allowed_roles:
                logger.warning(f"Access denied for user {user_id} with role '{user.get('role')}' on restricted endpoint.")
                return jsonify({'success': False, 'message': 'Access denied: Insufficient permissions'}), 403

            # Pass current_user into the route function via kwargs
            kwargs['current_user'] = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator
