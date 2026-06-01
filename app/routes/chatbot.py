from flask import Blueprint, request, jsonify
from app.services.chatbot_service import ChatbotService
from app.utils.jwt_handler import JWTHandler
import logging

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

# ============================================================
# ENDPOINT 1: START CHAT
# ============================================================

@chatbot_bp.route('/start', methods=['POST'])
def start_chat():
    """
    Start a new chat session
    
    Expected JSON: {}
    Authorization: Bearer token (required)
    
    Returns:
    {
        "success": true,
        "session_id": 123,
        "first_question": "What is your budget...?",
        "stage": 1
    }
    """
    try:
        # Verify token
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
        
        # Start chat
        result = ChatbotService.start_chat(user_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in start_chat: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error starting chat: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 2: PROCESS MESSAGE
# ============================================================

@chatbot_bp.route('/message', methods=['POST'])
def process_message():
    """
    Process user message and get bot response
    
    Expected JSON: {
        "session_id": 123,
        "message": "400k to 800k"
    }
    
    Returns:
    {
        "success": true,
        "current_stage": 1,
        "next_question": "Which location...?",
        "preferences_complete": false,
        "collected_preferences": {...}
    }
    """
    try:
        # Verify token
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
        
        session_id = data.get('session_id')
        message = data.get('message', '').strip()
        lang = data.get('lang', 'en')
        
        # Validate
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'session_id is required'
            }), 400
        
        if not message:
            return jsonify({
                'success': False,
                'message': 'message cannot be empty'
            }), 400
        
        # Process message
        result = ChatbotService.process_user_message(session_id, message, lang)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error in process_message: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error processing message: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 3: GET CHAT HISTORY
# ============================================================

@chatbot_bp.route('/history/<int:session_id>', methods=['GET'])
def get_chat_history(session_id):
    """
    Get chat session progress
    
    Authorization: Bearer token (required)
    
    Returns:
    {
        "success": true,
        "session_id": 123,
        "user_id": 456,
        "current_stage": 2,
        "status": "active",
        "collected_preferences": {...},
        "preferences_complete": false
    }
    """
    try:
        # Verify token
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
        
        # Get session progress
        result = ChatbotService.get_session_progress(session_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    
    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error retrieving chat history: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 4: TEST GROQ CONNECTION (Debug)
# ============================================================

@chatbot_bp.route('/test-groq', methods=['GET'])
def test_groq():
    """
    Test Groq API connection (for debugging)
    
    Returns:
    {
        "success": true,
        "message": "Connection successful..."
    }
    """
    try:
        from app.services.groq_service import GroqService
        
        success, message = GroqService.test_connection()
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 500
    
    except Exception as e:
        logger.error(f"Error in test_groq: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error testing Groq: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 5: SAVE TRANSCRIPT (Called after completion)
# ============================================================

@chatbot_bp.route('/save-transcript', methods=['POST'])
def save_transcript():
    """
    Save completed chat transcript to chat_messages table.
    Called once by the frontend when preferences_complete fires.

    Expected JSON: {
        "session_id": 123,
        "transcript": [{"sender": "user"|"bot", "text": "..."}]
    }
    """
    try:
        token = JWTHandler.extract_token_from_header(request)
        if not token:
            return jsonify({'success': False, 'message': 'No token provided'}), 401

        user_id = JWTHandler.verify_token(token)
        if user_id is None:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        session_id = data.get('session_id')
        transcript = data.get('transcript', [])

        if not session_id or not transcript:
            return jsonify({'success': False, 'message': 'session_id and transcript required'}), 400

        from app.models.chat_session import ChatSession
        success, msg = ChatSession.save_messages(session_id, transcript)

        return jsonify({'success': success, 'message': msg}), 200 if success else 500

    except Exception as e:
        logger.error(f"Error in save_transcript: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# ENDPOINT 6: GET COMPLETED SESSIONS (History Page)
# ============================================================

@chatbot_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """
    Get all completed chat sessions with messages for the logged-in user.

    Returns:
    {
        "success": true,
        "sessions": [
            {
                "session_id": 123,
                "created_at": "2026-05-11 13:00",
                "preferences": {...},
                "messages": [{"sender": "bot"|"user", "text": "..."}]
            }
        ]
    }
    """
    try:
        token = JWTHandler.extract_token_from_header(request)
        if not token:
            return jsonify({'success': False, 'message': 'No token provided'}), 401

        user_id = JWTHandler.verify_token(token)
        if user_id is None:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401

        from app.models.chat_session import ChatSession
        sessions = ChatSession.get_completed_sessions(user_id)

        return jsonify({'success': True, 'sessions': sessions}), 200

    except Exception as e:
        logger.error(f"Error in get_sessions: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500