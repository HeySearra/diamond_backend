from datetime import datetime
from typing import Tuple

from ckeditor.fields import RichTextField
from django.db import models

from entity.hypers import BASIC_DATA_MAX_LEN, COMMENT_MAX_LEN
from entity.models import Entity
from meta_config import TIME_FMT, KB
from user.models import User
from utils.cast import encode, decode


class Collection(models.Model):
    user = models.ForeignKey('user.User', related_name='collections', on_delete=models.CASCADE)
    ent = models.ForeignKey('entity.Entity', related_name='collected', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True, verbose_name='文件收藏时间')

    class Meta:
        ordering = ["-dt"]

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class Links(models.Model):
    user = models.ForeignKey(null=False, to='user.User', related_name='links', on_delete=models.CASCADE)
    ent = models.ForeignKey(null=False, to='entity.Entity', related_name='links', on_delete=models.CASCADE)


class UserTemplate(models.Model):
    @property
    def encoded_id(self) -> str:
        return encode(self.id)

    @staticmethod
    def get_via_encoded_id(encoded_id: str):
        u = UserTemplate.objects.filter(id=int(decode(encoded_id)))
        return u.get() if u.exists() else None

    creator = models.ForeignKey(to='user.User', on_delete=models.CASCADE, verbose_name='创建者')
    name = models.CharField(verbose_name='个人模板名称', unique=False, default='未命名', max_length=65)
    content = RichTextField(verbose_name='内容', default='', max_length=32 * KB)
    create_dt = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    # delete_dt = models.DateTimeField(verbose_name='删除时间', null=True)
    # is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-create_dt']


class OfficialTemplate(models.Model):
    @property
    def encoded_id(self) -> str:
        return encode(self.id)

    @staticmethod
    def get_via_encoded_id(encoded_id: str):
        o = OfficialTemplate.objects.filter(id=int(decode(encoded_id)))
        return o.get() if o.exists() else None

    name = models.CharField(verbose_name='官方模板名称', unique=False, default='未命名', max_length=65)
    title = models.CharField(verbose_name='官方模板类型', unique=False, default='通用', max_length=65)
    portrait = models.CharField(verbose_name='官方模板预览图', blank=True, null=True, default='', max_length=512)
    content = RichTextField(verbose_name='内容', default='', max_length=32 * KB)
    create_dt = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    only_vip = models.BooleanField(default=False)


class Comment(models.Model):
    @property
    def encoded_id(self) -> str:
        return encode(self.id)

    did = models.ForeignKey('entity.Entity', on_delete=models.CASCADE)
    uid = models.ForeignKey('user.User', on_delete=models.CASCADE)
    threadId = models.CharField(unique=False, max_length=BASIC_DATA_MAX_LEN)
    commentId = models.CharField(unique=False, max_length=BASIC_DATA_MAX_LEN)
    content = models.CharField(unique=False, max_length=COMMENT_MAX_LEN)
    createdAt = models.BigIntegerField(default=0)


class Trajectory(models.Model):
    class Meta:
        ordering = ['-id']  # achieving the optimal sorting performance!

    ent = models.ForeignKey(to='entity.Entity', related_name='trajectories', on_delete=models.CASCADE)
    user = models.ForeignKey(to='user.User', related_name='trajectories', on_delete=models.CASCADE)
    dt = models.DateTimeField(null=True, default=datetime.now)
    updated_content = RichTextField(default='', max_length=32 * KB)
    initial = models.BooleanField(default=False)

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)

    @property
    def name_portrait_dt_str(self) -> Tuple[str, str, str]:
        return self.user.name, self.user.portrait, self.dt_str


class EditLock(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    ent = models.ForeignKey(to=Entity, on_delete=models.CASCADE)
    dt = models.DateTimeField(default=datetime.now)

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)
