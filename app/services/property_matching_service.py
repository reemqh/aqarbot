from xml.sax.handler import all_properties

from app.models.property import Property
from app.models.chat_session import ChatSession
import logging

logger = logging.getLogger(__name__)

class PropertyMatchingService:
    """Property matching service - match user preferences to properties"""
    
    # Scoring weights
    WEIGHT_BUDGET = 0.30      # 30%
    WEIGHT_LOCATION = 0.25    # 25%
    WEIGHT_TYPE = 0.15        # 15%
    WEIGHT_BEDROOMS = 0.15    # 15%
    WEIGHT_FACILITIES = 0.15   # 15%
    
    @staticmethod
    def match_preferences_to_properties(preferences, limit=10):
        """
        Match user preferences to properties and return sorted results
        
        Args:
            preferences: Dict with budget_min, budget_max, location, property_type, num_bedrooms, required_facilities
            limit: Number of top properties to return (default 10)
        
        Returns:
            List of properties with match scores, sorted by score (highest first)
        """
        try:
            logger.info(f"Matching preferences: {preferences}")
            
            # Get all available properties
            all_properties = Property.get_all_properties(status='available')
            
            if not all_properties:
                logger.warning("No available properties found")
                return []
            
            # STEP 1: SCORE - Score all available properties directly
            scored_properties = PropertyMatchingService._score_properties(
                all_properties,
                preferences
            )
            

            
            # STEP 3: SORT - Sort by score (highest first)
            scored_properties.sort(key=lambda x: x['match_score'], reverse=True)
            
            # Return top N
            top_properties = scored_properties[:limit]
            
            logger.info(f"Returning top {len(top_properties)} properties")
            
            return top_properties
        
        except Exception as e:
            logger.error(f"Error in match_preferences_to_properties: {str(e)}")
            return []
    
    @staticmethod
    def _filter_properties(properties, preferences):
        """
        Filter out properties that don't meet basic criteria
        
        Args:
            properties: List of all properties
            preferences: User preferences
        
        Returns:
            Filtered list of candidate properties
        """
        try:
            candidates = []
            
            budget_min = preferences.get('budget_min')
            budget_max = preferences.get('budget_max')
            property_type = preferences.get('property_type')
            num_bedrooms = preferences.get('num_bedrooms')
            
            for prop in properties:
                # Must be in budget range
                if budget_min and budget_max:
                    if prop['price'] < budget_min or prop['price'] > budget_max:
                        continue  # Skip this property
                
                # Must be correct type
                if property_type and prop['property_type'] != property_type:
                    continue  # Skip this property
                
                # Must have at least required bedrooms
                if num_bedrooms and prop['num_bedrooms'] < num_bedrooms:
                    continue  # Skip this property
                
                # If passes all filters, add to candidates
                candidates.append(prop)
            
            logger.info(f"Filtered {len(properties)} properties to {len(candidates)} candidates")
            return candidates
        
        except Exception as e:
            logger.error(f"Error filtering properties: {str(e)}")
            return []
    
    @staticmethod
    def _score_properties(properties, preferences):
        """
        Calculate match score for each property
        
        Args:
            properties: List of candidate properties
            preferences: User preferences
        
        Returns:
            List of properties with match_score added
        """
        try:
            for prop in properties:
                score = 0
                
                # 1. BUDGET SCORE (30 points max)
                budget_score = PropertyMatchingService._calculate_budget_score(prop, preferences)
                score += budget_score * PropertyMatchingService.WEIGHT_BUDGET * 100
                
                # 2. LOCATION SCORE (25 points max)
                location_score = PropertyMatchingService._calculate_location_score(prop, preferences)
                score += location_score * PropertyMatchingService.WEIGHT_LOCATION * 100
                
                # 3. TYPE SCORE (15 points max)
                type_score = PropertyMatchingService._calculate_type_score(prop, preferences)
                score += type_score * PropertyMatchingService.WEIGHT_TYPE * 100
                
                # 4. BEDROOMS SCORE (15 points max)
                bedroom_score = PropertyMatchingService._calculate_bedroom_score(prop, preferences)
                score += bedroom_score * PropertyMatchingService.WEIGHT_BEDROOMS * 100
                
                # 5. FACILITIES SCORE (15 points max)
                facility_score = PropertyMatchingService._calculate_facility_score(prop, preferences)
                score += facility_score * PropertyMatchingService.WEIGHT_FACILITIES * 100
                
                prop['match_score'] = round(score, 2)
            
            return properties
        
        except Exception as e:
            logger.error(f"Error scoring properties: {str(e)}")
            return properties
    
    @staticmethod
    def _calculate_budget_score(property_data, preferences):
        """
        Score based on how close price is to user's budget range
        
        Returns: 0-1 (normalized score)
        """
        try:
            budget_min = preferences.get('budget_min')
            budget_max = preferences.get('budget_max')
            price = property_data.get('price')
            
            if not (budget_min and budget_max and price):
                return 0
            
            # Perfect if in middle of range
            mid_range = (budget_min + budget_max) / 2
            range_span = budget_max - budget_min
            
            # How far from middle?
            distance_from_mid = abs(price - mid_range)
            
            # If within range, give points based on closeness to middle
            if distance_from_mid <= range_span / 2:
                # Closer to middle = higher score
                score = 1 - (distance_from_mid / (range_span / 2))
                return max(0, score)
            else:
                return 0
        
        except Exception as e:
            logger.error(f"Error calculating budget score: {str(e)}")
            return 0
    
    @staticmethod
    def _calculate_location_score(property_data, preferences):
        """
        Score based on location match
        
        Returns: 0-1 (1 = exact match, 0.6 = partial match, 0 = no match)
        """
        try:
            user_location = preferences.get('location', '').lower()
            prop_location = property_data.get('location', '').lower()
            
            if not user_location or not prop_location:
                return 0
            
            # Exact match
            if user_location == prop_location:
                return 1.0
            
            # Partial match (one contains other)
            if user_location in prop_location or prop_location in user_location:
                return 0.6
            
            return 0
        
        except Exception as e:
            logger.error(f"Error calculating location score: {str(e)}")
            return 0
    
    @staticmethod
    def _calculate_type_score(property_data, preferences):
        """
        Score based on property type match
        
        Returns: 0-1 (1 = match, 0 = no match)
        """
        try:
            user_type = preferences.get('property_type', '').lower()
            prop_type = property_data.get('property_type', '').lower()
            
            if not user_type or not prop_type:
                return 0
            
            if user_type == prop_type:
                return 1.0
            
            return 0
        
        except Exception as e:
            logger.error(f"Error calculating type score: {str(e)}")
            return 0
    
    @staticmethod
    def _calculate_bedroom_score(property_data, preferences):
        """
        Score based on bedroom count
        
        Returns: 0-1 (1 = exact match, 0.7 = more than needed, 0 = less than needed)
        """
        try:
            required_bedrooms = preferences.get('num_bedrooms')
            prop_bedrooms = property_data.get('num_bedrooms')
            
            if not (required_bedrooms and prop_bedrooms):
                return 0
            
            # Exact match = full points
            if prop_bedrooms == required_bedrooms:
                return 1.0
            
            # More bedrooms than needed = partial points (bonus)
            if prop_bedrooms > required_bedrooms:
                return 0.7
            
            # Less bedrooms = no points (filtered out earlier, but just in case)
            return 0
        
        except Exception as e:
            logger.error(f"Error calculating bedroom score: {str(e)}")
            return 0
    
    @staticmethod
    def _calculate_facility_score(property_data, preferences):
        """
        Score based on amenities match
        
        Returns: 0-1 (percentage of requested amenities that property has)
        """
        try:
            required_facilities = preferences.get('required_facilities')
            
            # If user didn't specify facilities, give full points
            if not required_facilities or len(required_facilities) == 0:
                return 1.0
            
            prop_amenities_str = property_data.get('amenities', '')
            if not prop_amenities_str:
                return 0
            
            # Parse property amenities
            prop_amenities = [a.strip().lower() for a in prop_amenities_str.split(',')]
            
            # Parse required facilities
            if isinstance(required_facilities, str):
                # If it's a JSON string, parse it
                try:
                    import json
                    required_facilities = json.loads(required_facilities)
                except:
                    required_facilities = [f.strip().lower() for f in required_facilities.split(',')]
            
            required_facilities = [f.lower() for f in required_facilities]
            
            # Count matches
            matching = 0
            for facility in required_facilities:
                if facility in prop_amenities:
                    matching += 1
            
            # Score = percentage of matched facilities
            score = matching / len(required_facilities)
            return score
        
        except Exception as e:
            logger.error(f"Error calculating facility score: {str(e)}")
            return 0
    
    @staticmethod
    def get_match_score_breakdown(property_data, preferences):
        """
        Get detailed breakdown of match score (for debugging)
        
        Returns:
            Dict with individual scores for each factor
        """
        try:
            return {
                'budget_score': PropertyMatchingService._calculate_budget_score(property_data, preferences),
                'location_score': PropertyMatchingService._calculate_location_score(property_data, preferences),
                'type_score': PropertyMatchingService._calculate_type_score(property_data, preferences),
                'bedroom_score': PropertyMatchingService._calculate_bedroom_score(property_data, preferences),
                'facility_score': PropertyMatchingService._calculate_facility_score(property_data, preferences)
            }
        except Exception as e:
            logger.error(f"Error getting score breakdown: {str(e)}")
            return {}