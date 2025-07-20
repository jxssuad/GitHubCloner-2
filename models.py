from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import secrets
import string


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    access_key_id = db.Column(db.Integer, db.ForeignKey('access_keys.id'), nullable=True)
    tradingview_username = db.Column(db.String(100), nullable=True)
    has_generated_access = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    access_key = db.relationship('AccessKey', back_populates='user')
    access_logs = db.relationship('AccessLog', back_populates='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class AccessKey(db.Model):
    __tablename__ = 'access_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_code = db.Column(db.String(32), unique=True, nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'used', 'expired'
    created_by_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='access_key', uselist=False)
    
    @staticmethod
    def generate_key():
        """Generate a unique 16-character access key"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(16))
    
    def mark_as_used(self):
        self.status = 'used'
        self.used_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<AccessKey {self.key_code}: {self.status}>'


class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'grant', 'remove'
    pine_script_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False)  # 'success', 'failed'
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='access_logs')
    
    def __repr__(self):
        return f'<AccessLog {self.username}: {self.action} - {self.status}>'


class PineScript(db.Model):
    __tablename__ = 'pine_scripts'
    
    id = db.Column(db.Integer, primary_key=True)
    pine_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PineScript {self.name}: {self.pine_id}>'


class UserAccess(db.Model):
    __tablename__ = 'user_accesses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pine_script_id = db.Column(db.Integer, db.ForeignKey('pine_scripts.id'), nullable=False)
    tradingview_username = db.Column(db.String(100), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='granted_accesses')
    pine_script = db.relationship('PineScript', backref='user_accesses')
    
    def __repr__(self):
        return f'<UserAccess {self.tradingview_username}: {self.pine_script_id}>'