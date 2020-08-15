import json

from django.db.models import Q
from django.shortcuts import render

# Create your views here.
from django.views import View

from entity.models import Entity
from fusion.models import Collection
from user.models import User
from utils.cast import decode
from utils.meta_wrapper import JSR


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


class FSStar(View):
    @JSR('status')
    def post(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1
        u = u.get()
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type', 'is_starred'}:
            return 1,

        ent = Entity.get_via_encoded_id(kwargs['id'])
        if ent is None:
            return 3

        if kwargs['is_starred']:
            Collection.objects.get_or_create(user=u, ent=ent)
        else:
            Collection.objects.filter(ent=ent, user_id=int(decode(request.session['uid']))).delete()
        return 0



