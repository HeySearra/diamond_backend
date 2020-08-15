import json
import random
import string
import hashlib

from datetime import datetime, date
from easydict import EasyDict
from django.views import View
from django.db.utils import IntegrityError, DataError
from django.db.models import Q

from Dia.settings import BASE_DIR
from teamwork.models import Team
from user.models import User, EmailRecord, Message
from user.hypers import *
from utils.cast import encode, decode, cur_time
from utils.network import send_code
from utils.meta_wrapper import JSR
from entity.models import Entity


def send_team_invite_message(team: Team, su: User, mu: User):
    # tid:团队id，suid:发起邀请的用户，muid：接收邀请的用户
    # 我存的数据库原始id，使用msg/info给我发消息时请加密
    m = Message()
    m.owner = mu
    m.sender = su
    m.title = "团队邀请"
    m.content = su.name + " 邀请你加入团队：" + team.name
    m.portrait = team.portrait if team.portrait else ''
    m.related_id = team.id
    m.type = 'join'
    try:
        m.save()
    except:
        return False
    return True


def send_team_out_message(team: Team, mu: User):
    # mu: 被踢出的
    m = Message()
    m.owner = mu
    m.title = "团队消息"
    m.content = "您已被移出团队：" + team.name
    m.portrait = team.portrait if team.portrait else ''
    m.related_id = team.id
    m.type = 'out'
    try:
        m.save()
    except:
        return False
    return True


def send_team_member_out_message(team: Team, su: User, mu: User):
    # mu: 退出的
    m = Message()
    m.owner = mu
    m.sender = su
    m.title = "团队消息"
    m.content = su.name + " 已经退出团队：" + team.name
    m.portrait = team.portrait if team.portrait else ''
    m.related_id = team.id
    m.type = 'out'
    try:
        m.save()
    except:
        return False
    return True


def send_team_dismiss_message(team: Team, mu: User, su:User):
    # mu: 团队解散
    m = Message()
    m.owner = mu
    m.title = "团队消息"
    m.content = "团队 " + team.name + " 已被 " + su.name + " 解散"
    m.portrait = team.portrait if team.portrait else ''
    m.related_id = team.id
    m.type = 'out'
    try:
        m.save()
    except:
        return False
    return True


def send_team_accept_message(team: Team, su: User, mu: User, if_accept: bool):
    # tid:团队id，su:发起邀请的用户，mu:处理邀请的用户，if_accept:是否接受邀请
    # 我存的数据库原始id，使用msg/info给我发消息时请加密
    m = Message()
    m.owner = mu
    m.sender = su
    m.title = "团队邀请"
    m.content = su.name + (" 接受" if if_accept else " 拒绝") + "了您的团队邀请：" + team.name
    m.portrait = team.portrait if team.portrait else ''
    m.related_id = team.id
    m.type = 'accept' if if_accept else 'reject'
    try:
        m.save()
    except:
        return False
    return True


def send_team_admin_message(team: Team, su: User, mu: User):
    # tid:团队id，su:发起添加管理员的用户，mu：刚被设为管理员的用户
    # 我存的数据库原始id，使用msg/info给我发消息时请加密
    m = Message()
    m.owner = mu
    m.sender = su
    m.title = "团队消息"
    m.content = su.name + " 将你设为团队 " + team.name + " 的管理员"
    m.portrait = team.portrait if team.portrait else ''
    m.related_id = team.id
    m.type = 'admin'
    try:
        m.save()
    except:
        return False
    return True


def send_team_admin_cancel_message(team: Team, su: User, mu: User):
    # tid:团队id，su:发起解除管理员的用户，mu：刚被解除管理的用户
    # 我存的数据库原始id，使用msg/info给我发消息时请加密
    m = Message()
    m.owner = mu
    m.sender = su
    m.title = "团队消息"
    m.content = su.name + " 已解除你在团队 " + team.name + " 的管理员"
    m.portrait = team.portrait if team.portrait else ''
    m.related_id = team.id
    m.type = 'out'
    try:
        m.save()
    except:
        return False
    return True


def send_comment_message(comment=(), su=User(), mu=User()):
    # tid:团队id，su:发表评论的用户，mu：文档的拥有者
    # 我存的数据库原始id，使用msg/info给我发消息时请加密
    # 这里没有写完，注释的地方需要完善
    m = Message()
    m.owner = mu
    m.sender = su
    m.title = su.name + " 评论了您的文档："  # + comment.doc.title
    m.content = comment.content
    m.portrait = su.portrait
    m.related_id = comment.id
    m.type = 'doc'
    try:
        m.save()
    except:
        return False
    return True


def hash_password(pwd):
    m = hashlib.md5()
    m.update(pwd.encode('utf-8'))
    m.update(b"It's DiaDoc!")
    return m.digest()


class SearchUser(View):
    @JSR('list', 'status')
    def post(self, request):
        if not request.session['is_login']:
            return [], 2
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'key'}:
            return [], 1
        us = User.objects.filter(Q(name__icontains=kwargs['key']) | Q(acc__icontains=kwargs['key']))
        ulist = []
        for u in us:
            ulist.append({
                'name': u.name,
                'portrait': u.portrait,
                'acc': u.acc,
                'uid': encode(u.id)
            })
        return ulist, 0


class Register(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.key, E.acc, E.pwd, E.code, E.name, E.uni = 1, 2, 3, 4, 5, 6
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'acc', 'ver_code', 'pwd', 'name'}:
            return E.key,
        if not CHECK_ACC(kwargs['acc']):
            return E.acc,
        if not CHECK_PWD(kwargs['pwd']):
            return E.pwd,
        if not CHECK_NAME(kwargs['name']):
            return E.name,
        kwargs.update({'pwd': hash_password(kwargs['pwd'])})
        kwargs.update({'portrait': DEFAULT_PROFILE_ROOT + '\handsome.jpg'})
        er = EmailRecord.objects.filter(code=kwargs['ver_code'], acc=kwargs['acc'])
        if not er.exists():
            return E.code
        er = er.get()
        kwargs.pop('ver_code')

        if datetime.now() < er.expire_time:
            try:
                root = Entity.locate_root(name=kwargs['name'])
                u = User.objects.create(root=root, **kwargs)
            except IntegrityError:
                return E.uni,  # 字段unique未满足
            except DataError as e:
                return E.uk,  # 诸如某个CharField超过了max_len的错误
            except:
                return E.uk,
            request.session['is_login'] = True
            request.session['uid'] = encode(u.id)
            return 0,
        else:
            return 7

    @JSR('status')
    def get(self, request):
        try:
            acc = str(request.GET.get('acc'))
        except:
            return 1,

        if send_code(acc, 'register'):
            return 0,
        else:
            return -1,


class Login(View):
    @JSR('count', 'status')
    def post(self, request):
        if request.session.get('is_login', None):  # 已登录
            try:
                u = User.objects.get(id=int(decode(request.session['uid'])))
            except:
                return 0, -1
            print(1)
            if u.login_date != date.today():
                u.login_date = date.today()
                u.wrong_count = 0
                try:
                    u.save()
                except:
                    return 0, -1
            return 0, 0
        print(2)
        E = EasyDict()
        E.uk = -1
        E.key, E.exist, E.pwd, E.many = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'acc', 'pwd'}:
            return 0, E.key
        print(3)
        u = User.objects.filter(acc=kwargs['acc'])
        if not u.exists():
            return 0, E.exist
        u = u.get()
        print(4)
        if u.login_date != date.today():
            u.login_date = date.today()
            u.wrong_count = 0
            try:
                u.save()
            except:
                return u.wrong_count, E.uk

        if u.wrong_count == MAX_WRONG_PWD:
            return u.wrong_count, E.many
        print(4.5)
        if u.pwd != str(hash_password(kwargs['pwd'])):
            print(5)
            u.wrong_count += 1
            try:
                u.save()
            except:
                return 0, -1
            return u.wrong_count, E.pwd
        print(6)
        request.session['is_login'] = True
        request.session['uid'] = encode(u.id)
        request.session['name'] = u.name
        request.session.save()
        try:
            u.save()
        except:
            return u.wrong_count, E.uk
        return u.wrong_count, 0

    @JSR('status')
    def get(self, request):
        if request.session.get('is_login', None):
            request.session['is_login'] = False
            # request.session.flush()
            return 0
        else:
            return -1


class FindPwd(View):
    @JSR('status')
    def get(self, request):
        if dict(request.GET).keys() != {'acc'}:
            return 1
        try:
            acc = str(request.GET.get('acc'))
        except:
            return -1
        send_code(acc, 'forget')
        return 0


class ForgetSetPwd(View):
    @JSR('status')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'acc', 'pwd', 'key'}:
            return 1,
        u = User.objects.filter(acc=kwargs['acc'])
        if not u.exists():
            return 2,
        u = u.get()
        if not CHECK_PWD(kwargs['pwd']):
            return 3,
        if not EmailRecord.objects.filter(code=kwargs['key']).exists():
            return 4,
        er = EmailRecord.objects.filter(Q(acc=kwargs['acc']) | Q(code=kwargs['key'])).get()
        u.pwd = hash_password(kwargs['pwd'])
        u.save()
        return 0,


class UnreadCount(View):
    @JSR('count', 'status')
    def get(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return 0, -1
        u = u.get()
        count = Message.objects.filter(Q(owner_id=u.id) & Q(is_read=False)).count()
        return count, 0


class AskMessageList(View):
    @JSR('status', 'cur_dt', 'amount', 'list')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return 1, [], 0, ''
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except ValueError:
            return -1, [], 0, ''

        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1, [], 0, ''
        u = u.get()
        messages = Message.objects.filter(owner_id=u.id).order_by('-dt')[(page - 1) * each: page * each]
        msg = []
        for message in messages:
            msg.append({
                'mid': encode(message.id),
                'dt': message.dt_str,
            })
        return 0, cur_time(), len(msg), msg


class AskMessageInfo(View):
    @JSR('status', 'is_read', 'is_process', 'is_dnd', 'title', 'portrait', 'type', 'id', 'content', 'cur_dt', 'dt')
    def get(self, request):
        if dict(request.GET).keys() != {'mid'}:
            return 1, [] * 13
        try:
            mid = int(decode(request.GET.get('mid')))
        except ValueError:
            return -1, [] * 13

        u = User.objects.filter(id=int(decode(request.session['uid'])))

        if not u.exists():
            return -1, [] * 13
        u = u.get()
        msg = Message.objects.filter(id=mid)
        if not msg.exists():
            return -1, [] * 13
        msg = msg.get()
        return 0, msg.is_read, msg.is_process, u.is_dnd, msg.title, msg.portrait, msg.type, encode(msg.related_id) if msg.related_id else '', msg.content, cur_time(), msg.dt_str


class SetMsgRead(View):
    @JSR('status')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'mid'}:
            return 1,
        msg = Message.objects.filter(id=int(decode(kwargs['mid'])))
        if not msg.exists():
            return -1,
        msg = msg.get()
        msg.is_read = True
        msg.save()
        return 0,


class SetAllMsgRead(View):
    @JSR('status')
    def post(self, request):
        msg = Message.objects.all()
        for m in msg:
            m.is_read = True
            m.save()
        return 0,


class SetDnd(View):
    @JSR('status')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'is_dnd'}:
            return 1,
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1,
        u = u.get()
        u.is_dnd = kwargs['is_dnd']
        u.save()
        return 0,

    @JSR('status', 'is_dnd')
    def post(self, request):
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return -1, False
        u = u.get()
        return 0, u.is_dnd


class UserInfo(View):
    @JSR('name', 'portrait', 'acc', 'uid', 'status')
    def get(self, request):
        if not request.session.get('is_login', None):
            return '', '', '', '', 2
        try:
            uid = int(decode(request.session.get('uid', None)))
        except:
            return '', '', '', '', -1
        u = User.objects.filter(id=uid)
        if not u.exists():
            return '', '', '', '', -1
        u = u.get()
        return u.name, u.portrait, u.acc, encode(u.id), 0


class UserEditInfo(View):
    @JSR('status')
    def post(self, request):
        if not request.session['is_login']:
            return 2,
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'name', 'img'}:
            return 1,
        if not CHECK_NAME(kwargs['name']):
            return 3,
        try:
            uid = int(decode(request.session.get('uid', None)))
        except:
            return -1
        u = User.objects.filter(id=uid)
        if not u.exists():
            return -1
        u = u.get()
        u.name = kwargs['name']
        u.portrait = kwargs['img'].replace('\\\\', '\\')
        try:
            u.save()
        except:
            return -1
        return 0


class SetPwd(View):
    @JSR('status')
    def post(self, request):
        if not request.session['is_login']:
            return 2
        E = EasyDict()
        E.uk = -1
        E.key, E.wr_pwd, E.ill_pwd = 1, 2, 3
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'old_pwd', 'new_pwd'}:
            return E.key

        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return E.uk
        u = u.get()

        if kwargs['old_pwd'] != u.pwd:
            return E.wr_pwd
        if not CHECK_PWD(kwargs['new_pwd']):
            return E.ill_pwd

        u.pwd = hash_password(kwargs['new_pwd'])
        try:
            u.save()
        except:
            return E.uk
        return 0


class ChangeProfile(View):
    @JSR('src', 'status')
    def post(self, request):
        errc = EasyDict()
        errc.unknown = -1
        errc.toobig = 3

        file = request.FILES.get("file", None)
        if not file:
            return '', errc.unknown
        u = User.objects.filter(id=int(decode(request.session['uid'])))
        if not u.exists():
            return '', errc.unknown
        u = u.get()

        if file.size > MAX_UPLOADED_FSIZE:
            return '', errc.toobig

        file_name = ''.join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(FNAME_DEFAULT_LEN)]) + '.' + \
                    str(file.name).split(".")[-1]
        file_path = os.path.join(DEFAULT_PROFILE_ROOT, file_name)
        with open(file_path, 'wb') as dest:
            [dest.write(chunk) for chunk in file.chunks()]
        u.portrait = os.path.join(BASE_DIR, file_path)
        try:
            u.save()
        except:
            return '', errc.unknown
        return u.portrait, 0
