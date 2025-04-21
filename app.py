from flask import Flask
from routes.event_routes import event_bp 
from routes.user_routes import user_bp

app = Flask(__name__)
app.register_blueprint(user_bp)
app.register_blueprint(event_bp)

@app.route('/')
def home():
    return "Welcome to the homepage!"

if __name__ == '__main__':
    app.run(debug=True)
