from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import Activity, User, Venue, ActivityType
from forms import VenueForm, ActivityTypeForm
from extensions import db

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    search_query = request.args.get('search', '')
    query = User.query
    if search_query:
        query = query.filter(User.username.ilike(f'%{search_query}%'))
    users = query.all()
    return render_template('admin_users.html', users=users, search_query=search_query)

@admin_bp.route('/edit_user_permissions/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user_permissions(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('无法修改您自己的权限', 'warning')
        return redirect(url_for('admin.users'))
    
    # 根据表单数据更新权限
    user.is_admin = request.form.get('is_admin') == 'true'
    user.is_reviewer = request.form.get('is_reviewer') == 'true'
    
    db.session.commit()
    flash(f'用户 {user.username} 的权限已更新', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/venues')
@login_required
@admin_required
def venues():
    venues = Venue.query.all()
    return render_template('admin_venues.html', venues=venues)

@admin_bp.route('/venues/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_venue():
    form = VenueForm()
    if form.validate_on_submit():
        venue = Venue(
            name=form.name.data,
            address=form.address.data,
            capacity=form.capacity.data
        )
        db.session.add(venue)
        db.session.commit()
        flash('场地创建成功！', 'success')
        return redirect(url_for('admin.venues'))
    return render_template('create_venue.html', form=form)

@admin_bp.route('/venues/<int:venue_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(obj=venue)
    if form.validate_on_submit():
        form.populate_obj(venue)
        db.session.commit()
        flash('场地更新成功！', 'success')
        return redirect(url_for('admin.venues'))
    return render_template('edit_venue.html', form=form, venue=venue)

@admin_bp.route('/venues/<int:venue_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    # 检查是否有活动关联到此场地
    if Activity.query.filter_by(venue_id=venue_id).first():
        flash('无法删除场地，存在关联的活动。', 'warning')
    else:
        db.session.delete(venue)
        db.session.commit()
        flash('场地删除成功', 'success')
    return redirect(url_for('admin.venues'))

@admin_bp.route('/activity_types')
@login_required
@admin_required
def activity_types():
    activity_types = ActivityType.query.all()
    return render_template('admin_activity_types.html', activity_types=activity_types)

@admin_bp.route('/activity_types/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_activity_type():
    form = ActivityTypeForm()
    if form.validate_on_submit():
        activity_type = ActivityType(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(activity_type)
        db.session.commit()
        flash('活动类型创建成功！', 'success')
        return redirect(url_for('admin.activity_types'))
    return render_template('create_activity_type.html', form=form)

@admin_bp.route('/activity_types/<int:type_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_activity_type(type_id):
    activity_type = ActivityType.query.get_or_404(type_id)
    form = ActivityTypeForm(obj=activity_type)
    if form.validate_on_submit():
        form.populate_obj(activity_type)
        db.session.commit()
        flash('活动类型更新成功！', 'success')
        return redirect(url_for('admin.activity_types'))
    return render_template('edit_activity_type.html', form=form, activity_type=activity_type)

@admin_bp.route('/activity_types/<int:type_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_activity_type(type_id):
    activity_type = ActivityType.query.get_or_404(type_id)
    # 检查是否有活动关联到此活动类型
    if Activity.query.filter_by(activity_type_id=type_id).first():
        flash('无法删除活动类型，存在关联的活动。', 'warning')
    else:
        db.session.delete(activity_type)
        db.session.commit()
        flash('活动类型删除成功', 'success')
    return redirect(url_for('admin.activity_types')) 