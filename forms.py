from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateTimeField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo

# 登录表单
class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

# 注册表单
class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    department = StringField('院系', validators=[DataRequired()])
    submit = SubmitField('注册')

# 场地表单
class VenueForm(FlaskForm):
    name = StringField('场地名称', validators=[DataRequired(), Length(max=100)])
    address = StringField('地址', validators=[DataRequired(), Length(max=200)])
    capacity = IntegerField('容量', validators=[DataRequired()])
    submit = SubmitField('保存场地')

# 活动表单
class ActivityForm(FlaskForm):
    title = StringField('活动标题', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('活动描述', validators=[DataRequired()])
    start_time = DateTimeField('开始时间', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeField('结束时间', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    venue = SelectField('选择场地', validators=[DataRequired()], coerce=int)
    activity_type = SelectField('活动类型', validators=[DataRequired()], coerce=int)
    max_participants = IntegerField('最大参与人数', validators=[DataRequired()])
    tags = StringField('标签', validators=[DataRequired()])
    poster = FileField('活动海报', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], '只允许上传jpg、jpeg或png格式的图片！')
    ])
    submit = SubmitField('创建活动')

# 活动类型表单
class ActivityTypeForm(FlaskForm):
    name = StringField('类型名称', validators=[DataRequired(), Length(max=50)])
    description = StringField('类型描述', validators=[Length(max=200)])
    submit = SubmitField('保存类型') 