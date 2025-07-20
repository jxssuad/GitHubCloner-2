from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User, AccessKey, AccessLog, PineScript, UserAccess
from tradingview import TradingViewAPI
import logging

main_bp = Blueprint('main', __name__)

# Home page - Key Entry or Login
@main_bp.route('/')
def index():
    return render_template('index.html')

# Key validation and user registration
@main_bp.route('/validate-key', methods=['POST'])
def validate_key():
    key_code = request.form.get('key_code', '').strip().upper()
    
    if not key_code:
        flash('Please enter an access key', 'error')
        return redirect(url_for('main.index'))
    
    # Check if key exists and is active
    access_key = AccessKey.query.filter_by(key_code=key_code, status='active').first()
    if not access_key:
        flash('Invalid or expired access key', 'error')
        return redirect(url_for('main.index'))
    
    # Store key info in session for registration
    session['pending_key'] = {
        'id': access_key.id,
        'key_code': access_key.key_code,
        'user_name': access_key.user_name,
        'user_email': access_key.user_email
    }
    
    return render_template('register.html', 
                         user_name=access_key.user_name, 
                         user_email=access_key.user_email)

# User registration with key
@main_bp.route('/register', methods=['POST'])
def register():
    if 'pending_key' not in session:
        flash('Invalid session. Please enter your access key again.', 'error')
        return redirect(url_for('main.index'))
    
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    if not email or not password:
        flash('Email and password are required', 'error')
        return render_template('register.html')
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('An account with this email already exists. Please login instead.', 'error')
        return redirect(url_for('main.login'))
    
    # Get the pending key
    pending_key = session['pending_key']
    access_key = AccessKey.query.get(pending_key['id'])
    
    if not access_key or access_key.status != 'active':
        flash('Access key is no longer valid', 'error')
        return redirect(url_for('main.index'))
    
    # Create new user
    user = User(
        email=email,
        name=pending_key['user_name'],
        access_key_id=access_key.id
    )
    user.set_password(password)
    
    # Mark key as used
    access_key.mark_as_used()
    
    db.session.add(user)
    db.session.commit()
    
    # Login the user
    login_user(user)
    
    # Clear session
    session.pop('pending_key', None)
    
    flash('Account created successfully! Welcome to TradingView Access Manager.', 'success')
    return redirect(url_for('main.manage'))

# Login page
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if user.is_admin:
                return redirect(next_page) if next_page else redirect(url_for('main.admin'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('main.manage'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

# Logout
@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

# Main management panel (was /manage, now main page for users)
@main_bp.route('/manage')
@login_required
def manage():
    if current_user.is_admin:
        return redirect(url_for('main.admin'))
    
    return render_template('manage.html')

# Admin panel (was dashboard, now /admin)
@main_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.manage'))
    
    # Get all access keys with their associated users
    access_keys = AccessKey.query.order_by(AccessKey.created_at.desc()).all()
    
    # Get user access data for each key
    key_data = []
    for key in access_keys:
        key_info = {
            'key': key,
            'user': key.user,
            'accesses': []
        }
        
        if key.user:
            accesses = UserAccess.query.filter_by(user_id=key.user.id).all()
            for access in accesses:
                key_info['accesses'].append({
                    'pine_script': access.pine_script,
                    'tradingview_username': access.tradingview_username,
                    'granted_at': access.granted_at
                })
        
        key_data.append(key_info)
    
    return render_template('admin.html', key_data=key_data)

# Create new access key (admin only)
@main_bp.route('/admin/create-key', methods=['POST'])
@login_required
def create_key():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    data = request.get_json()
    user_name = data.get('user_name', '').strip()
    user_email = data.get('user_email', '').strip()
    
    if not user_name or not user_email:
        return jsonify({'success': False, 'message': 'Name and email are required'})
    
    # Generate unique key
    while True:
        key_code = AccessKey.generate_key()
        if not AccessKey.query.filter_by(key_code=key_code).first():
            break
    
    access_key = AccessKey(
        key_code=key_code,
        user_name=user_name,
        user_email=user_email
    )
    
    db.session.add(access_key)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Access key created successfully',
        'key_code': key_code
    })

# Remove user access from admin panel
@main_bp.route('/admin/remove-access', methods=['POST'])
@login_required
def admin_remove_access():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    pine_script_ids = data.get('pine_script_ids', [])
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'})
    
    user = User.query.get(user_id)
    if not user or not user.tradingview_username:
        return jsonify({'success': False, 'message': 'User not found or no TradingView username set'})
    
    try:
        tv_api = TradingViewAPI()
        
        # If specific scripts provided, remove only those; otherwise remove all
        if pine_script_ids:
            scripts_to_remove = PineScript.query.filter(PineScript.id.in_(pine_script_ids)).all()
        else:
            # Remove all access for this user
            user_accesses = UserAccess.query.filter_by(user_id=user_id).all()
            scripts_to_remove = [access.pine_script for access in user_accesses]
        
        removed_scripts = []
        for script in scripts_to_remove:
            success = tv_api.remove_access(user.tradingview_username, script.pine_id)
            if success:
                # Remove from database
                UserAccess.query.filter_by(
                    user_id=user_id, 
                    pine_script_id=script.id
                ).delete()
                removed_scripts.append(script.name)
                
                # Log the action
                log_entry = AccessLog(
                    user_id=current_user.id,
                    username=user.tradingview_username,
                    action='remove',
                    pine_script_id=script.pine_id,
                    status='success',
                    details=f'Removed by admin: {current_user.email}'
                )
                db.session.add(log_entry)
        
        # Reset user's access generation flag if all access removed
        remaining_access = UserAccess.query.filter_by(user_id=user_id).count()
        if remaining_access == 0:
            user.has_generated_access = False
            user.tradingview_username = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully removed access for {len(removed_scripts)} script(s)',
            'removed_scripts': removed_scripts
        })
    
    except Exception as e:
        logging.error(f"Error removing access: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# API Routes for the management panel
@main_bp.route('/api/validate-username', methods=['POST'])
@login_required
def api_validate_username():
    if current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin accounts cannot manage TradingView access'})
    
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': 'Username is required'})
    
    # Check if user already has access and username is different
    if current_user.has_generated_access and current_user.tradingview_username != username:
        return jsonify({
            'success': False, 
            'message': f'You already have access granted for "{current_user.tradingview_username}". Please remove all access before switching users.'
        })
    
    try:
        tv_api = TradingViewAPI()
        is_valid, verified_username = tv_api.validate_username(username)
        
        if is_valid:
            return jsonify({
                'success': True,
                'message': f'Username "{verified_username}" is valid',
                'data': {
                    'validuser': True,
                    'verifiedUserName': verified_username
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Username "{username}" not found on TradingView'
            })
    
    except Exception as e:
        logging.error(f"Username validation error: {str(e)}")
        return jsonify({'success': False, 'message': f'Validation error: {str(e)}'})

@main_bp.route('/api/pine-scripts')
@login_required
def api_pine_scripts():
    scripts = PineScript.query.filter_by(active=True).all()
    return jsonify({
        'success': True,
        'scripts': [{
            'id': script.id,
            'pine_id': script.pine_id,
            'name': script.name,
            'description': script.description
        } for script in scripts]
    })

@main_bp.route('/api/grant-access', methods=['POST'])
@login_required
def api_grant_access():
    if current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin accounts cannot manage TradingView access'})
    
    data = request.get_json()
    username = data.get('username', '').strip()
    pine_ids = data.get('pine_ids', [])
    
    if not username or not pine_ids:
        return jsonify({'success': False, 'message': 'Username and pine script IDs are required'})
    
    # Check if user can generate access
    if current_user.has_generated_access and current_user.tradingview_username != username:
        return jsonify({
            'success': False,
            'message': 'You already have access for another username. Remove all access first.'
        })
    
    try:
        tv_api = TradingViewAPI()
        scripts = PineScript.query.filter(PineScript.pine_id.in_(pine_ids)).all()
        
        granted_count = 0
        for script in scripts:
            success = tv_api.grant_access(username, script.pine_id)
            if success:
                # Check if access already exists
                existing_access = UserAccess.query.filter_by(
                    user_id=current_user.id,
                    pine_script_id=script.id
                ).first()
                
                if not existing_access:
                    user_access = UserAccess(
                        user_id=current_user.id,
                        pine_script_id=script.id,
                        tradingview_username=username
                    )
                    db.session.add(user_access)
                
                # Log the action
                log_entry = AccessLog(
                    user_id=current_user.id,
                    username=username,
                    action='grant',
                    pine_script_id=script.pine_id,
                    status='success'
                )
                db.session.add(log_entry)
                granted_count += 1
        
        # Update user flags
        current_user.has_generated_access = True
        current_user.tradingview_username = username
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully granted access to {granted_count} Pine Script(s) for {username}'
        })
    
    except Exception as e:
        logging.error(f"Grant access error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@main_bp.route('/api/remove-access', methods=['POST'])
@login_required
def api_remove_access():
    if current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin accounts cannot manage TradingView access'})
    
    data = request.get_json()
    username = data.get('username', current_user.tradingview_username)
    
    if not username:
        return jsonify({'success': False, 'message': 'No username to remove access for'})
    
    try:
        tv_api = TradingViewAPI()
        
        # Get all user accesses
        user_accesses = UserAccess.query.filter_by(user_id=current_user.id).all()
        
        removed_count = 0
        for access in user_accesses:
            success = tv_api.remove_access(username, access.pine_script.pine_id)
            if success:
                db.session.delete(access)
                
                # Log the action
                log_entry = AccessLog(
                    user_id=current_user.id,
                    username=username,
                    action='remove',
                    pine_script_id=access.pine_script.pine_id,
                    status='success'
                )
                db.session.add(log_entry)
                removed_count += 1
        
        # Reset user flags
        current_user.has_generated_access = False
        current_user.tradingview_username = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully removed all access for {username}'
        })
    
    except Exception as e:
        logging.error(f"Remove access error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})