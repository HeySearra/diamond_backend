import json

from django.db.models import Q
from django.shortcuts import render

# Create your views here.
from django.views import View

from misc.models import Collection
from user.models import User
from utils.cast import decode
from utils.response import JSR


class StarCondition(View):
    @JSR('is_starred', 'status')
    def get(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return False, -1
        u = u.get()
        if dict(request.GET).keys() != {'id', 'type'}:
            return False, 1
        try:
            did = int(decode(request.GET.get('id')))
        except:
            return False, -1
        is_starred = False
        if not Collection.objects.filter(Q(user_id=u.id) | Q(ent_id=did)).exists():
            is_starred = True
        return is_starred, 0


class Star(View):
    @JSR('status')
    def post(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1
        u = u.get()
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type', 'is_starred'}:
            return 1,
        if kwargs['is_starred']:
            try:
                Collection.objects.filter(id=int(decode(request.session['uid']))).delete()
            except:
                return -1,
        star = Collection()
        star.user = u
        star.ent = int(decode(kwargs['id']))
        star.save()
        return 0
