import json
import os
import random
import string
import smtplib

from email.mime.text import MIMEText
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from easydict import EasyDict
from django.views import View
from django.db.utils import IntegrityError, DataError
from django.db.models import Q
from email.header import Header
from user.models import User, Follow, EmailRecord, Message
from user.hypers import *
from utils.cast import encode, decode, get_time
from utils.response import JSR


def send_code(email, email_type):
    # 发信方的信息：发信邮箱，QQ 邮箱授权码
    from_addr = 'diadoc@163.com'
    password = 'UTXGEJFQTCJNDAHQ'

    # 收信方邮箱
    to_addr = email

    # 发信服务器
    smtp_server = 'smtp.163.com'

    # 生成随机验证码
    code_list = []
    for i in range(10):  # 0~9
        code_list.append(str(i))
    key_list = []
    for i in range(65, 91):  # A-Z
        key_list.append(chr(i))
    for i in range(97, 123):  # a-z
        key_list.append(chr(i))
    if email_type == 'register':
        code = random.sample(code_list, 6)  # 随机取6位数
        code_num = ''.join(code)
        # 数据库保存验证码！！！！！！！！！！！
        ver_code = EmailRecord()
        ver_code.code = code_num
        ver_code.email = email
        ver_code.send_time = datetime.now()
        ver_code.expire_time = datetime.now()+timedelta(minutes=5)
        ver_code.email_type = email_type

        # 邮箱正文内容，第一个参数为内容，第二个参数为格式(plain 为纯文本)，第三个参数为编码
        msg = MIMEText('验证码为' + code_num, 'plain', 'utf-8')
        msg['Subject'] = Header('金刚石文档注册验证码')
    else:
        code = random.sample(key_list, 10)
        code_num = ''.join(code)

        ver_code = EmailRecord()
        ver_code.code = '/forget/set?acc='+acc+'&key='+code_num
        ver_code.email = email
        ver_code.send_time = datetime.now()
        ver_code.expire_time = datetime.now() + timedelta(minutes=60)
        ver_code.email_type = email_type
        msg = MIMEText('找回密码的链接为:/forget/set?acc='+acc+'&key='+code_num + code_num, 'plain', 'utf-8')
        msg['Subject'] = Header('金刚石文档找回密码')

    # 邮件头信息
    msg['From'] = Header(from_addr)
    msg['To'] = Header(to_addr)

    # 开启发信服务，这里使用的是加密传输
    server = smtplib.SMTP_SSL(host='smtp.163.com')
    server.connect(smtp_server, 465)
    # 登录发信邮箱
    server.login(from_addr, password)
    # 发送邮件
    server.sendmail(from_addr, to_addr, msg.as_string())
    # 关闭服务器
    server.quit()


class SearchUser(View):
    @JSR('list', 'status')
    def post(self, request):
        if not request.session['is_login']:
            return [], 2
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'key'}:
            return [], 1
        us = User.objects.filter(name__icontains=kwargs['key'])
        ulist = []
        for u in us:
            ulist.append({
                'name': u.name,
                'portrait': u.profile_photo,
                'acc': u.email,
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
        kwargs.update({'email': kwargs['acc']})
        kwargs.pop('acc')
        kwargs.update({'profile_photo': DEFAULT_PROFILE_ROOT + '\handsome.jpg'})
        kwargs.update({'point': 5})

        er = EmailRecord.objects.filter(code=kwargs['ver_code'], email=kwargs['acc']).exists()
        if not er:
            return E.code
        er = EmailRecord.objects.filter(code=kwargs['ver_code'], email=kwargs['acc']).get()
        if datetime.now() - er.expire_time > 0:
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
            return 0

        return E.code


class Login(View):
    @JSR('count', 'status')
    def post(self, request):
        if request.session.get('is_login', None):
            u = User.objects.get(decode(request.session['uid']))
            if u.login_date != date.today():
                u.login_date = date.today()
                u.wrong_count = 0
                try:
                    u.save()
                except:
                    return 0, -1
            return 0, 0

        E = EasyDict()
        E.uk = -1
        E.key, E.exist, E.pwd, E.many = 1, 2, 3, 4
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'acc', 'pwd'}:
            return 0, E.key

        u = User.objects.filter(email=kwargs['acc'])
        if not u.exists():
            return 0, E.exist
        u = u.get()

        if u.login_date != date.today():
            u.login_date = date.today()
            u.wrong_count = 0
            try:
                u.save()
            except:
                return u.wrong_count, E.uk

        if u.wrong_count == MAX_WRONG_PWD:
            return u.wrong_count, E.many

        if u.password != kwargs['pwd']:
            u.wrong_count += 1
            try:
                u.save()
            except:
                return 0, -1
            return u.wrong_count, E.pwd

        u.verify_vip()
        request.session['is_login'] = True
        request.session['uid'] = encode(u.id)
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


class RegisterCode(View):
    @JSR('status')
    def get(self, request):
        if dict(request.GET).keys() != {'acc'}:
            return 1
        try:
            acc = str(request.GET.get('acc'))
        except:
            return -1

        send_code(acc, 'register')
        return 0


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


class SetPwd(View):
    @JSR('status')
    def post(self,  request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'acc', 'pwd', 'key'}:
            return 1,
        u = User.objects.filter(email=kwargs['acc'])
        if not u.exists():
            return 2,
        u = u.get()
        if not CHECK_PWD(kwargs['pwd']):
            return 3,
        if not EmailRecord.objects.filter(code=kwargs['key']).exists():
            return 4,
        er = EmailRecord.objects.filter(Q(acc=kwargs['acc']) | Q(code=kwargs['key'])).get()
        u.password = kwargs['pwd']
        u.save()
        return 0,


class UnreadCount(View):
    @JSR('count', 'status')
    def get(self, request):
        u = User.objects.filter(id=decode(request.session['uid']))
        if not u.exists():
            return 0, -1
        u = u.get()
        count = Message.objects.filter(Q(user=u.id) | Q(is_read=False)).count()
        return count, 0


class AskMessageList(View):
    @JSR('status', 'cur_dtdt', 'list')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return 1, [], ''
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except ValueError:
            return -1, [], ''

        u = User.objects.filter(id=decode(request.session['uid']))
        if not u.exists():
            return -1, [], ''
        u = u.get()
        messages = Message.objects.filter(user=u.id).order_by('id')[(page - 1) * each: page * each]
        msg = []
        for message in messages:
            msg.append({
                'mid': encode(message.id),
                'dtdt': datetime.strptime(str(message.dt), "%Y-%m-%d %H:%M:%S"),
            })
        return 0, datetime.strptime(str(datetime.now()), "%Y-%m-%d %H:%M:%S"), msg


class AskMessageInfo(View):
    @JSR('status', 'is_read', 'is_dnd', 'name', 'po', 'content', 'cur_dtdt', 'dt')
    def get(self, request):
        if dict(request.GET).keys() != {'mid'}:
            return 1, []*7
        try:
            mid = int(decode(request.GET.get('page')))
        except ValueError:
            return -1, []*7

        u = User.objects.filter(id=decode(request.session['uid']))

        if not u.exists():
            return -1, []*7
        u = u.get()
        msg = Message.objects.filter(user=u.id)
        if not msg.exists():
            return -1, [] * 7
        msg = msg.get()
        return 0, msg.is_read, u.is_dnd, msg.title, msg.portrait_url, msg.content, get_time(), msg.dt


class SetMsgRead(View):
    @JSR('status')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'mid'}:
            return 1,
        msg = Message.objects.filter(id=decode(kwargs['mid']))
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
        u = User.objects.filter(id=decode(request.session['uid']))
        if not u.exists():
            return -1,
        u = u.get()
        u.is_dnd = kwargs['is_dnd']
        u.save()
        return 0,


class AskDnd(View):
    @JSR('status', 'is_dnd')
    def post(self, request):
        u = User.objects.filter(id=decode(request.session['uid']))
        if not u.exists():
            return -1, False
        u = u.get()
        return 0, u.is_dnd


class Member(View):
    @JSR('status')
    def post(self, request):
        E = EasyDict()
        E.uk = -1
        E.exist = 1

        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'time'}:
            return E.uk

        u = User.objects.filter(id=int(decode(request.session['uid'])))
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
        u = User.objects.filter(id=int(decode(uid)))
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
    @JSR('name', 'portrait', 'acc', 'uid', 'status')
    def get(self, request):
        if not request.session['is_login']:
            return '', '', '', '', 2
        try:
            uid = int(decode(request.session.get('uid', None)))
        except:
            return '', '', '', '', -1
        u = User.objects.filter(id=uid)
        if not u.exists():
            return '', '', '', '', -1
        u = u.get()
        return u.name, u.profile_photo.path, u.email, encode(u.id), 0


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
        if uid is not None:
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

        file_name = ''.join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(FNAME_DEFAULT_LEN)]) + '.' + \
                    str(file.name).split(".")[-1]
        file_path = os.path.join(DEFAULT_PROFILE_ROOT, file_name)
        with open(file_path, 'wb') as dest:
            [dest.write(chunk) for chunk in file.chunks()]
        u.profile_photo = file_path
        try:
            u.save()
        except:
            return '', errc.unknown, '头像保存失败'
        return file_path, 0, ''

# class GetMessage(View):
#     @JSR('amount', 'message', 'dict')
#     def get(self, request):
#         if dict(request.GET).keys() != {'page', 'each'}:
#             return 0, [], []
#         try:
#             uid = int(request.session['uid'])
#             page = int(request.GET.get('page'))
#             each = int(request.GET.get('each'))
#         except:
#             return 0, [], []
#         mes = Message.objects.filter(owner_id=uid).order_by('-time')
#         amount = mes.count()
#         mes = mes[(page - 1) * each: page * each]
#         a = []
#         li = []
#         for i in mes:
#             if i.article_comment:
#                 b = i.article_comment
#                 if b.fa_comment and b.fa_comment.author.id != uid:
#                     content = b.author.name + " 回复了您的评论 " + b.fa_comment.content + " ：" + b.content
#                 else:
#                     content = b.author.name + " 评论了您的文章 " + b.fa_article.title + " ：" + b.content
#                 a.append({'time': i.time.strftime("%Y-%m-%d %H-%M-%S"), 'content': content, 'condition': i.condition, 'aid': b.id})
#                 li.append({'aid': b.fa_article_id})
#             elif i.resource_comment:
#                 b = i.resource_comment
#                 if b.fa_comment and b.fa_comment.author.id != uid:
#                     content = b.author.name + " 回复了您的评论 " + b.fa_comment.content + " ：" + b.content
#                 else:
#                     content = b.author.name + " 评论了您的资源 " + b.fa_resource.title + " ：" + b.content
#                 a.append({'time': i.time.strftime("%Y-%m-%d %H-%M-%S"), 'content': content, 'condition': i.condition, 'rid': b.id})
#                 li.append({'rid': b.fa_resource_id})
#             else:
#                 b = i.complain
#                 content = "您的举报已被处理：" + b.content + " 处理结果：" + "通过" if b.result else "不通过"
#                 a.append({'time': i.time.strftime("%Y-%m-%d %H-%M-%S"), 'content': content, 'condition': i.condition, 'mid': b.id})
#
#         return amount, a, li


# class GetComplainInfo(View):
#     @JSR('time', 'condition', 'id')
#     def get(self, request):
#
#
#
# class GetNews(View):
#     @JSR('amount', 'list')
#     def get(self, request):
#         if dict(request.GET).keys() != {'page', 'each'}:
#             return 0, []
#         try:
#             page = int(request.GET.get('page'))
#             each = int(request.GET.get('each'))
#         except:
#             return 0, []
#         u = Follow.objects.filter(follower_id=request.session['uid'])
#         a = []
#         for i in u:
#             e = i.followed
#             a = a + [q for q in e.article_author.filter(recycled=False, blocked=False)]
#             a = a + [q for q in e.resource_author.filter(recycled=False, blocked=False)]
#         a = sorted(a, key=lambda e: e.create_time, reverse=False)
#         b = [{'aid' if isinstance(q, Article) else 'rid': q.id} for q in a]
#         amount = len(b)
#         b = b[(page - 1) * each: page * each]
#         return amount, b
#
