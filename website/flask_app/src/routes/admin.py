"""
Admin routes for Toronto AI Weather web application.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from src.main import db
from src.models.user import User, UserTier, RegistrationRequest
from src.models.weather import Location, WeatherData, Forecast, WeatherAlert
from src.models.device import Device, SystemMetrics
from src.models.api import ApiKey, ApiQuota

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access."""
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Admin access required', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/')
@admin_required
def index():
    """Admin dashboard."""
    # Get system metrics
    metrics = SystemMetrics.query.order_by(SystemMetrics.timestamp.desc()).first()
    
    # Get user counts by tier
    user_counts = db.session.query(
        User.tier, db.func.count(User.id)
    ).group_by(User.tier).all()
    
    # Get pending registration requests
    pending_requests = RegistrationRequest.query.filter_by(
        status='pending'
    ).count()
    
    # Get active devices
    active_devices = Device.query.filter_by(is_active=True).count()
    
    # Get recent alerts
    recent_alerts = WeatherAlert.query.filter(
        WeatherAlert.end_time > datetime.utcnow()
    ).order_by(WeatherAlert.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/index.html',
        title='Admin Dashboard',
        metrics=metrics,
        user_counts=dict(user_counts),
        pending_requests=pending_requests,
        active_devices=active_devices,
        recent_alerts=recent_alerts
    )

@admin_bp.route('/users')
@admin_required
def users():
    """User management."""
    # Get all users with pagination
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    
    return render_template(
        'admin/users.html',
        title='User Management',
        users=users
    )

@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """User detail view."""
    user = User.query.get_or_404(user_id)
    
    # Get user's devices
    devices = Device.query.filter_by(user_id=user.id).all()
    
    # Get user's API keys
    api_keys = ApiKey.query.filter_by(user_id=user.id).all()
    
    # Get user's API quota
    api_quota = ApiQuota.query.filter_by(user_id=user.id).first()
    
    return render_template(
        'admin/user_detail.html',
        title=f'User: {user.username}',
        user=user,
        devices=devices,
        api_keys=api_keys,
        api_quota=api_quota
    )

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def edit_user(user_id):
    """Edit user."""
    user = User.query.get_or_404(user_id)
    
    # Update user fields
    user.username = request.form.get('username', user.username)
    user.email = request.form.get('email', user.email)
    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name = request.form.get('last_name', user.last_name)
    user.tier = request.form.get('tier', user.tier)
    user.organization = request.form.get('organization', user.organization)
    user.is_active = request.form.get('is_active') == 'on'
    user.is_verified = request.form.get('is_verified') == 'on'
    
    db.session.commit()
    
    flash('User updated successfully', 'success')
    return redirect(url_for('admin.user_detail', user_id=user.id))

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """Reset user password."""
    user = User.query.get_or_404(user_id)
    
    password = request.form.get('password')
    if not password:
        flash('Password is required', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user.id))
    
    user.set_password(password)
    db.session.commit()
    
    flash('Password reset successfully', 'success')
    return redirect(url_for('admin.user_detail', user_id=user.id))

@admin_bp.route('/registration-requests')
@admin_required
def registration_requests():
    """Registration request management."""
    # Get all pending requests
    requests = RegistrationRequest.query.filter_by(
        status='pending'
    ).order_by(RegistrationRequest.created_at.desc()).all()
    
    return render_template(
        'admin/registration_requests.html',
        title='Registration Requests',
        requests=requests
    )

@admin_bp.route('/registration-requests/<int:request_id>/approve', methods=['POST'])
@admin_required
def approve_request(request_id):
    """Approve registration request."""
    reg_request = RegistrationRequest.query.get_or_404(request_id)
    
    if reg_request.status != 'pending':
        flash('Request has already been processed', 'warning')
        return redirect(url_for('admin.registration_requests'))
    
    # Find the user
    user = User.query.filter_by(email=reg_request.email).first()
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.registration_requests'))
    
    # Update user tier
    user.tier = reg_request.requested_tier
    user.organization = reg_request.organization
    
    # Update request status
    reg_request.status = 'approved'
    reg_request.processed_at = datetime.utcnow()
    reg_request.processed_by = current_user.id
    
    db.session.commit()
    
    # Create API quota for user if needed
    if user.can_access_api():
        quota = ApiQuota.query.filter_by(user_id=user.id).first()
        
        if not quota:
            # Set quota based on tier
            daily_limit = 1000  # Default
            monthly_limit = 30000  # Default
            
            if user.tier == UserTier.WEATHER_AGENCY:
                daily_limit = 10000
                monthly_limit = 300000
            elif user.tier == UserTier.NEWS:
                daily_limit = 5000
                monthly_limit = 150000
            elif user.tier == UserTier.GOVERNMENT:
                daily_limit = 20000
                monthly_limit = 600000
            elif user.tier == UserTier.MILITARY:
                daily_limit = 50000
                monthly_limit = 1500000
            
            quota = ApiQuota(
                user_id=user.id,
                tier=user.tier,
                daily_limit=daily_limit,
                monthly_limit=monthly_limit,
                reset_day=1  # First day of month
            )
            
            db.session.add(quota)
            db.session.commit()
    
    flash('Registration request approved', 'success')
    return redirect(url_for('admin.registration_requests'))

@admin_bp.route('/registration-requests/<int:request_id>/reject', methods=['POST'])
@admin_required
def reject_request(request_id):
    """Reject registration request."""
    reg_request = RegistrationRequest.query.get_or_404(request_id)
    
    if reg_request.status != 'pending':
        flash('Request has already been processed', 'warning')
        return redirect(url_for('admin.registration_requests'))
    
    # Update request status
    reg_request.status = 'rejected'
    reg_request.processed_at = datetime.utcnow()
    reg_request.processed_by = current_user.id
    
    db.session.commit()
    
    flash('Registration request rejected', 'success')
    return redirect(url_for('admin.registration_requests'))

@admin_bp.route('/devices')
@admin_required
def devices():
    """Device management."""
    # Get all devices with pagination
    page = request.args.get('page', 1, type=int)
    devices = Device.query.paginate(page=page, per_page=20)
    
    return render_template(
        'admin/devices.html',
        title='Device Management',
        devices=devices
    )

@admin_bp.route('/devices/<int:device_id>')
@admin_required
def device_detail(device_id):
    """Device detail view."""
    device = Device.query.get_or_404(device_id)
    
    # Get device contributions
    from src.models.device import DeviceContribution
    contributions = DeviceContribution.query.filter_by(
        device_id=device.id
    ).order_by(DeviceContribution.created_at.desc()).limit(20).all()
    
    return render_template(
        'admin/device_detail.html',
        title=f'Device: {device.device_name}',
        device=device,
        contributions=contributions
    )

@admin_bp.route('/devices/<int:device_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_device_active(device_id):
    """Toggle device active status."""
    device = Device.query.get_or_404(device_id)
    
    device.is_active = not device.is_active
    db.session.commit()
    
    status = 'activated' if device.is_active else 'deactivated'
    flash(f'Device {status} successfully', 'success')
    return redirect(url_for('admin.device_detail', device_id=device.id))

@admin_bp.route('/system-metrics')
@admin_required
def system_metrics():
    """System metrics view."""
    # Get metrics with pagination
    page = request.args.get('page', 1, type=int)
    metrics = SystemMetrics.query.order_by(
        SystemMetrics.timestamp.desc()
    ).paginate(page=page, per_page=24)  # 24 hours of hourly metrics
    
    return render_template(
        'admin/system_metrics.html',
        title='System Metrics',
        metrics=metrics
    )

@admin_bp.route('/alerts')
@admin_required
def alerts():
    """Weather alert management."""
    # Get all active alerts
    active_alerts = WeatherAlert.query.filter(
        WeatherAlert.end_time > datetime.utcnow()
    ).order_by(WeatherAlert.created_at.desc()).all()
    
    # Get recent expired alerts
    expired_alerts = WeatherAlert.query.filter(
        WeatherAlert.end_time <= datetime.utcnow()
    ).order_by(WeatherAlert.end_time.desc()).limit(20).all()
    
    return render_template(
        'admin/alerts.html',
        title='Weather Alerts',
        active_alerts=active_alerts,
        expired_alerts=expired_alerts
    )

@admin_bp.route('/alerts/create', methods=['GET', 'POST'])
@admin_required
def create_alert():
    """Create a new weather alert."""
    if request.method == 'POST':
        # Get form data
        location_id = request.form.get('location_id')
        alert_type = request.form.get('alert_type')
        severity = request.form.get('severity')
        title = request.form.get('title')
        description = request.form.get('description')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        issuing_authority = request.form.get('issuing_authority')
        
        if not all([location_id, alert_type, severity, title, description, start_time, end_time]):
            flash('All fields are required', 'danger')
            return redirect(url_for('admin.create_alert'))
        
        try:
            location_id = int(location_id)
            start_time = datetime.fromisoformat(start_time)
            end_time = datetime.fromisoformat(end_time)
        except (ValueError, TypeError):
            flash('Invalid input data', 'danger')
            return redirect(url_for('admin.create_alert'))
        
        # Create new alert
        alert = WeatherAlert(
            location_id=location_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            issuing_authority=issuing_authority or 'Toronto AI Weather'
        )
        
        db.session.add(alert)
        db.session.commit()
        
        flash('Alert created successfully', 'success')
        return redirect(url_for('admin.alerts'))
    
    # Get all locations for the form
    locations = Location.query.all()
    
    return render_template(
        'admin/create_alert.html',
        title='Create Alert',
        locations=locations
    )

@admin_bp.route('/alerts/<int:alert_id>/delete', methods=['POST'])
@admin_required
def delete_alert(alert_id):
    """Delete a weather alert."""
    alert = WeatherAlert.query.get_or_404(alert_id)
    
    db.session.delete(alert)
    db.session.commit()
    
    flash('Alert deleted successfully', 'success')
    return redirect(url_for('admin.alerts'))
