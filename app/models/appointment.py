from app.database import db
import datetime
import logging
import json

logger = logging.getLogger(__name__)

class Appointment:
    """Appointment model - Manage property viewing appointments with agents"""
    
    @staticmethod
    def create_appointment(user_id, property_id, agent_id, appointment_time, notes=''):
        """
        Create a new appointment for property viewing
        
        Args:
            user_id: User ID making the appointment
            property_id: Property ID to view
            agent_id: Agent ID to meet with
            appointment_time: Appointment datetime (format: 'YYYY-MM-DD HH:MM' or datetime object)
            notes: Optional notes about the appointment
        
        Returns:
            (appointment_id, message)
        """
        try:
            cursor = db.get_cursor()
            
            # Ensure appointment_time is in correct format
            if isinstance(appointment_time, str):
                # Validate format: YYYY-MM-DD HH:MM
                try:
                    appointment_dt = datetime.datetime.strptime(appointment_time, '%Y-%m-%d %H:%M')
                    appointment_time = appointment_dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return None, f"Invalid datetime format. Use 'YYYY-MM-DD HH:MM'"
            
            # Insert appointment
            cursor.execute("""
                INSERT INTO appointments 
                (user_id, property_id, agent_id, appointment_time, notes, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, property_id, agent_id, appointment_time, notes, 'pending', datetime.datetime.now()))
            
            db.commit()
            
            # Get the newly created appointment ID
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            appointment_id = result['id'] if result else None
            
            logger.info(f"Appointment created: {appointment_id} for user {user_id}")
            return appointment_id, "Appointment created successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating appointment: {str(e)}")
            return None, f"Error creating appointment: {str(e)}"
    
    @staticmethod
    def get_appointments_by_user(user_id):
        """
        Get all appointments for a user
        
        Args:
            user_id: User ID
        
        Returns:
            List of appointment dicts with property and agent details
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT 
                    a.id,
                    a.user_id,
                    a.property_id,
                    a.agent_id,
                    a.appointment_time,
                    a.notes,
                    a.status,
                    a.created_at,
                    a.updated_at,
                    p.title as property_title,
                    p.location as property_location,
                    p.price as property_price,
                    p.image_url as property_image,
                    ag.name as agent_name,
                    ag.phone_number as agent_phone,
                    ag.email as agent_email
                FROM appointments a
                LEFT JOIN properties p ON a.property_id = p.id
                LEFT JOIN agents ag ON a.agent_id = ag.id
                WHERE a.user_id = %s
                ORDER BY a.appointment_time DESC
            """, (user_id,))
            
            appointments = cursor.fetchall()
            return appointments if appointments else []
        
        except Exception as e:
            logger.error(f"Error getting appointments: {str(e)}")
            return []
    
    @staticmethod
    def get_appointment_by_id(appointment_id):
        """
        Get single appointment by ID with full details
        
        Args:
            appointment_id: Appointment ID
        
        Returns:
            Appointment dict with property and agent details, or None
        """
        try:
            cursor = db.get_cursor()
            cursor.execute("""
                SELECT 
                    a.id,
                    a.user_id,
                    a.property_id,
                    a.agent_id,
                    a.appointment_time,
                    a.notes,
                    a.status,
                    a.created_at,
                    a.updated_at,
                    p.title as property_title,
                    p.location as property_location,
                    p.price as property_price,
                    p.image_url as property_image,
                    p.num_bedrooms,
                    p.num_bathrooms,
                    ag.name as agent_name,
                    ag.phone_number as agent_phone,
                    ag.email as agent_email,
                    ag.agency_name
                FROM appointments a
                LEFT JOIN properties p ON a.property_id = p.id
                LEFT JOIN agents ag ON a.agent_id = ag.id
                WHERE a.id = %s
            """, (appointment_id,))
            
            appointment = cursor.fetchone()
            return appointment
        
        except Exception as e:
            logger.error(f"Error getting appointment: {str(e)}")
            return None
    
    @staticmethod
    def get_appointments_by_property(property_id, status=None):
        """
        Get all appointments for a specific property
        
        Args:
            property_id: Property ID
            status: Optional status filter (pending, completed, cancelled)
        
        Returns:
            List of appointments for that property
        """
        try:
            cursor = db.get_cursor()
            
            if status:
                cursor.execute("""
                    SELECT 
                        id, user_id, property_id, agent_id, appointment_time,
                        notes, status, created_at, updated_at
                    FROM appointments
                    WHERE property_id = %s AND status = %s
                    ORDER BY appointment_time DESC
                """, (property_id, status))
            else:
                cursor.execute("""
                    SELECT 
                        id, user_id, property_id, agent_id, appointment_time,
                        notes, status, created_at, updated_at
                    FROM appointments
                    WHERE property_id = %s
                    ORDER BY appointment_time DESC
                """, (property_id,))
            
            appointments = cursor.fetchall()
            return appointments if appointments else []
        
        except Exception as e:
            logger.error(f"Error getting appointments by property: {str(e)}")
            return []
    
    @staticmethod
    def get_appointments_by_agent(agent_id, status=None):
        """
        Get all appointments for a specific agent
        
        Args:
            agent_id: Agent ID
            status: Optional status filter
        
        Returns:
            List of appointments for that agent
        """
        try:
            cursor = db.get_cursor()
            
            if status:
                cursor.execute("""
                    SELECT 
                        id, user_id, property_id, agent_id, appointment_time,
                        notes, status, created_at, updated_at
                    FROM appointments
                    WHERE agent_id = %s AND status = %s
                    ORDER BY appointment_time DESC
                """, (agent_id, status))
            else:
                cursor.execute("""
                    SELECT 
                        id, user_id, property_id, agent_id, appointment_time,
                        notes, status, created_at, updated_at
                    FROM appointments
                    WHERE agent_id = %s
                    ORDER BY appointment_time DESC
                """, (agent_id,))
            
            appointments = cursor.fetchall()
            return appointments if appointments else []
        
        except Exception as e:
            logger.error(f"Error getting appointments by agent: {str(e)}")
            return []
    
    @staticmethod
    def update_appointment_status(appointment_id, status):
        """
        Update appointment status
        
        Args:
            appointment_id: Appointment ID
            status: New status (pending, completed, cancelled)
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            valid_statuses = ['pending', 'completed', 'cancelled']
            if status not in valid_statuses:
                return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            
            cursor.execute("""
                UPDATE appointments
                SET status = %s, updated_at = NOW()
                WHERE id = %s
            """, (status, appointment_id))
            
            db.commit()
            
            logger.info(f"Appointment {appointment_id} status updated to {status}")
            return True, f"Appointment status updated to {status}"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating appointment status: {str(e)}")
            return False, f"Error updating appointment: {str(e)}"
    
    @staticmethod
    def cancel_appointment(appointment_id):
        """
        Cancel an appointment (mark as cancelled)
        
        Args:
            appointment_id: Appointment ID
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            # Check if appointment exists
            cursor.execute("SELECT id FROM appointments WHERE id = %s", (appointment_id,))
            if not cursor.fetchone():
                return False, "Appointment not found"
            
            cursor.execute("""
                UPDATE appointments
                SET status = 'cancelled', updated_at = NOW()
                WHERE id = %s
            """, (appointment_id,))
            
            db.commit()
            
            logger.info(f"Appointment {appointment_id} cancelled")
            return True, "Appointment cancelled successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling appointment: {str(e)}")
            return False, f"Error cancelling appointment: {str(e)}"
    
    @staticmethod
    def mark_completed(appointment_id):
        """
        Mark appointment as completed
        
        Args:
            appointment_id: Appointment ID
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            # Check if appointment exists
            cursor.execute("SELECT id FROM appointments WHERE id = %s", (appointment_id,))
            if not cursor.fetchone():
                return False, "Appointment not found"
            
            cursor.execute("""
                UPDATE appointments
                SET status = 'completed', updated_at = NOW()
                WHERE id = %s
            """, (appointment_id,))
            
            db.commit()
            
            logger.info(f"Appointment {appointment_id} marked as completed")
            return True, "Appointment marked as completed"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking appointment completed: {str(e)}")
            return False, f"Error marking appointment completed: {str(e)}"
    
    @staticmethod
    def update_appointment_notes(appointment_id, notes):
        """
        Update appointment notes
        
        Args:
            appointment_id: Appointment ID
            notes: New notes
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("""
                UPDATE appointments
                SET notes = %s, updated_at = NOW()
                WHERE id = %s
            """, (notes, appointment_id))
            
            db.commit()
            
            logger.info(f"Appointment {appointment_id} notes updated")
            return True, "Notes updated successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating notes: {str(e)}")
            return False, f"Error updating notes: {str(e)}"
    
    @staticmethod
    def delete_appointment(appointment_id):
        """
        Delete an appointment (hard delete)
        
        Args:
            appointment_id: Appointment ID
        
        Returns:
            (success, message)
        """
        try:
            cursor = db.get_cursor()
            
            cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
            
            db.commit()
            
            logger.info(f"Appointment {appointment_id} deleted")
            return True, "Appointment deleted successfully"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting appointment: {str(e)}")
            return False, f"Error deleting appointment: {str(e)}"