from django.views import View
from easydict import EasyDict as ED
import json
import os
from datetime import datetime, timedelta
from dateutil import relativedelta
from entity.models import Entity
from fusion.models import Collection
from record.models import record
from django.db.utils import IntegrityError, DataError
from django.db.models import Q
from utils.cast import encode, decode, cur_time
from utils.response import JSR
from entity.hypers import *
from user.models import *


class FSNew(View):
    @JSR('fid', 'status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_fa, E.inv_name, E.rename = 2, 3, 4, 5
        if not request.session.get('is_login', False):
            return '', E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'name', 'pfid', 'type'}:
            return '', E.k

        name, pfid, type = kwargs['name'], kwargs['pfid'], kwargs['type']

        fa = Entity.get_via_encoded_id(pfid)
        if fa is None:
            return '', E.no_fa

        e = Entity(name=name, father=fa, type=type)
        try:
            e.save()
        except:
            return '', E.u
        return e.encoded_id, 0


class FSelem(View):
    @JSR('status', 'cur_dt', 'path', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_f = 2, 3
        if not request.session.get('is_login', False):
            return E.au, '', [], []
        if dict(request.GET).keys() != {'fid'}:
            return E.k, '', [], []
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except ValueError:
            return -1, [], 0, ''

        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1, [], 0, ''
        u = u.get()
