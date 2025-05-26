"""
Authentication routes for Toronto AI Weather web application.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from datetime import datetime

from src.main import db
from src.models.user import User, UserTier, RegistrationRequest
from src.utils.email import send_verification_email, send_password_reset_email
import secrets

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html', title='Sign In')
        
        if not user.is_active:
            flash('Account is disabled. Please contact support.', 'danger')
            return render_template('auth/login.html', title='Sign In')
        
        if not user.is_verified:
            flash('Please verify your email address before logging in.', 'warning')
            return render_template('auth/login.html', title='Sign In')
        
        login_user(user, remember=remember)
        user.update_last_login()
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Validate input
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'danger')
            return render_template('auth/register.html', title='Register')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html', title='Register')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html', title='Register')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('auth/register.html', title='Register')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password=password,
            tier=UserTier.CIVILIAN,
            first_name=first_name,
            last_name=last_name
        )
        
        # Generate verification token
        user.verification_token = secrets.token_hex(16)
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(user)
        
        flash('Registration successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register')

@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify user email."""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid or expired verification link', 'danger')
        return redirect(url_for('auth.login'))
    
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Handle password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email is required', 'danger')
            return render_template('auth/reset_password_request.html', title='Reset Password')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            user.verification_token = secrets.token_hex(16)
            db.session.commit()
            
            # Send password reset email
            send_password_reset_email(user)
        
        flash('If your email is registered, you will receive password reset instructions.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', title='Reset Password')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid or expired reset link', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([password, confirm_password]):
            flash('All fields are required', 'danger')
            return render_template('auth/reset_password.html', title='Reset Password', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/reset_password.html', title='Reset Password', token=token)
        
        user.set_password(password)
        user.verification_token = None
        db.session.commit()
        
        flash('Password has been reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Reset Password', token=token)

@auth_bp.route('/request-tier-upgrade', methods=['GET', 'POST'])
@login_required
def request_tier_upgrade():
    """Handle tier upgrade requests."""
    if request.method == 'POST':
        requested_tier = request.form.get('requested_tier')
        organization = request.form.get('organization')
        justification = request.form.get('justification')
        
        if not all([requested_tier, organization, justification]):
            flash('All fields are required', 'danger')
            return render_template('auth/request_tier_upgrade.html', title='Request Tier Upgrade')
        
        # Check if user already has a pending request
        existing_request = RegistrationRequest.query.filter_by(
            email=current_user.email,
            status='pending'
        ).first()
        
        if existing_request:
            flash('You already have a pending tier upgrade request', 'warning')
            return redirect(url_for('main.profile'))
        
        # Create new request
        upgrade_request = RegistrationRequest(
            email=current_user.email,
            organization=organization,
            requested_tier=requested_tier,
            justification=justification
        )
        
        db.session.add(upgrade_request)
        db.session.commit()
        
        flash('Your tier upgrade request has been submitted and is pending review.', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('auth/request_tier_upgrade.html', title='Request Tier Upgrade')

@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    """API endpoint for user login."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403
    
    if not user.is_verified:
        return jsonify({'error': 'Email not verified'}), 403
    
    # Generate API token
    token = secrets.token_hex(32)
    
    # Return user info and token
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'tier': user.tier,
        'token': token
    }), 200
