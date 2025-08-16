from datetime import datetime
import secrets
import string

# In-memory storage for the application
access_logs = []
pine_scripts = {}

class AccessLog:
    """In-memory access log storage"""

    def __init__(self, username, pine_id, pine_script_name, operation, status, details=""):
        self.username = username
        self.pine_id = pine_id
        self.pine_script_name = pine_script_name
        self.operation = operation
        self.status = status
        self.timestamp = datetime.utcnow()
        self.details = details

    @staticmethod
    def create(username, pine_id, pine_script_name, operation, status, details=""):
        """Create and store a new access log"""
        log = AccessLog(username, pine_id, pine_script_name, operation, status, details)
        access_logs.append(log)
        return log

    @staticmethod
    def get_all():
        """Get all access logs"""
        return access_logs

    @staticmethod
    def count_successful_grants():
        """Count successful grant operations"""
        return sum(1 for log in access_logs if log.operation == 'grant' and log.status == 'success')

class PineScript:
    """In-memory Pine Script storage"""

    def __init__(self, pine_id, name, description="", is_active=True, is_visible_to_agent=True):
        self.pine_id = pine_id
        self.name = name
        self.description = description
        self.is_active = is_active
        self.is_visible_to_agent = is_visible_to_agent
        self.created_at = datetime.utcnow()

    @staticmethod
    def create(pine_id, name, description="", is_active=True, is_visible_to_agent=True):
        """Create and store a new Pine Script"""
        script = PineScript(pine_id, name, description, is_active, is_visible_to_agent)
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
    def get_agent_visible():
        """Get scripts visible to agents"""
        return [script for script in pine_scripts.values() if script.is_active and script.is_visible_to_agent]

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

    @staticmethod
    def get_usernames(pine_id):
        """Get all usernames that have accessed a specific script"""
        return list(set(log.username for log in access_logs if log.pine_id == pine_id))

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
            ("PrimeAlgo", "PUB;933c9921bf5845bb844b3e09f371b271"),
            ("Prime OB", "PUB;19ad042efef94ad681fbc27812a15b92"),
            ("Prime OSI", "PUB;78ea5893ce664b64b15aa737eba353f9"),
            ("SMRTAlgo", "PUB;cd52ab53c0154f3da9f66de7d1709f29"),
            ("PRO V6", "PUB;cd88bb06edd74f0d9af1958980d63aad"),
        ]

        for name, pine_id in default_scripts:
            PineScript.create(pine_id, name, f"Default {name} script", True)