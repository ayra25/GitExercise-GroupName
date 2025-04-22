# app.py

from flask import Flask
from extensions import db, migrate  # <<< import here

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mmunity.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    from models import user, event
    from routes.user_routes import user_bp
    from routes.event_routes import event_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(event_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
