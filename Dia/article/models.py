from django.db import models

from mainpage.models import Tag
from datetime import date


class Column(models.Model):
    title = models.CharField(blank=True, verbose_name="专栏名称", max_length=256, default='')
    views = models.IntegerField(blank=True, verbose_name="阅读量", default=0)  # 专栏下所有文章浏览量的和
    article_num = models.IntegerField(blank=True, verbose_name="文章数量", default=0)
    
    owner = models.ForeignKey('user.User', on_delete=models.CASCADE)


class Article(models.Model):
    title = models.CharField(verbose_name="标题", max_length=256, default='')
    abstract = models.CharField(verbose_name="摘要", max_length=256, default='')
    content = models.TextField(verbose_name="全文", default='')
    views = models.IntegerField(verbose_name="阅读量", default=0)
    view_day = models.IntegerField(blank=True, verbose_name='最近一天阅读次数', default=0)
    star_day = models.IntegerField(blank=True, verbose_name='最近一天收藏次数', default=0)
    like_day = models.IntegerField(blank=True, verbose_name='最近一天被点赞次数', default=0)
    comment_day = models.IntegerField(blank=True, verbose_name='最近一天被评论次数', default=0)
    view_week = models.CharField(blank=True, verbose_name='最近一周浏览量', default='', max_length=256)
    view_date = models.DateField(blank=True, verbose_name='最近被查看时间', default=date(1900, 1, 1))
    star_date = models.DateField(blank=True, verbose_name='最近被收藏时间', default=date(1900, 1, 1))
    like_date = models.DateField(blank=True, verbose_name='最近被点赞时间', default=date(1900, 1, 1))
    comment_date = models.DateField(blank=True, verbose_name='最近被评论时间', default=date(1900, 1, 1))
    url = models.CharField(verbose_name="文章url", max_length=256, default='')
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    edit_time = models.DateTimeField(verbose_name="修改时间", auto_now_add=True)
    recycle_time = models.DateTimeField(verbose_name="删除时间", null=True)
    blocked = models.BooleanField(blank=True, verbose_name='被封禁', default=False)
    recycled = models.BooleanField(blank=True, verbose_name='在回收站里', default=False)
    is_top = models.BooleanField(verbose_name='被置顶', default=False)
    add_into_column_time = models.DateTimeField(verbose_name='加入专栏的时间', null=True, blank=True, default=None)
    tag = models.CharField(verbose_name='主标签', default='', max_length=128)
    
    author = models.ForeignKey('user.User', related_name="article_author", on_delete=models.CASCADE)
    column = models.ForeignKey(Column, on_delete=models.CASCADE, null=True)
    who_like = models.ManyToManyField('user.User', related_name='like_person', verbose_name='like_person')  # 被谁点赞
    who_star = models.ManyToManyField('user.User', related_name='star_person', verbose_name='star_person')  # 被谁收藏
    
    def tags_qset(self) -> str:
        return self.tagged_article


class ArticleComment(models.Model):
    content = models.CharField(verbose_name="内容", max_length=512, default='')
    blocked = models.BooleanField(verbose_name='被封禁', default=False)
    create_time = models.DateTimeField(verbose_name='发表时间', auto_now_add=True)
    
    author = models.ForeignKey(to="user.User", related_name="article_comment_author", on_delete=models.CASCADE)
    fa_article = models.ForeignKey(to="Article", related_name="comment_article", on_delete=models.CASCADE)
    who_like = models.ManyToManyField('user.User', verbose_name='like_person')
    fa_comment = models.ForeignKey(null=True, to="ArticleComment", related_name="comment_comment", on_delete=models.CASCADE)
