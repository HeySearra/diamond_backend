from django.db import models
from datetime import datetime
from teamwork.hypers import DOC_AUTH
from typing import List, Tuple


def record(auth: str, user, ent) -> List[Tuple[object, bool]]:
    clz = [CreateRecord, WriteRecord, CommentRecord, ReadRecord]
    pos = ['create', DOC_AUTH.write, DOC_AUTH.comment, DOC_AUTH.read].index(auth)
    obj = [c.objects.get_or_create(user=user, ent=ent)[0] for c in clz[pos:]]
    [o.upd_dt() for o in obj]
    return obj


class CreateRecord(models.Model):
    user = models.ForeignKey(to='user.User', related_name='create_records', on_delete=models.CASCADE)
    ent = models.ForeignKey(to='entity.Entity', related_name='create_records', on_delete=models.CASCADE)
    dt = models.DateTimeField(null=True, default=datetime.now)
    
    def upd_dt(self):
        self.dt = datetime.now()
        self.save()


class WriteRecord(models.Model):
    user = models.ForeignKey(to='user.User', related_name='write_records', on_delete=models.CASCADE)
    ent = models.ForeignKey(to='entity.Entity', related_name='write_records', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    
    def upd_dt(self):
        self.dt = datetime.now()
        self.save()


class CommentRecord(models.Model):
    user = models.ForeignKey(to='user.User', related_name='comment_records', on_delete=models.CASCADE)
    ent = models.ForeignKey(to='entity.Entity', related_name='comment_records', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    
    def upd_dt(self):
        self.dt = datetime.now()
        self.save()


class ReadRecord(models.Model):
    user = models.ForeignKey(to='user.User', related_name='read_records', on_delete=models.CASCADE)
    ent = models.ForeignKey(to='entity.Entity', related_name='read_records', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    
    def upd_dt(self):
        self.dt = datetime.now()
        self.save()
