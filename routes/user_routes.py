from flask import Blueprint, render_template, request

user_bp = Blueprint('user',__name__)

@user_bp.route('/signup')
def signup():
    return render_template('signup.html')

@user_bp.route('/login')
def login():
    return render_template('login.html')

@user_bp.route('/signup-user', methods=['POST'])
def handle_signup():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    return f"Welcome {name}, you’ve successfully signed up with {email}!"

@user_bp.route('/login-user', methods=['POST'])
def handle_login():
    name = request.form['name']
    username = request.form['username']
    password = request.form['password']
    if username == 'user' and password == '1234':
        return f"Welcome back {name}, Login successful!"
    else:
        return "Invalid Login credentials!"
