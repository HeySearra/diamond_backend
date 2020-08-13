from django.shortcuts import render

# your views here.
import json
from django.views import View
from easydict import EasyDict

from utils.cast import encode, decode
from utils.response import JSR
from teamwork.models import *
from teamwork.hypers import *


class NewFromFold(View):
    @JSR('tid', 'status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.root = 1, 2, 3
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'fid'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        try:
            user = User.objects.get(id=int(decode(request.session['uid'])))
            entity = Entity.objects.get(id=int(decode(kwargs['fid'])))
        except:
            return E.uk
        if not entity.can_convert_to_team():
            return E.root
        try:
            team = Team.objects.create(root=entity)
            Member.objects.create(member=user, team=team, auth='owner')
            entity.father = None
            entity.save()
        except:
            return E.uk
        return team.id, 0


class Invitation(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.typo, E.exist = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid', 'account'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        try:
            user1 = User.objects.get(id=int(decode(request.session['uid'])))
            user2 = User.objects.get(acc=kwargs['account'])
            team = Team.objects.get(id=int(decode(kwargs['tid'])))
            auth = Member.objects.get(user=user1, team=team).auth
        except:
            return E.uk
        if auth == 'member':
            return E.auth
        if Member.objects.filter(user=user2, team=team).exists():
            return E.exist
        try:
            Member.objects.create(member=user2, team=team, author='member')
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
            auth = Member.objects.get(user=user1, team=team).auth
        except:
            return E.uk
        if auth == 'member':
            return E.auth
        try:
            u = Member.objects.filter(user=user2, team=team)
        except:
            return E.uk
        if not u.exists():
            return E.exist
        try:
            u.delete()
        except:
            return E.uk
        return 0


class Info(View):
    @JSR('status', 'name', 'intro', 'portrait', 'create_dt', 'doc_num',
         'cuid', 'cname', 'norm', 'admin')
    def get(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid = 1, 2, 3
        if dict(request.GET).keys() != {'tid'}:
            return E.key, '', '', '', '', 0, '', '', [], []
        uid = int(decode(request.session['uid']))
        tid = int(decode(request.GET['tid']))
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
        portrait = team.img
        create_dt = team.create_dt
        doc_num = len(team.root.subtree(True))
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
        except:
            return E.auth
        if owner.auth != 'owner':
            return E.auth
        try:
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
        if not (0 <= len(str(kwargs['name'])) <= 64 and str(kwargs['name']).isprintable()):
            return E.name
        try:
            # 创建新根文件夹
            root = Entity.objects.create(name=kwargs['name'])
            team = Team.objects.create(name=kwargs['name'], root=root)
            Member.objects.create(team=team, member=owner, auth='owner')
        except:
            return E.uk


class EditInfo(View):
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
        team.img = kwargs['img']
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
                    'portrait': m.team.img,
                    'member_count': len(Member.objects.filter(m.team.id))
                })
            else:
                join_team.append({
                    'tid': encode(str(m.team.id)),
                    'name': m.team.name,
                    'intro': m.team.intro,
                    'portrait': m.team.img,
                    'member_count': len(Member.objects.filter(m.team.id))
                })
        return 0, my_team, join_team


class InvitationConfirm(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth = 1, 2
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'jid', 'result'}:
            return E.key
        # ..todo
        return 0


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
        tid = int(decode(request.GET['tid']))
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
