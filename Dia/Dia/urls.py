from django.urls import path, re_path
from django.views.generic import TemplateView

from user.views import *
from entity.views import *
from record.views import *
from fusion.views import *
from misc.views import *
from teamwork.views import *
from chat.views import *

# add for ckeditor image upload
import os
from django.conf.urls import url
from django.views import static
from Dia import settings

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html"), name='index'),

    # 用户通用
    path('user_info', UserInfo.as_view(), name='user_info'),  # 用户信息
    path('search_user', SearchUser.as_view(), name='search_user'),  # 关键词搜索用户
    path('user/edit_info', UserEditInfo.as_view(), name='edit_info'),  # 修改个人信息
    path('user/user_info', GetUserInfo.as_view(), name='get_user_info'),

    # 用户登录注册找回密码
    path('user/login/submit', Login.as_view(), name='login_submit'),  # 登录
    path('user/register/submit', Register.as_view(), name='register_submit'),  # 注册和请求注册验证码
    path('user/logout/submit', Login.as_view(), name='logout_submit'),  # 注销登录
    path('user/forget/send_email', FindPwd.as_view(), name='forget_send_email'),  # 找回密码
    path('user/forget/set_pwd', ForgetSetPwd.as_view(), name='forget_set_pwd'),  # 找回密码设置新密码
    path('user/set_pwd', SetPwd.as_view(), name='user_set_pwd'),  # 修改密码
    path('upload/port', ChangeProfile.as_view(), name='user_change_profile'),

    # 消息
    path('msg/unread_count', UnreadCount.as_view(), name='msg_unread_count'),
    path('msg/list', AskMessageList.as_view(), name='msg_list'),
    path('msg/info', AskMessageInfo.as_view(), name='msg_info'),
    path('msg/ar', SetMsgRead.as_view(), name='msg_ar'),
    path('msg/ar_all', SetAllMsgRead.as_view(), name='msg_ar_all'),
    path('msg/dnd', SetDnd.as_view(), name='msg_dnd'),  # 设置及查询消息免打扰

    # 文档编辑
    path('document/auth', DocAuth.as_view(), name='document_auth'),
    path('document/edit', DocEdit.as_view(), name='document_edit'),
    path('document/all', DocAll.as_view(), name='document_all'),
    path('document/info', DocInfo.as_view(), name='document_info'),
    path('document/lock', DocLock.as_view(), name='document_lock'),
    path('document/comment/get_users', CommentGetUsers.as_view(), name='document_comment_users'),
    path('document/comment/get_comments_of_thread', CommentGetCommentsOfThread.as_view(), name='doc_comment_get_comments_of_thread'),
    path('document/comment/add', CommentAdd.as_view(), name='document_comment_add'),
    path('document/comment/update', CommentUpdate.as_view(), name='document_comment_update'),
    path('document/comment/remove', CommentRemove.as_view(), name='document_comment_remove'),
    path('document/share', AddShare.as_view(), name='add_read_auth'),
    # path('document/add_comment', AddCommentAuth.as_view(), name='add_comment_auth'),
    # path('document/add_write', AddWriteAuth.as_view(), name='add_write_auth'),
    path('document/online', DocumentOnline.as_view(), name='online'),
    path('document/ver_condition', VersionQuery.as_view(), name='version_query'),
    path('document/history', DocumentHistory.as_view(), name='document_history'),

    # 文件系统 -- 工作台
    path('workbench/recent', WorkbenchRecentView.as_view(), name='workbench_recent_view'),
    path('workbench/star', WorkbenchStar.as_view(), name='workbench_star'),
    path('workbench/create', WorkbenchCreate.as_view(), name='workbench_create'),
    path('workbench/share', WorkbenchShare.as_view(), name='workbench_share'),
    path('workbench/search', WorkbenchSearch.as_view(), name='workbench_search'),

    # 文件系统 -- 文件夹系统
    path('fs/new', FSNew.as_view(), name='fs_new'), # 请求新建文件or夹
    path('fs/fold/elem', FSFoldElem.as_view(), name='fs_fold_elem'), # 请求文件夹下的所有条目
    path('fs/recycle/elem', FSRecycleElem.as_view(), name='fs_recycle_elem'), # 请求回收站下的所有条目
    path('fs/father', FSFather.as_view(), name='fs_father'), # 请求文件or夹的上级文件夹
    path('fs/doc/info', FSDocInfo.as_view(), name='fs_doc_info'), # 请求文档预览信息（弹窗）
    path('fs/fold/info', FSFoldInfo.as_view(), name='fs_fold_info'), # 请求文件夹预览信息（弹窗）
    path('fs/rename', FSRename.as_view(), name='fs_rename'), # 修改文件 / 文件夹名称（重命名）
    path('fs/link/new', FSLinkNew.as_view(), name='fs_link_new'), # 请求新建快捷方式到桌面
    path('fs/move', FSMove.as_view(), name='fs_move'), # 移动文档或文件夹
    path('fs/copy', FSCopy.as_view(), name='fs_copy'), # 复制文档
    path('fs/delete', FSDelete.as_view(), name='fs_delete'), # 删除文档or文件夹
    path('fs/delete_link', FSDeleteLink.as_view(), name='fs_delete_link'), # 从桌面移除快捷方式
    path('fs/star', FSStar.as_view(), name='fs_star'), # 收藏文件or夹
    path('fs/user/root', FSUserRoot.as_view(), name='fs_user_root'), # 请求个人根文件夹fid
    path('fs/team/root', FSTeamRoot.as_view(), name='fs_team_root'), # 请求团队根文件夹fid
    path('fs/recycle/recover', FSRecycleRecover.as_view(), name='fs_recycle_recover'), # 恢复回收站的内容
    path('fs/recycle/delete', FSRecycleDelete.as_view(), name='fs_recycle_delete'), # 彻底删除回收站的内容
    path('fs/recycle/clear', FSRecycleClear.as_view(), name='fs_recycle_clear'), # 彻底删回收站库
    path('fs/star_condition', FSStarCondition.as_view(), name='fs_star_condition'),
    path('fs/share_link', FSShareKey.as_view(), name='fs_share_key'), # 请求分享内容
    path('fs/share_change_auth', ChangeShareAuth.as_view(), name="fs_share_change_auth"),
    path('fs/share_reset', ResetKey.as_view(), name='reset_key'),
    path('fs/share_dtd_list', AuthFileList.as_view(), name='reset_key'),
    path('fs/share_dtd_change', ChangeMemberAuth.as_view(), name='change_member_auth'),

    # 团队相关
    path('team/new_from_fold', NewFromFold.as_view(), name='team_new_from_fold'),
    path('team/invitation', Invitation.as_view(), name='team_invitation'),
    path('team/auth', Auth.as_view(), name='team_auth'),
    path('team/remove', Remove.as_view(), name='team_remove'),
    path('team/info', Info.as_view(), name='team_info'),
    path('team/delete', Delete.as_view(), name='team_delete'),
    path('team/new', New.as_view(), name='team_new'),
    path('team/edit_info', TeamEditInfo.as_view(), name='team_edit_info'),
    path('team/all', All.as_view(), name='team_all'),
    path('team/identity', Identity.as_view(), name='team_identity'),
    path('team/quit', Quit.as_view(), name='team_quit'),
    path('team/invitation/confirm', InvitationConfirm.as_view(), name='team_invitation_confirm'),
    path('team/send_all', SendAll.as_view(), name='team_send_all'),

    # 模板库
    path('temp/all', TempAll.as_view(), name='temp_all'),
    path('temp/content', TempContent.as_view(), name='temp_content'),
    path('temp/delete', TempDelete.as_view(), name='temp_delete'),
    path('temp/new_doc', TempNewDoc.as_view(), name='temp_new_doc'),
    path('temp/new', TempNew.as_view(), name='temp_new'),

    # 私信
    path('chat/list', ChatList.as_view(), name='chat_list'),
    path('chat/content', ChatContent.as_view(), name='chat_content'),
    path('chat/send', SendChat.as_view(), name='chat_send'),
    path('chat/count', ChatCount.as_view(), name='chat_count'),
    path('chat/build_chat', BuildChat.as_view(), name='chat_build_chat'),

    # 阴间
    path('hell/words', HellWords.as_view(), name='hell_words'),

    # ckeditor image upload
    path('uploadImg', UploadImg.as_view(), name='uploadImg'),

    re_path(r'.*', TemplateView.as_view(template_name='index.html')),
]

