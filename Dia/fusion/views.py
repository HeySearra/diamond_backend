import json

from django.db.models import Q
from django.shortcuts import render

# Create your views here.
from django.views import View
from easydict import EasyDict

from entity.hypers import BASIC_DATA_MAX_LEN
from entity.models import Entity
from fusion.models import Collection, UserTemplate, OfficialTemplate
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


class TempAll(View):  # 该请求复杂度高达n^2
    @JSR('status', 'my_list', 'official_list')
    def get(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth = 1, 2
        if dict(request.GET).keys() != set():
            return E.key, [], []
        if not request.session['is_login']:
            return E.auth, [], []
        uid = int(decode(request.session['uid']))
        try:
            user = User.objects.get(id=uid)
        except:
            return E.uk, [], []
        my_list = []
        official_list = []  # 按类型存放官方模板
        title_list = []  # 所有的官方目标种类
        # 同一类型的官方模板实体
        try:
            user_template_list = UserTemplate.objects.filter(creator=user)
        except:
            return E.uk, [], []
        for user_template in user_template_list:
            my_list.append({
                'tid': user_template.id,
                'title': user_template.name  # 个人模板名称
            })
        try:
            official_template_list = OfficialTemplate.objects.all()
        except:
            return E.uk, [], []
        # [{'title': official_template.title, 'temps': [{'tid': }...]}...]
        for official_template in official_template_list:
            if official_template.title not in title_list:
                title_list.append(official_template.title)
        for title in title_list:
            temps = []
            for t in OfficialTemplate.objects.filter(title=title):
                temps.append({
                    'tid': t.id,
                    'name': t.name,
                    'img': t.portrait,
                    'only_vip': t.only_vip
                })
            official_list.append({
                'title': title,
                'temps': temps
            })
        return 0, my_list, official_list


class TempContent(View):
    @JSR('status', 'name', 'content')
    def get(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.tid = 1, 2, 3
        if dict(request.GET).keys() != {'tid', 'type'}:
            return E.key, '', ''
        if not request.session['is_login']:
            return E.auth, [], []
        type_ = request.GET.get('type')
        tid = int(decode(request.GET.get('tid')))
        try:
            t = UserTemplate.objects.get(id=tid) if type_ == 'user' else OfficialTemplate.objects.get(id=tid)
        except:
            return E.tid, '', ''
        return 0, t.name, t.content


class TempDelete(View):
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
            t = UserTemplate.objects.get(id=int(decode(kwargs['tid'])))
        except:
            return E.tid
        try:
            t.delete()
        except:
            return E.uk
        return 0


class TempNewDoc(View):
    @JSR('status', 'did')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.fa, E.uni, E.name = 1, 2, 3, 4, 5
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tid', 'name', 'pfid', 'type'}:
            return E.key
        if not request.session['is_login']:
            return E.auth
        try:
            t = UserTemplate.objects.get(id=int(decode(kwargs['tid']))) \
                if kwargs['type'] == 'user' else OfficialTemplate.objects.get(id=int(decode(kwargs['tid'])))
        except:
            return E.uk, ''
        try:
            father = Entity.objects.get(id=int(decode(kwargs['pfid'])))
        except:
            return E.fa, ''
        if not (0 <= len(kwargs['name']) <= BASIC_DATA_MAX_LEN and str(kwargs['name']).isprintable()):
            return E.name
        if father.sons_dup_name(kwargs['name']):
            return E.uni
        try:
            e = Entity.objects.create(father=father, name=kwargs['name'], content=t.content, type='doc')
        except:
            return E.uk, ''
        return 0, e.id


class TempNew(View):
    @JSR('status', 'tid')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.auth, E.uni, E.name = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'name', 'content'}:
            return E.key, ''
        if not request.session['is_login']:
            return E.auth, ''
        if not (0 <= len(kwargs['name']) <= BASIC_DATA_MAX_LEN and str(kwargs['name']).isprintable()):
            return E.name, ''
        try:
            user = User.objects.get(id=int(decode(request.session['uid'])))
        except:
            return E.uk, ''
        user_template_list = UserTemplate.objects.filter(creator=user)
        for t in user_template_list:
            if t.name == kwargs['name']:
                return E.uni, ''
        try:
            t = UserTemplate.objects.create(creator=user, name=kwargs['name'], content=kwargs['content'])
        except:
            return E.uk, ''
        return 0, t.id
