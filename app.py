from flask import Flask
from routes.event_routes import event_bp  # Import your blueprint

app = Flask(__name__)

# Register the blueprint
app.register_blueprint(event_bp)

@app.route('/')
def home():
    return "Welcome to the homepage!"

if __name__ == '__main__':
    app.run(debug=True)
