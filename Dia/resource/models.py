from datetime import date

from django.db import models
from mainpage.models import Tag


class Resource(models.Model):
    title = models.CharField(verbose_name="标题", max_length=256, default='')
    content = models.CharField(blank=True, verbose_name="描述", max_length=256, default='')
    file_path = models.CharField(blank=True, verbose_name="资源路径", max_length=256, default='')
    file_size = models.CharField(blank=True, verbose_name="大小", max_length=256, default='')
    views = models.IntegerField(blank=True, verbose_name="阅读量", default=0)
    view_day = models.IntegerField(blank=True, verbose_name='最近一天阅读次数', default=0)
    star_day = models.IntegerField(blank=True, verbose_name='最近一天收藏次数', default=0)
    like_day = models.IntegerField(blank=True, verbose_name='最近一天被点赞次数', default=0)
    comment_day = models.IntegerField(blank=True, verbose_name='最近一天被评论次数', default=0)
    point_day = models.IntegerField(blank=True, verbose_name='最近一天得的积分数', default=0)
    view_date = models.DateField(blank=True, verbose_name='最近被查看时间', default=date(1900, 1, 1))
    star_date = models.DateField(blank=True, verbose_name='最近被收藏时间', default=date(1900, 1, 1))
    like_date = models.DateField(blank=True, verbose_name='最近被点赞时间', default=date(1900, 1, 1))
    comment_date = models.DateField(blank=True, verbose_name='最近被评论时间', default=date(1900, 1, 1))
    point_date = models.DateField(blank=True, verbose_name='最近被下载时间', default=date(1900, 1, 1))
    points = models.IntegerField(blank=True, verbose_name="所需积分", default=0)
    create_time = models.DateTimeField(blank=True, verbose_name='上传时间', auto_now_add=True)
    edit_time = models.DateTimeField(blank=True, verbose_name='修改时间', auto_now=True)
    blocked = models.BooleanField(blank=True, verbose_name='被封禁', default=False)
    recycled = models.BooleanField(blank=True, verbose_name='在回收站里', default=False)
    tag = models.CharField(verbose_name='主标签', default='', max_length=128)
    
    author = models.ForeignKey(to='user.User', related_name="resource_author", on_delete=models.CASCADE)
    who_like = models.ManyToManyField('user.User', related_name='person_like', verbose_name='点赞的人')  # 被谁点赞
    who_star = models.ManyToManyField('user.User', related_name='person_star', verbose_name='收藏的人')  # 被谁收藏
    who_buy = models.ManyToManyField('user.User', related_name='person_buy', verbose_name='购买的人')  # 被谁购买
    
    def tags_qset(self) -> str:
        return self.tagged_resource


class ResourceComment(models.Model):
    content = models.CharField(verbose_name="内容", max_length=512, default='')
    blocked = models.BooleanField(verbose_name='被封禁', default=False)
    create_time = models.DateTimeField(verbose_name='发表时间', auto_now_add=True)
    
    author = models.ForeignKey(null=True, to="user.User", related_name="resource_comment_author", on_delete=models.CASCADE)
    fa_resource = models.ForeignKey(null=True, to=Resource, related_name="comment_resource", on_delete=models.CASCADE)
    who_like = models.ManyToManyField('user.User', verbose_name='like_person')
    fa_comment = models.ForeignKey(null=True, to="ResourceComment", related_name="comment_comment", on_delete=models.CASCADE)


class Download(models.Model):
    owner = models.ForeignKey('user.User', related_name='download_owner', on_delete=models.CASCADE)
    resources = models.ManyToManyField('resource.Resource', through='DownloadMembership')


class DownloadMembership(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    
    download = models.ForeignKey('Download', on_delete=models.CASCADE)
    resource = models.ForeignKey('Resource', on_delete=models.CASCADE)
