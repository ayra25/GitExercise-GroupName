from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, current_user
from models.event import Event, EventAttendance
from models.club import Club, ClubMembership
from models.form import EventForm
from models.announcement import Announcement, PollVote, PollOption
from models.comment import EventComment
from routes.club_routes import create_notification
from extensions import db
from datetime import datetime, timedelta

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
    
    events = Event.query.options(
        db.joinedload(Event.comments).joinedload(EventComment.user)
    ).filter_by(club_id=club_id).order_by(Event.date.desc()).all()

    announcements = Announcement.query.options(
        db.joinedload(Announcement.poll_options).joinedload(PollOption.votes)
    ).filter_by(
        club_id=club_id
    ).order_by(Announcement.created_at.desc()).all()

    announcements_data = []
    for announcement in announcements:
        announcement_dict = {
            'announcement': announcement,
            'total_votes': 0,
            'options': [],
            'user_has_voted': False,
            'user_voted_option': None  
        }
        
        if announcement.has_poll and announcement.poll_options:
            total_votes = 0
            user_has_voted = False
            user_voted_option = None
            
            options = []
            for option in announcement.poll_options:
                option_votes = len(option.votes)
                total_votes += option_votes
                
                user_vote = any(vote.user_id == current_user.id for vote in option.votes)
                if user_vote:
                    user_has_voted = True
                    user_voted_option = option.id
                
                options.append({
                    'option': option,
                    'votes': option_votes,
                    'user_voted': user_vote
                })
            
            announcement_dict['total_votes'] = total_votes
            announcement_dict['options'] = options
            announcement_dict['user_has_voted'] = user_has_voted
            announcement_dict['user_voted_option'] = user_voted_option
        
        announcements_data.append(announcement_dict)
    
    user_voted_announcements = set()
    if current_user.is_authenticated:
        user_votes = PollVote.query.join(
            PollOption,
            PollOption.id == PollVote.option_id
        ).filter(
            PollVote.user_id == current_user.id
        ).all()
        user_voted_announcements = {vote.option.announcement_id for vote in user_votes}
    
    selected_id = request.args.get('selected')
    selected_event = next(
        (e for e in events if str(e.id) == selected_id),
        events[0] if events else None
    )

    host_user_ids = {m.user_id for m in club.memberships if m.is_host}

    return render_template('event.html',
        club=club,
        events=events,
        announcements=announcements_data,
        selected_event=selected_event,
        is_host=membership.is_host,
        now=datetime.utcnow(),
        timedelta=timedelta,
        membership=membership,
        host_user_ids=host_user_ids,
        user_voted_announcements=user_voted_announcements
    )

@event_bp.route('/event/<int:club_id>/post-event', methods=['GET', 'POST'])
@login_required
def post_event(club_id):

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
                date=form.date.data,        
                time=form.time.data,        
                location=form.location.data.strip(),
                club_id=club.id,
                host_id=current_user.id
            )
            
            db.session.add(new_event)
            db.session.flush()

            members = ClubMembership.query.filter_by(club_id=club_id).all()
            club = Club.query.get(club_id)

            for member in members:
                if member.user_id != current_user.id:
                    create_notification(
                        user_id=member.user_id,
                        message=f"New event in {club.name}: {new_event.title}",
                        notification_type='event',
                        related_id=club_id
                    )
            
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

@event_bp.route('/event/<int:event_id>/comment', methods=['POST'])
@login_required
def post_comment(event_id):
    event = Event.query.get_or_404(event_id)
    parent_id = request.form.get('parent_id')
    
    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=event.club_id
    ).first()
    
    if not membership:
        abort(403)
    
    content = request.form.get('comment_content', '').strip()
    if not content:
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('event.events_page', club_id=event.club_id, selected=event_id))
    
    try:
        comment = EventComment(
            content=content,
            user_id=current_user.id,
            event_id=event.id,
            parent_id=parent_id if parent_id else None
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment posted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to post comment', 'danger')
    
    return redirect(url_for('event.events_page', club_id=event.club_id, selected=event_id))