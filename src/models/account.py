from src.models.user import db
from datetime import datetime

class InstagramAccount(db.Model):
    __tablename__ = 'instagram_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    two_factor = db.Column(db.String(20), nullable=True)
    price = db.Column(db.Float, default=0.10, nullable=False)
    is_sold = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<InstagramAccount {self.username}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'two_factor': self.two_factor,
            'price': self.price,
            'is_sold': self.is_sold,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
