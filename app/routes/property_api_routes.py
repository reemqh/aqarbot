from flask import Blueprint, request, jsonify
from app.models.property import Property
from app.models.agent import Agent
from app.models.chat_session import ChatSession
from app.services.property_matching_service import PropertyMatchingService
from app.utils.jwt_handler import JWTHandler
import logging

logger = logging.getLogger(__name__)

property_bp = Blueprint('property', __name__, url_prefix='/api/property')

# ============================================================
# ENDPOINT 1: GET MATCHING PROPERTIES FOR SESSION
# ============================================================

@property_bp.route('/recommendations/<int:session_id>', methods=['GET'])
def get_recommendations(session_id):
    """
    Get recommended properties based on user's collected preferences
    
    Authorization: Bearer token (required)
    URL: GET /api/property/recommendations/1
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
        
        # Get session
        session = ChatSession.get_session(session_id)
        
        if not session:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
        
        # Check if preferences complete
        if not session['current_stage'] >= 6:
            return jsonify({
                'success': False,
                'message': 'Preferences not complete yet. Complete all 5 stages first.'
            }), 400
        
        # Get preferences
        preferences = session['preferences']
        
        logger.info(f"Getting recommendations for session {session_id}")
        
        # Match and score properties
        all_matched_properties = PropertyMatchingService.match_preferences_to_properties(preferences, limit=100)
        
        if not all_matched_properties:
            return jsonify({
                'success': True,
                'session_id': session_id,
                'preferences': preferences,
                'total_matched': 0,
                'best_match': None,
                'alternatives': [],
                'low_confidence': True
            }), 200
        
        best_match = all_matched_properties[0]
        alternatives = all_matched_properties[1:4]
        low_confidence = best_match['match_score'] < 20

        return jsonify({
            'success': True,
            'session_id': session_id,
            'preferences': preferences,
            'total_matched': len(all_matched_properties),
            'best_match': best_match,
            'alternatives': alternatives,
            'low_confidence': low_confidence
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error getting recommendations: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 2: GET ALL PROPERTIES
# ============================================================

@property_bp.route('/all', methods=['GET'])
def get_all_properties():
    """
    Get all available properties
    
    URL: GET /api/property/all?status=available
    """
    try:
        status = request.args.get('status', 'available')
        properties = Property.get_all_properties(status=status)
        
        return jsonify({
            'success': True,
            'total': len(properties),
            'properties': properties
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting all properties: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================
# ENDPOINT 3: GET PROPERTY BY ID (WITH AGENT INFO)
# ============================================================

@property_bp.route('/<int:property_id>', methods=['GET'])
def get_property_detail(property_id):
    """
    Get detailed information about a specific property including agent info
    
    URL: GET /api/property/1
    Returns: property data + agent data
    """
    try:
        # Get property data
        property_data = Property.get_property_by_id(property_id)
        
        if not property_data:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404
        
        # Get agent data if agent_id exists
        agent_data = None
        agent_id = property_data.get('agent_id')
        
        if agent_id:
            agent_data = Agent.get_agent_by_id(agent_id)
            logger.info(f"Agent {agent_id} fetched for property {property_id}")
        
        logger.info(f"Property {property_id} detail retrieved")
        
        return jsonify({
            'success': True,
            'property': property_data,
            'agent': agent_data
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting property: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500