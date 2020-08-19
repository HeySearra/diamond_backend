# your views here.
import json
from typing import Callable, Union

from django.views import View
from easydict import EasyDict

from entity.models import Entity
from record.models import upd_record_create, upd_record_user
from teamwork.hypers import *
from teamwork.models import Team, Member, ROOT_SUFFIX
from user.models import User, Message
from user.views import send_team_invite_message, send_team_out_message, send_team_dismiss_message, \
    send_team_accept_message, send_team_admin_message, send_team_admin_cancel_message, send_team_member_out_message, send_team_all_message
from utils.cast import encode
from utils.meta_wrapper import JSR


def delete_records_and_workbench(ref_old_user: Union[User, None], ref_new_user: User) -> Callable:

    def __closure_fn(ent: Entity):
        upd_record_user(auth='create', ent=ent, old_user=ref_old_user, new_user=ref_new_user)
        if ref_old_user is not None:
            ref_new_user.collections.filter(ent_id=ent.id).delete()
            ref_new_user.links.filter(ent_id=ent.id).delete()

    return __closure_fn


class NewFromFold(View):
    @JSR('tid', 'status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.root = 1, 2, 3
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'fid'}:
            return None, E.key
        if not request.session['is_login']:
            return None, E.auth
        user = User.get_via_encoded_id(request.session['uid'])
        entity = Entity.get_via_encoded_id(kwargs['fid'])
        if user is None:
            return None, E.auth
        if entity is None:
            return None, E.uk
        if not entity.can_convert_to_team():
            return None, E.root

        try:
            team = Team.objects.create(root=entity, name=entity.name)
            Member.objects.create(member=user, team=team, auth=TEAM_AUTH.write, membership=TEAM_MEM.owner)
            entity.father = None
            entity.name = team.name + ROOT_SUFFIX
            entity.save()
            user.links.filter(ent=entity).delete()
            user.collections.filter(ent=entity).delete()
            upd_record_create(user, entity, delete=True)
        except:
            return None, E.uk
        return team.id, 0


class Invitation(View):
    @JSR('status', 'user_info')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid, E.no, E.me, E.exist, E.is_auth, E.admin = 1, 2, 3, 4, 5, 6, 7, 8
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid', 'acc', 'auth', 'is_new'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        if kwargs['auth'] not in ['write', 'read', 'comment', 'no_share']:
            return E.key
        user1 = User.get_via_encoded_id(request.session['uid'])
        if user1 is None:
            return E.auth
        try:
            user2 = User.objects.get(acc=kwargs['acc'])
        except:
            return E.no

        team = Team.get_via_encoded_id(kwargs['tid'])
        if team is None:
            return E.tid
        if user1 == user2 or user2 == team.owner:
            return E.me
        try:
            mem = Member.objects.get(member=user1, team=team)
        except:
            return E.no

        if mem.membership == TEAM_MEM.member:
            return E.auth
        if Member.objects.filter(member=user2, team=team).exists() and kwargs['is_new']:
            return E.exist
        try:
            mem = Member.objects.get(member=user2, team=team)
            if mem.membership == TEAM_MEM.admin and user1 != team.owner:
                return E.admin
            if mem.membership != kwargs['auth'] and kwargs['auth'] != 'no_share':
                mem.membership = kwargs['auth']
                mem.save()
                if not send_team_invite_message(team, user1, user2, False, kwargs['auth']):
                    return E.uk
            elif mem.membership == kwargs['auth']:
                return E.is_auth
            elif kwargs['auth'] == 'no_share':
                if not send_team_out_message(team, user2):
                    return E.uk
                old_user = mem.member
                owner = team.owner
                team.root.bfs_apply(func=delete_records_and_workbench(old_user, owner))
                mem.delete()
        except:
            # Member.objects.create(member=user2, team=team, membership=TEAM_MEM.member, auth=kwargs['auth'])
            if not send_team_invite_message(team, user1, user2):
                return E.uk
        return 0, {'uid': encode(user2.id), 'name': user2.name, 'src': user2.portrait}


class Auth(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid, E.uid = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid', 'list'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        team = Team.get_via_encoded_id(kwargs['tid'])
        if team is None:
            return E.tid
        user = User.get_via_encoded_id(request.session['uid'])
        if user is None:
            return E.auth

        try:
            owner = Member.objects.get(member=user, team=team)
        except:
            return E.auth
        if owner.membership != TEAM_MEM.owner:
            return E.auth
        user_list = Member.objects.filter(team=team)
        for member in user_list:
            u = member.member
            # 前端已判断不能设置自己权限（指创建者设置自己权限）
            # 如果本身是管理员且不在设置的uid_list里，就撤销并发信息
            if member.membership == TEAM_MEM.admin and u.encoded_id not in kwargs['list']:
                member.membership = TEAM_MEM.member
                try:
                    member.save()
                except:
                    return E.uk
                if not send_team_admin_cancel_message(team=team, su=user, mu=u):
                    return E.uk
                # print('==' * 10, 'to_member')
            elif member.membership == TEAM_MEM.member and u.encoded_id in kwargs['list']:
                member.membership = TEAM_MEM.admin
                try:
                    member.save()
                except:
                    return E.uk
                if not send_team_admin_message(team=team, su=user, mu=u):
                    return E.uk
                # print('==' * 10, 'to_admin')
        return 0


class Remove(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid, E.exist, E.uid = 1, 2, 3, 4, 5
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid', 'uid'}:
            return E.key
        if not request.session['is_login']:
            return E.auth

        user1 = User.get_via_encoded_id(request.session['uid'])
        team = Team.get_via_encoded_id(kwargs['tid'])
        user2 = User.get_via_encoded_id(kwargs['uid'])
        if user1 is None:
            return E.auth
        if team is None:
            return E.tid
        if user2 is None:
            return E.uid

        try:
            auth1 = Member.objects.get(member=user1, team=team).auth1
            auth2 = Member.objects.get(member=user2, team=team).auth2
        except:
            return E.auth
        if auth1 == TEAM_MEM.member or (auth1 == TEAM_MEM.admin and auth2 == TEAM_MEM.admin):
            return E.auth
        m = Member.objects.filter(member=user2, team=team)
        if not m.exists():
            return E.exist
        try:
            if not send_team_out_message(team, user2):
                return E.uk
            old_user = m.get().member
            owner = team.owner
            team.root.bfs_apply(func=delete_records_and_workbench(old_user, owner))
            m.delete()
        except:
            return E.uk
        return 0


class Info(View):
    @JSR('status', 'name', 'intro', 'portrait', 'create_dt', 'doc_num',
         'cuid', 'csrc', 'cname', 'cacc', 'norm', 'admin')
    def get(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid = 1, 2, 3
        if dict(request.GET).keys() != {'tid'}:
            return E.key, '', '', '', '', 0, '', '', '', '', [], []
        user = User.get_via_encoded_id(request.session['uid'])
        if user is None:
            return E.auth, '', '', '', '', 0, '', '', '', '', [], []
        team = Team.get_via_encoded_id(request.GET.get('tid'))
        if team is None:
            return E.tid, '', '', '', '', 0, '', '', '', '', [], []
        members = Member.objects.filter(team=team)
        if not members.exists():
            return E.tid, '', '', '', '', 0, '', '', '', '', [], []
        name = team.name
        intro = team.intro
        if team.portrait == "team.jpg":
            team.portrait = 'http://47.96.109.229/static/upload/portrait/team.jpg'
            team.save()
        portrait = team.portrait if team.portrait else ''
        create_dt = team.create_dt_str
        doc_num = team.root.num_leaves()
        cuid = ''
        cacc = ''
        cname = ''
        csrc = ''
        norm = []
        admin = []

        for m in members:
            if m.membership == 'owner':
                cuid = m.member.encoded_id
                cname = m.member.name
                csrc = m.member.portrait
                cacc = m.member.acc
            elif m.membership == 'admin':
                admin.append({
                    'uid': m.member.encoded_id,
                    'acc': m.member.acc,
                    'src': m.member.portrait,
                    'name': m.member.name
                })
            else:
                norm.append({
                    'uid': m.member.encoded_id,
                    'acc': m.member.acc,
                    'src': m.member.portrait,
                    'name': m.member.name,
                    'auth': m.auth,
                })
        return 0, name, intro, portrait, create_dt, doc_num, cuid, csrc, cname, cacc, norm, admin


# 解散团队
class Delete(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid, E.name = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        user = User.get_via_encoded_id(request.session['uid'])
        if user is None:
            return E.auth
        team = Team.get_via_encoded_id(kwargs['tid'])
        if team is None:
            return E.tid
        try:
            owner = Member.objects.get(member=user, team=team)
            members = Member.objects.filter(team=team)
        except:
            return E.auth
        if owner.membership != TEAM_MEM.owner:
            return E.auth
        if owner.member.root.sons_dup_name(name=team.root.name):
            return E.name
        try:
            for m in members:
                if not send_team_dismiss_message(team=team, mu=m.member, su=user):
                    return E.uk
            team.root.move(user.root)
            # 篡位嗷
            upd_record_create(user, team.root)
            team.root.bfs_apply(func=delete_records_and_workbench(ref_old_user=None, ref_new_user=user))
            team.delete()
        except:
            return E.uk
        return 0


class New(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.name = 1, 2, 3
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'name'}:
            return E.key
        if not request.session['is_login']:
            return E.auth

        owner = User.get_via_encoded_id(request.session['uid'])
        if owner is None:
            return E.auth
        if not CHECK_TEAM_NAME(kwargs['name']):
            return E.name
        try:
            # 创建新根文件夹
            root = Entity.locate_root(kwargs['name'])
            team = Team.objects.create(name=kwargs['name'], root=root, portrait="team.jpg")
            Member.objects.create(team=team, member=owner, auth=TEAM_AUTH.write, membership=TEAM_MEM.owner)
        except:
            return E.uk
        return 0


class TeamEditInfo(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid, E.name, E.intro = 1, 2, 3, 4, 5
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid', 'name', 'intro', 'img'}:
            return E.key
        if not request.session['is_login']:
            return E.auth

        team = Team.get_via_encoded_id(kwargs['tid'])
        if team is None:
            return E.tid
        if not CHECK_TEAM_NAME(kwargs['name']):
            return E.name
        if not CHECK_TEAM_INTRO(kwargs['intro']):
            return E.intro

        team.name = kwargs['name']
        team.root.name = kwargs['name'] + ROOT_SUFFIX
        team.intro = kwargs['intro']
        team.portrait = kwargs['img']
        try:
            team.save()
            team.root.save()
        except:
            return E.uk
        return 0


class All(View):
    @JSR('status', 'my_team', 'join_team')
    def get(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid = 1, 2, 3
        if dict(request.GET).keys() != set():
            return E.key, [], []
        if not request.session['is_login']:
            return E.auth
        my_team = []
        join_team = []
        members = Member.get_members_via_member_encoded_id(member_encoded_id=request.session['uid'])
        for m in members:
            if m.membership == TEAM_MEM.owner:
                my_team.append({
                    'tid': m.team.encoded_id,
                    'name': m.team.name,
                    'intro': m.team.intro,
                    'portrait': m.team.portrait if m.team.portrait else '',
                    'member_count': len(Member.objects.filter(team=m.team))
                })
            else:
                join_team.append({
                    'tid': m.team.encoded_id,
                    'name': m.team.name,
                    'intro': m.team.intro,
                    'portrait': m.team.portrait if m.team.portrait else '',
                    'member_count': len(Member.objects.filter(team=m.team))
                })
        return 0, my_team, join_team


class InvitationConfirm(View):
    @JSR('status', 'tid')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.exist, E.mid = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'mid', 'result'}:
            return E.key, ''
        if not request.session['is_login']:
            return E.auth, ''

        msg = Message.get_via_encoded_id(kwargs['mid'])
        if msg is None:
            return E.mid, ''
        msg.is_process = True
        msg.result_content = '您已' + ('接受' if kwargs['result'] else '拒绝') + '该邀请'
        try:
            team = Team.objects.get(id=msg.related_id)  # 消息里的id未加密
            msg.save()
        except:
            return E.uk, ''
        if kwargs['result']:
            if Member.objects.filter(team=team, member=msg.owner).exists():
                return E.exist, ''
            try:
                Member.objects.create(team=team, member=msg.owner, membership=TEAM_MEM.member, auth=TEAM_AUTH.read)
                if not send_team_accept_message(team=team, su=msg.owner, mu=msg.sender, if_accept=True):
                    return E.uk, ''
            except:
                return E.uk, ''
        else:
            if Member.objects.filter(team=team, member=msg.owner).exists():
                return E.exist, ''
            if not send_team_accept_message(team=team, su=msg.owner, mu=msg.sender, if_accept=False):
                return E.uk, ''
        return 0, team.encoded_id


class Identity(View):
    @JSR('identity', 'status', 'auth')
    def get(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid = 1, 2, 3
        if dict(request.GET).keys() != {'tid'}:
            return '', E.key
        if not request.session['is_login']:
            return 'none', E.auth
        user = User.get_via_encoded_id(request.session['uid'])
        if user is None:
            return '', E.auth
        team = Team.get_via_encoded_id(request.GET.get('tid'))
        if team is None:
            return '', E.tid

        try:
            mem = Member.objects.get(team=team, member=user)
        except:
            return 'none', 0
        return mem.membership, 0, mem.auth


class Quit(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid, E.exist = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        user = User.get_via_encoded_id(request.session['uid'])
        if user is None:
            return E.auth

        team = Team.get_via_encoded_id(kwargs['tid'])
        if team is None:
            return E.tid

        try:
            m = Member.objects.get(team=team, member=user)
        except:
            return E.exist
        try:
            m.delete()
        except:
            return E.uk
        members = Member.objects.filter(team=team)
        for m in members:
            if m.membership == TEAM_MEM.owner or m.membership == TEAM_MEM.admin:
                if not send_team_member_out_message(team=team, su=user, mu=m.member):
                    return E.uk
        team.root.bfs_apply(func=delete_records_and_workbench(user, team.owner))
        return 0


class SendAll(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid, E.content = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid', 'content'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        user = User.get_via_encoded_id(request.session['uid'])
        if user is None:
            return E.auth
        team = Team.get_via_encoded_id(kwargs['tid'])
        if team is None:
            return E.tid

        try:
            auth = Member.objects.get(team=team, member=user).membership
        except:
            return E.tid
        if auth != 'admin' and auth != 'owner':
            return E.auth
        if not 0 <= len(kwargs['content']) <= 1024:
            return E.content
        if not send_team_all_message(team=team, su=user, content=kwargs['content']):
            return E.uk
        return 0
