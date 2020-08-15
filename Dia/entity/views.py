import time

from django.views import View
from easydict import EasyDict as ED
import json
import os
from user.models import User
from datetime import datetime, timedelta
from dateutil import relativedelta
from entity.models import Entity
from fusion.models import Collection, Links
from record.models import upd_record, CreateRecord, WriteRecord, record_create
from django.db.utils import IntegrityError, DataError
from django.db.models import Q
from utils.cast import encode, decode, cur_time
from utils.meta_wrapper import JSR
from entity.hypers import *
from typing import List, Tuple
from teamwork.models import Team


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
        ls = u.read_records.all().order_by('-dt')
        ents = [_.ent for _ in ls if not _.ent.backtrace_deleted and _.ent.is_doc()][:15]
        return 0, cur_time(), [{
            'pfid': e.father.encoded_id if e.father.first_person(u) else '',
            'name': e.name,
            'dt': e.create_dt_str,
            'type': e.type,
            'id': e.encoded_id,
            'is_starred': Collection.objects.filter(user=u, ent=e).exists(),
        } for e in ents]


class WorkbenchStar(View):
    @JSR('status', 'amount', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k, E.au = -1, 1, 2
        if not request.session.get('is_login', False):
            return E.au

        kwargs: dict = request.GET
        if kwargs.keys() != {'page', 'each'}:
            return E.k

        page, each = int(kwargs.get('page')), int(kwargs.get('each'))

        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        ents = [c.ent for c in u.related_collection.all() if not c.ent.backtrace_deleted]

        amount = len(ents)
        ents = ents[(page - 1) * each: page * each]
        return 0, amount, [{
            'pfid': e.father.encoded_id if e.father.first_person(u) else '',
            'name': e.name,
            'create_dt': e.create_dt_str,
            'edit_dt': e.edit_dt_str,
            'type': e.type,
            'id': e.encoded_id,
            'cname': e.creator.name,
            'is_starred': Collection.objects.filter(user=u, ent=e).exists(),
        } for e in ents]


class WorkbenchCreate(View):
    @JSR('status', 'amount', 'cur_dt', 'list')
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

        ls = u.create_records.all()
        amount = ls.count()
        ents = [_.ent for _ in ls if not _.ent.backtrace_deleted][(page - 1) * each: page * each]

        return 0, amount, cur_time(), [{
            'pfid': e.father.encoded_id,
            'name': e.name,
            'create_dt': e.create_dt_str,
            'edit_dt': e.edit_dt_str,
            'type': e.type,
            'id': e.encoded_id,
            'cname': e.creator.name,
            'is_starred': Collection.objects.filter(user=u, ent=e).exists(),
        } for e in ents]


class DocEdit(View):
    # todo: upd record
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
        if e.brothers_dup_name(name):
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
    # todo: upd record
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
    # todo: upd record
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
        kwargs = eval(list(request.GET.keys())[0])
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

        cnm, cid, cdt = e.create_name_uid_dt_str
        enm, eid, edt = e.edit_name_uid_dt_str

        return (
            0, e.name, Collection.objects.filter(user=u, ent=e).exists(),
            cdt, cid, cnm,
            edt, eid, enm,
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
        if fa.sons_dup_name(name):
            return '', E.rename
        e = Entity(name=name, father=fa, type=type)
        try:
            e.save()
        except:
            return '', E.u
        record_create(u, e)
        return e.encoded_id, 0


class FSFoldElem(View):
    @JSR('status', 'cur_dt', 'path', 'list', 'name')
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

        if not e.first_person(u):
            return E.no_f

        sons: List[Tuple[Entity, str, bool]] = [(s, e.encoded_id, False) for s in e.sons.filter(is_deleted=False).order_by('name')]
        if e.is_user_root():
            sons.extend(
                sorted([
                    (lk.ent, lk.ent.father.encoded_id if lk.ent.father is not None and lk.ent.first_person(u) else '', True)
                    for lk in Links.objects.filter(user=u)
                    if not lk.ent.backtrace_deleted
                ], key=lambda tu: tu[0].name)
            )
        path_s = [{'fid': f.encoded_id, 'name': f.name} for f in e.path]
        # st = time.time()

        cre_edi = [(f[0].create_name_uid_dt_str, f[0].edit_name_uid_dt_str) for f in sons]
        # cre_edi = [(('1', '2', '3'), ('4', '5', '6'))] * len(sons)

        # print(f'time cost: {time.time()-st:.2f}\t\t' * 100)
        sons_s = [{
            'pfid': pfid,
            'type': f.type, 'id': f.encoded_id, 'name': f.name,
            'is_link': is_link, 'is_starred': Collection.objects.filter(user=u, ent=f).exists(),
            'create_dt': cdt, 'cuid': cuid, 'cname': cnm,
            'edit_dt': edt, 'euid': euid, 'ename': enm,
        } for (f, pfid, is_link), ((cnm, cuid, cdt), (enm, euid, edt)) in zip(sons, cre_edi)]

        return 0, cur_time(), path_s, sons_s, e.name


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
            'delete_dt': f.ent.delete_dt_str, 'is_dia': False,  # todo
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
        if not e.first_person(u):
            return E.no_father

        return 0, e.father.encoded_id


class FSDocInfo(View):
    @JSR('status', 'name', 'size', 'cuid', 'cname', 'is_locked', 'path')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no, E.no_fa = 2, 3, 4
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
        if e is None:
            return E.no

        if e.father is None or not e.first_person(u):
            return E.no_fa

        cnm, cid, cdt = e.create_name_uid_dt_str
        return (
            0, e.name, len(e.plain_content),
            cid, cnm,
            e.is_locked, [{'fid': f.encoded_id, 'name': f.name} for f in e.path]
        )


class FSFoldInfo(View):
    @JSR('status', 'name', 'cuid', 'cname', 'path')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no, E.no_fa = 2, 3, 4
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
        if e is None:
            return E.no

        if e.father is None or not e.first_person(u):
            return E.no_fa

        cnm, cid, cdt = e.create_name_uid_dt_str
        return (
            0, e.name,
            cid, cnm,
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
        if e.brothers_dup_name(name):
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
        E.au, E.uni, E.already, E.not_found, E.taowa = 2, 3, 4, 5, 6
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

        dest = Entity.get_via_encoded_id(kwargs['pfid'])
        if dest is None or dest.is_doc():
            return E.not_found

        if e.father is not None and e.father.id == dest.id:
            return E.already

        if dest.sons_dup_name(e.name):
            return E.uni

        if any(e.bfs_apply(func=lambda ent: ent.id == dest.id)):
            return E.taowa

        e.move(dest)

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
        E.au, E.not_found, E.dup_name, E.no_fa = 2, 3, 4, 5
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        # todo: 更多权限判断
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'id', 'type'}:
            return E.k

        e = Entity.objects.filter(id=int(decode(kwargs['id'])))
        if not e.exists():
            return E.not_found
        e = e.get()
        if not e.is_deleted:
            return E.not_found

        if e.father.backtrace_deleted:
            return E.no_fa
        if e.brothers_dup_name(e.name):
            return E.dup_name
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

        e = Entity.objects.filter(id=int(decode(kwargs['id'])))
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
