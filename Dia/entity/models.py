from collections import deque
from datetime import datetime
from typing import Callable

from ckeditor.fields import RichTextField
from django.db import models
from django.template.defaultfilters import striptags

from entity.hypers import *
from meta_config import KB
from utils.cast import encode, decode


class Entity(models.Model):
    
    @staticmethod
    def get_via_encoded_id(encoded_id):
        return Entity.objects.get(id=int(decode(encoded_id)))
    
    @property
    def encoded_id(self):
        return encode(self.id)
    
    name = models.CharField(unique=False, max_length=BASIC_DATA_MAX_LEN)
    type = models.CharField(max_length=BASIC_DATA_MAX_LEN, choices=ENT_TYPE_CHS)
    content = RichTextField(default='', max_length=32 * KB)
    
    @property
    def plain_content(self):
        return striptags(self.content)
    
    father = models.ForeignKey(null=True, to='self', related_name='sons', on_delete=models.CASCADE)
    # creator = models.ForeignKey(null=True, to='user.User', related_name='created_ents', on_delete=models.CASCADE)
    # create_dt = models.DateTimeField(auto_now_add=True)
    # editor = models.ForeignKey(null=True, to='user.User', related_name='edited_ents', on_delete=models.CASCADE)
    # edit_dt = models.DateTimeField(default=datetime.now)
    row = models.IntegerField(default=-1)
    
    delete_dt = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    
    
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
    def subtree(self):
        return self.bfs_apply(func=lambda _: _)
    
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
    
    def is_user_root(self):
        return self.root_user is not None
    
    def is_team_root(self):
        return self.root_team is not None
    
    @property
    def backtrace_root_user(self):
        return self.root.root_user
    
    @property
    def backtrace_root_team(self):
        return self.root.root_team
    
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


