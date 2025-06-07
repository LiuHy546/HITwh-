import importlib
import sys
from datetime import datetime, timedelta, timezone
import random
from faker import Faker
from sqlalchemy import text

# 导入必要的模块
from app import create_app
from extensions import db
from models import User, Activity, Venue, ActivityType, Participation, Comment

fake = Faker('zh_CN')  # 使用中文数据

def make_utc_aware(dt):
    """确保datetime对象是UTC时区感知的"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def get_random_poster_url():
    """预定义的2:1长宽比图片URL（宽度为高度的2倍）"""
    preset_urls = [
        # 晚会类（横幅海报）
        'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop',
        'https://images.unsplash.com/photo-1511578314322-379afb476865?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop',
        
        # 讲座类（横向学术图）
        'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop',
        'https://images.unsplash.com/photo-1524178232363-1fb2b075b655?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop',
        
        # 竞赛类（横向比赛图）
        'https://images.unsplash.com/photo-1547347298-4074fc3086f0?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop',
        'https://images.unsplash.com/photo-1517649763962-0c623066013b?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop',
        
        # 体育类（横向运动图）
        'https://images.unsplash.com/photo-1543351611-58f69d7c1781?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop',
        'https://images.unsplash.com/photo-1521412644187-c49fa049e84d?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop',
        
        # 其他活动（通用横幅）
        'https://images.unsplash.com/photo-1541178735493-479c1a27ed24?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop',
        'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&h=400&fit=crop'
    ]
    return random.choice(preset_urls) if random.random() > 0.2 else None  # 80%概率有海报

def seed_data():
    app = create_app()
    with app.app_context():
        db.create_all()

        # 清空现有数据 (按照依赖关系顺序删除)
        print('清空现有数据...')
        Comment.query.delete()  # 先删除评论
        Participation.query.delete()  # 再删除参与记录
        db.session.execute(text('DELETE FROM likes'))  # 删除点赞记录
        Activity.query.delete()  # 然后删除活动
        Venue.query.delete()  # 删除场地
        User.query.delete()  # 删除用户
        ActivityType.query.delete()  # 最后删除活动类型
        db.session.commit()
        
        print('确保数据库结构已创建...')

        # 创建管理员用户
        if not User.query.filter_by(username='admin').first():
            print('创建管理员...')
            admin = User(
                username='admin',
                email='admin@example.com',
                department='计算机学院',
                is_admin=True,
                created_at=make_utc_aware(datetime.now())
            )
            admin.set_password('admin123')
            db.session.add(admin)

        # 创建审核员用户
        print('创建审核员...')
        reviewers = []
        reviewer_departments = ['学生处', '团委', '教务处']
        for i in range(3):
            reviewer = User(
                username=f'reviewer{i+1}',
                email=f'reviewer{i+1}@example.com',
                department=reviewer_departments[i],
                is_reviewer=True,
                created_at=make_utc_aware(datetime.now())
            )
            reviewer.set_password('reviewer123')
            reviewers.append(reviewer)
            db.session.add(reviewer)

        # 创建更真实的普通用户
        departments = ['计算机学院', '经济学院', '医学院', '文学院', '理学院', '工学院', '法学院', '艺术学院']
        # Ensure at least 50 users exist
        num_users_to_create = 50 - User.query.count()
        if num_users_to_create > 0:
            print(f'创建 {num_users_to_create} 个用户...')
            for i in range(num_users_to_create):
                user = User(
                    username=fake.user_name() + str(random.randint(100, 999)),
                    email=fake.email(),
                    department=random.choice(departments),
                    interests=','.join(random.sample(['编程','阅读','音乐','运动','摄影','旅行','美食','电影'], 3)),
                    created_at=make_utc_aware(fake.date_time_between(start_date='-1y', end_date='now'))
                )
                user.set_password('password123')
                db.session.add(user)

        db.session.commit()

        # 创建活动类型（修改为要求的五类）
        if ActivityType.query.count() == 0:
            print('创建活动类型...')
            activity_types_data = [
                ('晚会', '各类文艺演出和娱乐活动'),
                ('讲座', '学术报告和知识分享活动'),
                ('竞赛', '各类比赛和竞技活动'),
                ('体育', '体育运动和健身活动'),
                ('其他', '其他类型的活动')
            ]
            for name, description in activity_types_data:
                 activity_type = ActivityType(name=name, description=description)
                 db.session.add(activity_type)
            db.session.commit()

        # 创建场地（保持原有场地不变）
        if Venue.query.count() == 0:
             print('创建场地...')
             venues_data = [
                 ('体育馆', '校内体育馆', 500),
                 ('图书馆报告厅', '图书馆附属报告厅', 200),
                 ('学生活动中心', '多功能学生活动场所', 300),
                 ('操场', '学校室外操场', 1000),
                 ('礼堂', '学校大型礼堂', 800),
             ]
             for name, address, capacity in venues_data:
                 venue = Venue(name=name, address=address, capacity=capacity)
                 db.session.add(venue)
             db.session.commit()

        # 获取所有用户、活动类型和场地
        users = User.query.all()
        activity_types = ActivityType.query.all()
        venues = Venue.query.all()
        admin_user = User.query.filter_by(is_admin=True).first()

        # 创建活动 (目标200个活动)
        num_activities_to_create = 200 - Activity.query.count()
        if num_activities_to_create > 0:
            print(f'创建 {num_activities_to_create} 个活动...')

            # 更新活动模板以匹配新的活动类型
            activity_templates = {
                '晚会': [
                    '校园{}晚会', '{}迎新晚会', '{}毕业晚会', '元旦晚会', 
                    '中秋晚会', '十佳歌手大赛', '舞蹈比赛', '才艺展示晚会'
                ],
                '讲座': [
                    '{}学术讲座', '科研方法研讨会', '论文写作指导', 
                    '创新创业论坛', '人工智能前沿', '学术沙龙第{}期',
                    '职业发展讲座', '学科交叉研讨会'
                ],
                '竞赛': [
                    '编程大赛', '数学建模比赛', '电子设计竞赛', '创业大赛', 
                    '演讲比赛', '辩论赛', '知识竞赛', '创新大赛'
                ],
                '体育': [
                    '校园篮球联赛', '足球友谊赛', '羽毛球公开赛', 
                    '乒乓球挑战赛', '春季运动会', '游泳比赛',
                    '校园马拉松', '排球联赛'
                ],
                '其他': [
                    '社团招新', '志愿服务', '校友见面会', '开放日', 
                    '文化节', '美食节', '游园会', '义卖活动'
                ]
            }

            for i in range(num_activities_to_create):
                activity_type = random.choice(activity_types)
                template = activity_templates.get(activity_type.name, activity_templates['其他'])
                title_template = random.choice(template)
                
                if '{}' in title_template:
                    if activity_type.name == '晚会':
                        title = title_template.format(random.choice(['文艺', '迎新', '毕业', '元旦']))
                    elif activity_type.name == '讲座':
                        title = title_template.format(fake.last_name() + '教授')
                    elif activity_type.name == '竞赛':
                        title = title_template
                    elif activity_type.name == '体育':
                        title = title_template
                    else:  # 其他
                        title = title_template
                else:
                    title = title_template

                # 使用fake.text()生成更长的描述
                description = fake.text(max_nb_chars=random.randint(100, 300))
                
                tags = ', '.join(random.sample([
                    activity_type.name, 
                    random.choice(['校园', '学生', '大学']),
                    random.choice(['比赛', '活动', '交流']),
                    random.choice(['2025', '2026', '学期'])
                ], 3))

                now = make_utc_aware(datetime.now())
                status_choice = random.choices(['ended', 'ongoing', 'upcoming'], weights=[0.4, 0.1, 0.5], k=1)[0]
                
                if status_choice == 'ended':
                    duration = random.choices([1, 2, 3, 6, 24], weights=[0.4, 0.3, 0.2, 0.05, 0.05], k=1)[0]
                    end_time = now - timedelta(days=random.randint(1, 180), hours=random.randint(1, 12))
                    start_time = end_time - timedelta(hours=duration)
                elif status_choice == 'ongoing':
                    duration = random.randint(1, 3)
                    start_time = now - timedelta(hours=random.randint(0, duration-1))
                    end_time = start_time + timedelta(hours=duration)
                else:  # upcoming
                    duration = random.choices([1, 2, 3, 6, 24, 48], weights=[0.3, 0.3, 0.2, 0.1, 0.05, 0.05], k=1)[0]
                    start_time = now + timedelta(days=random.randint(1, 60), hours=random.randint(1, 12))
                    end_time = start_time + timedelta(hours=duration)

                # 根据活动类型智能选择场地
                if activity_type.name == '晚会':
                    venue = random.choice([v for v in venues if v.name in ['礼堂', '学生活动中心']])
                elif activity_type.name == '讲座':
                    venue = random.choice([v for v in venues if v.name in ['图书馆报告厅', '礼堂']])
                elif activity_type.name == '竞赛':
                    venue = random.choice([v for v in venues if v.name in ['学生活动中心', '体育馆']])
                elif activity_type.name == '体育':
                    venue = random.choice([v for v in venues if v.name in ['体育馆', '操场']])
                else:  # 其他
                    venue = random.choice([v for v in venues if v.name in ['学生活动中心', '操场']])

                organizer = random.choice(users) if random.random() > 0.1 else admin_user

                max_participants = random.randint(
                    int(venue.capacity * 0.3), 
                    min(int(venue.capacity * 1.1), venue.capacity + 20)
                )
                
                if status_choice == 'ended':
                    current_participants = random.randint(int(max_participants * 0.7), max_participants)
                elif status_choice == 'ongoing':
                    current_participants = random.randint(int(max_participants * 0.3), int(max_participants * 0.8))
                else:  # upcoming
                    current_participants = random.randint(0, int(max_participants * 0.6))

                # 随机选择审核状态
                review_status = random.choices(['pending', 'approved', 'rejected'], weights=[0.2, 0.7, 0.1], k=1)[0]
                reviewer = random.choice(reviewers) if review_status != 'pending' else None
                review_time = make_utc_aware(datetime.now() - timedelta(days=random.randint(1, 30))) if reviewer else None
                review_comment = random.choice([
                    '活动内容符合要求，予以通过。',
                    '活动安排合理，建议通过。',
                    '活动规模适当，予以批准。',
                    '活动内容需要调整，建议修改后重新提交。',
                    '活动规模过大，建议缩小规模。'
                ]) if review_status == 'rejected' else None

                # 使用预设的图片URL
                poster_url = get_random_poster_url()

                activity = Activity(
                    title=title,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    venue_id=venue.id,
                    activity_type_id=activity_type.id,
                    organizer_id=organizer.id,
                    max_participants=max_participants,
                    current_participants=current_participants,
                    tags=tags,
                    status='active' if review_status == 'approved' else 'pending',
                    review_status=review_status,
                    reviewer_id=reviewer.id if reviewer else None,
                    review_time=review_time,
                    review_comment=review_comment,
                    is_approved=(review_status == 'approved'),
                    poster_url=poster_url,
                    likes_count=random.randint(0, 200),
                    created_at=now
                )
                db.session.add(activity)

            db.session.commit()

            # 创建参与记录
            print('创建活动参与记录...')
            activities = Activity.query.all()
            
            for activity in activities:
                potential_participants = [u for u in users if u.id != activity.organizer_id]
                num_participants = min(activity.current_participants, len(potential_participants))
                
                if num_participants > 0:
                    participants = random.sample(potential_participants, num_participants)
                    
                    for user in participants:
                        # 确保注册时间在活动创建时间和开始时间之间
                        registration_start = make_utc_aware(activity.created_at)
                        registration_end = make_utc_aware(activity.start_time if activity.status == 'ended' else datetime.now())
                        
                        # 确保时间范围有效
                        if registration_end > registration_start:
                            registered_at = make_utc_aware(fake.date_time_between(
                                start_date=registration_start,
                                end_date=registration_end
                            ))
                        else:
                            registered_at = make_utc_aware(activity.created_at)

                        participation = Participation(
                            user_id=user.id,
                            activity_id=activity.id,
                            status='registered',
                            registered_at=registered_at
                        )
                        db.session.add(participation)

            db.session.commit()

            # 创建评论
            print('创建评论...')
            for activity in activities:
                num_comments = random.randint(0, 10)
                if num_comments > 0:
                    commenters = random.sample(users, min(num_comments, len(users)))
                    for user in commenters:
                        comment = Comment(
                            content=random.choice([
                                '活动很棒，期待下次参与！',
                                '组织得很好，收获很多。',
                                '活动安排很合理，体验很好。',
                                '希望能多举办类似的活动。',
                                '活动很有意义，感谢组织者。'
                            ]),
                            user_id=user.id,
                            activity_id=activity.id,
                            created_at=make_utc_aware(fake.date_time_between(
                                start_date=activity.created_at,
                                end_date=datetime.now()
                            ))
                        )
                        db.session.add(comment)

            db.session.commit()

        print(f'数据库填充完毕。总活动数: {Activity.query.count()}, 总用户数: {User.query.count()}, 总参与记录数: {Participation.query.count()}')

        print(f'数据库填充完毕。总活动数: {Activity.query.count()}, 总用户数: {User.query.count()}, 总参与记录数: {Participation.query.count()}, 总评论数: {Comment.query.count()}')

if __name__ == '__main__':
    seed_data()