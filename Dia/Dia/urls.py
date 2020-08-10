from django.urls import path, re_path
from django.views.generic import TemplateView

from mainpage.views import *
from user.views import *
from resource.views import *
from article.views import *

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html"), name='index'),
    
    # 通用（信息）
    path('index/statistics_card', StatisticsCard.as_view(), name='index_statistics_card'),  # 简易数据卡片统计的内容（都统计昨日新增的）
    path('article_view_card?atc_num=(num)', ArticleViewCard.as_view(), name='article_view_card?atc_num=(num)'),  # 浏览量卡片的内容
    path('simple_user_info', SimpleUserInfo.as_view(), name='simple_user_info'),  # 用户简单信息
    
    # 登录/注册
    path('login/submit', Login.as_view(), name='login_submit'),  # 登录
    path('register/submit', Register.as_view(), name='register_submit'),  # 注册
    path('login/submit', Login.as_view(), name='login_submit'),  # 注销登录，同登录
    path('login/message', GetMessage.as_view()),
    path('login/news', GetNews.as_view()),
    
    # 主页
    path('index/recommend', RecommendArticles.as_view(), name='index_recommend'),  # 请求推荐文章列表（疑问：游客跟用户的推荐方式有区别）
    path('index/recommend/like', LikeRecommend.as_view(), name='index_recommend'),  # 请求推荐文章列表（疑问：游客跟用户的推荐方式有区别）
    path('index/recommend/dislike', DisLikeRecommend.as_view(), name='index_recommend'),  # 请求推荐文章列表（疑问：游客跟用户的推荐方式有区别）
    path('base/article_view', ArticleView.as_view(), name='base_article_view'),  # 请求文章条目（浏览）
    path('base/resource_view', ResourceView.as_view(), name='base_resource_view'),  # 请求资源条目（浏览）
    path('index/hot', HotArticles.as_view(), name='hot'),  # 热门文章
    path('side/hot_tags', HotDogs.as_view(), name='side_hot_tags'),  # 热门标签
    path('side/hot_tags/info', ElementsWithTag.as_view(), name='side_hot_tags_info'),  # 某个标签的所有文章/资源
    path('search/main', SearchMain.as_view(), name='search_main'),  # 搜索主内容
    
    # 管理中心博文
    path('create/article/list', ArticleList.as_view(), name='create_article_list'),  # 请求用户的文章列表
    path('create/article/article_edit', ArticleInfoForEdit.as_view(), name='create_article_article_edit'),  # 请求文章条目（编辑）
    path('edit/submit', EditOrSubmitArticle.as_view(), name='edit_submit'),  # 发布或编辑文章
    path('create/article/delete', DelArticle.as_view(), name='create_article_delete'),  # 删除文章（放入回收站）
    path('create/article/top', TopArticle.as_view(), name='create_article_top'),  # 置顶文章
    path('create/special/list', ColumnList.as_view(), name='create_special_list'),  # 请求专栏列表
    path('create/special/info', ColumnArticle.as_view(), name='create_special_info'),  # 请求专栏中的文章
    path('create/special/info_for_edit', ArticleInColumn.as_view(), name='create_special_info_for_edit'),  # 请求用于编辑专栏的文章列表
    path('create/special/edit', EditColumn.as_view(), name='create_special_edit'),  # 编辑专栏内容
    path('create/special/rename', RenameColumn.as_view(), name='create_special_rename'),  # 编辑专栏名称
    path('create/special/new', NewColumn.as_view(), name='create_special_new'),  # 新建专栏
    path('create/special/delete', DelColumn.as_view(), name='create_special_delete'),  # 删除专栏
    path('create/recycle/list', RecycleList.as_view(), name='create_recycle_list'),  # 请求回收站的文章列表
    path('create/recycle/article_recycle', ArticleRecycle.as_view(), name='create_recycle_article_recycle'),  # 请求文章条目（回收站）
    path('create/recycle/recover', Recover.as_view(), name='create_recycle_recover'),  # 恢复回收站的文章
    path('create/recycle/delete', DelRecycle.as_view(), name='create_recycle_delete'),  # 彻底删除文章
    path('edit/image', UploadImage.as_view(), name='edit_image'),  # 上传文章图片
    path('article/relative', RelativeArticle.as_view(), name='relative_article'),

    # 管理中心资源
    path('create/resource/upload_limit', ResourceUploadLimit.as_view(), name='create_resource_upload_limit'),  # 请求资源的上传大小上限
    path('create/resource/upload_file', ResourceUploadFile.as_view(), name='create_resource_upload_file'),  # 上传资源文件
    path('create/resource/new', ResourceNew.as_view(), name='create_resource_new'),  # 上传或编辑资源文件信息
    path('resource/download', DownloadResource.as_view(), name='resource_downlo'),  # 下载资源
    path('create/resource/upload_list', ResourceUploadList.as_view(), name='create_resource_upload_list'),  # 获取已上传的资源列表
    path('create/resource/edit', ResourceInfoForEdit.as_view(), name='create_resource_edit'),  # 请求资源条目（编辑）
    path('create/resource/download_list', ResourceDownloadList.as_view(), name='create_resource_download_list'),  # 获取已购买的资源列表
    path('create/resource/delete', ResourceDelete.as_view(), name='create_resource_delete'),  # 删除资源
    path('resource/relative', RelativeResource.as_view(), name='relative_resource'),

    # 管理中心收藏夹
    path('collection/list', CollectionList.as_view(), name='collection_list'),  # 获取收藏夹列表
    path('collection/info', CollectionInfo.as_view(), name='collection_info'),  # 获取收藏夹中的详细内容
    path('collection/add_article', CollectArticle.as_view(), name='collection_add_article'),  # 添加文章到收藏夹中
    path('collection/add_resource', CollectResource.as_view(), name='collection_add_resource'),  # 添加资源到收藏夹中
    path('collection/remove_article', CollectionRemoveArticle.as_view(), name='collection_remove_article'),  # 取消收藏
    path('collection/remove_resource', CollectionRemoveResource.as_view(), name='collection_remove_resource'),  # 取消收藏
    path('collection/new', CollectionNew.as_view(), name='collection_new'),  # 新建收藏夹
    path('collection/rename', CollectionRename.as_view(), name='collection_rename'),  # 重命名收藏夹
    path('collection/condition', CollectionCondition.as_view(), name='collection_condition'),  # 设置收藏夹可见
    path('collection/delete', CollectionDelete.as_view(), name='collection_delete'),  # 删除收藏夹
    path('collection/move_article', CollectionMoveArticle.as_view(), name='collection_move_article'),  # 转移文章到另外一个收藏夹中
    path('collection/move_resource', CollectionMoveResource.as_view(), name='collection_move_resource'),  # 转移资源到另外一个收藏夹中
    
    # 管理中心积分
    path('create/point/list', PointDetailedList.as_view(), name='create_point_list'),  # 获取积分明细条目
    
    # 管理中心数据中心
    path('create/data/all', UserAllData.as_view(), name='create_data_all'),  # 请求汇总数据
    
    # 管理中心详情页
    path('side/user_info', SideUserInfo.as_view(), name='side_user_info'),  # 侧边栏用户卡片
    path('article/all', ArticleInfo.as_view(), name='article_all'),  # 获取文章详情
    path('resource/all', ResourceInfo.as_view(), name='resource_all'),  # 获取资源详情
    path('article/comment', GetArticleComment.as_view(), name='article_comment'),  # 请求该文章下的评论
    path('resource/comment', GetResourceComment.as_view(), name='resource_comment'),  # 请求该资源下的所有评论
    path('article/like', LikeArticle.as_view(), name='article_like'),  # 点赞/取消点赞文章
    path('resource/like', LikeResource.as_view(), name='resource_like'),  # 点赞/取消点赞资源
    path('article/complain', ComplainArticle.as_view(), name='article_complain'),  # 举报文章
    path('resource/complain', ComplainResource.as_view(), name='resource_complain'),  # 举报资源
    
    # 管理中心评论
    path('article/comment/all', ArticleCommentInfo.as_view(), name='comment_all'),  # 请求评论详情（写了两个）
    path('resource/comment/all', ResourceCommentInfo.as_view(), name='comment_all'),  # 请求评论详情（写了两个）
    path('article/comment/submit', SubmitArticleComment.as_view(), name='article_comment_submit'),  # 发表文章评论
    path('resource/comment/submit', SubmitResourceComment.as_view(), name='resource_comment_submit'),  # 发表资源评论
    path('article/comment/delete', DelArticleComment.as_view(), name='comment_delete'),  # 删除评论
    path('resource/comment/delete', DelResourceComment.as_view(), name='comment_delete'),  # 删除评论
    path('article/comment/like', LikeArticleComment.as_view(), name='comment_like'),  # 点赞 / 取消点赞评论
    path('resource/comment/like', LikeResourceComment.as_view(), name='comment_like'),  # 点赞 / 取消点赞评论
    path('article/comment/complain', ComplainArticleComment.as_view(), name='comment_complain'),  # 举报评论
    path('resource/complain', ComplainResourceComment.as_view(), name='comment_complain'),  # 举报评论
    
    # 管理中心个人设置
    path('member/apply', Member.as_view(), name='member_apply'),  # 申请成为会员
    # path('member/apply', Member.as_view(), name='member_apply'),  # 获取会员信息，同上
    path('user/info', UserInfo.as_view(), name='user_in'),  # 获取个人信息
    path('user/change_account', ChangeAccount.as_view(), name='user_change_account'),  # 修改邮箱
    path('user/change_password', ChangePassword.as_view(), name='user_change_password'),  # 修改密码
    path('user/complain', ComplainUser.as_view(), name='user_complain'),  # 举报用户
    path('user/info_card', UserInfoCard.as_view(), name='user_info_card'),  # 获取个人主页信息
    path('user/change_profile', ChangeProfile.as_view(), name=''),
    
    # 管理中心关注和粉丝
    path('data/fans_and_follows', FansAndFollows.as_view(), name='data_fans_and_follows'),  # 获取某用户关注和粉丝的数量
    path('create/follow', FollowList.as_view(), name='create_follow'),  # 获取关注列表
    path('create/fans', FanList.as_view(), name='create_fans'),  # 获取粉丝列表
    path('create/follow', FollowList.as_view(), name='create_foll'),  # 关注或取关，同上
    
    re_path(r'.*', TemplateView.as_view(template_name='index.html')),
]

