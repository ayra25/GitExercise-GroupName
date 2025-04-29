from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  
    first_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='normal_user')
    
    
    hosted_events = db.relationship('Event', back_populates='host')
    event_attendances = db.relationship('EventAttendance', back_populates='user')
    club_memberships = db.relationship('ClubMembership', back_populates='member')

