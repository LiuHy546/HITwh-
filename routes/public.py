from flask import Blueprint, render_template, request, redirect, url_for, send_file
from flask_login import current_user, login_required
from datetime import datetime, timezone, timedelta
from models import Activity, ActivityType, Participation, Comment, Like, Venue
from extensions import db
from sqlalchemy import true, false
import io
import csv

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    activity_type_id = request.args.get('activity_type_id', type=int)
    hot = request.args.get('hot', '0')
    status_filter = request.args.get('status', '')
    recommend_flag = request.args.get('recommend', '0')
    venue_id = request.args.get('venue_id', type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    recommend_activities = []
    hot_activities = []

    # 推荐逻辑
    if recommend_flag == '1':
        if current_user.is_authenticated:
            participated_activity_ids = [p.activity_id for p in Participation.query.filter_by(user_id=current_user.id).all()]
            participated_activities = Activity.query.filter(Activity.id.in_(participated_activity_ids)).all()
            participated_type_ids = list(set([a.activity_type_id for a in participated_activities if a.activity_type_id]))
            participated_tags = list(set([tag.strip() for a in participated_activities if a.tags for tag in a.tags.split(',') if tag.strip()]))
            # 有参与历史
            if participated_activity_ids:
                recommend_query = Activity.query.filter(
                    Activity.is_approved==True,
                    Activity.status=='active',
                    Activity.start_time > datetime.now(timezone.utc),
                    Activity.id.notin_(participated_activity_ids)
                ).options(db.joinedload(Activity.venue), db.joinedload(Activity.activity_type))
                type_recommendations = recommend_query.filter(
                    Activity.activity_type_id.in_(participated_type_ids)
                )
                tag_recommendations = recommend_query.filter(
                    ~Activity.activity_type_id.in_(participated_type_ids) if participated_type_ids else true(),
                    db.or_(*[Activity.tags.ilike(f'%{t}%') for t in participated_tags]) if participated_tags else false()
                )
                type_recommendations = type_recommendations.order_by(Activity.created_at.desc()).limit(5).all()
                recommended_count = len(type_recommendations)
                if recommended_count < 5:
                    tag_recommendations = tag_recommendations.order_by(Activity.created_at.desc()).limit(5 - recommended_count).all()
                    recommend_activities = type_recommendations + tag_recommendations
                else:
                    recommend_activities = type_recommendations
            else:
                # 新用户推荐热门活动
                now_utc = datetime.now(timezone.utc)
                upcoming_activities = Activity.query.filter(
                    Activity.is_approved==True,
                    Activity.status == 'active',
                    Activity.start_time > now_utc
                ).options(db.joinedload(Activity.comments)).all()
                def calculate_hot_score(activity):
                    like_weight = 2.0
                    comment_weight = 1.5
                    participation_weight = 10.0
                    participation_ratio = activity.current_participants / activity.max_participants if activity.max_participants > 0 else 0
                    likes = activity.likes_count or 0
                    comments = len(activity.comments)
                    hot_score = likes * like_weight + comments * comment_weight + participation_ratio * participation_weight
                    return hot_score
                activities_with_scores = [(activity, calculate_hot_score(activity)) for activity in upcoming_activities]
                recommend_activities = [activity for activity, score in sorted(activities_with_scores, key=lambda item: item[1], reverse=True)[:8]]
        else:
            # 未登录用户推荐热门活动
            now_utc = datetime.now(timezone.utc)
            upcoming_activities = Activity.query.filter(
                Activity.is_approved==True,
                Activity.status == 'active',
                Activity.start_time > now_utc
            ).options(db.joinedload(Activity.comments)).all()
            def calculate_hot_score(activity):
                like_weight = 2.0
                comment_weight = 1.5
                participation_weight = 10.0
                participation_ratio = activity.current_participants / activity.max_participants if activity.max_participants > 0 else 0
                likes = activity.likes_count or 0
                comments = len(activity.comments)
                hot_score = likes * like_weight + comments * comment_weight + participation_ratio * participation_weight
                return hot_score
            activities_with_scores = [(activity, calculate_hot_score(activity)) for activity in upcoming_activities]
            recommend_activities = [activity for activity, score in sorted(activities_with_scores, key=lambda item: item[1], reverse=True)[:8]]
        # 主列表只显示推荐活动
        activities = recommend_activities
        recommend_mode = True
    else:
        recommend_mode = False
        query = Activity.query.filter_by(status='active', is_approved=True)
        query = query.options(db.joinedload(Activity.venue), db.joinedload(Activity.activity_type))
        if search_query:
            query = query.filter(Activity.title.ilike(f'%{search_query}%'))
            activity_type_id = None
            status_filter = ''
        if activity_type_id:
            query = query.filter_by(activity_type_id=activity_type_id)
            hot = '0'
        if venue_id:
            query = query.filter_by(venue_id=venue_id)
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Activity.start_time >= start_dt)
            except Exception:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(Activity.end_time <= end_dt + timedelta(days=1))
            except Exception:
                pass
        now_utc = datetime.now(timezone.utc)
        if status_filter == 'upcoming':
            query = query.filter(Activity.start_time > now_utc)
        elif status_filter == 'ongoing':
            query = query.filter(Activity.start_time <= now_utc, Activity.end_time >= now_utc)
        elif status_filter == 'ended':
            query = query.filter(Activity.end_time < now_utc)
        if hot == '1' and not search_query and not activity_type_id and not status_filter:
            query = query.order_by(Activity.current_participants.desc(), Activity.created_at.desc())
        else:
            query = query.order_by(Activity.start_time.desc())
        activities = query.paginate(page=page, per_page=9)

    cst = timezone(timedelta(hours=8))
    if recommend_mode:
        for activity in activities:
            if activity.start_time:
                start_time_utc = activity.start_time.replace(tzinfo=timezone.utc) if activity.start_time.tzinfo is None else activity.start_time
                activity.display_start_time = start_time_utc.astimezone(cst).strftime('%Y-%m-%d %H:%M')
            else:
                activity.display_start_time = 'N/A'
            if activity.end_time:
                end_time_utc = activity.end_time.replace(tzinfo=timezone.utc) if activity.end_time.tzinfo is None else activity.end_time
                activity.display_end_time = end_time_utc.astimezone(cst).strftime('%Y-%m-%d %H:%M')
            else:
                activity.display_end_time = 'N/A'
            if activity.created_at:
                created_at_utc = activity.created_at.replace(tzinfo=timezone.utc) if activity.created_at.tzinfo is None else activity.created_at
                activity.display_created_at = created_at_utc.astimezone(cst).strftime('%Y-%m-%d %H:%M')
            else:
                activity.display_created_at = 'N/A'
    else:
        for activity in activities.items:
            if activity.start_time:
                start_time_utc = activity.start_time.replace(tzinfo=timezone.utc) if activity.start_time.tzinfo is None else activity.start_time
                activity.display_start_time = start_time_utc.astimezone(cst).strftime('%Y-%m-%d %H:%M')
            else:
                activity.display_start_time = 'N/A'
            if activity.end_time:
                end_time_utc = activity.end_time.replace(tzinfo=timezone.utc) if activity.end_time.tzinfo is None else activity.end_time
                activity.display_end_time = end_time_utc.astimezone(cst).strftime('%Y-%m-%d %H:%M')
            else:
                activity.display_end_time = 'N/A'
            if activity.created_at:
                created_at_utc = activity.created_at.replace(tzinfo=timezone.utc) if activity.created_at.tzinfo is None else activity.created_at
                activity.display_created_at = created_at_utc.astimezone(cst).strftime('%Y-%m-%d %H:%M')
            else:
                activity.display_created_at = 'N/A'

    if current_user.is_authenticated:
        for activity in activities:
            activity.is_joined = Participation.query.filter_by(
                user_id=current_user.id,
                activity_id=activity.id
            ).first() is not None
            # Check if current user has liked the activity
            activity.is_liked = Like.query.filter_by(
                user_id=current_user.id,
                activity_id=activity.id
            ).first() is not None
    
    all_activity_types = ActivityType.query.all()
    all_venues = Venue.query.all()
    
    # 热门活动推荐逻辑
    now_utc = datetime.now(timezone.utc)
    upcoming_activities = Activity.query.filter(
        Activity.is_approved==True,
        Activity.status == 'active',
        Activity.start_time > now_utc
    ).options(db.joinedload(Activity.comments)).all()

    def calculate_hot_score(activity):
        like_weight = 2.0
        comment_weight = 1.5
        participation_weight = 10.0
        participation_ratio = activity.current_participants / activity.max_participants if activity.max_participants > 0 else 0
        likes = activity.likes_count or 0
        comments = len(activity.comments)
        hot_score = likes * like_weight + comments * comment_weight + participation_ratio * participation_weight
        return hot_score, likes, comments, participation_ratio

    activities_with_scores = [
        (activity, *calculate_hot_score(activity)) for activity in upcoming_activities
    ]
    hot_activities = [
        {
            'activity': activity,
            'score': score,
            'likes': likes,
            'comments': comments,
            'participation_ratio': participation_ratio
        }
        for activity, score, likes, comments, participation_ratio in sorted(activities_with_scores, key=lambda item: item[1], reverse=True)[:8]
    ]

    return render_template('index.html', 
                           activities=activities, 
                           search_query=search_query, 
                           activity_type_id=activity_type_id,
                           recommend_activities=[], # 不再传递为你推荐
                           hot=hot,
                           activity_types=all_activity_types,
                           venues=all_venues,
                           is_admin=current_user.is_authenticated and current_user.is_admin,
                           status_filter=status_filter,
                           hot_activities=hot_activities,
                           recommend_mode=recommend_mode,
                           venue_id=venue_id,
                           start_date=start_date,
                           end_date=end_date
                           )

@public_bp.route('/activity/<int:activity_id>')
def activity_detail(activity_id):
    activity = db.session.query(Activity).options(db.joinedload(Activity.venue)).filter_by(id=activity_id).first_or_404()
    db.session.refresh(activity)
    comments = activity.comments
    comments = sorted(comments, key=lambda c: c.created_at, reverse=True)
    cst = timezone(timedelta(hours=8))
    for comment in comments:
        if comment.created_at.tzinfo is None:
            comment.created_at = comment.created_at.replace(tzinfo=timezone.utc)
        comment.created_at = comment.created_at.astimezone(cst)
        comment.display_time = comment.created_at.strftime('%Y-%m-%d %H:%M')
    if not activity.is_approved and (not current_user.is_authenticated or (current_user.id != activity.organizer_id and not current_user.is_admin and not current_user.is_reviewer)):
        abort(403)
    is_joined = False
    if current_user.is_authenticated:
        participation = Participation.query.filter_by(
            user_id=current_user.id,
            activity_id=activity_id
        ).first()
        is_joined = participation is not None
    is_exportable = False
    if activity.end_time:
        now = datetime.now(timezone.utc)
        if activity.end_time.tzinfo is None:
            activity_end_time = activity.end_time.replace(tzinfo=timezone.utc)
        else:
            activity_end_time = activity.end_time
        if (now - activity_end_time).days >= 7:
            is_exportable = current_user.is_authenticated and current_user.id == activity.organizer_id
    return render_template('activity_detail.html', activity=activity, comments=comments, is_joined=is_joined, is_exportable=is_exportable)

@public_bp.route('/activity/<int:activity_id>/like', methods=['POST'])
def like_activity(activity_id):
    # Ensure user is authenticated
    if not current_user.is_authenticated:
        return {'success': False, 'message': '请先登录才能点赞'}, 401

    activity = Activity.query.get_or_404(activity_id)
    
    # Check if user has already liked the activity
    existing_like = Like.query.filter_by(user_id=current_user.id, activity_id=activity_id).first()

    if existing_like:
        # Unlike the activity
        db.session.delete(existing_like)
        activity.likes_count -= 1
        db.session.commit()
        return {'success': True, 'likes': activity.likes_count, 'liked': False}
    else:
        # Like the activity
        new_like = Like(user_id=current_user.id, activity_id=activity_id)
        db.session.add(new_like)
        activity.likes_count += 1
        db.session.commit()
        return {'success': True, 'likes': activity.likes_count, 'liked': True}

@public_bp.route('/activity/<int:activity_id>/export')
@login_required
def export_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    # 只允许发起者导出
    if activity.organizer_id != current_user.id:
        abort(403)
    # 只允许结束超过一周的活动导出
    now = datetime.now(timezone.utc)
    if activity.end_time:
        if activity.end_time.tzinfo is None:
            activity_end_time = activity.end_time.replace(tzinfo=timezone.utc)
        else:
            activity_end_time = activity.end_time
    else:
        activity_end_time = None
    if not activity_end_time or (now - activity_end_time).days < 7:
        flash('活动结束需超过一周才可导出数据', 'warning')
        return redirect(url_for('public.activity_detail', activity_id=activity_id))
    # 导出内容：活动信息+参与用户
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['活动名称', '开始时间', '结束时间', '场地', '类型', '最大人数', '当前人数'])
    writer.writerow([
        activity.title,
        activity.start_time.strftime('%Y-%m-%d %H:%M'),
        activity.end_time.strftime('%Y-%m-%d %H:%M'),
        activity.venue.name if activity.venue else '',
        activity.activity_type.name if activity.activity_type else '',
        activity.max_participants,
        activity.current_participants
    ])
    writer.writerow([])
    writer.writerow(['参与用户ID', '用户名', '报名时间'])
    for p in activity.participations:
        writer.writerow([
            p.user.id,
            p.user.username,
            p.registered_at.strftime('%Y-%m-%d %H:%M')
        ])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'activity_{activity_id}_export.csv'
    ) 