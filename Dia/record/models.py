from django.db import models
from datetime import datetime

from meta_config import TIME_FMT
from teamwork.hypers import DOC_AUTH
from typing import List, Tuple


def _get_clz(auth):
    clz = [CreateRecord, WriteRecord, CommentRecord, ReadRecord]
    pos = ['create', DOC_AUTH.write, DOC_AUTH.comment, DOC_AUTH.read].index(auth)
    return clz[pos:]


def upd_record_user(auth: str, ent, old_user, new_user):
    """
    对于一个指定文档和指定的人（未指定人则仅用指定文档筛），更新某种权限及其所有比它小的权限的操作者（权限大小是：创建 > 写 > 评论 > 阅读）
    例如，更新创建记录，会同时更新写记录、评论记录、阅读记录
    :param auth: 权限，从 'create', 'write', 'comment', 'read' 任选其一
    :param ent: 指定的文档
    :param old_user: 用于筛选的操作者
    :param new_user: 改后的操作者
    """
    kwargs = dict(ent=ent)
    if old_user is not None:
        kwargs['user'] = old_user
    for c in _get_clz(auth):
        recs = c.objects.filter(**kwargs)
        for rec in recs:
            rec.user = new_user
            rec.save()


def upd_record(auth: str, user, ent, delete):
    """
    对于一个指定文档和指定操作者，更新某种权限及其所有比它小的权限的操作者及操作时间（权限大小是：创建 > 写 > 评论 > 阅读）
    例如，更新创建记录，会同时更新写记录、评论记录、阅读记录
    :param auth: 权限，从 'create', 'write', 'comment', 'read' 任选其一
    :param user: 指定的操作者
    :param ent: 指定的文档
    :param delete: 为 True 则是删除条目，False 则是更新or创建条目
    """
    clz = [CreateRecord, WriteRecord, CommentRecord, ReadRecord]
    pos = ['create', DOC_AUTH.write, DOC_AUTH.comment, DOC_AUTH.read].index(auth)
    kwargs = dict(user=user, ent=ent)
    if delete:
        [c.objects.filter(**kwargs).delete() for c in clz[pos:]]
    else:  # update
        for o in [
            c.objects.get_or_create(**kwargs)[0]
            for c in clz[pos:]
        ]:
            o.upd_dt()


def record_create(user, ent, delete=False):
    return upd_record('create', user, ent, delete)


def record_write(user, ent, delete=False):
    return upd_record('write', user, ent, delete)


def record_comment(user, ent, delete=False):
    return upd_record('comment', user, ent, delete)


def record_read(user, ent, delete=False):
    return upd_record('read', user, ent, delete)


class CreateRecord(models.Model):
    user = models.ForeignKey(to='user.User', related_name='create_records', on_delete=models.CASCADE)
    ent = models.ForeignKey(to='entity.Entity', related_name='create_records', on_delete=models.CASCADE)
    dt = models.DateTimeField(null=True, default=datetime.now)
    
    class Meta:
        ordering = ['-dt']
    
    def upd_dt(self):
        self.dt = datetime.now()
        self.save()
    
    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class WriteRecord(models.Model):
    user = models.ForeignKey(to='user.User', related_name='write_records', on_delete=models.CASCADE)
    ent = models.ForeignKey(to='entity.Entity', related_name='write_records', on_delete=models.CASCADE)
    dt = models.DateTimeField(null=True, default=datetime.now)
    
    class Meta:
        ordering = ['-dt']
    
    def upd_dt(self):
        self.dt = datetime.now()
        self.save()
    
    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class CommentRecord(models.Model):
    user = models.ForeignKey(to='user.User', related_name='comment_records', on_delete=models.CASCADE)
    ent = models.ForeignKey(to='entity.Entity', related_name='comment_records', on_delete=models.CASCADE)
    dt = models.DateTimeField(null=True, default=datetime.now)
    
    class Meta:
        ordering = ['-dt']
    
    def upd_dt(self):
        self.dt = datetime.now()
        self.save()
    
    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class ReadRecord(models.Model):
    user = models.ForeignKey(to='user.User', related_name='read_records', on_delete=models.CASCADE)
    ent = models.ForeignKey(to='entity.Entity', related_name='read_records', on_delete=models.CASCADE)
    dt = models.DateTimeField(null=True, default=datetime.now)
    
    class Meta:
        ordering = ['-dt']
    
    def upd_dt(self):
        self.dt = datetime.now()
        self.save()
    
    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)
