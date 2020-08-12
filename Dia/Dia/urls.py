from django.urls import path, re_path
from django.views.generic import TemplateView


from user.views import *
from teamwork.views import *

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html"), name='index'),

    # 通用（信息）
    path('simple_user_info', SimpleUserInfo.as_view(), name='simple_user_info'),  # 用户简单信息

    # 登录/注册
    path('user/login/submit', Login.as_view(), name='login_submit'),  # 登录
    path('user/register/submit', Register.as_view(), name='register_submit'),  # 注册
    path('user/login/submit', Login.as_view(), name='login_submit'),  # 注销登录，同登录

    # 管理中心个人设置
    # path('member/apply', Member.as_view(), name='member_apply'),  # 申请成为会员
    # path('member/apply', Member.as_view(), name='member_apply'),  # 获取会员信息，同上
    path('user/info', UserInfo.as_view(), name='user_in'),  # 获取个人信息
    path('user/change_password', ChangePwd.as_view(), name='user_change_password'),  # 修改密码
    path('user/change_profile', ChangeProfile.as_view(), name=''),
    
    re_path(r'.*', TemplateView.as_view(template_name='index.html')),
]

