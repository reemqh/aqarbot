from app.database import db
import logging

logger = logging.getLogger(__name__)

class Agent:
    """Agent model - manages real estate agents"""
    
    @staticmethod
    def create_agent(name, email, phone_number, agency_name, specializations='', rating=0.0):
        """
        Create a new agent
        
        Args:
            name: Agent name
            email: Agent email
            phone_number: Agent phone number
            agency_name: Agency/company name
            specializations: Comma-separated specializations (luxury, commercial, residential)
            rating: Agent rating (0-5)
        
        Returns:
            (agent_id, message)
        """
        try:
            cursor = db.get_cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM agents WHERE email = %s", (email,))
            existing = cursor.fetchone()
            
            if existing:
                return None, "Agent email already exists"
            
            cursor.execute("""
                INSERT INTO agents 
                (name, email, phone_number, agency_name, specializations, rating, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (name, email, phone_number, agency_name, specializations, rating))
            
            db.commit()
            
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            agent_id = result['id'] if result else None
            
            logger.info(f"Agent created successfully: {agent_id}")
            return agent_id, "Agent created successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating agent: {str(e)}")
            return None, f"Error creating agent: {str(e)}"
    
    @staticmethod
    def get_all_agents(rating_min=None):
        """
        Get all agents with optional minimum rating filter
        
        Args:
            rating_min: Minimum rating to filter by
        
        Returns:
            List of agent dicts
        """
        try:
            cursor = db.get_cursor()
            
            if rating_min:
                cursor.execute("""
                    SELECT 
                        id, name, email, phone_number, agency_name,
                        specializations, rating, created_at
                    FROM agents
                    WHERE rating >= %s
                    ORDER BY rating DESC
                """, (rating_min,))
            else:
                cursor.execute("""
                    SELECT 
                        id, name, email, phone_number, agency_name,
                        specializations, rating, created_at
                    FROM agents
                    ORDER BY rating DESC
                """)
            
            agents = cursor.fetchall()
            
            # Parse specializations from comma-separated to list
            for agent in agents:
                if agent['specializations']:
                    agent['specializations'] = [s.strip() for s in agent['specializations'].split(',')]
                else:
                    agent['specializations'] = []
            
            return agents if agents else []
        
        except Exception as e:
            logger.error(f"Error getting agents: {str(e)}")
            return []
    
    @staticmethod
    def get_agent_by_id(agent_id):
        """
        Get single agent by ID
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Agent dict or None
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("""
                SELECT 
                    id, name, email, phone_number, agency_name,
                    specializations, rating, created_at
                FROM agents
                WHERE id = %s
            """, (agent_id,))
            
            agent = cursor.fetchone()
            
            if agent and agent['specializations']:
                agent['specializations'] = [s.strip() for s in agent['specializations'].split(',')]
            
            return agent
        
        except Exception as e:
            logger.error(f"Error getting agent: {str(e)}")
            return None
    
    @staticmethod
    def get_agent_by_email(email):
        """
        Get agent by email
        
        Args:
            email: Agent email
        
        Returns:
            Agent dict or None
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("""
                SELECT 
                    id, name, email, phone_number, agency_name,
                    specializations, rating, created_at
                FROM agents
                WHERE email = %s
            """, (email,))
            
            agent = cursor.fetchone()
            
            if agent and agent['specializations']:
                agent['specializations'] = [s.strip() for s in agent['specializations'].split(',')]
            
            return agent
        
        except Exception as e:
            logger.error(f"Error getting agent by email: {str(e)}")
            return None
    
    @staticmethod
    def get_agents_by_specialization(specialization):
        """
        Get all agents with specific specialization
        
        Args:
            specialization: Specialization to filter by
        
        Returns:
            List of agent dicts
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("""
                SELECT 
                    id, name, email, phone_number, agency_name,
                    specializations, rating, created_at
                FROM agents
                WHERE FIND_IN_SET(%s, specializations) > 0
                ORDER BY rating DESC
            """, (specialization,))
            
            agents = cursor.fetchall()
            
            for agent in agents:
                if agent['specializations']:
                    agent['specializations'] = [s.strip() for s in agent['specializations'].split(',')]
            
            return agents if agents else []
        
        except Exception as e:
            logger.error(f"Error getting agents by specialization: {str(e)}")
            return []
    
    @staticmethod
    def update_agent_rating(agent_id, rating):
        """
        Update agent rating
        
        Args:
            agent_id: Agent ID
            rating: New rating (0-5)
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            if rating < 0 or rating > 5:
                return False, "Rating must be between 0 and 5"
            
            cursor.execute("""
                UPDATE agents
                SET rating = %s
                WHERE id = %s
            """, (rating, agent_id))
            
            db.commit()
            
            logger.info(f"Agent {agent_id} rating updated to {rating}")
            return True, "Agent rating updated successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating agent rating: {str(e)}")
            return False, f"Error updating agent rating: {str(e)}"
    
    @staticmethod
    def update_agent_info(agent_id, **kwargs):
        """
        Update agent information
        
        Args:
            agent_id: Agent ID
            kwargs: Fields to update (name, email, phone_number, agency_name, specializations)
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            allowed_fields = ['name', 'email', 'phone_number', 'agency_name', 'specializations']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
            
            if not updates:
                return False, "No valid fields to update"
            
            set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [agent_id]
            
            query = f"UPDATE agents SET {set_clause} WHERE id = %s"
            cursor.execute(query, values)
            
            db.commit()
            
            logger.info(f"Agent {agent_id} information updated")
            return True, "Agent information updated successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating agent info: {str(e)}")
            return False, f"Error updating agent info: {str(e)}"
    
    @staticmethod
    def delete_agent(agent_id):
        """
        Delete an agent
        
        Args:
            agent_id: Agent ID
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("DELETE FROM agents WHERE id = %s", (agent_id,))
            
            db.commit()
            
            logger.info(f"Agent deleted: {agent_id}")
            return True, "Agent deleted successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting agent: {str(e)}")
            return False, f"Error deleting agent: {str(e)}"