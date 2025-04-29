# routes/attendance_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.event import Event, EventAttendance
from models.club import Club, ClubMembership
from extensions import db
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/event/<int:event_id>/take-attendance')
@login_required
def take_attendance(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Verify user is host of this club
    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=event.club_id,
        is_host=True
    ).first_or_404()
    
    # Get all club members
    members = ClubMembership.query.filter_by(club_id=event.club_id).all()
    
    # Get existing attendance records
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
    
    # Verify user is host
    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=event.club_id,
        is_host=True
    ).first_or_404()
    
    # Process attendance form
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
    
    flash('Attendance saved successfully!', 'success')
    return redirect(url_for('event.events_page', club_id=event.club_id))