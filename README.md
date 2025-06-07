# 校园活动管理系统

## 项目简介

这是一个基于 Flask 构建的校园活动社交平台。旨在帮助学生发现、参与和组织校园活动，提供活动发布、报名、评论、用户管理等功能。

## 主要功能

- 用户认证：注册、登录、退出
- 活动管理：
  - 查看活动列表（支持搜索、按类型筛选、按状态筛选）
  - 查看活动详情
  - 创建活动（需登录，管理员可直接发布，普通用户需审核）
  - 编辑和删除活动（仅限组织者或管理员）
  - 报名和退出活动
- 评论系统：在活动详情页发表和查看评论
- 场地管理（管理员权限）：增删改查场地信息
- 活动类型管理（管理员权限）：增删改查活动类型
- 用户管理（管理员权限）：查看用户列表，修改用户权限（设为/取消管理员）
- 个人中心：查看自己发起和参与的活动
- 推荐活动：为登录用户推荐可能感兴趣的活动

## 技术栈

- 后端框架：Flask
- 数据库：MySQL
- 前端：HTML, CSS (Bootstrap 5), JavaScript
- 其他库：Faker

## 安装和运行

### 前置条件

- Python 3.6+
- MySQL 数据库
- pip 包管理器

### 安装步骤

1. 进入项目目录：
   ```bash
   cd campus_activities
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置数据库：
   - 创建一个 MySQL 数据库，例如 `campus_activities`。
   - 设置数据库连接字符串。可以在系统环境变量中设置 `DATABASE_URL`，或者直接修改 `app.py` 中的 `SQLALCHEMY_DATABASE_URI`。
     ```python
     app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@host/campus_activities'
     ```

4. 初始化并迁移数据库：
   ```bash
   flask db init
   flask db migrate -m "initial migration"
   flask db upgrade
   ```
   如果后续模型有修改，只需运行 `flask db migrate -m "migration message"` 和 `flask db upgrade`。

5. 填充初始数据（可选）：
   运行 `seed.py` 脚本来填充一些用户、活动类型、场地和活动数据。
   ```bash
   python seed.py
   ```

6. 运行应用：
   ```bash
   flask run
   ```

### 环境变量

- `SECRET_KEY`: Flask 应用的密钥，用于会话管理和安全性。建议在生产环境中设置一个强密钥。
- `DATABASE_URL`: 数据库连接字符串，格式如 `mysql+pymysql://user:password@host/database`。

## 项目结构

```
.  
├── migrations/         # 数据库迁移脚本
├── templates/          # HTML 模板文件
├── static/             # 静态文件 (CSS, JS, 图片等)
├── app.py              # 主应用文件，包含路由、模型、表单等
├── seed.py             # 数据库填充脚本
├── requirements.txt    # 项目依赖
└── README.md           # 项目说明
```
