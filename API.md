# 校园活动社交平台 - 路由文档

本文档列出了校园活动社交平台的主要网页路由及其功能说明。

## 公共路由 (无需登录)

| 路由          | HTTP 方法 | 功能描述                                       | 备注                                       |
|---------------|-----------|------------------------------------------------|--------------------------------------------|
| `/`           | `GET`     | 首页，显示活动列表（支持搜索、筛选、排序）       |                                            |
| `/login`      | `GET`, `POST` | 用户登录页面和处理登录请求                 | GET 显示登录表单，POST 处理提交的表单      |
| `/register`   | `GET`, `POST` | 用户注册页面和处理注册请求               | GET 显示注册表单，POST 处理提交的表单      |
| `/activity/<int:activity_id>` | `GET` | 显示特定活动的详细信息和评论              | `<int:activity_id>` 为活动ID             |

## 用户路由 (需登录)

| 路由          | HTTP 方法 | 功能描述                        | 备注                                       |
|---------------|-----------|---------------------------------|--------------------------------------------|
| `/logout`     | `GET`     | 用户退出登录                    |                                            |
| `/profile`    | `GET`     | 用户个人中心，显示发起和参与的活动 |                                            |
| `/activity/create` | `GET`, `POST` | 创建新活动页面和处理创建请求 | GET 显示创建表单，POST 处理提交的表单      |
| `/activity/<int:activity_id>/join` | `POST` | 报名参加活动                     | 需要活动ID                                  |
| `/activity/<int:activity_id>/comment` | `POST` | 为活动添加评论                   | 需要活动ID                                  |
| `/activity/<int:activity_id>/edit` | `GET`, `POST` | 编辑活动页面和处理编辑请求     | 需要活动ID，仅限组织者或管理员           |
| `/activity/<int:activity_id>/quit` | `POST` | 退出参加活动                     | 需要活动ID                                  |
| `/activity/<int:activity_id>/delete` | `POST` | 删除活动                         | 需要活动ID，仅限组织者或管理员           |
| `/my_activities` | `GET`     | 显示当前用户发起和参与的活动列表 |                                            |

## 管理员路由 (需管理员权限)

| 路由                      | HTTP 方法 | 功能描述                                   | 备注                      |
|---------------------------|-----------|--------------------------------------------|---------------------------|
| `/admin_dashboard`        | `GET`     | 管理员仪表盘，显示待审核活动等信息         |                           |
| `/admin/approve_activity/<int:activity_id>` | `POST` | 审核通过活动                               | 需要活动ID                |
| `/admin/users`            | `GET`     | 用户管理页面，列出所有用户（支持搜索）       |                           |
| `/admin/edit_user_permissions/<int:user_id>` | `POST` | 修改用户的管理员权限（设为/取消管理员）   | 需要用户ID，不能修改自身权限 |
| `/admin/venues`           | `GET`     | 场地管理页面，列出所有场地                 |                           |
| `/admin/venues/new`       | `GET`, `POST` | 创建新场地页面和处理创建请求           |                           |
| `/admin/venues/<int:venue_id>/edit` | `GET`, `POST` | 编辑场地页面和处理编辑请求         | 需要场地ID                |
| `/admin/venues/<int:venue_id>/delete` | `POST` | 删除场地                                   | 需要场地ID                |
| `/admin/activity_types`   | `GET`     | 活动类型管理页面，列出所有活动类型         |                           |
| `/admin/activity_types/new` | `GET`, `POST` | 创建新活动类型页面和处理创建请求       |                           |
| `/admin/activity_types/<int:type_id>/edit` | `GET`, `POST` | 编辑活动类型页面和处理编辑请求     | 需要活动类型ID            |
| `/admin/activity_types/<int:type_id>/delete` | `POST` | 删除活动类型                               | 需要活动类型ID            |

## 错误处理路由

| 路由    | HTTP 方法 | 功能描述   |
|---------|-----------|------------|
| `404`   | `GET`     | 页面未找到 |
| `500`   | `GET`     | 服务器内部错误 | 