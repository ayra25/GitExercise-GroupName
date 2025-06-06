from extensions import db

class BannedMember(db.Model):
    __tablename__ = 'banned_members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    reason = db.Column(db.String(255))
    banned_at = db.Column(db.DateTime, default=db.func.now())

    user = db.relationship('User')  # Optional, for easy access to user info
    club = db.relationship('Club', back_populates='banned_members')  # Step 2
