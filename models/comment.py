from extensions import db
from datetime import datetime

class EventComment(db.Model):
    __tablename__ = 'event_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('event_comments.id'))  # New field for replies
    
    user = db.relationship('User', back_populates='event_comments')
    event = db.relationship('Event', back_populates='comments')
    parent = db.relationship('EventComment', remote_side=[id], backref='replies')  # Self-referential relationship