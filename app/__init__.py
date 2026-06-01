from flask import Flask, app, render_template, request, jsonify, redirect, url_for, make_response
from flask_cors import CORS
import logging
from app.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """
    Application factory pattern for Flask app
    
    Returns:
        Flask application instance
    """
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS for web frontend
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    
    # Register blueprints (routes)
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.property_api_routes import property_bp
    from app.routes.appointment import appointment_bp
    from app.routes.admin import admin_bp
    
    
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(property_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(admin_bp)
    
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {
            'status': 'healthy',
            'message': 'AqarBot API is running'
        }, 200
    
    @app.route('/set-lang/<lang>')
    def set_language(lang):
        if lang not in ['ar', 'en']:
            lang = 'ar'  # fallback to Arabic

    # Redirect back to the page user came from (or to register if no referrer)
        response = make_response(redirect(request.referrer or url_for('register_page')))

    # Set cookie for 1 year
        response.set_cookie('lang', lang, max_age=31536000, httponly=True, samesite='Lax')

        return response

    # Root endpoint
    @app.route('/')
    def index():
        return redirect(url_for('register_page'))
    
    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')
    
    @app.route('/forgot-password')
    def forgot_password_page():
        return render_template('forgot_password.html')

    @app.route('/reset-password')
    def reset_password_page():
        return render_template('reset_password.html')
    
    @app.route('/profile')
    def profile_page():
        return render_template('profile_api_based.html', lang=request.cookies.get('lang', 'ar'))
    
    @app.route('/chat')
    def chat_page():
        return render_template('chat.html')
    
    @app.route('/property')
    def property_page():
        return render_template('property.html')
    
    @app.route('/appointment/book')
    def appointment_booking_page():
        return render_template('appointment_booking.html')

    @app.route('/appointments')
    def appointments_page():
        return render_template('appointment_list.html')

    @app.route('/appointment/<int:appointment_id>')
    def appointment_detail_page(appointment_id):
        return render_template('appointment_detail.html')
    
    @app.route('/history')
    def history_page():
        return render_template('history.html')

    @app.route('/admin')
    def admin_dashboard_page():
        return render_template('admin_dashboard.html')
    


    logger.info("Flask app created successfully")
    
    return app