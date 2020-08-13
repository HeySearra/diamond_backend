from collections import deque
from typing import Callable

from ckeditor.fields import RichTextField
from django.db import models
from django.template.defaultfilters import striptags

from entity.hypers import *
from meta_config import KB
from teamwork.models import Team
from utils.cast import encode, decode
from record.models import record_create, CreateRecord, WriteRecord, ReadRecord


class Entity(models.Model):
    
    @staticmethod
    def get_via_encoded_id(encoded_id):
        e = Entity.objects.filter(id=int(decode(encoded_id)))
        return e.get() if e.exists() and not e.get().backtrace_deleted else None
    
    @property
    def encoded_id(self) -> str:
        return encode(self.id)
    
    @staticmethod
    def locate_root(name):
        return Entity.objects.create(name=name, type=ENT_TYPE.fold)
    
    name = models.CharField(unique=False, max_length=BASIC_DATA_MAX_LEN)
    type = models.CharField(max_length=BASIC_DATA_MAX_LEN, choices=ENT_TYPE_CHS)
    content = RichTextField(default='', max_length=32 * KB)
    
    @property
    def plain_content(self):
        return striptags(self.content)
        
    father = models.ForeignKey(null=True, to='self', related_name='sons', on_delete=models.SET_NULL)
    # creator = models.ForeignKey(null=True, to='user.User', related_name='created_ents', on_delete=models.CASCADE)
    # create_dt = models.DateTimeField(auto_now_add=True)
    # editor = models.ForeignKey(null=True, to='user.User', related_name='edited_ents', on_delete=models.CASCADE)
    # edit_dt = models.DateTimeField(default=datetime.now)
    row = models.IntegerField(default=-1)

    @property
    def creator(self):
        r = CreateRecord.objects.filter(ent=self)
        return r.first().user if r.exists() else None

    @property
    def create_dt(self):
        r = CreateRecord.objects.filter(ent=self)
        return r.first().dt if r.exists() else None

    @property
    def editor(self):
        r = WriteRecord.objects.filter(ent=self)
        return r.first().user if r.exists() else None

    @property
    def edit_dt(self):
        r = WriteRecord.objects.filter(ent=self)
        return r.first().dt if r.exists() else None
    
    delete_dt = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    
    def is_fold(self):
        return self.type == 'fold'
    
    def is_doc(self):
        return self.type == 'doc'
    
    def for_each(self, func: Callable, cond: Callable = lambda _: True):
        return [func(e) for e in self.sons.all() if cond(e)]
    
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

    @property
    def backtrace_deleted(self):
        if self.is_deleted:
            return True
        f = self.father
        if f is None:
            return False
        while f.father is not None:
            if f.is_deleted:
                return True
            f = f.father
        return False
    
    def is_user_root(self):
        return self.root_user.exists()
    
    def is_team_root(self):
        return self.root_team.exists()
    
    @property
    def backtrace_root_user(self):
        u = self.root.root_user
        return u.get() if u.exists() else None
    
    @property
    def backtrace_root_team(self):
        t = self.root.root_team
        return t.get() if t.exists() else None
    
    def can_convert_to_team(self):
        # todo: 别忘了把团队根的father变成None
        r = self.backtrace_root_user
        return all((
            not self.backtrace_deleted,
            r is not None,
            self.father is not None,
            r.id == self.father.id
        ))
    
    def sons_dup_name(self, name):
        return self.sons.filter(is_deleted=False, name=name).exists()
    
    def replicate(self, user, dest):
        new_ent = Entity.objects.create(
            name=self.name,
            type=self.type,
            content=self.content,
            father=dest,
        )
        record_create(user, new_ent)
        
        return new_ent
    
    def move(self, dest):
        self.father = dest
        try:
            self.save()
        except:
            return False
        return True

    def first_person(self, p):
        """
        :param p: User类型
        :return: 是否是第一批写权限者。
        """
        t: Team
        u, t = self.backtrace_root_user, self.backtrace_root_team
        if u is not None:
            return u.id == p.id
        elif t is not None:
            return t.contains_user(p.id)
        else:
            return False
