from datetime import datetime
from extensions import db

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    has_poll = db.Column(db.Boolean, default=False)
    
    club = db.relationship('Club', backref=db.backref('announcements', lazy=True))
    
class PollOption(db.Model):
    __tablename__ = 'poll_options'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id'), nullable=False)
    
    announcement = db.relationship('Announcement', backref=db.backref('poll_options', lazy=True, cascade='all, delete-orphan'))

class PollVote(db.Model):
    __tablename__ = 'poll_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('poll_options.id'), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('poll_votes'))
    option = db.relationship('PollOption', backref=db.backref('votes', cascade='all, delete-orphan'))