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

@main_bp.route('/manage', methods=['GET', 'POST'])
def manage():
    """User access management page"""
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username', '').strip()
        pine_ids_input = request.form.get('pine_ids', '').strip()
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Validate inputs
        if not username:
            if is_ajax:
                return jsonify({"success": False, "message": "Username is required", "type": "danger"})
            flash("Username is required", "danger")
            return redirect(url_for('main.manage'))
        
        if not pine_ids_input and action != 'validate':
            if is_ajax:
                return jsonify({"success": False, "message": "At least one Pine Script ID is required", "type": "danger"})
            flash("At least one Pine Script ID is required", "danger")
            return redirect(url_for('main.manage'))
        
        # Parse pine IDs
        pine_ids = [pid.strip() for pid in pine_ids_input.split(',') if pid.strip()]
        
        try:
            if action == 'validate':
                result = tv_api.validate_username(username)
                if result['validuser']:
                    message = f"Username '{result['verifiedUserName']}' is valid"
                    if is_ajax:
                        return jsonify({"success": True, "message": message, "type": "success", "data": result})
                    flash(message, "success")
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
                else:
                    message = f"Username '{username}' is not valid"
                    if is_ajax:
                        return jsonify({"success": False, "message": message, "type": "warning", "data": result})
                    flash(message, "warning")
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
            
            elif action == 'check':
                results = tv_api.get_user_access(username, pine_ids)
                access_summary = []
                for result in results:
                    status = "Has Access" if result['hasAccess'] else "No Access"
                    access_summary.append(f"{result['pine_id']}: {status}")
                
                message = f"Access Status: {'; '.join(access_summary)}" if access_summary else "Unable to retrieve access information"
                msg_type = "info" if access_summary else "warning"
                
                if is_ajax:
                    return jsonify({"success": bool(access_summary), "message": message, "type": msg_type, "data": results})
                flash(message, msg_type)
                
                # Log check operation
                log = AccessLog(
                    username=username,
                    pine_id=",".join(pine_ids),
                    operation="check",
                    status="success",
                    details=f"Checked {len(pine_ids)} scripts"
                )
                db.session.add(log)
                db.session.commit()
            
            elif action == 'grant':
                results = tv_api.grant_access(username, pine_ids)
                success_count = sum(1 for r in results if 'Success' in r.get('status', ''))
                message = f"Successfully granted access to {success_count} script(s)" if success_count > 0 else "Failed to grant access"
                msg_type = "success" if success_count > 0 else "danger"
                
                if is_ajax:
                    return jsonify({"success": success_count > 0, "message": message, "type": msg_type, "data": results})
                flash(message, msg_type)
                
                # Log grant operation
                log = AccessLog(
                    username=username,
                    pine_id=",".join(pine_ids),
                    operation="grant",
                    status="success" if success_count > 0 else "failure",
                    details=f"Granted access to {success_count}/{len(pine_ids)} scripts"
                )
                db.session.add(log)
                db.session.commit()
            
            elif action == 'remove':
                results = tv_api.remove_access(username, pine_ids)
                success_count = sum(1 for r in results if 'Success' in r.get('status', ''))
                message = f"Successfully removed access from {success_count} script(s)" if success_count > 0 else "Failed to remove access"
                msg_type = "success" if success_count > 0 else "danger"
                
                if is_ajax:
                    return jsonify({"success": success_count > 0, "message": message, "type": msg_type, "data": results})
                flash(message, msg_type)
                
                # Log remove operation
                log = AccessLog(
                    username=username,
                    pine_id=",".join(pine_ids),
                    operation="remove",
                    status="success" if success_count > 0 else "failure",
                    details=f"Removed access from {success_count}/{len(pine_ids)} scripts"
                )
                db.session.add(log)
                db.session.commit()
        
        except Exception as e:
            logger.error(f"Error in manage operation: {e}")
            error_message = f"Error: {str(e)}"
            if is_ajax:
                return jsonify({"success": False, "message": error_message, "type": "danger"})
            flash(error_message, "danger")
        
        if not is_ajax:
            return redirect(url_for('main.manage'))
    
    # GET request - show form
    pine_scripts = PineScript.query.filter_by(is_active=True).all()
    default_pine_ids = ",".join(Config.DEFAULT_PINE_IDS) if Config.DEFAULT_PINE_IDS else ""
    
    return render_template('manage.html', 
                         pine_scripts=pine_scripts,
                         default_pine_ids=default_pine_ids)

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
