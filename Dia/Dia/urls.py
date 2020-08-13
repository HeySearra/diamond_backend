from django.urls import path, re_path
from django.views.generic import TemplateView

from user.views import *
from teamwork.views import *

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html"), name='index'),

    # 通用（信息）
    path('user_info', UserInfo.as_view(), name='user_info'),  # 用户信息
    path('search_user', SearchUser.as_view(), name='search_user'),  # 关键词搜索用户
    path('user/edit_info', EditInfo.as_view(), name='edit_info'),  # 修改个人信息

    # 登录/注册
    path('user/login/submit', Login.as_view(), name='login_submit'),  # 登录
    path('user/register/submit', Register.as_view(), name='register_submit'),  # 注册和请求注册验证码
    path('user/logout/submit', Login.as_view(), name='logout_submit'),  # 注销登录
    path('user/forget/send_email', FindPwd.as_view(), name='forget_send_email'),  # 找回密码
    path('user/forget/set_pwd', SetPwd.as_view(), name='forget_set_pwd'),  # 找回密码设置新密码

    # 管理中心个人设置
    path('user/change_password', ChangePwd.as_view(), name='user_change_password'),  # 修改密码
    path('user/change_profile', ChangeProfile.as_view(), name='user_change_profile'),

    # 消息
    path('msg/unread_count', UnreadCount.as_view(), name='msg_unread_count'),
    path('msg/list/', AskMessageList.as_view(), name='msg_list'),
    path('msg/info/', AskMessageInfo.as_view(), name='msg_info'),
    path('msg/ar', SetMsgRead.as_view(), name='msg_ar'),
    path('msg/ar_all', SetAllMsgRead.as_view(), name='msg_ar_all'),
    path('msg/dnd', SetDnd.as_view(), name='msg_dnd'),  # 设置及查询消息免打扰

    # 团队相关
    path('team/new_from_fold', NewFromFold.as_view(), name='team_new_from_fold'),
    path('team/invitation', Invitation.as_view(), name='team_invitation'),
    path('team/auth', Auth.as_view(), name='team_auth'),
    path('team/remove', Remove.as_view(), name='team_remove'),
    path('team/info', Info.as_view(), name='team_info'),
    path('team/delete', Delete.as_view(), name='team_delete'),
    path('team/new', New.as_view(), name='team_new'),
    path('team/edit_info', EditInfo.as_view(), name='team_edit_info'),
    path('team/all', All.as_view(), name='team_all'),

    path('user/change_profile', ChangeProfile.as_view(), name=''),

    re_path(r'.*', TemplateView.as_view(template_name='index.html')),
]

