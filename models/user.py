from extensions import db
from flask_login import UserMixin
from models.notification import Notification
import bcrypt

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(150))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='normal_user')
    bio = db.Column(db.Text, default="")
    
    hosted_events = db.relationship('Event', back_populates='host')
    event_attendances = db.relationship('EventAttendance', back_populates='user')
    club_memberships = db.relationship('ClubMembership', back_populates='member')
    event_comments = db.relationship('EventComment', back_populates='user')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def unread_notifications_count(self):
        return Notification.query.filter_by(
            user_id=self.id,
            is_read=False
        ).count()

    def recent_notifications(self, limit=5):
        return Notification.query.filter_by(
            user_id=self.id
        ).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
    