from src.models.user import db
from datetime import datetime

class InstagramAccount(db.Model):
    __tablename__ = 'instagram_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    two_factor = db.Column(db.String(50), nullable=True)
    is_sold = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'two_factor': self.two_factor,
            'is_sold': self.is_sold,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
