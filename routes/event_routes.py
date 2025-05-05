from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, current_user
from models.event import Event, EventAttendance
from models.club import Club, ClubMembership
from models.form import EventForm
from models.announcement import Announcement
from extensions import db
from datetime import datetime

event_bp = Blueprint('event', __name__)

@event_bp.route('/event/<int:club_id>')
@login_required
def events_page(club_id):
    club = Club.query.options(
        db.joinedload(Club.club_events)
    ).get_or_404(club_id)
    
    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=club_id
    ).first()
    
    if not membership:
        abort(403)
    
    events = Event.query.filter_by(club_id=club_id).order_by(Event.date.desc()).all()
    announcements = Announcement.query.filter_by(
        club_id=club_id
    ).order_by(Announcement.created_at.desc()).all()
    
    selected_id = request.args.get('selected')
    selected_event = next(
        (e for e in events if str(e.id) == selected_id),
        events[0] if events else None
    )

    return render_template('event.html',
        club=club,
        events=events,
        announcements=announcements,
        selected_event=selected_event,
        is_host=membership.is_host,
        now=datetime.utcnow(),
        membership=membership,  # Pass membership to the template
    )

@event_bp.route('/event/<int:club_id>/post-event', methods=['GET', 'POST'])
@login_required
def post_event(club_id):
    # Verify host status
    if not ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=club_id,
        is_host=True
    ).first():
        abort(403)
    
    club = Club.query.get_or_404(club_id)
    form = EventForm()
    
    if form.validate_on_submit():
        try:
            new_event = Event(
                title=form.title.data.strip(),
                description=form.description.data.strip(),
                date=form.date.data,        # ✅ Save date properly
                time=form.time.data,        # ✅ Save time properly
                location=form.location.data.strip(),
                club_id=club.id,
                host_id=current_user.id
            )
            
            db.session.add(new_event)
            db.session.commit()
            
            flash('Event created!', 'success')
            return redirect(url_for('event.events_page', club_id=club.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('post_event.html', form=form, club=club)

@event_bp.route('/event/<int:event_id>/attend', methods=['POST'])
@login_required
def mark_attendance(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check membership first
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
    flash('Attendance updated!', 'success')
    return redirect(url_for('event.events_page', club_id=event.club_id))