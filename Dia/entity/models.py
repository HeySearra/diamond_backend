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
    
    def bfs_apply(self, func: Callable, cond: Callable = lambda _: True):
        ret = [func(self)] if cond(self) else []
        q = deque(f for f in self.sons.all())
        while len(q):
            f = q.popleft()
            q.extend(ff for ff in f.sons.all())
            if cond(f):
                ret.append(func(f))
        return ret
    
    @property
    def subtree(self, include_self=False):
        return self.bfs_apply(func=lambda _: _)[0 if include_self else 1:]
    
    @staticmethod
    def _dfs(f, func, cond, ret):
        if cond(f):
            ret.append(func(f))
        [Entity._dfs(ff, func, cond, ret) for ff in f.sons.all()]
    
    def dfs_apply(self, func: Callable, cond: Callable = lambda _: True):
        ret = []
        Entity._dfs(self, func, cond, ret)
        return ret
    
    @property
    def path(self, root_begins=True):
        p = []
        f = self.father
        while f is not None:
            p.append(f)
            f = f.father
        return reversed(p) if root_begins else p
    
    @property
    def root(self):
        f = self.father
        if f is None:
            return self
        while f.father is not None:
            f = f.father
        return f
    
    @property
    def root_user(self):
        r = self.root
        # todo
    
    @property
    def root_team(self):
        r = self.root
        # todo
    
    def can_convert_to_team(self):
        r = self.root_user
        return all((
            r is not None,
            self.father is not None,
            r.id == self.father.id
        ))
    
    def sons_dup_name(self, name):
        return self.sons.filter(name=name).exists()
    
    def touch(self, user):
        self.editor, self.edit_dt = user, datetime.now()
        try:
            self.save()
        except:
            return False
        return True
    
    def replicate(self, user, dest):
        new_ent = Entity.objects.create(
            name=self.name,
            type=self.type,
            content=self.content,
            father=dest,
            creator=user,
            editor=user,
        )
        return new_ent
    
    def move(self, dest):
        self.father = dest
        try:
            self.save()
        except:
            return False
        return True
