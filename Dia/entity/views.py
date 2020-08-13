from django.views import View
from easydict import EasyDict as ED
import json
import os
from user.models import User
from datetime import datetime, timedelta
from dateutil import relativedelta
from entity.models import Entity
from fusion.models import Collection, Links
from record.models import record, CreateRecord, WriteRecord, record_create
from django.db.utils import IntegrityError, DataError
from django.db.models import Q
from utils.cast import encode, decode, cur_time
from utils.response import JSR
from entity.hypers import *
from typing import List, Tuple
from teamwork.models import Team


class WorkbenchCreate(View):
    @JSR('status', 'cur_dt', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au = 2
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs: dict = request.GET
        if kwargs.keys() != {'page', 'each'}:
            return E.k

        page, each = int(kwargs.get('page')), int(kwargs.get('each'))

        ls = u.create_records.all()[(page - 1) * each: page * each]
        ls = [_.ent for _ in ls if not _.ent.backtrace_deleted]

        return 0, cur_time(), [{
            'type': l.type,
            'pfid': l.father.encoded_id,
            'dt': l.create_dt,
            'name': l.name,
            'id': l.encoded_id
        } for l in ls]


class WorkbenchRecentView(View):
    @JSR('status', 'cur_dt', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au = 2
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs: dict = request.GET
        if kwargs.keys() != {}.keys():
            return E.k
        ls = u.read_records.all()[:15]
        ls = [_.ent for _ in ls if not _.ent.backtrace_deleted]
        print(ls)
        return 0, cur_time(), [{
            'name': l.name,
            'dt': l.create_dt,
            'id': l.encoded_id,
            'is_starred': Collection.objects.filter(user=u, ent=l).exists(),
        } for l in ls]


class WorkbenchStar(View):
    @JSR('status', 'list')
    def get(self, request):
        return 0, []


class DocEdit(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.inv_name, E.inv_cont, E.rename = 2, 3, 4, 5
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'name', 'did', 'content'}:
            return E.k

        name, did, content = kwargs['name'], kwargs['did'], kwargs['content']

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.u
        if e.father.sons_dup_name(name):
            return E.rename
        if not CHECK_ENAME(name):
            return E.inv_name
        e.name = name
        e.content = content
        try:
            e.save()
        except:
            return E.u

        return 0


class DocComment(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.inv_name, E.inv_cont, E.rename = 2, 3, 4, 5
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'did', 'content'}:
            return E.k

        did, content = kwargs['did'], kwargs['content']

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.u
        e.content = content
        try:
            e.save()
        except:
            return E.u

        return 0


class DocAll(View):
    @JSR('status', 'name', 'content')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs: dict = request.GET
        if kwargs.keys() != {'did'}:
            return E.k

        did = kwargs.get('did')

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.no_ent
        return 0, e.name, e.content


class DocInfo(View):
    @JSR('status', 'name', 'is_starred', 'create_dt', 'cuid', 'cname', 'edit_dt', 'euid', 'ename')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs: dict = request.GET
        if kwargs.keys() != {'did'}:
            return E.k

        did = kwargs.get('did')

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.no_ent
        return (
            0, e.name, Collection.objects.filter(user=u, ent=e).exists(),
            e.create_dt, e.creator.encoded_id, e.creator.name,
            e.edit_dt, e.editor.encoded_id, e.editor.name,
        )


class DocLock(View):
    @JSR('status', 'is_locked')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs: dict = request.GET
        if kwargs.keys() != {'did'}:
            return E.k

        did = kwargs.get('did')

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.no_ent
        return 0, e.is_locked

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
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'did', 'is_locked'}:
            return E.k

        did, is_locked = kwargs['did'], kwargs['is_locked']

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.no_ent
        e.is_locked = is_locked
        try:
            e.save()
        except:
            return E.u
        return 0


class FSNew(View):
    @JSR('fid', 'status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_fa, E.inv_name, E.rename = 2, 3, 4, 5
        if not request.session.get('is_login', False):
            return '', E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return '', E.au
        kwargs: dict = {'pfid': None}
        kwargs.update(json.loads(request.body))
        if kwargs.keys() != {'name', 'pfid', 'type'}:
            return '', E.k

        name, pfid, type = kwargs['name'], kwargs['pfid'], kwargs['type']

        fa = Entity.get_via_encoded_id(pfid) if pfid is not None else u.root
        if fa is None:
            return '', E.no_fa
        print('================================', fa.name)
        e = Entity(name=name, father=fa, type=type)
        try:
            e.save()
        except:
            return '', E.u
        record_create(u, e)
        return e.encoded_id, 0


class FSFoldElem(View):
    @JSR('status', 'cur_dt', 'path', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_f = 2, 3
        if not request.session.get('is_login', False):
            return E.au, '', [], []
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au, '', [], []
        kwargs = request.GET
        if kwargs.keys() != {'fid'}:
            return E.k, '', [], []

        e = Entity.get_via_encoded_id(kwargs.get('fid'))
        if e is None:
            return E.no_f, '', [], []

        path: List[Entity] = e.path
        sons: List[Tuple[Entity, bool]] = [(s, False) for s in e.sons.filter(is_deleted=False)]
        if e.is_user_root():
            sons.extend([(lk.ent, True) for lk in Links.objects.filter(user=u)])

        path_s = [{'fid': f.encoded_id, 'name': f.name} for f in path]
        sons_s = [{
            'type': f.type, 'id': f.encoded_id, 'name': f.name,
            'is_link': is_link, 'is_starred': Collection.objects.filter(user=u, ent=f).exists(),
            'create_dt': f.create_dt, 'cuid': f.creator.encoded_id, 'cname': f.creator.name,
            'edit_dt': f.edit_dt, 'euid': f.editor.encoded_id, 'ename': f.editor.name,
        } for f, is_link in sons]

        return 0, cur_time(), path_s, sons_s


class FSRecycleElem(View):
    @JSR('status', 'cur_dt', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au = 2
        if not request.session.get('is_login', False):
            return E.au, '', []
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au, '', []
        kwargs = request.GET
        if kwargs.keys() != set():
            return E.k, '', []

        fs = u.create_records.filter(ent__is_deleted=True)

        ret = [{
            'type': f.ent.type, 'id': f.ent.encoded_id, 'name': f.ent.name,
            'delete_dt': f.ent.delete_dt, 'is_dia': False,  # todo
        } for f in fs]

        return 0, cur_time(), ret


class FSFather(View):
    @JSR('status', 'pfid')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no, E.no_father = 2, 3, 4
        if not request.session.get('is_login', False):
            return E.au, ''
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au, ''
        kwargs = request.GET
        if kwargs.keys() != {'id', 'type'}:
            return E.k, ''

        e = Entity.get_via_encoded_id(kwargs.get('id'))
        if e is None:
            return E.no, ''
        if e.father is None:
            return E.no_father, ''

        return 0, e.father.encoded_id


class FSDocInfo(View):
    @JSR('status', 'name', 'size', 'cuid', 'cname', 'is_locked', 'path')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs = request.GET
        if kwargs.keys() != {'did'}:
            return E.k

        e = Entity.get_via_encoded_id(kwargs.get('did'))
        if e is None or e.father is None:
            return E.no

        return (
            0, e.name, len(e.plain_content),
            e.creator.encoded_id, e.creator.name,
            e.is_locked, [{'fid': f.encoded_id, 'name': f.name} for f in e.path]
        )


class FSFoldInfo(View):
    @JSR('status', 'name', 'cuid', 'cname', 'path')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs = request.GET
        if kwargs.keys() != {'fid'}:
            return E.k

        e = Entity.get_via_encoded_id(kwargs.get('fid'))
        if e is None or e.father is None:
            return E.no

        return (
            0, e.name,
            e.creator.encoded_id, e.creator.name,
            [{'fid': f.encoded_id, 'name': f.name} for f in e.path]
        )


class FSRename(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.uni, E.too_long = 2, 3, 4
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type', 'name'}:
            return E.k

        name = kwargs['name']
        if not CHECK_ENAME(name):
            return E.too_long
        e = Entity.get_via_encoded_id(kwargs['id'])
        if e is None:
            return E.u
        if e.father.sons_dup_name():
            return E.uni
        e.name = name
        e.save()
        return 0


class FSLinkNew(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.uni, E.no_id = 2, 3, 4
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type'}:
            return E.k

        e = Entity.get_via_encoded_id(kwargs['id'])
        if e is None:
            return E.u
        if u.links.filter(ent__name=e.name):
            return E.uni

        Links.objects.create(user=u, ent=e)

        return 0


class FSMove(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.uni, E.already, E.not_found = 2, 3, 4, 5
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type', 'pfid'}:
            return E.k

        e = Entity.get_via_encoded_id(kwargs['id'])
        if e is None:
            return E.u

        fa = Entity.get_via_encoded_id(kwargs['pfid'])
        if fa is None or fa.is_doc():
            return E.not_found

        if e.father is not None and e.father.id == fa.id:
            return E.already

        if fa.sons_dup_name(e.name):
            return E.uni

        e.move(fa)

        return 0


class FSCopy(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.uni, E.already, E.not_found = 2, 3, 4, 5
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type', 'pfid'}:
            return E.k

        e = Entity.get_via_encoded_id(kwargs['id'])
        if e is None:
            return E.u

        fa = Entity.get_via_encoded_id(kwargs['pfid'])
        if fa is None or fa.is_doc():
            return E.not_found

        if e.father is not None and e.father.id == fa.id:
            return E.already

        if fa.sons_dup_name(e.name):
            return E.uni

        e.replicate(u, fa)

        return 0


class FSDelete(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_id = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type'}:
            return E.k

        e = Entity.get_via_encoded_id(kwargs['id'])
        if e is None:
            return E.no_id

        e.is_deleted = True
        e.delete_dt = datetime.now()
        e.save()

        return 0


class FSDeleteLink(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_id = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type'}:
            return E.k

        e = Entity.get_via_encoded_id(kwargs['id'])
        if e is None:
            return E.u

        q = Links.objects.filter(user=u, ent=e)
        if q.exists():
            q.delete()
        else:
            return E.no_id

        return 0


class FSUserRoot(View):
    @JSR('status', 'fid')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au = 2
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs = request.GET
        if kwargs.keys() != set():
            return E.k

        return 0, u.root.encoded_id


class FSTeamRoot(View):
    @JSR('status', 'fid')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au = 2
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        # print(request.GET)
        kwargs = request.GET
        if kwargs.keys() != {'tid'}:
            return E.k

        t: Team

        t = Team.get_via_encoded_id(kwargs.get('tid'))
        if t is None or not t.contains_user(u):
            return E.u

        return 0, t.root.encoded_id


class FSRecycleRecover(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.not_found = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type'}:
            return E.k

        e = Entity.objects.filter(int(decode(kwargs['id'])))
        if not e.exists():
            return E.not_found
        e = e.get()
        if not e.is_deleted:
            return E.not_found
        if e.father.backtrace_deleted:
            return E.not_found
        e.is_deleted = False
        e.save()

        return 0


class FSRecycleDelete(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.not_found = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type'}:
            return E.k

        e = Entity.objects.filter(int(decode(kwargs['id'])))
        if not e.exists():
            return E.not_found
        ent: Entity = e.get()
        if not ent.is_deleted:
            return E.not_found

        [so.delete() for so in ent.subtree]

        return 0


class FSRecycleClear(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.not_found = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {}.keys():
            return E.k

        all_f = []
        for rec in u.create_records.filter(ent__is_deleted=True):
            e: Entity = rec.ent
            all_f.extend(e.subtree)

        fids = [f.id for f in all_f]
        all_f = [Entity.objects.get(id=fid) for fid in list(set(fids))]
        [f.delete() for f in all_f]
        return 0
