
from datetime import datetime
import secrets
import string

# In-memory storage for the application
access_keys = {}
access_logs = []
pine_scripts = {}

class AccessKey:
    """In-memory access key storage"""
    
    def __init__(self, key_code):
        self.key_code = key_code
        self.created_at = datetime.utcnow()
        self.is_used = False
        self.used_at = None
        self.used_by_username = None
    
    @staticmethod
    def generate_key():
        """Generate a unique 8-character access key"""
        while True:
            key = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if key not in access_keys:
                return key
    
    @staticmethod
    def create(key_code):
        """Create and store a new access key"""
        key = AccessKey(key_code)
        access_keys[key_code] = key
        return key
    
    @staticmethod
    def get(key_code):
        """Get access key by code"""
        return access_keys.get(key_code)
    
    @staticmethod
    def get_all():
        """Get all access keys"""
        return list(access_keys.values())
    
    @staticmethod
    def count():
        """Count total access keys"""
        return len(access_keys)
    
    @staticmethod
    def count_used():
        """Count used access keys"""
        return sum(1 for key in access_keys.values() if key.is_used)

class AccessLog:
    """In-memory access log storage"""
    
    def __init__(self, username, pine_id, pine_script_name, operation, status, details="", key_code=None):
        self.username = username
        self.pine_id = pine_id
        self.pine_script_name = pine_script_name
        self.operation = operation
        self.status = status
        self.timestamp = datetime.utcnow()
        self.details = details
        self.key_code = key_code
    
    @staticmethod
    def create(username, pine_id, pine_script_name, operation, status, details="", key_code=None):
        """Create and store a new access log"""
        log = AccessLog(username, pine_id, pine_script_name, operation, status, details, key_code)
        access_logs.append(log)
        return log
    
    @staticmethod
    def get_by_key(key_code):
        """Get access logs for a specific key"""
        return [log for log in access_logs if log.key_code == key_code]
    
    @staticmethod
    def count_successful_grants():
        """Count successful grant operations"""
        return sum(1 for log in access_logs if log.operation == 'grant' and log.status == 'success')

class PineScript:
    """In-memory Pine Script storage"""
    
    def __init__(self, pine_id, name, description="", is_active=True):
        self.pine_id = pine_id
        self.name = name
        self.description = description
        self.is_active = is_active
        self.created_at = datetime.utcnow()
    
    @staticmethod
    def create(pine_id, name, description="", is_active=True):
        """Create and store a new Pine Script"""
        script = PineScript(pine_id, name, description, is_active)
        pine_scripts[pine_id] = script
        return script
    
    @staticmethod
    def get(pine_id):
        """Get Pine Script by ID"""
        return pine_scripts.get(pine_id)
    
    @staticmethod
    def get_all():
        """Get all Pine Scripts"""
        return list(pine_scripts.values())
    
    @staticmethod
    def get_active():
        """Get active Pine Scripts"""
        return [script for script in pine_scripts.values() if script.is_active]
    
    @staticmethod
    def delete(pine_id):
        """Delete Pine Script"""
        if pine_id in pine_scripts:
            del pine_scripts[pine_id]
            return True
        return False
    
    @staticmethod
    def count():
        """Count total Pine Scripts"""
        return len(pine_scripts)

# Initialize default Pine Scripts
def initialize_default_scripts():
    """Add default Pine Scripts if none exist"""
    if len(pine_scripts) == 0:
        default_scripts = [
            ("Ultraalgo", "PUB;0c59036edcae4c8684c8e17c01eaf137"),
            ("simplealgo", "PUB;a3690bb3cb3549e7af0378a978f96a43"),
            ("Million moves.", "PUB;53828990c8014de895162ec99f480803"),
            ("luxalgo", "PUB;b73e59a4d74e4d3d9a449ad1187b786b"),
            ("lux Osi Matrix", "PUB;996c8fa1a3d74270b95e24643df04fd5"),
            ("infnity algo", "PUB;bfb44fdc5d234c4f8aa5fd06f1bf56a6"),
            ("Diamond algo", "PUB;504fed266bcf48d8ad1d2c7bbe1927ff"),
            ("Blue signals", "PUB;278e02e275914ad5a5cec9ce0e9d9d22"),
            ("Goatalgo", "PUB;0a056b6e1feb4183abf6e601d4140189"),
            ("xpalgo", "PUB;5e901ec6f78043b4bca09e8c2f911e01"),
            ("NovaAlgo", "PUB;f42a2d8c9ede4bc4b005fb8e56b500cc"),
        ]
        
        for name, pine_id in default_scripts:
            PineScript.create(pine_id, name, f"Default {name} script", True)
