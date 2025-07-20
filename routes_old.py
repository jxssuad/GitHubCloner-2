from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app import db
from models import AccessLog, PineScript
from tradingview import tv_api
from config import Config
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard page"""
    try:
        Config.validate()
        # Get recent access logs
        recent_logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(10).all()
        # Get configured pine scripts
        pine_scripts = PineScript.query.filter_by(is_active=True).all()
        
        return render_template('index.html', 
                             recent_logs=recent_logs, 
                             pine_scripts=pine_scripts,
                             config_valid=True)
    except ValueError as e:
        flash(f"Configuration Error: {e}", "danger")
        return render_template('index.html', 
                             recent_logs=[], 
                             pine_scripts=[],
                             config_valid=False)

@main_bp.route('/manage')
def manage():
    """User access management page"""
    return render_template('manage.html')

# API endpoints for the new manage interface
@main_bp.route('/api/pine-scripts')
def api_pine_scripts():
    """Get list of active Pine Scripts"""
    scripts = PineScript.query.filter_by(is_active=True).all()
    return jsonify({
        "scripts": [
            {
                "id": script.id,
                "pine_id": script.pine_id,
                "name": script.name,
                "description": script.description
            }
            for script in scripts
        ]
    })

@main_bp.route('/api/validate-username', methods=['POST'])
def api_validate_username_new():
    """Validate TradingView username"""
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({"success": False, "message": "Username is required"})
    
    try:
        result = tv_api.validate_username(username)
        if result['validuser']:
            # Log validation
            log = AccessLog(
                username=username,
                pine_id="validation",
                operation="validate",
                status="success",
                details=f"Verified as: {result['verifiedUserName']}"
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                "success": True, 
                "message": f"Username '{result['verifiedUserName']}' is valid",
                "data": result
            })
        else:
            # Log failed validation
            log = AccessLog(
                username=username,
                pine_id="validation",
                operation="validate",
                status="failure",
                details="Username not found"
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                "success": False, 
                "message": f"Username '{username}' is not valid"
            })
    
    except Exception as e:
        logger.error(f"Error validating username: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@main_bp.route('/api/grant-access', methods=['POST'])
def api_grant_access_new():
    """Grant access to Pine Scripts"""
    data = request.get_json()
    username = data.get('username', '').strip()
    pine_ids = data.get('pine_ids', [])
    duration = data.get('duration', '30D')
    
    if not username or not pine_ids:
        return jsonify({"success": False, "message": "Username and Pine Scripts are required"})
    
    try:
        results = tv_api.grant_access(username, pine_ids, duration)
        
        # Log each grant attempt
        for result in results:
            log = AccessLog(
                username=result['username'],
                pine_id=result['pine_id'],
                operation="grant",
                status="success" if result['hasAccess'] else "failure",
                details=f"Duration: {duration}, Status: {result.get('status', 'Unknown')}"
            )
            db.session.add(log)
        
        db.session.commit()
        
        success_count = sum(1 for r in results if r['hasAccess'])
        if success_count == len(results):
            message = f"Successfully granted access to all {len(results)} Pine Scripts for {duration}"
            return jsonify({"success": True, "message": message, "data": results})
        else:
            message = f"Granted access to {success_count} out of {len(results)} Pine Scripts"
            return jsonify({"success": False, "message": message, "data": results})
    
    except Exception as e:
        logger.error(f"Error granting access: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@main_bp.route('/api/remove-access', methods=['POST'])
def api_remove_access_new():
    """Remove access from Pine Scripts"""
    data = request.get_json()
    username = data.get('username', '').strip()
    pine_ids = data.get('pine_ids', [])
    
    if not username or not pine_ids:
        return jsonify({"success": False, "message": "Username and Pine Scripts are required"})
    
    try:
        results = tv_api.remove_access(username, pine_ids)
        
        # Log each remove attempt
        for result in results:
            log = AccessLog(
                username=result['username'],
                pine_id=result['pine_id'],
                operation="remove",
                status="success" if not result['hasAccess'] else "failure",
                details=f"Status: {result.get('status', 'Unknown')}"
            )
            db.session.add(log)
        
        db.session.commit()
        
        success_count = sum(1 for r in results if not r['hasAccess'])
        if success_count == len(results):
            message = f"Successfully removed access from all {len(results)} Pine Scripts"
            return jsonify({"success": True, "message": message, "data": results})
        else:
            message = f"Removed access from {success_count} out of {len(results)} Pine Scripts"
            return jsonify({"success": False, "message": message, "data": results})
    
    except Exception as e:
        logger.error(f"Error removing access: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@main_bp.route('/api/validate/<username>')
def api_validate_username(username):
    """API endpoint for username validation"""
    try:
        result = tv_api.validate_username(username)
        return jsonify(result)
    except Exception as e:
        logger.error(f"API validation error: {e}")
        return jsonify({"validuser": False, "verifiedUserName": "", "error": str(e)}), 500

@main_bp.route('/api/access/<username>', methods=['GET', 'POST', 'DELETE'])
def api_manage_access(username):
    """API endpoints for access management"""
    try:
        if request.method == 'GET':
            # Get current access
            data = request.get_json() or {}
            pine_ids = data.get('pine_ids', [])
            results = tv_api.get_user_access(username, pine_ids)
            return jsonify(results)
        
        elif request.method == 'POST':
            # Grant access
            data = request.get_json() or {}
            pine_ids = data.get('pine_ids', [])
            results = tv_api.grant_access(username, pine_ids)
            return jsonify(results)
        
        elif request.method == 'DELETE':
            # Remove access
            data = request.get_json() or {}
            pine_ids = data.get('pine_ids', [])
            results = tv_api.remove_access(username, pine_ids)
            return jsonify(results)
    
    except Exception as e:
        logger.error(f"API access management error: {e}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/scripts/add', methods=['POST'])
def add_pine_script():
    """Add a new Pine Script configuration"""
    pine_id = request.form.get('pine_id', '').strip()
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not pine_id or not name:
        flash("Pine ID and Name are required", "danger")
        return redirect(url_for('main.index'))
    
    try:
        # Check if active script already exists, remove any inactive ones
        existing = PineScript.query.filter_by(pine_id=pine_id).first()
        if existing:
            if existing.is_active:
                flash("Pine Script with this ID already exists and is active", "warning")
                return redirect(url_for('main.index'))
            else:
                # Remove inactive script with same ID to allow re-adding
                db.session.delete(existing)
                db.session.commit()
                logger.info(f"Removed inactive Pine Script {pine_id} to allow re-adding")
        
        # Add new script
        script = PineScript(
            pine_id=pine_id,
            name=name,
            description=description
        )
        db.session.add(script)
        db.session.commit()
        
        flash(f"Pine Script '{name}' added successfully", "success")
    
    except Exception as e:
        logger.error(f"Error adding pine script: {e}")
        flash(f"Error adding Pine Script: {str(e)}", "danger")
    
    return redirect(url_for('main.index'))

@main_bp.route('/scripts/toggle/<int:script_id>')
def toggle_pine_script(script_id):
    """Toggle Pine Script active status - removes from backend when turned off"""
    try:
        script = PineScript.query.get_or_404(script_id)
        
        if script.is_active:
            # If turning off, remove completely from backend
            script_name = script.name
            db.session.delete(script)
            db.session.commit()
            flash(f"Pine Script '{script_name}' removed from backend", "success")
            logger.info(f"Pine Script {script.pine_id} ({script_name}) removed from backend")
        else:
            # If turning on (shouldn't happen since we delete inactive ones)
            script.is_active = True
            db.session.commit()
            flash(f"Pine Script '{script.name}' activated", "success")
    
    except Exception as e:
        logger.error(f"Error toggling pine script: {e}")
        flash(f"Error updating Pine Script: {str(e)}", "danger")
    
    return redirect(url_for('main.index'))
