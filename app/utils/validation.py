import logging
import re

logger = logging.getLogger(__name__)

class Validation:
    """Validation functions for chatbot preference collection"""
    
    # Valid locations in Riyadh
    VALID_LOCATIONS = [
        'downtown riyadh',
        'al-olaya',
        'king fahd road',
        'north riyadh',
        'al-nakheel',
        'al-qadsiyah'
    ]
    
    # Valid property types
    VALID_PROPERTY_TYPES = ['apartment', 'villa', 'townhouse']
    
    # Valid amenities
    VALID_AMENITIES = [
        'gym',
        'pool',
        'parking',
        'garden',
        'security',
        'maid_room',
        'garage',
        'home_cinema',
        'playground',
        'concierge'
    ]

    @staticmethod
    def convert_arabic_numerals(text):
        """
        Convert Arabic-Indic numerals (٠-٩) to Western digits (0-9).
        Handles mixed strings like '٤٠٠٠٠٠ إلى ٨٠٠٠٠٠'.
        """
        arabic_to_western = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        return str(text).translate(arabic_to_western)
    
    @staticmethod
    def validate_budget(extracted_value):
        """
        Validate budget range
        
        Args:
            extracted_value: User's budget input (should be formatted as "min-max")
        
        Returns:
            (is_valid, cleaned_value, error_message)
        """
        try:
            if not extracted_value:
                return False, None, "Budget cannot be empty"

            # Convert Arabic-Indic numerals to Western digits first
            extracted_value = Validation.convert_arabic_numerals(extracted_value)

            # Try to extract two numbers
            numbers = re.findall(r'\d+', str(extracted_value))
            
            if len(numbers) < 2:
                return False, None, "Please provide both minimum and maximum budget amount"
            
            budget_min = int(numbers[0])
            budget_max = int(numbers[1])
            
            # Validate ranges
            if budget_min <= 0 or budget_max <= 0:
                return False, None, "Budget amounts must be positive numbers"
            
            if budget_min > budget_max:
                # Swap if reversed
                budget_min, budget_max = budget_max, budget_min
            
            # Reasonable budget range check (50k to 5M SAR)
            if budget_min < 50000:
                return False, None, "Minimum budget seems too low (minimum 50,000 SAR)"
            
            if budget_max > 5000000:
                return False, None, "Maximum budget seems too high (maximum 5,000,000 SAR)"
            
            cleaned_value = {
                'budget_min': budget_min,
                'budget_max': budget_max
            }
            
            return True, cleaned_value, None
        
        except Exception as e:
            logger.error(f"Error validating budget: {str(e)}")
            return False, None, f"Invalid budget format: {str(e)}"
    
    @staticmethod
    def validate_location(extracted_value):
        """
        Validate location
        
        Args:
            extracted_value: User's location input
        
        Returns:
            (is_valid, cleaned_value, error_message)
        """
        try:
            if not extracted_value:
                return False, None, "Location cannot be empty"
            
            location_lower = str(extracted_value).strip().lower()
            
            # Check if location matches valid locations (partial match)
            for valid_loc in Validation.VALID_LOCATIONS:
                if valid_loc in location_lower or location_lower in valid_loc:
                    return True, valid_loc, None
            
            # If no match, still accept but warn
            logger.warning(f"Location '{extracted_value}' not in predefined list but accepting")
            return True, location_lower, None
        
        except Exception as e:
            logger.error(f"Error validating location: {str(e)}")
            return False, None, f"Invalid location: {str(e)}"
    
    @staticmethod
    def validate_property_type(extracted_value):
        """
        Validate property type
        
        Args:
            extracted_value: User's property type input
        
        Returns:
            (is_valid, cleaned_value, error_message)
        """
        try:
            if not extracted_value:
                return False, None, "Property type cannot be empty"
            
            property_type_lower = str(extracted_value).strip().lower()
            
            # Check if type is valid
            for valid_type in Validation.VALID_PROPERTY_TYPES:
                if valid_type in property_type_lower:
                    return True, valid_type, None
            
            return False, None, f"Property type must be one of: {', '.join(Validation.VALID_PROPERTY_TYPES)}"
        
        except Exception as e:
            logger.error(f"Error validating property type: {str(e)}")
            return False, None, f"Invalid property type: {str(e)}"
    
    @staticmethod
    def validate_bedrooms(extracted_value):
        """
        Validate number of bedrooms
        
        Args:
            extracted_value: User's bedroom count input
        
        Returns:
            (is_valid, cleaned_value, error_message)
        """
        try:
            if not extracted_value:
                return False, None, "Number of bedrooms cannot be empty"

            # Convert Arabic-Indic numerals to Western digits first
            extracted_value = Validation.convert_arabic_numerals(extracted_value)

            # Extract first number from string
            numbers = re.findall(r'\d+', str(extracted_value))
            
            if not numbers:
                return False, None, "Please provide a number for bedrooms"
            
            num_bedrooms = int(numbers[0])
            
            # Validate range (1-10 bedrooms)
            if num_bedrooms < 1:
                return False, None, "Number of bedrooms must be at least 1"
            
            if num_bedrooms > 10:
                return False, None, "Number of bedrooms should not exceed 10"
            
            return True, num_bedrooms, None
        
        except Exception as e:
            logger.error(f"Error validating bedrooms: {str(e)}")
            return False, None, f"Invalid bedroom count: {str(e)}"
    
    @staticmethod
    def validate_facilities(extracted_value):
        """
        Validate amenities/facilities
        
        Args:
            extracted_value: User's facilities input
        
        Returns:
            (is_valid, cleaned_value, error_message)
        """
        try:
            if not extracted_value:
                # Facilities are optional
                return True, [], None
            
            # Split by comma and clean
            facilities_str = str(extracted_value).lower()
            
            # Extract facility names
            mentioned_facilities = []
            
            for valid_facility in Validation.VALID_AMENITIES:
                if valid_facility.replace('_', ' ') in facilities_str or valid_facility in facilities_str:
                    mentioned_facilities.append(valid_facility)
            
            # If no valid facilities found, still accept (user might want general properties)
            if not mentioned_facilities:
                logger.warning(f"No recognized facilities in: {extracted_value}")
                return True, [], None
            
            return True, mentioned_facilities, None
        
        except Exception as e:
            logger.error(f"Error validating facilities: {str(e)}")
            return False, None, f"Invalid facilities format: {str(e)}"
    
    @staticmethod
    def validate_stage_answer(stage_number, extracted_value):
        """
        Validate answer for a specific stage
        
        Args:
            stage_number: Current stage (1-5)
            extracted_value: User's answer
        
        Returns:
            (is_valid, cleaned_value, error_message)
        """
        try:
            if stage_number == 1:
                return Validation.validate_budget(extracted_value)
            elif stage_number == 2:
                return Validation.validate_location(extracted_value)
            elif stage_number == 3:
                return Validation.validate_property_type(extracted_value)
            elif stage_number == 4:
                return Validation.validate_bedrooms(extracted_value)
            elif stage_number == 5:
                return Validation.validate_facilities(extracted_value)
            else:
                return False, None, f"Invalid stage number: {stage_number}"
        
        except Exception as e:
            logger.error(f"Error validating stage answer: {str(e)}")
            return False, None, f"Validation error: {str(e)}"