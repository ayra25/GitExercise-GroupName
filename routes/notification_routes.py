from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from models.notification import Notification
from extensions import db
from flask_login import login_required, current_user
from datetime import datetime

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/notifications')
@login_required
def all_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .all()
    return render_template('notifications.html', notifications=notifications)

@notification_bp.route('/notifications/<int:notification_id>')
@login_required
def view_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        abort(403)
    
    if not notification.is_read:
        notification.is_read = True
        db.session.commit()
    
    if notification.notification_type == 'announcement':
        return redirect(url_for('event.events_page', club_id=notification.related_id))
    elif notification.notification_type == 'membership':
        return redirect(url_for('club.dashboard'))
    elif notification.notification_type == 'event':
        return redirect(url_for('event.events_page', club_id=notification.related_id))
    
    return redirect(url_for('notification.all_notifications'))

@notification_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read', 'success')
    return redirect(url_for('notification.all_notifications'))