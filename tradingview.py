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
            # First, get the login page to get CSRF token
            login_page = self.session.get(f"{self.base_url}/accounts/signin/")
            if login_page.status_code != 200:
                logger.error("Failed to access login page")
                return False

            # Extract CSRF token from the login page
            csrf_patterns = [
                r'name="authenticity_token"[^>]*value="([^"]+)"',
                r'"csrf_token":"([^"]+)"',
                r'window\._csrf = "([^"]+)"',
                r'csrf_token["\']:\s*["\']([^"\']+)["\']'
            ]

            for pattern in csrf_patterns:
                csrf_match = re.search(pattern, login_page.text)
                if csrf_match:
                    self.csrf_token = csrf_match.group(1)
                    logger.debug(f"Found CSRF token with pattern: {pattern[:20]}...")
                    break

            if not self.csrf_token:
                logger.warning("Could not find CSRF token")

            # Prepare login data
            login_data = {
                'username': self.username,
                'password': self.password,
                'remember': 'on',
                'return_to': '/'
            }

            if self.csrf_token:
                login_data['authenticity_token'] = self.csrf_token

            # Set headers for login
            login_headers = {
                'Referer': f"{self.base_url}/accounts/signin/",
                'Origin': self.base_url,
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            # Attempt login
            response = self.session.post(
                f"{self.base_url}/accounts/signin/",
                data=login_data,
                headers=login_headers,
                allow_redirects=False  # Don't follow redirects to see the response
            )

            logger.debug(f"Login response status: {response.status_code}")
            logger.debug(f"Login response headers: {dict(response.headers)}")

            # Check if login was successful (usually a redirect or JSON response)
            if response.status_code in [302, 303, 200]:
                # Follow the redirect or check for success indicators
                if response.status_code in [302, 303]:
                    redirect_url = response.headers.get('Location', '/')
                    if '/accounts/signin' not in redirect_url:
                        logger.info("Authentication successful - redirected to main site")
                        self._save_session()
                        return True
                elif response.status_code == 200:
                    # Check for JSON response with user data (indicates successful login)
                    try:
                        json_data = response.json()
                        if 'user' in json_data and json_data['user'].get('username'):
                            logger.info(f"Authentication successful - logged in as {json_data['user']['username']}")
                            self._save_session()
                            return True
                        elif json_data.get('error'):
                            logger.error(f"Authentication failed - {json_data['error']}")
                            return False
                    except json.JSONDecodeError:
                        # Not JSON, check HTML content for success indicators
                        if 'error' not in response.text.lower() and \
                           ('dashboard' in response.text.lower() or 'chart' in response.text.lower()):
                            logger.info("Authentication successful - logged in")
                            self._save_session()
                            return True

            logger.error("Authentication failed - login unsuccessful")
            logger.debug(f"Response content snippet: {response.text[:500]}")
            return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def validate_username(self, username):
        """Validate if a TradingView username exists using real TradingView API"""
        try:
            if not self._ensure_authenticated():
                return {"validuser": False, "verifiedUserName": ""}

            # Use TradingView's username hint API for accurate validation
            hint_url = f"{self.base_url}/username_hint/?s={username}"
            response = self.session.get(hint_url)

            if response.status_code == 200:
                users_list = response.json()
                valid_user = False
                verified_name = ''

                for user in users_list:
                    if user['username'].lower() == username.lower():
                        valid_user = True
                        verified_name = user['username']
                        logger.info(f"Username validation successful: {verified_name}")
                        return {"validuser": True, "verifiedUserName": verified_name}

                logger.warning(f"Username validation failed for: {username}")
                return {"validuser": False, "verifiedUserName": ""}
            else:
                logger.error(f"Username hint API returned status: {response.status_code}")
                return {"validuser": False, "verifiedUserName": ""}

        except Exception as e:
            logger.error(f"Username validation error: {e}")
            return {"validuser": False, "verifiedUserName": ""}

    def get_user_access(self, username, pine_ids):
        """Get current access status for user and pine scripts using real TradingView API"""
        try:
            if not self._ensure_authenticated():
                return []

            results = []
            for pine_id in pine_ids:
                # Use TradingView's list_users API to check access
                list_users_url = f"{self.base_url}/pine_perm/list_users/?limit=10&order_by=-created"

                from urllib3 import encode_multipart_formdata
                payload = {
                    'pine_id': pine_id,
                    'username': username
                }

                body, content_type = encode_multipart_formdata(payload)

                headers = {
                    'Origin': self.base_url,
                    'Content-Type': content_type,
                    'Cookie': f'sessionid={self._get_session_id()}',
                    'Referer': f"{self.base_url}/"
                }

                response = self.session.post(
                    list_users_url,
                    data=body,
                    headers=headers
                )

                access_details = {
                    "pine_id": pine_id,
                    "username": username,
                    "hasAccess": False,
                    "noExpiration": False,
                    "currentExpiration": datetime.now().isoformat()
                }

                if response.status_code == 200:
                    try:
                        data = response.json()
                        users = data.get('results', [])

                        for user in users:
                            if user['username'].lower() == username.lower():
                                access_details['hasAccess'] = True
                                str_expiration = user.get("expiration")
                                if str_expiration is not None:
                                    access_details['currentExpiration'] = user['expiration']
                                    access_details['noExpiration'] = False
                                else:
                                    access_details['noExpiration'] = True
                                break

                    except Exception as e:
                        logger.error(f"Error parsing access data for {pine_id}: {e}")

                results.append(access_details)

            return results

        except Exception as e:
            logger.error(f"Get access error: {e}")
            return []

    def grant_access(self, username, pine_ids, duration="1L"):
        """Grant access to user for specified pine scripts"""
        try:
            if not self._ensure_authenticated():
                return []

            logger.info(f"Attempting to grant access for {username} to {len(pine_ids)} scripts")

            results = []
            for pine_id in pine_ids:
                logger.info(f"Processing grant access for {username} to {pine_id}")

                # Use real TradingView Pine permission API endpoints
                add_access_url = f"{self.base_url}/pine_perm/add/"

                # Prepare multipart form data as required by TradingView
                from urllib3 import encode_multipart_formdata

                payload = {
                    'pine_id': pine_id,
                    'username_recip': username
                }

                # Add expiration if not lifetime
                if duration != "1L":
                    # Convert duration to expiration date
                    expiration_date = self._calculate_expiration(duration)
                    if expiration_date:
                        payload['expiration'] = expiration_date

                body, content_type = encode_multipart_formdata(payload)

                headers = {
                    'Origin': self.base_url,
                    'Content-Type': content_type,
                    'Cookie': f'sessionid={self._get_session_id()}',
                    'Referer': f"{self.base_url}/"
                }

                response = self.session.post(
                    add_access_url,
                    data=body,
                    headers=headers
                )

                logger.debug(f"Grant access API response: {response.status_code}")

                access_result = {
                    "pine_id": pine_id,
                    "username": username,
                    "hasAccess": False,
                    "noExpiration": duration == "1L",
                    "currentExpiration": datetime.now().isoformat(),
                    "expiration": (datetime.now() + timedelta(days=365)).isoformat(),
                    "status": "Failed"
                }

                # HTTP 200 (OK) and 201 (Created) both indicate success
                if response.status_code in [200, 201]:
                    access_result.update({
                        "hasAccess": True,
                        "status": "Success"
                    })
                    logger.info(f"Successfully granted access for {username} to {pine_id}")
                else:
                    access_result["status"] = f"Failed: HTTP {response.status_code}"
                    logger.error(f"Grant access failed with status {response.status_code}")

                results.append(access_result)
                time.sleep(0.1)  # Small delay between requests

            return results

        except Exception as e:
            logger.error(f"Grant access error: {e}")
            return []

    def remove_access(self, username, pine_ids):
        """Remove access from user for specified pine scripts using real TradingView API"""
        try:
            if not self._ensure_authenticated():
                return []

            results = []
            for pine_id in pine_ids:
                # Use TradingView's remove access API
                remove_url = f"{self.base_url}/pine_perm/remove/"

                from urllib3 import encode_multipart_formdata
                payload = {
                    'pine_id': pine_id,
                    'username_recip': username
                }

                body, content_type = encode_multipart_formdata(payload)

                headers = {
                    'Origin': self.base_url,
                    'Content-Type': content_type,
                    'Cookie': f'sessionid={self._get_session_id()}',
                    'Referer': f"{self.base_url}/"
                }

                response = self.session.post(
                    remove_url,
                    data=body,
                    headers=headers
                )

                access_result = {
                    "pine_id": pine_id,
                    "username": username,
                    "hasAccess": True,  # Assume had access before removal
                    "noExpiration": False,
                    "currentExpiration": datetime.now().isoformat(),
                    "status": "Success" if response.status_code == 200 else f"Failed: HTTP {response.status_code}"
                }

                if response.status_code == 200:
                    access_result["hasAccess"] = False  # Access removed successfully
                    logger.info(f"Successfully removed access for {username} from {pine_id}")
                else:
                    logger.error(f"Failed to remove access for {username} from {pine_id}: {response.status_code}")

                results.append(access_result)
                time.sleep(0.2)  # Rate limiting

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

    def _get_fresh_csrf_token(self):
        """Get a fresh CSRF token from the current session"""
        try:
            # Get CSRF token from chart page
            response = self.session.get(f"{self.base_url}/chart/")
            if response.status_code == 200:
                csrf_patterns = [
                    r'window\.__csrfToken\s*=\s*["\']([^"\']+)["\']',
                    r'csrfToken["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'csrf_token["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'authenticity_token["\']?\s*["\']([^"\']+)["\']'
                ]

                for pattern in csrf_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        self.csrf_token = match.group(1)
                        logger.debug("Fresh CSRF token extracted")
                        return self.csrf_token

                # Also check cookies for CSRF token
                for cookie in self.session.cookies:
                    if 'csrf' in cookie.name.lower():
                        self.csrf_token = cookie.value
                        logger.debug(f"CSRF token found in cookie: {cookie.name}")
                        return self.csrf_token

        except Exception as e:
            logger.debug(f"Error getting fresh CSRF token: {e}")

        return None

    def _get_session_id(self):
        """Get session ID from cookies"""
        for cookie in self.session.cookies:
            if cookie.name == 'sessionid':
                return cookie.value
        return None

    def _calculate_expiration(self, duration):
        """Calculate expiration date from duration string (e.g., '7D', '2M', '1L')"""
        try:
            if duration == "1L":
                return None  # Lifetime access

            from datetime import datetime, timedelta

            if duration.endswith('D'):
                days = int(duration[:-1])
                expiration = datetime.now() + timedelta(days=days)
            elif duration.endswith('M'):
                months = int(duration[:-1])
                expiration = datetime.now() + timedelta(days=months * 30)
            elif duration.endswith('Y'):
                years = int(duration[:-1])
                expiration = datetime.now() + timedelta(days=years * 365)
            else:
                # Default to 30 days if format not recognized
                expiration = datetime.now() + timedelta(days=30)

            return expiration.strftime('%Y-%m-%d %H:%M:%S')

        except Exception as e:
            logger.error(f"Error calculating expiration: {e}")
            return None

    def get_script_users(self, pine_id):
        """Get all usernames that have access to a specific Pine Script with pagination"""
        try:
            if not self._ensure_authenticated():
                return []

            all_users = []
            offset = 0
            limit = 100  # Fetch in batches of 100
            
            while True:
                # Use TradingView's list_users API to get users with pagination
                list_users_url = f"{self.base_url}/pine_perm/list_users/"

                from urllib3 import encode_multipart_formdata
                payload = {
                    'pine_id': pine_id,
                    'limit': limit,
                    'offset': offset,
                    'order_by': '-created'
                }

                body, content_type = encode_multipart_formdata(payload)

                headers = {
                    'Origin': self.base_url,
                    'Content-Type': content_type,
                    'Cookie': f'sessionid={self._get_session_id()}',
                    'Referer': f"{self.base_url}/"
                }

                response = self.session.post(
                    list_users_url,
                    data=body,
                    headers=headers
                )

                if response.status_code == 200:
                    try:
                        data = response.json()
                        users = data.get('results', [])
                        
                        # No more users to fetch
                        if not users:
                            break
                            
                        # Add users from this batch
                        for user in users:
                            user_info = {
                                'username': user.get('username', ''),
                                'expiration': user.get('expiration'),
                                'created': user.get('created'),
                                'has_lifetime_access': user.get('expiration') is None
                            }
                            all_users.append(user_info)

                        # If we got fewer results than the limit, we've reached the end
                        if len(users) < limit:
                            break
                            
                        # Move to next batch
                        offset += limit
                        logger.debug(f"Fetched {len(users)} users (batch {offset//limit}), total so far: {len(all_users)}")
                        
                        # Add small delay between requests to avoid rate limiting
                        time.sleep(0.1)

                    except Exception as e:
                        logger.error(f"Error parsing users data for {pine_id}: {e}")
                        break
                else:
                    logger.error(f"API request failed with status {response.status_code}")
                    break

            logger.info(f"Found {len(all_users)} total users with access to {pine_id}")
            return all_users

        except Exception as e:
            logger.error(f"Error getting script users: {e}")
            return []

    def add_pine_permission(self, username, pine_id):
        """Add Pine Script permission for a user"""
        try:
            if not self._ensure_authenticated():
                return {"success": False, "message": "Authentication failed"}

            logger.info(f"Attempting to grant access for {username} to {pine_id}")

            # Use real TradingView Pine permission API endpoints
            add_access_url = f"{self.base_url}/pine_perm/add/"

            # Prepare multipart form data as required by TradingView
            from urllib3 import encode_multipart_formdata

            payload = {
                'pine_id': pine_id,
                'username_recip': username
            }

            body, content_type = encode_multipart_formdata(payload)

            headers = {
                'Origin': self.base_url,
                'Content-Type': content_type,
                'Cookie': f'sessionid={self._get_session_id()}',
                'Referer': f"{self.base_url}/"
            }

            response = self.session.post(
                add_access_url,
                data=body,
                headers=headers
            )

            logger.debug(f"Grant access API response: {response.status_code}")

            # HTTP 200 (OK) and 201 (Created) both indicate success
            if response.status_code in [200, 201]:
                logger.info(f"Successfully granted access for {username} to {pine_id}")
                return {"success": True, "message": "Access granted successfully"}
            else:
                logger.error(f"Grant access failed with status {response.status_code}")
                return {"success": False, "message": f"Failed: HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Grant access error: {e}")
            return {"success": False, "message": str(e)}

    def remove_pine_permission(self, username, pine_id):
        """Remove Pine Script permission for a user"""
        try:
            if not self._ensure_authenticated():
                return {"success": False, "message": "Authentication failed"}

            # Use TradingView's remove access API
            remove_url = f"{self.base_url}/pine_perm/remove/"

            from urllib3 import encode_multipart_formdata
            payload = {
                'pine_id': pine_id,
                'username_recip': username
            }

            body, content_type = encode_multipart_formdata(payload)

            headers = {
                'Origin': self.base_url,
                'Content-Type': content_type,
                'Cookie': f'sessionid={self._get_session_id()}',
                'Referer': f"{self.base_url}/"
            }

            response = self.session.post(
                remove_url,
                data=body,
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"Successfully removed access for {username} from {pine_id}")
                return {"success": True, "message": "Access removed successfully"}
            else:
                logger.error(f"Failed to remove access for {username} from {pine_id}: {response.status_code}")
                return {"success": False, "message": f"Failed: HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Remove access error: {e}")
            return {"success": False, "message": str(e)}

# Global API instance
tv_api = TradingViewAPI()