# TradingView Access Management System

## Overview

This is a Flask-based web application designed to manage user access to TradingView Pine Scripts. The system provides a web interface for granting, removing, and monitoring access to specific Pine Scripts for TradingView users. It includes logging capabilities, session management, and a clean Bootstrap-based UI.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM
- **Database**: SQLite by default with configurable database support via environment variables
- **Session Management**: Flask sessions with proxy fix for deployment environments
- **Configuration**: Environment-based configuration with dotenv support
- **TradingView Integration**: Real authentication with session management and Pine Script access control

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask
- **CSS Framework**: Bootstrap 5 with dark theme
- **JavaScript**: Vanilla JavaScript with Bootstrap components and AJAX for form handling
- **Icons**: Font Awesome for UI icons
- **User Experience**: Non-refreshing interface with real-time feedback

## Key Components

### Models (models.py)
- **AccessKey**: Stores one-time access keys with usage tracking and user relationships
- **AccessLog**: Tracks all access management operations with timestamps, status, and details, linked to access keys
- **PineScript**: Stores Pine Script configurations including ID, name, description, and active status

### Routes (routes.py)
- **Admin Routes** (`/admin`): Administrator dashboard for key management, Pine Script management, and access monitoring
- **Access Routes** (`/access`): User interface for key validation, username entry, and Pine Script access
- **API Routes**: Key validation, username validation, access granting, and administrative operations

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
- `DATABASE_URL`: Database connection string (auto-configured on Render)
- `SESSION_SECRET`: Flask session secret key (auto-generated on Render)
- `PORT`: Application port (auto-set by Render)

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
- Render-optimized deployment with PostgreSQL support
- Comprehensive deployment documentation and quick setup guides

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

### Enhanced Premium User Interface
- **Problem**: Basic success page needed premium feel and better user management
- **Solution**: Added premium status card, remaining scripts management, and user session persistence
- **Features**: Crown icons, active status badges, access date tracking, additional script grants without username changes
- **Date**: July 20, 2025

### Render Deployment Optimization
- **Problem**: App needed production-ready deployment configuration
- **Solution**: Added comprehensive Render deployment files and database URL handling
- **Files**: render.yaml, Procfile, runtime.txt, .env.example, DEPLOYMENT.md, RENDER_SETUP.md
- **Features**: PostgreSQL support, environment-based secrets, production configurations
- **Date**: July 20, 2025

### Complete Architecture Separation with Key-Based Authentication
- **Problem**: User requested complete separation of admin and user interfaces with key-based access control
- **Solution**: Restructured entire application with /admin dashboard and /access user page, implemented one-time key system
- **Features**: 
  - /admin dashboard for administrators with key generation, script management, and access monitoring
  - /access page for users with key validation and script selection
  - One-time access keys that can only be used once
  - Manage functionality for each key to view and remove granted access
  - Default Pine Scripts auto-loaded (11 popular scripts including Ultraalgo, luxalgo, etc.)
- **Database Changes**: Added AccessKey model with relationships to AccessLog
- **UI Changes**: Completely new admin.html and access.html templates with premium styling
- **Date**: July 20, 2025