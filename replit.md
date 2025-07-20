# TradingView Access Management System

## Overview

This is a comprehensive Flask-based web application with advanced key-based authentication for managing TradingView Pine Script access. The system features a multi-tiered interface: admin panel for creating and managing access keys, user registration workflow through key validation, and comprehensive access control with one-user-per-account restrictions until full removal.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM and Flask-Login for authentication
- **Database**: PostgreSQL with connection pooling and health checks
- **Authentication**: Key-based access control with Flask-Login session management
- **User Management**: Multi-tiered access system (admin/user roles)
- **Session Management**: Flask sessions with proxy fix for deployment environments
- **Configuration**: Environment-based configuration with dotenv support
- **TradingView Integration**: Real authentication with session management and Pine Script access control

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask
- **CSS Framework**: Bootstrap 5 with dark theme (Replit-themed)
- **JavaScript**: Vanilla JavaScript with Bootstrap components and AJAX for form handling
- **Icons**: Font Awesome for UI icons
- **User Experience**: Multi-page authentication flow with real-time feedback

## Key Components

### Models (models.py)
- **User**: Core user model with Flask-Login integration, admin flags, and TradingView username tracking
- **AccessKey**: One-time use access keys created by admins for user registration
- **AccessLog**: Tracks all access management operations with timestamps, status, and user attribution
- **PineScript**: Stores Pine Script configurations including ID, name, description, and active status
- **UserAccess**: Junction table tracking which users have access to which Pine Scripts

### Routes (routes.py)
- **Home Route** (`/`): Key entry portal for new users or login link for existing users
- **Key Validation** (`/validate-key`): Validates access keys and initiates registration flow
- **Registration** (`/register`): User account creation after key validation
- **Login/Logout** (`/login`, `/logout`): Standard authentication endpoints
- **Management Route** (`/manage`): User access management interface for granting/removing access
- **Admin Panel** (`/admin`): Comprehensive admin interface for key creation and user management
- **API Endpoints**: RESTful APIs for username validation, Pine Script management, and access control

### TradingView Integration (tradingview.py)
- **TradingViewAPI Class**: Handles authentication and session management with TradingView
- **Session Persistence**: Saves and loads sessions to/from file for efficiency
- **Cookie Management**: Manages TradingView authentication cookies

### Configuration (config.py)
- **Environment Variables**: Manages TradingView credentials and system settings
- **Validation**: Ensures required configuration is present
- **Defaults**: Provides sensible defaults for optional settings

## Data Flow

1. **User Authentication**: System authenticates with TradingView using stored credentials
2. **Session Management**: Sessions are cached locally to avoid repeated authentication
3. **Access Operations**: Users can grant or remove access to Pine Scripts through the web interface
4. **Logging**: All operations are logged to the database for audit purposes
5. **Status Monitoring**: Dashboard provides real-time status of operations and system health

## External Dependencies

### Required Environment Variables
- `TRADINGVIEW_USERNAME`: TradingView account username
- `TRADINGVIEW_PASSWORD`: TradingView account password
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)
- `SESSION_SECRET`: Flask session secret key (optional, has development default)

### Optional Configuration
- `SESSION_TIMEOUT`: Session timeout in seconds (default: 3600)
- `DEFAULT_PINE_IDS`: Comma-separated list of default Pine Script IDs
- `LOG_LEVEL`: Logging level (default: INFO)

### Third-Party Services
- **TradingView**: Primary integration for managing Pine Script access
- **Bootstrap CDN**: For UI styling and components
- **Font Awesome CDN**: For icons

## Deployment Strategy

### Local Development
- Runs on Flask development server (port 5000)
- Uses SQLite database for simplicity
- Debug mode enabled for development

### Production Considerations
- ProxyFix middleware configured for reverse proxy deployments
- Database connection pooling with health checks
- Environment-based configuration for security
- Session file persistence for TradingView authentication

### Database Strategy
- SQLAlchemy with declarative base for easy model management
- Database tables created automatically on application startup
- Connection pooling and health checks configured for reliability

### Security Features
- Environment-based secrets management
- Session security with configurable secret keys
- Input validation for user data
- Audit logging for all access operations

## Key Design Decisions

### Database Choice
- **Problem**: Need persistent storage for logs and Pine Script configurations
- **Solution**: SQLAlchemy with SQLite default, PostgreSQL support via environment variables
- **Rationale**: SQLite for development simplicity, easy migration to PostgreSQL for production

### Session Management
- **Problem**: Avoid repeated TradingView authentication for efficiency
- **Solution**: File-based session persistence with cookie management
- **Rationale**: Reduces API calls and improves user experience

### Configuration Management
- **Problem**: Secure handling of TradingView credentials
- **Solution**: Environment variable configuration with validation
- **Rationale**: Follows 12-factor app principles for configuration management

### UI Framework
- **Problem**: Need responsive, professional interface
- **Solution**: Bootstrap 5 with dark theme and Font Awesome icons
- **Rationale**: Rapid development with consistent, modern UI components

### Pine Script Management
- **Problem**: Deactivated Pine Scripts caused re-adding issues
- **Solution**: Complete removal from backend when turned off instead of soft deletion
- **Rationale**: Prevents database conflicts and allows clean re-addition of scripts
- **Date**: July 20, 2025

### Real TradingView API Integration
- **Problem**: Demo mode was not performing actual access management
- **Solution**: Implemented real TradingView API endpoints (username_hint, pine_perm/add, pine_perm/list_users, pine_perm/remove)
- **Rationale**: Provides genuine Pine Script access control with proper authentication
- **Date**: July 20, 2025