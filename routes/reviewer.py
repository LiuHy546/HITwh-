from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Activity, db, Notification
from datetime import datetime, timezone

reviewer_bp = Blueprint('reviewer', __name__)

@reviewer_bp.before_request
@login_required
def before_request():
    if not current_user.is_reviewer:
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('public.index'))

@reviewer_bp.route('/review/list')
def review_list():
    search_query = request.args.get('search', '')
    
    activities_query = Activity.query.filter_by(review_status='pending')
    
    if search_query:
        activities_query = activities_query.filter(Activity.title.ilike(f'%{search_query}%'))
        
    activities = activities_query.order_by(Activity.created_at.desc()).all()
    
    return render_template('reviewer/list.html', activities=activities, search_query=search_query)

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
            notification_type = 'activity_review'
            review_status_msg = '通过审核'
            review_comment_msg = review_comment if review_comment else '无'
        else:
            activity.status = 'rejected'
            activity.is_approved = False
            notification_type = 'activity_review'
            review_status_msg = '未通过审核'
            review_comment_msg = review_comment if review_comment else '无'
            
        # 创建通知
        notification = Notification(
            user_id=activity.organizer_id,
            activity_id=activity.id,
            notification_type=notification_type,
            activity_title=activity.title,
            review_status=review_status,
            review_comment=review_comment_msg
        )
        db.session.add(notification)
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