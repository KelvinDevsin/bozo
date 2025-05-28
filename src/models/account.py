from src.models.user import db
from datetime import datetime

class AccountType(db.Model):
    __tablename__ = 'account_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, default=0.0, nullable=False)
    is_empty = db.Column(db.Boolean, default=True)  # True para contas vazias, False para contas montadas
    available_quantity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    accounts = db.relationship('InstagramAccount', backref='account_type', lazy=True)
    
    def __repr__(self):
        return f'<AccountType {self.name}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'is_empty': self.is_empty,
            'available_quantity': self.available_quantity,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class InstagramAccount(db.Model):
    __tablename__ = 'instagram_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    two_factor = db.Column(db.String(20), nullable=True)
    account_type_id = db.Column(db.Integer, db.ForeignKey('account_types.id'), nullable=True)
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
            'account_type_id': self.account_type_id,
            'is_sold': self.is_sold,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
