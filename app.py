from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize Flask app
app = Flask(__name__)

# Load config (DB URI, secret keys, etc.)
app.config.from_object('config.Config')

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models so Flask-Migrate can see them
from models import user, event

# Import and register blueprints
from routes.user_routes import user_bp
from routes.event_routes import event_bp

# Register blueprints (url_prefix is optional but cleaner)
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(event_bp, url_prefix='/event')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)