import os
from datetime import date, datetime, timedelta
from django.db import models

from user.hypers import *


class User(models.Model):
    # basic fields
    tel = models.CharField(null=True, unique=True, verbose_name='电话', max_length=BASIC_DATA_MAX_LEN)
    email = models.EmailField(null=True, unique=True, verbose_name='邮箱', max_length=BASIC_DATA_MAX_LEN)
    password = models.CharField(verbose_name='密码', max_length=BASIC_DATA_MAX_LEN)
    name = models.CharField(verbose_name='姓名', max_length=BASIC_DATA_MAX_LEN)
    is_dnd = models.BooleanField(blank=True, verbose_name='消息是否免打扰', default=False)

    # extended fields
    intro = models.CharField(blank=True, verbose_name='简介', max_length=EXT_DATA_MAX_LEN, default='')
    session_key = models.CharField(blank=True, verbose_name='session键', max_length=EXT_DATA_MAX_LEN, default='')

    # other fields
    login_date = models.DateField(blank=True, verbose_name='最近登录时间', auto_now_add=True)
    wrong_count = models.IntegerField(blank=True, verbose_name='最近一天密码错误次数', default=0)
    vip_date = models.DateField(blank=True, verbose_name='会员到期时间', default=date(1900, 1, 1))
    create_time = models.DateTimeField(blank=True, verbose_name='创建时间', auto_now_add=True)
    profile_photo = models.FileField(blank=True, upload_to=DEFAULT_PROFILE_ROOT, verbose_name="头像路径", max_length=256, default='')

    def verify_vip(self) -> bool:
        if self.vip_date < date.today():
            self.identity = 'user'
            self.save()
        else:
            self.identity = 'vip'
        return self.identity == 'vip'

    # def get_data_day(self):
    #     atc = Article.objects.filter(author=self, recycled=False, blocked=False)
    #     self.like_day = 0
    #     self.view_day = 0
    #     self.star_day = 0
    #     self.comment_day = 0
    #     self.point_day = 0
    #     for a in atc:
    #         if a.like_date == date.today() - timedelta(days=1):
    #             self.like_day += a.like_date
    #         if a.view_date == date.today() - timedelta(days=1):
    #             self.view_day += a.view_date
    #         if a.star_date == date.today() - timedelta(days=1):
    #             self.star_day += a.star_date
    #         if a.comment_date == date.today() - timedelta(days=1):
    #             self.comment_day += a.comment_view
    #         if a.like_date != date.today():
    #             a.like_day = 0
    #         if a.view_date != date.today():
    #             a.view_day = 0
    #         if a.star_date != date.today():
    #             a.star_day = 0
    #         if a.comment_date != date.today():
    #             a.comment_day = 0
    #         self.view_day += a.view_day
    #         self.star_day += a.star_day
    #         self.like_day += a.like_day
    #         self.comment_day += a.comment_day
    #         a.save()
    #     res = Resource.objects.filter(author=self, blocked=False)
    #     for a in res:
    #         if a.like_date == date.today() - timedelta(days=1):
    #             self.like_day += a.like_date
    #         if a.view_date == date.today() - timedelta(days=1):
    #             self.view_day += a.view_date
    #         if a.star_date == date.today() - timedelta(days=1):
    #             self.star_day += a.star_date
    #         if a.comment_date == date.today() - timedelta(days=1):
    #             self.comment_day += a.comment_view
    #         if a.like_date != date.today():
    #             a.like_day = 0
    #         if a.view_date != date.today():
    #             a.view_day = 0
    #         if a.star_date != date.today():
    #             a.star_day = 0
    #         if a.comment_date != date.today():
    #             a.comment_day = 0
    #         if a.point_date != date.today():
    #             a.point_day = 0
    #         self.view_day += a.view_day
    #         self.star_day += a.star_day
    #         self.like_day += a.like_day
    #         self.comment_day += a.comment_day
    #         self.point_day += a.point_day
    #         a.save()
    #     self.save()
    #
    # def get_data_count(self):
    #     atc = Article.objects.filter(author=self, recycled=False, blocked=False)
    #     self.like_count = 0
    #     self.view_count = 0
    #     self.star_count = 0
    #     self.comment_count = 0
    #     self.point_count = 0
    #     for a in atc:
    #         self.like_count += a.who_like.all().count()
    #         self.view_count = a.views
    #         self.star_count = a.who_star.all().count()
    #         self.comment_count = a.comment_article.count()
    #     res = Resource.objects.filter(author=self, blocked=False)
    #     for a in res:
    #         self.like_count += a.who_like.all().count()
    #         self.view_count = a.views
    #         self.star_count = a.who_star.all().count()
    #         self.comment_count = a.comment_resource.count()
    #         self.point = a.who_buy.all().count() * a.points
    #     self.save()


class Detail(models.Model):
    point = models.IntegerField(verbose_name="积分变动", default=0)
    reason = models.CharField(verbose_name="理由", max_length=256)
    time = models.DateTimeField(verbose_name="时间", auto_now_add=True)
    owner = models.ForeignKey('user.User', on_delete=models.CASCADE)


class Follow(models.Model):
    followed = models.ForeignKey(User, related_name='followed', on_delete=models.CASCADE)
    follower = models.ForeignKey(User, related_name='follower', on_delete=models.CASCADE)


class EmailRecord(models.Model):
    code = models.CharField(max_length=20, verbose_name='验证码')
    email = models.EmailField(max_length=50, verbose_name='用户邮箱')
    send_time = models.DateTimeField(default=datetime.now, verbose_name='发送时间', null=True, blank=True)
    expire_time = models.DateTimeField(null=True)
    email_type = models.CharField(choices=(('register', '注册邮件'), ('forget', '找回密码')), max_length=10)

    class Meta:
        verbose_name = '邮件验证码'
        verbose_name_plural = verbose_name


class Message(models.Model):
    user = models.ForeignKey('user.User', related_name='id', on_delete=models.CASCADE)
    title = models.CharField(max_length=64, verbose_name='标题')
    content = models.TextField(blank=False, verbose_name='消息内容', max_length=201)
    is_read = models.BooleanField(blank=True, verbose_name='消息是否读取', default=False)
    portrait_url = models.CharField(max_length=512, verbose_name='头像url', default='')
    dt = models.DateTimeField(default=datetime.now, verbose_name='消息产生时间')
    type = models.CharField(blank=False, verbose_name='消息类型')

