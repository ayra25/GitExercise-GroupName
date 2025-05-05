from datetime import datetime
from extensions import db

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)  
    
    club = db.relationship('Club', backref=db.backref('announcements', lazy=True))
    
    def __repr__(self):
        return f"<Announcement {self.title}>"