from flask import render_template, request, jsonify, session, redirect, url_for
from app import app
from models import AccessLog, PineScript, AccessKey, initialize_default_scripts
from tradingview import TradingViewAPI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize TradingView API
tv_api = TradingViewAPI()

# ===== ADMIN ROUTES =====

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard - key management and monitoring"""
    # Initialize default scripts if needed
    initialize_default_scripts()

    access_keys = AccessKey.get_all()
    scripts = PineScript.get_all()

    # Calculate stats
    total_keys = AccessKey.count()
    used_keys = AccessKey.count_used()
    total_access = AccessLog.count_successful_grants()

    # Sort by creation date (newest first)
    access_keys.sort(key=lambda x: x.created_at, reverse=True)
    scripts.sort(key=lambda x: x.created_at, reverse=True)

    return render_template('admin.html',
                         access_keys=access_keys,
                         scripts=scripts,
                         total_keys=total_keys,
                         used_keys=used_keys,
                         total_access=total_access)

@app.route('/admin/generate-key', methods=['POST'])
def admin_generate_key():
    """Generate a new access key"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        name = data.get('name', '').strip()
        
        if not email or not name:
            return jsonify({"success": False, "error": "Email and name are required"})
        
        key_code = AccessKey.generate_key()
        AccessKey.create(key_code, email, name)

        total_keys = AccessKey.count()

        return jsonify({
            "success": True,
            "key": key_code,
            "email": email,
            "name": name,
            "total_keys": total_keys
        })
    except Exception as e:
        logger.error(f"Error generating key: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/admin/add-script', methods=['POST'])
def admin_add_script():
    """Add a new Pine Script"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        script_id = data.get('script_id', '').strip()
        description = data.get('description', '').strip()

        if not name or not script_id:
            return jsonify({"success": False, "error": "Name and Script ID are required"})

        # Check if script already exists
        if PineScript.get(script_id):
            return jsonify({"success": False, "error": "Script ID already exists"})

        PineScript.create(script_id, name, description, True)

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error adding script: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/admin/remove-script', methods=['POST'])
def admin_remove_script():
    """Remove a Pine Script"""
    try:
        data = request.get_json()
        script_id = data.get('script_id')

        if not PineScript.delete(script_id):
            return jsonify({"success": False, "error": "Script not found"})

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error removing script: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/admin/key-access/<key_code>')
def admin_key_access(key_code):
    """Get access logs for a specific key"""
    try:
        access_key = AccessKey.get(key_code)
        if not access_key:
            return jsonify({"success": False, "error": "Key not found"})

        logs = AccessLog.get_by_key(key_code)

        return jsonify({
            "success": True,
            "access_logs": [
                {
                    "pine_id": log.pine_id,
                    "pine_script_name": log.pine_script_name,
                    "operation": log.operation,
                    "status": log.status,
                    "timestamp": log.timestamp.isoformat(),
                    "details": log.details
                }
                for log in logs
            ]
        })
    except Exception as e:
        logger.error(f"Error getting key access: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/admin/remove-user-access', methods=['POST'])
def admin_remove_user_access():
    """Remove user access to a Pine Script"""
    try:
        data = request.get_json()
        username = data.get('username')
        pine_id = data.get('pine_id')

        if not username or not pine_id:
            return jsonify({"success": False, "error": "Username and Pine ID required"})

        # Remove access via TradingView API
        result = tv_api.remove_pine_permission(username, pine_id)

        # Log the operation
        script = PineScript.get(pine_id)
        script_name = script.name if script else pine_id

        AccessLog.create(
            username=username,
            pine_id=pine_id,
            pine_script_name=script_name,
            operation="remove",
            status="success" if result.get('success', False) else "failure",
            details=result.get('message', 'Admin removal'),
            key_code=None  # Admin action, not tied to a key
        )

        return jsonify({
            "success": result.get('success', False),
            "message": result.get('message', 'Access removal completed')
        })
    except Exception as e:
        logger.error(f"Error removing user access: {e}")
        return jsonify({"success": False, "error": str(e)})

# ===== ACCESS ROUTES =====

@app.route('/access')
def access_page():
    """User access page - key entry and script selection"""
    scripts = PineScript.get_active()
    return render_template('access.html', scripts=scripts)

@app.route('/access/validate-key', methods=['POST'])
def access_validate_key():
    """Validate access key"""
    try:
        data = request.get_json()
        key_code = data.get('key', '').strip().upper()

        if not key_code:
            return jsonify({"success": False, "error": "Access key is required"})

        # Find the key
        access_key = AccessKey.get(key_code)

        if not access_key:
            return jsonify({"success": False, "error": "Invalid access key"})

        if access_key.is_used:
            return jsonify({"success": False, "error": "This access key has already been used"})

        # Mark key as validated in session (but not used yet)
        session['access_key_code'] = access_key.key_code
        session['access_key_used'] = True

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error validating key: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/access/validate-username', methods=['POST'])
def access_validate_username():
    """Validate TradingView username"""
    try:
        if not session.get('access_key_used'):
            return jsonify({"success": False, "error": "Please validate your access key first"})

        data = request.get_json()
        username = data.get('username', '').strip()

        if not username:
            return jsonify({"success": False, "error": "Username is required"})

        # Validate username with TradingView
        result = tv_api.validate_username(username)

        if result.get('validuser', False):
            session['username'] = username
            session['username_valid'] = True
            return jsonify({"success": True, "verified_name": result.get('verifiedUserName', username)})
        else:
            return jsonify({"success": False, "error": "Invalid TradingView username"})

    except Exception as e:
        logger.error(f"Error validating username: {e}")
        return jsonify({"success": False, "error": "Error validating username. Please try again."})

@app.route('/access/grant-access', methods=['POST'])
def access_grant_access():
    """Grant access to selected Pine Scripts"""
    try:
        if not session.get('access_key_used') or not session.get('username_valid'):
            return jsonify({"success": False, "error": "Please validate your key and username first"})

        data = request.get_json()
        selected_scripts = data.get('scripts', [])
        username = session.get('username')
        access_key_code = session.get('access_key_code')

        if not selected_scripts:
            return jsonify({"success": False, "error": "Please select at least one script"})

        # Mark the access key as used
        access_key = AccessKey.get(access_key_code)
        if access_key and not access_key.is_used:
            access_key.is_used = True
            access_key.used_at = datetime.utcnow()
            access_key.used_by_username = username

        results = []
        errors = []

        for script_id in selected_scripts:
            script = PineScript.get(script_id)
            script_name = script.name if script else script_id

            try:
                # Grant access via TradingView API
                result = tv_api.add_pine_permission(username, script_id)

                success = result.get('success', False)
                status = "success" if success else "failure"

                # Log the operation
                AccessLog.create(
                    username=username,
                    pine_id=script_id,
                    pine_script_name=script_name,
                    operation="grant",
                    status=status,
                    details=result.get('message', ''),
                    key_code=access_key_code
                )

                if success:
                    results.append({"script_name": script_name, "success": True})
                else:
                    errors.append({"script_name": script_name, "error": result.get('message', 'Unknown error')})

            except Exception as e:
                logger.error(f"Error granting access to {script_name}: {e}")
                errors.append({"script_name": script_name, "error": str(e)})

        # Clear session after use
        session.pop('access_key_code', None)
        session.pop('access_key_used', None)
        session.pop('username_valid', None)

        return jsonify({
            "success": len(results) > 0,
            "results": results,
            "errors": errors
        })

    except Exception as e:
        logger.error(f"Error granting access: {e}")
        return jsonify({"success": False, "error": str(e)})

# ===== REDIRECT ROUTES =====

@app.route('/')
def index():
    """Redirect to admin dashboard"""
    return redirect(url_for('admin_dashboard'))

@app.route('/manage')
def manage_redirect():
    """Redirect old manage route to admin"""
    return redirect(url_for('admin_dashboard'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return "<h1>404 - Page Not Found</h1>", 404

@app.errorhandler(500)
def internal_error(error):
    return "<h1>500 - Internal Server Error</h1>", 500