from app.database import db
import json
import datetime
import logging

logger = logging.getLogger(__name__)

class ChatSession:
    """Chat session model - manages conversation state and preference collection"""
    
    @staticmethod
    def create_session(user_id):
        """
        Create a new chat session for user
        
        Args:
            user_id: User ID starting the conversation
        
        Returns:
            (session_id, message) - session_id if success, None if failed
        """
        try:
            cursor = db.get_cursor()
            
            # Initialize preferences JSON with all fields as None
            initial_preferences = {
                'budget_min': None,
                'budget_max': None,
                'location': None,
                'property_type': None,
                'num_bedrooms': None,
                'required_facilities': None
            }
            
            # Insert new session
            cursor.execute("""
                INSERT INTO chat_sessions 
                (user_id, status, current_stage, preferences, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                'active',
                1,
                json.dumps(initial_preferences),
                datetime.datetime.now()
            ))
            
            db.commit()
            
            # Get the newly created session ID
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            session_id = result['id'] if result else None
            
            logger.info(f"Chat session created successfully: {session_id} for user: {user_id}")
            return session_id, "Session created successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating chat session: {str(e)}")
            return None, f"Error creating session: {str(e)}"
    
    @staticmethod
    def get_session(session_id):
        """
        Get chat session by ID
        
        Args:
            session_id: Chat session ID
        
        Returns:
            Session dict with preferences parsed from JSON, or None if not found
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT 
                    id, 
                    user_id, 
                    status, 
                    current_stage, 
                    preferences,
                    created_at,
                    updated_at
                FROM chat_sessions 
                WHERE id = %s
            """, (session_id,))
            
            session = cursor.fetchone()
            
            if session and session['preferences']:
                # Parse JSON preferences
                session['preferences'] = json.loads(session['preferences'])
            
            return session
        
        except Exception as e:
            logger.error(f"Error getting chat session: {str(e)}")
            return None
    
    @staticmethod
    def save_preference(session_id, field_name, value):
        """
        Save a single preference field to the session
        
        Args:
            session_id: Chat session ID
            field_name: Field to update (budget_min, budget_max, location, property_type, num_bedrooms, required_facilities)
            value: Value to save
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            # Get current preferences
            cursor.execute("""
                SELECT preferences 
                FROM chat_sessions 
                WHERE id = %s
            """, (session_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return False, "Session not found"
            
            # Parse current preferences
            preferences = json.loads(result['preferences']) if result['preferences'] else {}
            
            # Update the specific field
            allowed_fields = ['budget_min', 'budget_max', 'location', 'property_type', 'num_bedrooms', 'required_facilities']
            
            if field_name not in allowed_fields:
                return False, f"Invalid field: {field_name}"
            
            preferences[field_name] = value
            
            # Update preferences in database
            cursor.execute("""
                UPDATE chat_sessions 
                SET preferences = %s, updated_at = NOW()
                WHERE id = %s
            """, (json.dumps(preferences), session_id))
            
            db.commit()
            
            logger.info(f"Preference saved - Session {session_id}: {field_name} = {value}")
            return True, "Preference saved successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving preference: {str(e)}")
            return False, f"Error saving preference: {str(e)}"
    
    @staticmethod
    def update_stage(session_id, stage):
        """
        Update current stage of conversation
        
        Args:
            session_id: Chat session ID
            stage: Next stage (1-5, or 6 for completed)
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            # Validate stage
            if stage < 1 or stage > 6:
                return False, "Invalid stage number (should be 1-6)"
            
            # If stage 6, mark as completed
            status = 'completed' if stage == 6 else 'active'
            
            cursor.execute("""
                UPDATE chat_sessions 
                SET current_stage = %s, status = %s, updated_at = NOW()
                WHERE id = %s
            """, (stage, status, session_id))
            
            db.commit()
            
            logger.info(f"Stage updated - Session {session_id}: stage {stage}, status {status}")
            return True, f"Stage updated to {stage}"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating stage: {str(e)}")
            return False, f"Error updating stage: {str(e)}"
    
    @staticmethod
    def get_all_preferences(session_id):
        """
        Get all collected preferences for a session
        
        Args:
            session_id: Chat session ID
        
        Returns:
            Preferences dict or None if session not found
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT preferences 
                FROM chat_sessions 
                WHERE id = %s
            """, (session_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return None
            
            # Parse and return preferences
            preferences = json.loads(result['preferences']) if result['preferences'] else {}
            return preferences
        
        except Exception as e:
            logger.error(f"Error getting preferences: {str(e)}")
            return None
    
    @staticmethod
    def is_preferences_complete(session_id):
        """
        Check if all 5 preferences have been collected
        
        Args:
            session_id: Chat session ID
        
        Returns:
            True if all fields filled, False otherwise
        """
        try:
            preferences = ChatSession.get_all_preferences(session_id)
            
            if not preferences:
                return False
            
            # Check if all required fields are filled (not None)
            required_fields = ['budget_min', 'budget_max', 'location', 'property_type', 'num_bedrooms', 'required_facilities']
            
            for field in required_fields:
                if preferences.get(field) is None:
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking preferences complete: {str(e)}")
            return False
    
    @staticmethod
    def mark_session_complete(session_id):
        """
        Mark session as completed (all preferences collected)
        
        Args:
            session_id: Chat session ID
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("""
                UPDATE chat_sessions 
                SET status = 'completed', current_stage = 6, updated_at = NOW()
                WHERE id = %s
            """, (session_id,))
            
            db.commit()
            
            logger.info(f"Session marked as completed: {session_id}")
            return True, "Session marked as completed"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking session complete: {str(e)}")
            return False, f"Error marking session complete: {str(e)}"
    
    @staticmethod
    def get_session_by_user(user_id, status='active'):
        """
        Get most recent session for a user by status
        
        Args:
            user_id: User ID
            status: Session status (active, completed, archived)
        
        Returns:
            Session dict or None if not found
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT 
                    id, 
                    user_id, 
                    status, 
                    current_stage, 
                    preferences,
                    created_at,
                    updated_at
                FROM chat_sessions 
                WHERE user_id = %s AND status = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id, status))
            
            session = cursor.fetchone()
            
            if session and session['preferences']:
                # Parse JSON preferences
                session['preferences'] = json.loads(session['preferences'])
            
            return session
        
        except Exception as e:
            logger.error(f"Error getting session by user: {str(e)}")
            return None
    
    @staticmethod
    def archive_session(session_id):
        """
        Archive a session (user started new conversation)
        
        Args:
            session_id: Chat session ID
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("""
                UPDATE chat_sessions 
                SET status = 'archived', updated_at = NOW()
                WHERE id = %s
            """, (session_id,))
            
            db.commit()
            
            logger.info(f"Session archived: {session_id}")
            return True, "Session archived"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error archiving session: {str(e)}")
            return False, f"Error archiving session: {str(e)}"
    
    @staticmethod
    def get_all_sessions_by_user(user_id):
        """
        Get all sessions for a user
        
        Args:
            user_id: User ID
        
        Returns:
            List of sessions
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT 
                    id, 
                    user_id, 
                    status, 
                    current_stage, 
                    preferences,
                    created_at,
                    updated_at
                FROM chat_sessions 
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            
            sessions = cursor.fetchall()
            
            for session in sessions:
                if session['preferences']:
                    session['preferences'] = json.loads(session['preferences'])
            
            return sessions
        
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return []

    @staticmethod
    def save_messages(session_id, transcript):
        """
        Bulk-save transcript messages to chat_messages table.
        Called only once when a chat is completed.

        Args:
            session_id: Chat session ID
            transcript: List of {sender, text} dicts

        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            for entry in transcript:
                cursor.execute("""
                    INSERT INTO chat_messages (session_id, sender, message)
                    VALUES (%s, %s, %s)
                """, (session_id, entry.get('sender'), entry.get('text')))
            db.commit()
            logger.info(f"Transcript saved for session {session_id}: {len(transcript)} messages")
            return True, "Transcript saved"
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving transcript: {str(e)}")
            return False, str(e)

    @staticmethod
    def get_completed_sessions(user_id):
        """
        Get all completed sessions for a user with their messages.

        Args:
            user_id: User ID

        Returns:
            List of session dicts, each containing messages list
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT id, status, preferences, created_at
                FROM chat_sessions
                WHERE user_id = %s AND status = 'completed'
                ORDER BY created_at DESC
            """, (user_id,))
            sessions = cursor.fetchall()

            result = []
            for session in sessions:
                prefs = json.loads(session['preferences']) if session['preferences'] else {}

                # Fetch messages for this session
                cursor.execute("""
                    SELECT sender, message, created_at
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                """, (session['id'],))
                messages = cursor.fetchall()

                result.append({
                    'session_id': session['id'],
                    'created_at': session['created_at'].strftime('%Y-%m-%d %H:%M') if session['created_at'] else '',
                    'preferences': prefs,
                    'messages': [{'sender': m['sender'], 'text': m['message']} for m in messages]
                })

            return result
        except Exception as e:
            logger.error(f"Error getting completed sessions: {str(e)}")
            return []