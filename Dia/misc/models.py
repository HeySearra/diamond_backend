from django.db import models
from meta_config import TIME_FMT


class WriteMem(models.Model):
    user = models.ForeignKey(to='user.User', on_delete=models.CASCADE)
    write_auth = models.ForeignKey(to='WriteAuth', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class CommentMem(models.Model):
    user = models.ForeignKey(to='user.User', on_delete=models.CASCADE)
    comment_auth = models.ForeignKey(to='CommentAuth', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class ReadMem(models.Model):
    user = models.ForeignKey(to='user.User', on_delete=models.CASCADE)
    read_auth = models.ForeignKey(to='ReadAuth', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)

    @property
    def dt_str(self):
        return self.dt.strftime(TIME_FMT)


class ReadAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='readable_doc', through='ReadMem', through_fields=('read_auth', 'user'))
    ent = models.ForeignKey(to='entity.Entity', related_name='read_auth', on_delete=models.CASCADE)
    key = models.CharField(max_length=64, verbose_name='可读权限密钥', default='')

    def add_auth(self, user):
        ra, flag = ReadMem.objects.get_or_create(user=user, read_auth=self)
        ra.save()
        return flag

    def remove_auth(self, user):
        try:
            ReadMem.objects.get(user=user, read_auth=self).delete()
        except:
            return False
        return True


class CommentAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='commentable_doc', through='CommentMem', through_fields=('comment_auth', 'user'))
    ent = models.ForeignKey(to='entity.Entity', related_name='comment_auth', on_delete=models.CASCADE)
    key = models.CharField(max_length=64, verbose_name='可评论权限密钥', default='')

    def add_auth(self, user):
        ra, flag = CommentMem.objects.get_or_create(user=user, comment_auth=self)
        ra.save()
        return flag

    def remove_auth(self, user):
        try:
            CommentMem.objects.get(user=user, comment_auth=self).delete()
        except:
            return False
        return True


class WriteAuth(models.Model):
    user = models.ManyToManyField(to='user.User', related_name='writeable_doc', through='WriteMem', through_fields=('write_auth', 'user'))
    ent = models.ForeignKey(to='entity.Entity', related_name='write_auth', on_delete=models.CASCADE)
    key = models.CharField(max_length=64, verbose_name='可写权限密钥', default='')

    def add_auth(self, user):
        ra, flag = WriteMem.objects.get_or_create(user=user, write_auth=self)
        ra.save()
        return flag

    def remove_auth(self, user):
        try:
            WriteMem.objects.get(user=user, write_auth=self).delete()
        except:
            return False
        return True