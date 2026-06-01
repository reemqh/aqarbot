from app.models.appointment import Appointment
from app.models.property import Property
from app.models.agent import Agent
from app.models.user import User
from app.utils.time_slot_utils import TimeSlotUtils
from app.database import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AppointmentService:
    """Service layer for appointment management"""
    
    @staticmethod
    def get_available_slots(property_id, days_ahead=7):
        """
        Get available appointment slots for a property
        
        Args:
            property_id: Property ID
            days_ahead: Number of days to look ahead (default 7)
        
        Returns:
            {
                'success': bool,
                'property_id': int,
                'available_slots': list of datetime strings,
                'message': str
            }
        """
        try:
            # Verify property exists
            property_data = Property.get_property_by_id(property_id)
            if not property_data:
                return {
                    'success': False,
                    'message': 'Property not found',
                    'available_slots': []
                }
            
            # Get all possible slots for next N business days
            all_slots = TimeSlotUtils.get_all_available_slots(days_ahead)
            
            if not all_slots:
                return {
                    'success': True,
                    'property_id': property_id,
                    'available_slots': [],
                    'message': 'No available slots'
                }
            
            # Get already booked appointments for this property
            booked_appointments = Appointment.get_appointments_by_property(
                property_id, 
                status='pending'
            )
            
            # Extract booked times
            booked_times = set()
            for appt in booked_appointments:
                # Convert appointment_time to 'YYYY-MM-DD HH:MM' format
                appt_time = appt.get('appointment_time')
                if isinstance(appt_time, str):
                    # Already in correct format
                    booked_times.add(appt_time)
                else:
                    # Convert datetime object
                    booked_times.add(appt_time.strftime('%Y-%m-%d %H:%M'))
            
            # Filter out booked slots
            available_slots = [slot for slot in all_slots if slot not in booked_times]
            
            logger.info(f"Found {len(available_slots)} available slots for property {property_id}")
            
            return {
                'success': True,
                'property_id': property_id,
                'property_name': property_data.get('title'),
                'total_possible_slots': len(all_slots),
                'booked_slots': len(booked_times),
                'available_slots': available_slots,
                'message': f'Found {len(available_slots)} available slots'
            }
        
        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'available_slots': []
            }
    
    @staticmethod
    def book_appointment(user_id, property_id, agent_id, appointment_time, notes=''):
        """
        Book an appointment for property viewing
        
        Args:
            user_id: User ID making the appointment
            property_id: Property ID
            agent_id: Agent ID
            appointment_time: Appointment datetime (format: 'YYYY-MM-DD HH:MM')
            notes: Optional notes
        
        Returns:
            {
                'success': bool,
                'appointment_id': int or None,
                'property_name': str,
                'agent_name': str,
                'appointment_time': str,
                'message': str
            }
        """
        try:
            # Validate appointment time format and business hours/days
            is_valid, validation_msg = TimeSlotUtils.validate_appointment_time(appointment_time)
            if not is_valid:
                return {
                    'success': False,
                    'appointment_id': None,
                    'message': validation_msg
                }
            
            # Verify property exists
            property_data = Property.get_property_by_id(property_id)
            if not property_data:
                return {
                    'success': False,
                    'appointment_id': None,
                    'message': 'Property not found'
                }
            
            # Verify agent exists
            agent_data = Agent.get_agent_by_id(agent_id)
            if not agent_data:
                return {
                    'success': False,
                    'appointment_id': None,
                    'message': 'Agent not found'
                }
            
            # Verify user exists
            user_data = User.get_user_by_id(user_id)
            if not user_data:
                return {
                    'success': False,
                    'appointment_id': None,
                    'message': 'User not found'
                }
            
            # Check if this slot is already booked
            booked_appointments = Appointment.get_appointments_by_property(
                property_id,
                status='pending'
            )
            
            for appt in booked_appointments:
                appt_time = appt.get('appointment_time')
                if isinstance(appt_time, str):
                    booked_time_str = appt_time
                else:
                    booked_time_str = appt_time.strftime('%Y-%m-%d %H:%M')
                
                if booked_time_str == appointment_time:
                    return {
                        'success': False,
                        'appointment_id': None,
                        'message': f'This time slot is already booked. Please choose another time.'
                    }
            
            # Create appointment
            appointment_id, create_msg = Appointment.create_appointment(
                user_id=user_id,
                property_id=property_id,
                agent_id=agent_id,
                appointment_time=appointment_time,
                notes=notes
            )
            
            if not appointment_id:
                return {
                    'success': False,
                    'appointment_id': None,
                    'message': create_msg
                }
            
            logger.info(f"Appointment {appointment_id} booked successfully")
            
            return {
                'success': True,
                'appointment_id': appointment_id,
                'property_id': property_id,
                'property_name': property_data.get('title'),
                'agent_id': agent_id,
                'agent_name': agent_data.get('name'),
                'agent_phone': agent_data.get('phone_number'),
                'agent_email': agent_data.get('email'),
                'appointment_time': appointment_time,
                'status': 'pending',
                'message': 'Appointment booked successfully'
            }
        
        except Exception as e:
            logger.error(f"Error booking appointment: {str(e)}")
            return {
                'success': False,
                'appointment_id': None,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def get_user_appointments(user_id, status=None):
        """
        Get all appointments for a user
        
        Args:
            user_id: User ID
            status: Optional status filter (pending, completed, cancelled)
        
        Returns:
            {
                'success': bool,
                'count': int,
                'appointments': list of appointment dicts,
                'message': str
            }
        """
        try:
            appointments = Appointment.get_appointments_by_user(user_id)
            
            # Filter by status if provided
            if status:
                appointments = [a for a in appointments if a.get('status') == status]
            
            return {
                'success': True,
                'count': len(appointments),
                'appointments': appointments,
                'message': f'Retrieved {len(appointments)} appointments'
            }
        
        except Exception as e:
            logger.error(f"Error getting user appointments: {str(e)}")
            return {
                'success': False,
                'count': 0,
                'appointments': [],
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def get_appointment_details(appointment_id, user_id=None):
        """
        Get single appointment details
        
        Args:
            appointment_id: Appointment ID
            user_id: Optional user ID to verify ownership
        
        Returns:
            {
                'success': bool,
                'appointment': dict or None,
                'message': str
            }
        """
        try:
            appointment = Appointment.get_appointment_by_id(appointment_id)
            
            if not appointment:
                return {
                    'success': False,
                    'appointment': None,
                    'message': 'Appointment not found'
                }
            
            # Verify ownership if user_id provided
            if user_id and appointment.get('user_id') != user_id:
                return {
                    'success': False,
                    'appointment': None,
                    'message': 'Unauthorized'
                }
            
            return {
                'success': True,
                'appointment': appointment,
                'message': 'Appointment retrieved successfully'
            }
        
        except Exception as e:
            logger.error(f"Error getting appointment details: {str(e)}")
            return {
                'success': False,
                'appointment': None,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def cancel_appointment(appointment_id, user_id=None):
        """
        Cancel an appointment
        
        Args:
            appointment_id: Appointment ID
            user_id: Optional user ID to verify ownership
        
        Returns:
            {
                'success': bool,
                'appointment_id': int,
                'message': str
            }
        """
        try:
            # Verify ownership if user_id provided
            if user_id:
                appointment = Appointment.get_appointment_by_id(appointment_id)
                if not appointment or appointment.get('user_id') != user_id:
                    return {
                        'success': False,
                        'appointment_id': appointment_id,
                        'message': 'Unauthorized'
                    }
            
            success, msg = Appointment.cancel_appointment(appointment_id)
            
            return {
                'success': success,
                'appointment_id': appointment_id,
                'message': msg
            }
        
        except Exception as e:
            logger.error(f"Error cancelling appointment: {str(e)}")
            return {
                'success': False,
                'appointment_id': appointment_id,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def mark_completed(appointment_id, user_id=None):
        """
        Mark appointment as completed
        
        Args:
            appointment_id: Appointment ID
            user_id: Optional user ID to verify ownership
        
        Returns:
            {
                'success': bool,
                'appointment_id': int,
                'message': str
            }
        """
        try:
            # Verify ownership if user_id provided
            if user_id:
                appointment = Appointment.get_appointment_by_id(appointment_id)
                if not appointment or appointment.get('user_id') != user_id:
                    return {
                        'success': False,
                        'appointment_id': appointment_id,
                        'message': 'Unauthorized'
                    }
            
            success, msg = Appointment.mark_completed(appointment_id)
            
            return {
                'success': success,
                'appointment_id': appointment_id,
                'message': msg
            }
        
        except Exception as e:
            logger.error(f"Error marking appointment completed: {str(e)}")
            return {
                'success': False,
                'appointment_id': appointment_id,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def get_agent_appointments(agent_id, status=None):
        """
        Get all appointments for an agent
        
        Args:
            agent_id: Agent ID
            status: Optional status filter
        
        Returns:
            {
                'success': bool,
                'count': int,
                'appointments': list,
                'message': str
            }
        """
        try:
            appointments = Appointment.get_appointments_by_agent(agent_id, status)
            
            return {
                'success': True,
                'count': len(appointments),
                'appointments': appointments,
                'message': f'Retrieved {len(appointments)} appointments for agent'
            }
        
        except Exception as e:
            logger.error(f"Error getting agent appointments: {str(e)}")
            return {
                'success': False,
                'count': 0,
                'appointments': [],
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def get_property_appointments(property_id, status=None):
        """
        Get all appointments for a property
        
        Args:
            property_id: Property ID
            status: Optional status filter
        
        Returns:
            {
                'success': bool,
                'count': int,
                'appointments': list,
                'message': str
            }
        """
        try:
            appointments = Appointment.get_appointments_by_property(property_id, status)
            
            return {
                'success': True,
                'count': len(appointments),
                'appointments': appointments,
                'message': f'Retrieved {len(appointments)} appointments for property'
            }
        
        except Exception as e:
            logger.error(f"Error getting property appointments: {str(e)}")
            return {
                'success': False,
                'count': 0,
                'appointments': [],
                'message': f'Error: {str(e)}'
            }