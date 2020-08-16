from django.db import models
from datetime import datetime
from meta_config import TIME_FMT


class ReadAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='readable_doc')
    ent = models.ForeignKey(to='entity.Entity', related_name='read_auth', on_delete=models.CASCADE)
    key = models.CharField(max_length=64, verbose_name='可读权限密钥', default='')

    def add_auth(self, user):
        if user not in self.user.all():
            self.user.add(user)
            try:
                self.save()
            except:
                return False
            return True
        else:
            return False

    def remove_auth(self, user):
        if user in self.user.all():
            self.user.remove(user)
            try:
                self.save()
            except:
                return False
            return True
        else:
            return False


class CommentAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='commentable_doc')
    ent = models.ForeignKey(to='entity.Entity', related_name='comment_auth', on_delete=models.CASCADE)
    key = models.CharField(max_length=64, verbose_name='可评论权限密钥', default='')

    def add_auth(self, user):
        if user not in self.user.all():
            self.user.add(user)
            try:
                self.save()
            except:
                return False
            return True
        else:
            return False

    def remove_auth(self, user):
        if user in self.user.all():
            self.user.remove(user)
            try:
                self.save()
            except:
                return False
            return True
        else:
            return False


class WriteAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='writeable_doc')
    ent = models.ForeignKey(to='entity.Entity', related_name='write_auth', on_delete=models.CASCADE)
    key = models.CharField(max_length=64, verbose_name='可写权限密钥', default='')

    def add_auth(self, user):
        if user not in self.user.all():
            self.user.add(user)
            try:
                self.save()
            except:
                return False
            return True
        else:
            return False

    def remove_auth(self, user):
        if user in self.user.all():
            self.user.remove(user)
            try:
                self.save()
            except:
                return False
            return True
        else:
            return False