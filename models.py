from datetime import datetime, timezone, timedelta
from flask_login import UserMixin
from extensions import db, bcrypt

# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    department = db.Column(db.String(50))
    interests = db.Column(db.String(200))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    is_admin = db.Column(db.Boolean, default=False)
    is_reviewer = db.Column(db.Boolean, default=False)
    activities = db.relationship('Activity', backref='organizer', lazy=True, foreign_keys='Activity.organizer_id')
    reviewed_activities = db.relationship('Activity', backref='reviewer', lazy=True, foreign_keys='Activity.reviewer_id')
    participations = db.relationship('Participation', backref='user', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

# 活动类型模型
class ActivityType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    activities = db.relationship('Activity', backref='activity_type', lazy=True)

    def __repr__(self):
        return f'<ActivityType {self.name}>'

# 活动模型
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100))
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    max_participants = db.Column(db.Integer)
    current_participants = db.Column(db.Integer, default=0)
    tags = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    review_status = db.Column(db.String(20), default='pending')
    review_comment = db.Column(db.Text)
    review_time = db.Column(db.DateTime(timezone=True))
    poster_url = db.Column(db.String(200))
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    is_approved = db.Column(db.Boolean, default=False)
    comments = db.relationship('Comment', backref='activity', lazy=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
    activity_type_id = db.Column(db.Integer, db.ForeignKey('activity_type.id'))
    likes = db.relationship('Like', backref='activity', lazy=True, cascade="all, delete-orphan")

    @property
    def start_time_cst(self):
        cst = timezone(timedelta(hours=8))
        start_time_utc = self.start_time.replace(tzinfo=timezone.utc) if self.start_time and self.start_time.tzinfo is None else self.start_time
        return start_time_utc.astimezone(cst) if start_time_utc else None

    @property
    def end_time_cst(self):
        cst = timezone(timedelta(hours=8))
        end_time_utc = self.end_time.replace(tzinfo=timezone.utc) if self.end_time and self.end_time.tzinfo is None else self.end_time
        return end_time_utc.astimezone(cst) if end_time_utc else None

    @property
    def created_at_cst(self):
        cst = timezone(timedelta(hours=8))
        created_at_utc = self.created_at.replace(tzinfo=timezone.utc) if self.created_at and self.created_at.tzinfo is None else self.created_at
        return created_at_utc.astimezone(cst) if created_at_utc else None

    @property
    def current_status(self):
        cst = timezone(timedelta(hours=8))
        now_cst = datetime.now(cst)

        if self.start_time_cst and now_cst < self.start_time_cst:
            return '报名中'
        elif self.start_time_cst and self.end_time_cst and self.start_time_cst <= now_cst <= self.end_time_cst:
            return '进行中'
        else:
            return '已结束'

# 活动参与记录
class Participation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'))
    status = db.Column(db.String(20), default='registered')
    registered_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    activity = db.relationship('Activity', backref='participations')

# 评论模型
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    user = db.relationship('User', backref='comments')

# 场地模型
class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer)
    description = db.Column(db.Text)
    activities = db.relationship('Activity', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.name}>'

# 点赞模型
class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))

    # 组合唯一索引，确保一个用户只能给一个活动点赞一次
    __table_args__ = (db.UniqueConstraint('user_id', 'activity_id', name='_user_activity_uc'),) 