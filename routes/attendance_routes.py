from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user, login_user
from models.event import Event, EventAttendance
from models.club import Club, ClubMembership
from models.user import User  # adjust this import as needed
from extensions import db
from datetime import datetime
import qrcode
import io

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/event/<int:event_id>/take-attendance')
@login_required
def take_attendance(event_id):
    event = Event.query.get_or_404(event_id)

    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=event.club_id,
        is_host=True
    ).first_or_404()

    members = ClubMembership.query.filter_by(club_id=event.club_id).all()
    attendances = {a.user_id: a for a in event.attendances}

    return render_template('take_attendance.html',
        event=event,
        members=members,
        attendances=attendances
    )

@attendance_bp.route('/event/<int:event_id>/submit-attendance', methods=['POST'])
@login_required
def submit_attendance(event_id):
    event = Event.query.get_or_404(event_id)

    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=event.club_id,
        is_host=True
    ).first_or_404()

    for member_id, attended in request.form.items():
        if member_id.isdigit():
            attendance = EventAttendance.query.filter_by(
                event_id=event_id,
                user_id=int(member_id)
            ).first()

            if not attendance:
                attendance = EventAttendance(
                    event_id=event_id,
                    user_id=int(member_id),
                    attended=(attended == 'on')
                )
                db.session.add(attendance)
            else:
                attendance.attended = (attended == 'on')

    event.attendance_started = True
    db.session.commit()

    return redirect(url_for('event.events_page', club_id=event.club_id))

@attendance_bp.route('/event/<int:event_id>/attend', methods=['POST'])
@login_required
def mark_attendance(event_id):
    event = Event.query.get_or_404(event_id)

    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=event.club_id
    ).first_or_404()

    attendance = EventAttendance.query.filter_by(
        event_id=event_id,
        user_id=current_user.id
    ).first()

    if attendance:
        attendance.attended = not attendance.attended
    else:
        attendance = EventAttendance(
            event_id=event_id,
            user_id=current_user.id,
            attended=True
        )
        db.session.add(attendance)

    db.session.commit()
    return redirect(url_for('event.events_page', club_id=event.club_id))

# --- QR Routes ---

@attendance_bp.route('/event/<int:event_id>/qr')
@login_required
def display_qr(event_id):
    event = Event.query.get_or_404(event_id)

    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=event.club_id,
        is_host=True
    ).first_or_404()

    qr_url = url_for('attendance.attend_via_qr', event_id=event.id, _external=True)

    return render_template('qr_display.html', event=event, qr_data=qr_url)

@attendance_bp.route('/event/<int:event_id>/qr_image')
@login_required
def qr_image(event_id):
    qr_url = url_for('attendance.attend_via_qr', event_id=event_id, _external=True)
    qr = qrcode.make(qr_url)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@attendance_bp.route('/event/<int:event_id>/attend-via-qr', methods=['GET', 'POST'])
def attend_via_qr(event_id):
    event = Event.query.get_or_404(event_id)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)

            attendance = EventAttendance.query.filter_by(
                event_id=event.id,
                user_id=user.id
            ).first()

            if not attendance:
                attendance = EventAttendance(
                    event_id=event.id,
                    user_id=user.id,
                    attended=True
                )
                db.session.add(attendance)
            else:
                attendance.attended = True

            db.session.commit()

            flash('Your attendance has been recorded!', 'success')
            return redirect(url_for('event.events_page', club_id=event.club_id))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('attend_via_qr.html', event=event)
