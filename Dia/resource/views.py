import json
import random
import re
import string
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from easydict import EasyDict
from django.http import JsonResponse, FileResponse
from django.views import View
from django.db.models import Count, F, Q, Min
from resource.models import Resource, ResourceComment, Download
from mainpage.models import Complain, Tag, ResourceCollect, Collection, Message
from user.models import User
import os
from utils.response import JSR
from resource.hypers import *


class ResourceUploadLimit(View):
    @JSR('size', 'byte')
    def get(self, request):
        return MAX_UPLOADED_FSIZE_DESC, MAX_UPLOADED_FSIZE


class CollectResource(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'cid', 'rid'}:
            return -1, '参数错误'
        col = Collection.objects.filter(id=kwargs['cid'])
        if not col.exists():
            return 1, '收藏夹不存在'
        col = col.get()
        res = Resource.objects.filter(id=kwargs['rid'], blocked=False)
        if not res.exists():
            return -1, '资源不存在'
        res = res.get()
        src_list = ResourceCollect.objects.filter(user=col, resource=res)
        if src_list.exists():
            return 2, '资源已经在收藏夹内'
        ResourceCollect.objects.create(user=col, resource=res)
        res.who_star.add(col.owner)
        if res.star_date != date.today():
            res.star_date = date.today()
            res.star_day = 0
        res.star_day = res.star_day + 1
        res.who_star.add(User.objects.get(id=request.session['uid']))
        res.save()
        return 0, ''


class CollectionMoveResource(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'src', 'dst', 'rid'}:
            return -1, '参数错误'
        col_src = Collection.objects.filter(id=kwargs['src'])
        if not col_src.exists():
            return 1, '原收藏夹不存在'
        col_src = col_src.get()
        col_dst = Collection.objects.filter(id=kwargs['dst'])
        if not col_dst.exists():
            return 1, '新收藏夹不存在'
        col_dst = col_dst.get()
        res = Resource.objects.filter(id=kwargs['rid'])
        if not res.exists():
            return -1, '资源不存在'
        res = res.get()
        src_list = ResourceCollect.objects.filter(user=col_src, resource=res)
        if not src_list.exists():
            return -1, '资源不在原收藏夹内'
        src_list.delete()
        dst_list = ResourceCollect.objects.filter(user=col_dst, resource=res)
        if dst_list.exists():
            return -1, '资源已在新收藏夹内'
        ResourceCollect.objects.create(user=col_dst, resource=res)
        return 0, ''


class CollectionRemoveResource(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'rid'} and kwargs.keys() != {'rid', 'cid'}:
            return -1, '参数错误'
        res = Resource.objects.filter(id=kwargs['rid'], blocked=False)
        if not res.exists():
            return -1, '资源不存在'
        res = res.get()
        src_list = ResourceCollect.objects.filter(user__owner_id=request.session['uid'], resource=res)
        if not src_list.exists():
            return 1, '用户没有收藏该资源'
        src_list.delete()
        if res.star_date != date.today():
            res.star_date = date.today()
            res.star_day = 0
        res.star_day = res.star_day - 1
        res.who_star.remove(User.objects.get(id=request.session['uid']))
        res.save()
        return 0, ''


class ResourceUploadFile(View):
    @JSR('src', 'status', 'wrong_msg')
    def post(self, request):
        errc = EasyDict()
        errc.unknown = -1
        errc.toobig = 1

        file = request.FILES.get("file", None)
        if not file:
            return '', errc.unknown, '获取文件失败'
        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return '', errc.unknown, '获取用户失败'
        u = u.get()
        
        if u.file_size + file.size > MAX_UPLOADED_FSIZE:
            return '', errc.toobig, f'上传资源的总大小超过了限制({MAX_UPLOADED_FSIZE_DESC})'

        file_name = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(FNAME_DEFAULT_LEN)]) + '.' + str(file.name).split(".")[-1]
        file_path = os.path.join(DEFAULT_FILE_ROOT, file_name)
        with open(file_path, 'wb') as dest:
            [dest.write(chunk) for chunk in file.chunks()]
        return file_name, 0, ''


class ResourceNew(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        errc = EasyDict()
        errc.unknown = -1
        errc.notfound = 1
        errc.notag = 2
        errc.notitle = 3
        errc.title_toolong = 4
        
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'title', 'introduction', 'tags', 'points', 'src', 'rid'} and kwargs.keys() != {'title', 'introduction', 'tags', 'points', 'rid'}:
            return errc.unknown, '参数错误'

        if kwargs['tags'] == '':
            return errc.notag, '标签为空'
        
        if kwargs['tags'] == '':
            return errc.notitle, '名称为空'
        
        if len(kwargs['tags']) > FNAME_DEFAULT_LEN:
            return errc.title_toolong, '名称过长'

        if kwargs['rid'] == 0:
            res = Resource.objects.create(author_id=request.session['uid'], title=kwargs['title'], content=kwargs['introduction'], points=kwargs['points'], file_path=kwargs['src'])
        else:
            res = Resource.objects.filter(id=kwargs['rid'])
            if res.exists():
                res = res.get()
                res.title = kwargs['title']
                res.content = kwargs['introduction']
                res.points = kwargs['points']
                res.tagged_resource.clear()
        if len(kwargs['tags']):
            res.tag = kwargs['tags'][0]
            for t in kwargs['tags']:
                tag = Tag.objects.filter(name=t)
                if tag.exists():
                    tag = tag.get()
                else:
                    tag = Tag.objects.create(name=t)
                tag.resource.add(res)
                tag.save()
        res.save()
        return 0, ''


class ResourceUploadList(View):
    @JSR('rid', 'amount')
    def get(self, request):
        if dict(request.GET).keys() == {'page', 'each', 'uid'}:
            try:
                uid = int(request.GET.get('uid'))
            except:
                return [], 0
        elif dict(request.GET).keys() != {'page', 'each'}:
            return [], 0
        else:
            uid = int(request.session['uid'])
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except ValueError:
            return [], 0
        res = Resource.objects.filter(author_id=uid, blocked=False)
        num = res.count()
        res = res[(page - 1) * each:page * each]
        return [i.id for i in res], num


class ResourceInfoForEdit(View):
    @JSR('title', 'points', 'size', 'views', 'comment', 'likes', 'stars', 'detail')
    def get(self, request):
        if dict(request.GET).keys() != {'rid'}:
            return '', 0, '', 0, 0, 0, 0, []
        try:
            rid = int(request.GET.get('rid'))
        except ValueError:
            return '', 0, '', 0, 0, 0, 0, []
        res = Resource.objects.filter(id=rid).get()
        comment = ResourceComment.objects.filter(fa_resource=res).count()
        detail = [{'key': 'create_time', 'value': res.create_time}]
        return res.title, res.points, res.file_size, res.views, comment, res.stars, detail


class ResourceDownloadList(View):
    @JSR('rid', 'amount')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return [], 0
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except ValueError:
            return [], 0
        resource = Download.objects.filter(owner=User.objects.filter(id=request.session['uid']).get())
        num = resource.count()
        resource = resource[(page - 1) * each:page * each]
        rid = []
        for i in resource:
            rid.append(i.id)
        return rid, num


class ResourceDelete(View):
    @JSR('src', 'status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'rid'}:
            return '', 1, '参数错误'

        res = Resource.objects.filter(id=kwargs['rid'])
        if res.exists():
            res = res.get()
            file_path = res.file_path.path
            res.delete()
            return file_path, 0, ''
        else:
            return '', 1, '没有该文件'


class ResourceInfo(View):
    @JSR('title', 'description', 'views', 'stars', 'likes', 'comments', 'points', 'tags', 'ruid', 'user_options', 'detail')
    def get(self, request):
        if dict(request.GET).keys() != {'rid'}:
            return '', '', 0, 0, 0, 0, 0, [], 0, {}, []
        try:
            rid = int(request.GET.get('rid'))
        except ValueError:
            return '', '', 0, 0, 0, 0, 0, [], 0, {}, []
        res = Resource.objects.filter(id=rid).get()
        comment = ResourceComment.objects.filter(fa_resource=res).count()
        tags = [i.name for i in res.tagged_resource.all()]
        if not request.session['uid']:
            op = {'is_like': -1, 'is_star': -1, 'is_buy': -1}
        else:
            is_like = 1 if res.who_like.filter(id=request.session['uid']).exists() else 0
            is_star = 1 if res.who_star.filter(id=request.session['uid']).exists() else 0
            is_buy = 1 if res.who_buy.filter(id=request.session['uid']).exists() else 0
            op = {'is_like': is_like, 'is_star': is_star, 'is_buy': is_buy}
        detail = [{'key': '创建时间', 'value': res.create_time}, {'key': '资源大小', 'value': res.file_size}]
        if res.view_date != date.today():
            res.view_day = 0
        res.view_day += 1
        res.views += 1
        res.save()
        return res.title, res.content, res.views - 1, res.who_star.count(), res.who_like.count(), comment, res.points, tags, res.author_id, op, detail


# class DownloadResource(View):
#     @JSR('src', 'status', 'wrong_msg')
#     def post(self, request):
#         kwargs: dict = json.loads(request.body)
#         if kwargs.keys() != {'rid'}:
#             return '', -1, '参数错误'
#         if Resource.objects.filter(id=kwargs['rid']).exists():
#             res = Resource.objects.filter(id=kwargs['rid']).get()
#             u = User.objects.filter(id=request.session['uid']).get()
#             if u.point < res.points and u != res.author:
#                 return '', 1, '余额不足'
#             if u != res.author:
#                 u.point -= res.points
#                 res.who_buy.add(u)
#             file = open(res.file_path)
#             return file, 0, ''
#         else:
#             return '', -1, '没有该文件'


class DownloadResource(View):
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'rid'}:
            return JsonResponse({'src': '', 'status': -1, 'wrong_msg': ''})
        if Resource.objects.filter(id=kwargs['rid']).exists():
            res = Resource.objects.filter(id=kwargs['rid']).get()
            u = User.objects.filter(id=request.session['uid']).get()
            if u.point < res.points and u != res.author:
                return JsonResponse({'src': '', 'status': 1, 'wrong_msg': '余额不足'})
            if u != res.author:
                u.point -= res.points
                res.who_buy.add(u)

            filename = res.title + '.' + str(res.file_path).split(".")[-1]
            filepath = os.path.join(DEFAULT_FILE_ROOT, res.file_path)
            if not os.path.isfile(filepath):
                return JsonResponse({'src': '', 'status': 2, 'wrong_msg': '文件不存在'})
            file = open(filepath, 'rb')
            response = FileResponse(file)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
            return response


class GetResourceComment(View):
    @JSR('comment', 'amount')
    def get(self, request):
        if dict(request.GET).keys() != {'rid', 'page', 'each'}:
            return [], 0
        try:
            rid = int(request.GET.get('rid'))
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except ValueError:
            return [], 0
        comment = ResourceComment.objects.filter(fa_resource=rid, blocked=False).order_by('-create_time')
        num = comment.count()
        comment = comment[(page - 1) * each:page * each]
        a = []
        for i in comment:
            a.append(i.id)
        return a, num


class LikeResource(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'rid', 'condition'}:
            return -1, '参数错误'
        if not Resource.objects.filter(id=kwargs['rid']).exists():
            return 1, '资源不存在'
        res = Resource.objects.filter(id=kwargs['rid']).get()
        if kwargs['condition']:
            if res.like_date != date.today():
                res.like_date = date.today()
                res.like_day = 0
            res.like_day = res.like_day + 1
            res.who_like.add(u)
        else:
            if res.like_date != date.today():
                res.like_date = date.today()
                res.like_day = 0
            res.like_day = res.like_day - 1
            res.who_like.remove(u)
        res.save()
        return 0, ''


class ComplainResource(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'rid', 'reason'}:
            return -1, '参数错误'
        if not Resource.objects.filter(id=kwargs['rid']).exists():
            return 1, '资源不存在'
        res = Resource.objects.filter(id=kwargs['rid']).get()
        m = Complain(owner=u, content=kwargs['reason'], resource=res)
        m.save()
        return 0, ''


class ResourceCommentInfo(View):
    @JSR('qid', 'content', 'likes', 'user_options', 'ruid', 'name', 'portrait', 'is_member', 'time', 'header')
    def get(self, request):
        if dict(request.GET).keys() != {'qid'}:
            return tuple([''] * 10)
        try:
            qid = int(request.GET.get('qid'))
        except:
            return tuple([''] * 10)
        comment = ResourceComment.objects.filter(id=qid)
        if not comment.exists():
            return tuple([''] * 10)
        comment = comment.get()
        is_like = -1
        if request.session.get('uid', None) and User.objects.filter(id=request.session['uid']).exists():
            u = User.objects.filter(id=request.session['uid']).get()
            is_like = 0
            if u in comment.who_like.all():
                is_like = 1
        is_its = 0
        if request.session.get('uid', None) and comment.author.id == request.session['uid']:
            is_its = 1
        user_options = {'is_like': is_like, 'is_its': is_its}
        ruid = comment.author.id
        name = comment.author.name
        portrait = comment.author.profile_photo.url
        is_member = 0
        if comment.author.verify_vip():
            is_member = 1
        if datetime.now() - comment.create_time < timedelta(minutes=5):
            time = '刚刚'
        elif datetime.now() - comment.create_time < timedelta(hours=1):
            time = str((datetime.now() - comment.create_time).seconds // 60) + "分钟前"
        elif datetime.now() - comment.create_time < timedelta(days=1):
            time = str((datetime.now() - comment.create_time).seconds // 3600) + "小时前"
        elif datetime.now() - relativedelta(months=1) < comment.create_time:
            time = str((datetime.now() - comment.create_time).days) + "天前"
        elif datetime.now() - relativedelta(years=1) < comment.create_time:
            time = str((datetime.now() - comment.create_time).days // 30) + "月前"
        else:
            time = str((datetime.now() - comment.create_time).days // 365) + "年前"
        header = ''
        if comment.fa_comment:
            header = '回复 ' + comment.fa_comment.author.name + '：'
        return qid, comment.content, comment.who_like.count(), user_options, ruid, name, portrait, is_member, time, header


class SubmitResourceComment(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'rid', 'content', 'pqid'}:
            return -1, '参数错误'
        res = Resource.objects.filter(id=kwargs['rid'])
        if not res.exists():
            return 1, '资源不存在'
        res = res.get()
        if kwargs['pqid'] == -1:
            rc = ResourceComment.objects.create(content=kwargs['content'], fa_resource=res, author=u)
        else:
            fc = ResourceComment.objects.filter(id=kwargs['pqid'])
            if not fc.exists():
                return 2, '父评论不存在'
            rc = ResourceComment.objects.create(content=kwargs['content'], fa_resource=res, author=u, fa_comment_id=kwargs['pqid'])
            Message.objects.create(owner=rc.fa_comment.author, resource_comment=rc)
        if res.comment_date != date.today():
            res.comment_date = date.today()
            res.comment_day = 0
        res.comment_day = res.comment_day + 1
        res.save()
        Message.objects.create(owner=res.author, resource_comment=rc)
        return 0, ''


class DelResourceComment(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'qid'}:
            return -1, '参数错误'
        if not ResourceComment.objects.filter(id=kwargs['qid']).exists():
            return -1, '评论不存在'
        rc = ResourceComment.objects.filter(id=kwargs['qid']).get()
        if request.session['uid'] != rc.author_id:
            return 1, '没有权限'
        ResourceComment.objects.filter(fa_comment_id=kwargs['qid']).delete()
        ResourceComment.objects.filter(id=kwargs['qid']).delete()
        return 0, ''


class LikeResourceComment(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'qid', 'condition'}:
            return -1, '参数错误'
        if not ResourceComment.objects.filter(id=kwargs['qid']).exists():
            return -1, '评论不存在'
        rc = ResourceComment.objects.filter(id=kwargs['qid']).get()
        if kwargs['condition']:
            rc.who_like.add(u)
            return 0, ''
        else:
            rc.who_like.remove(u)
        return 0, ''


class ComplainResourceComment(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'qid', 'reason'}:
            return -1, '参数错误'
        if not ResourceComment.objects.filter(id=kwargs['qid']).exists():
            return 1, '评论不存在'
        rc = ResourceComment.objects.filter(id=kwargs['qid']).get()
        m = Complain(owner=u, content=kwargs['reason'], resource_comment=rc)
        try:
            m.save()
        except:
            return -1, '保存错误'
        return 0, ''


class ResourceView(View):
    @JSR('title', 'simple_content', 'views', 'stars', 'likes', 'comments', 'tag', 'author_name', 'author_is_member', 'author_portrait_url', 'ruid')
    def get(self, request):
        if dict(request.GET).keys() != {'rid'}:
            return tuple([''] * 11)
        try:
            aid = int(request.GET.get('rid'))
        except:
            return tuple([''] * 11)
        res = Resource.objects.filter(id=aid, blocked=False)
        if not res.exists():
            return tuple([''] * 11)
        res = res.get()
        u = res.author
        return res.title, re.sub(r'\s+', ' ', res.content)[0:200], res.views, res.who_star.count(), res.who_like.count(), res.comment_resource.count(), res.tag, u.name, u.verify_vip(), u.profile_photo.path, u.id


class RelativeResource(View):
    @JSR('resource')
    def get(self, request):
        if dict(request.GET).keys() == {'rid', 'count'}:
            try:
                rid = int(request.GET.get('rid'))
                count = int(request.GET.get('count'))
            except:
                return []
        else:
            return []
        a = Resource.objects.filter(id=rid)
        try:
            a = a.get()
        except:
            return []
        prs = []
        sa = set([t.name for t in a.tagged_resource.all()])
        for o in Resource.objects.all():
            sb = set([t.name for t in o.tagged_resource.all()])
            cr = sa & sb
            if len(cr):
                prs.append((len(cr), o))
        return [{
            'rid': b.id,
            'title': b.title
        } for b in list(zip(*sorted(prs, key=lambda x: x[0])))[1] if b != a][:count]
