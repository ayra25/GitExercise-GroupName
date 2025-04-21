# app.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Set DB name
DB_NAME = 'mmunity.db'

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Manually setting config
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models
    from models import user, event

    # Import and register blueprints
    from routes.user_routes import user_bp
    from routes.event_routes import event_bp

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(event_bp, url_prefix='/event')

    return app

# Only run the server if directly executing app.py
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)