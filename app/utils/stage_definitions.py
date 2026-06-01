import logging

logger = logging.getLogger(__name__)

class StageDefinitions:
    """Stage definitions for chatbot preference collection - Bilingual (English & Arabic)"""
    
    # Define all 5 stages with BOTH English and Arabic questions
    STAGES = {
        1: {
            'name': 'Budget',
            'question_en': 'What is your budget range? Please provide minimum and maximum amount in SAR (e.g., 400000 to 800000)',
            'question_ar': 'ما هي ميزانيتك؟ يرجى إدخال الحد الأدنى والأقصى بالريال السعودي (مثال: من 400000 إلى 800000)',
            'field_name': 'budget_min and budget_max',
            'expected_format': 'Two numbers representing min-max range',
            'examples': [
                'Between 400000 and 800000',
                '300k to 600k',
                '500000 minimum, 1000000 maximum',
                'Min 450k, Max 850k'
            ]
        },
        2: {
            'name': 'Location',
            'question_en': 'Which location in Riyadh interests you? (e.g., Downtown, Al-Olaya, King Fahd Road, North Riyadh, Al-Nakheel, Al-Qadsiyah)',
            'question_ar': 'أي منطقة في الرياض تفضل؟ (مثال: وسط البلد، العليا، طريق الملك فهد، شمال الرياض، النخيل، القادسية)',
            'field_name': 'location',
            'expected_format': 'City or area name',
            'examples': [
                'Downtown Riyadh',
                'Al-Olaya',
                'King Fahd Road',
                'North Riyadh area',
                'Al-Nakheel'
            ]
        },
        3: {
            'name': 'Property Type',
            'question_en': 'What type of property are you looking for? (apartment, villa, or townhouse)',
            'question_ar': 'ما نوع العقار الذي تبحث عنه؟ (شقة أو فيلا أو دوبلكس)',
            'field_name': 'property_type',
            'expected_format': 'apartment, villa, or townhouse',
            'examples': [
                'apartment',
                'villa',
                'townhouse',
                'a villa',
                'apartments please'
            ]
        },
        4: {
            'name': 'Number of Bedrooms',
            'question_en': 'How many bedrooms do you need?',
            'question_ar': 'كم عدد غرف النوم التي تحتاج؟',
            'field_name': 'num_bedrooms',
            'expected_format': 'Positive integer (1, 2, 3, 4, 5, etc.)',
            'examples': [
                '2 bedrooms',
                '3',
                'Four bedrooms',
                'I need 5 rooms'
            ]
        },
        5: {
            'name': 'Facilities/Amenities',
            'question_en': 'What facilities or amenities are important to you? (e.g., gym, pool, parking, garden, security, maid room)',
            'question_ar': 'ما المرافق والتسهيلات المهمة لك؟ (مثال: صالة رياضية، حمام سباحة، موقف سيارات، حديقة، أمن، غرفة خادمة)',
            'field_name': 'required_facilities',
            'expected_format': 'List of amenities (can be comma-separated or natural language)',
            'examples': [
                'gym and pool',
                'gym, pool, parking',
                'I want a garden and parking',
                'security and maid room',
                'pool, gym, parking, security'
            ]
        }
    }
    
    @staticmethod
    def detect_language(user_message):
        """
        Detect if user message is in Arabic or English
        
        Args:
            user_message: User's message
        
        Returns:
            'ar' for Arabic, 'en' for English
        """
        try:
            # Check for Arabic letters AND Arabic-Indic numerals (٠١٢٣٤٥٦٧٨٩)
            arabic_chars = set('ابجدهوزحطيكلمنسعفصقرشتثخذضظغ' +
                              'أةئؤبآىءيهوةۀں' +
                              '٠١٢٣٤٥٦٧٨٩')

            message_chars = set(user_message)

            if message_chars & arabic_chars:
                return 'ar'
            else:
                # Ambiguous (pure digits) — let the caller use page language
                return None
        except Exception as e:
            logger.error(f"Error detecting language: {str(e)}")
            return None  # Let caller decide
    
    @staticmethod
    def get_stage_info(stage_number):
        """
        Get information for a specific stage
        
        Args:
            stage_number: Stage number (1-5)
        
        Returns:
            Stage definition dict or None
        """
        try:
            if stage_number not in StageDefinitions.STAGES:
                logger.warning(f"Invalid stage number: {stage_number}")
                return None
            
            return StageDefinitions.STAGES[stage_number]
        
        except Exception as e:
            logger.error(f"Error getting stage info: {str(e)}")
            return None
    
    @staticmethod
    def get_stage_question(stage_number, language='en'):
        """
        Get the bot question for a specific stage
        
        Args:
            stage_number: Stage number (1-5)
            language: 'en' for English, 'ar' for Arabic
        
        Returns:
            Question string or None
        """
        try:
            stage_info = StageDefinitions.get_stage_info(stage_number)
            
            if not stage_info:
                return None
            
            if language == 'ar':
                return stage_info.get('question_ar', stage_info.get('question_en'))
            else:
                return stage_info.get('question_en')
        
        except Exception as e:
            logger.error(f"Error getting stage question: {str(e)}")
            return None
    
    @staticmethod
    def get_next_stage(current_stage):
        """
        Get next stage number
        
        Args:
            current_stage: Current stage number
        
        Returns:
            Next stage number (1-6), or None if already at stage 6
        """
        try:
            if current_stage < 5:
                return current_stage + 1
            elif current_stage == 5:
                return 6  # Stage 6 = preferences complete
            else:
                return None  # Already completed
        
        except Exception as e:
            logger.error(f"Error getting next stage: {str(e)}")
            return None
    
    @staticmethod
    def is_final_stage(stage_number):
        """
        Check if this is the final stage
        
        Args:
            stage_number: Stage number
        
        Returns:
            True if stage 5 (final preference stage), False otherwise
        """
        try:
            return stage_number == 5
        
        except Exception as e:
            logger.error(f"Error checking final stage: {str(e)}")
            return False
    
    @staticmethod
    def is_preferences_complete(stage_number):
        """
        Check if all preferences have been collected
        
        Args:
            stage_number: Current stage number
        
        Returns:
            True if stage 6 (completed), False otherwise
        """
        try:
            return stage_number >= 6
        
        except Exception as e:
            logger.error(f"Error checking preferences complete: {str(e)}")
            return False
    
    @staticmethod
    def get_stage_name(stage_number):
        """
        Get human-readable name for a stage
        
        Args:
            stage_number: Stage number (1-5)
        
        Returns:
            Stage name string
        """
        try:
            stage_info = StageDefinitions.get_stage_info(stage_number)
            return stage_info['name'] if stage_info else "Unknown"
        
        except Exception as e:
            logger.error(f"Error getting stage name: {str(e)}")
            return "Unknown"