from flask import Flask, render_template
from routes.user_routes import user_bp

app = Flask(__name__)
app.register_blueprint(user_bp)

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True) #test