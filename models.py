from app import db
from datetime import datetime
import secrets
import string


class AccessKey(db.Model):
    """Model to store one-time access keys"""
    __tablename__ = 'access_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_code = db.Column(db.String(32), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    used_at = db.Column(db.DateTime)
    used_by_username = db.Column(db.String(100))
    
    # Relationship to access logs
    access_logs = db.relationship('AccessLog', backref='access_key', lazy=True)

    @staticmethod
    def generate_key():
        """Generate a unique 8-character access key"""
        while True:
            key = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not AccessKey.query.filter_by(key_code=key).first():
                return key

    def __repr__(self):
        return f'<AccessKey {self.key_code}>'


class AccessLog(db.Model):
    """Model to track access management operations"""
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    pine_id = db.Column(db.String(100), nullable=False)
    pine_script_name = db.Column(db.String(200), nullable=False)
    operation = db.Column(db.String(50), nullable=False)  # 'grant', 'remove', 'check'
    status = db.Column(db.String(50), nullable=False)  # 'success', 'failure'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)
    
    # Foreign key to access key
    key_id = db.Column(db.Integer, db.ForeignKey('access_keys.id'), nullable=True)

    def __repr__(self):
        return f'<AccessLog {self.username} - {self.operation} {self.pine_script_name}>'


class PineScript(db.Model):
    """Model to store Pine Script configurations"""
    __tablename__ = 'pine_scripts'
    
    id = db.Column(db.Integer, primary_key=True)
    pine_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PineScript {self.name}>'
