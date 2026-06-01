from app.models.chat_session import ChatSession
from app.services.groq_service import GroqService
from app.utils.stage_definitions import StageDefinitions
from app.utils.validation import Validation
import json
import logging

logger = logging.getLogger(__name__)

class ChatbotService:
    """Chatbot service - orchestrates preference collection conversation"""
    
    @staticmethod
    def start_chat(user_id):
        """
        Start a new chat session
        
        Args:
            user_id: User ID starting the chat
        
        Returns:
            {
                "session_id": session_id,
                "first_question": "What is your budget...?",
                "stage": 1
            }
        """
        try:
            # Create NEW session
            session_id, msg = ChatSession.create_session(user_id)
            
            if session_id is None:
                return {
                    "success": False,
                    "error": msg
                }
            
            # Get first question (default English)
            first_question = StageDefinitions.get_stage_question(1, language='en')
            
            logger.info(f"New chat session started for user {user_id}, session {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "first_question": first_question,
                "stage": 1,
                "message": "Welcome! Let's find your perfect property. I'll ask you a few questions."
            }
        
        except Exception as e:
            logger.error(f"Error starting chat: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def process_user_message(session_id, user_message, page_lang='en'):
        """
        Process user message and progress conversation
        
        Args:
            session_id: Chat session ID
            user_message: User's message
        
        Returns:
            {
                "success": true/false,
                "current_stage": current stage,
                "next_question": question for next stage (if continuing),
                "preferences_complete": true if all 5 collected,
                "collected_preferences": {...},
                "error": error message if any
            }
        """
        try:
            # Get current session
            session = ChatSession.get_session(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            current_stage = session['current_stage']
            current_prefs = session['preferences']
            
            logger.info(f"Processing message for session {session_id}, stage {current_stage}")
            
            # DETECT LANGUAGE from user message (use original for accurate detection)
            detected_language = StageDefinitions.detect_language(user_message)
            # If ambiguous (pure digits), fall back to the page language sent by frontend
            if detected_language is None:
                detected_language = page_lang
            logger.info(f"Detected language: {detected_language} (page_lang: {page_lang})")

            # CHECK IF ALREADY COMPLETED
            if StageDefinitions.is_preferences_complete(current_stage):
                return {
                    "success": True,
                    "current_stage": current_stage,
                    "preferences_complete": True,
                    "message": "All preferences already collected",
                    "collected_preferences": current_prefs
                }

            # SANITIZE for Groq: For Stage 1 (budget), auto-format long numbers with commas
            # This prevents the AI from miscounting zeros in strings like '400000'
            # We use a separate variable so the original is preserved for language detection
            groq_message = user_message
            if current_stage == 1:
                import re
                # Format Western digits (400000 → 400,000)
                groq_message = re.sub(r'(\d)(?=(\d{3})+(?!\d))', r'\1,', user_message)
                # Format Arabic-Indic digits (٤٠٠٠٠٠ → ٤٠٠،٠٠٠)
                groq_message = re.sub(r'([٠-٩])(?=([٠-٩]{3})+(?![٠-٩]))', r'\1،', groq_message)
                logger.info(f"Budget message formatted for Groq: '{user_message}' → '{groq_message}'")
            
            # Step 1: Send to Groq for extraction
            groq_response = GroqService.extract_stage_value(
                current_stage,
                groq_message,
                current_prefs
            )
            
            logger.info(f"Groq response: {groq_response}")
            
            # Check if Groq found a valid value
            if not groq_response.get('is_valid', False):
                # Groq couldn't extract, ask for clarification
                logger.info(f"Invalid extraction for stage {current_stage}")
                
                # Get question in detected language
                clarification_question = StageDefinitions.get_stage_question(
                    current_stage, 
                    language=detected_language
                )
                
                return {
                    "success": True,
                    "current_stage": current_stage,
                    "preferences_complete": False,
                    "next_question": groq_response.get('bot_response', clarification_question),
                    "validation_error": True,
                    "collected_preferences": current_prefs
                }
            
            # Step 2: Validate with our validation functions
            extracted_value = groq_response.get('extracted_value')
            
            is_valid, cleaned_value, error_msg = Validation.validate_stage_answer(
                current_stage,
                extracted_value
            )
            
            if not is_valid:
                # Validation failed
                logger.warning(f"Validation failed for stage {current_stage}: {error_msg}")
                
                # Pick bilingual error prefix
                error_prefix = "يرجى تقديم إجابة صالحة." if detected_language == 'ar' else "I need a valid answer."
                
                return {
                    "success": True,
                    "current_stage": current_stage,
                    "preferences_complete": False,
                    "next_question": f"{error_prefix} {error_msg}",
                    "validation_error": True,
                    "collected_preferences": current_prefs
                }
            
            # Step 3: Save to session
            if current_stage == 1:
                ChatSession.save_preference(session_id, 'budget_min', cleaned_value.get('budget_min'))
                ChatSession.save_preference(session_id, 'budget_max', cleaned_value.get('budget_max'))
            elif current_stage == 5:
                ChatSession.save_preference(session_id, 'required_facilities', json.dumps(cleaned_value))
            else:
                field_mapping = {
                    2: 'location',
                    3: 'property_type',
                    4: 'num_bedrooms'
                }
                field_name = field_mapping.get(current_stage)
                ChatSession.save_preference(session_id, field_name, cleaned_value)
            
            logger.info(f"Saved preference for stage {current_stage}: {cleaned_value}")
            
            # Step 4: Check if all 5 stages complete
            next_stage = StageDefinitions.get_next_stage(current_stage)
            
            if next_stage > 5:
                # All preferences collected
                ChatSession.mark_session_complete(session_id)
                
                # Get final preferences
                final_prefs = ChatSession.get_all_preferences(session_id)
                
                # Completion message in detected language
                completion_msg_en = "Perfect! I have all your preferences. Let me find the best properties for you!"
                completion_msg_ar = "ممتاز! لدي جميع تفضيلاتك. دعني أبحث عن أفضل العقارات بالنسبة لك!"
                
                completion_msg = completion_msg_ar if detected_language == 'ar' else completion_msg_en
                
                return {
                    "success": True,
                    "current_stage": next_stage,
                    "preferences_complete": True,
                    "message": completion_msg,
                    "collected_preferences": final_prefs
                }
            
            # Step 5: Return next question in DETECTED LANGUAGE
            next_question = StageDefinitions.get_stage_question(
                next_stage, 
                language=detected_language
            )
            
            # Update session stage
            ChatSession.update_stage(session_id, next_stage)
            
            # Get updated preferences
            updated_prefs = ChatSession.get_all_preferences(session_id)
            
            return {
                "success": True,
                "current_stage": next_stage,
                "preferences_complete": False,
                "next_question": next_question,
                "message": groq_response.get('bot_response', ''),
                "collected_preferences": updated_prefs
            }
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_session_progress(session_id):
        """
        Get current session progress
        
        Args:
            session_id: Chat session ID
        
        Returns:
            Session info dict
        """
        try:
            session = ChatSession.get_session(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            return {
                "success": True,
                "session_id": session['id'],
                "user_id": session['user_id'],
                "current_stage": session['current_stage'],
                "status": session['status'],
                "collected_preferences": session['preferences'],
                "preferences_complete": StageDefinitions.is_preferences_complete(session['current_stage'])
            }
        
        except Exception as e:
            logger.error(f"Error getting session progress: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }