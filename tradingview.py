import requests
import json
import logging
import os
import time
import re
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
        self.csrf_token = None
        self.session_hash = None
        self._setup_session()
        self._load_session()
    
    def _setup_session(self):
        """Setup session with proper headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
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
            # Get the main page first to establish session
            main_page = self.session.get(f"{self.base_url}/")
            if main_page.status_code != 200:
                logger.error("Failed to access main page")
                return False
            
            # Extract CSRF token from the page
            csrf_match = re.search(r'"csrf_token":"([^"]+)"', main_page.text)
            if csrf_match:
                self.csrf_token = csrf_match.group(1)
                logger.debug(f"Found CSRF token: {self.csrf_token[:10]}...")
            else:
                logger.warning("Could not find CSRF token")
            
            # Get session hash
            session_match = re.search(r'"session_hash":"([^"]+)"', main_page.text)
            if session_match:
                self.session_hash = session_match.group(1)
                logger.debug(f"Found session hash: {self.session_hash[:10]}...")
            
            # Prepare login data
            login_data = {
                'username': self.username,
                'password': self.password,
                'remember': 'on'
            }
            
            if self.csrf_token:
                login_data['authenticity_token'] = self.csrf_token
            
            # Set additional headers for login
            login_headers = {
                'Referer': f"{self.base_url}/accounts/signin/",
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }
            
            # Attempt login
            response = self.session.post(
                f"{self.base_url}/accounts/signin/",
                data=login_data,
                headers=login_headers,
                allow_redirects=True
            )
            
            # Check if login was successful
            if response.status_code == 200:
                # Check for successful login indicators
                if ('user' in response.text.lower() and 'error' not in response.text.lower()) or \
                   response.url != f"{self.base_url}/accounts/signin/":
                    logger.info("Authentication successful")
                    self._save_session()
                    return True
                else:
                    logger.error("Authentication failed - invalid credentials")
                    return False
            else:
                logger.error(f"Authentication failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def validate_username(self, username):
        """Validate if a TradingView username exists"""
        try:
            if not self._ensure_authenticated():
                return {"validuser": False, "verifiedUserName": ""}
            
            # Use TradingView's internal API for user validation
            api_url = f"{self.base_url}/pine_perm/check_users/"
            
            payload = {
                'usernames': [username]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f"{self.base_url}/"
            }
            
            if self.csrf_token:
                headers['X-CSRFToken'] = self.csrf_token
            
            response = self.session.post(
                api_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and username.lower() in [u.lower() for u in data]:
                    # Find the exact case match
                    verified_name = next((u for u in data if u.lower() == username.lower()), username)
                    return {"validuser": True, "verifiedUserName": verified_name}
            
            return {"validuser": False, "verifiedUserName": ""}
            
        except Exception as e:
            logger.error(f"Username validation error: {e}")
            # Fallback to profile page check
            try:
                response = self.session.get(f"{self.base_url}/u/{username}/")
                if response.status_code == 200 and "Page Not Found" not in response.text:
                    return {"validuser": True, "verifiedUserName": username}
            except:
                pass
            return {"validuser": False, "verifiedUserName": ""}
    
    def get_user_access(self, username, pine_ids):
        """Get current access status for user and pine scripts"""
        try:
            if not self._ensure_authenticated():
                return []
            
            # Use TradingView's internal API to check access
            api_url = f"{self.base_url}/pine_perm/get_user_access/"
            
            payload = {
                'username': username,
                'pine_ids': pine_ids
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f"{self.base_url}/"
            }
            
            if self.csrf_token:
                headers['X-CSRFToken'] = self.csrf_token
            
            response = self.session.post(
                api_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'access_info' in data:
                    return data['access_info']
            
            # If API call fails, return default structure
            results = []
            for pine_id in pine_ids:
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
    
    def grant_access(self, username, pine_ids, duration="1L"):
        """Grant access to user for specified pine scripts"""
        try:
            if not self._ensure_authenticated():
                return []
            
            # Use TradingView's internal API to grant access
            api_url = f"{self.base_url}/pine_perm/add_expiration/"
            
            results = []
            for pine_id in pine_ids:
                payload = {
                    'username': username,
                    'pine_id': pine_id,
                    'expiration': duration  # 1L = lifetime, 7D = 7 days, 1M = 1 month
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f"{self.base_url}/"
                }
                
                if self.csrf_token:
                    headers['X-CSRFToken'] = self.csrf_token
                
                response = self.session.post(
                    api_url,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('success', False):
                            access_result = {
                                "pine_id": pine_id,
                                "username": username,
                                "hasAccess": True,
                                "noExpiration": duration == "1L",
                                "currentExpiration": data.get('expiration', (datetime.now() + timedelta(days=365)).isoformat()),
                                "expiration": data.get('expiration', (datetime.now() + timedelta(days=365)).isoformat()),
                                "status": "Success"
                            }
                        else:
                            access_result = {
                                "pine_id": pine_id,
                                "username": username,
                                "hasAccess": False,
                                "noExpiration": False,
                                "currentExpiration": datetime.now().isoformat(),
                                "expiration": datetime.now().isoformat(),
                                "status": data.get('error', 'Failed')
                            }
                    except json.JSONDecodeError:
                        # Handle non-JSON response
                        access_result = {
                            "pine_id": pine_id,
                            "username": username,
                            "hasAccess": True,
                            "noExpiration": duration == "1L",
                            "currentExpiration": (datetime.now() + timedelta(days=365)).isoformat(),
                            "expiration": (datetime.now() + timedelta(days=365)).isoformat(),
                            "status": "Success"
                        }
                else:
                    access_result = {
                        "pine_id": pine_id,
                        "username": username,
                        "hasAccess": False,
                        "noExpiration": False,
                        "currentExpiration": datetime.now().isoformat(),
                        "expiration": datetime.now().isoformat(),
                        "status": f"HTTP {response.status_code}"
                    }
                
                results.append(access_result)
                time.sleep(0.5)  # Rate limiting
            
            return results
            
        except Exception as e:
            logger.error(f"Grant access error: {e}")
            return []
    
    def remove_access(self, username, pine_ids):
        """Remove access from user for specified pine scripts"""
        try:
            if not self._ensure_authenticated():
                return []
            
            # Use TradingView's internal API to remove access
            api_url = f"{self.base_url}/pine_perm/delete_expiration/"
            
            results = []
            for pine_id in pine_ids:
                payload = {
                    'username': username,
                    'pine_id': pine_id
                }
                
                headers = {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f"{self.base_url}/"
                }
                
                if self.csrf_token:
                    headers['X-CSRFToken'] = self.csrf_token
                
                response = self.session.post(
                    api_url,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('success', False):
                            access_result = {
                                "pine_id": pine_id,
                                "username": username,
                                "hasAccess": False,
                                "noExpiration": False,
                                "currentExpiration": datetime.now().isoformat(),
                                "status": "Success"
                            }
                        else:
                            access_result = {
                                "pine_id": pine_id,
                                "username": username,
                                "hasAccess": True,
                                "noExpiration": False,
                                "currentExpiration": datetime.now().isoformat(),
                                "status": data.get('error', 'Failed')
                            }
                    except json.JSONDecodeError:
                        # Handle non-JSON response
                        access_result = {
                            "pine_id": pine_id,
                            "username": username,
                            "hasAccess": False,
                            "noExpiration": False,
                            "currentExpiration": datetime.now().isoformat(),
                            "status": "Success"
                        }
                else:
                    access_result = {
                        "pine_id": pine_id,
                        "username": username,
                        "hasAccess": True,
                        "noExpiration": False,
                        "currentExpiration": datetime.now().isoformat(),
                        "status": f"HTTP {response.status_code}"
                    }
                
                results.append(access_result)
                time.sleep(0.5)  # Rate limiting
            
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
