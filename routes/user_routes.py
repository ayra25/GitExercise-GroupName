from flask import Blueprint, render_template, request, flash, redirect, url_for
from models.user import User
from extensions import db
from flask_login import login_user, login_required, logout_user, current_user
import bcrypt  
from utils.token import generate_reset_token, verify_reset_token
from utils.email import send_reset_email


user_bp = Blueprint('user', __name__)

@user_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('club.dashboard'))  
    return render_template('landing.html')
 

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('club.dashboard'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.login'))


@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:

            hashed_password = bcrypt.hashpw(password1.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            new_user = User(email=email, first_name=first_name, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('club.dashboard'))

    return render_template("signup.html", user=current_user)

@user_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('user.reset_password_token', token=token, _external=True)
            send_reset_email(user.email, reset_url)  
            flash('A password reset link has been sent to your email.', 'info')
        else:
            flash('No account found with that email.', 'danger')
    return render_template('forgot_password.html')

@user_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    email = verify_reset_token(token)
    if not email:
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('user.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('user.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        if not new_password or len(new_password) < 7:
            flash('Password must be at least 7 characters.', 'error')
        else:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            flash('Password has been reset. You can now log in.', 'success')
            return redirect(url_for('user.login'))

    return render_template('reset_password.html')  

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.email = request.form.get('email')

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if current_password and new_password:
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('user.profile'))

            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('user.profile'))

            if len(new_password) < 7:
                flash('New password must be at least 7 characters.', 'danger')
                return redirect(url_for('user.profile'))

            current_user.set_password(new_password)

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.index'))

    return render_template('profile.html', user=current_user)
