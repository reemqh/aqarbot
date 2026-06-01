from flask import Blueprint, jsonify, request
from app.utils.auth_decorators import roles_required
from app.database import db
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
logger = logging.getLogger(__name__)


# ============================================================
# ENDPOINT 1: LIST ALL USERS WITH THEIR PROFILE INFO
# ============================================================

@admin_bp.route('/users', methods=['GET'])
@roles_required(['limited_admin'])
def get_all_users(current_user):
    """
    GET: List all users with their basic profile info.

    URL: GET /api/admin/users
    Auth: Required (Bearer token, limited_admin role only)
    """
    try:
        cursor = db.get_cursor()
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                u.phone_number,
                u.created_at,
                up.bio,
                up.profile_picture,
                up.phone_number AS profile_phone
            FROM users u
            LEFT JOIN user_profile up ON up.user_id = u.id
            WHERE u.role = 'user'
            ORDER BY u.created_at DESC
        """)
        users = cursor.fetchall()

        # Convert datetime to string for JSON serialization
        result = []
        for user in users:
            result.append({
                'user_id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'phone_number': user['phone_number'] or user.get('profile_phone'),
                'bio': user.get('bio'),
                'profile_picture': user.get('profile_picture'),
                'joined_at': str(user['created_at']) if user.get('created_at') else None
            })

        logger.info(f"Admin '{current_user['email']}' retrieved user list ({len(result)} users).")

        return jsonify({
            'success': True,
            'message': f'{len(result)} user(s) found',
            'data': result
        }), 200

    except Exception as e:
        logger.error(f"Admin get_all_users error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================================
# ENDPOINT 2: GET A SINGLE USER'S DETAILS + THEIR PROPERTIES
# ============================================================

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@roles_required(['limited_admin'])
def get_user_details(current_user, user_id):
    """
    GET: Get a specific user's details including their chat preferences / property searches.

    URL: GET /api/admin/users/<user_id>
    Auth: Required (Bearer token, limited_admin role only)
    """
    try:
        cursor = db.get_cursor()

        # Get basic user info + profile
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                u.phone_number,
                u.created_at,
                up.bio,
                up.profile_picture,
                up.phone_number AS profile_phone
            FROM users u
            LEFT JOIN user_profile up ON up.user_id = u.id
            WHERE u.id = %s AND u.role = 'user'
        """, (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Get user's completed property searches (chat sessions with preferences)
        cursor.execute("""
            SELECT
                id AS session_id,
                status,
                preferences,
                created_at,
                updated_at
            FROM chat_sessions
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        sessions = cursor.fetchall()

        # Get user's appointments
        cursor.execute("""
            SELECT
                a.id AS appointment_id,
                a.appointment_time,
                a.status,
                a.notes,
                p.title AS property_title,
                p.location AS property_location,
                ag.name AS agent_name
            FROM appointments a
            JOIN properties p ON p.id = a.property_id
            JOIN agents ag ON ag.id = a.agent_id
            WHERE a.user_id = %s
            ORDER BY a.appointment_time DESC
        """, (user_id,))
        appointments = cursor.fetchall()

        # Build response
        session_list = []
        for s in sessions:
            session_list.append({
                'session_id': s['session_id'],
                'status': s['status'],
                'preferences': s['preferences'],
                'created_at': str(s['created_at']) if s.get('created_at') else None,
                'updated_at': str(s['updated_at']) if s.get('updated_at') else None,
            })

        appointment_list = []
        for ap in appointments:
            appointment_list.append({
                'appointment_id': ap['appointment_id'],
                'property_title': ap['property_title'],
                'property_location': ap['property_location'],
                'agent_name': ap['agent_name'],
                'appointment_time': str(ap['appointment_time']) if ap.get('appointment_time') else None,
                'status': ap['status'],
                'notes': ap['notes'],
            })

        logger.info(f"Admin '{current_user['email']}' viewed details for user {user_id}.")

        return jsonify({
            'success': True,
            'data': {
                'user_id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'phone_number': user['phone_number'] or user.get('profile_phone'),
                'bio': user.get('bio'),
                'profile_picture': user.get('profile_picture'),
                'joined_at': str(user['created_at']) if user.get('created_at') else None,
                'property_searches': session_list,
                'appointments': appointment_list
            }
        }), 200

    except Exception as e:
        logger.error(f"Admin get_user_details error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
