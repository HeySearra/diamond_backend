import json
import re
import string
from datetime import datetime, timedelta, date
import random

from dateutil.relativedelta import relativedelta
from django.views import View
from article.models import Article, ArticleComment, Column
from mainpage.models import Complain, Tag, Collection, ArticleCollect, Message
from user.models import User, Detail
from utils.response import JSR
from article.hypers import *


class CollectArticle(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'cid', 'aid'}:
            return -1, '参数错误'
        col = Collection.objects.filter(id=kwargs['cid'])
        if not col.exists():
            return 1, '收藏夹不存在'
        col = col.get()
        atc = Article.objects.filter(id=kwargs['aid'], recycled=False, blocked=False)
        if not atc.exists():
            return -1, '文章不存在'
        atc = atc.get()
        src_list = ArticleCollect.objects.filter(user=col, article=atc)
        if src_list.exists():
            return 2, '文章已经在收藏夹内'
        ArticleCollect.objects.create(user=col, article=atc)
        atc.who_star.add(col.owner)
        if atc.star_date != date.today():
            atc.star_date = date.today()
            atc.star_day = 0
        atc.star_day = atc.star_day + 1
        atc.who_star.add(User.objects.get(id=request.session['uid']))
        atc.save()
        return 0, ''


class CollectionRemoveArticle(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'aid'} and kwargs.keys() != {'aid', 'cid'}:
            return -1, '参数错误'

        atc = Article.objects.filter(id=kwargs['aid'], recycled=False, blocked=False)
        if not atc.exists():
            return -1, '文章不存在'
        atc = atc.get()
        src_list = ArticleCollect.objects.filter(user__owner_id=request.session['uid'], article=atc)
        if not src_list.exists():
            return 1, '用户没有收藏该文章'
        src_list.delete()
        if atc.star_date != date.today():
            atc.star_date = date.today()
            atc.star_day = 0
        atc.star_day = atc.star_day - 1
        u = User.objects.get(id=request.session['uid'])
        atc.who_star.remove(u)
        atc.save()
        return 0, ''


class CollectionNew(View):
    @JSR('status', 'cid', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'title', 'condition'}:
            return -1, '参数错误'
        u = User.objects.filter(id=request.session['uid'])
        if not u.exists():
            return -1, 0, ''
        u = u.get()
        col = Collection.objects.filter(name=kwargs['title'], owner_id=request.session['uid'])
        if col.exists():
            return 1, 0, '已存在该收藏夹'
        col = Collection.objects.create(name=kwargs['title'], hide=kwargs['condition'], owner=u)
        return 0, col.id, ''


class CollectionRename(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'cid', 'name'}:
            return -1, '参数错误'
        col = Collection.objects.filter(id=kwargs['cid'])
        if not col.exists():
            return 1, '收藏夹不存在'
        col = col.get()
        col.name = kwargs['name']
        col.save()
        return 0, ''


class CollectionCondition(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'cid', 'condition'}:
            return -1, '参数错误'
        col = Collection.objects.filter(id=kwargs['cid'])
        if not col.exists():
            return 1, '收藏夹不存在'
        col = col.get()
        col.hide = kwargs['condition']
        col.save()
        return 0, ''


class CollectionDelete(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'cid'}:
            return -1, '参数错误'
        if not Collection.objects.filter(id=kwargs['cid']).exists():
            return 1, '不存在该收藏夹'
        Collection.objects.filter(id=kwargs['cid']).delete()
        return 0, ''


class CollectionMoveArticle(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'src', 'dst', 'aid'}:
            return -1, '参数错误'
        col_src = Collection.objects.filter(id=kwargs['src'])
        if not col_src.exists():
            return 1, '原收藏夹不存在'
        col_src = col_src.get()
        col_dst = Collection.objects.filter(id=kwargs['dst'])
        if not col_dst.exists():
            return 1, '新收藏夹不存在'
        col_dst = col_dst.get()
        atc = Article.objects.filter(id=kwargs['aid'], recycled=False, blocked=False)
        if not atc.exists():
            return -1, '文章不存在'
        atc = atc.get()
        src_list = ArticleCollect.objects.filter(user=col_src, article=atc)
        if not src_list.exists():
            return -1, '文章不在原收藏夹内'
        src_list.delete()
        dst_list = ArticleCollect.objects.filter(user=col_dst, article=atc)
        if dst_list.exists():
            return -1, '文章已在新收藏夹内'
        ArticleCollect.objects.create(user=col_dst, article=atc)
        return 0, ''


class ArticleList(View):
    @JSR('article', 'amount')
    def get(self, request):
        if dict(request.GET).keys() == {'uid', 'page', 'each'}:
            try:
                uid = int(request.GET.get('uid'))
            except:
                return [], 0
        elif dict(request.GET).keys() != {'page', 'each'}:
            return [], 0
        else:
            uid = request.session['uid']
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return [], 0
        article = Article.objects.filter(author_id=uid, recycled=False, blocked=False).order_by('-is_top', 'edit_time')
        num = article.count()
        article = article[(page - 1) * each: page * each]
        return [{'aid': i.id, 'is_top': i.is_top} for i in article], num


class ArticleInfoForEdit(View):
    @JSR('title', 'simple_content', 'views', 'stars', 'likes', 'comments', 'condition', 'detail', 'tag')
    def get(self, request):
        if dict(request.GET).keys() != {'aid'}:
            return tuple([''] * 9)
        try:
            aid = int(request.GET.get('aid'))
        except:
            return tuple([''] * 9)
        a = Article.objects.filter(id=aid, recycled=False, blocked=False)
        if not a.exists():
            return tuple([] * 9)
        a = a.get()
        comment = ArticleComment.objects.filter(fa_article=a).count()
        detail = [
            {'key': '发布时间', 'value': a.create_time.strftime("%Y-%m-%d %H:%M:%S")},
            {'key': '最近编辑', 'value': a.edit_time.strftime("%Y-%m-%d %H:%M:%S")}
        ]
        return a.title, a.abstract, a.views, a.who_star.count(), a.who_like.count(), comment, a.blocked, detail, a.tag


class EditOrSubmitArticle(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'title', 'tags', 'content', 'aid'}:
            return 1, '参数错误'
        if kwargs['aid'] == 0:
            atc = Article.objects.create(author_id=request.session['uid'], title=kwargs['title'],
                                         content=kwargs['content'])
            if len(kwargs['tags']):
                atc.tag = kwargs['tags'][0]
                for t in kwargs['tags']:
                    tag = Tag.objects.filter(name=t)
                    if tag.exists():
                        tag = tag.get()
                    else:
                        tag = Tag.objects.create(name=t)
                    tag.article.add(atc)
                    tag.save()
        else:
            atc = Article.objects.filter(id=kwargs['aid'], recycled=False, blocked=False)
            atc = atc.get()
            atc.title = kwargs['title']
            atc.content = kwargs['content']
            atc.tagged_article.clear()
            for t in kwargs['tags']:
                tag = Tag.objects.filter(name=t)
                if tag.exists():
                    tag = tag.get()
                else:
                    tag = Tag.objects.create(name=t)
                tag.article.add(atc)
                tag.save()
        atc.edit_time = datetime.now()
        atc.save()
        return 0, ''


class DelArticle(View):
    @JSR('status')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'aid'}:
            return 1
        article = Article.objects.filter(id=kwargs['aid'], recycled=False, blocked=False)
        if not article.exists():
            return -1
        article = article.get()
        article.recycled = True
        article.recycle_time = datetime.now()
        article.save()
        u = User.objects.get(id=request.session['uid'])
        if u.article_id == article.id:
            u.article_id = -1
        u.save()
        return 0


class TopArticle(View):
    # 若当前文章已被置顶，则为取消置顶
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'aid'}:
            return 1, '参数错误'
        atc = Article.objects.filter(id=kwargs['aid'], recycled=False, blocked=False)
        if not atc.exists():
            return 1
        atc = atc.get()
        if atc.blocked or atc.recycled:
            return 2, '文章状态错误'

        user = User.objects.get(id=request.session['uid'])
        if user.article_id == -1:
            atc.is_top = True
        elif user.article_id != atc.id:
            atc_old = Article.objects.get(id=user.article_id)
            atc_old.is_top = False
            atc.is_top = True
            atc_old.save()
        else:
            atc.is_top = False
        user.article_id = atc.id if user.article_id != atc.id else -1
        atc.save()
        user.save()
        return 0, ''


class ColumnList(View):
    @JSR('list', 'amount')
    def get(self, request):
        if dict(request.GET).keys() == {'uid', 'page', 'each'}:
            try:
                uid = int(request.GET.get('uid'))
                page = int(request.GET.get('page'))
                each = int(request.GET.get('each'))
            except:
                return [], 0
        elif dict(request.GET).keys() == {'page', 'each'}:
            try:
                page = int(request.GET.get('page'))
                each = int(request.GET.get('each'))
            except:
                return [], 0
            uid = request.session['uid']
        elif dict(request.GET).keys() == {'uid'}:
            try:
                uid = int(request.GET.get('uid'))
            except:
                return [], 0
            page = -1
        else:
            return [], 0
        column = Column.objects.filter(owner=uid)
        num = len(column)
        if page != -1:
            column = column[(page - 1) * each: page * each]
        c = []
        for i in column:
            c.append({'sid': i.id, 'name': i.title, 'count': i.article_set.count()})
        return c, num


class ColumnArticle(View):
    @JSR('article_list', 'amount')
    def get(self, request):
        if dict(request.GET).keys() == {'sid', 'page', 'each'}:
            try:
                page = int(request.GET.get('page'))
                each = int(request.GET.get('each'))
            except:
                return tuple([''])
        elif dict(request.GET).keys() != {'sid'}:
            return tuple([''])
        else:
            page = -1
        try:
            sid = int(request.GET.get('sid'))
        except:
            return tuple([''])
        column = Column.objects.filter(id=sid).get()
        article = Article.objects.filter(column=column, recycled=False, blocked=False).order_by('-create_time')
        if page != -1:
            article = article[(page - 1) * each: page * each]
        a = []
        for i in article:
            a.append({'aid': i.id, 'title': i.title})
        return a, len(a)


class ArticleInColumn(View):
    @JSR('article_list')
    def get(self, request):
        article = Article.objects.filter(author_id=request.session['uid'], recycled=False, blocked=False).order_by(
            '-edit_time')
        a = []
        for i in article:
            a.append({'aid': i.id, 'title': i.title, 'sid': i.column.id if i.column else ''})
        return a


class EditColumn(View):
    @JSR('status')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'sid', 'article'}:
            return -1
        column = Column.objects.filter(id=kwargs['sid'])
        if not column.exists():
            return -1
        column = column.get()
        column.article_set.clear()
        column.save()
        for i in kwargs['article']:
            i = Article.objects.filter(id=int(i), recycled=False, blocked=False)
            if not i.exists():
                return -1
            i = i.get()
            if i.recycled or i.blocked:
                return -1
            i.column = column
            i.save()
        column.save()
        return 0


class RenameColumn(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'title', 'sid'}:
            return -1, '参数错误'
        if len(kwargs['title']) > MAX_COL_WORDS:
            return 2, f'专栏字数超过限制（{MAX_COL_WORDS}）'
        if Column.objects.filter(title=kwargs['title']).exists():
            return 1, '存在同名专栏'
        column = Column.objects.filter(id=kwargs['sid']).get()
        column.title = kwargs['title']
        column.save()
        return 0, ''


class NewColumn(View):
    @JSR('status', 'wrong_msg', 'sid')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        print(len(kwargs['title']))
        if kwargs.keys() != {'title'}:
            return -1, '参数错误'
        if len(kwargs['title']) > MAX_COL_WORDS:
            return 2, f'专栏字数超过限制（{MAX_COL_WORDS}）'
        if Column.objects.filter(title=kwargs['title']).exists():
            return 1, '存在同名专栏'
        column = Column(title=kwargs['title'], owner_id=request.session['uid'])
        column.save()
        return 0, '', column.id


class DelColumn(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'sid'}:
            return -1, '参数错误'
        if not Column.objects.filter(id=kwargs['sid']).exists():
            return -1, '专栏不存在'
        Column.objects.filter(id=kwargs['sid']).delete()
        return 0, ''


class RecycleList(View):
    @JSR('article', 'amount')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return [], 0
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return [], 0
        atc_tobe_del = Article.objects.filter(author_id=request.session['uid'], recycled=True,
                                              recycle_time__lte=datetime.now() - timedelta(days=15))
        atc_tobe_del.delete()
        article = Article.objects.filter(author_id=request.session['uid'], recycled=True,
                                         recycle_time__gt=datetime.now() - timedelta(days=15)).order_by('-recycle_time')
        num = article.count()
        article = article[(page - 1) * each: page * each]
        a = []
        for i in article:
            a.append(i.id)
        return a, num


class ArticleRecycle(View):
    @JSR('title', 'simple_content', 'detail', 'tag')
    def get(self, request):
        if dict(request.GET).keys() != {'aid'}:
            return tuple([''] * 4)
        try:
            aid = int(request.GET.get('aid'))
        except:
            return tuple([''] * 4)
        a = Article.objects.filter(id=aid, recycled=True, blocked=False)
        if not a.exists():
            return tuple([''] * 4)
        a = a.get()
        detail = [{'key': '删除时间', 'value': a.recycle_time.strftime("%Y-%m-%d %H:%M:%S")}]
        return a.title, a.abstract, detail, a.tag


class Recover(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'aid'}:
            return -1, '参数错误'
        article = Article.objects.filter(id=kwargs['aid'], blocked=False)
        if not article.exists():
            return -1, '文章不存在'
        article = article.get()
        article.recycled = False
        article.save()
        return 0, ''


class DelRecycle(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'aid'}:
            return -1, '参数错误'
        if Article.objects.filter(id=kwargs['aid']).exists():
            Article.objects.filter(id=kwargs['aid']).delete()
            return 0, ''
        return -1, '该文章不存在'


class UploadImage(View):
    @JSR('url', 'status')
    def post(self, request):
        img = request.FILES.get("image", None)
        if not img:
            return '', -1

        file_name = ''.join([random.choice(string.ascii_letters + string.digits)
                             for _ in range(FNAME_DEFAULT_LEN)]) + '.' + str(img.name).split(".")[-1]
        file_path = os.path.join(DEFAULT_IMG_ROOT, file_name)
        with open(file_path, 'wb') as fp:
            [fp.write(c) for c in img.chunks()]
        return file_path, 0


class PointDetailedList(View):
    @JSR('amount', 'list')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return 0, []
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return 0, []
        detail = Detail.objects.filter(owner=request.session['uid']).order_by('-time')
        num = len(detail)
        detail = detail[(page - 1) * each: page * each]
        a = []
        for i in detail:
            a.append({'point': i.point, 'time': i.time, 'content': i.reason})
        return num, a


class GetArticleComment(View):
    @JSR('comment', 'amount')
    def get(self, request):
        if dict(request.GET).keys() != {'aid', 'page', 'each'}:
            return [], 0
        try:
            aid = int(request.GET.get('aid'))
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return [], 0
        comment = ArticleComment.objects.filter(fa_article=aid, blocked=False).order_by('-create_time')
        num = len(comment)
        comment = comment[(page - 1) * each:page * each]
        a = []
        for i in comment:
            a.append(i.id)
        return a, num


class LikeArticle(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'aid', 'condition'}:
            return -1, '参数错误'
        article = Article.objects.filter(id=kwargs['aid'], recycled=False, blocked=False)
        if not article.exists():
            return 1, '文章不存在'
        atc = article.get()
        if kwargs['condition']:
            if atc.like_date != date.today():
                atc.like_date = date.today()
                atc.like_day = 0
            atc.like_day = atc.like_day + 1
            atc.who_like.add(u)
        else:
            if atc.like_date != date.today():
                atc.like_date = date.today()
                atc.like_day = 0
            atc.like_day = atc.like_day - 1
            atc.who_like.remove(u)
        atc.save()
        return 0, ''


class ComplainArticle(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'aid', 'reason'}:
            return -1, '参数错误'
        article = Article.objects.filter(id=kwargs['aid'], recycled=False, blocked=False)
        if not article.exists():
            return 1, '文章不存在'
        article = article.get()
        m = Complain(owner=u, content=kwargs['reason'], article=article)
        m.save()
        return 0, ''


class ArticleCommentInfo(View):
    @JSR('qid', 'content', 'likes', 'user_options', 'ruid', 'name', 'portrait', 'is_member', 'time', 'header')
    def get(self, request):
        if dict(request.GET).keys() != {'qid'}:
            return tuple([''] * 10)
        try:
            qid = int(request.GET.get('qid'))
        except:
            return tuple([''] * 10)
        comment = ArticleComment.objects.filter(id=qid)
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
        portrait = comment.author.profile_photo.path
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


class SubmitArticleComment(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'aid', 'content', 'pqid'}:
            return -1, '参数错误'
        atc = Article.objects.filter(id=kwargs['aid'], recycled=False, blocked=False)
        if not atc.exists():
            return 1, '文章不存在'
        atc = atc.get()
        if kwargs['pqid'] == -1:
            ac = ArticleComment.objects.create(content=kwargs['content'], fa_article=atc, author=u)
        else:
            fc = ArticleComment.objects.filter(id=kwargs['pqid'])
            if not fc.exists():
                return 2, '父评论不存在'
            ac = ArticleComment.objects.create(content=kwargs['content'], fa_article=atc, author=u,
                                          fa_comment_id=kwargs['pqid'])
            Message.objects.create(owner=ac.fa_comment.author, article_comment=ac)
        if atc.comment_date != date.today():
            atc.comment_date = date.today()
            atc.comment_day = 0
        atc.comment_day = atc.comment_day + 1
        atc.save()
        Message.objects.create(owner=atc.author, article_comment=ac)
        return 0, ''


class DelArticleComment(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'qid'}:
            return -1, '参数错误'
        if not ArticleComment.objects.filter(id=kwargs['qid']).exists():
            return -1, '评论不存在'
        ac = ArticleComment.objects.filter(id=kwargs['qid']).get()
        if request.session['uid'] != ac.author_id:
            return 1, '没有权限'
        ArticleComment.objects.filter(fa_comment_id=kwargs['qid']).delete()
        ArticleComment.objects.filter(id=kwargs['qid']).delete()
        return 0, ''


class LikeArticleComment(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'qid', 'condition'}:
            return -1, '参数错误'
        if not ArticleComment.objects.filter(id=kwargs['qid']).exists():
            return -1, '评论不存在'
        ac = ArticleComment.objects.filter(id=kwargs['qid']).get()
        if kwargs['condition']:
            ac.who_like.add(u)
            return 0, ''
        else:
            ac.who_like.remove(u)
        return 0, ''


class ComplainArticleComment(View):
    @JSR('status', 'wrong_msg')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        u = User.objects.filter(id=request.session['uid']).get()
        if kwargs.keys() != {'qid', 'reason'}:
            return -1, '参数错误'
        if not ArticleComment.objects.filter(id=kwargs['qid']).exists():
            return 1, '评论不存在'
        ac = ArticleComment.objects.filter(id=kwargs['qid']).get()
        m = Complain(owner=u, content=kwargs['reason'], article_comment=ac)
        m.save()
        return 0, ''


class ArticleInfo(View):
    @JSR('title', 'content', 'views', 'stars', 'likes', 'comments', 'tags', 'auid', 'user_options', 'detail')
    def get(self, request):
        if dict(request.GET).keys() != {'aid'}:
            return tuple([''] * 10)
        try:
            aid = int(request.GET.get('aid'))
        except:
            return tuple([''] * 10)
        atc = Article.objects.filter(id=aid, recycled=False, blocked=False)
        if not atc.exists():
            return tuple([''] * 10)
        atc = atc.get()
        if not request.session.get('uid', None):
            op = {'is_like': -1, 'is_star': -1, 'is_buy': -1}
        else:
            is_like = 1 if atc.who_like.filter(id=request.session['uid']).exists() else 0
            is_star = 1 if atc.who_star.filter(id=request.session['uid']).exists() else 0
            op = {'is_like': is_like, 'is_star': is_star}
        detail = [
            {'key': '发布时间', 'value': atc.create_time.strftime("%Y-%m-%d %H:%M:%S")},
            {'key': '最近编辑', 'value': atc.edit_time.strftime("%Y-%m-%d %H:%M:%S")}
        ]
        if atc.view_date != date.today():
            w = atc.view_week.split("&&")[1:7]
            w.append(str(atc.view_day))
            atc.view_week = "&&".join(w)
            atc.view_day = 0
        atc.view_day += 1
        atc.views += 1
        atc.save()
        return atc.title, atc.content, atc.views - 1, atc.who_star.count(), atc.who_like.count(), ArticleComment.objects.filter(
            fa_article=atc).count(), [t.name for t in atc.tagged_article.all()], atc.author_id, op, detail


class ArticleView(View):
    @JSR('title', 'simple_content', 'views', 'stars', 'likes', 'comments', 'tag', 'author_name', 'author_is_member',
         'author_portrait_url', 'auid')
    def get(self, request):
        if dict(request.GET).keys() != {'aid'}:
            return tuple([''] * 11)
        try:
            aid = int(request.GET.get('aid'))
        except:
            return tuple([''] * 11)
        atc = Article.objects.filter(id=aid, recycled=False, blocked=False)
        if not atc.exists():
            return tuple([''] * 10)
        atc = atc.get()
        u = atc.author
        simple = re.sub(r'\s+', ' ', re.sub(r'\*\*|<<|-\s|!\[.*\]\(.*\)|#+|-+', '', atc.content))
        return atc.title, simple[0:200], atc.views, atc.who_star.count(), atc.who_like.count(), atc.comment_article.count(), atc.tag, u.name, u.verify_vip(), u.profile_photo.path, u.id


class RelativeArticle(View):
    @JSR('article')
    def get(self, request):
        if dict(request.GET).keys() == {'aid', 'count'}:
            try:
                aid = int(request.GET.get('aid'))
                count = int(request.GET.get('count'))
            except:
                return []
        else:
            return []
        a = Article.objects.filter(id=aid)
        try:
            a = a.get()
        except:
            return []
        prs = []
        sa = set([t.name for t in a.tagged_article.all()])
        for o in Article.objects.all():
            sb = set([t.name for t in o.tagged_article.all()])
            cr = sa & sb
            if len(cr):
                prs.append((len(cr), o))
        return [{
            'aid': b.id,
            'title': b.title
        } for b in list(zip(*sorted(prs, key=lambda x: x[0])))[1] if b != a][:count]
