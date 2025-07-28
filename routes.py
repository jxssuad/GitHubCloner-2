from flask import render_template, request, jsonify, session, redirect, url_for
from app import app
from models import AccessLog, PineScript, initialize_default_scripts
from tradingview import TradingViewAPI
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Initialize TradingView API
tv_api = TradingViewAPI()

# ===== MAIN ROUTES =====

@app.route('/')
def index():
    """Main dashboard - manage Pine Scripts and grant access"""
    # Initialize default scripts if needed
    initialize_default_scripts()

    scripts = PineScript.get_all()
    access_logs = AccessLog.get_all()

    # Calculate stats
    total_scripts = PineScript.count()
    total_access = AccessLog.count_successful_grants()

    # Sort by creation date (newest first)
    scripts.sort(key=lambda x: x.created_at, reverse=True)
    access_logs.sort(key=lambda x: x.timestamp, reverse=True)

    return render_template('admin.html',
                         scripts=scripts,
                         access_logs=access_logs[:20],  # Show last 20 logs
                         total_scripts=total_scripts,
                         total_access=total_access)

@app.route('/api/validate-username', methods=['POST'])
def validate_username():
    """Validate TradingView username"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()

        if not username:
            return jsonify({"success": False, "error": "Username is required"})

        # Validate username with TradingView
        result = tv_api.validate_username(username)

        if result.get('validuser', False):
            return jsonify({"success": True, "verified_name": result.get('verifiedUserName', username)})
        else:
            return jsonify({"success": False, "error": "Invalid TradingView username"})

    except Exception as e:
        logger.error(f"Error validating username: {e}")
        return jsonify({"success": False, "error": "Error validating username. Please try again."})

@app.route('/api/grant-access', methods=['POST'])
def grant_access():
    """Grant access to selected Pine Scripts"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        selected_scripts = data.get('scripts', [])
        duration = data.get('duration', '1L')  # Default to lifetime

        if not username:
            return jsonify({"success": False, "error": "Username is required"})

        if not selected_scripts:
            return jsonify({"success": False, "error": "Please select at least one script"})

        results = []
        errors = []

        for script_id in selected_scripts:
            script = PineScript.get(script_id)
            script_name = script.name if script else script_id

            try:
                # Grant access via TradingView API with duration
                if duration == '1L':
                    result = tv_api.add_pine_permission(username, script_id)
                else:
                    result = tv_api.grant_access(username, [script_id], duration)
                    if isinstance(result, list) and len(result) > 0:
                        result = result[0]
                        result = {
                            'success': result.get('status') == 'Success',
                            'message': result.get('status', 'Unknown')
                        }

                success = result.get('success', False)
                status = "success" if success else "failure"

                # Log the operation
                AccessLog.create(
                    username=username,
                    pine_id=script_id,
                    pine_script_name=script_name,
                    operation="grant",
                    status=status,
                    details=f"Duration: {duration}, {result.get('message', '')}"
                )

                if success:
                    results.append({"script_name": script_name, "success": True, "duration": duration})
                else:
                    errors.append({"script_name": script_name, "error": result.get('message', 'Unknown error')})

            except Exception as e:
                logger.error(f"Error granting access to {script_name}: {e}")
                errors.append({"script_name": script_name, "error": str(e)})

        return jsonify({
            "success": len(results) > 0,
            "results": results,
            "errors": errors
        })

    except Exception as e:
        logger.error(f"Error granting access: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/remove-access', methods=['POST'])
def remove_access():
    """Remove access from user for specified Pine Scripts"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        script_id = data.get('script_id', '').strip()

        if not username or not script_id:
            return jsonify({"success": False, "error": "Username and Script ID required"})

        # Remove access via TradingView API
        result = tv_api.remove_pine_permission(username, script_id)

        # Log the operation
        script = PineScript.get(script_id)
        script_name = script.name if script else script_id

        AccessLog.create(
            username=username,
            pine_id=script_id,
            pine_script_name=script_name,
            operation="remove",
            status="success" if result.get('success', False) else "failure",
            details=result.get('message', 'Admin removal')
        )

        return jsonify({
            "success": result.get('success', False),
            "message": result.get('message', 'Access removal completed')
        })
    except Exception as e:
        logger.error(f"Error removing user access: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/get-script-users/<script_id>')
def get_script_users(script_id):
    """Get all usernames that have access to a specific Pine Script"""
    try:
        # Get users from TradingView API
        users = tv_api.get_script_users(script_id)

        script = PineScript.get(script_id)
        script_name = script.name if script else script_id

        return jsonify({
            "success": True,
            "script_id": script_id,
            "script_name": script_name,
            "users": users
        })
    except Exception as e:
        logger.error(f"Error getting script users: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/add-script', methods=['POST'])
def add_script():
    """Add a new Pine Script"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        script_id = data.get('script_id', '').strip()
        description = data.get('description', '').strip()
        scrape_users = data.get('scrape_users', False)

        if not name or not script_id:
            return jsonify({"success": False, "error": "Name and Script ID are required"})

        # Check if script already exists
        if PineScript.get(script_id):
            return jsonify({"success": False, "error": "Script ID already exists"})

        PineScript.create(script_id, name, description, True)

        response_data = {"success": True, "message": "Script added successfully"}

        # Optionally scrape users if requested
        if scrape_users:
            scrape_result = tv_api.scrape_all_users_from_new_script(script_id)
            if scrape_result.get('success', False):
                response_data['user_data'] = scrape_result['data']
                response_data['message'] = f"Script added successfully. Found {scrape_result['data']['total_users']} existing users."
            else:
                response_data['scrape_error'] = scrape_result.get('error', 'Failed to scrape users')

        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error adding script: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/scrape-script-users/<script_id>', methods=['POST'])
def scrape_script_users(script_id):
    """Scrape all users from a specific script"""
    try:
        # Check if script exists
        script = PineScript.get(script_id)
        if not script:
            return jsonify({"success": False, "error": "Script not found"})

        # Scrape users from the script
        result = tv_api.scrape_all_users_from_new_script(script_id)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "script_name": script.name,
                "user_data": result['data']
            })
        else:
            return jsonify({
                "success": False, 
                "error": result.get('error', 'Failed to scrape users')
            })
            
    except Exception as e:
        logger.error(f"Error scraping users for script {script_id}: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/scrape-all-scripts-users', methods=['POST'])
def scrape_all_scripts_users():
    """Scrape all users from all active scripts"""
    try:
        active_scripts = PineScript.get_active()
        if not active_scripts:
            return jsonify({"success": False, "error": "No active scripts found"})

        pine_ids = [script.pine_id for script in active_scripts]
        
        # Scrape users from all scripts
        result = tv_api.scrape_all_users_from_multiple_scripts(pine_ids)
        
        if result.get('success', False):
            return jsonify({
                "success": True,
                "summary": {
                    "scripts_processed": result['scripts_processed'],
                    "total_users_found": result['total_users_found']
                },
                "detailed_results": result['results']
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to scrape users from scripts')
            })
            
    except Exception as e:
        logger.error(f"Error scraping users from all scripts: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/remove-script', methods=['POST'])
def remove_script():
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

@app.route('/api/bulk-remove-access', methods=['POST'])
def bulk_remove_access():
    """Remove access for multiple users from a Pine Script"""
    try:
        data = request.get_json()
        usernames = data.get('usernames', [])
        script_id = data.get('script_id', '').strip()

        if not usernames or not script_id:
            return jsonify({"success": False, "error": "Usernames and Script ID required"})

        script = PineScript.get(script_id)
        script_name = script.name if script else script_id

        removed_count = 0
        errors = []

        for username in usernames:
            try:
                # Remove access via TradingView API
                result = tv_api.remove_pine_permission(username, script_id)

                # Log the operation
                AccessLog.create(
                    username=username,
                    pine_id=script_id,
                    pine_script_name=script_name,
                    operation="remove",
                    status="success" if result.get('success', False) else "failure",
                    details=f"Bulk removal - {result.get('message', '')}"
                )

                if result.get('success', False):
                    removed_count += 1
                else:
                    errors.append(f"{username}: {result.get('message', 'Unknown error')}")

            except Exception as e:
                logger.error(f"Error removing access for {username}: {e}")
                errors.append(f"{username}: {str(e)}")

        return jsonify({
            "success": removed_count > 0,
            "removed_count": removed_count,
            "total_requested": len(usernames),
            "errors": errors
        })

    except Exception as e:
        logger.error(f"Error bulk removing access: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/export-script-users/<script_id>')
def export_script_users(script_id):
    """Export all usernames that have access to a specific Pine Script as text file"""
    try:
        # Get users from TradingView API
        users = tv_api.get_script_users(script_id)
        
        script = PineScript.get(script_id)
        script_name = script.name if script else script_id

        if not users:
            # Return empty file if no users
            from flask import Response
            return Response(
                "No users found with access to this script.\n",
                mimetype='text/plain',
                headers={"Content-disposition": f"attachment; filename={script_name.replace(' ', '_')}_users.txt"}
            )

        # Create text content with usernames
        text_content = f"Users with access to: {script_name}\n"
        text_content += f"Script ID: {script_id}\n"
        text_content += f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text_content += "=" * 50 + "\n\n"
        
        for i, user in enumerate(users, 1):
            username = user.get('username', 'Unknown')
            access_type = 'Lifetime' if user.get('has_lifetime_access', False) else 'Temporary'
            expiration = user.get('expiration')
            created = user.get('created')
            
            text_content += f"{i}. {username}\n"
            text_content += f"   Access Type: {access_type}\n"
            
            if expiration:
                text_content += f"   Expires: {expiration}\n"
            else:
                text_content += f"   Expires: Never\n"
                
            if created:
                text_content += f"   Created: {created}\n"
            
            text_content += "\n"

        text_content += f"\nTotal Users: {len(users)}\n"

        from flask import Response
        return Response(
            text_content,
            mimetype='text/plain',
            headers={"Content-disposition": f"attachment; filename={script_name.replace(' ', '_')}_users.txt"}
        )

    except Exception as e:
        logger.error(f"Error exporting script users: {e}")
        from flask import Response
        return Response(
            f"Error exporting users: {str(e)}\n",
            mimetype='text/plain',
            headers={"Content-disposition": f"attachment; filename=export_error.txt"}
        )

# ===== REDIRECT ROUTES =====

@app.route('/admin')
def admin_redirect():
    """Redirect admin to main dashboard"""
    return redirect(url_for('index'))

@app.route('/access')
def access_redirect():
    """Redirect access to main dashboard"""
    return redirect(url_for('index'))

@app.route('/manage')
def manage_redirect():
    """Redirect old manage route to main dashboard"""
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return "<h1>404 - Page Not Found</h1>", 404

@app.errorhandler(500)
def internal_error(error):
    return "<h1>500 - Internal Server Error</h1>", 500