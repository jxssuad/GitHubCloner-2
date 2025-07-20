import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for TradingView Access Management"""
    
    # TradingView credentials
    TRADINGVIEW_USERNAME = os.getenv("TRADINGVIEW_USERNAME", "")
    TRADINGVIEW_PASSWORD = os.getenv("TRADINGVIEW_PASSWORD", "")
    
    # Session configuration
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour default
    
    # API configuration
    TRADINGVIEW_BASE_URL = "https://www.tradingview.com"
    
    # Default Pine IDs (can be configured via environment)
    DEFAULT_PINE_IDS = os.getenv("DEFAULT_PINE_IDS", "").split(",") if os.getenv("DEFAULT_PINE_IDS") else []
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.TRADINGVIEW_USERNAME or not Config.TRADINGVIEW_PASSWORD:
            raise ValueError("TRADINGVIEW_USERNAME and TRADINGVIEW_PASSWORD must be set in environment variables")
        return True
