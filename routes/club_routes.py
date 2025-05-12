from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from models.club import ClubMembership, Club
from models.event import Event, EventAttendance
from models.announcement import Announcement, PollOption, PollVote
from extensions import db
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import calendar
import random

club_bp = Blueprint('club', __name__)

def verify_host(club_id):
    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=club_id,
        is_host=True
    ).first()
    
    if not membership:
        abort(403)

@club_bp.route('/dashboard')
@login_required
def dashboard():
    # Get all clubs the user is a member of with their events
    memberships = ClubMembership.query.filter_by(user_id=current_user.id).options(
        db.joinedload(ClubMembership.club).joinedload(Club.club_events)
    ).all()
    
    today = datetime.utcnow().date()
    club_ids = [m.club_id for m in memberships]
    
    # Prepare clubs data
    clubs_data = []
    for membership in memberships:
        club = membership.club
        total_events = len(club.club_events)
        upcoming_count = sum(1 for e in club.club_events if e.date >= today)
        
        clubs_data.append({
            'club': club,
            'total_events': total_events,
            'upcoming_count': upcoming_count,
            'is_host': membership.is_host
        })
    
    # Get upcoming events (next 5 days)
    upcoming_events = db.session.query(Event).outerjoin(
        EventAttendance,
        (EventAttendance.event_id == Event.id) & 
        (EventAttendance.user_id == current_user.id)
    ).filter(
        Event.club_id.in_(club_ids),
        Event.date >= today,
        db.or_(
            EventAttendance.attended == None,  
            EventAttendance.attended == False  
        )
    ).order_by(Event.date.asc()).limit(5).all()
    
    # Get attended events (most recent 5)
    attended_events = db.session.query(Event).join(
        EventAttendance,
        (EventAttendance.event_id == Event.id) & 
        (EventAttendance.user_id == current_user.id) &
        (EventAttendance.attended == True)
    ).filter(
        Event.club_id.in_(club_ids),
        Event.date <= today
    ).order_by(Event.date.desc()).limit(5).all()

    # Get announcements (most recent 5)
    announcements = db.session.query(Announcement).select_from(Announcement).join(
    ClubMembership, ClubMembership.club_id == Announcement.club_id
    ).filter(
    ClubMembership.user_id == current_user.id
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    # Calendar setup
    month = request.args.get('month', type=int, default=datetime.utcnow().month)
    year = request.args.get('year', type=int, default=datetime.utcnow().year)
    
    # Validate month and year
    if month < 1 or month > 12:
        month = datetime.utcnow().month
    if year < 2000 or year > 2100:
        year = datetime.utcnow().year
    
    # Calculate previous and next months for navigation
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
        
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    # Prepare calendar events
    calendar_events = []
    for membership in memberships:
        start_date = datetime(year, month, 1).date()
        end_date = datetime(next_year, next_month, 1).date() - timedelta(days=1)
        
        club_events = Event.query.filter(
            Event.club_id == membership.club_id,
            Event.date >= datetime(prev_year, prev_month, 1).date(),
            Event.date <= end_date
        ).all()
        
        for event in club_events:
            calendar_events.append({
                'date': event.date,
                'title': event.title,
                'club_id': membership.club_id,
                'event_id': event.id,
                'club_name': membership.club.name,
                'url': url_for('event.events_page', club_id=membership.club_id, selected=event.id)
            })
    
    return render_template('home.html',
        clubs_data=clubs_data,
        upcoming_events=upcoming_events,
        attended_events=attended_events,
        announcements=announcements,
        now=datetime.utcnow(),
        calendar_events=calendar_events,
        current_month=month,
        current_year=year,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        datetime=datetime,
        timedelta=timedelta
    )

@club_bp.route('/create-club', methods=['GET', 'POST'])
@login_required
def create_club():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            join_code = request.form.get('join_code', '').strip()
            description = request.form.get('description', '').strip() or None

            if not name or not join_code:
                flash('Club name and join code are required', 'danger')
                return redirect(url_for('club.create_club'))

            if Club.query.filter_by(join_code=join_code).first():
                flash('Join code already taken!', 'danger')
                return redirect(url_for('club.create_club'))
            
            cover_image = random.randint(1, 5)

            new_club = Club(
                name=name,
                join_code=join_code,
                description=description,
                cover_image=cover_image
            )
            db.session.add(new_club)
            db.session.flush()

            new_membership = ClubMembership(
                user_id=current_user.id,
                club_id=new_club.id,
                is_host=True
            )
            db.session.add(new_membership)
            db.session.commit()
            
            flash('Club created successfully!', 'success')
            return redirect(url_for('club.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating club: {str(e)}', 'danger')
            return redirect(url_for('club.create_club'))

    return render_template('create.html')

@club_bp.route('/join-club', methods=['GET', 'POST'])
@login_required
def join_club():
    if request.method == 'POST':
        try:
            join_code = request.form['join_code']
            club = Club.query.filter_by(join_code=join_code).first()
            
            if not club:
                flash('Invalid join code', 'danger')
                return redirect(url_for('club.join_club'))
                
            if ClubMembership.query.filter_by(user_id=current_user.id, club_id=club.id).first():
                flash('You are already a member of this club', 'info')
                return redirect(url_for('club.join_club'))
                
            new_membership = ClubMembership(
                user_id=current_user.id,
                club_id=club.id,
                is_host=False
            )
            
            db.session.add(new_membership)
            db.session.commit()
            
            flash(f'Successfully joined {club.name}!', 'success')
            return redirect(url_for('club.dashboard'))
            
        except KeyError:
            return "Bad Request: 'join_code' not provided", 400
            
    return render_template('join.html')

@club_bp.route('/club/<int:club_id>/analytics')
@login_required
def attendance_analytics(club_id):
    verify_host(club_id)
    
    club = Club.query.get_or_404(club_id)
    
    events = Event.query.filter_by(club_id=club_id).options(
        db.joinedload(Event.attendances)
    ).all()
    
    event_stats = []
    for event in events:
        total_members = ClubMembership.query.filter_by(club_id=club_id).count()
        attended = sum(1 for a in event.attendances if a.attended)
        event_stats.append({
            'event': event,
            'total_participants': total_members,
            'attended': attended,
            'attendance_rate': (attended / total_members * 100) if total_members > 0 else 0
        })
    
    members = ClubMembership.query.filter_by(club_id=club_id).options(
        db.joinedload(ClubMembership.member)
    ).all()
    
    member_stats = []
    for member in members:
        total_events = Event.query.filter_by(club_id=club_id).count()
        attended_events = EventAttendance.query.filter_by(
            user_id=member.user_id,
            attended=True
        ).count()
        member_stats.append({
            'member': member.member, 
            'total_events': total_events,
            'attended_events': attended_events,
            'attendance_rate': (attended_events / total_events * 100) if total_events > 0 else 0
        })
    
    return render_template('attendance_analytics.html',
        club=club,
        event_stats=event_stats,
        member_stats=member_stats
    )

@club_bp.route('/my-events')
@login_required
def event_history():
    attended_events = db.session.query(Event).join(
        EventAttendance,
        (EventAttendance.event_id == Event.id) & 
        (EventAttendance.user_id == current_user.id) &
        (EventAttendance.attended == True)
    ).order_by(Event.date.desc()).all()
    
    return render_template('event_history.html', 
        events=attended_events,
        now=datetime.utcnow()
    )

@club_bp.route('/club/<int:club_id>/post-announcement', methods=['GET', 'POST'])
@login_required
def post_announcement(club_id):
    verify_host(club_id)
    
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            has_poll = 'has_poll' in request.form
            poll_options = request.form.getlist('poll_options[]')
            
            if not title or not content:
                flash('Title and content are required', 'danger')
                return redirect(url_for('club.post_announcement', club_id=club_id))
                
            new_announcement = Announcement(
                title=title,
                content=content,
                club_id=club_id,
                has_poll=has_poll
            )
            
            db.session.add(new_announcement)
            db.session.flush()  # Get the announcement ID
            
            if has_poll and poll_options:
                for option_text in poll_options:
                    if option_text.strip():  # Skip empty options
                        option = PollOption(
                            text=option_text.strip(),
                            announcement_id=new_announcement.id
                        )
                        db.session.add(option)
            
            db.session.commit()
            
            flash('Announcement posted!', 'success')
            return redirect(url_for('event.events_page', club_id=club_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error posting announcement: {str(e)}', 'danger')
    
    return render_template('post_announcement.html', club_id=club_id)

@club_bp.route('/leave-club', methods=['POST'])
@login_required
def leave_club():
    try:
        club_id = request.form.get('club_id')
        if not club_id:
            flash('Invalid request', 'danger')
            return redirect(url_for('club.dashboard'))
        
        membership = ClubMembership.query.filter_by(
            user_id=current_user.id,
            club_id=club_id
        ).first()
        
        if not membership:
            flash('You are not a member of this club', 'danger')
            return redirect(url_for('club.dashboard'))
        
        if membership.is_host:
            flash('Hosts cannot leave their own club', 'danger')
            return redirect(url_for('club.dashboard'))
        
        db.session.delete(membership)
        db.session.commit()
        
        flash('You have left the club', 'success')
        return redirect(url_for('club.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error leaving club: {str(e)}', 'danger')
        return redirect(url_for('club.dashboard'))
    
@club_bp.route('/vote-poll/<int:option_id>', methods=['POST'])
@login_required
def vote_poll(option_id):
    option = PollOption.query.get_or_404(option_id)
    announcement = option.announcement
    
    # Check if user is a member of the club
    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=announcement.club_id
    ).first()
    
    if not membership:
        abort(403)
    
    # Check if user already voted in this poll
    existing_vote = PollVote.query.filter_by(
        user_id=current_user.id,
        option_id=option_id
    ).first()
    
    if existing_vote:
        flash('You have already voted in this poll', 'info')
    else:
        # Delete any previous votes in this poll (modified for SQLite compatibility)
        votes_to_delete = PollVote.query.filter(
            PollVote.user_id == current_user.id,
            PollOption.announcement_id == announcement.id,
            PollOption.id == PollVote.option_id
        ).join(PollOption).all()
        
        for vote in votes_to_delete:
            db.session.delete(vote)
        
        # Add new vote
        new_vote = PollVote(
            user_id=current_user.id,
            option_id=option_id
        )
        db.session.add(new_vote)
        db.session.commit()
        flash('Your vote has been recorded', 'success')
    
    return redirect(url_for('event.events_page', club_id=announcement.club_id))