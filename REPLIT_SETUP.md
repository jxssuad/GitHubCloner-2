
# Replit Setup Guide - No Database Version

## Quick Setup (3 steps)

### 1. Set Your Secrets
1. Click on "Secrets" tab in Replit (lock icon on left sidebar)
2. Add these two secrets:
   - Key: `TRADINGVIEW_USERNAME`, Value: your TradingView username
   - Key: `TRADINGVIEW_PASSWORD`, Value: your TradingView password

### 2. Run the Application
1. Click the "Run" button
2. The app will automatically:
   - Load default Pine Scripts in memory
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

- ✅ No database required - all data stored in memory
- ✅ Built-in Pine Scripts (Ultraalgo, luxalgo, etc.)
- ✅ One-time access keys
- ✅ Admin monitoring dashboard
- ✅ User-friendly access interface

## Data Storage

- Uses in-memory storage (data resets when app restarts)
- No database files or external services needed
- Perfect for temporary access management
- All data stored in Python variables

## Security

- TradingView credentials stored securely in Replit Secrets
- Session keys auto-generated
- One-time access keys prevent reuse
- Admin and user interfaces separated

## Troubleshooting

**Can't validate username?**
- Check your TRADINGVIEW_USERNAME and TRADINGVIEW_PASSWORD in Secrets
- Make sure they match your actual TradingView login

**App won't start?**
- Check the console for error messages
- Ensure Secrets are set correctly
- Try clicking Run again

**Data disappeared?**
- This is normal - data is stored in memory and resets when the app restarts
- Generate new access keys as needed
