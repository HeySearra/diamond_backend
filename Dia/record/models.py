from django.db import models
from datetime import datetime

from meta_config import TIME_FMT
from teamwork.hypers import DOC_AUTH
from typing import List, Tuple


def record(auth: str, user, ent, delete):
    clz = [CreateRecord, WriteRecord, CommentRecord, ReadRecord]
    pos = ['create', DOC_AUTH.write, DOC_AUTH.comment, DOC_AUTH.read].index(auth)
    kwargs = dict(user=user, ent=ent)
    if delete:
        [c.objects.filter(**kwargs).delete() for c in clz[pos:]]
    else:   # update
        [
            o.upd_dt() for o in [
                c.objects.get_or_create(user=user, ent=ent)[0]
                for c in clz[pos:]
            ]
        ]


def record_create(user, ent, delete=False):
    return record('create', user, ent, delete)


def record_write(user, ent, delete=False):
    return record('write', user, ent, delete)


def record_comment(user, ent, delete=False):
    return record('comment', user, ent, delete)


def record_read(user, ent, delete=False):
    return record('read', user, ent, delete)


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
