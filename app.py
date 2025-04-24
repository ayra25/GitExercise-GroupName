# app.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

DB_NAME = 'mmunity.db'

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    from models import user, event

    from routes.user_routes import user_bp
    from routes.event_routes import event_bp

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(event_bp, url_prefix='/event')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)