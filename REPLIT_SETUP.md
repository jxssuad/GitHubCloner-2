
# Replit Setup Guide

## Quick Setup (3 steps)

### 1. Set Your Secrets
1. Click on "Secrets" tab in Replit (lock icon on left sidebar)
2. Add these two secrets:
   - Key: `TRADINGVIEW_USERNAME`, Value: your TradingView username
   - Key: `TRADINGVIEW_PASSWORD`, Value: your TradingView password

### 2. Run the Application
1. Click the "Run" button
2. The app will automatically:
   - Create SQLite database in `instance/` folder
   - Set up database tables
   - Load default Pine Scripts
   - Start the web server on port 5000

### 3. Access Your App
1. **Admin Dashboard**: `https://your-repl-name.your-username.repl.co/admin`
   - Generate access keys
   - Manage Pine Scripts
   - Monitor user access

2. **User Access**: `https://your-repl-name.your-username.repl.co/access`
   - Users enter access keys
   - Select Pine Scripts
   - Get TradingView access

## Features

- ✅ Simple SQLite database (no external database needed)
- ✅ Automatic database setup
- ✅ Built-in Pine Scripts (Ultraalgo, luxalgo, etc.)
- ✅ One-time access keys
- ✅ Admin monitoring dashboard
- ✅ User-friendly access interface

## Database

- Uses SQLite stored in `instance/tradingview_access.db`
- Automatically created on first run
- All data stored locally in your Repl
- No external database service required

## Security

- TradingView credentials stored securely in Replit Secrets
- Session keys auto-generated
- One-time access keys prevent reuse
- Admin and user interfaces completely separated

## Troubleshooting

**Can't validate username?**
- Check your TRADINGVIEW_USERNAME and TRADINGVIEW_PASSWORD in Secrets
- Make sure they match your actual TradingView login

**Database errors?**
- The `instance/` folder and database are created automatically
- If issues persist, delete the `instance/` folder and restart

**App won't start?**
- Check the console for error messages
- Ensure Secrets are set correctly
- Try clicking Run again
