from flask import Blueprint, render_template

event_bp = Blueprint('event', __name__)

#dummy data
events = [
    {
        'title': 'Weekly Chess Night 2',
        'time': '2:00 p.m. – 4:00 p.m.',
        'location': 'CQA2003',
        'description': 'Come join us on 24/5! Make sure to...',
        'details': 'Join us for a relaxed evening of chess! Whether you\'re here to learn, practice, or show off your skills...'
    },
    {
        'title': 'Ice Breaking Session',
        'time': '2:00 p.m. – 4:00 p.m.',
        'location': 'CQA2003',
        'description': 'Come join us on 24/5! Make sure to...',
        'details': 'An ice-breaking session for new members! Fun games, quick matches, and lots of laughs.'
    }
]

announcements = [
    {
        'title': 'Weekly Chess Night Poll',
        'description': 'Help us make Chess Night even better! 🌟 Cast your vote and let us know...',
        'details': 'Help us make Chess Night even better! 🌟 Cast your vote and let us know your preferences...'
    },
    {
        'title': 'MMU Chess Championship',
        'description': '2:00 p.m. – 4:00 p.m. @ CQA2003<br>Come join us on 24/5! Make sure to...',
        'details': 'The MMU Chess Championship is back! 🏆 Sign up now and stand a chance to win prizes!'
    }
]

@event_bp.route('/event')
def event_page():
    return render_template('event.html', events=events, announcements=announcements)

@event_bp.route('/post-event')
def post_page():
    return render_template('post_event.html')
