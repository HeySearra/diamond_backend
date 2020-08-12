from datetime import datetime
from typing import Callable
from collections import deque

from django.db import models

from entity.hypers import *
from utils.cast import encode, decode


class Entity(models.Model):
    name = models.CharField(unique=False, max_length=BASIC_DATA_MAX_LEN)
    type = models.CharField(max_length=BASIC_DATA_MAX_LEN, choices=ENT_TYPE_CHS)
    content = models.TextField(default='')
    
    father = models.ForeignKey(null=True, to='self', related_name='sons', on_delete=models.CASCADE)
    creator = models.ForeignKey(null=False, to='user.User', related_name='created_ents', on_delete=models.CASCADE)
    create_dt = models.DateTimeField(auto_now_add=True)
    editor = models.ForeignKey(null=True, to='user.User', related_name='edited_ents', on_delete=models.CASCADE)
    edit_dt = models.DateTimeField(default=datetime.now)
    row = models.IntegerField(default=-1)
    
    delete_dt = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    
    @staticmethod
    def get_ent_via_encoded_id(encoded_id):
        return Entity.objects.get(id=int(decode(encoded_id)))
    
    @property
    def encoded_id(self):
        return encode(self.id)
    
    def is_fold(self):
        return self.type == 'fold'
    
    def is_doc(self):
        return self.type == 'doc'
    
    def for_each(self, func: Callable):
        return [func(e) for e in self.sons.all()]
    
    def bfs_apply(self, func: Callable):
        ret = [func(self)]
        q = deque(f for f in self.sons.all() if f.is_fold())
        while len(q):
            f = q.popleft()
            q.extend(ff for ff in f.sons.all() if ff.is_fold())
            ret.append(func(f))
        return ret
    
    @staticmethod
    def _dfs(f, func, ret):
        ret.append(func(f))
        [Entity._dfs(ff, func, ret) for ff in f.sons.all() if ff.is_fold()]
    
    def dfs_apply(self, func: Callable):
        ret = []
        Entity._dfs(self, func, ret)
        return ret
    
    @property
    def path(self):
        p = []
        f = self.father
        while f is not None:
            p.append(f)
            f = f.father
        return reversed(p)
    
    @property
    def root(self):
        f = self.father
        if f is None:
            return self
        while f.father is not None:
            f = f.father
        return f
    
    def root_user(self):
        r = self.root
        # todo
    
    def sons_dup_name(self, name):
        return self.sons.filter(name=name).exists()
    
    def touch(self, user):
        self.editor, self.edit_dt = user, datetime.now()
        try:
            self.save()
        except:
            return False
        return True
    
    def make_replica(self, user, dest):
        new_ent = Entity.objects.create(
            name=self.name,
            type=self.type,
            content=self.content,
            father=dest,
            creator=user,
            editor=user,
        )
        return new_ent
    
    @property
    def all_sons(self):
        return self.bfs_apply(lambda _: _)[1:]
