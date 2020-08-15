from django.shortcuts import render

# your views here.
import json
from django.views import View
from easydict import EasyDict

from meta_config import ROOT_SUFFIX
from record.models import record_create, upd_record_user
from user.models import Message
from user.views import send_team_invite_message, send_team_out_message, send_team_dismiss_message, \
    send_team_accept_message
from utils.cast import encode, decode
from utils.response import JSR
from teamwork.models import *
from teamwork.hypers import *
from entity.models import Entity


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
        try:
            user = User.objects.get(id=int(decode(request.session['uid'])))
            entity = Entity.get_via_encoded_id(kwargs['fid'])
        except:
            return None, E.uk
        if not entity.can_convert_to_team():
            return None, E.root
        try:
            team = Team.objects.create(root=entity)
            Member.objects.create(member=user, team=team, auth='owner')
            entity.father = None
            entity.name = team.name + ROOT_SUFFIX
            entity.save()
            record_create(user, entity, delete=True)
        except:
            return None, E.uk
        return team.id, 0


class Invitation(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.typo, E.exist = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid', 'acc'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        try:
            user1 = User.objects.get(id=int(decode(request.session['uid'])))
            user2 = User.objects.get(acc=kwargs['acc'])
            team = Team.objects.get(id=int(decode(kwargs['tid'])))
            auth = Member.objects.get(member=user1, team=team).auth
        except:
            return E.uk
        if auth == 'member':
            return E.auth
        if Member.objects.filter(member=user2, team=team).exists():
            return E.exist
        try:
            # Member.objects.create(member=user2, team=team, author='member')
            print(111)
            if not send_team_invite_message(team, user1, user2):
                return E.uk
        except:
            return E.uk
        return 0


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
        try:
            team = Team.objects.get(id=int(decode(kwargs['tid'])))
        except:
            return E.tid
        try:
            u = User.objects.get(id=int(decode(request.session['uid'])))
            owner = Member.objects.get(member=u, team=team)
        except:
            return E.auth
        if owner.auth != 'owner':
            return E.auth
        for uid in kwargs['list']:
            try:
                u = User.objects.get(id=uid)
                member = Member.objects.get(member=u, team=team)
                member.auth = 'admin' if member.auth == 'member' else 'member'
            except:
                return E.uid
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
        try:
            user1 = User.objects.get(id=int(decode(request.session['uid'])))
            user2 = User.objects.get(id=int(decode(kwargs['uid'])))
            team = Team.objects.get(id=int(decode(kwargs['tid'])))
            auth = Member.objects.get(member=user1, team=team).auth
        except:
            return E.uk
        if auth == 'member':
            return E.auth
        try:
            u = Member.objects.filter(member=user2, team=team)
        except:
            return E.uk
        if not u.exists():
            return E.exist
        try:
            if not send_team_out_message(team, user2):
                return E.uk
            old_user = u.get().member
            team.root.bfs_apply(
                func=lambda ent: upd_record_user(
                    auth='create', ent=ent,
                    old_user=old_user,
                    new_user=team.owner
                )
            )

            u.delete()
        except:
            return E.uk
        return 0


class Info(View):
    @JSR('status', 'name', 'intro', 'portrait', 'create_dt', 'doc_num',
         'cuid', 'cname', 'norm', 'admin')
    def get(self, request):
        print(request.GET)
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid = 1, 2, 3
        if dict(request.GET).keys() != {'tid'}:
            return E.key, '', '', '', '', 0, '', '', [], []
        uid = int(decode(request.session['uid']))
        tid = int(decode(request.GET.get('tid')))
        try:
            user = User.objects.get(id=uid)
        except:
            return E.auth, '', '', '', '', 0, '', '', [], []
        try:
            team = Team.objects.get(id=tid)
        except:
            return E.tid, '', '', '', '', 0, '', '', [], []
        members = Member.objects.filter(team=team)
        if not members.exists():
            return E.tid, '', '', '', '', 0, '', '', [], []
        name = team.name
        intro = team.intro
        portrait = team.portrait if team.portrait else ''
        create_dt = team.create_dt_str
        doc_num = len(team.root.subtree)
        cuid = ''
        cname = ''
        norm = []
        admin = []

        for m in members:
            if m.auth == 'owner':
                cuid = encode(str(m.member.id))
                cname = m.member.name
            elif m.auth == 'admin':
                admin.append({
                    'uid': encode(str(m.member.id)),
                    'name': m.member.name
                })
            else:
                norm.append({
                    'uid': encode(str(m.member.id)),
                    'name': m.member.name
                })
        return 0, name, intro, portrait, create_dt, doc_num, cuid, cname, norm, admin


# 解散团队
class Delete(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid = 1, 2, 3
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        try:
            team = Team.objects.get(id=int(decode(kwargs['tid'])))
        except:
            return E.tid
        try:
            user = User.objects.get(id=int(decode(request.session['uid'])))
            owner = Member.objects.get(member=user, team=team)
            members = Member.objects.filter(team=team)
        except:
            return E.auth
        if owner.auth != 'owner':
            return E.auth
        try:
            for m in members:
                print(111)
                if not send_team_dismiss_message(team=team, mu=m.member):
                    return E.uk
            team.root.move(user.root)
            # 篡位嗷
            team.root.bfs_apply(
                func=lambda f: upd_record_user('create', f, old_user=None, new_user=user)
            )
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
        try:
            owner = User.objects.get(id=int(decode(request.session['uid'])))
        except:
            return E.auth
        if not (0 <= len(str(kwargs['name'])) <= TEAM_NAME_MAX_LENGTH and str(kwargs['name']).isprintable()):
            return E.name
        try:
            # 创建新根文件夹
            root = Entity.locate_root(kwargs['name'])
            team = Team.objects.create(name=kwargs['name'], root=root)
            Member.objects.create(team=team, member=owner, auth='owner')
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
        try:
            team = Team.objects.get(id=int(decode(kwargs['tid'])))
        except:
            return E.tid
        if not (0 < len(kwargs['name']) <= TEAM_NAME_MAX_LENGTH and str(kwargs['name']).isprintable()):
            return E.name
        if not 0 < len(kwargs['intro']) <= TEAM_INTRO_MAX_LENGTH:
            return E.intro
        team.name = kwargs['name']
        team.intro = kwargs['intro']
        team.portrait = kwargs['img']
        try:
            team.save()
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
        uid = int(decode(request.session['uid']))
        try:
            members = Member.objects.filter(member=uid)
        except:
            return E.uk
        my_team = []
        join_team = []
        for m in members:
            if m.auth == 'owner':
                my_team.append({
                    'tid': encode(str(m.team.id)),
                    'name': m.team.name,
                    'intro': m.team.intro,
                    'portrait': m.team.portrait if m.team.portrait else '',
                    'member_count': len(Member.objects.filter(team=m.team))
                })
            else:
                join_team.append({
                    'tid': encode(str(m.team.id)),
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
        try:
            msg = Message.objects.get(id=int(decode(kwargs['mid'])))
        except:
            return E.mid, ''
        try:
            team = Team.objects.get(id=msg.related_id)  # 消息里的id未加密
        except:
            return E.uk, ''
        if kwargs['result']:
            if Member.objects.filter(team=team, member=msg.owner).exists():
                return E.exist, ''
            try:
                Member.objects.create(team=team, member=msg.owner, auth='member')
                if not send_team_accept_message(team=team, su=msg.owner, mu=msg.sender, if_accept=True):
                    return E.uk, ''
            except:
                return E.uk, ''
        else:
            if not send_team_accept_message(team=team, su=msg.owner, mu=msg.sender, if_accept=False):
                return E.uk, ''
        return 0, encode(team.id)


class Identity(View):
    @JSR('identity', 'status')
    def get(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid = 1, 2, 3
        if dict(request.GET).keys() != {'tid'}:
            return '', E.key
        if not request.session['is_login']:
            return 'none', E.auth
        uid = int(decode(request.session['uid']))
        tid = int(decode(request.GET.get('tid')))
        try:
            user = User.objects.get(id=uid)
        except:
            return '', E.uk
        try:
            team = Team.objects.get(id=tid)
        except:
            return '', E.tid
        try:
            identity = Member.objects.get(team=team, member=user).auth
        except:
            return 'none', 0
        return identity, 0


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
        try:
            team = Team.objects.get(id=int(decode(kwargs['tid'])))
            user = User.objects.get(id=int(decode(request.session['uid'])))
        except:
            return E.tid
        try:
            m = Member.objects.get(team=team, member=user)
        except:
            return E.exist
        try:
            m.delete()
        except:
            return E.uk
        return 0
