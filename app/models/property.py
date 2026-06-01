from app.database import db
import logging

logger = logging.getLogger(__name__)

class Property:
    """Property model - manages property listings"""
    
    @staticmethod
    def create_property(agent_id, title, description, property_type, price, location, latitude, longitude, 
                        num_bedrooms, num_bathrooms, area_sqft, amenities, image_url, status='available'):
        """
        Create a new property listing
        
        Args:
            agent_id: Agent ID who listed the property
            title: Property title
            description: Property description
            property_type: apartment, villa, townhouse, etc.
            price: Price in SAR
            location: Location/area name
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            num_bedrooms: Number of bedrooms
            num_bathrooms: Number of bathrooms
            area_sqft: Area in square feet
            amenities: Comma-separated amenities (gym,pool,parking)
            image_url: URL to property image
            status: available, sold, rented
        
        Returns:
            (property_id, message)
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("""
                INSERT INTO properties 
                (agent_id, title, description, property_type, price, location, 
                 latitude, longitude, num_bedrooms, num_bathrooms, area_sqft, 
                 amenities, image_url, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (agent_id, title, description, property_type, price, location, 
                  latitude, longitude, num_bedrooms, num_bathrooms, area_sqft, 
                  amenities, image_url, status))
            
            db.commit()
            
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            property_id = result['id'] if result else None
            
            logger.info(f"Property created successfully: {property_id}")
            return property_id, "Property created successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating property: {str(e)}")
            return None, f"Error creating property: {str(e)}"
    
    @staticmethod
    def get_all_properties(status='available'):
        """
        Get all properties with optional status filter
        
        Args:
            status: Filter by status (available, sold, rented)
        
        Returns:
            List of property dicts
        """
        try:
            cursor = db.get_cursor()
            
            if status:
                cursor.execute("""
                    SELECT 
                        id, agent_id, title, description, property_type, price,
                        location, latitude, longitude, num_bedrooms, num_bathrooms,
                        area_sqft, amenities, image_url, status, created_at
                    FROM properties
                    WHERE status = %s
                    ORDER BY created_at DESC
                """, (status,))
            else:
                cursor.execute("""
                    SELECT 
                        id, agent_id, title, description, property_type, price,
                        location, latitude, longitude, num_bedrooms, num_bathrooms,
                        area_sqft, amenities, image_url, status, created_at
                    FROM properties
                    ORDER BY created_at DESC
                """)
            
            properties = cursor.fetchall()
            
            # Parse amenities from comma-separated string to list
            for prop in properties:
                if prop['amenities']:
                    prop['amenities'] = [a.strip() for a in prop['amenities'].split(',')]
                else:
                    prop['amenities'] = []
            
            return properties if properties else []
        
        except Exception as e:
            logger.error(f"Error getting properties: {str(e)}")
            return []
    
    @staticmethod
    def get_property_by_id(property_id):
        """
        Get single property by ID
        
        Args:
            property_id: Property ID
        
        Returns:
            Property dict or None
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("""
                SELECT 
                    id, agent_id, title, description, property_type, price,
                    location, latitude, longitude, num_bedrooms, num_bathrooms,
                    area_sqft, amenities, image_url, status, created_at
                FROM properties
                WHERE id = %s
            """, (property_id,))
            
            property_data = cursor.fetchone()
            
            if property_data and property_data['amenities']:
                property_data['amenities'] = [a.strip() for a in property_data['amenities'].split(',')]
            
            return property_data
        
        except Exception as e:
            logger.error(f"Error getting property: {str(e)}")
            return None
    
    @staticmethod
    def get_properties_by_agent(agent_id, status='available'):
        """
        Get all properties listed by specific agent
        
        Args:
            agent_id: Agent ID
            status: Filter by status
        
        Returns:
            List of property dicts
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("""
                SELECT 
                    id, agent_id, title, description, property_type, price,
                    location, latitude, longitude, num_bedrooms, num_bathrooms,
                    area_sqft, amenities, image_url, status, created_at
                FROM properties
                WHERE agent_id = %s AND status = %s
                ORDER BY created_at DESC
            """, (agent_id, status))
            
            properties = cursor.fetchall()
            
            for prop in properties:
                if prop['amenities']:
                    prop['amenities'] = [a.strip() for a in prop['amenities'].split(',')]
            
            return properties if properties else []
        
        except Exception as e:
            logger.error(f"Error getting properties by agent: {str(e)}")
            return []
    
    @staticmethod
    def search_properties_by_criteria(property_type=None, location=None, 
                                     min_price=None, max_price=None,
                                     min_bedrooms=None):
        """
        Search properties by multiple criteria
        
        Args:
            property_type: Filter by type
            location: Filter by location
            min_price: Minimum price
            max_price: Maximum price
            min_bedrooms: Minimum bedrooms
        
        Returns:
            List of matching property dicts
        """
        try:
            cursor = db.get_cursor()
            
            query = "SELECT * FROM properties WHERE status = 'available'"
            params = []
            
            if property_type:
                query += " AND property_type = %s"
                params.append(property_type)
            
            if location:
                query += " AND location = %s"
                params.append(location)
            
            if min_price:
                query += " AND price >= %s"
                params.append(min_price)
            
            if max_price:
                query += " AND price <= %s"
                params.append(max_price)
            
            if min_bedrooms:
                query += " AND num_bedrooms >= %s"
                params.append(min_bedrooms)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            properties = cursor.fetchall()
            
            for prop in properties:
                if prop['amenities']:
                    prop['amenities'] = [a.strip() for a in prop['amenities'].split(',')]
            
            return properties if properties else []
        
        except Exception as e:
            logger.error(f"Error searching properties: {str(e)}")
            return []
    
    @staticmethod
    def update_property_status(property_id, status):
        """
        Update property status (available, sold, rented)
        
        Args:
            property_id: Property ID
            status: New status
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            valid_statuses = ['available', 'sold', 'rented']
            if status not in valid_statuses:
                return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            
            cursor.execute("""
                UPDATE properties
                SET status = %s
                WHERE id = %s
            """, (status, property_id))
            
            db.commit()
            
            logger.info(f"Property {property_id} status updated to {status}")
            return True, "Property status updated successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating property status: {str(e)}")
            return False, f"Error updating property: {str(e)}"
    
    @staticmethod
    def delete_property(property_id):
        """
        Delete a property listing
        
        Args:
            property_id: Property ID
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("DELETE FROM properties WHERE id = %s", (property_id,))
            
            db.commit()
            
            logger.info(f"Property deleted: {property_id}")
            return True, "Property deleted successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting property: {str(e)}")
            return False, f"Error deleting property: {str(e)}"