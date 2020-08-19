from django.db.models import QuerySet, Q
from django.views import View
from easydict import EasyDict as ED
import json

from misc.views import check_auth, get_auth, WriteMem, CommentMem, ReadMem, ShareMem
from teamwork.hypers import DOC_AUTH
from user.models import User
from datetime import datetime
from entity.models import Entity
from fusion.models import Collection, Links, Trajectory, EditLock
from record.models import upd_record_create, upd_record_write, FocusingRecord, upd_record_comment, upd_record_read
from utils.cast import decode, cur_time
from utils.meta_wrapper import JSR
from entity.hypers import *
from typing import List, Tuple
from teamwork.models import Team
from utils.xml import xml_auto_merge


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

        records = u.read_records.all()
        ent_dt: List[Tuple[Entity, str]] = [
            (rec.ent, rec.dt_str)
            for rec in records if not rec.ent.backtrace_deleted and rec.ent.is_doc()
        ][:15]

        return 0, cur_time(), [{
            'pfid': e.father.encoded_id if e.father is not None and e.father.first_person(u) else '',
            'name': e.name,
            'dt': dt,
            'type': e.type,
            'id': e.encoded_id,
            'is_starred': Collection.objects.filter(user=u, ent=e).exists(),
        } for e, dt in ent_dt]


class WorkbenchStar(View):
    @JSR('status', 'cur_dt', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k, E.au = -1, 1, 2
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        if request.GET.keys() != set():
            return E.k

        ents = [c.ent for c in u.collections.all() if not c.ent.backtrace_deleted]
        return 0, cur_time(), [{
            'pfid': e.father.encoded_id if e.father is not None and e.father.first_person(u) else '',
            'name': e.name,
            'create_dt': e.create_dt_str,
            'edit_dt': e.edit_dt_str,
            'type': e.type,
            'id': e.encoded_id,
            'cname': e.creator.name,
            'is_starred': True  # Collection.objects.filter(user=u, ent=e).exists(),
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

        try:
            page, each = int(kwargs.get('page')), int(kwargs.get('each'))
        except (TypeError, ValueError):
            return E.u

        records = u.create_records.all()
        amount = records.count()
        ents = [rec.ent for rec in records if not rec.ent.backtrace_deleted][(page - 1) * each: page * each]

        return 0, amount, cur_time(), [{
            'pfid': e.father.encoded_id if e.father is not None else '',
            'name': e.name,
            'create_dt': e.create_dt_str,
            'edit_dt': e.edit_dt_str,
            'type': e.type,
            'id': e.encoded_id,
            'cname': e.creator.name,
            'is_starred': Collection.objects.filter(user=u, ent=e).exists(),
        } for e in ents]


class WorkbenchShare(View):
    # todo: tky double-check
    @JSR('status', 'cur_dt', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k, E.au = -1, 1, 2
        if not request.session.get('is_login', False):
            return E.au

        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        ws = [a for a in WriteMem.objects.filter(user=u).all() if not a.auth.ent.backtrace_deleted]
        cs = [a for a in CommentMem.objects.filter(user=u).all() if not a.auth.ent.backtrace_deleted]
        rs = [a for a in ReadMem.objects.filter(user=u).all() if not a.auth.ent.backtrace_deleted]
        ss = [a for a in ShareMem.objects.filter(user=u).all() if not a.auth.ent.backtrace_deleted]
        ents = sorted(ws + cs + rs + ss, key=lambda e: e.dt)
        ents = [a.auth.ent if isinstance(a, WriteMem) else a.auth.ent if isinstance(a, CommentMem) else a.auth.ent for a in ents]
        return 0, cur_time(), [{
            'type': e.type,
            'auth': DOC_AUTH.write if WriteMem.objects.filter(user=u, auth__ent=e).exists() else 'comment' if CommentMem.objects.filter(user=u, auth__ent=e).exists() else 'read',
            'view_dt': e.read_dt_str,
            'edit_dt': e.edit_dt_str,
            'name': e.name,
            'id': e.encoded_id,
            'cname': e.creator.name,
            'is_starred': Collection.objects.filter(user=u, ent=e).exists(),
        } for e in ents if e.creator != u]


# class SearchMain(View):
#     @JSR('result', 'tags', 'wrong_msg', 'amount')
#     def post(self, request):
#         kwargs: dict = json.loads(request.body)
#         if kwargs.keys() != {'key', 'limit', 'order', 'tags', 'page', 'each'}:
#             return -1, '参数错误'
#         sent, lim, tags, page, each = kwargs['key'], kwargs['limit'], set(kwargs['tags']), kwargs['page'], kwargs[
#             'each']
#         if not sent:
#             return [], [], '不准搜空字符串'
#
#         aset: QuerySet = Article.objects.all()[0:0]
#         rset: QuerySet = Resource.objects.all()[0:0]
#         for k in sent.split():
#             if lim & 1:
#                 rset = rset.union(
#                     Resource.objects.filter(
#                         Q(title__icontains=k) | Q(content__icontains=k),
#                         blocked=False
#                     ), *[
#                         u.resource_author.all()
#                         for u in User.objects.filter(name__icontains=k, blocked=False)
#                     ]
#                 )
#             if lim & 2:
#                 aset = aset.union(
#                     Article.objects.filter(
#                         Q(title__icontains=k) | Q(content__icontains=k),
#                         recycled=False, blocked=False
#                     ), *[
#                         u.article_author.all()
#                         for u in User.objects.filter(name__icontains=k, blocked=False)
#                     ]
#                 )
#         es = sorted(
#             [e for e in aset] + [e for e in rset],
#             key=lambda e: e.create_time if kwargs['order'] == 1 else e.views,
#             reverse=kwargs['order'] != 1
#         )
#         func = (lambda elem: set([tag.name for tag in elem.tags_qset().all()]) & tags) if len(tags) else lambda _: True
#         res = list(filter(func, es))
#         amount = len(res)
#         res = res[(page - 1) * each:page * each]
#         return (
#             [{
#                 'rid' if isinstance(elem, Resource) else 'aid': elem.id
#             } for elem in res],
#             list(set().union(*[[t.name for t in elem.tags_qset().all()] for elem in res])),
#             '', amount
#         )


class WorkbenchSearch(View):
    @JSR('status', 'cur_dt', 'list')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au = 2
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'key', 'limit', 'ord', 'towards'}:
            return E.k
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        keyword, lim, ord, towards = kwargs.get('key'), kwargs.get('limit'), kwargs.get('ord'), kwargs.get('towards')

        res_set = set()
        for a in keyword.split():
            if lim == 0:
                res_set = res_set.union(
                    set([e.ent for e in u.create_records.filter(Q(ent__name__icontains=a) | Q(ent__trajectories__updated_content__icontains=a))]),
                    set([e.ent for e in u.read_records.filter(Q(ent__name__icontains=a) | Q(ent__trajectories__updated_content__icontains=a))])
                )
            elif lim == 1:
                res_set = res_set.union(
                    set([e.ent for e in u.create_records.filter(Q(ent__type='doc') & (Q(ent__name__icontains=a) | Q(ent__trajectories__updated_content__icontains=a)))]),
                    set([e.ent for e in u.read_records.filter(Q(ent__type='doc') & (Q(ent__name__icontains=a) | Q(ent__trajectories__updated_content__icontains=a)))])
                )
            elif lim == 2:
                res_set = res_set.union(
                    set([e.ent for e in u.create_records.filter(Q(ent__type='fold') & (Q(ent__name__icontains=a) | Q(ent__trajectories__updated_content__icontains=a)))]),
                    set([e.ent for e in u.read_records.filter(Q(ent__type='fold') & (Q(ent__name__icontains=a) | Q(ent__trajectories__updated_content__icontains=a)))])
                )
            else:
                return E.k
        if ord == 1:
            res_set = sorted(list(res_set), key=lambda e: e.create_dt_str)
        elif ord == 2:
            res_set = sorted(list(res_set), key=lambda e: e.edit_dt_str)
        else:
            return E.k
        if towards == 1:
            res_set.reverse()

        res_set = list(filter(lambda e: not e.backtrace_deleted, res_set))
        return 0, cur_time(), [{
            'pfid': e.father.encoded_id if e.father else '',
            'name': e.name,
            'content': e.plain_content[:400] if e.type == 'doc' and e.trajectories.all().count() else '',
            'create_dt': e.create_dt_str,
            'edit_dt': e.edit_dt_str,
            'type': e.type,
            'id': e.encoded_id,
            'cname': e.creator.name,
            'is_starred': Collection.objects.filter(user=u, ent=e).exists(),
        } for e in res_set]


class DocAuth(View):
    @JSR('status', 'auth')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = request.GET
        if kwargs.keys() != {'did'}:
            return E.k
        did = kwargs.get('did')

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.no_ent

        return 0, get_auth(u, e)


class DocEdit(View):
    @JSR('status', 'ver')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.inv_name, E.inv_cont, E.rename, E.need_to_merge, E.auto_merged = 2, 3, 4, 5, 6, 7
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'name', 'did', 'ver', 'auth', 'content'}:
            return E.k

        name, did, ver, auth, content = kwargs['name'], kwargs['did'], str(kwargs['ver']), kwargs['auth'], kwargs['content']
        if auth not in [DOC_AUTH.write, DOC_AUTH.comment]:
            return E.k

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.u
        if not check_auth(user=u, ent=e, auth=auth, double_check_deleted=False):
            return E.au

        if e.brothers_dup_name(name):
            return E.rename
        if not CHECK_ENAME(name):
            return E.inv_name
        e.name = name

        auto_mg = False
        cvi = e.cur_ver_id
        if cvi != ver:
            merged = xml_auto_merge(content, e.content)
            if merged is not None:
                auto_mg = True
                content = merged
            else:
                return E.need_to_merge, cvi

        e.content = content
        upd_record_write(user=u, ent=e) if auth == DOC_AUTH.write else upd_record_comment(user=u, ent=e)
        traj = Trajectory(
            ent=e,
            user=u,
            updated_content=content,
            initial=False
        )

        try:
            traj.save()
            e.save()
        except:
            return E.u

        return E.auto_merged if auto_mg else 0, traj.id


class DocAll(View):
    # todo: upd record
    @JSR('status', 'ver', 'name', 'content', 'locked_uid')
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent = 2, 3
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = request.GET
        if kwargs.keys() != {'did', 'ver'} and kwargs.keys() != {'did'}:
            return E.k
        did = kwargs.get('did')
        ver = str(kwargs.get('ver', '-1'))

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.no_ent
        if not check_auth(u, e, DOC_AUTH.read):
            return E.au

        cvi = e.cur_ver_id
        if ver == '-1':
            ver = cvi

        q = e.trajectories.filter(id=ver)
        if not q.exists():
            return E.no_ent
        traj: Trajectory = q.get()
        upd_record_read(u, e)
        lock = EditLock.objects.filter(ent=e)
        return 0, e.cur_ver_id, e.name, traj.updated_content, lock.get().user.encoded_id if lock.exists() else ''


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
    # @JSR('status', 'is_locked')
    # def get(self, request):
    #     E = ED()
    #     E.u, E.k = -1, 1
    #     E.au, E.no_ent = 2, 3
    #     if not request.session.get('is_login', False):
    #         return E.au
    #     u = User.get_via_encoded_id(request.session['uid'])
    #     if u is None:
    #         return E.au
    #     kwargs: dict = request.GET
    #     if kwargs.keys() != {'did'}:
    #         return E.k
    #
    #     did = kwargs.get('did')
    #
    #     e = Entity.get_via_encoded_id(did)
    #     if e is None:
    #         return E.no_ent
    #     return 0, e.is_locked

    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k = -1, 1
        E.au, E.no_ent, E.is_locked = 2, 3, 4
        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'did', 'op'}:
            return E.k

        did, op = kwargs['did'], kwargs['op']

        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.no_ent
        if not op:
            try:
                lock = EditLock.objects.get(user=u, ent=e)
            except:
                return E.is_locked
            try:
                lock.delete()
            except:
                return E.u
        else:
            lock = EditLock.objects.filter(ent=e)
            if lock.exists():
                l = lock.get()
                if l.user == u:
                    l.dt = datetime.now()
                else:
                    if (datetime.now() - l.dt).seconds > LOCK_CONTAIN_TIME:
                        l.user = u
                        l.dt = datetime.now()
                    else:
                        return E.is_locked
                try:
                    l.save()
                except:
                    return E.u
            else:
                EditLock.objects.create(user=u, ent=e)
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
        upd_record_create(u, e)
        if e.is_doc():
            Trajectory.objects.create(
                ent=e,
                user=u,
                updated_content='',
                initial=True
            )
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
            'pfid': pfid, 'can_share': False if u != e.creator and ((u != e.backtrace_root_team.owner) if e.backtrace_root_team else False) else True,
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

        new_ent = e.replicate(u, fa)
        Trajectory.objects.create(
            ent=new_ent,
            user=u,
            updated_content=new_ent.content,
            initial=True
        )

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


class FSStarCondition(View):
    @JSR('is_starred', 'status')
    def get(self, request):
        E = ED()
        E.u, E.k, E.au, E.ne = -1, 1, 2, 3
        if not request.session.get('is_login', False):
            return False, E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return False, E.au
        kwargs: dict = request.GET
        if kwargs.keys() != {'id', 'type'}:
            return False, E.k
        e = Entity.objects.filter(id=int(decode(kwargs.get('id'))))
        if not e.exists():
            return False, E.ne
        e = e.get()
        if e.is_deleted:
            return False, E.ne

        if check_auth(u, e, DOC_AUTH.write) or check_auth(u, e, DOC_AUTH.comment) or check_auth(u, e, DOC_AUTH.read):
            return Collection.objects.filter(user=u, ent=e).exists(), 0
        else:
            return False, 0


class DocumentOnline(View):
    @JSR('status', 'list', 'locked_uid')
    def get(self, request):
        E = ED()
        E.u, E.k, E.au, E.no_ent = -1, 1, 2, 3

        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = request.GET
        if kwargs.keys() != {'did'}:
            return E.k

        e: Entity = Entity.get_via_encoded_id(kwargs.get('did'))
        if e is None:
            return E.no_ent

        FocusingRecord.focus(u, e)
        lock = EditLock.objects.filter(ent=e)
        return 0, [
            {
                'uid': r.user.encoded_id,
                'acc': r.user.acc,
                'name': r.user.name,
                'portrait': r.user.portrait
            }
            for r in e.focusing_records.all()
            if r.obj_focusing()
        ], lock.get().user.encoded_id if lock.exists() else ''


class VersionQuery(View):
    @JSR('status', 'is_newest')
    def get(self, request):
        E = ED()
        E.u, E.k, E.au, E.no_ent = -1, 1, 2, 3

        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = request.GET
        if kwargs.keys() != {'did', 'ver'}:
            return E.k

        e = Entity.get_via_encoded_id(kwargs.get('did'))
        if e is None:
            return E.no_ent

        return 0, str(kwargs.get('ver')) == e.cur_ver_id


class DocumentHistory(View):
    @JSR('status', 'cur_dt', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k, E.au, E.no_ent = -1, 1, 2, 3

        if not request.session.get('is_login', False):
            return E.au
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        kwargs = request.GET
        if kwargs.keys() != {'did'}:
            return E.k

        e: Entity = Entity.get_via_encoded_id(kwargs.get('did'))
        if e is None:
            return E.no_ent

        trajs = e.trajectories.filter(initial=False)
        trajs, too_old = trajs[15:], trajs[:15]
        too_old.delete()

        return 0, cur_time(), [
            {
                'ver': traj.id,
                'dt': traj.dt_str,
                'portrait': traj.user.portrait,
                'name': traj.user.name,
            }
            for traj in trajs
        ]
