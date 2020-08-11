import json
import os
import random
import string


from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from easydict import EasyDict
from django.views import View
from django.db.utils import IntegrityError, DataError

from mainpage.models import Complain, Message
from resource.hypers import DEFAULT_FILE_ROOT
from user.models import User, Follow
from user.hypers import *
from utils.response import JSR
from article.models import Article


class Register(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.acc, E.pwd, E.name, E.uni = 1, 2, 3, 4

        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'account', 'password', 'name'}:
            return E.uk,
        if not CHECK_ACC(kwargs['account']):
            return E.acc,
        if not CHECK_PWD(kwargs['password']):
            return E.pwd,
        if not CHECK_NAME(kwargs['name']):
            return E.name,

        kwargs.update({'email' if '@' in kwargs['account'] else 'tel': kwargs['account']})
        kwargs.pop('account')
        kwargs.update({'profile_photo': DEFAULT_PROFILE_ROOT + '\handsome.jpg'})
        kwargs.update({'point': 5})

        try:
            u = User.objects.create(**kwargs)
        except IntegrityError:
            return E.uni,  # 字段unique未满足
        except DataError:
            return E.uk,  # 诸如某个CharField超过了max_len的错误
        except:
            return E.uk,
        request.session['is_login'] = True
        request.session['uid'] = u.id
        print(u.profile_photo.path)
        request.session.save()
        return 0,


class Login(View):
    @JSR('count', 'status')
    def post(self, request):
        if request.session.get('is_login', None):
            u = User.objects.get(request.session['uid'])
            if u.login_date != date.today():
                u.login_date = date.today()
                u.point += 5
                u.wrong_count = 0
                try:
                    u.save()
                except:
                    return 0, -1
            return 0, 0

        E = EasyDict()
        E.uk = -1
        E.exist, E.pwd, E.max_wrong, E.block = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'account', 'password'}:
            return 0, E.uk

        u = (User.objects.filter(email=kwargs['account']) if '@' in kwargs['account']
             else User.objects.filter(tel=kwargs['account']))
        if not u.exists():
            return 0, E.exist
        u = u.get()

        if u.login_date != date.today():
            u.login_date = date.today()
            u.point += 5
            u.wrong_count = 0
            try:
                u.save()
            except:
                return u.wrong_count, E.uk

        if u.blocked:
            return u.wrong_count, E.block

        if u.wrong_count == MAX_WRONG_PWD:
            return u.wrong_count, E.max_wrong

        if u.password != kwargs['password']:
            u.wrong_count += 1
            try:
                u.save()
            except:
                return 0, -1
            return u.wrong_count, E.pwd

        u.verify_vip()
        request.session['is_login'] = True
        request.session['uid'] = u.id
        request.session['name'] = u.name
        request.session['identity'] = u.identity
        request.session.save()
        u.session_key = request.session.session_key
        try:
            u.save()
        except:
            return u.wrong_count, E.uk
        return u.wrong_count, 0

    @JSR('status')
    def get(self, request):
        if request.session.get('is_login', None):
            request.session.flush()
            return 0
        else:
            return -1


class Member(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.exist = 1

        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'time'}:
            return E.uk

        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return E.exist
        u = u.get()

        if u.vip_time < date.today():
            u.vip_time = date.today()
        u.vip_time = u.vip_time + relativedelta(months=int(kwargs['time']))
        u.identity = 'vip'
        try:
            u.save()
        except:
            return E.uk
        request.session['identity'] = 'vip'
        request.save()
        return 0

    @JSR('date', 'is_member')
    def get(self, request):
        if dict(request.GET).keys() != {'uid'}:
            return '', False
        try:
            uid = int(request.GET.get('uid'))
        except:
            return '', False
        u = User.objects.filter(id=uid)
        if not u.exists():
            return '', False
        u = u.get()
        is_vip = u.verify_vip()
        try:
            u.save()
        except:
            return '', False
        return u.vip_date.strftime("%Y-%m-%d") if is_vip else '', is_vip


class SimpleUserInfo(View):
    @JSR('name', 'portrait', 'is_member', 'account', 'uid')
    def get(self, request):
        try:
            uid = int(request.session.get('uid', None))
        except:
            return '', '', False, '', ''
        u = User.objects.filter(id=uid)
        if not u.exists():
            return '', '', False, '', ''
        u = u.get()
        if u.login_date != date.today():
            u.login_date = date.today()
            u.point += 5
            u.wrong_count = 0
            try:
                u.save()
            except:
                return '', '', False, '', ''
        return u.name, u.profile_photo.path, u.verify_vip(), u.email if u.email is not None else u.tel, u.id


class ChangeAccount(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.pwd, E.acc, E.exist = 1, 2, 3
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'account', 'password'}:
            return E.uk,

        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return E.uk,
        u = u.get()

        if not CHECK_ACC(kwargs['account']):
            return E.acc,
        if u.password != kwargs['password']:
            return E.pwd,

        attr = 'email' if '@' in kwargs['account'] else 'tel'
        if User.objects.filter(**{attr: kwargs['account']}).exists():
            return E.exist,
        setattr(u, attr, kwargs['account'])
        try:
            u.save()
        except:
            return E.uk,
        return 0,


class ChangePassword(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.wr_pwd, E.same_pwd, E.ill_pwd = 1, 2, 3
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'old_password', 'new_password'}:
            return E.uk

        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return E.uk
        u = u.get()

        if kwargs['old_password'] != u.password:
            return E.wr_pwd
        if kwargs['old_password'] == kwargs['new_password']:
            return E.same_pwd
        if not CHECK_PWD(kwargs['new_password']):
            return E.ill_pwd

        u.password = kwargs['new_password']
        try:
            u.save()
        except:
            return E.uk
        return 0


class FollowList(View):
    @JSR('uid', 'amount')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return [], 0
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except ValueError:
            return [], 0

        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return [], 0
        u = u.get()

        follow_set = Follow.objects.filter(follower=u).all().order_by('id')[(page - 1) * each: page * each]
        li = [u.followed.id for u in follow_set]
        return li, len(li)

    @JSR('status')
    def post(self, request):
        # 关注或取关
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'uid', 'condition'}:
            return -1
        uid = kwargs['uid']
        uf = User.objects.filter(id=uid)
        if not uf.exists():
            return 1,
        uf = uf.get()

        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return 1,
        u = u.get()

        if uid == request.session['uid']:
            return 2,
        if Follow.objects.filter(follower=u, followed=uf).exists():
            Follow.objects.filter(follower=u, followed=uf).delete()
        else:
            f = Follow()
            f.followed = uf
            f.follower = u
            f.save()
        return 0,


class FanList(View):
    @JSR('uid', 'status')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return [], 0
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except ValueError:
            return [], 0

        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return [], 0
        u = u.get()

        follow_set = Follow.objects.filter(followed=u).order_by('id')[(page - 1) * each: page * each]
        li = [u.follower.id for u in follow_set]
        return li, len(li)


class FansAndFollows(View):
    @JSR('fans', 'follows')
    def get(self, request):
        if dict(request.GET).keys() != {'uid'}:
            return 0, 0
        try:
            uid = int(request.GET.get('uid'))
        except:
            return 0, 0
        u = User.objects.filter(id=uid)
        if not u.exists():
            return 0, 0
        u = u.get()
        return Follow.objects.filter(followed=u).count(), Follow.objects.filter(follower=u).count()


class UserAllData(View):
    @JSR('views', 'views_inc', 'likes', 'likes_inc', 'comments', 'comments_inc')
    def get(self, request):
        if dict(request.GET).keys() != {'uid'}:
            return tuple([0] * 6)
        try:
            uid = int(request.GET.get('uid'))
        except:
            return tuple([0] * 6)
        user = User.objects.filter(id=uid)
        if not user.exists():
            return tuple([0] * 6)
        user.get()
        user.get_data_day()
        user.get_data_count()
        return user.view_count, user.view_day, user.like_count, user.like_day, user.comment_count, user.comment_day


class UserInfo(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.name, E.school, E.company, E.job, E.intro = 1, 2, 3, 4, 5

        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'name', 'sex', 'birthday', 'school', 'company', 'job', 'introduction', 'src'}:
            return E.uk,
        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return E.uk,
        u = u.get()

        if not CHECK_NAME(kwargs['name']):
            return E.name,
        if str(kwargs['sex']) not in GENDER_DICT.keys():
            return E.uk,
        if not CHECK_DESCS(kwargs['school']):
            return E.school,
        if not CHECK_DESCS(kwargs['company']):
            return E.company,
        if not CHECK_DESCS(kwargs['job']):
            return E.job,
        if not CHECK_DESCS(kwargs['introduction']):
            return E.intro,
        u.name = kwargs['name']
        u.gender = kwargs['sex']

        bir = kwargs['birthday']
        for ch in (_ for _ in bir if not _.isdigit() and _ != '-'):
            bir = bir.split(ch)[0]
        u.birthday = datetime.strptime(bir, '%Y-%m-%d').date()
        u.school = kwargs['school']
        u.company = kwargs['company']
        u.job = kwargs['job']
        u.intro = kwargs['introduction']

        try:
            u.save()
        except:
            return E.uk,
        return 0,

    @JSR('uid', 'name', 'sex', 'birthday', 'school', 'company', 'job', 'introduction')
    def get(self, request):
        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return '', '', 2, '', '', '', '', ''
        u = u.get()
        return u.id, u.name, int(u.gender), u.birthday.strftime('%Y-%m-%d'), u.school, u.company, u.job, u.intro


class SideUserInfo(View):
    @JSR('name', 'portrait', 'is_member', 'introduction', 'condition')
    def get(self, request):
        print(dict(request.GET).keys())
        if dict(request.GET).keys() != {'uid'}:
            return '', '', False, '', ''
        try:
            uid = int(request.GET.get('uid'))
        except:
            return '', '', False, '', ''
        u = User.objects.filter(id=uid)
        if not u.exists():
            return '', '', False, '', ''
        u = u.get()
        if request.session.get('is_login', None):
            me = User.objects.get(id=request.session['uid'])
            condition = 1 if Follow.objects.filter(follower=me, followed=u).exists() else 0
        else:
            condition = -1
        return u.name, u.profile_photo.path, u.verify_vip(), u.intro, condition


class UserInfoCard(View):
    @JSR('info', 'name', 'is_member', 'introduction', 'src', 'is_follow')
    def get(self, request):
        if dict(request.GET).keys() != {'uid'}:
            return [], '', False, '', '', ''
        try:
            uid = int(request.GET.get('uid'))
        except:
            return [], '', False, '', '', ''
        u = User.objects.filter(id=uid)
        if not u.exists():
            return [], '', False, '', '', ''
        u = u.get()
        uid = request.session.get('uid', None)
        if uid != None:
            user = User.objects.get(id=uid)
            is_follow = 1 if Follow.objects.filter(follower=user, followed=u) else 0
        else:
            is_follow = -1
        info = []
        if u.birthday != date(1900, 1, 1):
            info.append({'key': '生日', 'value': u.birthday.strftime("%Y-%m-%d")})
        if u.gender != '0':
            info.append({'key': '性别', 'value': u.get_gender_display()})
        if u.school != '':
            info.append({'key': '学校', 'value': u.school})
        if u.company != '':
            info.append({'key': '公司', 'value': u.company})
        if u.job != '':
            info.append({'key': '职位', 'value': u.job})
        return info, u.name, u.verify_vip(), u.intro, u.profile_photo.path, is_follow


class ComplainUser(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'aid', 'reason'}:
            return -1, '参数错误'
        if not User.objects.filter(id=kwargs['aid']).exists():
            return 1, '文章不存在'
        article = User.objects.filter(id=kwargs['aid']).get()
        m = Complain(owner=u, content=kwargs['reason'], article=article)
        m.save()
        return 0, ''


class StatisticsCard(View):
    @JSR('views', 'points', 'stars', 'likes')
    def get(self, request):
        uid = request.session.get('uid', None)
        if uid:
            u = User.objects.filter(id=uid).get()
            if u.login_date != date.today():
                u.get_data_day()
                u.get_data_count()
            return u.view_day, u.point, u.star_count, u.like_count
        else:
            return 0, 0, 0, 0


class ArticleViewCard(View):
    @JSR('article')
    def get(self, request):
        if dict(request.GET).keys() != {'atc_num'}:
            return []
        try:
            atc_num = int(request.GET.get('atc_num'))
        except:
            return []
        article = Article.objects.all().order_by('-view_day')[0:atc_num]
        return [{'title': i.title, 'simple_content': i.abstract, 'new_view': i.view_day, 'aid': i.id} for i in article]


class ChangeProfile(View):
    @JSR('src', 'status', 'wrong_msg')
    def post(self, request):
        errc = EasyDict()
        errc.unknown = -1
        errc.toobig = 1

        file = request.FILES.get("profile", None)
        if not file:
            return '', errc.unknown, '获取图片失败'
        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return '', errc.unknown, '获取用户失败'
        u = u.get()

        if u.file_size + file.size > MAX_UPLOADED_FSIZE:
            return '', errc.toobig, '上传头像的大小超过了限制(1MB)'

        file_name = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(FNAME_DEFAULT_LEN)]) + '.' + str(file.name).split(".")[-1]
        file_path = os.path.join(DEFAULT_PROFILE_ROOT, file_name)
        with open(file_path, 'wb') as dest:
            [dest.write(chunk) for chunk in file.chunks()]
        u.profile_photo = file_path
        try:
            u.save()
        except:
            return '', errc.unknown, '头像保存失败'
        return file_path, 0, ''


class GetMessage(View):
    @JSR('amount', 'message', 'dict')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return 0, [], []
        try:
            uid = int(request.session['uid'])
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return 0, [], []
        mes = Message.objects.filter(owner_id=uid).order_by('-time')
        amount = mes.count()
        mes = mes[(page - 1) * each: page * each]
        a = []
        li = []
        for i in mes:
            if i.article_comment:
                b = i.article_comment
                if b.fa_comment and b.fa_comment.author.id != uid:
                    content = b.author.name + " 回复了您的评论 " + b.fa_comment.content + " ：" + b.content
                else:
                    content = b.author.name + " 评论了您的文章 " + b.fa_article.title + " ：" + b.content
                a.append({'time': i.time.strftime("%Y-%m-%d %H-%M-%S"), 'content': content, 'condition': i.condition, 'aid': b.id})
                li.append({'aid': b.fa_article_id})
            elif i.resource_comment:
                b = i.resource_comment
                if b.fa_comment and b.fa_comment.author.id != uid:
                    content = b.author.name + " 回复了您的评论 " + b.fa_comment.content + " ：" + b.content
                else:
                    content = b.author.name + " 评论了您的资源 " + b.fa_resource.title + " ：" + b.content
                a.append({'time': i.time.strftime("%Y-%m-%d %H-%M-%S"), 'content': content, 'condition': i.condition, 'rid': b.id})
                li.append({'rid': b.fa_resource_id})
            else:
                b = i.complain
                content = "您的举报已被处理：" + b.content + " 处理结果：" + "通过" if b.result else "不通过"
                a.append({'time': i.time.strftime("%Y-%m-%d %H-%M-%S"), 'content': content, 'condition': i.condition, 'mid': b.id})

        return amount, a, li


# class GetComplainInfo(View):
#     @JSR('time', 'condition', 'id')
#     def get(self, request):
#

class ComplainList(View):
    @JSR('amount', 'list')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return 0, []
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return 0, []
        m = Complain.objects.all().order_by('-create_time')
        amount = m.count()
        m = m[(page - 1) * each: page * each]
        return amount, [i.id for i in m]


class DealComplain(View):
    @JSR('amount', 'list')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return 0, []
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return 0, []
        m = Complain.objects.all().order_by('-create_time')
        amount = m.count()
        m = m[(page - 1) * each: page * each]
        return amount, [i.id for i in m]

    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'mid', 'condition', 'reason'}:
            return -1, ''
        m = Complain.objects.filter(id='mid')
        if not m.exists():
            return -1, ''
        m = m.get()
        if kwargs['condition']:
            if m.article_comment:
                a = m.article_comment
                a.blocked = True
                a.save()
            elif m.resource_comment:
                a = m.resource_comment
                a.blocked = True
                a.save()
            elif m.article:
                a = m.article
                a.blocked = True
                a.save()
            elif m.resource:
                a = m.resource
                a.blocked = True
                a.save()
            elif m.user:
                a = m.user
                a.blocked = True
                a.save()
            m.result = True
        else:
            m.result = False
        m.save()
        Message.objects.create(owner=m.owner, complain=m)
        return 0, ''


class GetNews(View):
    @JSR('amount', 'list')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return 0, []
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return 0, []
        u = Follow.objects.filter(follower_id=request.session['uid'])
        a = []
        for i in u:
            e = i.followed
            a = a + [q for q in e.article_author.filter(recycled=False, blocked=False)]
            a = a + [q for q in e.resource_author.filter(recycled=False, blocked=False)]
        a = sorted(a, key=lambda e: e.create_time, reverse=False)
        b = [{'aid' if isinstance(q, Article) else 'rid': q.id} for q in a]
        amount = len(b)
        b = b[(page - 1) * each: page * each]
        return amount, b

