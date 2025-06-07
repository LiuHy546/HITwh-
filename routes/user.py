from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, make_response
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from models import Activity, Participation, Comment, Venue, ActivityType
from forms import ActivityForm
from extensions import db
from werkzeug.utils import secure_filename
import random
import os
import csv
import io

user_bp = Blueprint('user', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route('/profile')
@login_required
def profile():
    user_activities = Activity.query.filter_by(organizer_id=current_user.id).all()
    participations = Participation.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', user=current_user, activities=user_activities, participations=participations)

@user_bp.route('/create_activity', methods=['GET', 'POST'])
@login_required
def create_activity():
    form = ActivityForm()
    activity_types = ActivityType.query.all()
    venues = Venue.query.all()
    form.activity_type.choices = [(t.id, t.name) for t in activity_types]
    form.venue.choices = [(v.id, v.name) for v in venues]

    if request.method == 'POST':
        if form.validate_on_submit():
            title = form.title.data
            description = form.description.data
            activity_type_id = form.activity_type.data
            venue_id = form.venue.data
            start_time = form.start_time.data
            end_time = form.end_time.data
            max_participants = form.max_participants.data
            tags = form.tags.data
            poster = request.files.get('poster')

            # 处理海报上传
            poster_url = None
            if poster and poster.filename:
                if not allowed_file(poster.filename):
                    flash('不支持的文件类型', 'warning')
                    return render_template('create_activity.html', form=form, activity_types=activity_types, venues=venues)
                
                filename = secure_filename(poster.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{filename}"
                poster_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                poster.save(poster_path)
                poster_url = url_for('uploaded_file', filename=filename)

            # 验证时间
            if end_time <= start_time:
                flash('结束时间必须晚于开始时间', 'warning')
                return render_template('create_activity.html', form=form, activity_types=activity_types, venues=venues)

            # 验证参与人数
            if max_participants <= 0:
                flash('参与人数必须是正整数', 'warning')
                return render_template('create_activity.html', form=form, activity_types=activity_types, venues=venues)

            # 验证场地容量
            venue = Venue.query.get(venue_id)
            if not venue:
                flash('选择的场地不存在', 'warning')
                return render_template('create_activity.html', form=form, activity_types=activity_types, venues=venues)

            if max_participants > venue.capacity:
                flash(f'活动最大参与人数 ({max_participants}) 超过场地容量 ({venue.capacity})。', 'warning')
                return render_template('create_activity.html', form=form, activity_types=activity_types, venues=venues)

            # 验证场地时间冲突
            conflicting_activities = Activity.query.filter(
                Activity.venue_id == venue_id,
                Activity.start_time < end_time,
                Activity.end_time > start_time
            ).count()

            if conflicting_activities > 0:
                flash('场地在该时间段已被占用，请选择其他时间或场地。', 'warning')
                return render_template('create_activity.html', form=form, activity_types=activity_types, venues=venues)

            # 创建活动
            activity = Activity(
                title=title,
                description=description,
                activity_type_id=activity_type_id,
                venue_id=venue_id,
                start_time=start_time,
                end_time=end_time,
                max_participants=max_participants,
                tags=tags,
                poster_url=poster_url,
                organizer_id=current_user.id,
                status='pending',
                current_participants=0
            )

            # 根据用户角色设置审核状态
            # 无论是谁创建的活动都需要审核员的审核
            activity.review_status = 'pending'
            activity.status = 'pending'
            activity.review_comment = '等待审核员审核'

            db.session.add(activity)
            db.session.commit()

            flash('活动创建成功，等待审核员审核。', 'success')
            return redirect(url_for('user.my_activities'))
        else:
            # 表单验证失败，flash 错误信息并重新渲染表单
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{form[field].label.text}: {error}', 'warning')
    # GET请求显示创建表单 (或 POST 请求验证失败)
    return render_template('create_activity.html', 
                         form=form, 
                         activity_types=activity_types,
                         venues=venues)

@user_bp.route('/activity/<int:activity_id>/join', methods=['POST'])
@login_required
def join_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    
    if activity.current_status != '报名中':
        flash(f'活动当前状态为 \'{activity.current_status}\', 无法报名。', 'warning')
        return redirect(url_for('public.activity_detail', activity_id=activity_id))

    existing_participation = Participation.query.filter_by(
        user_id=current_user.id,
        activity_id=activity_id
    ).first()
    
    if existing_participation:
        flash('您已经参加过这个活动了！', 'warning')
        return redirect(url_for('public.activity_detail', activity_id=activity_id))
    
    if activity.current_participants < activity.max_participants:
        participation = Participation(user_id=current_user.id, activity_id=activity_id)
        activity.current_participants += 1
        db.session.add(participation)
        db.session.commit()
        flash('成功参加活动！', 'success')
    else:
        flash('活动已满！', 'error')
    return redirect(url_for('public.activity_detail', activity_id=activity_id))

@user_bp.route('/activity/<int:activity_id>/comment', methods=['POST'])
@login_required
def add_comment(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    content = request.form.get('content')
    if content:
        comment = Comment(
            content=content,
            user_id=current_user.id,
            activity_id=activity_id,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(comment)
        db.session.commit()
        flash('评论发布成功！', 'success')
    return redirect(url_for('public.activity_detail', activity_id=activity_id))

@user_bp.route('/activity/<int:activity_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_activity(activity_id):
    activity = Activity.query.options(db.joinedload(Activity.venue)).get_or_404(activity_id)
    if activity.organizer_id != current_user.id and not current_user.is_admin:
        abort(403)

    form = ActivityForm(obj=activity)

    venues = Venue.query.all()
    activity_types = ActivityType.query.all()
    form.venue.choices = [(v.id, v.name) for v in venues]
    form.activity_type.choices = [(t.id, t.name) for t in activity_types]

    if request.method == 'GET':
        if activity.venue_id:
            form.venue.data = activity.venue_id
        if activity.activity_type_id:
            form.activity_type.data = activity.activity_type_id

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        venue_id = request.form.get('venue')
        activity_type_id = request.form.get('activity_type')
        max_participants = request.form.get('max_participants')
        tags = request.form.get('tags')

        try:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
            start_time = start_time.replace(tzinfo=timezone(timedelta(hours=8))).astimezone(timezone.utc)
            end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
            end_time = end_time.replace(tzinfo=timezone(timedelta(hours=8))).astimezone(timezone.utc)
            max_participants = int(max_participants)
            venue_id = int(venue_id) if venue_id else None
            activity_type_id = int(activity_type_id) if activity_type_id else None
        except Exception as e:
            flash('表单数据格式有误，请检查输入', 'danger')
            return render_template('edit_activity.html', form=form, activity=activity)

        if venue_id:
            venue = Venue.query.get(venue_id)
            if not venue:
                flash('选择的场地不存在', 'danger')
                return render_template('edit_activity.html', form=form, activity=activity)

            conflicting_activities = Activity.query.filter(
                Activity.venue_id == venue_id,
                Activity.id != activity_id,
                Activity.start_time < end_time,
                Activity.end_time > start_time
            ).count()

            if conflicting_activities > 0:
                flash('场地在该时间段已被占用，请选择其他时间或场地。', 'danger')
                return render_template('edit_activity.html', form=form, activity=activity)

            if max_participants > venue.capacity:
                 flash(f'活动最大参与人数 ({max_participants}) 超过场地容量 ({venue.capacity})。', 'danger')
                 return render_template('edit_activity.html', form=form, activity=activity)

        if activity_type_id:
            activity_type = ActivityType.query.get(activity_type_id)
            if not activity_type:
                flash('选择的活动类型不存在', 'danger')
                return render_template('edit_activity.html', form=form, activity=activity)

        # 处理海报上传
        poster_url = activity.poster_url
        if 'poster' in request.files:
            file = request.files['poster']
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
                filename = f"{timestamp}_{random_str}_{filename}"
                
                # 确保上传目录存在
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                
                # 保存文件
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # 设置海报URL
                poster_url = url_for('uploaded_file', filename=filename)
        # 支持移除海报
        if request.form.get('remove_poster') == '1':
            poster_url = None

        activity.title = title
        activity.description = description
        activity.start_time = start_time
        activity.end_time = end_time
        activity.venue_id = venue_id
        activity.activity_type_id = activity_type_id
        activity.max_participants = max_participants
        activity.tags = tags
        activity.poster_url = poster_url

        db.session.commit()
        flash('活动更新成功！', 'success')
        return redirect(url_for('public.activity_detail', activity_id=activity.id))

    return render_template('edit_activity.html', form=form, activity=activity)

@user_bp.route('/activity/<int:activity_id>/quit', methods=['POST'])
@login_required
def quit_activity(activity_id):
    participation = Participation.query.filter_by(user_id=current_user.id, activity_id=activity_id).first()
    activity = Activity.query.get_or_404(activity_id)
    if participation:
        db.session.delete(participation)
        if activity.current_participants > 0:
            activity.current_participants -= 1
        db.session.commit()
        flash('已成功退出活动', 'info')
    else:
        flash('您未参加该活动', 'warning')
    return redirect(url_for('public.activity_detail', activity_id=activity_id))

@user_bp.route('/activity/<int:activity_id>/delete', methods=['POST'])
@login_required
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    if activity.organizer_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    db.session.delete(activity)
    db.session.commit()
    flash('活动已删除', 'success')
    return redirect(url_for('public.index'))

@user_bp.route('/my_activities')
@login_required
def my_activities():
    # 获取筛选参数
    activity_type_id = request.args.get('activity_type_id', type=int)
    status_filter = request.args.get('status', '')
    venue_id = request.args.get('venue_id', type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # 获取所有类型和场地
    activity_types = ActivityType.query.all()
    venues = Venue.query.all()

    # 我发布的活动筛选 - 显示所有发布的活动
    organized_query = Activity.query.filter_by(organizer_id=current_user.id)
    if activity_type_id:
        organized_query = organized_query.filter_by(activity_type_id=activity_type_id)
    if venue_id:
        organized_query = organized_query.filter_by(venue_id=venue_id)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            organized_query = organized_query.filter(Activity.start_time >= start_dt)
        except Exception:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            organized_query = organized_query.filter(Activity.end_time <= end_dt + timedelta(days=1))
        except Exception:
            pass
    if status_filter:
        now_utc = datetime.now(timezone.utc)
        if status_filter == 'upcoming':
            organized_query = organized_query.filter(Activity.start_time > now_utc)
        elif status_filter == 'ongoing':
            organized_query = organized_query.filter(Activity.start_time <= now_utc, Activity.end_time >= now_utc)
        elif status_filter == 'ended':
            organized_query = organized_query.filter(Activity.end_time < now_utc)
    organized_activities = organized_query.order_by(Activity.start_time.desc()).all()

    # 我参与的活动筛选（只显示未结束或结束时间在一周内的活动）
    participated_query = Activity.query.join(Participation).filter(
        Participation.user_id==current_user.id,
        Activity.organizer_id!=current_user.id
    )
    now_utc = datetime.now(timezone.utc)
    one_week_ago = now_utc - timedelta(days=7)
    participated_query = participated_query.filter(
        (Activity.end_time >= now_utc) | (Activity.end_time >= one_week_ago)
    )
    if activity_type_id:
        participated_query = participated_query.filter(Activity.activity_type_id==activity_type_id)
    if venue_id:
        participated_query = participated_query.filter(Activity.venue_id==venue_id)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            participated_query = participated_query.filter(Activity.start_time >= start_dt)
        except Exception:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            participated_query = participated_query.filter(Activity.end_time <= end_dt + timedelta(days=1))
        except Exception:
            pass
    if status_filter:
        if status_filter == 'upcoming':
            participated_query = participated_query.filter(Activity.start_time > now_utc)
        elif status_filter == 'ongoing':
            participated_query = participated_query.filter(Activity.start_time <= now_utc, Activity.end_time >= now_utc)
        elif status_filter == 'ended':
            participated_query = participated_query.filter(Activity.end_time < now_utc)
    participated_activities = participated_query.order_by(Activity.start_time.desc()).all()

    return render_template(
        'my_activities.html',
        organized_activities=organized_activities,
        participated_activities=participated_activities,
        activity_types=activity_types,
        venues=venues,
        activity_type_id=activity_type_id,
        status_filter=status_filter,
        venue_id=venue_id,
        start_date=start_date,
        end_date=end_date
    )

@user_bp.route('/export_activity_data', methods=['POST'])
@login_required
def export_activity_data():
    activity_id = request.form.get('activity_id')
    if not activity_id:
        flash('请选择要导出的活动', 'warning')
        return redirect(url_for('user.my_activities'))

    # 使用 joinedload 加载评论和用户数据
    activity = Activity.query.options(
        db.joinedload(Activity.comments).joinedload(Comment.user),
        db.joinedload(Activity.participations).joinedload(Participation.user)
    ).get_or_404(activity_id)

    if activity.organizer_id != current_user.id and not current_user.is_admin:
        abort(403)

    # 创建CSV文件
    filename = f"activity_{activity_id}_data.csv"
    response = make_response(generate_csv_data(activity))
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

def generate_csv_data(activity):
    output = io.StringIO()
    writer = csv.writer(output)

    # 活动基本信息
    writer.writerow(['活动基本信息'])
    writer.writerow(['活动ID', activity.id])
    writer.writerow(['标题', activity.title])
    writer.writerow(['描述', activity.description])
    writer.writerow(['类型', activity.activity_type.name if activity.activity_type else ''])
    writer.writerow(['场地', activity.venue.name if activity.venue else ''])
    writer.writerow(['开始时间', activity.start_time.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M') if activity.start_time else ''])
    writer.writerow(['结束时间', activity.end_time.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M') if activity.end_time else ''])
    writer.writerow(['最大参与人数', activity.max_participants])
    writer.writerow(['当前参与人数', activity.current_participants])
    writer.writerow(['标签', activity.tags])
    writer.writerow(['状态', activity.status])
    writer.writerow(['审核状态', activity.review_status])
    writer.writerow(['审核意见', activity.review_comment])
    writer.writerow(['创建时间', activity.created_at.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M') if activity.created_at else ''])
    writer.writerow(['发起人ID', activity.organizer_id])
    writer.writerow(['发起人用户名', activity.organizer.username if activity.organizer else ''])
    writer.writerow(['海报URL', activity.poster_url or ''])
    writer.writerow([])

    # 活动统计
    writer.writerow(['活动统计'])
    likes = activity.likes_count or 0
    comments_count = len(activity.comments)
    participants_count = activity.current_participants or 0
    activity_score = (likes + comments_count) / max(participants_count, 1)
    writer.writerow(['点赞数', likes])
    writer.writerow(['评论数', comments_count])
    writer.writerow(['参与人数', participants_count])
    writer.writerow(['活动评分', f'{activity_score:.2f}'])
    writer.writerow([])

    # 参与用户
    writer.writerow(['参与用户信息'])
    writer.writerow(['用户ID', '用户名', '参与状态', '报名时间'])
    for p in activity.participations:
        writer.writerow([
            p.user.id if p.user else '',
            p.user.username if p.user else '',
            p.status,
            p.registered_at.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M') if p.registered_at else ''
        ])
    writer.writerow([])

    # 评论详情
    writer.writerow(['评论详情'])
    writer.writerow(['评论ID', '用户ID', '用户名', '评论内容', '评论时间', '点赞数'])
    for c in activity.comments:
        writer.writerow([
            c.id,
            c.user.id if c.user else '',
            c.user.username if c.user else '',
            c.content,
            c.created_at.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M') if c.created_at else '',
            c.likes_count or 0
        ])

    return output.getvalue() 