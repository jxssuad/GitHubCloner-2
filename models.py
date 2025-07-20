from app import db
from datetime import datetime

class AccessLog(db.Model):
    """Model to track access management operations"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    pine_id = db.Column(db.String(100), nullable=False)
    operation = db.Column(db.String(50), nullable=False)  # 'grant', 'remove', 'check'
    status = db.Column(db.String(50), nullable=False)  # 'success', 'failure'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)

class PineScript(db.Model):
    """Model to store Pine Script configurations"""
    id = db.Column(db.Integer, primary_key=True)
    pine_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
