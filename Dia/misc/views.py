from django.shortcuts import redirect
from django.views import View

from entity.models import Entity
from meta_config import HELL_WORDS, HOST_IP
from teamwork.hypers import DOC_AUTH_CHS, DOC_AUTH
from user.models import User
from utils.cast import encode
from utils.meta_wrapper import JSR
from misc.models import *
from easydict import EasyDict as ED

from Dia import settings
import random
import string
import json
from user.hypers import *


def check_auth(user: User, ent: Entity, auth: str, double_check_deleted: bool = True) -> bool:
    if user is None or ent is None:
        return False
    if double_check_deleted and ent.backtrace_deleted:
        return False
    if ent.first_person(user):
        return True
    if ent.is_locked:
        return False
    assert auth in list(zip(*DOC_AUTH_CHS))[0]
    
    wt, ct, rt = (WriteMem, 'write'), (CommentMem, 'comment'), (ReadMem, 'read')
    cfgs = {
        DOC_AUTH.write: (wt, ),
        DOC_AUTH.comment: (ct, wt),
        DOC_AUTH.read: (rt, ct, wt),
    }
    return any(
        clz.objects.filter(**{'user': user, f'{au}__ent': ent}).exists()
        for clz, au in cfgs[auth]
    )


def get_auth(user: User, ent: Entity, double_check_deleted: bool = True) -> str:
    if user is None or ent is None:
        return DOC_AUTH.none
    if double_check_deleted and ent.backtrace_deleted:
        return DOC_AUTH.none
    if ent.first_person(user):
        return DOC_AUTH.write
    if ent.is_locked:
        return DOC_AUTH.none

    if WriteMem.objects.filter(user=user, auth__ent=ent).exists():
        return DOC_AUTH.write
    if CommentMem.objects.filter(user=user, auth__ent=ent).exists():
        return DOC_AUTH.comment
    if ReadMem.objects.filter(user=user, auth__ent=ent).exists():
        return DOC_AUTH.read


class HellWords(View):
    @JSR('words', 'status')
    def get(self, request):
        return HELL_WORDS, 0


class UploadImg(View):
    @JSR('code', 'url')
    def post(self, request):
        print('receive img')
        file = request.FILES.get('img')
        file_name = ''.join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(FNAME_DEFAULT_LEN)]) + '.' + \
                    str(file.name).split(".")[-1]
        file_path = os.path.join(DEFAULT_IMG_ROOT, file_name)
        with open(file_path, 'wb') as dest:
            [dest.write(chunk) for chunk in file.chunks()]
        return 0, 'http://47.96.109.229/static/upload/img/' + file_name


def get_key():
    key = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(FNAME_DEFAULT_LEN)])
    if ShareAuth.objects.filter(key=key).exists():
        return get_key()
    return key


class ResetKey(View):
    @JSR('status', 'key')
    def post(self, request):
        E = ED()
        E.u, E.k, E.au, E.nf = -1, 1, 2, 3
        if not request.session.get('is_login', False):
            return E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'did', 'is_clear'}:
            return E.k
        did = kwargs.get('did')
        is_clear = kwargs.get('is_clear')
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.k
        if e.type == 'fold' or e.backtrace_deleted:
            return E.k
        try:
            sa = ShareAuth.objects.get(ent=e)
        except:
            return E.u
        if not sa.can_share(u):
            return E.au
        if is_clear:
            sa.user.clear()
        sa.key = get_key()
        sa.save()
        return 0, sa.key


class FSShareKey(View):
    @JSR('status', 'key', 'auth')
    def post(self, request):
        E = ED()
        E.u, E.k, E.au, E.nf = -1, 1, 2, 3
        if not request.session.get('is_login', False):
            return E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'did'}:
            return E.k
        did = kwargs.get('did')
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.nf
        if e.type == 'fold' or e.backtrace_deleted:
            return E.k

        sa = ShareAuth.objects.filter(ent=e)
        if not sa.exists():
            sa = ShareAuth.objects.create(ent=e)
            sa.add_owner(e.creator)
            team = e.backtrace_root_team
            if team is not None:
                sa.add_owner(team.owner)
            sa.key = get_key()
            sa.save()
        else:
            sa = sa.get()
        if sa.can_share(u):
            return 0, sa.key, sa.auth
        else:
            return E.au, '', 'no_share'


class ChangeShareAuth(View):
    @JSR('status')
    def post(self, request):
        E = ED()
        E.u, E.k, E.au, E.nf = -1, 1, 2, 3
        if not request.session.get('is_login', False):
            return E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'did', 'auth'}:
            return E.k
        did = kwargs.get('did')
        auth = kwargs.get('auth')
        if auth not in ['no_share', 'write', 'comment', 'read']:
            return E.k
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.nf
        if e.type == 'fold' or e.backtrace_deleted:
            return E.k
        sa = ShareAuth.objects.filter(ent=e)
        if not sa.exists():
            sa = WriteAuth.objects.create(ent=e)
            sa.add_owner(e.creator)
            team = e.backtrace_root_team
            if team is not None:
                sa.add_owner(team.owner)
            sa.key = get_key()
            sa.save()
        else:
            sa = sa.get()
        if not sa.can_share(u):
            return E.au
        try:
            sa.auth = auth
            sa.save()
        except:
            return E.u
        return 0

class AuthFileList(View):
    @JSR('status', 'list')
    def get(self, request):
        E = ED()
        E.u, E.k, E.au, E.nf = -1, 1, 2, 3
        if not request.session.get('is_login', False):
            return E.au
        kwargs: dict = request.GET
        if kwargs.keys() != {'did'}:
            return E.k
        did = kwargs.get('did')
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return E.au
        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.nf
        if e.type == 'fold' or e.backtrace_deleted:
            return E.k
        if u != e.creator and (u != e.backtrace_root_team.owner) if e.backtrace_root_team else False:
            return E.au
        wa = WriteAuth.objects.filter(ent=e)
        ca = CommentAuth.objects.filter(ent=e)
        ra = ReadAuth.objects.filter(ent=e)
        res = []
        if wa.exists():
            wa = wa.get()
            res.extend([{
                'uid': encode(u.id), 'src': u.portrait, 'acc': u.acc, 'auth': 'write'
            }for u in wa.get_user_list()])
        if ca.exists():
            ca = ca.get()
            res.extend([{
                'uid': encode(u.id), 'src': u.portrait, 'acc': u.acc, 'auth': 'comment'
            }for u in ca.get_user_list()])
        if ra.exists():
            ra = ra.get()
            res.extend([{
                'uid': encode(u.id), 'src': u.portrait, 'acc': u.acc, 'auth': 'read'
            }for u in ra.get_user_list()])
        return 0, res


class ChangeMemberAuth(View):
    @JSR('status', 'is_new', 'user_info')
    def post(self, request):
        E = ED()
        E.u, E.k, E.au, E.nf, E.nu = -1, 1, 2, 3, 4
        if not request.session.get('is_login', False):
            return E.au
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'did', 'acc', 'auth', 'is_new'}:
            return E.k
        did = kwargs.get('did')
        auth = kwargs.get('auth')
        is_new = kwargs.get('is_new')
        if auth not in ['no_share', 'write', 'comment', 'read']:
            return E.k
        try:
            u = User.objects.get(acc=kwargs.get('acc'))
        except:
            return E.nu
        me = User.get_via_encoded_id(request.session['uid'])
        if me is None:
            return E.au
        e = Entity.get_via_encoded_id(did)
        if e is None:
            return E.nf
        if e.type == 'fold' or e.backtrace_deleted:
            return E.k
        if me != e.creator and (me != e.backtrace_root_team.owner) if e.backtrace_root_team else False:
            return E.au
        if u == me or (me == e.backtrace_root_team.owner) if e.backtrace_root_team else False:
            return 5

        wa = WriteAuth.objects.filter(ent=e)
        can_write = wa.exists() and u in wa.get().get_user_list()
        if can_write:
            if is_new:
                return 6
            if auth != 'write':
                wa.get().remove_auth(u)
            else:
                return 0, {'uid': encode(u.id), 'name': u.name, 'src': u.portrait}
        elif auth == 'write':
            wa.get().add_auth(u)
            return 0, {'uid': encode(u.id), 'name': u.name, 'src': u.portrait}
        ca = CommentAuth.objects.filter(ent=e)
        can_comment = ca.exists() and u in ca.get().get_user_list()
        if can_comment:
            if is_new:
                return 6
            if auth != 'comment':
                ca.get().remove_auth(u)
            else:
                return 0, {'uid': encode(u.id), 'name': u.name, 'src': u.portrait}
        elif auth == 'comment':
            ca.get().add_auth(u)
            return 0, {'uid': encode(u.id), 'name': u.name, 'src': u.portrait}
        ra = ReadAuth.objects.filter(ent=e)
        can_read = ra.exists() and u in ra.get().get_user_list()
        if can_read:
            if is_new:
                return 6
            if auth != 'read':
                ra.get().remove_auth(u)
            else:
                return 0, {'uid': encode(u.id), 'name': u.name, 'src': u.portrait}
        elif auth == 'read':
            ra.get().add_auth(u)
        return 0, {'uid': encode(u.id), 'name': u.name, 'src': u.portrait}

        # wa = WriteAuth.objects.filter(ent=e)
        # if not wa.exists():
        #     wa = WriteAuth.objects.create(ent=e)
        #     wa.add_auth(e.creator)
        #     wa.key = self.get_key(DOC_AUTH.write)
        #     wa.save()
        # else:
        #     wa = wa.get()
        #
        # if auth == DOC_AUTH.write:
        #     if not WriteMem.objects.filter(user=u, write_auth=wa).exists():
        #         return E.au, ''
        #     else:
        #         return 0, wa.key
        # if auth == DOC_AUTH.comment:
        #     ca = CommentAuth.objects.filter(ent=e)
        #     if not ca.exists():
        #         ca = CommentAuth.objects.create(ent=e)
        #         ca.key = self.get_key(DOC_AUTH.comment)
        #         ca.save()
        #     else:
        #         ca = ca.get()
        #     if not CommentMem.objects.filter(user=u, comment_auth=ca).exists() and not WriteMem.objects.filter(user=u, write_auth=wa).exists():
        #         return E.au, ''
        #     else:
        #         return 0, ca.key
        # if auth == DOC_AUTH.read:
        #     ra = ReadAuth.objects.filter(ent=e)
        #     if not ra.exists():
        #         ra = ReadAuth.objects.create(ent=e)
        #         ra.key = self.get_key(DOC_AUTH.read)
        #         ra.save()
        #     else:
        #         ra = ra.get()
        #     ca = CommentAuth.objects.filter(ent=e)
        #     wf = True if WriteMem.objects.filter(user=u, write_auth=wa).exists() else False
        #     rf = True if ReadMem.objects.filter(user=u, read_auth=ra).exists() else False
        #     if (ca.exists() and CommentMem.objects.filter(user=u, comment_auth=ca.get()).exists()) or rf or wf:
        #         return 0, ra.key
        #     else:
        #         return E.au, ''
        # return E.k, ''
#
#
class AddShare(View):
    def get(self, request):
        E = ED()
        E.u, E.k = -1, 1
        u = User.get_via_encoded_id(request.session['uid'])
        if u is None:
            return redirect('/login')
        kwargs = request.GET
        if kwargs.keys() != {'dk'}:
            return redirect('/workbench/recent_view')
        ra = ShareAuth.objects.filter(key=kwargs.get('dk'))
        if not ra.exists():
            return redirect('/workbench/recent_view')
        try:
            ra = ra.get()
            if ra.ent.backtrace_deleted or ra.auth == 'no_share':
                return redirect('/workbench/recent_view')
            ra.add_auth(u)
        except:
            return redirect('/workbench/recent_view')
        return redirect('/doc/' + ra.ent.encoded_id)
#
#
# class AddCommentAuth(View):
#     def get(self, request):
#         E = ED()
#         E.u, E.k = -1, 1
#         kwargs = request.GET
#         if kwargs.keys() != {'dk'}:
#             return redirect('/workbench/recent_view')
#         u = User.get_via_encoded_id(request.session['uid'])
#         if u is None:
#             return redirect('/login')
#         ca = CommentAuth.objects.filter(key=kwargs.get('dk'))
#         if not ca.exists():
#             return redirect('/workbench/recent_view')
#         try:
#             ca = ca.get()
#             if ca.ent.is_locked:
#                 return redirect('/workbench/recent_view')
#             ca.add_auth(u)
#         except:
#             return redirect('/workbench/recent_view')
#         return redirect('/doc/' + ca.ent.encoded_id)
#
#
# class AddWriteAuth(View):
#     def get(self, request):
#         E = ED()
#         E.u, E.k = -1, 1
#         kwargs = request.GET
#         if kwargs.keys() != {'dk'}:
#             return redirect('/workbench/recent_view')
#         u = User.get_via_encoded_id(request.session['uid'])
#         if u is None:
#             return redirect('/login')
#         wa = WriteAuth.objects.filter(key=kwargs.get('dk'))
#         if not wa.exists():
#             return redirect('/workbench/recent_view')
#         try:
#             wa = wa.get()
#             if wa.ent.is_locked:
#                 return redirect('/workbench/recent_view')
#             wa.add_auth(u)
#         except:
#             return redirect('/workbench/recent_view')
#         return redirect('/doc/' + wa.ent.encoded_id)
