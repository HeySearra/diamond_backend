from django.shortcuts import render

# Create your views here.
import json
from django.views import View
from easydict import EasyDict

from utils.cast import encode, decode
from utils.response import JSR
from teamwork.models import *
from teamwork.hypers import *


class Invitation(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.typo, E.exist = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid', 'uid'}:
            return E.key
        try:
            user1 = User.objects.get(id=decode(request.session['uid']))
            user2 = User.objects.get(id=decode(kwargs['uid']))
            team = Team.objects.get(id=decode(kwargs['tid']))
            auth = Member.objects.get(user=user1, team=team).auth
        except:
            return E.uk
        if auth == 'member':
            return E.auth
        if Member.objects.filter(user=user2, team=team).exists():
            return E.exist
        new_member = Member()
        new_member.member = user2
        new_member.auth = 'member'
        new_member.team = team
        try:
            new_member.save()
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
        try:
            team = Team.objects.get(id=decode(kwargs['tid']))
        except:
            return E.tid
        try:
            u = User.objects.get(id=decode(request.session['uid']))
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


# class Remove(View):
#     @JSR('status')
#     def post(self, request):
#         E = EasyDict()
#         E.uk = -1
#         E.key, E.auth, E.tid, E.exist, E.uid = 1, 2, 3, 4, 5
