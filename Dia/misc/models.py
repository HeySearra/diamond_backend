from django.db import models
from meta_config import TIME_FMT
from misc.hypers import *


class WriteMem(models.Model):
    user = models.ForeignKey(to='user.User', on_delete=models.CASCADE)
    auth = models.ForeignKey(to='WriteAuth', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)    # 预留给工作台和文件系统的排序

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class CommentMem(models.Model):
    user = models.ForeignKey(to='user.User', on_delete=models.CASCADE)
    auth = models.ForeignKey(to='CommentAuth', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class ReadMem(models.Model):
    user = models.ForeignKey(to='user.User', on_delete=models.CASCADE)
    auth = models.ForeignKey(to='ReadAuth', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class ReadAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='readable_doc', through='ReadMem', through_fields=('auth', 'user'))
    ent = models.ForeignKey(to='entity.Entity', related_name='read_auth', on_delete=models.CASCADE)

    def add_auth(self, user):
        ra, flag = ReadMem.objects.get_or_create(user=user, auth=self)
        ra.save()
        return flag

    def remove_auth(self, user):
        try:
            ReadMem.objects.get(user=user, auth=self).delete()
        except:
            return False
        return True

    def get_user_list(self):
        return [e.user for e in ReadMem.objects.filter(auth=self)]


class CommentAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='commentable_doc', through='CommentMem', through_fields=('auth', 'user'))
    ent = models.ForeignKey(to='entity.Entity', related_name='comment_auth', on_delete=models.CASCADE)

    def add_auth(self, user):
        ra, flag = CommentMem.objects.get_or_create(user=user, auth=self)
        ra.save()
        return flag

    def remove_auth(self, user):
        try:
            CommentMem.objects.get(user=user, auth=self).delete()
        except:
            return False
        return True

    def get_user_list(self):
        return [e.user for e in CommentMem.objects.filter(auth=self)]


class WriteAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='writeable_doc', through='WriteMem', through_fields=('auth', 'user'))
    ent = models.ForeignKey(to='entity.Entity', related_name='write_auth', on_delete=models.CASCADE)

    def add_auth(self, user):
        ra, flag = WriteMem.objects.get_or_create(user=user, auth=self)
        ra.save()
        return flag

    def remove_auth(self, user):
        try:
            WriteMem.objects.get(user=user, auth=self).delete()
        except:
            return False
        return True

    def get_user_list(self):
        return [e.user for e in WriteMem.objects.filter(auth=self)]


class ShareMem(models.Model):
    user = models.ForeignKey(to='user.User', on_delete=models.CASCADE)
    auth = models.ForeignKey(to='ShareAuth', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)    # 预留给工作台和文件系统的排序

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class ShareAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='shared_doc', blank=True, through='ShareMem', through_fields=('auth', 'user'))
    owner = models.ManyToManyField(to='user.User', related_name='shareable_doc', blank=True)
    ent = models.ForeignKey(to='entity.Entity', related_name='share_auth', on_delete=models.CASCADE)
    auth = models.CharField(max_length=64, verbose_name="分享的权限", choices=AUTH_TYPE_CHS, default='no_share')
    key = models.CharField(max_length=64, verbose_name='可写权限密钥', default='')

    def add_auth(self, user):
        ra, flag = ShareMem.objects.get_or_create(user=user, auth=self)
        ra.save()
        return flag

    def remove_auth(self, user):
        try:
            ShareMem.objects.get(user=user, auth=self).delete()
        except:
            return False
        return True

    def is_in_auth(self, user):
        if user in self.user.all():
            return True
        else:
            return False

    def can_share(self, user):
        if user in self.owner.all():
            return True
        else:
            return False

    def add_owner(self, user):
        try:
            self.owner.add(user)
            self.save()
        except:
            return False
        return True

    def remove_owner(self, user):
        try:
            self.owner.remove(user)
            self.save()
        except:
            return False
        return True
