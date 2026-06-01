from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TimeSlotUtils:
    """Utility functions for generating and managing appointment time slots"""
    
    # Business hours configuration
    START_HOUR = 9      # 9 AM
    END_HOUR = 17       # 5 PM
    SLOT_DURATION = 30  # 30 minutes
    
    @staticmethod
    def get_business_days(days_ahead=7):
        """
        Get list of business days (Sat-Thu, no Friday)
        
        Args:
            days_ahead: Number of days to generate (default 7)
        
        Returns:
            List of date objects for business days
        """
        try:
            business_days = []
            current_date = datetime.now().date()
            
            while len(business_days) < days_ahead:
                # Check if current_date is not Friday (Friday = 4)
                if current_date.weekday() != 4:  # 0=Monday, 4=Friday
                    business_days.append(current_date)
                
                current_date += timedelta(days=1)
            
            logger.info(f"Generated {len(business_days)} business days")
            return business_days
        
        except Exception as e:
            logger.error(f"Error getting business days: {str(e)}")
            return []
    
    @staticmethod
    def generate_time_slots(date_obj):
        """
        Generate 30-minute time slots for a specific date (9 AM - 5 PM)
        
        Args:
            date_obj: Date object or string (format: 'YYYY-MM-DD')
        
        Returns:
            List of time strings (format: 'HH:MM')
            Example: ['09:00', '09:30', '10:00', ..., '16:30']
        """
        try:
            slots = []
            current_hour = TimeSlotUtils.START_HOUR
            current_minute = 0
            
            while current_hour < TimeSlotUtils.END_HOUR:
                time_str = f"{current_hour:02d}:{current_minute:02d}"
                slots.append(time_str)
                
                # Add 30 minutes for next slot
                current_minute += TimeSlotUtils.SLOT_DURATION
                if current_minute >= 60:
                    current_minute = 0
                    current_hour += 1
            
            logger.info(f"Generated {len(slots)} time slots for {date_obj}")
            return slots
        
        except Exception as e:
            logger.error(f"Error generating time slots: {str(e)}")
            return []
    
    @staticmethod
    def is_friday(date_obj):
        """
        Check if given date is Friday
        
        Args:
            date_obj: Date object or string (format: 'YYYY-MM-DD')
        
        Returns:
            True if Friday, False otherwise
        """
        try:
            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
            
            # Friday = 4 (0=Monday, 6=Sunday)
            return date_obj.weekday() == 4
        
        except Exception as e:
            logger.error(f"Error checking if Friday: {str(e)}")
            return False
    
    @staticmethod
    def is_business_day(date_obj):
        """
        Check if date is a business day (not Friday)
        
        Args:
            date_obj: Date object or string (format: 'YYYY-MM-DD')
        
        Returns:
            True if business day, False if Friday or invalid
        """
        try:
            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
            
            # False if Friday, True otherwise
            return date_obj.weekday() != 4
        
        except Exception as e:
            logger.error(f"Error checking business day: {str(e)}")
            return False
    
    @staticmethod
    def is_business_hours(time_str):
        """
        Check if time is within business hours (9 AM - 5 PM)
        
        Args:
            time_str: Time string (format: 'HH:MM')
        
        Returns:
            True if within business hours, False otherwise
        """
        try:
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            start_time = datetime.strptime(f"{TimeSlotUtils.START_HOUR:02d}:00", '%H:%M').time()
            end_time = datetime.strptime(f"{TimeSlotUtils.END_HOUR:02d}:00", '%H:%M').time()
            
            return start_time <= time_obj < end_time
        
        except Exception as e:
            logger.error(f"Error checking business hours: {str(e)}")
            return False
    
    @staticmethod
    def validate_time_slot(time_str):
        """
        Validate time slot format (HH:MM)
        
        Args:
            time_str: Time string (format: 'HH:MM')
        
        Returns:
            True if valid format, False otherwise
        """
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_appointment_time(appointment_time_str):
        """
        Validate complete appointment datetime
        
        Args:
            appointment_time_str: Datetime string (format: 'YYYY-MM-DD HH:MM')
        
        Returns:
            (is_valid, message)
        """
        try:
            # Parse datetime
            appointment_dt = datetime.strptime(appointment_time_str, '%Y-%m-%d %H:%M')
            appointment_date = appointment_dt.date()
            appointment_time = appointment_dt.time()
            
            # Check if date is in the past
            if appointment_date < datetime.now().date():
                return False, "Cannot book appointment for past dates"
            
            # Check if it's a business day (not Friday)
            if not TimeSlotUtils.is_business_day(appointment_date):
                return False, "Appointments only available Saturday to Thursday (no Friday)"
            
            # Check if time is within business hours
            time_str = appointment_time.strftime('%H:%M')
            if not TimeSlotUtils.is_business_hours(time_str):
                return False, f"Appointments only available {TimeSlotUtils.START_HOUR:02d}:00 - {TimeSlotUtils.END_HOUR:02d}:00"
            
            return True, "Valid appointment time"
        
        except ValueError:
            return False, "Invalid datetime format. Use 'YYYY-MM-DD HH:MM'"
        except Exception as e:
            logger.error(f"Error validating appointment time: {str(e)}")
            return False, f"Error validating time: {str(e)}"
    
    @staticmethod
    def get_available_slots_for_date(date_obj):
        """
        Get all available time slots for a specific date
        
        Args:
            date_obj: Date object or string (format: 'YYYY-MM-DD')
        
        Returns:
            List of full datetime strings (format: 'YYYY-MM-DD HH:MM')
            Example: ['2026-02-25 09:00', '2026-02-25 09:30', ...]
        """
        try:
            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
            
            # Check if it's a business day
            if not TimeSlotUtils.is_business_day(date_obj):
                logger.warning(f"Requested date {date_obj} is not a business day")
                return []
            
            # Generate time slots for this date
            time_slots = TimeSlotUtils.generate_time_slots(date_obj)
            
            # Convert to full datetime strings
            date_str = date_obj.strftime('%Y-%m-%d')
            full_slots = [f"{date_str} {time}" for time in time_slots]
            
            return full_slots
        
        except Exception as e:
            logger.error(f"Error getting available slots: {str(e)}")
            return []
    
    @staticmethod
    def get_all_available_slots(days_ahead=7):
        """
        Get all available slots for next N business days
        
        Args:
            days_ahead: Number of days to generate (default 7)
        
        Returns:
            List of full datetime strings
            Example: ['2026-02-25 09:00', '2026-02-25 09:30', ..., '2026-02-26 09:00', ...]
        """
        try:
            all_slots = []
            business_days = TimeSlotUtils.get_business_days(days_ahead)
            
            for date_obj in business_days:
                slots_for_date = TimeSlotUtils.get_available_slots_for_date(date_obj)
                all_slots.extend(slots_for_date)
            
            logger.info(f"Generated total {len(all_slots)} available slots")
            return all_slots
        
        except Exception as e:
            logger.error(f"Error getting all slots: {str(e)}")
            return []