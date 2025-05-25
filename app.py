from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from extensions import db


migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mmunity.db'  
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    
    db.init_app(app)  
    migrate.init_app(app, db)  
    login_manager.init_app(app)  

    login_manager.login_view = 'user.login'  

    
    from models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  

    
    from routes.user_routes import user_bp
    from routes.event_routes import event_bp
    from routes.club_routes import club_bp
    from routes.attendance_routes import attendance_bp
    from routes.notification_routes import notification_bp
    from models.filters import time_ago
    app.register_blueprint(user_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(club_bp, url_prefix='/club')
    app.register_blueprint(attendance_bp)
    app.register_blueprint(notification_bp)
    app.jinja_env.filters['time_ago'] = time_ago

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)