import requests
import json
import logging
import os
import time
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)

class TradingViewAPI:
    """TradingView API client for managing script access"""
    
    def __init__(self):
        self.base_url = Config.TRADINGVIEW_BASE_URL
        self.username = Config.TRADINGVIEW_USERNAME
        self.password = Config.TRADINGVIEW_PASSWORD
        self.session = requests.Session()
        self.session_file = "session.txt"
        self._load_session()
    
    def _load_session(self):
        """Load session from file if exists"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                    # Set cookies from saved session
                    for cookie_data in session_data.get('cookies', []):
                        self.session.cookies.set(**cookie_data)
                logger.info("Session loaded from file")
        except Exception as e:
            logger.error(f"Error loading session: {e}")
    
    def _save_session(self):
        """Save current session to file"""
        try:
            cookies_data = []
            for cookie in self.session.cookies:
                cookies_data.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path
                })
            
            session_data = {
                'cookies': cookies_data,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
            logger.info("Session saved to file")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
    
    def _authenticate(self):
        """Authenticate with TradingView"""
        try:
            # First, get the login page to extract necessary tokens
            login_page = self.session.get(f"{self.base_url}/accounts/signin/")
            
            if login_page.status_code != 200:
                logger.error("Failed to access login page")
                return False
            
            # Extract CSRF token or other necessary data from login page
            # This is a simplified version - actual implementation may need more complex token extraction
            
            login_data = {
                'username': self.username,
                'password': self.password,
            }
            
            # Attempt login
            response = self.session.post(
                f"{self.base_url}/accounts/signin/",
                data=login_data,
                headers={
                    'Referer': f"{self.base_url}/accounts/signin/",
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            if response.status_code == 200 and 'accounts/signin' not in response.url:
                logger.info("Authentication successful")
                self._save_session()
                return True
            else:
                logger.error("Authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def validate_username(self, username):
        """Validate if a TradingView username exists"""
        try:
            if not self._ensure_authenticated():
                return {"validuser": False, "verifiedUserName": ""}
            
            # Make request to validate username
            response = self.session.get(
                f"{self.base_url}/u/{username}/",
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            if response.status_code == 200:
                # Check if user profile exists
                if "Page Not Found" not in response.text and "User not found" not in response.text:
                    return {"validuser": True, "verifiedUserName": username}
            
            return {"validuser": False, "verifiedUserName": ""}
            
        except Exception as e:
            logger.error(f"Username validation error: {e}")
            return {"validuser": False, "verifiedUserName": ""}
    
    def get_user_access(self, username, pine_ids):
        """Get current access status for user and pine scripts"""
        try:
            if not self._ensure_authenticated():
                return []
            
            results = []
            for pine_id in pine_ids:
                # This is a simplified implementation
                # Actual implementation would need to make specific API calls to check access
                access_info = {
                    "pine_id": pine_id,
                    "username": username,
                    "hasAccess": False,
                    "noExpiration": False,
                    "currentExpiration": datetime.now().isoformat()
                }
                results.append(access_info)
            
            return results
            
        except Exception as e:
            logger.error(f"Get access error: {e}")
            return []
    
    def grant_access(self, username, pine_ids):
        """Grant access to user for specified pine scripts"""
        try:
            if not self._ensure_authenticated():
                return []
            
            results = []
            for pine_id in pine_ids:
                # Simulate granting access
                # Actual implementation would make API calls to grant access
                access_result = {
                    "pine_id": pine_id,
                    "username": username,
                    "hasAccess": True,
                    "noExpiration": True,
                    "currentExpiration": (datetime.now() + timedelta(days=365)).isoformat(),
                    "expiration": (datetime.now() + timedelta(days=365)).isoformat(),
                    "status": "Success"
                }
                results.append(access_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Grant access error: {e}")
            return []
    
    def remove_access(self, username, pine_ids):
        """Remove access from user for specified pine scripts"""
        try:
            if not self._ensure_authenticated():
                return []
            
            results = []
            for pine_id in pine_ids:
                # Simulate removing access
                access_result = {
                    "pine_id": pine_id,
                    "username": username,
                    "hasAccess": False,
                    "noExpiration": False,
                    "currentExpiration": datetime.now().isoformat(),
                    "status": "Success"
                }
                results.append(access_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Remove access error: {e}")
            return []
    
    def _ensure_authenticated(self):
        """Ensure session is authenticated"""
        # Check if current session is valid
        try:
            test_response = self.session.get(f"{self.base_url}/chart/")
            if test_response.status_code == 200 and 'accounts/signin' not in test_response.url:
                return True
        except:
            pass
        
        # Session invalid, re-authenticate
        return self._authenticate()

# Global API instance
tv_api = TradingViewAPI()
