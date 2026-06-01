from flask import Blueprint, request, jsonify
from app.services.appointment_service import AppointmentService
from app.utils.jwt_handler import JWTHandler
import logging

logger = logging.getLogger(__name__)

appointment_bp = Blueprint('appointment', __name__, url_prefix='/api/appointments')

# ============================================================
# ENDPOINT 1: GET AVAILABLE SLOTS FOR PROPERTY
# ============================================================

@appointment_bp.route('/available-slots/<int:property_id>', methods=['GET'])
def get_available_slots(property_id):
    """
    Get available appointment time slots for a property
    
    URL: GET /api/appointments/available-slots/3
    Query params: ?days_ahead=7 (optional, default 7)
    
    Returns: List of available datetime slots (YYYY-MM-DD HH:MM format)
    """
    try:
        # Extract optional days_ahead parameter
        days_ahead = request.args.get('days_ahead', 7, type=int)
        
        if days_ahead < 1 or days_ahead > 30:
            return jsonify({
                'success': False,
                'message': 'days_ahead must be between 1 and 30'
            }), 400
        
        logger.info(f"Getting available slots for property {property_id}, {days_ahead} days ahead")
        
        # Get available slots
        result = AppointmentService.get_available_slots(property_id, days_ahead)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 2: BOOK APPOINTMENT
# ============================================================

@appointment_bp.route('/book', methods=['POST'])
def book_appointment():
    """
    Book an appointment for property viewing
    
    URL: POST /api/appointments/book
    Auth: Required (Bearer token)
    
    Body: {
        "property_id": 3,
        "agent_id": 1,
        "appointment_time": "2026-02-25 14:00",
        "notes": "Optional notes about the appointment"
    }
    
    Returns: Appointment confirmation with ID
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
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        property_id = data.get('property_id')
        agent_id = data.get('agent_id')
        appointment_time = data.get('appointment_time')
        notes = data.get('notes', '')
        
        # Validation
        if not property_id or not agent_id or not appointment_time:
            return jsonify({
                'success': False,
                'message': 'property_id, agent_id, and appointment_time are required'
            }), 400
        
        logger.info(f"Booking appointment for user {user_id}, property {property_id}, agent {agent_id}")
        
        # Book appointment
        result = AppointmentService.book_appointment(
            user_id=user_id,
            property_id=property_id,
            agent_id=agent_id,
            appointment_time=appointment_time,
            notes=notes
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 3: GET USER'S APPOINTMENT HISTORY
# ============================================================

@appointment_bp.route('/history', methods=['GET'])
def get_appointment_history():
    """
    Get all appointments for the logged-in user
    
    URL: GET /api/appointments/history
    Auth: Required (Bearer token)
    Query params: ?status=pending (optional - filter by pending/completed/cancelled)
    
    Returns: List of user's appointments
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
        
        # Get optional status filter
        status = request.args.get('status', None)
        
        if status and status not in ['pending', 'completed', 'cancelled']:
            return jsonify({
                'success': False,
                'message': 'Invalid status. Must be pending, completed, or cancelled'
            }), 400
        
        logger.info(f"Getting appointments for user {user_id}")
        
        # Get appointments
        result = AppointmentService.get_user_appointments(user_id, status)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error getting appointment history: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 4: GET SINGLE APPOINTMENT DETAILS
# ============================================================

@appointment_bp.route('/<int:appointment_id>', methods=['GET'])
def get_appointment_details(appointment_id):
    """
    Get detailed information about a single appointment
    
    URL: GET /api/appointments/5
    Auth: Required (Bearer token)
    
    Returns: Full appointment details with property and agent info
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
        
        logger.info(f"Getting appointment details: {appointment_id}")
        
        # Get appointment with ownership verification
        result = AppointmentService.get_appointment_details(appointment_id, user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 403 if 'Unauthorized' in result['message'] else 404
            return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error getting appointment: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 5: CANCEL APPOINTMENT
# ============================================================

@appointment_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    """
    Cancel an appointment
    
    URL: POST /api/appointments/5/cancel
    Auth: Required (Bearer token)
    Body: {} (empty)
    
    Returns: Cancellation confirmation
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
        
        logger.info(f"Cancelling appointment {appointment_id} for user {user_id}")
        
        # Cancel appointment with ownership verification
        result = AppointmentService.cancel_appointment(appointment_id, user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 403 if 'Unauthorized' in result['message'] else 404
            return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 6: MARK APPOINTMENT AS COMPLETED
# ============================================================

@appointment_bp.route('/<int:appointment_id>/complete', methods=['POST'])
def mark_completed(appointment_id):
    """
    Mark an appointment as completed
    
    URL: POST /api/appointments/5/complete
    Auth: Required (Bearer token)
    Body: {} (empty)
    
    Returns: Completion confirmation
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
        
        logger.info(f"Marking appointment {appointment_id} as completed for user {user_id}")
        
        # Mark as completed with ownership verification
        result = AppointmentService.mark_completed(appointment_id, user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 403 if 'Unauthorized' in result['message'] else 404
            return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error marking appointment completed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500