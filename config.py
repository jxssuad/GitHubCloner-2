
import os

class Config:
    """Configuration class for TradingView Access Management - No Database Version"""
    
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
    
    # Replit deployment configuration
    PORT = int(os.getenv("PORT", "5000"))
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        if not Config.TRADINGVIEW_USERNAME or not Config.TRADINGVIEW_PASSWORD:
            raise ValueError("TRADINGVIEW_USERNAME and TRADINGVIEW_PASSWORD must be set in Secrets")
        return True
    
    @staticmethod
    def is_production():
        """Check if running in production (Replit)"""
        return os.getenv('REPL_ID') is not None
