from extensions import db

class Club(db.Model):
    __tablename__ = 'clubs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    join_code = db.Column(db.String(10), nullable=False, unique=True)
    cover_image = db.Column(db.Integer, default=1)
    
    
    club_events = db.relationship('Event', back_populates='club', cascade='all, delete-orphan')
    memberships = db.relationship('ClubMembership', back_populates='club')  


class ClubMembership(db.Model):
    __tablename__ = 'club_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'))
    is_host = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=db.func.now())
    
    member = db.relationship('User', back_populates='club_memberships')
    club = db.relationship('Club', back_populates='memberships')





