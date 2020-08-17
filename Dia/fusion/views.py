import json
import time

from django.db.models import Q
from django.views import View
from easydict import EasyDict as ED
from easydict import EasyDict

from entity.hypers import BASIC_DATA_MAX_LEN, CHECK_ENAME
from entity.models import Entity
from fusion.models import Collection, Comment, Trajectory
from meta_config import HOST_IP
from fusion.models import Collection, UserTemplate, OfficialTemplate
from record.models import upd_record_create
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

        ent = Entity.get_via_encoded_id(request.GET.get('id'))
        if ent is None:
            return False, -1

        return Collection.objects.filter(user_id=u.id, ent_id=ent.id).exists(), 0


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


class TempAll(View):
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
                'tid': user_template.encoded_id,
                'title': user_template.name  # 个人模板名称
            })
        try:
            official_template_list = OfficialTemplate.objects.all()
        except:
            return E.uk, [], []
        # [{'title': official_template.title, 'temps': [{'tid': }...]}...]

        from collections import defaultdict
        official_dict = defaultdict(list)

        [official_dict[t.title].append({
            'tid': t.encoded_id,
            'title': t.name,
            'img': t.portrait,
            'only_vip': t.only_vip
        }) for t in official_template_list]

        return 0, my_list, [dict(title=k, temps=v) for k, v in official_dict.items()]


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
            user = User.objects.get(id=int(decode(request.session.get('uid', '-1'))))
        except:
            return E.auth, ''

        try:
            t = UserTemplate.objects.get(id=int(decode(kwargs['tid']))) \
                if kwargs['type'] == 'user' else OfficialTemplate.objects.get(id=int(decode(kwargs['tid'])))
        except:
            return E.uk, ''
        father = Entity.get_via_encoded_id(kwargs['pfid'])
        if father is None:
            return E.fa, ''
        if not CHECK_ENAME(kwargs['name']):
            return E.name
        if father.sons_dup_name(kwargs['name']):
            return E.uni
        try:
            e = Entity.objects.create(father=father, name=kwargs['name'], content=t.content, type='doc')
            upd_record_create(user, e)
            Trajectory.objects.create(
                ent=e,
                user=user,
                updated_content=e.content
            )

        except:
            return E.uk, ''
        return 0, e.encoded_id


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
        return 0, t.encoded_id


class CommentGetUsers(View):
    @JSR('status', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au, None
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au, None
        kwargs = request.GET
        if kwargs.keys() != {'did'}:
            return E.k, None

        did = kwargs.get('did')

        ent = Entity.get_via_encoded_id(did)
        if ent is None:
            return E.no_ent, None
        try:
            comments = Comment.objects.filter(did_id=ent.id)
            users = []
            user = User.get_via_encoded_id(request.session['uid'])
            dic = {'id': user.encoded_id,
                   'name': user.name,
                   'avatar': f'http://{HOST_IP}:8000/' + user.portrait}
            users.append(dic)
            for comment in comments:
                user = comment.uid
                dic = {'id': user.encoded_id,
                       'name': user.name,
                       'avatar': f'http://{HOST_IP}:8000/' + user.portrait}
                if dic not in users:
                    users.append(dic)
        except:
            return E.u, None
        return 0, users


class CommentGetCommentsOfThread(View):
    @JSR('status', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au, None
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au, None

        kwargs = request.GET
        if kwargs.keys() != {'did', 'threadId'}:
            return E.k, None
        did = kwargs.get('did')
        threadId = kwargs.get('threadId')

        ent = Entity.get_via_encoded_id(did)
        if ent is None:
            return E.no_ent

        try:
            items = list(Comment.objects.filter(did_id=ent.id,
                                                threadId=threadId).values())
        except:
            return E.u, None
        if items is None:
            return E.no_ent, None
        res = []
        for it in items:
            dic = {'commentId': it.get('commentId'),
                   'authorId': str(it.get('uid_id')),
                   'content': it.get('content'),
                   'createdAt': it.get('createdAt')}
            res.append(dic)
        return 0, res


class CommentAdd(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = json.loads(request.body)
        if kwargs.keys() != {'did', 'threadId', 'commentId', 'content'}:
            return E.k

        did = kwargs.get('did')

        ent = Entity.get_via_encoded_id(did)
        if ent is None:
            return E.no_ent
        try:
            new_comment = Comment(did=ent,
                                  uid=u,
                                  threadId=kwargs.get('threadId'),
                                  commentId=kwargs.get('commentId'),
                                  content=kwargs.get('content'),
                                  createdAt=int(time.time() * 1000))
            new_comment.save()
        except:
            return E.u
        return 0


class CommentUpdate(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = json.loads(request.body)
        if kwargs.keys() != {'did', 'threadId', 'commentId', 'content'}:
            return E.k

        did = kwargs['did']

        ent = Entity.get_via_encoded_id(did)
        if ent is None:
            return E.no_ent

        try:
            upd_comment = Comment.objects.get(did_id=ent.id,
                                              uid_id=u.id,
                                              threadId=kwargs.get('threadId'),
                                              commentId=kwargs.get('commentId'))
            if upd_comment is None:
                return E.no_ent
            upd_comment.content = kwargs.get('content')
            upd_comment.save()
        except:
            return E.u
        return 0


class CommentRemove(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = json.loads(request.body)
        if kwargs.keys() != {'did', 'threadId', 'commentId'}:
            return E.k

        did = kwargs['did']

        ent = Entity.get_via_encoded_id(did)
        if ent is None:
            return E.no_ent

        try:
            rmv_comment = Comment.objects.get(did_id=ent.id,
                                              uid_id=u.id,
                                              threadId=kwargs.get('threadId'),
                                              commentId=kwargs.get('commentId'))
            if rmv_comment is None:
                return E.no_ent
            rmv_comment.delete()
        except:
            return E.u
        return 0
