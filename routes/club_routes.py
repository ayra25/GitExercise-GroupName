from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from models.club import ClubMembership, Club
from models.user import User
from models.event import Event, EventAttendance
from models.announcement import Announcement, PollOption, PollVote
from models.notification import Notification
from extensions import db
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import random
from models.banned import BannedMember

club_bp = Blueprint('club', __name__)

def verify_host(club_id):
    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=club_id,
        is_host=True
    ).first()
    
    if not membership:
        abort(403)

def create_notification(user_id, message, notification_type=None, related_id=None):
    notification = Notification(
        user_id=user_id,
        message=message,
        notification_type=notification_type,
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()

@club_bp.route('/dashboard')
@login_required
def dashboard():

    memberships = ClubMembership.query.filter_by(user_id=current_user.id).options(
        db.joinedload(ClubMembership.club).joinedload(Club.club_events)
    ).all()
    
    today = datetime.utcnow().date()
    club_ids = [m.club_id for m in memberships]
    
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
    
    attended_events = db.session.query(Event).join(
        EventAttendance,
        (EventAttendance.event_id == Event.id) & 
        (EventAttendance.user_id == current_user.id) &
        (EventAttendance.attended == True)
    ).filter(
        Event.club_id.in_(club_ids),
        Event.date <= today
    ).order_by(Event.date.desc()).limit(5).all()

    announcements = db.session.query(Announcement).select_from(Announcement).join(
    ClubMembership, ClubMembership.club_id == Announcement.club_id
    ).filter(
    ClubMembership.user_id == current_user.id
    ).order_by(Announcement.created_at.desc()).limit(5).all()

    month = request.args.get('month', type=int, default=datetime.utcnow().month)
    year = request.args.get('year', type=int, default=datetime.utcnow().year)
    
    if month < 1 or month > 12:
        month = datetime.utcnow().month
    if year < 2000 or year > 2100:
        year = datetime.utcnow().year
    
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
            participant_limit = request.form.get('participant_limit', type=int)

            if not name or not join_code:
                flash('Club name and join code are required', 'danger')
                return redirect(url_for('club.create_club'))

            if participant_limit is not None and participant_limit < 1:
                flash('Participant limit must be at least 1.', 'danger')
                return redirect(url_for('club.create_club'))

            if Club.query.filter_by(join_code=join_code).first():
                flash('Join code already taken!', 'danger')
                return redirect(url_for('club.create_club'))
            
            cover_image = random.randint(1, 5)

            new_club = Club(
                name=name,
                join_code=join_code,
                description=description,
                cover_image=cover_image,
                participant_limit=participant_limit if participant_limit else None
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
            
            return redirect(url_for('club.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating club: {str(e)}', 'danger')
            return redirect(url_for('club.create_club'))

    return render_template('create.html')


@club_bp.route('/join-club', methods=['GET', 'POST'])
@login_required
def join_club():
    join_code = None

    if request.method == 'GET':
        join_code = request.args.get('join_code')
        if not join_code:
            return render_template('join.html')

    elif request.method == 'POST':
        try:
            join_code = request.form['join_code']
            club = Club.query.filter_by(join_code=join_code).first()
            
            if not club:
                flash('Invalid join code', 'danger')
                return redirect(url_for('club.join_club'))
            
            banned = BannedMember.query.filter_by(club_id=club.id, user_id=current_user.id).first()
            if banned:
                flash("You are banned from this club and cannot join.", "danger")
                return redirect(url_for('club.join_club'))

                
            if ClubMembership.query.filter_by(user_id=current_user.id, club_id=club.id).first():
                flash('You are already a member of this club', 'info')
                return redirect(url_for('club.join_club'))
            
            current_members = ClubMembership.query.filter_by(club_id=club.id,).count()
            if club.participant_limit and current_members >= club.participant_limit:
                flash('This club has reached its participant limit.', 'danger')
                return redirect(url_for('club.join_club'))
                
            new_membership = ClubMembership(
                user_id=current_user.id,
                club_id=club.id,
                is_host=False
            )
            
            db.session.add(new_membership)
            db.session.commit()
            
            return redirect(url_for('club.dashboard'))
            
        except KeyError:
            flash("Bad Request: 'join_code' not provided", 'danger')
            return redirect(url_for('club.join_club'))

    club = Club.query.filter_by(join_code=join_code).first()

    if not club:
        flash('Invalid join code. Club not found.', 'danger')
        return render_template('join.html') 
    
    existing_membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=club.id
    ).first()
    
    if existing_membership:
        flash('You are already a member of this club.', 'info')
        return redirect(url_for('club.dashboard'))

    current_members = ClubMembership.query.filter_by(club_id=club.id).count()
    if club.participant_limit and current_members >= club.participant_limit:
        flash('This club has reached its participant limit.', 'danger')
        return render_template('join.html')

    new_membership = ClubMembership(
        user_id=current_user.id,
        club_id=club.id,
        is_host=False
    )

    db.session.add(new_membership)
    db.session.commit()

    return redirect(url_for('club.dashboard'))

@club_bp.route('/club/<int:club_id>/members')
@login_required
def view_members(club_id):
    verify_host(club_id)  

    club = Club.query.get_or_404(club_id)
    members = ClubMembership.query.filter_by(club_id=club_id).join(ClubMembership.member).all()

    return render_template('members.html', club=club, members=members)

@club_bp.route('/club/<int:club_id>/remove-member', methods=['POST'])
@login_required
def remove_member(club_id):
    verify_host(club_id)  
    
    club = Club.query.get_or_404(club_id)
    member_id = request.form.get('member_id')
    
    if not member_id:
        flash('Invalid member selection.', 'danger')
        return redirect(url_for('club.view_members', club_id=club_id))

    if int(member_id) == current_user.id:
        flash("You can't remove yourself as host.", 'danger')
        return redirect(url_for('club.view_members', club_id=club_id))

    membership = ClubMembership.query.filter_by(user_id=member_id, club_id=club_id).first()

    if not membership:
        flash('Member not found.', 'warning')
    elif membership.is_host:
        flash('You cannot remove another host.', 'danger')
    else:
        
        create_notification(
            user_id=member_id,
            message=f"You've been removed from {club.name}",
            notification_type='membership',
            related_id=club_id
        )
        
        db.session.delete(membership)
        db.session.commit()  

    return redirect(url_for('club.view_members', club_id=club_id))

@club_bp.route('/club/<int:club_id>/promote-member', methods=['POST'])
@login_required
def promote_member(club_id):
    verify_host(club_id)

    club = Club.query.get_or_404(club_id)

    member_id = request.form.get('member_id')
    if not member_id:
        flash('Invalid member selection.', 'danger')
        return redirect(url_for('club.view_members', club_id=club_id))

    membership = ClubMembership.query.filter_by(user_id=member_id, club_id=club_id).first()
    if not membership:
        flash('Member not found.', 'warning')
    elif membership.is_host:
        flash('This user is already a host.', 'info')
    else:
        membership.is_host = True

        create_notification(
            user_id=member_id,
            message=f"You've been promoted to host in {club.name}",
            notification_type='membership',
            related_id=club_id
        )
        
        db.session.commit()

    return redirect(url_for('club.view_members', club_id=club_id))

@club_bp.route('/ban-member/<int:club_id>/<int:user_id>', methods=['POST'])
@login_required
def ban_member(club_id, user_id):

    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id, is_host=True).first()
    if not membership:
        flash("You are not authorized to ban members from this club.", "danger")
        return redirect(url_for('club.dashboard'))

    existing_ban = BannedMember.query.filter_by(club_id=club_id, user_id=user_id).first()
    if existing_ban:
        flash("User is already banned from this club.", "info")
        return redirect(url_for('club.view_members', club_id=club_id))


    new_ban = BannedMember(user_id=user_id, club_id=club_id)
    db.session.add(new_ban)


    membership_to_remove = ClubMembership.query.filter_by(user_id=user_id, club_id=club_id).first()
    if membership_to_remove:
        db.session.delete(membership_to_remove)

    db.session.commit()
    flash("Member has been banned from the club.", "success")
    return redirect(url_for('club.view_members', club_id=club_id))

@club_bp.route('/club/<int:club_id>/banned-members')
@login_required
def view_banned_members(club_id):
    verify_host(club_id)

    club = Club.query.get_or_404(club_id)
    banned_members = BannedMember.query.filter_by(club_id=club_id).join(BannedMember.user).all()

    return render_template('banned_members.html', club=club, banned_members=banned_members)

@club_bp.route('/club/<int:club_id>/unban-member/<int:user_id>', methods=['POST'])
@login_required
def unban_member(club_id, user_id):
    verify_host(club_id)

    ban_entry = BannedMember.query.filter_by(club_id=club_id, user_id=user_id).first()
    if not ban_entry:
        flash("User is not banned.", "info")
        return redirect(url_for('club.view_banned_members', club_id=club_id))

    db.session.delete(ban_entry)
    db.session.commit()

    flash("User has been unbanned and can now rejoin the club.", "success")
    return redirect(url_for('club.view_banned_members', club_id=club_id))


@club_bp.route('/club/<int:club_id>/analytics')
@login_required
def attendance_analytics(club_id):
    verify_host(club_id)
    
    club = Club.query.get_or_404(club_id)
    
    # Get all events with their attendances
    events = Event.query.filter_by(club_id=club_id).options(
        db.joinedload(Event.attendances)
    ).order_by(Event.date).all()
    
    # Calculate event statistics
    event_stats = []
    total_members = ClubMembership.query.filter_by(club_id=club_id).count()
    
    for event in events:
        attended = sum(1 for a in event.attendances if a.attended)
        event_stats.append({
            'event': event,
            'total_participants': total_members,
            'attended': attended,
            'attendance_rate': (attended / total_members * 100) if total_members > 0 else 0
        })
    
    # Calculate member statistics
    members = ClubMembership.query.filter_by(club_id=club_id).options(
        db.joinedload(ClubMembership.member)
    ).all()
    
    member_stats = []
    total_events = len(events)
    
    for member in members:
        attended_events = db.session.query(EventAttendance).join(Event).filter(
            Event.club_id == club_id,
            EventAttendance.user_id == member.user_id,
            EventAttendance.attended == True
        ).count()
        
        member_stats.append({
            'member': member.member,
            'total_events': total_events,
            'attended_events': attended_events,
            'attendance_rate': (attended_events / total_events * 100) if total_events > 0 else 0
        })
    
    # Calculate monthly statistics
    monthly_stats = []
    monthly_data = {}
    
    for event in events:
        month_year = event.date.strftime("%b %Y")
        attended = sum(1 for a in event.attendances if a.attended)
        
        if month_year not in monthly_data:
            monthly_data[month_year] = {
                'total_events': 0,
                'total_participants': 0,
                'total_attended': 0
            }
        
        monthly_data[month_year]['total_events'] += 1
        monthly_data[month_year]['total_participants'] += total_members
        monthly_data[month_year]['total_attended'] += attended
    
    # Convert to the format needed for the chart
    for month, data in monthly_data.items():
        if data['total_participants'] > 0:
            rate = (data['total_attended'] / data['total_participants']) * 100
            monthly_stats.append({
                'month': month,
                'attendance_rate': round(rate, 1),
                'events_count': data['total_events']
            })
    
    return render_template('attendance_analytics.html',
        club=club,
        event_stats=event_stats,
        member_stats=member_stats,
        monthly_stats=monthly_stats  # Add this line to pass the monthly data
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

    club = Club.query.get_or_404(club_id)
    
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
            db.session.flush() 
            
            if has_poll and poll_options:
                for option_text in poll_options:
                    if option_text.strip():  
                        option = PollOption(
                            text=option_text.strip(),
                            announcement_id=new_announcement.id
                        )
                        db.session.add(option)
            
            db.session.commit()

            members = ClubMembership.query.filter_by(club_id=club_id).all()
            for member in members:
                if member.user_id != current_user.id:
                    create_notification(
                        user_id=member.user_id,
                        message=f"New announcement in {club.name}: {new_announcement.title}",
                        notification_type='announcement',
                        related_id=new_announcement.id
                    )

            db.session.commit()
            
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
    
    membership = ClubMembership.query.filter_by(
        user_id=current_user.id,
        club_id=announcement.club_id
    ).first()
    
    if not membership:
        abort(403)
    
    existing_vote = PollVote.query.filter_by(
        user_id=current_user.id,
        option_id=option_id
    ).first()
    
    if existing_vote:
        flash('You have already voted in this poll', 'info')
    else:
        votes_to_delete = PollVote.query.filter(
            PollVote.user_id == current_user.id,
            PollOption.announcement_id == announcement.id,
            PollOption.id == PollVote.option_id
        ).join(PollOption).all()
        
        for vote in votes_to_delete:
            db.session.delete(vote)
        
        new_vote = PollVote(
            user_id=current_user.id,
            option_id=option_id
        )
        db.session.add(new_vote)
        db.session.commit()
    
    return redirect(url_for('event.events_page', club_id=announcement.club_id))

@club_bp.route('/club/<int:club_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_club(club_id):
    verify_host(club_id)

    club = Club.query.get_or_404(club_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        participant_limit = request.form.get('participant_limit', type=int)

        if not name:
            flash('Club name cannot be empty.', 'danger')
            return redirect(url_for('club.edit_club', club_id=club_id))

        if participant_limit is not None and participant_limit < 1:
            flash('Participant limit must be at least 1.', 'danger')
            return redirect(url_for('club.edit_club', club_id=club_id))

        club.name = name
        club.description = description or None
        club.participant_limit = participant_limit if participant_limit else None
        db.session.commit()

        return redirect(url_for('club.dashboard'))

    return render_template('edit_club.html', club=club)


@club_bp.route('/<int:club_id>/announcement/<int:announcement_id>/delete', methods=['POST'])
@login_required
def delete_announcement(club_id, announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)

   
    membership = ClubMembership.query.filter_by(user_id=current_user.id, club_id=club_id, is_host=True).first()
    if not membership:
        flash("You don't have permission to delete this announcement.", "danger")
        return redirect(url_for('event.events_page', club_id=club_id))

    db.session.delete(announcement)
    db.session.commit()
    return redirect(url_for('event.events_page', club_id=club_id))

@club_bp.route('/club/<int:club_id>/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(club_id, event_id):
    verify_host(club_id)
    
    event = Event.query.get_or_404(event_id)
    
    if event.club_id != club_id:
        abort(403)
    
    try:
        EventAttendance.query.filter_by(event_id=event_id).delete()
        
        db.session.delete(event)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting event: {str(e)}', 'danger')
    
    return redirect(url_for('event.events_page', club_id=club_id))

@club_bp.route('/club/<int:club_id>/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(club_id, event_id):
    verify_host(club_id)
    
    event = Event.query.get_or_404(event_id)
    club = Club.query.get_or_404(club_id)
    
    if event.club_id != club_id:
        abort(403)
    
    if request.method == 'POST':
        try:
            event.title = request.form.get('title', '').strip()
            event.description = request.form.get('description', '').strip()
            event.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            event.time = datetime.strptime(request.form.get('time'), '%H:%M').time()
            event.location = request.form.get('location', '').strip()
            event.additional_info = request.form.get('additional_info', '').strip() or None
            
            db.session.commit()
            return redirect(url_for('event.events_page', club_id=club_id, selected=event_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating event: {str(e)}', 'danger')
    
    return render_template('edit_event.html', 
                         club=club,  
                         event=event,
                         datetime=datetime)

@club_bp.route('/club/<int:club_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_club(club_id):
    verify_host(club_id)
    club = Club.query.get_or_404(club_id)
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        if not password:
            flash('Please enter your password', 'danger')
            return redirect(url_for('club.delete_club', club_id=club_id))
            
        if not current_user.check_password(password):
            flash('Incorrect password. Please try again.', 'danger')
            return render_template('delete_club.html', 
                               club=club,
                               password_error=True)
        
        try:
            EventAttendance.query.filter(
                EventAttendance.event_id.in_(
                    db.session.query(Event.id).filter_by(club_id=club_id)
                )
            ).delete(synchronize_session=False)

            Event.query.filter_by(club_id=club_id).delete()
            Announcement.query.filter_by(club_id=club_id).delete()
            ClubMembership.query.filter_by(club_id=club_id).delete()

            db.session.delete(club)
            db.session.commit()

            return redirect(url_for('club.dashboard'))

            
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting club: {str(e)}', 'danger')
            return redirect(url_for('club.delete_club', club_id=club_id))
    
    return render_template('delete_club.html', club=club)