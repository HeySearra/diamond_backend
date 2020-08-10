import json
from easydict import EasyDict
from django.http import JsonResponse
from django.views import View
from django.db.models import Count, F, Q, Min, QuerySet
from article.models import Article
from resource.models import Resource, ResourceComment, Download
from mainpage.models import Complain, Tag, Collection, ArticleCollect, ResourceCollect
from user.models import User
from utils.response import JSR
from mainpage.hypers import *


class CollectionList(View):
    @JSR('collections')
    def get(self, request):
        if dict(request.GET).keys() == {'uid'}:
            try:
                uid = int(request.GET.get('uid'))
                col = Collection.objects.filter(owner_id=uid, hide=False)
            except:
                return [], 0
        else:
            uid = request.session['uid']
            col = Collection.objects.filter(owner_id=uid)
        if not col:
            Collection.objects.create(owner_id=uid, name='默认收藏夹')
        return [
                   {
                       'cid': collection.id,
                       'title': collection.name,
                       'condition': 1 if collection.hide else 0,
                       'count': collection.articles.count() + collection.resources.count()
                   } for collection in Collection.objects.filter(owner_id=uid)
               ],


class CollectionInfo(View):
    @JSR('dist', 'amount')
    def get(self, request):
        if dict(request.GET).keys() == {'cid', 'page', 'each'}:
            try:
                page = int(request.GET.get('page'))
                each = int(request.GET.get('each'))
            except:
                return [], 0
        elif dict(request.GET).keys() == {'cid'}:
            page = -1
        else:
            return [], 0
        try:
            cid = int(request.GET.get('cid'))
        except:
            return [], 0
        collection = Collection.objects.filter(id=cid)
        if not collection.exists():
            return [], 0
        u = collection.get()
        if u.hide and (not request.session.get('uid', None) or request.session.get('uid', None) and User.objects.get(id=request.session['uid']) != u.owner):
            return [], 0
        ca = ArticleCollect.objects.filter(user=u)
        cr = ResourceCollect.objects.filter(user=u)
        num = ca.count() + cr.count()
        a = []
        a.extend(ca)
        a.extend(cr)
        a.sort(key=lambda c: c.time, reverse=True)
        if page != -1:
            a = a[(page - 1) * each: page * each]
        b = []
        for i in a:
            if isinstance(i, ArticleCollect):
                b.append({'aid': i.article.id})
            else:
                b.append({'rid': i.resource.id})
        return b, num


class RecommendArticles(View):
    @JSR('article', 'amount')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return [], [], 0
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return [], 0
        atcs = Article.objects.filter(recycled=False, blocked=False).order_by('-views')
        return [a.id for a in atcs[each * (page - 1):each * page]], atcs.count()


class DisLikeRecommend(View):
    @JSR()
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'aid'}:
            return
        """
        """
        return


class LikeRecommend(View):
    @JSR()
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'aid'}:
            return
        """
        """
        return


class HotArticles(View):
    @JSR('article', 'amount')
    def get(self, request):
        if dict(request.GET).keys() != {'page', 'each'}:
            return [], [], 0
        try:
            page = int(request.GET.get('page'))
            each = int(request.GET.get('each'))
        except:
            return [], 0
        atcs = sorted([a for a in Article.objects.filter(recycled=False, blocked=False)], key=lambda a: sum([int(i) for i in a.view_week.split("&&") if i != '']))
        return [a.id for a in atcs[each * (page - 1):each * page]], len(atcs)


class HotDogs(View):
    @JSR('tags')
    def get(self, request):
        tags = sorted([tg for tg in Tag.objects.all()],
                      key=lambda t: t.article.filter(recycled=False, blocked=False).count() + t.resource.filter(blocked=False).count(),
                      reverse=True
                      )[:MAX_TAGS_TO_FRONTEND]
        return [t.name for t in tags]


class ElementsWithTag(View):
    @JSR('content', 'amount')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'tag', 'page', 'each'}:
            return []
        name = kwargs['tag']
        tag = Tag.objects.filter(name=name)
        if not tag.exists():
            return []
        tag = tag.get()
        a = [e for e in tag.resource.filter(blocked=False)] + [e for e in tag.article.filter(recycled=False, blocked=False)]
        a = [{'aid' if isinstance(e, Article) else 'rid': e.id} for e in a]
        amount = len(a)
        a = a[(kwargs['page'] - 1) * kwargs['each']: kwargs['page'] * kwargs['each']]
        return a, amount


class SearchMain(View):
    @JSR('result', 'tags', 'wrong_msg', 'amount')
    def post(self, request):
        kwargs: dict = json.loads(request.body)
        if kwargs.keys() != {'key', 'limit', 'order', 'tags', 'page', 'each'}:
            return -1, '参数错误'
        sent, lim, tags, page, each = kwargs['key'], kwargs['limit'], set(kwargs['tags']), kwargs['page'], kwargs['each']
        if not sent:
            return [], [], '不准搜空字符串'
        
        aset: QuerySet = Article.objects.all()[0:0]
        rset: QuerySet = Resource.objects.all()[0:0]
        for k in sent.split():
            if lim & 1:
                rset = rset.union(
                    Resource.objects.filter(
                        Q(title__icontains=k) | Q(content__icontains=k),
                        blocked=False
                    ), *[
                        u.resource_author.all()
                        for u in User.objects.filter(name__icontains=k, blocked=False)
                    ]
                )
            if lim & 2:
                aset = aset.union(
                    Article.objects.filter(
                        Q(title__icontains=k) | Q(content__icontains=k),
                        recycled=False, blocked=False
                    ), *[
                        u.article_author.all()
                        for u in User.objects.filter(name__icontains=k, blocked=False)
                    ]
                )
        es = sorted(
            [e for e in aset] + [e for e in rset],
            key=lambda e: e.create_time if kwargs['order'] == 1 else e.views,
            reverse=kwargs['order'] != 1
        )
        func = (lambda elem: set([tag.name for tag in elem.tags_qset().all()]) & tags) if len(tags) else lambda _: True
        res = list(filter(func, es))
        amount = len(res)
        res = res[(page - 1) * each:page * each]
        return (
            [{
                'rid' if isinstance(elem, Resource) else 'aid': elem.id
            } for elem in res],
            list(set().union(*[[t.name for t in elem.tags_qset().all()] for elem in res])),
            '', amount
        )
