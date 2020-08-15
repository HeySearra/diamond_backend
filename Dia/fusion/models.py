from django.db import models


class Collection(models.Model):
    user = models.ForeignKey('user.User', related_name='related_collection', on_delete=models.CASCADE)
    ent = models.ForeignKey('entity.Entity', related_name='ent', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True, verbose_name='文件收藏时间')

    class Meta:
        ordering = ["-dt"]


class Links(models.Model):
    user = models.ForeignKey(null=False, to='user.User', related_name='links', on_delete=models.CASCADE)
    ent = models.ForeignKey(null=False, to='entity.Entity', related_name='links', on_delete=models.CASCADE)