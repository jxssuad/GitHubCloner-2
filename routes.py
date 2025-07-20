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
        
        # Validate inputs
        if not username:
            flash("Username is required", "danger")
            return redirect(url_for('main.manage'))
        
        if not pine_ids_input:
            flash("At least one Pine Script ID is required", "danger")
            return redirect(url_for('main.manage'))
        
        # Parse pine IDs
        pine_ids = [pid.strip() for pid in pine_ids_input.split(',') if pid.strip()]
        
        try:
            if action == 'validate':
                result = tv_api.validate_username(username)
                if result['validuser']:
                    flash(f"Username '{result['verifiedUserName']}' is valid", "success")
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
                    flash(f"Username '{username}' is not valid", "warning")
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
                
                if access_summary:
                    flash(f"Access Status: {'; '.join(access_summary)}", "info")
                else:
                    flash("Unable to retrieve access information", "warning")
                
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
                success_count = sum(1 for r in results if r.get('status') == 'Success')
                if success_count > 0:
                    flash(f"Successfully granted access to {success_count} script(s)", "success")
                else:
                    flash("Failed to grant access", "danger")
                
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
                success_count = sum(1 for r in results if r.get('status') == 'Success')
                if success_count > 0:
                    flash(f"Successfully removed access from {success_count} script(s)", "success")
                else:
                    flash("Failed to remove access", "danger")
                
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
            flash(f"Error: {str(e)}", "danger")
        
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
        # Check if script already exists
        existing = PineScript.query.filter_by(pine_id=pine_id).first()
        if existing:
            flash("Pine Script with this ID already exists", "warning")
            return redirect(url_for('main.index'))
        
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
    """Toggle Pine Script active status"""
    try:
        script = PineScript.query.get_or_404(script_id)
        script.is_active = not script.is_active
        db.session.commit()
        
        status = "activated" if script.is_active else "deactivated"
        flash(f"Pine Script '{script.name}' {status}", "success")
    
    except Exception as e:
        logger.error(f"Error toggling pine script: {e}")
        flash(f"Error updating Pine Script: {str(e)}", "danger")
    
    return redirect(url_for('main.index'))
