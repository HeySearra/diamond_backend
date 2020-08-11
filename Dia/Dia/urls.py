from django.urls import path, re_path
from django.views.generic import TemplateView


from user.views import *

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html"), name='index'),
    
    # 通用（信息）
    path('index/statistics_card', StatisticsCard.as_view(), name='index_statistics_card'),  # 简易数据卡片统计的内容（都统计昨日新增的）
    path('simple_user_info', SimpleUserInfo.as_view(), name='simple_user_info'),  # 用户简单信息
    
    # 登录/注册
    path('login/submit', Login.as_view(), name='login_submit'),  # 登录
    path('register/submit', Register.as_view(), name='register_submit'),  # 注册
    path('login/submit', Login.as_view(), name='login_submit'),  # 注销登录，同登录


    # 管理中心数据中心
    path('create/data/all', UserAllData.as_view(), name='create_data_all'),  # 请求汇总数据
    
    # 管理中心详情页
    path('side/user_info', SideUserInfo.as_view(), name='side_user_info'),  # 侧边栏用户卡片

    
    # 管理中心评论

    
    # 管理中心个人设置
    path('member/apply', Member.as_view(), name='member_apply'),  # 申请成为会员
    # path('member/apply', Member.as_view(), name='member_apply'),  # 获取会员信息，同上
    path('user/info', UserInfo.as_view(), name='user_in'),  # 获取个人信息
    path('user/change_account', ChangeAccount.as_view(), name='user_change_account'),  # 修改邮箱
    path('user/change_password', ChangePassword.as_view(), name='user_change_password'),  # 修改密码
    path('user/info_card', UserInfoCard.as_view(), name='user_info_card'),  # 获取个人主页信息
    path('user/change_profile', ChangeProfile.as_view(), name=''),
    
    # 管理中心关注和粉丝
    path('data/fans_and_follows', FansAndFollows.as_view(), name='data_fans_and_follows'),  # 获取某用户关注和粉丝的数量
    path('create/follow', FollowList.as_view(), name='create_follow'),  # 获取关注列表
    path('create/fans', FanList.as_view(), name='create_fans'),  # 获取粉丝列表
    path('create/follow', FollowList.as_view(), name='create_foll'),  # 关注或取关，同上
    
    re_path(r'.*', TemplateView.as_view(template_name='index.html')),
]

