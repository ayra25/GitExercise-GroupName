from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from extensions import db  # Importing db from extensions.py

# Initialize extensions
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Configurations (normally you'd import from config.py)
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mmunity.db'  # Or your database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)  # Initialize SQLAlchemy with the app
    migrate.init_app(app, db)  # Initialize Migrate with the app and db
    login_manager.init_app(app)  # Initialize LoginManager with the app

    login_manager.login_view = 'user.login'  # Redirect unauthorized users to login

    # User loader function to tell Flask-Login how to load a user from the session
    from models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Assuming your user model has an 'id' field

    # Register blueprints
    from routes.user_routes import user_bp
    from routes.event_routes import event_bp
    from routes.club_routes import club_bp
    from routes.attendance_routes import attendance_bp
    app.register_blueprint(user_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(club_bp)
    app.register_blueprint(attendance_bp)


    # You can register more blueprints here, e.g., event_bp, attendance_bp later

    return app

# For running the app
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)