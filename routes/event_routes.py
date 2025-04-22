# routes/event_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.event import Event
from app import db

event_bp = Blueprint('event', __name__)

# Route to show the event posting form
@event_bp.route('/event')
def event():
    all_events = Event.query.order_by(Event.date_posted.desc()).all()
    return render_template('event.html', events=all_events)   

@event_bp.route('/post', methods=['GET', 'POST'])
def post_event():
    if request.method == 'POST':
        # Grab data from form
        title = request.form.get('eventTitle')
        description = request.form.get('eventDescription')

        # Validate form input
        if not title or not description:
            flash('Please fill out all fields.', 'danger')
            return redirect(url_for('event.post_event'))

        # Create new event instance
        new_event = Event(title=title, description=description)

        # Add to DB
        db.session.add(new_event)
        db.session.commit()

        flash('Event posted successfully!', 'success')
        return redirect(url_for('event.post_event'))

    # If GET request, just show the form
    return render_template('post-event.html')
