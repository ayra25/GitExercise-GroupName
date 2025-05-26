from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models.event import Event, EventAttendance
from models.club import Club, ClubMembership
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

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    qr_text = f"Event ID: {event.id} | {now}"

    return render_template('qr_display.html', event=event, qr_data=qr_text)

@attendance_bp.route('/event/<int:event_id>/qr_image')
@login_required
def qr_image(event_id):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    qr_text = f"Event ID: {event_id} | {now}"
    qr = qrcode.make(qr_text)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')
