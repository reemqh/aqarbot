import mysql.connector
from mysql.connector import Error
from app.config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    """Database connection handler"""
    
    _connection = None
    _cursor = None
    
    @classmethod
    def get_connection(cls):
        """Get database connection"""
        if cls._connection is None:
            try:
                cls._connection = mysql.connector.connect(
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    port=Config.DB_PORT,
                    autocommit=False
                )
                logger.info("Database connected successfully")
            except Error as e:
                logger.error(f"Error while connecting to MySQL: {e}")
                raise
        return cls._connection
    
    @classmethod
    def get_cursor(cls):
        """Get database cursor"""
        connection = cls.get_connection()
        if cls._cursor is None:
            cls._cursor = connection.cursor(dictionary=True)
        return cls._cursor
    
    @classmethod
    def commit(cls):
        """Commit transaction"""
        if cls._connection:
            cls._connection.commit()
    
    @classmethod
    def rollback(cls):
        """Rollback transaction"""
        if cls._connection:
            cls._connection.rollback()
    
    @classmethod
    def close(cls):
        """Close database connection"""
        if cls._cursor:
            cls._cursor.close()
        if cls._connection:
            cls._connection.close()
        cls._connection = None
        cls._cursor = None

# Create a singleton instance
db = Database()