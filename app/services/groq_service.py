from groq import Groq
from app.config import Config
from app.utils.stage_definitions import StageDefinitions
import json
import logging

logger = logging.getLogger(__name__)

class GroqService:
    """Groq AI service - Extract preferences from user input"""
    
    MODEL = "llama-3.1-8b-instant"
    
    @staticmethod
    def extract_stage_value(stage_number, user_message, already_collected_prefs=None):
        """
        Extract preference value for current stage using Groq
        
        Args:
            stage_number: Current stage (1-5)
            user_message: User's message
            already_collected_prefs: Dict of already collected preferences
        
        Returns:
            {
                "extracted_value": extracted value,
                "is_valid": true/false,
                "bot_response": conversational response,
                "error": error message if any
            }
        """
        try:
            # Get stage info
            stage_info = StageDefinitions.get_stage_info(stage_number)
            if not stage_info:
                return {
                    "extracted_value": None,
                    "is_valid": False,
                    "bot_response": "Invalid stage",
                    "error": f"Unknown stage: {stage_number}"
                }
            
            # Build context string
            already_collected = already_collected_prefs or {}
            context_str = "Already collected:\n"
            for key, value in already_collected.items():
                if value is not None:
                    context_str += f"- {key}: {value}\n"
            
            # Build system prompt
            system_prompt = f"""
You are a helpful real estate chatbot assistant. Your job is to extract preference information from the user's message.

CURRENT STAGE: {stage_number} - {stage_info['name']}

WHAT WE NEED: {stage_info['field_name']}
EXPECTED FORMAT: {stage_info['expected_format']}

EXAMPLES OF VALID ANSWERS:
{chr(10).join([f"- {ex}" for ex in stage_info['examples'][:3]])}

{context_str}

INSTRUCTIONS:
1. Extract the preference value from the user's message for THIS STAGE ONLY
2. Be flexible with how users express their preferences
3. Ask for clarification if the answer is unclear
4. Return a JSON response with exactly these fields:
   - extracted_value: The extracted value (null if not clear)
   - is_valid: true if you extracted a valid value, false if unclear/invalid
   - bot_response: A friendly, conversational response

If the user doesn't provide clear information for this stage, ask them to clarify.
Always be conversational and helpful.

RESPOND ONLY WITH VALID JSON, NO ADDITIONAL TEXT.
"""
            
            # Call Groq
            client = Groq(api_key=Config.GROQ_API_KEY)
            
            completion = client.chat.completions.create(
                model=GroqService.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = completion.choices[0].message.content
            logger.info(f"Groq response for stage {stage_number}: {response_text}")
            
            # Parse JSON response
            try:
                groq_response = json.loads(response_text)
            except json.JSONDecodeError:
                # If response isn't JSON, try to extract it
                logger.warning(f"Groq response not valid JSON, attempting to parse: {response_text}")
                
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    groq_response = json.loads(json_match.group())
                else:
                    return {
                        "extracted_value": None,
                        "is_valid": False,
                        "bot_response": "Sorry, I didn't understand that. " + stage_info['question'],
                        "error": "Failed to parse Groq response"
                    }
            
            # Validate response structure
            if "extracted_value" not in groq_response:
                groq_response["extracted_value"] = None
            if "is_valid" not in groq_response:
                groq_response["is_valid"] = False
            if "bot_response" not in groq_response:
                groq_response["bot_response"] = stage_info['question']
            
            logger.info(f"Parsed Groq response: {groq_response}")
            
            return groq_response
        
        except Exception as e:
            logger.error(f"Error in extract_stage_value: {str(e)}")
            return {
                "extracted_value": None,
                "is_valid": False,
                "bot_response": "I encountered an error processing your message. Could you please rephrase?",
                "error": str(e)
            }
    
    @staticmethod
    def test_connection():
        """
        Test Groq API connection
        
        Returns:
            (success: bool, message: str)
        """
        try:
            client = Groq(api_key=Config.GROQ_API_KEY)
            
            completion = client.chat.completions.create(
                model=GroqService.MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": "Say 'Hello' only"
                    }
                ],
                max_tokens=10
            )
            
            response = completion.choices[0].message.content
            logger.info(f"Groq connection test successful: {response}")
            
            return True, f"Connection successful. Response: {response}"
        
        except Exception as e:
            logger.error(f"Groq connection test failed: {str(e)}")
            return False, f"Connection failed: {str(e)}"