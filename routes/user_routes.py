from flask import Blueprint, render_template, request
from models.user import User
from app import db

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

    new_user = User(name=name, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    return f"Welcome {name}, you’ve successfully signed up with {email}!"


@user_bp.route('/login-user', methods=['POST'])
def handle_login():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()
    
    if email == 'email' and password == '1234':
        return f"Welcome back {name}, Login successful!"
    else:
        return "Invalid Login credentials!"
