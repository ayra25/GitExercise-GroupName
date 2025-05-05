from datetime import datetime
from extensions import db

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)  
    time = db.Column(db.Time, nullable=False) 
    location = db.Column(db.String(100))
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'))
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    club = db.relationship('Club', back_populates='club_events')
    host = db.relationship('User', back_populates='hosted_events')
    attendances = db.relationship('EventAttendance', back_populates='event', cascade='all, delete-orphan')
    comments = db.relationship('EventComment', back_populates='event', cascade='all, delete-orphan')

class EventAttendance(db.Model):
    __tablename__ = 'event_attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    attended = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    event = db.relationship('Event', back_populates='attendances')
    user = db.relationship('User', back_populates='event_attendances')