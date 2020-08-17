from collections import deque
from typing import Callable, Tuple, List, Iterable

from ckeditor.fields import RichTextField
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import striptags

from entity.hypers import *
from meta_config import KB, TIME_FMT, ROOT_SUFFIX
from record.models import upd_record_create, CreateRecord, WriteRecord, ReadRecord
from utils.cast import encode, decode


# def auto_merge_available(xml1: str, xml2: str):
#     from xmldiff.actions import DeleteNode, InsertNode
#     from xmldiff.main import diff_texts
#     xml1 = f'<diadoc>{xml1}</diadoc>'
#     xml2 = f'<diadoc>{xml2}</diadoc>'
#     return all(
#         isinstance(n, DeleteNode) or isinstance(n, InsertNode)
#         for n in diff_texts(xml1, xml2)
#     )


class Entity(models.Model):
    @staticmethod
    def get_not_deleted(*args, **kwargs) -> List:
        return [f for f in Entity.objects.get(*args, **kwargs) if not f.backtrace_deleted]
    
    @staticmethod
    def get_via_encoded_id(encoded_id):
        e = Entity.objects.filter(id=int(decode(encoded_id)))
        if e.exists():
            e = e.get()
            return None if e.backtrace_deleted else e
        else:
            return None
    
    @property
    def cur_ver_id(self) -> str:
        return str(self.trajectories.first().id)
    
    def is_old_version(self, ver: str) -> bool:
        return self.cur_ver_id != ver
    
    @property
    def encoded_id(self) -> str:
        return encode(self.id)
    
    @staticmethod
    def locate_root(name):
        return Entity.objects.create(name=name + ROOT_SUFFIX, type=ENT_TYPE.fold, father=None)
    
    name = models.CharField(unique=False, max_length=BASIC_DATA_MAX_LEN)
    type = models.CharField(null=False, default=ENT_TYPE.doc, choices=ENT_TYPE_CHS, max_length=BASIC_DATA_MAX_LEN)
    content = RichTextField(default='', max_length=32 * KB)  # todo: REMOVE THIS!!!
    
    @property
    def plain_content(self) -> str:
        return striptags(self.content)
    
    father = models.ForeignKey(null=True, to='self', related_name='sons', on_delete=models.SET_NULL)
    # creator = models.ForeignKey(null=True, to='user.User', related_name='created_ents', on_delete=models.CASCADE)
    # create_dt = models.DateTimeField(auto_now_add=True)
    # editor = models.ForeignKey(null=True, to='user.User', related_name='edited_ents', on_delete=models.CASCADE)
    # edit_dt = models.DateTimeField(default=datetime.now)
    row = models.IntegerField(default=-1)
    
    @property
    def creator(self):
        q = CreateRecord.objects.filter(ent_id=self.id)
        if not q.exists():
            return None
        return q.first().user
    
    @property
    def create_dt_str(self) -> str:
        q = CreateRecord.objects.filter(ent_id=self.id)
        if not q.exists():
            return ''
        return q.first().dt_str
    
    @property
    def create_name_uid_dt_str(self) -> Tuple[str, str, str]:
        q = CreateRecord.objects.filter(ent_id=self.id)
        if not q.exists():
            return '', '', ''
        r = q.first()
        u = r.user
        return u.name, u.encoded_id, r.dt_str
    
    @property
    def editor(self):
        q = WriteRecord.objects.filter(ent_id=self.id)
        if not q.exists():
            return None
        return q.first().user
    
    @property
    def edit_dt_str(self) -> str:
        q = WriteRecord.objects.filter(ent_id=self.id)
        if not q.exists():
            return ''
        return q.first().dt_str
    
    @property
    def edit_name_uid_dt_str(self) -> Tuple[str, str, str]:
        q = WriteRecord.objects.filter(ent_id=self.id)
        if not q.exists():
            return '', '', ''
        r = q.first()
        u = r.user
        return u.name, u.encoded_id, r.dt_str
    
    def read_dt_str(self, user) -> str:
        q = ReadRecord.objects.filter(user_id=user.id, ent_id=self.id)
        if not q.exists():
            return ''
        return q.first().dt_str
    
    delete_dt = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    
    @property
    def delete_dt_str(self) -> str:
        return self.delete_dt.strftime(TIME_FMT)
    
    def is_fold(self) -> bool:
        return self.type == 'fold'
    
    def is_doc(self) -> bool:
        return self.type == 'doc'
    
    def for_each(self, func: Callable, cond: Callable = lambda _: True) -> List:
        return [func(e) for e in self.sons.all() if cond(e)]
    
    def bfs_apply(self, func: Callable, cond: Callable = lambda _: True) -> List:
        ret = [func(self)] if cond(self) else []
        q = deque(f for f in self.sons.all())
        while len(q):
            f = q.popleft()
            q.extend(ff for ff in f.sons.all())
            if cond(f):
                ret.append(func(f))
        return ret
    
    @property
    def subtree(self) -> List:
        return self.bfs_apply(func=lambda _: _)
    
    def num_leaves(self) -> int:
        if self.backtrace_deleted:
            return 0
        # if not recursive:
        #     return self.sons.filter(is_deleted=False).count()
        
        cnt = 0
        q = deque(f for f in self.sons.filter(is_deleted=False))
        while len(q):
            f = q.popleft()
            ex = [ff for ff in f.sons.filter(is_deleted=False)]
            if len(ex):
                q.extend(ex)
            else:
                cnt += 1
        return cnt
    
    @staticmethod
    def _dfs(f, func, cond, ret):
        if cond(f):
            ret.append(func(f))
        [Entity._dfs(ff, func, cond, ret) for ff in f.sons.all()]
    
    def dfs_apply(self, func: Callable, cond: Callable = lambda _: True) -> List:
        ret = []
        Entity._dfs(self, func, cond, ret)
        return ret
    
    @property
    def path(self) -> Iterable:
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
    def backtrace_deleted(self) -> bool:
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
    
    def is_user_root(self) -> bool:
        return self.root_user.exists()
    
    def is_team_root(self) -> bool:
        return self.root_team.exists()
    
    @property
    def backtrace_root_user(self):
        u = self.root.root_user
        return u.get() if u.exists() else None
    
    @property
    def backtrace_root_team(self):
        t = self.root.root_team
        return t.get() if t.exists() else None
    
    def can_convert_to_team(self) -> bool:
        r = self.backtrace_root_user
        return all((
            not self.backtrace_deleted,
            r is not None,
            self.father is not None,
            r.root.id == self.father.id
        ))
    
    def brothers_dup_name(self, name) -> bool:
        if self.father is None:
            return False
        return name in [e.name for e in self.father.sons.filter(~Q(id=self.id), is_deleted=False)]
    
    def sons_dup_name(self, name) -> bool:
        return name in [e.name for e in self.sons.filter(is_deleted=False)]
    
    def replicate(self, user, dest):
        new_ent = Entity.objects.create(
            name=self.name,
            type=self.type,
            content=self.content,
            father=dest,
        )
        upd_record_create(user, new_ent)
        
        return new_ent
    
    def move(self, dest) -> bool:
        self.father = dest
        try:
            self.save()
        except:
            return False
        return True
    
    def first_person(self, p) -> bool:
        """
        :param p: User类型
        :return: 是否是第一批写权限者。
        """
        u = self.backtrace_root_user
        if u is not None:
            return u.id == p.id
        else:
            t = self.backtrace_root_team
            if t is not None:
                return t.contains_user(p.id)
            else:
                return False
