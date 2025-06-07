from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Activity, db
from datetime import datetime, timezone

reviewer_bp = Blueprint('reviewer', __name__)

@reviewer_bp.before_request
@login_required
def before_request():
    if not current_user.is_reviewer and not current_user.is_admin:
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('public.index'))

@reviewer_bp.route('/review/list')
def review_list():
    activities = Activity.query.filter_by(review_status='pending').all()
    return render_template('reviewer/list.html', activities=activities)

@reviewer_bp.route('/review/<int:activity_id>', methods=['GET', 'POST'])
def review_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    
    if request.method == 'POST':
        review_status = request.form.get('review_status')
        review_comment = request.form.get('review_comment')
        
        activity.review_status = review_status
        activity.review_comment = review_comment
        activity.review_time = datetime.now(timezone.utc)
        activity.reviewer_id = current_user.id
        
        if review_status == 'approved':
            activity.status = 'active'
            activity.is_approved = True
        else:
            activity.status = 'rejected'
            activity.is_approved = False
            
        db.session.commit()
        flash('审核完成', 'success')
        return redirect(url_for('reviewer.review_list'))
        
    return render_template('reviewer/review.html', activity=activity)

@reviewer_bp.route('/review/history')
def review_history():
    activities = Activity.query.filter(
        Activity.reviewer_id == current_user.id,
        Activity.review_status != 'pending'
    ).all()
    return render_template('reviewer/history.html', activities=activities) 