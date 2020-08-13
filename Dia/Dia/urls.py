from django.urls import path, re_path
from django.views.generic import TemplateView

from user.views import *
from teamwork.views import *

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html"), name='index'),

    # 通用（信息）
    path('simple_user_info', SimpleUserInfo.as_view(), name='simple_user_info'),  # 用户简单信息

    # 登录/注册
    path('login/submit', Login.as_view(), name='login_submit'),  # 登录
    path('register/submit', Register.as_view(), name='register_submit'),  # 注册
    path('login/submit', Login.as_view(), name='login_submit'),  # 注销登录，同登录

    # 管理中心个人设置
    # path('member/apply', Member.as_view(), name='member_apply'),  # 申请成为会员
    # path('member/apply', Member.as_view(), name='member_apply'),  # 获取会员信息，同上
    # path('user/info', UserInfo.as_view(), name='user_in'),  # 获取个人信息
    path('user/change_password', ChangePwd.as_view(), name='user_change_password'),  # 修改密码
    # path('user/change_profile', ChangeProfile.as_view(), name=''),

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

    re_path(r'.*', TemplateView.as_view(template_name='index.html')),
]
